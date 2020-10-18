from setuptools import setup, find_packages

setup(
    name='opium-client',
    version='0.1',
    include_package_data=True,
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description='client for opium exchange',
    long_description=open('README.md').read(),
    install_requires=[
        'bitcoin==1.1.42',
        'cached-property==1.5.1',
        'certifi==2020.6.20',
        'chardet==3.0.4',
        'crypto==1.4.1',
        'cytoolz==0.10.1',
        'eth-abi==2.1.1',
        'eth-hash==0.2.0',
        'eth-typing==2.2.1',
        'eth-utils==1.9.5',
        'idna==2.10',
        'mypy-extensions==0.4.3',
        'Naked==0.1.31',
        'parsimonious==0.8.1',
        'py-ecc==4.0.0',
        'pycryptodome==3.9.8',
        'python-socketio==4.6.0',
        'PyYAML==5.3.1',
        'requests==2.24.0',
        'rlp==1.2.0',
        'shellescape==3.8.1',
        'six==1.15.0',
        'socketio==4.6.0',
        'urllib3==1.25.10',
        'web3==5.12.2'
    ],
    url='https://none',
)
