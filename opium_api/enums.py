from enum import Enum


class HttpMethod(Enum):
    get = 'get'
    post = 'post'
    put = 'put'


class OrderBookAction(Enum):
    ask = 'ASK'
    bid = 'BID'


class TradeType(Enum):
    BUY = 1
    SELL = 2
