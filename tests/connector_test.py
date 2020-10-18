from pprint import pprint

from config import read_config
from opium_api import OpiumClient


def get_balance_test():
    client = OpiumClient(read_config('public_key'), read_config('private_key'))

    print(f"balance: {client.get_balance()}")


def t():

    arguments = {
        'authAddress': public_key,
    }

    r = client.make_secure_call('/trades/all/address', arguments=arguments)
    pprint(r.json())

    r = client.make_secure_call('/tickers', arguments=arguments)
    pprint(r.json())


if __name__ == '__main__':
    get_balance_test()
