import aiohttp
import datetime
import ujson

from urllib.parse import urlunparse
from uuid import uuid4

from asyncio import get_event_loop, sleep, wait
from aiohttp import web

DDOS_DELAY = 1.0

GLOBAL = 0

DEBUG = True


async def fetch(session, url):
    global DEBUG
    uid = str(uuid4())[-5:] if DEBUG else None
    start = datetime.datetime.now() if DEBUG else None
    if uid:
        print('Fetching: {}'.format(uid))
    async with session.get(url) as response:
        response_text = await response.text()
    if uid:
        finish = datetime.datetime.now() - start
        took = finish.total_seconds()
        print('Done fetching: {}.\nTook: {} s'.format(uid, took))

    return response_text


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
        for product in response:
            product_ticker = product[0]
            clear_data[product_ticker] = {}
            if product_ticker.startswith('t'):
                clear_data[product_ticker] = {
                    'bid': product[1],
                    'bid_size': product[2],
                    'ask': product[3],
                    'ask_size': product[4],
                    'daily_change': product[5],
                    'daily_change_perc': product[6],
                    'last_price': product[7],
                    'volume': product[8],
                    'high': product[9],
                    'low': product[10]
                }

            elif product_ticker.startswith('f'):
                clear_data[product_ticker] = {
                    'frr': product[1],
                    'bid': product[2],
                    'id_size': product[3],
                    'bid_period': product[4],
                    'ask': product[5],
                    'ask_size': product[6],
                    'ask_period': product[7],
                    'daily_change': product[8],
                    'daily_change_perc': product[9],
                    'last_price': product[10],
                    'volume': product[11],
                    'high': product[11],
                    'low': product[12]
                }
        return clear_data

    async def _clear_response(self, response):
        clean_data = {}
        for key, value in response.items():
            clean_data[key] = float(value)
        return clean_data

    async def _fetch_response(self, url='', delay=0.0):
        if delay:
            await sleep(delay)
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            json_response = await fetch(session, url)
            response = ujson.loads(json_response)
            return response

    async def ticker(self, currency='ALL'):
        symbols = await self.products()
        symbols = list(symbols.keys())
        symbols = ['t' + symbol.upper() for symbol in symbols]

        # FUNDING STATS ???
        symbols.append('fUSD')
        symbols.append('fBTC')
        symbols.append('fETH')

        symbols = ','.join(symbols)
        scheme = BitfinexDataAdapet.scheme
        netloc = BitfinexDataAdapet.network_location
        path = BitfinexDataAdapet.public_path_v2 + '/tickers'
        query = 'symbols=' + symbols
        params, fragment = '', ''

        url = urlunparse((scheme, netloc, path, params, query, fragment))

        response = await self._fetch_response(url=url)
        clean_data = await self._clear_v2_response(response)

        # This code works mostly as sequential (but had to work in parallel
        # if exchanges was not shit :)
        ###################################################################
        # scheme = BitfinexDataAdapet.scheme
        # netloc = BitfinexDataAdapet.network_location
        # path = BitfinexDataAdapet.public_path_v2 + '/tickers'
        # params, fragment = '', ''
        # fetch_task = []
        #
        # delay = 30.0
        # space = numpy.linspace(0.0, delay, num=len(symbols))
        #
        # for symbol, delay in zip(symbols, space):
        #     query = 'symbols=' + symbol
        #     url = urlunparse((scheme, netloc, path, params, query, fragment))
        #     fetch_task.append(self._fetch_response(url=url, delay=delay))
        #
        # done, pending = await wait(fetch_task)
        # result = [item.result() for item in done]
        #
        # clean_data = await self._clear_v2_response(result)

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
        response = ujson.loads(json_response)
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

    # def __init__(self, session=None):
    #     if session:
    #         self._session = session
    #     else:
    #         self._session = aiohttp.ClientSession()

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
        response = ujson.loads(json_response)
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
    # client_session = aiohttp.ClientSession()
    result = loop.run_until_complete(adapter.ticker())
    print(result)
