from web3 import Web3


def wei_to_ether(wei: int) -> str:
    return str(Web3.fromWei(wei, 'ether'))
