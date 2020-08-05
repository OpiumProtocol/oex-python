from opium_api.constants import API_VERSION, API_HOST


class Connector:
    def __init__(self, private_key: str, public_key: str):
        if not private_key:
            raise ValueError('Empty "private_key"')
        if not public_key:
            raise ValueError('Empty "public_key"')

        self.__access_token: str = ''
        self.__private_key: bytes = bytes.fromhex(private_key)
        self.__public_key: str = public_key

    def __signe_message(self):
        raise NotImplemented

    def __make_secure_call(self):
        raise NotImplemented

    def __make_public_call(self):
        raise NotImplemented

    def __api_auth_logindata(self):
        """
        GET /auth/loginData
        """
        raise NotImplemented

    def __api_wallet_balance_tokens(self):
        """
        GET /wallet/balance/tokens
        """
        raise NotImplemented

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
        raise NotImplemented

    def send_order(self):
        raise NotImplemented
