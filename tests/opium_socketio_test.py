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
    r = asyncio.run(OpiumApi(test_api=True).listen_for_orders(trading_pair=trading_pair,
                                                              maker_addr=read_config('public_key'),
                                                              sig=token,
                                                              output=NotImplemented))
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


def test_listen_for_order_book_diffs():

    async def run():
        trading_pair = 'OEX-FUT-1DEC-135.00'
        g = OpiumApi(test_api=True).listen_for_order_book_diffs(trading_pair=trading_pair)

        async for ob_update in g:
            print(f"ob_update: {ob_update}")
    r = asyncio.run(run())
    print(r)



if __name__ == '__main__':
    test_listen_for_order_book_diffs()
