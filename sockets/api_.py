import asyncio
from json.decoder import JSONDecodeError
from typing import Dict
import requests
import socketio


class SocketBase:
    TEST_ENDPOINT = 'https://api-test.opium.exchange'
    ENDPOINT = 'https://api.opium.exchange'

    NAMESPACE = '/v1'

    def __init__(self, test_api=False):
        self.endpoint = (SocketBase.TEST_ENDPOINT if test_api else SocketBase.ENDPOINT) + self.NAMESPACE + '/'
        self._sio: socketio.Client = socketio.AsyncClient(engineio_logger=True, logger=True)
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
            return await self.get_as_rest('trades:ticker:all', ticker)
        except JSONDecodeError as ex:
            print(f"ex: {ex} check if the server works")
            return {}

    async def get_new_order_book(self, ticker: str):  # -> OrderBook:
        # TODO move ex handling into get_as_rest(...)
        try:
            return await self.get_as_rest('orderbook:orders:ticker', ticker)
        except JSONDecodeError as ex:
            print(f"ex: {ex} check if the server works")
            return {}

    async def listen_for_trades(self, ev_loop: asyncio.BaseEventLoop, output: asyncio.Queue):

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




        while True:
            await asyncio.sleep(1)

            output.put_nowait('msg')


if __name__ == '__main__':
    r = asyncio.run(OpiumApi(test_api=True).get_new_order_book('OEX-FUT-1NOV-135.00'))
    print(r)
