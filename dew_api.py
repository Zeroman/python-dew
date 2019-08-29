# coding=utf-8

import json
import requests
import time
import hashlib
from web3 import Account, Web3


class DewApi():
    def __init__(self, api_key, api_secret, key_store, key_pwd):
        self.api_key = api_key
        self.api_secret = api_secret
        self.key_store = key_store
        self.key_pwd = key_pwd

    def _format_result(self, res):
        obj = json.loads(res.text)
        if obj['success']:
            return obj['result']
        return res.text

    def get_url(self, method):
        return 'https://api.dew.one/api/v1/' + method

    def get_sign_str(self, params, api_secret):
        if 'tonce' not in params.keys():
            tonce = int(time.time() * 1000)
            params['tonce'] = tonce
        if 'apiKey' not in params.keys():
            params['apiKey'] = self.api_key

        sign_item = []
        for key in sorted(params):
            sign_item.append('%s=%s' % (key, params[key]))
        if api_secret is not None:
            sign_item.append("secretKey=%s" % api_secret)
        return '&'.join(sign_item)

    def eth_sign(self, params):
        sign_str = self.get_sign_str(params, None)
        message = Web3.toHex(Web3.sha3(text=sign_str))
        private_key = Account.decrypt(self.key_store, self.key_pwd)
        acct = Account.privateKeyToAccount(private_key)
        hash = acct.signHash(message)
        border = 'big'
        v = hash['v'].to_bytes(1, border)
        r = hash['r'].to_bytes(32, border)
        s = hash['s'].to_bytes(32, border)
        z = v + r + s
        sign = z.hex()
        params['presign'] = sign

    def md5_sign(self, params):
        sign_str = self.get_sign_str(params, self.api_secret)
        sign = hashlib.md5(sign_str.encode(encoding='UTF-8')).hexdigest()
        params['sign'] = sign

    def symbols(self):
        url = self.get_url("fut/symbols")
        params = {}
        self.md5_sign(params)
        res = requests.get(url, params=params)
        return self._format_result(res)

    def accounts(self):
        url = self.get_url("accounts")
        params = {}
        self.md5_sign(params)
        res = requests.get(url, params=params)
        return self._format_result(res)

    def ticker(self, symbol):
        url = self.get_url("ticker")
        params = {'symbol': symbol}
        self.md5_sign(params)
        res = requests.get(url, params=params)
        return self._format_result(res)

    def positions(self, symbol):
        url = self.get_url("fut/positions")
        params = {'symbol': symbol}
        self.md5_sign(params)
        res = requests.post(url, params=params)
        return self._format_result(res)

    def depth(self, symbol):
        url = self.get_url("depth")
        params = {'symbol': symbol, 'size': 30}
        self.md5_sign(params)
        res = requests.post(url, params=params)
        return self._format_result(res)

    def get_orders(self, symbol, size=30):
        url = self.get_url("fut/orders")
        params = {'symbol': symbol, 'size': size}
        self.md5_sign(params)
        res = requests.post(url, params=params)
        return self._format_result(res)

    def order(self, symbol, is_open, is_short, num, price):
        url = self.get_url("fut/trade")
        params = {'symbol': symbol, 'type': 'open' if is_open else 'close', 'side': 'sell' if is_short else 'buy', 'num': num,
                  'price': price}
        self.eth_sign(params)
        self.md5_sign(params)
        res = requests.post(url, params=params)
        return self._format_result(res)

    # 开多
    def order_open_long(self, symbol, num, price):
        self.order(symbol, True, False, num, price)

    # 开空
    def order_open_short(self, symbol, num, price):
        self.order(symbol, True, True, num, price)

    # 卖多
    def order_close_long(self, symbol, num, price):
        self.order(symbol, False, False, num, price)

    # 卖空
    def order_close_short(self, symbol, num, price):
        self.order(symbol, False, True, num, price)

    def cancel_orders(self, symbol, order_ids):
        url = self.get_url("fut/cancel")
        params = {'symbol': symbol, 'orderId': ','.join([str(order_id) for order_id in order_ids])}
        self.eth_sign(params)
        self.md5_sign(params)
        res = requests.post(url, params=params)
        return self._format_result(res)

    def margin_call(self, symbol, position_id, deposit):
        url = self.get_url("fut/margin_call")
        params = {'symbol': symbol, 'positionId': position_id, 'deposit': deposit}
        self.eth_sign(params)
        self.md5_sign(params)
        res = requests.post(url, params=params)
        return self._format_result(res)

    def margin_call_result(self, symbol, order_id):
        url = self.get_url("fut/margin_call_result")
        params = {'symbol': symbol, 'orderId': order_id}
        self.eth_sign(params)
        self.md5_sign(params)
        res = requests.post(url, params=params)
        return self._format_result(res)

    def fut_dones(self, symbol, order_ids=None, start_time=None, end_time=None):
        url = self.get_url("fut/dones")
        params = {'symbol': symbol}
        if order_ids is not None:
            params['orderId'] = ','.join([str(order_id) for order_id in order_ids])
        if start_time is not None:
            params['startTime'] = time.strftime(start_time, '%Y-%m-%d %H:%M:%S')
        if end_time is not None:
            params['endTime'] = time.strftime(end_time, '%Y-%m-%d %H:%M:%S')
        self.eth_sign(params)
        self.md5_sign(params)
        res = requests.post(url, params=params)
        return self._format_result(res)

    def stop_loss(self, symbol, is_cancel, position_id, earn_price, loss_price, tick):
        url = self.get_url("fut/stop_loss")
        params = {
            'symbol': symbol,
            'operType': 'CANCEL' if is_cancel else 'SET',
            'positionId': position_id,
        }
        if earn_price is not None:
            params['earnPrice'] = earn_price
        if loss_price is not None:
            params['lossPrice'] = loss_price
        if tick is not None:
            params['tick'] = tick
        self.eth_sign(params)
        self.md5_sign(params)
        res = requests.post(url, params=params)
        return self._format_result(res)


def print_json(obj, color=True):
    if isinstance(obj, str):
        obj = json.loads(obj)
    formatted_json = json.dumps(
        obj, indent=2, ensure_ascii=False, sort_keys=True)
    if color:
        from pygments import highlight, lexers, formatters
        formatted_json = highlight(
            formatted_json.encode('UTF-8'), lexers.JsonLexer(),
            formatters.TerminalFormatter())
    print(formatted_json)
