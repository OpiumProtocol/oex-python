from decimal import Decimal
from pprint import pprint

from opium_api.connector import Connector
from opium_api.enums import OrderBookAction

if __name__ == '__main__':
    cc = Connector(private_key='d849a3cf8f1e8c2285532db010298b2b06e8f56b24ca1feaf66717fb7044d35b',
                   public_key='0x2083fc00ad9a17b9073b10b520dcf936a14eaa05')

    zz = cc.send_order(action=OrderBookAction.bid,
                       ticker_hash='0x598cc7d5b3a09a27e68b450610d5b47d86cc8602308f23232c03571f79e65a77',
                       currency_hash='0x0558dc82f203C8c5f5b9033061aa5AdefFC40AF7',
                       price=Decimal(666.42),
                       quantity=1,
                       expires_at=0)
    pprint(zz)
    # zz = cc.cancel_order('5f2bcaa5c90c490033f39a75')
    # pprint(zz)

    # pprint(cc.get_balance())
