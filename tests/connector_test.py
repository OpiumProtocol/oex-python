from decimal import Decimal
from pprint import pprint

from config import read_config
from opium_api import OpiumClient
from opium_api.enums import OrderBookAction
from sockets import OpiumApi

api = OpiumApi(test_api=True)


def get_balance_test():
    client = OpiumClient(read_config('public_key'), read_config('private_key'))

    print(f"balance: {client.get_balance()}")


def limit_buy_sell_test():
    test_ticker = 'OEX-FUT-1DEC-135.00'

    client = OpiumClient(read_config('public_key'), read_config('private_key'))
    traded_tickers = api.get_traded_tickers()

    test_ticker_hash = traded_tickers[test_ticker]
    currency_hash = api.get_ticker_token(test_ticker_hash)

    print(f"traded_tickers: {traded_tickers}")
    print(f"test_ticker_hash: {test_ticker_hash}")

    # order: [{'id': '5f92b180603bd50028f46a82'}]
    order = client.send_order(action=OrderBookAction.bid,
                              ticker_hash=test_ticker_hash,
                              currency_hash=currency_hash,
                              price=Decimal('2.37'), quantity=10,
                              expires_at=9999999999)
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
