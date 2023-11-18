import aiohttp
import random
from typing import List


proxy_auth = aiohttp.BasicAuth('', '')  # login, password
proxy_token = ''

async def get_proxies(countries: str) -> List:
    async with aiohttp.ClientSession() as session_:
        url = 'https://proxy.webshare.io/api/v2/proxy/list/' \
              '?mode=direct' \
              '&page=1' \
              '&page_size=100,' \
              f'&country_code__in={countries}'
        async with session_.get(
                url, headers={"Authorization": proxy_token}) as response:
            proxies = await response.json()
    return proxies.get('results')


async def get_one_proxy(proxies: List) -> str:
    len_proxy = len(proxies)
    choice_1 = random.randint(0, len_proxy - 1)
    proxy = f"http://{proxies[choice_1].get('proxy_address')}:{proxies[choice_1].get('port')}"
    return proxy


async def get_scanner_format(type_name, type_, line, odds):
    scanner_format_bet = {
                        'type_name': type_name,
                        'type': type_,
                        'line': line,
                        'odds': odds
                    }
    return scanner_format_bet
