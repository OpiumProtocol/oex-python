from enum import IntEnum, Enum


class HttpMethod(IntEnum):
    get = 1
    post = 2


class OrderBookAction(Enum):
    ask = 'ASK'
    bid = 'BID'
