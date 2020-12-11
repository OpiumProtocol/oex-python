import datetime as dt
from typing import Dict, Any, List


class Parser:
    @staticmethod
    def parse_order_book(order_book: List[Dict[str, Any]]) -> Dict[str, Any]:

        bids = []
        asks = []

        if order_book is not None:
            for order in order_book:
                if order['a'] == 'BID':
                    bids.append([order['p'], order['v']])
                else:
                    asks.append([order['p'], order['v']])

        return {'lastUpdateId': int(dt.datetime.now().timestamp()),
                'bids': bids,
                'asks': asks}

    @staticmethod
    def parse_account_trade(trade, trading_pair) -> Dict[str, Any]:
        return {
            'side': 'BUY' if trade['a'] == 'BID' else 'SELL',
            'instrument_name': trading_pair,
            'fee': 0.0,
            'trade_id': trade.get('i', 0),
            'create_time': trade['t'],
            'traded_price': trade['p'],
            'traded_quantity': trade['q'],
            'fee_currency': 'DAI',
            'order_id': trade.get('oi', 0)
        }

    @staticmethod
    def parse_order(order, trading_pair):
        """
        order = {'i': '5fa128759522f40033ef41c8', 'a': 'BID', 'p': 78, 'q': 17, 'f': -3, 'm': True, 'cT': 1604397173, 'eT': 0}
        """
        return {
            "status": order['s'],
            'side': 'BUY' if order['a'] == 'BID' else 'SELL',
            "price": order['p'],
            "quantity": order['q'],
            "order_id": order['i'],
            "create_time": order['cT'],
            "type": "LIMIT",
            "instrument_name": trading_pair,
            "cumulative_quantity": order['q'] - abs(order['f']),
            "cumulative_value": (order['q'] - abs(order['f'])) * order['p'],
            "fee_currency": "DAI",
        }

    @staticmethod
    def parse_position(t, trading_pair):
        return {
            "currency": trading_pair,
            "balance": t['q'],
            "available": t['q'],
        }



class AccountOrders:
    def __init__(self):
        self.__orders = {}


    def update(self, orders, trading_pair, msg_type):
        r = []
        if msg_type == 'SET':
            for order in orders:
                order = Parser.parse_order(order, trading_pair)
                if order['status'] == 'PROCESSED':
                    order['status'] = 'ACTIVE'
                    self.__orders[order['order_id']] = order
                    r.append(order)
        # UPDATE
        else:
            for order in orders:
                order = Parser.parse_order(order, trading_pair)
                order_id = order['order_id']
                order_status = order['status']

                if order_status in {'CANCELED', 'FILLED'} and self.__orders.pop(order_id, None) is not None:
                    r.append(order)
                elif order_status in {'NEW', 'PROCESSED'} and order_id not in self.__orders:
                    order['status'] = 'OPEN'
                    self.__orders[order_id] = order
                    r.append(order)
        return r