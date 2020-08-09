import os
import unittest
from ..connector import *

# Some values are hardcoded because there is no way of discovering them (ex. ticker_hash)

# The wallet must have some amount of DAI on Rinkeby for creating orders and
# some amount of ETH for sending transactions
connector = Connector(os.environ['PRIVATE_KEY'], os.environ['PUBLIC_KEY'])

class TestApiConnector(unittest.TestCase):

    def create_and_delete(self):
        # Create ASK order
        sendOrderResponse = connector.send_order(
            OrderBookAction.ask,
            '0x598cc7d5b3a09a27e68b450610d5b47d86cc8602308f23232c03571f79e65a77',
            '0x0558dc82f203C8c5f5b9033061aa5AdefFC40AF7', # DAI token address on Rinkeby
            3,
            1,
            0
        )
        # TODO: check that order was created

        connector.cancel_order(List(sendOrderResponse[0].id))
        # TODO: check that order was deleted

    def test_matching(self):
        # Create ASK order
        sendOrderResponse = connector.send_order(
            OrderBookAction.ask,
            '0x598cc7d5b3a09a27e68b450610d5b47d86cc8602308f23232c03571f79e65a77',
            '0x0558dc82f203C8c5f5b9033061aa5AdefFC40AF7', # DAI token address on Rinkeby
            3,
            1,
            0
        )
        # TODO: check that order was created

        # Create BID order
        sendOrderResponse = connector.send_order(
            OrderBookAction.bid,
            '0x598cc7d5b3a09a27e68b450610d5b47d86cc8602308f23232c03571f79e65a77',
            '0x0558dc82f203C8c5f5b9033061aa5AdefFC40AF7',
            3,
            1,
            0
        )
        # TODO: check that order was created

        # TODO: await few seconds (~10 secs) and check if orders matched

    def test_secondary_market(self):
        # Create ASK order
        sendOrderResponse = connector.send_order(
            OrderBookAction.ask,
            '0x598cc7d5b3a09a27e68b450610d5b47d86cc8602308f23232c03571f79e65a77',
            '0x0558dc82f203C8c5f5b9033061aa5AdefFC40AF7', # DAI token address on Rinkeby
            3,
            1,
            0
        )

        # TODO: Check that you are selling your previously matched position and did not create a new order

    def test_creating_an_order_after_secondary_position(self):
        # Create ASK order
        sendOrderResponse = connector.send_order(
            OrderBookAction.ask,
            '0x598cc7d5b3a09a27e68b450610d5b47d86cc8602308f23232c03571f79e65a77',
            '0x0558dc82f203C8c5f5b9033061aa5AdefFC40AF7', # DAI token address on Rinkeby
            3,
            1,
            0
        )
        # TODO: check that order was created

if __name__ == '__main__':
    unittest.main()
