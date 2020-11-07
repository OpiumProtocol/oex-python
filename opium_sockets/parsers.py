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
    def parse_order(t, trading_pair):
        print(f"t: {t}")
        """
        order = {'i': '5fa128759522f40033ef41c8', 'a': 'BID', 'p': 78, 'q': 17, 'f': -3, 'm': True, 'cT': 1604397173, 'eT': 0}
        """
        return {
            "status": t['s'],
            "side": "BUY",
            "price": t['p'],
            "quantity": t['q'],
            "order_id": t['i'],
            "create_time": t['cT'],
            "type": "LIMIT",
            "instrument_name": trading_pair,
            "cumulative_quantity": t['q'] - abs(t['f']),
            "cumulative_value": (t['q'] - abs(t['f'])) * t['p'],
            "fee_currency": "DAI",
        }

    @staticmethod
    def parse_position(t, trading_pair):
        return {
            "currency": trading_pair,
            "balance": t['q'],
            "available": t['q'],
        }


class OrdersState:
    def __init__(self):
        self.__orders = {}

    @staticmethod
    def __to_dict(orders: List) -> Dict:
        return {order['order_id']: order for order in orders}

    @staticmethod
    def __get_filled_orders(current_orders_ids: set, new_orders_ids: set) -> set:
        """
        orders which we had in current_orders and don't have in new_orders
        """
        return current_orders_ids.difference(new_orders_ids)

    @staticmethod
    def __get_new_orders(current_orders_ids: set, new_orders_ids: set) -> set:
        """
        orders which we don't have in current_orders and have in new_orders
        """
        return new_orders_ids.difference(current_orders_ids)

    def update(self, orders: List) -> List:
        orders = self.__to_dict(orders)

        # getting filled orders
        filled_orders_ids: set = self.__get_filled_orders(set(self.__orders.keys()),
                                                          set(orders.keys()))

        orders_to_send = []

        for id_ in filled_orders_ids:
            order = self.__orders.pop(id_)
            order['status'] = 'CANCELED'
            orders_to_send.append(order)

        # getting new orders
        new_orders_ids: set = self.__get_new_orders(set(self.__orders.keys()),
                                                    set(orders.keys()))

        for id_ in new_orders_ids:
            new_order = orders.pop(id_)
            new_order['status'] = 'ACTIVE'
            self.__orders[id_] = new_order
            orders_to_send.append(new_order)

        return orders_to_send


def orders_state_test():
    os = OrdersState()

    r = os.update([{'order_id': 1, 'val': 1}, {'order_id': 2, 'val': 2}])
    print(f"r: {r}")

    r = os.update([{'order_id': 2, 'val': 2}, {'order_id': 3, 'val': 3}])
    print(f"r: {r}")


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