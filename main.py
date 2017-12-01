import aiohttp
import json

from aiohttp import web


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def main():
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, 'http://python.org')
        print(html)


async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    if name != 'kwn':
        if name == 'favicon.ico':
            return web.Response(status=404)
        raise RuntimeError('Only kwn is allowed!')

    url = 'https://api.bithumb.com/public/ticker/ALL'
    async with aiohttp.ClientSession() as session:
        async with aiohttp.ClientSession() as client_session:
            json_str = await fetch(client_session, url)
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


app = web.Application()
app.router.add_get('/', handle)
app.router.add_get('/{name}', handle)
web.run_app(app, host='exdata', port=8181)
