# coding=utf-8
import json
from datetime import datetime, timedelta
from json import JSONDecodeError

import requests
import time
import hashlib
from web3 import Account, Web3


class DewApiException(Exception):
    def __init__(self, err, msg):
        self._err = err
        self._msg = msg

    def __str__(self):
        return '%s: %s' % (self._err, self._msg)


class DewApi():
    def __init__(self, api_key, api_secret, key_store, key_pwd):
        self.api_key = api_key
        self.api_secret = api_secret
        self.key_store = key_store
        self.key_pwd = key_pwd
        self.api_lang = 'en'  # or zh_cn
        self.last_access_time = datetime.now()
        self._pub_headers = {
            "Dew-Dev": "Web:web.dew.com",
            "Dew-Nw": "unknown",
            "Dew-Sign": "",
            "Dew-Spec": "1.0",
            "Dew-Token": "",
            "Dew-Uid": "0",
            "Dew-Ver": "0.0.0",
        }

    def _format_result(self, res):
        try:
            obj = json.loads(res.text)
            if obj['success']:
                return obj['result']
            else:
                raise DewApiException('server error', res.text)
        except JSONDecodeError:
            raise DewApiException('JSONDecodeError', res.text)

    def _to_json_param(self, req):
        return json.dumps(req, separators=(',', ':'))

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
            value = params[key]
            sign_item.append('%s=%s' % (key, value))
        if api_secret is not None:
            sign_item.append("secretKey=%s" % api_secret)
        return '&'.join(sign_item)

    def eth_sign(self, params):
        sign_str = self.get_sign_str(params, None)
        # print(sign_str)
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

    def tonce(self):
        url = self.get_url("tonce")
        res = requests.get(url)
        return self._format_result(res)

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

    def positions(self, symbol=None):
        url = self.get_url("fut/positions")
        params = {}
        if symbol is not None:
            params['symbol'] = symbol
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
        return self.order(symbol, True, False, num, price)

    # 开空
    def order_open_short(self, symbol, num, price):
        return self.order(symbol, True, True, num, price)

    # 平多
    def order_close_long(self, symbol, num, price):
        return self.order(symbol, False, False, num, price)

    # 平空
    def order_close_short(self, symbol, num, price):
        return self.order(symbol, False, True, num, price)

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
            params['startTime'] = start_time.strftime('%Y-%m-%d %H:%M:%S')
        if end_time is not None:
            params['endTime'] = end_time.strftime('%Y-%m-%d %H:%M:%S')
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

    # start_time end_time单位是天，不建议时间跨度太大，resolution单位是分钟
    def get_kline_data(self, symbol='BTC', start_time=None, end_time=None, resolution=1):
        url = 'https://hq.biz.dew.one/pub/quotation-new/kdata.jhtml'
        if start_time is None:
            start_time = datetime.now()
        if end_time is None:
            end_time = start_time
        params = {
            'code': symbol,
            'resolution': resolution,
            'startTime': int(start_time.timestamp()),
            'endTime': int(end_time.timestamp()),
            'market': "MATCH_QH",
            'lang': self.api_lang,
            'reqType': 'INIT'
        }
        # print(params)
        res = requests.get(url, params=params, headers=self._pub_headers)
        return self._format_result(res)

    def get_guess_tickers(self, period='5m'):
        url = 'https://guess.biz.dew.one/pub/query/codes.jhtml'
        params = {
            'period': period,
            'lang': self.api_lang,
        }
        # print_json(params)
        res = requests.get(url, params=params, headers=self._pub_headers)
        return self._format_result(res)

    def get_guess_data(self, symbol="BTC", currency='DEW', period='5m', end_time=None, page=1):
        url = 'https://guess.biz.dew.one/pub/query/historys.jhtml'
        if end_time is None:
            end_time = datetime.now()
        minutes = end_time.minute % 5
        end_time -= timedelta(minutes=minutes)
        date_str = end_time.strftime('%Y%m%d%H%M00')
        params = {
            # 'BTC-DEW-5m-20190831173000',
            'code': "%s-%s-%s-%s" % (symbol, currency, period, date_str),
            'page': page,
            'lang': self.api_lang,
        }
        # print_json(params)
        res = requests.get(url, params=params, headers=self._pub_headers)
        return self._format_result(res)

    def guess_category(self):
        url = self.get_url("guess/category")
        params = {}
        self.md5_sign(params)
        res = requests.get(url, params=params)
        return self._format_result(res)

    def guess_trade(self, symbol, currency, period, is_bull, num):
        url = self.get_url("guess/trade")
        params = {
            'symbol': symbol.upper(),
            'currency': currency.upper(),
            'period': period,
            'type': 'BULL' if is_bull else 'BEAR',
            'num': num
        }
        self.eth_sign(params)
        self.md5_sign(params)
        # print_json(params)
        res = requests.post(url, params=params)
        return self._format_result(res)

    # orders = [[symbol, currency, period, is_bull, num],[...]]
    def guess_trade_batch(self, orders=[]):
        url = self.get_url("guess/trade_batch")
        _orders = []
        for index, order in enumerate(orders):
            _order = {
                'index': index + 1,
                'symbol': order[0].upper(),
                'currency': order[1].upper(),
                'period': order[2],
                'type': 'BULL' if order[3] else 'BEAR',
                'num': order[4],
            }
            _orders.append(_order)
        params = {"orders": self._to_json_param(_orders)}
        self.eth_sign(params)
        self.md5_sign(params)
        print_json(params)
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
