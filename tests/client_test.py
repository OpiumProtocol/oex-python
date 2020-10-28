from decimal import Decimal
from pprint import pprint

from config import read_config
from opium_api import OpiumClient
from opium_api.enums import OrderBookAction
from opium_sockets import OpiumApi


# api = OpiumApi(test_api=True)


def get_balance_test():
    client = OpiumClient(read_config('public_key'), read_config('private_key'))

    print(f"balance: {client.get_balance()}")


def limit_buy_sell_test():

    client = OpiumClient(read_config('public_key'), read_config('private_key'))

    # order: [{'id': '5f92b180603bd50028f46a82'}]
    order = client.create_order('OEX-FUT-1DEC-135.00',
                                side='BUY',
                                price=Decimal('20.43'),
                                quantity=10)
    print(f"order: {order}")
    #
    # print(f"balance: {client.get_balance()}")


# def t():
#
#     arguments = {
#         'authAddress': public_key,
#     }
#
#     r = client.make_secure_call('/trades/all/address', arguments=arguments)
#     pprint(r.json())
#
#     r = client.make_secure_call('/tickers', arguments=arguments)
#     pprint(r.json())


if __name__ == '__main__':
    limit_buy_sell_test()
