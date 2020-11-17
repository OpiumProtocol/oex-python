from typing import List, Dict


# we don't use it anymore
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




def temp():
    async def listen_for_trades(self, trading_pair: str):
        """
        Convert a trade data into standard OrderBookMessage:
            "exchange_order_id": msg.get("d"),
            "trade_type": msg.get("s"),
            "price": msg.get("p"),
            "amount": msg.get("q")

        """

        ticker_hash = self._get_ticker_hash(trading_pair)

        delta: int = int(dt.timedelta(days=-5).total_seconds())

        last_ts: int = self.get_timestamp() - delta

        last_trade_tx: str = ''
        init = True
        # TODO: add queue

        async for trades in self.listen_for('trades:ticker:all',
                                            {'t': ticker_hash, 'c': await self.get_ticker_token(ticker_hash)}):

            if init:
                init = False
                t = trades[-1]
                last_trade_tx = t['tx']

            found_last_tx = False
            for t in reversed(trades):
                tx = t['tx']

                if found_last_tx:
                    # new trades
                    ts = self.get_timestamp()
                    last_trade_tx = tx
                    trade = {
                        'trading_pair': trading_pair,
                        'trade_type': 'na',
                        'exchange_order_id': t['tx'],
                        'update_id': self.get_timestamp(),
                        'price': t['p'],
                        'amount': t['q'],
                        'timestamp': self.get_timestamp()
                    }
                    yield trade

                if last_trade_tx == tx and found_last_tx is False:
                    found_last_tx = True
#
