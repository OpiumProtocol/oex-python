from pprint import pprint

from opium_api.connector import Connector

public_key = ...
private_key = ...


client = Connector(private_key, public_key)
print(client.get_balance())

arguments = {
    'authAddress': public_key,
}

r = client.make_secure_call('/trades/all/address', arguments=arguments)
pprint(r.json())

r = client.make_secure_call('/tickers', arguments=arguments)
pprint(r.json())

