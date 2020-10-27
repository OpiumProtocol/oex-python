import asyncio
from json.decoder import JSONDecodeError
from typing import Dict, List, Any
import requests
import datetime as dt

from socketio import AsyncClient


class SocketBase:
    TEST_ENDPOINT = 'https://api-test.opium.exchange'
    ENDPOINT = 'https://api.opium.exchange'

    NAMESPACE = '/v1'

    def __init__(self, test_api=False):
        self.endpoint = (SocketBase.TEST_ENDPOINT if test_api else SocketBase.ENDPOINT) + self.NAMESPACE + '/'
        self._sio = AsyncClient(engineio_logger=True, logger=True)
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

    async def read_queue_once(self):
        msg = await self.queue.get()
        self.queue.task_done()
        return msg

    async def subscribe(self, channel, **kwargs):
        s = {'ch': channel}
        s.update(kwargs)
        print(f"s: {s}")
        await self.register_event(channel)
        await self.emit('subscribe', s)


class OpiumApi:
    TEST_ENDPOINT = 'https://api-test.opium.exchange/'
    ENDPOINT = 'https://api.opium.exchange/'

    NAMESPACE = 'v1/'

    def __init__(self, test_api=False):
        self.endpoint = (OpiumApi.TEST_ENDPOINT if test_api else OpiumApi.ENDPOINT) + self.NAMESPACE
        self._last_recv_time: float = 0

    def get_last_message_time(self):
        return self._last_recv_time

    def get_traded_tickers(self) -> Dict[str, str]:
        """
        Get not expired tickers
        """
        r = requests.get(f'{self.endpoint}tickers?expired=false')
        return {ticker['productTitle']: ticker['hash'] for ticker in r.json()}

    def get_ticker_token(self, ticker_hash: str) -> str:
        return requests.get(f'{self.endpoint}tickers/data/{ticker_hash}').json()[0]['token']

    async def get_as_rest(self, channel: str, ticker: str) -> Dict[str, str]:
        """
        we use socket_io as rest api here
        @param ticker: ticker in human readable format. example: 'OEX-FUT-1NOV-135.00'
        @return:
        """

        # TODO get_latest_prices(...)
        traded_tickers = self.get_traded_tickers()

        try:
            ticker_hash = traded_tickers[ticker]
        except KeyError:
            print('Ticker is not in traded tickers')
            return None

        currency = self.get_ticker_token(ticker_hash)

        subscription = {
            't': ticker_hash,
            'c': currency}

        s = SocketBase(test_api=True)
        await s.init()
        await s.connect()
        await s.subscribe(channel=channel, **subscription)
        await asyncio.sleep(1)
        await s.disconnect()

        return await s.read_queue_once()

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
    def response_to_order_book(r: Dict[str, Any]) -> Dict[str, Any]:
        bids = []
        asks = []

        order_book = r.get('d')
        if order_book is not None:
            for order in order_book:
                if order['a'] == 'BID':
                    bids.append([order['p'], order['v']])
                else:
                    asks.append([order['p'], order['v']])

        return {'lastUpdateId': int(dt.datetime.now().timestamp()),
                'bids': bids,
                'asks': asks}

    async def get_new_order_book(self, ticker: str):  # -> OrderBook:
        """
        returns:
        {'lastUpdateId': 1603730733,
        'bids': [[12.36, 1], [2.35, 10], [2.33, 2], [2.31, 1], [1.9, 3], [1.09, 4], [0.88, 1], [0.76, 5], [0.46, 3]...
        'asks': [[20.09, 3], [20.27, 1], [20.43, 5], [20.49, 5], [21.58, 2], [22.004, 1], [22.047, 1]...
        """
        # TODO move ex handling into get_as_rest(...)
        try:
            return self.response_to_order_book(await self.get_as_rest('orderbook:orders:ticker', ticker))
        except JSONDecodeError as ex:
            print(f"ex: {ex} check if the server works")
            return {}

    @staticmethod
    def get_timestamp() -> int:
        return int(dt.datetime.now().timestamp())


    async def listen_for_trades(self, trading_pair: str):
        """
        Convert a trade data into standard OrderBookMessage:
            "exchange_order_id": msg.get("d"),
            "trade_type": msg.get("s"),
            "price": msg.get("p"),
            "amount": msg.get("q")

        """

        traded_tickers = self.get_traded_tickers()

        try:
            ticker_hash = traded_tickers[trading_pair]
        except KeyError:
            print('Ticker is not in traded tickers')
            return

        currency = self.get_ticker_token(ticker_hash)
        subscription = {
            't': ticker_hash,
            'c': currency}

        s = SocketBase(test_api=True)
        await s.init()
        await s.connect()
        await s.subscribe(channel='trades:ticker:all', **subscription)

        queue = s.queue

        delta: int = int(dt.timedelta(days=-5).total_seconds())

        last_ts: int = self.get_timestamp() - delta

        last_trade_tx: str = ''
        init = True
        # TODO: add queue

        while True:
            msg = await queue.get()

            print(f"msg: {msg}")
            trades: List = msg['d']

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
                        'trade_id': tx,
                        'update_id': ts,
                        'price': t['p'],
                        'amount': t['q'],
                        'timestamp': ts

                    }
                    yield trade

                if last_trade_tx == tx and found_last_tx is False:
                    print(f"found_last_tx: {found_last_tx}")
                    found_last_tx = True

    async def listen_for_order_book_diffs(self):
        traded_tickers = self.get_traded_tickers()

        trading_pair = 'OEX-FUT-1DEC-135.00'

        try:
            ticker_hash = traded_tickers[trading_pair]
        except KeyError:
            print('Ticker is not in traded tickers')
            return None

        currency = self.get_ticker_token(ticker_hash)
        subscription = {
            't': ticker_hash,
            'c': currency}

        s = SocketBase(test_api=True)
        await s.init()
        await s.connect()
        await s.subscribe(channel='orderbook:orders:ticker', **subscription)

        queue = s.queue

        while True:
            msg = await queue.get()
            print(f"msg: {msg}")

    async def listen_for_orders(self, trading_pair: str, maker_addr: str, sig: str, output: asyncio.Queue):
        """
        trading_pair = 'OEX-FUT-1DEC-135.00'
        """

        traded_tickers = self.get_traded_tickers()

        try:
            ticker_hash = traded_tickers[trading_pair]
        except KeyError:
            print('Ticker is not in traded tickers')
            return None

        currency = self.get_ticker_token(ticker_hash)
        subscription = {
            't': ticker_hash,
            'c': currency,
            'addr': maker_addr,
            'sig': sig}

        s = SocketBase(test_api=True)
        await s.init()
        await s.connect()
        await s.subscribe(channel='orderbook:orders:makerAddress', **subscription)

        queue = s.queue

        current_msg = None

        while True:
            msg = await queue.get()
            self._last_recv_time = dt.time()
            await output.put(msg)
            queue.task_done()

            print(f"msg: {msg}")
            current_msg = msg.get('d')

            print(f"current_msg: {current_msg}")
