import asyncio
from typing import List
import logging
from socketio import AsyncClient

logger = logging.getLogger(__name__)


class SocketBase:
    """
    SocketIO wrapper
    """
    TEST_ENDPOINT = 'https://api-test.opium.exchange'
    ENDPOINT = 'https://api.opium.exchange'

    NAMESPACE = '/v1'

    def __init__(self, test_api=False, debug=False):
        self.endpoint = (SocketBase.TEST_ENDPOINT if test_api else SocketBase.ENDPOINT) + self.NAMESPACE + '/'
        self._sio = AsyncClient(engineio_logger=debug, logger=False)
        self.queue: asyncio.Queue = asyncio.Queue()

    async def init(self):
        await self.register_event('connect', self.connect_handler)
        await self.register_event('connect_error', self.connect_error_handler)
        await self.register_event('disconnect', self.disconnect_handler)

    @staticmethod
    async def connect_handler():
        logger.info("I'm connected!")

    @staticmethod
    async def connect_error_handler():
        logger.info("The connection failed!")

    @staticmethod
    async def disconnect_handler():
        logger.info("I'm disconnected!")

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
