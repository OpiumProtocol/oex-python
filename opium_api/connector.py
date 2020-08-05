from http import HTTPStatus
from typing import Optional

import requests

from requests import Response

from libs.py_eth_sig_utils.signing import v_r_s_to_signature, sign_typed_data


from opium_api.enums import HttpMethod
from opium_api.constants import API_VERSION, API_HOST
from opium_api.exceptions import APIException, UnknownHttpMethod


class Connector:
    def __init__(self, private_key: str, public_key: str):
        if not private_key:
            raise ValueError('Empty "private_key"')
        if not public_key:
            raise ValueError('Empty "public_key"')

        self.__api_url: str = f'https://{API_HOST}/{API_VERSION}'
        self.__access_token: str = ''
        self.__private_key: bytes = bytes.fromhex(private_key)
        self.__public_key: str = public_key

    def __signe_message(self):
        raise NotImplemented

    def __generate_access_token(self):
        message_for_signing = self.__api_auth_logindata()
        self.__access_token = v_r_s_to_signature(*sign_typed_data(message_for_signing, self.__private_key)).hex()

    def __make_public_call(self,
                           endpoint: str,
                           method: HttpMethod,
                           headers: Optional[dict] = None,
                           arguments: Optional[dict] = None,
                           data: Optional[dict] = None) -> Response:
        headers = headers or dict()
        arguments = arguments or dict()
        data = data or dict()

        api_url = f'{self.__api_url}{endpoint}'

        if method == HttpMethod.get:
            ret = requests.get(url=api_url, headers=headers, params=arguments)

        elif method == HttpMethod.post:
            ret = requests.post(url=api_url, headers=headers, params=arguments, json=data)

        else:
            raise UnknownHttpMethod

        return ret

    def __make_secure_call(self,
                           endpoint: str,
                           method: HttpMethod,
                           arguments: Optional[dict] = None,
                           data: Optional[dict] = None) -> Response:
        if not self.__access_token:
            self.__generate_access_token()

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
        ret = self.__make_secure_call(endpoint='/auth/loginData', method=HttpMethod.get)

        if ret.status_code != HTTPStatus.OK:
            raise APIException('Unable to get login data')

        return ret.json()

    def __api_wallet_balance_tokens(self):
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

    def __api_orderbook_formorder(self):
        """
        POST /orderbook/formOrder
        """
        raise NotImplemented

    def __api_orderbook_orders(self):
        """
        POST /orderbook/orders
        """
        raise NotImplemented

    def __api_orderbook_cancel(self):
        """
        GET /orderbook/cancel
        """
        raise NotImplemented

    def __prepare_order(self):
        raise NotImplemented

    def __create_order(self):
        raise NotImplemented

    def login(self):
        raise NotImplemented

    def get_balance(self):
        # TODO: Think about return
        return self.__api_wallet_balance_tokens()

    def send_order(self):
        raise NotImplemented
