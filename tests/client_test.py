from decimal import Decimal
from pprint import pprint

from config import read_config
from opium_api import OpiumClient
from opium_api.enums import OrderBookAction
from opium_sockets import OpiumApi


client = OpiumClient(read_config('public_key'), read_config('private_key'))


def get_balance_test():

    print(f"balance: {client.get_balance()}")


def test_limit_buy_sell():

    # order: [{'id': '5f92b180603bd50028f46a82'}]
    order = client.create_order('OEX-FUT-1DEC-135.00',
                                side='BUY',
                                price=Decimal('19.43'),
                                quantity='10')
    print(f"order: {order}")
    #
    # print(f"balance: {client.get_balance()}")


def test_cancel_order():
    id_: str = '5f9a8043468dd6003aaba960'
    r = client.cancel_order([id_])

    print(f"r: {r}")


if __name__ == '__main__':
    test_cancel_order()