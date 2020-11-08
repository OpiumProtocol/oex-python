import asyncio
from typing import Dict, List, Any

import aiohttp
import requests
import datetime as dt
from socketio import AsyncClient

from opium_api import OpiumClient
from .parsers import Parser, OrdersState, AccountOrders


class SocketBase:
    """
    SocketIO wrapper
    """
    TEST_ENDPOINT = 'https://api-test.opium.exchange'
    ENDPOINT = 'https://api.opium.exchange'

    NAMESPACE = '/v1'

    def __init__(self, test_api=False, debug=False):
        self.endpoint = (SocketBase.TEST_ENDPOINT if test_api else SocketBase.ENDPOINT) + self.NAMESPACE + '/'
        self._sio = AsyncClient(engineio_logger=debug, logger=True)
        self.queue: asyncio.Queue = asyncio.Queue()

    async def init(self):
        await self.register_event('connect', self.connect_handler)
        await self.register_event('connect_error', self.connect_error_handler)
        await self.register_event('disconnect', self.disconnect_handler)

    @staticmethod
    async def connect_handler():
        print("I'm connected!")

    @staticmethod
    async def connect_error_handler():
        print("The connection failed!")

    @staticmethod
    async def disconnect_handler():
        print("I'm disconnected!")

    async def connect(self):
        await self._sio.connect(url=self.endpoint, transports=['polling', 'websocket'], namespaces=[self.NAMESPACE])
        await asyncio.sleep(1)

    async def disconnect(self):
        await self._sio.disconnect()

    async def emit(self, event: str, data):
        await self._sio.emit(event=event, data=data, callback=self.callback, namespace=self.NAMESPACE)

    async def register_event(self, event, handler=None):
        if handler is None:
            handler = self.handler
        self._sio.on(event=event, handler=handler, namespace=self.NAMESPACE)

    async def callback(self, data):
        await asyncio.sleep(0)
        print('callback')
        print(f"data: {data}")

    async def handler(self, data):
        await self.queue.put(data)

    async def subscribe(self, channels: List[str], **kwargs):
        for channel in channels:
            s = {'ch': channel}
            s.update(kwargs)
            await self.register_event(channel)
            await self.emit('subscribe', s)
            await asyncio.sleep(0.25)

    async def unsubscribe(self, channels: List[str], **kwargs):
        for channel in channels:
            s = {'ch': channel}
            s.update(kwargs)
            await self.emit('unsubscribe', s)

    async def listen_for(self, channels: List, **kwargs):
        """
        Move this into base_class
        """
        await self.init()
        await self.connect()

        # TODO: pass different kwargs
        await self.subscribe(channels=channels, **kwargs)

        while True:
            msg = await self.queue.get()
            self.queue.task_done()
            yield msg

    async def read_once(self, channel, **kwargs):
        """
        Move this into base_class
        """
        await self.init()
        await self.connect()

        await self.subscribe(channel=channel, **kwargs)

        while True:
            msg = await self.queue.get()
            self.queue.task_done()
            await self.unsubscribe(channel, **kwargs)
            await asyncio.sleep(0.5)
            await self.disconnect()
            return msg


def get_traded_tickers() -> Dict[str, str]:
    """
    Get not expired tickers
    """
    r = requests.get(f'https://api-test.opium.exchange/v1/tickers?expired=false')
    return {ticker['productTitle']: ticker['hash'] for ticker in r.json()}


class OpiumApi:
    TEST_ENDPOINT = 'https://api-test.opium.exchange/'
    ENDPOINT = 'https://api.opium.exchange/'

    NAMESPACE = 'v1/'

    traded_tickers = get_traded_tickers()

    def __init__(self, test_api=False):
        self.endpoint = (OpiumApi.TEST_ENDPOINT if test_api else OpiumApi.ENDPOINT) + self.NAMESPACE
        self._last_recv_time: float = 0
        self._current_channels = None
        self._current_subscription = None
        self._socket = SocketBase(test_api=True)
        self.tickers_tokens = {}

    def get_last_message_time(self):
        return self._last_recv_time

    async def get_ticker_token(self, ticker_hash: str) -> str:
        if (token := self.tickers_tokens.get(ticker_hash)) is None:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{self.endpoint}tickers/data/{ticker_hash}') as resp:
                    token = (await resp.json())[0]['token']
                    self.tickers_tokens[ticker_hash] = token
        return token

    async def get_latest_price(self, ticker: str) -> Dict[str, str]:
        async for trades in self.listen_for_trades(ticker, new_only=False):
            await self.close()
            return {ticker: str(trades[0]['price'])}

    @staticmethod
    def get_timestamp() -> int:
        return int(dt.datetime.now().timestamp())

    async def close(self):
        await self._socket.unsubscribe(self._current_channels, **self._current_subscription)
        await asyncio.sleep(0.5)
        await self._socket.disconnect()

    async def listen_for(self, channels: List[str], subscription):
        self._current_channels = channels
        self._current_subscription = subscription

        async for msg in self._socket.listen_for(self._current_channels, **self._current_subscription):
            self._last_recv_time = dt.datetime.now().timestamp()
            yield msg

    def _get_ticker_hash(self, trading_pair: str):
        try:
            return self.traded_tickers[trading_pair]
        except KeyError:
            print(f'Ticker {trading_pair} is not in traded tickers')
            return

    async def listen_for_account_orders(self, trading_pair: str, maker_addr: str, sig: str):
        """
        Listen for orders in orderbook for the maker_addr
        """
        ticker_hash = self._get_ticker_hash(trading_pair)

        async for order in self.listen_for(['orderbook:orders:makerAddress'], {'t': ticker_hash,
                                                                               'c': await self.get_ticker_token(
                                                                                   ticker_hash),
                                                                               'addr': maker_addr,
                                                                               'sig': sig}):
            yield order

    async def listen_for_account_trades(self, trading_pair: str, maker_addr: str, sig: str, new_only=False):
        """
        Listen for completed trades for the maker_addr
        """
        ticker_hash = self._get_ticker_hash(trading_pair)

        ts: int = int(dt.datetime.now().timestamp()) if new_only else 0

        async for trades in self.listen_for(['trades:ticker:address'], {'t': ticker_hash,
                                                                        'c': await self.get_ticker_token(ticker_hash),
                                                                        'addr': maker_addr,
                                                                        'sig': sig}):
            trades = [Parser.parse_account_trade(t, trading_pair) for t in trades if t['t'] >= ts]
            if trades and new_only:
                ts: int = trades[0]['create_time']
            yield trades

    async def listen_for_account_trades_orders(self, trading_pair: str, maker_addr, sig):
        """
        Listen for orders, trades, balances
        """
        ticker_hash = self._get_ticker_hash(trading_pair)

        last_id: str = '0'

        os = OrdersState()

        acc_orders = AccountOrders()

        channels = ['orderbook:orders:makerAddress:updates', 'positions:address', 'trades:ticker:address']
        # channels = ['orderbook:orders:makerAddress:updates']

        async for msg in self.listen_for(channels,
                                         {'t': ticker_hash, 'c': await self.get_ticker_token(ticker_hash),
                                          'addr': maker_addr,
                                          'sig': sig}):
            data = msg['d']

            # we don't use this channel anymore
            if (msg_ch := msg['ch']) == 'orderbook:orders:makerAddress':
                data = os.update([Parser.parse_order(order, trading_pair) for order in data])

            elif msg_ch == 'orderbook:orders:makerAddress:updates':
                msg_type = msg['a']
                data = acc_orders.update(data, trading_pair, msg_type)


            elif msg_ch == 'trades:ticker:address':
                if last_id == '0':
                    last_id: int = data[0]['i']
                    data = []
                else:
                    # TODO: change to compare by hex id
                    trades = []
                    last_id_met = False
                    for trade in reversed(data):
                        if trade['i'] == last_id:
                            last_id_met = True
                        elif last_id_met:
                            trades.append(Parser.parse_account_trade(trade, trading_pair))
                    if trades:
                        last_id: int = trades[0]['trade_id']
                    data = trades

            elif msg_ch == 'positions:address':
                data = [Parser.parse_position(position, trading_pair) for position in data['pos']
                        if position['tt'] == trading_pair and position['ty'] == 'LONG']

            else:
                raise NotImplementedError(msg_ch)

            yield {'result': {'channel': msg['ch'],
                              'data': data}}

    async def listen_for_balance(self, client: OpiumClient):
        while True:
            await asyncio.sleep(1)
            yield await asyncio.get_event_loop().run_in_executor(None,
                                                                 lambda: client.get_balance())

    def parse_trade(self, t, trading_pair):
        return {
            'trading_pair': trading_pair,
            'trade_type': 'BUY' if t['a'] == 'ASK' else 'SELL',
            'exchange_order_id': t['tx'],
            'update_id': self.get_timestamp(),
            'price': t['p'],
            'amount': t['q'],
            'timestamp': self.get_timestamp()
        }

    async def listen_for_trades(self, trading_pair: str, new_only=True):
        """
        Listen for trades
        """
        ticker_hash = self._get_ticker_hash(trading_pair)

        ts: int = int(dt.datetime.now().timestamp()) if new_only else 0

        async for trades in self.listen_for(['trades:ticker:all'],
                                            {'t': ticker_hash, 'c': await self.get_ticker_token(ticker_hash)}):
            trades = [self.parse_trade(t, trading_pair) for t in trades['d'] if t['t'] >= ts]
            if trades and new_only:
                ts: int = trades[0]['timestamp']
            yield trades

    async def listen_for_order_book_diffs(self, trading_pair: str):
        ticker_hash = self._get_ticker_hash(trading_pair)

        async for ob in self.listen_for(['orderbook:orders:ticker'], {'t': ticker_hash,
                                                                      'c': await self.get_ticker_token(ticker_hash)}):
            yield Parser.parse_order_book(ob['d'])

    async def get_account_orders(self, trading_pair, marker_addr, access_token):
        async for orders in self.listen_for_account_orders(trading_pair, marker_addr, access_token):
            await self.close()
            return orders
            # for order in orders:
            #     if True:
            #         await self.close()
            #         return order

    async def get_account_trades(self, trading_pair, maker_addr, access_token):
        async for trades in self.listen_for_account_trades(trading_pair, maker_addr, access_token):
            await self.close()
            return trades

            # for trade in trades:
            #     if True:
            #         await self.close()
            #         return trade

    async def get_new_order_book(self, trading_pair: str):  # -> OrderBook:
        """
        returns:
        {'lastUpdateId': 1603730733,
        'bids': [[12.36, 1], [2.35, 10], [2.33, 2], [2.31, 1], [1.9, 3], [1.09, 4], [0.88, 1], [0.76, 5], [0.46, 3]...
        'asks': [[20.09, 3], [20.27, 1], [20.43, 5], [20.49, 5], [21.58, 2], [22.004, 1], [22.047, 1]...
        """
        async for ob in self.listen_for_order_book_diffs(trading_pair=trading_pair):
            await self.close()
            return ob


def temp():
    async def listen_for_trades(self, trading_pair: str):
        """
        Convert a trade data into standard OrderBookMessage:
            "exchange_order_id": msg.get("d"),
            "trade_type": msg.get("s"),
            "price": msg.get("p"),
            "amount": msg.get("q")

        """

        ticker_hash = self._get_ticker_hash(trading_pair)

        delta: int = int(dt.timedelta(days=-5).total_seconds())

        last_ts: int = self.get_timestamp() - delta

        last_trade_tx: str = ''
        init = True
        # TODO: add queue

        async for trades in self.listen_for('trades:ticker:all',
                                            {'t': ticker_hash, 'c': await self.get_ticker_token(ticker_hash)}):

            if init:
                init = False
                t = trades[-1]
                last_trade_tx = t['tx']

            found_last_tx = False
            for t in reversed(trades):
                tx = t['tx']

                if found_last_tx:
                    # new trades
                    ts = self.get_timestamp()
                    last_trade_tx = tx
                    trade = {
                        'trading_pair': trading_pair,
                        'trade_type': 'na',
                        'exchange_order_id': t['tx'],
                        'update_id': self.get_timestamp(),
                        'price': t['p'],
                        'amount': t['q'],
                        'timestamp': self.get_timestamp()
                    }
                    yield trade

                if last_trade_tx == tx and found_last_tx is False:
                    found_last_tx = True
#
