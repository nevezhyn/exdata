import os
import sys
import json

import aiohttp

from aiohttp import web


async def korea():
    url = 'https://api.bithumb.com/public/ticker/ALL'

    async with aiohttp.ClientSession() as session:
        json_str = await fetch(session, url)

    json_dict = json.loads(json_str)

    if json_dict['status'] != '0000':
        raise RuntimeError('Wrong response from exchange!')

    clean_data = {}

    for index, values in json_dict['data'].items():
        clean_data[index] = {}
        if index != 'date':
            for metric, metric_value in values.items():
                v = float(metric_value)
                clean_data[index][metric] = v
        else:
            clean_data[index] = float(values)

    return web.Response(text=json.dumps(clean_data))


async def wex():
    info_url = 'https://wex.nz/api/3/info'
    async with aiohttp.ClientSession() as session:
        pairs = await fetch(session, info_url)
    pairs_dict = json.loads(pairs)
    pairs = pairs_dict['pairs'].keys()
    ticker_url = 'https://wex.nz/api/3/ticker/'

    for pair in pairs:
        ticker_url += pair + '-'

    ticker_url = ticker_url[:-1]

    async with aiohttp.ClientSession() as session:
        json_str = await fetch(session, ticker_url)
    return web.Response(text=json_str)


EX_NAMES = {'kwn': korea, 'wex': wex}


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def ex_request(name):
    strategy = EX_NAMES[name]
    return await strategy()


async def handle(request):
    name = request.match_info.get('name', "Anonymous")

    if name not in EX_NAMES:
        if name == 'favicon.ico':
            return web.Response(status=404)
        raise RuntimeError('Only {} is allowed!'.format(EX_NAMES.keys()))

    return await ex_request(name)


app = web.Application()
app.router.add_get('/', handle)
app.router.add_get('/{name}', handle)
host = os.getenv('HOSTNAME')
web.run_app(app, host=host, port=8181)
