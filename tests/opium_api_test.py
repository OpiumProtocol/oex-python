import asyncio

from config import read_config
from sockets import OpiumApi
from opium_api import OpiumClient


def listen_for_orders_test():
    client = OpiumClient(read_config('public_key'), read_config('private_key'))

    token = '0x' + client.generate_access_token()
    print(f"token: {token}")
    trading_pair = 'OEX-FUT-1DEC-135.00'
    r = asyncio.run(OpiumApi(test_api=True).listen_for_orders(trading_pair=trading_pair,
                                                              maker_addr=read_config('public_key'),
                                                              sig=token,
                                                              output=NotImplemented))
    print(r)


if __name__ == '__main__':
    listen_for_orders_test()
