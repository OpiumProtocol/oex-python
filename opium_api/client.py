from decimal import Decimal, getcontext
from http import HTTPStatus
from typing import Optional, List, Union, Dict

import requests

from requests import Response

from libs.py_eth_sig_utils.signing import v_r_s_to_signature, sign_typed_data


from opium_api.enums import HttpMethod, OrderBookAction
from opium_api.constants import API_VERSION, API_HOST
from opium_api.exceptions import APIException, UnknownHttpMethod
from opium_api.utils import wei_to_ether


class OpiumClient:
    def __init__(self, public_key: str, private_key: str):
        if not private_key:
            raise ValueError('Empty "private_key"')
        if not public_key:
            raise ValueError('Empty "public_key"')


        self.__api_url: str = f'https://{API_HOST}/{API_VERSION}'
        self.__access_token: str = ''
        self.__private_key: bytes = bytes.fromhex(private_key)
        self.__public_key: str = public_key
        self.__traded_tickers: Dict[str, str] = self.get_traded_tickers()

    def get_public_key(self):
        return self.__public_key

    def get_traded_tickers(self) -> Dict[str, str]:
        """
        Get not expired tickers
        """
        r = requests.get(f'{self.__api_url}/tickers?expired=false')
        return {ticker['productTitle']: ticker['hash'] for ticker in r.json()}

    def get_ticker_token(self, ticker_hash: str) -> str:
        return requests.get(f'{self.__api_url}/tickers/data/{ticker_hash}').json()[0]['token']


    def __signe_message(self, msg: dict) -> str:
        return v_r_s_to_signature(*sign_typed_data(msg, self.__private_key)).hex()

    def generate_access_token(self):
        self.__access_token = self.__signe_message(self.__api_auth_logindata())
        return self.__access_token

    def __make_public_call(self,
                           endpoint: str,
                           method: HttpMethod,
                           headers: Optional[dict] = None,
                           arguments: Optional[dict] = None,
                           data: Union[Optional[dict], Optional[list]] = None) -> Response:
        headers = headers or dict()
        arguments = arguments or dict()
        data = data or dict()

        api_url = f'{self.__api_url}{endpoint}'

        if method == HttpMethod.get:
            ret = requests.get(url=api_url, headers=headers, params=arguments)

        elif method == HttpMethod.post:
            ret = requests.post(url=api_url, headers=headers, params=arguments, json=data)

        elif method == HttpMethod.put:
            ret = requests.put(url=api_url, headers=headers, params=arguments, json=data)

        else:
            raise UnknownHttpMethod

        return ret

    def __make_secure_call(self,
                           endpoint: str,
                           method: HttpMethod,
                           arguments: Optional[dict] = None,
                           data: Union[Optional[dict], Optional[list]] = None) -> Response:
        if not self.__access_token:
            self.generate_access_token()

        headers = {
            'Authorization': f'Bearer 0x{self.__access_token}'
        }

        return self.__make_public_call(endpoint=endpoint,
                                       method=method,
                                       headers=headers,
                                       arguments=arguments,
                                       data=data)

    def __api_auth_logindata(self) -> dict:
        """
        GET /auth/loginData
        """
        ret = self.__make_public_call(endpoint='/auth/loginData', method=HttpMethod.get)

        if ret.status_code != HTTPStatus.OK:
            raise APIException('Unable to get login data')

        return ret.json()

    def __api_wallet_balance_tokens(self) -> dict:
        """
        GET /wallet/balance/tokens
        """
        arguments = {
            'authAddress': self.__public_key
        }

        ret = self.__make_secure_call(endpoint='/wallet/balance/tokens',
                                      method=HttpMethod.get,
                                      arguments=arguments)

        # TODO: Ask @Alirun
        if ret.status_code == HTTPStatus.NO_CONTENT:
            raise APIException('Wallet NO CONTENT -- Not implemented')

        elif ret.status_code != HTTPStatus.OK:
            raise APIException('Unknown API error')

        return ret.json()

    def __api_orderbook_formorder(self,
                                  action: OrderBookAction,
                                  ticker_hash: str,
                                  currency_hash: str,
                                  price: Decimal,
                                  quantity: int,
                                  expires_at: int) -> List[dict]:
        """
        POST /orderbook/formOrder
        """
        arguments = {
            'authAddress': self.__public_key
        }

        getcontext().prec = 3

        data = {
            'action': action.value,
            'price': float(price),
            'ticker': ticker_hash,
            'quantity': quantity,
            'expiresAt': expires_at,
            'currency': currency_hash
        }

        ret = self.__make_secure_call(endpoint='/orderbook/formOrder',
                                      method=HttpMethod.post,
                                      arguments=arguments,
                                      data=data)
        # TODO:
        #   Status: 401 - Unauthorized
        #   Status: 403 - Forbidden
        #   Status: 422 - Unprocessable entity
        #   Status: 429 - Too many requests
        return ret.json()

    def __api_orderbook_orders(self, signed_orders: List[dict]):
        """
        POST /orderbook/orders
        """
        arguments = {
            'authAddress': self.__public_key
        }

        ret = self.__make_secure_call(endpoint='/orderbook/orders',
                                      method=HttpMethod.post,
                                      arguments=arguments,
                                      data=signed_orders)
        # TODO:
        #   Status: 201 - Created
        #   Status: 401 - Unauthorized
        #   Status: 403 - Forbidden
        #   Status: 404 - Not found
        #   Status: 409 - Conflict
        #   Status: 412 - Precondition Failed
        #   Status: 422 - Unprocessable entity
        #   Status: 429 - Too many requests
        return ret

    def __api_orderbook_cancel(self, order_ids: List[str]):
        """
        PUT /orderbook/cancel
        """
        arguments = {
            'authAddress': self.__public_key,
            'ids[]': order_ids
        }

        ret = self.__make_secure_call(endpoint='/orderbook/cancel',
                                      method=HttpMethod.put,
                                      arguments=arguments)

        if ret.status_code == HTTPStatus.UNAUTHORIZED:
            # TODO: Status: 401 - Unauthorized
            raise NotImplemented('__api_orderbook_cancel HTTPStatus.UNAUTHORIZED')
        elif ret.status_code == HTTPStatus.FORBIDDEN:
            # TODO: Status: 403 - Forbidden
            raise NotImplemented('__api_orderbook_cancel HTTPStatus.FORBIDDEN')
        elif ret.status_code == HTTPStatus.NOT_FOUND:
            # TODO: Status: 404 - Not found
            pass
        elif ret.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
            # TODO: Status: 422 - Unprocessable entity
            raise NotImplemented('__api_orderbook_cancel HTTPStatus.UNPROCESSABLE_ENTITY')
        elif ret.status_code != HTTPStatus.ACCEPTED:
            raise NotImplemented(f'__api_orderbook_cancel {ret.status_code}')

        return

    def __prepare_order(self,
                        action: OrderBookAction,
                        ticker_hash: str,
                        currency_hash: str,
                        price: Decimal,
                        quantity: int,
                        expires_at: int) -> List[dict]:
        orders_for_sign: List[dict] = self.__api_orderbook_formorder(action=action,
                                                                     ticker_hash=ticker_hash,
                                                                     currency_hash=currency_hash,
                                                                     price=price,
                                                                     quantity=quantity,
                                                                     expires_at=expires_at)
        if not orders_for_sign:
            # TODO: Ask @Alirun
            raise ValueError

        return orders_for_sign

    def __create_orders(self, orders: List[dict]) -> List[dict]:
        data = []

        # Convert str representation for uint256 to Python bigint
        for order in orders:
            for _t in order['orderToSign']['types'].values():
                for v in _t:
                    if v['type'] == 'uint256' and v['name'] in order['orderToSign']['message']:
                        order['orderToSign']['message'][v['name']] = int(order['orderToSign']['message'][v['name']])

            data.append({
                'id': order['id'],
                'signature': f'0x{self.__signe_message(order["orderToSign"])}'
            })

        ret = self.__api_orderbook_orders(signed_orders=data)

        return ret.json()

    def login(self):
        raise NotImplemented

    def get_balance(self) -> Dict:
        r = []
        for token in self.__api_wallet_balance_tokens():
            if token['title'] == 'ETH':
                total = wei_to_ether(int(token['total']))
            elif token.get('decimals') != 18:
                raise NotImplementedError(f"wey to {token['decimals']} decimals converter is not implemented")
            else:
                total = wei_to_ether(int(token['total']))

            r.append({'asset': token['title'], 'free': total})
        return {'balances': r}

    def create_order(self, instrument_name: str, side: str, price, quantity: str):
        action = OrderBookAction.bid if side == 'BUY' else OrderBookAction.ask

        ticker_hash = self.__traded_tickers[instrument_name]
        currency_hash = self.get_ticker_token(ticker_hash)
        # TODO: quantity is int here
        return self._send_order(action, ticker_hash, currency_hash, price, int(Decimal(quantity)),
                                expires_at=9999999999)

    def _send_order(self,
                    action: OrderBookAction,
                    ticker_hash: str,
                    currency_hash: str,
                    price: Decimal,
                    quantity: int,
                    expires_at: int):
        order = self.__prepare_order(action=action,
                                     ticker_hash=ticker_hash,
                                     currency_hash=currency_hash,
                                     price=price,
                                     quantity=quantity,
                                     expires_at=expires_at)
        # TODO: Think about return
        # [{'id': '5f2bb28fc90c490033f39a6f'}]
        return self.__create_orders(order)

    def cancel_order(self, order_ids: List[str]):
        # TODO: Think about return
        return self.__api_orderbook_cancel(order_ids=order_ids)
