import datetime as dt
from typing import Dict, Any



class Parser:
    @staticmethod
    def parse_order_book(r: Dict[str, Any]) -> Dict[str, Any]:
        bids = []
        asks = []

        order_book = r.get('d')
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
