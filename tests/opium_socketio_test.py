import asyncio

from config import read_config
from opium_sockets import OpiumApi
from opium_api import OpiumClient
import datetime as dt


def test_listen_for_orders():
    client = OpiumClient(read_config('public_key'), read_config('private_key'))

    token = '0x' + client.generate_access_token()
    print(f"token: {token}")
    trading_pair = 'OEX-FUT-1DEC-135.00'
    r = asyncio.run(OpiumApi(test_api=True).listen_for_account_orders(trading_pair=trading_pair,
                                                                      maker_addr=read_config('public_key'),
                                                                      sig=token))
    print(r)


def test_get_order_book():
    trading_pair = 'OEX-FUT-1DEC-135.00'

    r = asyncio.run(OpiumApi(test_api=True).get_new_order_book(trading_pair))
    print(f"r: {r}")


def test_get_latest_price():
    trading_pair = 'OEX-FUT-1DEC-135.00'

    r = asyncio.run(OpiumApi(test_api=True).get_latest_price(trading_pair))
    print(f"r: {r}")


def test_listen_for_trades():
    async def run():
        trading_pair = 'OEX-FUT-1DEC-135.00'

        g = OpiumApi(test_api=True).listen_for_trades(trading_pair=trading_pair)

        async for trade in g:
            print(f"trade: {trade}")

    r = asyncio.run(run())
    print(r)




def test_get_order_status():
    client = OpiumClient(read_config('public_key'), read_config('private_key'))

    async def get_order_status(order_id: str = None):
        token = '0x' + client.generate_access_token()
        print(f"token: {token}")
        trading_pair = 'OEX-FUT-1DEC-135.00'

        socketio = OpiumApi(test_api=True)

        orders = await socketio.get_account_orders(trading_pair, token)
        print(f"orders: {orders}")
        await asyncio.sleep(1)
        trades = await socketio.get_account_trades(trading_pair, token)
        print(f"trades: {trades}")
        return [orders, trades]

    r = asyncio.run(get_order_status())


class SocketIOTest:
    client = OpiumClient(read_config('public_key'), read_config('private_key'))
    trading_pair = 'OEX-FUT-1DEC-135.00'
    token = '0x' + client.generate_access_token()

    @classmethod
    def test_listen_for_trades(cls):
        async def run():
            async for trades in OpiumApi(test_api=True).listen_for_trades(trading_pair=cls.trading_pair, new_only=True):
                for t in trades:
                    print(f"t: {t}")

        r = asyncio.run(run())
        print(r)


    @classmethod
    def test_listen_for_account_trades(cls):
        async def run():
            socketio = OpiumApi(test_api=True)
            async for trades in socketio.listen_for_account_trades(cls.trading_pair, cls.client.get_public_key(), cls.token):
                for trade in trades:
                    print(f"t: {trade}")
        r = asyncio.run(run())
        print(r)

    @classmethod
    def test_listen_for_account_orders(cls):
        async def run():
            socketio = OpiumApi(test_api=True)
            async for orders in socketio.listen_for_account_orders(cls.trading_pair, cls.client.get_public_key(), cls.token):
                for order in orders:
                    print(f"t: {order}")
        r = asyncio.run(run())
        print(r)

    @classmethod
    def test_listen_for_order_book_diffs(cls):
        async def run():
            api = OpiumApi(test_api=True).listen_for_order_book_diffs(trading_pair=cls.trading_pair)

            async for ob_update in api:
                print(f"ob_update: {ob_update}")

        r = asyncio.run(run())
        print(r)


if __name__ == '__main__':
    SocketIOTest.test_listen_for_trades()
