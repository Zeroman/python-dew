#!/usr/bin/env python
# -*- coding: utf-8 -*-


from dew_api import DewApi, print_json

def get_test_user_api():
    apiKey = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    apiSecret = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    keyStore = '{"version":3,"id":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","address":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","crypto":{"ciphertext":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","cipherparams":{"iv":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"},"cipher":"aes-128-ctr","kdf":"scrypt","kdfparams":{"dklen":32,"salt":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","n":262144,"r":8,"p":1},"mac":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}}'
    keyStorePwd = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    api = DewApi(apiKey, apiSecret, keyStore, keyStorePwd)
    return api


if __name__ == '__main__':
    api = get_test_user_api()
    symbol = "BTC-YX"
    print_json(api.accounts())
    print_json(api.ticker(symbol))
    print_json(api.positions(symbol))
    print_json(api.depth(symbol))
    print_json(api.order_open_long(symbol, 1, 9000))
    print_json(api.get_orders(symbol))
    print_json(api.cancel_orders(symbol, [162462923, 162483767, 162467609]))
    print_json(api.get_orders(symbol))

