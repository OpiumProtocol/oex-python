import asyncio

from config import read_config
from opium_sockets import OpiumApi
from opium_api import OpiumClient
import datetime as dt


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


def get_order_book_test():
    trading_pair = 'OEX-FUT-1DEC-135.00'

    r = asyncio.run(OpiumApi(test_api=True).get_new_order_book(trading_pair))
    print(f"r: {r}")



    # {'ch': 'orderbook:orders:ticker', 'a': 'set',
    #  'p': {'t': '0xc9b51c4ff681d5e9c5ff2f850104bdefc2bb48d4575b458d81ee5cfb4d3c2e01',
    #        'c': '0x0558dc82f203C8c5f5b9033061aa5AdefFC40AF7'},
    #  'd': [{'v': 1, 'a': 'BID', 'p': 12.36, 'c': 0.010526315789473684},
    #        {'v': 10, 'a': 'BID', 'p': 2.35, 'c': 0.11578947368421053},
    #        {'v': 2, 'a': 'BID', 'p': 2.33, 'c': 0.1368421052631579},
    #        {'v': 1, 'a': 'BID', 'p': 2.31, 'c': 0.1473684210526316},
    #        {'v': 3, 'a': 'BID', 'p': 1.9, 'c': 0.17894736842105263},
    #        {'v': 4, 'a': 'BID', 'p': 1.09, 'c': 0.22105263157894736},
    #        {'v': 1, 'a': 'BID', 'p': 0.88, 'c': 0.23157894736842105},
    #        {'v': 5, 'a': 'BID', 'p': 0.76, 'c': 0.28421052631578947},
    #        {'v': 3, 'a': 'BID', 'p': 0.46, 'c': 0.3157894736842105},
    #        {'v': 3, 'a': 'BID', 'p': 0.45, 'c': 0.34736842105263155},
    #        {'v': 3, 'a': 'BID', 'p': 0.39, 'c': 0.3789473684210526},
    #        {'v': 4, 'a': 'BID', 'p': 0.15, 'c': 0.42105263157894735},
    #        {'v': 2, 'a': 'BID', 'p': 0.03, 'c': 0.4421052631578947},
    #        {'v': 3, 'a': 'ASK', 'p': 20.09, 'c': 0.031578947368421054},
    #        {'v': 1, 'a': 'ASK', 'p': 20.27, 'c': 0.042105263157894736},
    #        {'v': 5, 'a': 'ASK', 'p': 20.43, 'c': 0.09473684210526315},
    #        {'v': 5, 'a': 'ASK', 'p': 20.49, 'c': 0.14736842105263157},
    #        {'v': 2, 'a': 'ASK', 'p': 21.58, 'c': 0.16842105263157894},
    #        {'v': 1, 'a': 'ASK', 'p': 22.004, 'c': 0.17894736842105263},
    #        {'v': 1, 'a': 'ASK', 'p': 22.047, 'c': 0.18947368421052632}, {'v': 1, 'a': 'ASK', 'p': 22.072, 'c': 0.2},
    #        {'v': 1, 'a': 'ASK', 'p': 22.084, 'c': 0.2105263157894737},
    #        {'v': 1, 'a': 'ASK', 'p': 22.182, 'c': 0.2210526315789474},
    #        {'v': 1, 'a': 'ASK', 'p': 22.228, 'c': 0.23157894736842108},
    #        {'v': 1, 'a': 'ASK', 'p': 22.326, 'c': 0.24210526315789477},
    #        {'v': 1, 'a': 'ASK', 'p': 22.329, 'c': 0.25263157894736843},
    #        {'v': 1, 'a': 'ASK', 'p': 22.384, 'c': 0.2631578947368421},
    #        {'v': 1, 'a': 'ASK', 'p': 22.394, 'c': 0.27368421052631575},
    #        {'v': 1, 'a': 'ASK', 'p': 22.42, 'c': 0.2842105263157894},
    #        {'v': 1, 'a': 'ASK', 'p': 22.447, 'c': 0.2947368421052631},
    #        {'v': 1, 'a': 'ASK', 'p': 22.497, 'c': 0.30526315789473674},
    #        {'v': 1, 'a': 'ASK', 'p': 22.504, 'c': 0.3157894736842104},
    #        {'v': 1, 'a': 'ASK', 'p': 22.538, 'c': 0.32631578947368406},
    #        {'v': 1, 'a': 'ASK', 'p': 22.559, 'c': 0.3368421052631577},
    #        {'v': 1, 'a': 'ASK', 'p': 22.626, 'c': 0.3473684210526314},
    #        {'v': 1, 'a': 'ASK', 'p': 22.65, 'c': 0.35789473684210504},
    #        {'v': 1, 'a': 'ASK', 'p': 22.712, 'c': 0.3684210526315787},
    #        {'v': 2, 'a': 'ASK', 'p': 22.95, 'c': 0.3894736842105261},
    #        {'v': 1, 'a': 'ASK', 'p': 22.956, 'c': 0.39999999999999974},
    #        {'v': 4, 'a': 'ASK', 'p': 23.17, 'c': 0.4421052631578945},
    #        {'v': 2, 'a': 'ASK', 'p': 23.46, 'c': 0.4631578947368419},
    #        {'v': 1, 'a': 'ASK', 'p': 23.59, 'c': 0.47368421052631554},
    #        {'v': 4, 'a': 'ASK', 'p': 24.27, 'c': 0.5157894736842102},
    #        {'v': 4, 'a': 'ASK', 'p': 24.92, 'c': 0.557894736842105}]}


if __name__ == '__main__':
    get_order_book_test()
