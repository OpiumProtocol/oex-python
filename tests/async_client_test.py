import asyncio
from decimal import Decimal

from config import read_config
from opium_api import AsyncOpiumClient


# import sentry_sdk
# sentry_sdk.init(
#     "https://c8ad10ae5b0f4024be56e35032666fa8@o480606.ingest.sentry.io/5528023",
#     traces_sample_rate=1.0
# )

def get_tickers_test():
    async def run():
        client = AsyncOpiumClient(read_config('public_key'), read_config('private_key'))
        await client.init()
        tickers = await client.get_tickers()
        print(f"tickers: {tickers}")

        await client.close()

    asyncio.run(run())


def get_balance_async_test():
    async def run():
        client = AsyncOpiumClient(read_config('public_key'), read_config('private_key'))
        r = await client.get_balance()
        print(f"r: {r}")
        await client.close()

    asyncio.run(run())


def test_limit_buy_sell():
    async def run():
        client = AsyncOpiumClient(read_config('public_key'), read_config('private_key'))
        await client.init()

        r = await client.create_order('OEX-FUT-1DEC-135.00',
                                      side='BUY',
                                      price=Decimal('19.43'),
                                      quantity='10')
        await client.close()
        print(f"r: {r}")

    asyncio.run(run())

    # order: [{'id': '5f92b180603bd50028f46a82'}]


def test_cancel_order():
    async def run():
        client = AsyncOpiumClient(read_config('public_key'), read_config('private_key'))
        await client.init()
        id_: str = '5fbacea84aced7001cff1513'
        r = await client.cancel_order([id_])

        await client.close()
        print(f"r: {r}")

    asyncio.run(run())


def get_traded_tickers_test():

    async def run():
        client = AsyncOpiumClient(read_config('public_key'), read_config('private_key'))
        await client.init()
        tickers = client.get_traded_tickers()
        print(f"tickers: {tickers}")

        await client.close()

    asyncio.run(run())


def check_network_test():

    async def run():
        client = AsyncOpiumClient(read_config('public_key'), read_config('private_key'))
        await client.init()
        r = await client.check_network()
        print(f"r: {r}")

        await client.close()

    asyncio.run(run())



if __name__ == '__main__':
    check_network_test()
    # get_balance_async_test()
    # get_tickers_test()
