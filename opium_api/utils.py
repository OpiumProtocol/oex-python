from web3 import Web3


def wei_to_ether(wei: int, decimals: int = 18) -> str:
    # TODO: extend function for different decimals, by default
    return str(Web3.fromWei(wei, 'ether'))
