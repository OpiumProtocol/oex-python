import asyncio
from json.decoder import JSONDecodeError
from typing import Dict, List, Any
import requests
import datetime as dt
import logging
from socketio import AsyncClient

from config import read_config
from .parsers import Parser


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

    async def subscribe(self, channel, **kwargs):
        s = {'ch': channel}
        s.update(kwargs)
        await self.register_event(channel)
        await self.emit('subscribe', s)

    async def unsubscribe(self, channel, **kwargs):
        s = {'ch': channel}
        s.update(kwargs)
        await self.emit('unsubscribe', s)

    async def listen_for(self, channel, **kwargs):
        """
        Move this into base_class
        """
        await self.init()
        await self.connect()

        await self.subscribe(channel=channel, **kwargs)

        while True:
            msg = await self.queue.get()
            msg = msg.get('d')

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
            msg = msg.get('d')
            self.queue.task_done()
            await self.unsubscribe(channel, **kwargs)
            await asyncio.sleep(0.5)
            await self.disconnect()
            return msg



class OpiumApi:
    TEST_ENDPOINT = 'https://api-test.opium.exchange/'
    ENDPOINT = 'https://api.opium.exchange/'

    NAMESPACE = 'v1/'

    def __init__(self, test_api=False):
        self.endpoint = (OpiumApi.TEST_ENDPOINT if test_api else OpiumApi.ENDPOINT) + self.NAMESPACE
        self._last_recv_time: float = 0
        self._current_channel = None
        self._current_subscription = None

        self._socket = SocketBase(test_api=True)

    def get_last_message_time(self):
        return self._last_recv_time

    def get_traded_tickers(self) -> Dict[str, str]:
        # TODO: move this method into Opium Client
        """
        Get not expired tickers
        """
        r = requests.get(f'{self.endpoint}tickers?expired=false')
        return {ticker['productTitle']: ticker['hash'] for ticker in r.json()}

    def get_ticker_token(self, ticker_hash: str) -> str:
        # TODO: move this method into Opium Client
        return requests.get(f'{self.endpoint}tickers/data/{ticker_hash}').json()[0]['token']


    async def get_latest_price(self, ticker: str) -> Dict[str, str]:
        # TODO move ex handling into get_as_rest(...)
        try:
            r = await self.get_as_rest('trades:ticker:all', ticker)
            trades: List = r.get('d', [])
            price = trades[0]['p'] if trades else None
            return {ticker: str(price)}
        except JSONDecodeError as ex:
            print(f"ex: {ex} check if the server works")
            return {}



    @staticmethod
    def get_timestamp() -> int:
        return int(dt.datetime.now().timestamp())

    # async def listen_for_trades(self, trading_pair: str):
    #     """
    #     Convert a trade data into standard OrderBookMessage:
    #         "exchange_order_id": msg.get("d"),
    #         "trade_type": msg.get("s"),
    #         "price": msg.get("p"),
    #         "amount": msg.get("q")
    #
    #     """
    #
    #     ticker_hash = self._get_ticker_hash(trading_pair)
    #
    #     delta: int = int(dt.timedelta(days=-5).total_seconds())
    #
    #     last_ts: int = self.get_timestamp() - delta
    #
    #     last_trade_tx: str = ''
    #     init = True
    #     # TODO: add queue
    #
    #     async for trades in self.listen_for('trades:ticker:all', {'t': ticker_hash, 'c': self.get_ticker_token(ticker_hash)}):
    #
    #         if init:
    #             init = False
    #             t = trades[-1]
    #             last_trade_tx = t['tx']
    #
    #         found_last_tx = False
    #         for t in reversed(trades):
    #             tx = t['tx']
    #
    #             if found_last_tx:
    #                 # new trades
    #                 ts = self.get_timestamp()
    #                 last_trade_tx = tx
    #                 trade = {
    #                     'trading_pair': trading_pair,
    #                     'trade_type': 'na',
    #                     'exchange_order_id': tx,
    #                     'update_id': ts,
    #                     'price': t['p'],
    #                     'amount': t['q'],
    #                     'timestamp': ts
    #                 }
    #                 yield trade
    #
    #             if last_trade_tx == tx and found_last_tx is False:
    #                 found_last_tx = True

    async def close(self):
        await self._socket.unsubscribe(self._current_channel, **self._current_subscription)
        await asyncio.sleep(0.5)
        await self._socket.disconnect()

    async def listen_for(self, channel, subscription):
        self._current_channel = channel
        self._current_subscription = subscription

        async for msg in self._socket.listen_for(self._current_channel, **self._current_subscription):
            self._last_recv_time = dt.datetime.now().timestamp()
            yield msg

    def _get_ticker_hash(self, trading_pair: str):
        traded_tickers = self.get_traded_tickers()
        try:
            return traded_tickers[trading_pair]
        except KeyError:
            print('Ticker is not in traded tickers')
            return

    async def listen_for_account_orders(self, trading_pair: str, maker_addr: str, sig: str):
        """
        Listen for orders in orderbook for the maker_addr
        """
        ticker_hash = self._get_ticker_hash(trading_pair)

        async for order in self.listen_for('orderbook:orders:makerAddress', {'t': ticker_hash,
                                                                             'c': self.get_ticker_token(ticker_hash),
                                                                             'addr': maker_addr,
                                                                             'sig': sig}):
            yield order



    async def listen_for_account_trades(self, trading_pair: str, maker_addr: str, sig: str, new_only=False):
        """
        Listen for completed trades for the maker_addr
        """
        ticker_hash = self._get_ticker_hash(trading_pair)

        ts: int = int(dt.datetime.now().timestamp()) if new_only else 0

        async for trades in self.listen_for('trades:ticker:address', {'t': ticker_hash,
                                                                      'c': self.get_ticker_token(ticker_hash),
                                                                      'addr': maker_addr,
                                                                      'sig': sig}):
            trades = [Parser.parse_account_trade(t, trading_pair) for t in trades if t['t'] >= ts]
            if trades and new_only:
                ts: int = trades[0]['create_time']
            yield trades

    async def listen_for_trades(self, trading_pair: str, new_only=False):
        """
        Listen for trades
        """
        ticker_hash = self._get_ticker_hash(trading_pair)

        ts: int = int(dt.datetime.now().timestamp()) if new_only else 0

        async for trades in self.listen_for('trades:ticker:all', {'t': ticker_hash, 'c': self.get_ticker_token(ticker_hash)}):
            trades = [Parser.parse_account_trade(t, trading_pair) for t in trades if t['t'] >= ts]
            if trades and new_only:
                ts: int = trades[0]['create_time']
            yield trades


    async def listen_for_order_book_diffs(self, trading_pair: str):
        ticker_hash = self._get_ticker_hash(trading_pair)

        async for ob in self.listen_for('orderbook:orders:ticker', {'t': ticker_hash,
                                                                    'c': self.get_ticker_token(ticker_hash)}):
            yield Parser.parse_order_book(ob)

    async def get_account_orders(self, trading_pair, access_token):
        async for orders in self.listen_for_account_orders(trading_pair, read_config('public_key'),access_token):
            await self.close()
            return orders
            # for order in orders:
            #     if True:
            #         await self.close()
            #         return order

    async def get_account_trades(self, trading_pair, access_token):
        async for trades in self.listen_for_account_trades(trading_pair,read_config('public_key'), access_token):
            await self.close()
            return trades

            for trade in trades:
                if True:
                    await self.close()
                    return trade

    async def get_new_order_book(self, trading_pair: str):  # -> OrderBook:
        """
        returns:
        {'lastUpdateId': 1603730733,
        'bids': [[12.36, 1], [2.35, 10], [2.33, 2], [2.31, 1], [1.9, 3], [1.09, 4], [0.88, 1], [0.76, 5], [0.46, 3]...
        'asks': [[20.09, 3], [20.27, 1], [20.43, 5], [20.49, 5], [21.58, 2], [22.004, 1], [22.047, 1]...
        """
        async for ob in self.listen_for_order_book_diffs(trading_pair=trading_pair):
            await self.close()
            return Parser.parse_order_book(ob)
