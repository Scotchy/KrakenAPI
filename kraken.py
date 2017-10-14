import requests
import time
import json

#Private queries
import base64
import urllib.parse
import hashlib
import hmac

class Api():
    def __init__(self):
        self.krak_url = "https://api.kraken.com"
        self.krak_version = "0"
        with open("datas/pairs", "r") as p:
            self.pairs = json.load(p)
        self.last_update_book = dict( (pair, 1) for pair in self.pairs )
        self.last_update_ohlc = dict( (pair, 1) for pair in self.pairs )
        self.last_update_spread = dict( (pair, 1) for pair in self.pairs )
        self.last_update_trades = dict( (pair, 1) for pair in self.pairs )
        self.server_time = 0
        self.key = ""
        self.secret = ""
        self.session = requests.Session()

    #------PUBLIC------
        
    def get_book(self, pair, count):
        """Get order book: get_book(pair, count, since = 0)"""
        url = "/" + self.krak_version + "/public/Depth"
        try:
            r = self.send_api_request(url, {"pair": pair, "count": str(count)})
            return r["result"][pair]
        except APIError as e:
            raise APIError(e.value)

    def get_server_time(self):
        """Get server timestamp: get_server_time()"""
        url = "/" + self.krak_version + "/public/Time"
        try:
            r = self.send_api_request(url)
            return r["result"]
        except APIError as e:
            raise APIError(e.value)

    def get_ticker_information(self, pair):
        """get_ticker_information(pair)"""
        url = "/" + self.krak_version + "/public/Ticker"
        try:
            r = self.send_api_request(url, {"pair": pair})
            return r["result"]
        except APIError as e:
            raise APIError(e.value)
        
        
    def get_ohlc_data(self, pair, interval, since = 0):
        """Get OHLC data, interval can take following values {5, 15, 30, 60, 240, 1440, 100080, 21600}
get_ohlc_data(pair, interval, since)"""
        url = "/" + self.krak_version + "/public/OHLC"
        try:
            if since == 0:
                r = self.get_ohlc_data(pair, interval, self.last_update_ohlc[pair])
                return r
            else:
                r = self.send_api_request(url, {"pair": pair, "interval": str(interval), "since": str(since)})
                self.last_update_ohlc[pair] = int(r["result"]["last"])
                return r["result"][pair]
        except APIError as e:
            raise APIError(e.value)
    
    def get_recent_spread_data(self, pair, since = 0):
        """get_recent_spread_data(pair, since = 0)"""
        url = "/" + self.krak_version + "/public/Spread"
        try:            
            if since == 0:
                r = self.get_recent_spread_data(pair, self.last_update_spread[pair])
                return r
            else:
                r = self.send_api_request(url, {"pair": pair, "since": str(since)})
                self.last_update_spread[pair] = int(r["result"]["last"])
                return r["result"][pair]
        except APIError as e:
            raise APIError(e.value)

    def get_recent_trades(self, pair, i=0):
        """get_recent_trades(self, pair, i=0)"""
        url = "/" + self.krak_version + "/public/Trades"
        try:
            if i == 0:
                r = self.get_recent_trades(pair, self.last_update_trades[pair])
                return r
            else:
                r = ""
                if self.last_update_trades[pair] != 1:
                    r = self.send_api_request(url, {"pair": pair, "since": str(i)})
                else:
                    r = self.send_api_request(url, {"pair": pair})
                self.last_update_trades[pair] = int(r["result"]["last"])
                return r["result"][pair]
        except APIError as e:
            raise APIError(e)
        
    def get_pairs(self):
        url = "/" + self.krak_version + "/public/AssetPairs"
        try:
            r = self.send_api_request(url)
            return r["result"]
        except APIError as e:
            raise APIError(e.value)
    #------PRIVATE------

    def add_order(self, pair, type2, ordertype, volume, price = None, price2 = None, leverage = "none", oflags = None, 
        starttm = "0", expiretm = "0", userref = None, validate = None, 
        close_ordertype = None, close_price = None, close_price2 = None):
        """https://api.kraken.com/0/private/AddOrder"""
        url = "/" + self.krak_version + "/private/AddOrder"

        if not type2 in ["buy", "sell"]:
            raise Exception("type must be 'buy' or 'sell'.")
        if not ordertype in ["market", "limit", "stop-loss", "take-profit", "stop-loss-profit", "stop-loss-profit-limit"
                            "stop-loss-limit", "take-profit-limit", "trailing-stop", "trailing-stop-limit", 
                            "stop-loss-and-limit", "settle-position"]:
            raise Exception("Invalid ordertype.")
        if not oflags in ["viqc", "fcib", "fciq", "nompp", "post"] and oflags != None:
            raise Exception("Invalid oflags.")

        data = {"pair" : pair, 
                "type": type2, 
                "ordertype" : ordertype, 
                "volume" : volume}

        if price != None:
            data["price"] = price
        if price2 != None:
            data["price2"] = price2
        if oflags != None:
            data["oflags"] = oflags
        if userref != None:
            data["userref"] = userref
        if validate != None:
            data["validate"] = validate
        if oflags != None:
            data["oflags"] = oflags

        if close_ordertype != None:
            data["close[ordertype]"] = close_ordertype
        if close_price != None:
            data["close[price]"] = close_price
        if close_price2 != None:
            data["close[price2]"] = close_price2

        print(data)
        r = self.send_private_api_request(url, data)
        
        return r

    def cancel_order(self, txid):
        """https://api.kraken.com/0/private/CancelOrder"""
        url = "/" + self.krak_version + "/private/CancelOrder"
        try:            
            data = {"txid" : txid}
            r = self.send_private_api_request(url, data)
        except APIError as e:
            raise APIError(e.value)
        return r
    
    def get_account_balance(self):
        """https://api.kraken.com/0/private/Balance"""
        url = "/" + self.krak_version + "/private/Balance"
        try:            
            r = self.send_private_api_request(url)
        except APIError as e:
            raise APIError(e.value)
        return r

    def get_trade_balance(self, aclass = "currency", asset = "ZUSD"):
        """https://api.kraken.com/0/private/TradeBalance"""
        url = "/" + self.krak_version + "/private/TradeBalance"
        try:            
            r = self.send_private_api_request(url, {"aclass" : aclass, "asset" : asset})
        except APIError as e:
            raise APIError(e.value)
        return r

    def get_open_orders(self, trades = "false", userref = None):
        """https://api.kraken.com/0/private/OpenOrders"""
        url = "/" + self.krak_version + "/private/OpenOrders"
        try:            
            r = self.send_private_api_request(url, {"trades" : trades})
            if userref != None:
                data["userref"] = userref
        except APIError as e:
            raise APIError(e.value)
        return r

    def get_closed_orders(self, ofs, trades = "false", userref = None, start = None, end = None, closetime = "both"):
        """https://api.kraken.com/0/private/ClosedOrders"""
        url = "/" + self.krak_version + "/private/ClosedOrders"
        try:            
            data = {"trades" : trades, 
                    "ofs" : ofs, 
                    "closetime" : closetime}
            if start != "":
                if end == "":
                    raise APIError("Start is set whereas end is not.")
                
                data["start"] = start
                data["end"] = end
            if userref != None:
                data["userref"] = userref

            r = self.send_private_api_request(url, data)
        except APIError as e:
            raise APIError(e.value)
        return r

    def query_orders_info(self, txid, trades = "false", userref = None):
        """https://api.kraken.com/0/private/QueryOrders"""
        url = "/" + self.krak_version + "/private/QueryOrders"
        
        try:
            if len(txid.split(",")) > 20:
                raise APIError("Too much transactions in txid (>20).")
            data = {"txid" : txid, "trades" : trades}
            if userref != None:
                data["userref"] = userref

            r = self.send_private_api_request(url, data)
        except APIError as e:
            raise APIError(e.value)
        return r

    def get_trades_history(self, ofs, type2 = "all", trades = "false", start = None, end = None):
        """https://api.kraken.com/0/private/TradesHistory"""
        url = "/" + self.krak_version + "/private/TradesHistory"
        try:            
            data = {"trades" : trades, 
                    "ofs" : ofs,
                    "type" : type2}
            if start != None:
                if end == None:
                    raise APIError("Start is set whereas end is not.")
                
                data["start"] = start
                data["end"] = end

            r = self.send_private_api_request(url, data)
        except APIError as e:
            raise APIError(e.value)
        return r

    def query_trades_info(self, txid, trades = "false"):
        """https://api.kraken.com/0/private/QueryTrades"""
        url = "/" + self.krak_version + "/private/QueryTrades"
        if len(txid.split(",")) > 20:
            raise APIError("Too much transactions in txid (>20).")
        try:            
            r = self.send_private_api_request(url, {"txid" : txid, "trades" : trades})
        except APIError as e:
            raise APIError(e.value)
        return r

    def get_open_positions(self, txid, docalcs = "false"):
        """https://api.kraken.com/0/private/OpenPositions"""
        url = "/" + self.krak_version + "/private/OpenPositions"
        if len(txid.split(",")) > 20:
            raise APIError("Too much transactions in txid (>20).")
        try:            
            r = self.send_private_api_request(url, {"txid" : txid, "docalcs" : docalcs})
        except APIError as e:
            raise APIError(e.value)
        return r

    def get_ledgers_infos(self, ofs, aclass = "currency", asset = "all", type2 = "all", start = None, end = None):
        """https://api.kraken.com/0/private/Ledgers"""
        url = "/" + self.krak_version + "/private/Ledgers"
        try:
            data = {"aclass" : aclass, 
                    "asset" : asset, 
                    "type2" : type, 
                    "ofs" : ofs}
            if start != None:
                if end == None:
                    raise APIError("Start is set whereas end is not.")
                
                data["start"] = start
                data["end"] = end

            r = self.send_private_api_request(url, data)
        except APIError as e:
            raise APIError(e.value)
        return r

    def query_ledgers(self, ids):
        """https://api.kraken.com/0/private/QueryLedgers"""
        url = "/" + self.krak_version + "/private/QueryLedgers"
        try:
            if len(txid.split(",")) > 20:
                raise APIError("Too much transactions in txid (>20).")
            data = {"id" : ids}
            r = self.send_private_api_request(url, data)
        except APIError as e:
            raise APIError(e.value)
        return r

    def get_trade_volume(self, pair = None, fee_info = None):
        """https://api.kraken.com/0/private/TradeVolume"""
        url = "/" + self.krak_version + "/private/TradeVolume"
        try:
            data = {}
            if pair != None:
                data["pair"] = pair
            if fee_info != None:
                data["fee-info"] = fee_info

            r = self.send_private_api_request(url, data)
        except APIError as e:
            raise APIError(e.value)
        return r

    #------UTILS------
    def send_api_request(self, path, post_data = {}):
        url = self.krak_url + path
        r = self.session.get(url, params = post_data)
        if r != "":
            r = r.json()
            if r["error"] != [] or not "result" in r.keys():
                raise APIError(r["error"])
            if r == "":
                raise APIError("Empty answer.")
        return r;

    def send_private_api_request(self, path, post_data = {}):
        if self.secret == "" or self.key == "":
            self.load_key();

        url =  self.krak_url + path 
        print(url)
        post_data["nonce"] = self._nonce()

        headers = {
            'API-Key': self.key,
            'API-Sign': self._sign(post_data, path)
        }
        
        r = self.session.post(url, data = post_data, headers = headers)
        if r != "":
            r = r.json()
            if r["error"] != [] or not "result" in r.keys():
                raise APIError(r["error"])
            if r == "":
                raise APIError("Empty answer.")
        return r;

    def load_key(self, key_files = "key.asc"):
        try:
            f = open(key_files, "r")
        except FileNotFoundError:
            raise Exception("File " + key_files + " does not exist. Unable to load api key and private key.")
        self.key = f.readline().strip()
        self.secret = f.readline().strip()
        if self.key == "" or self.secret == "":
            raise Exception("No api key or no private key in file " + key_files)
        f.close()

    def _nonce(self):
        """ Nonce counter.
        :returns: an always-increasing unsigned integer (up to 64 bits wide)
        """
        return int(1000*time.time())

    def _sign(self, data, urlpath):
        """ Sign request data according to Kraken's scheme.
        :param data: API request parameters
        :type data: dict
        :param urlpath: API URL path sans host
        :type urlpath: str
        :returns: signature digest
        """
        postdata = urllib.parse.urlencode(data)

        # Unicode-objects must be encoded before hashing
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        signature = hmac.new(base64.b64decode(self.secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())

        return sigdigest.decode()

    def close():
        self.session.close()


class APIError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
