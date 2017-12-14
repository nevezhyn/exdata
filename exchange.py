import json
import aiohttp
from urllib.parse import urlunparse

from asyncio import get_event_loop, sleep

from aiohttp import web

DDOS_DELAY = 1.0

GLOBAL = 0


async def fetch(session, url):
    global GLOBAL
    headers = {'content-type': 'application/json'}
    GLOBAL += 1
    print('in fetch', GLOBAL)
    async with session.get(url, headers=headers) as response:
        return await response.text()


class AbstractDataAdapter():
    authority = ''

    def ticker(self):
        raise NotImplementedError

    def products(self):
        raise NotImplementedError

    def orderbook(self):
        raise NotImplementedError

    def latest_transactions(self):
        raise NotImplementedError


class BitfinexDataAdapet(AbstractDataAdapter):
    'https://api.bitfinex.com/v1/symbols_details'

    network_location = 'api.bitfinex.com'
    scheme = 'https'
    public_path_v1 = '/v1'
    public_path_v2 = '/v2'

    def __init__(self):
        pass

    async def _clear_v2_response(self, response):
        clear_data = {}
        for item in response:
            clear_data[item[0]] = {}
            clear_data[item[0]] = {'bid': item[1],
                                   'bid_size': item[2],
                                   'ask': item[3],
                                   'ask_size': item[4],
                                   'daily_change': item[5],
                                   'daily_change_perc': item[6],
                                   'last_price': item[7],
                                   'volume': item[8],
                                   'high': item[9],
                                   'low': item[10]}
        return clear_data

    async def _clear_response(self, response):
        clean_data = {}
        for key, value in response.items():
            clean_data[key] = float(value)
        return clean_data

    async def _fetch_response(self, url='', delay=0.0):
        if delay:
            sleep(delay)
        async with aiohttp.ClientSession() as session:
            json_response = await fetch(session, url)
        response = json.loads(json_response)
        return response

    async def ticker(self, currency='ALL'):
        symbols = await self.products()
        symbols = list(symbols.keys())
        symbols = ['t' + symbol.upper() for symbol in symbols]
        symbols = ','.join(symbols)

        scheme = BitfinexDataAdapet.scheme
        netloc = BitfinexDataAdapet.network_location
        path = BitfinexDataAdapet.public_path_v2 + '/tickers'
        query = 'symbols=' + symbols
        params, fragment = '', ''

        url = urlunparse((scheme, netloc, path, params, query, fragment))

        response = await self._fetch_response(url=url)
        clean_data = await self._clear_v2_response(response)

        return clean_data

    async def products(self):
        scheme = BitfinexDataAdapet.scheme
        netloc = BitfinexDataAdapet.network_location
        path = BitfinexDataAdapet.public_path_v1 + '/symbols_details'
        query, params, fragment = '', '', ''

        url = urlunparse((scheme, netloc, path, params, query, fragment))
        response = await self._fetch_response(url=url)

        products = {
            item['pair']:
                {'price_precision': item['price_precision'],
                 'initial_margin': float(item['initial_margin']),
                 'minimum_margin': float(item['minimum_margin']),
                 'maximum_order_size': float(item['maximum_order_size']),
                 'minimum_order_size': float(item['minimum_order_size']),
                 'expiration': item['expiration']}
            for item in response
        }

        # products = [
        #     "btcusd", "ltcusd", "ltcbtc", "ethusd", "ethbtc", "etcbtc",
        #     "etcusd",
        #     "rrtusd", "rrtbtc", "zecusd", "zecbtc", "xmrusd", "xmrbtc",
        #     "dshusd",
        #     "dshbtc", "bccbtc", "bcubtc", "bccusd", "bcuusd", "btceur",
        #     "xrpusd",
        #     "xrpbtc", "iotusd", "iotbtc", "ioteth", "eosusd", "eosbtc",
        #     "eoseth",
        #     "sanusd", "sanbtc", "saneth", "omgusd", "omgbtc", "omgeth",
        #     "bchusd",
        #     "bchbtc", "bcheth", "neousd", "neobtc", "neoeth", "etpusd",
        #     "etpbtc",
        #     "etpeth", "qtmusd", "qtmbtc", "qtmeth", "bt1usd", "bt2usd",
        #     "bt1btc",
        #     "bt2btc", "avtusd", "avtbtc", "avteth", "edousd", "edobtc",
        #     "edoeth",
        #     "btgusd", "btgbtc", "datusd", "datbtc", "dateth", "qshusd",
        #     "qshbtc",
        #     "qsheth", "yywusd", "yywbtc", "yyweth"]

        # return {product: {} for product in products}
        return products


class PoloniexDataAdapter(AbstractDataAdapter):
    network_location = 'poloniex.com'
    scheme = 'https'
    public_path = '/public'

    def __init__(self):
        pass

    async def _clear_response(self, response):
        clean_data = {}
        for pair, values in response.items():
            clean_data[pair] = {}
            for metric, metric_value in values.items():
                if metric == 'id':
                    continue
                clean_data[pair][metric] = float(metric_value)
        return clean_data

    async def _fetch_response(self, url=''):
        async with aiohttp.ClientSession() as session:
            json_response = await fetch(session, url)
        response = json.loads(json_response)
        return response

    async def ticker(self):
        scheme = PoloniexDataAdapter.scheme
        netloc = PoloniexDataAdapter.network_location
        path = PoloniexDataAdapter.public_path
        query = 'command=returnTicker'
        params, fragment = '', ''

        url = urlunparse((scheme, netloc, path, params, query, fragment))

        response = await self._fetch_response(url=url)
        clean_data = await self._clear_response(response)

        return clean_data

    async def products(self):
        scheme = PoloniexDataAdapter.scheme
        netloc = PoloniexDataAdapter.network_location
        path = PoloniexDataAdapter.public_path
        query = 'command=returnCurrencies'
        params, fragment = '', ''

        url = urlunparse((scheme, netloc, path, params, query, fragment))

        response = await self._fetch_response(url=url)
        return response


class BithumbDataAdaper(AbstractDataAdapter):
    network_location = 'api.bithumb.com'
    scheme = 'https'
    ticker_path = '/public/ticker/{currency}'
    orderbook_path = '/public/orderbook/{currency}'
    transactions_path = '/public/recent_transactions/{currency}'

    def __init__(self):
        pass

    async def _clear_response(self, response):
        clean_data = {}
        for index, values in response['data'].items():
            clean_data[index] = {}
            if index != 'date':
                for metric, metric_value in values.items():
                    v = float(metric_value)
                    clean_data[index][metric] = v
            else:
                clean_data[index] = float(values)
        return clean_data

    async def _fetch_response(self, url=''):
        async with aiohttp.ClientSession() as session:
            json_response = await fetch(session, url)
        response = json.loads(json_response)
        if response['status'] != '0000':
            # TODO: Logging module
            raise RuntimeError('Wrong response from exchange!')
        return response

    async def ticker(self, currency='ALL'):
        scheme = BithumbDataAdaper.scheme
        netloc = BithumbDataAdaper.network_location
        path = BithumbDataAdaper.ticker_path
        params, query, fragment = '', '', ''

        template = urlunparse((scheme, netloc, path, params, query, fragment))
        url = template.format(currency=currency)

        response = await self._fetch_response(url=url)
        clean_data = await self._clear_response(response)

        return clean_data

    def products(self):
        products = {'BTC': {}, 'ETH': {}, 'DASH': {}, 'LTC': {}, 'ETC': {},
                    'XRP': {}, 'BCH': {}, 'XMR': {}, 'ZEC': {}, 'QTUM': {},
                    'BTG': {}, 'ALL': {}}
        return products

    async def orderbook(self, currency='ALL'):
        scheme = BithumbDataAdaper.scheme
        netloc = BithumbDataAdaper.network_location
        path = BithumbDataAdaper.orderbook_path
        params, query, fragment = '', '', ''

        template = urlunparse((scheme, netloc, path, params, query, fragment))
        url = template.format(currency=currency)

        response = await self._fetch_response(url=url)
        clean_data = await self._clear_response(response)

        return clean_data

    async def latest_transactions(self, currency='BTC'):
        scheme = BithumbDataAdaper.scheme
        netloc = BithumbDataAdaper.network_location
        path = BithumbDataAdaper.transactions_path
        params, query, fragment = '', '', ''

        template = urlunparse((scheme, netloc, path, params, query, fragment))
        url = template.format(currency=currency)

        response = await self._fetch_response(url=url)
        clean_data = await self._clear_response(response)

        return clean_data


if __name__ == '__main__':
    loop = get_event_loop()
    adapter = BitfinexDataAdapet()
    result = loop.run_until_complete(adapter.ticker())
    print(result)
