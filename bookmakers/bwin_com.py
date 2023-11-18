import logging
import json
import time
import arrow
import datetime

import asyncio
import aiohttp
from aiohttp import ClientSession

from libs import bookmakers as bk

import nest_asyncio
nest_asyncio.apply()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)

MAIN_LOOP = 1
sport = 1

class BwinCom:

    BOOKIE = 'Bwin'
    MAIN_URL = 'https://bwin.com'
    EXPAND_MODE = False
    USE_PROXY = 1
    WORKERS = 200
    ALLOWED_SPORTS = [
        # 'Badminton',
        # 'Baseball',
        # 'Basketball',
        # 'Boxing',
        # 'E Sports',
        # 'Football',
        # 'Handball',
        # 'Hockey',
        # 'Rugby Union',
        # 'Snooker',
        'Football',
        # 'Tennis',
        # 'Volleyball'
    ]

    def __init__(self):
        self.proxies = asyncio.run(bk.get_proxies('GB,IT'))
        # self.headers = {'Request-Language': 'en'}
        self.proxy_auth = aiohttp.BasicAuth('', '')  # login, password
        self.headers = {"User-Agent": "Mozilla/5.0"}

    async def get_token(self) -> str:
        url = 'https://sports.bwin.com/en/api/clientconfig'
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url,
                    headers=self.headers,
                    proxy=await bk.get_one_proxy(self.proxies),
                    proxy_auth=self.proxy_auth,
                    timeout=20,
            ) as r:
                data = await r.json()
                token = data.get('msConnection').get('publicAccessId')
                return token

    async def get_matches(self, sport):
        token = await self.get_token()
        utc = arrow.utcnow()
        utc2 = utc.shift(hours=+24)
        url = 'https://sports.bwin.com/cds-api/bettingoffer/fixtures?' \
              f'x-bwin-accessid={token}' \
              f'&lang=en' \
              f'&country=GB' \
              f'&userCountry=GB' \
              f'&fixtureTypes=Standard&state=Latest' \
              f'&offerMapping=Filtered' \
              f'&offerCategories=Gridable' \
              f'&fixtureCategories=Gridable,NonGridable,Other' \
              f'&sportIds={await self.get_sport_id(sport)}' \
              f'&regionIds=' \
              f'&competitionIds=&conferenceIds=&isPriceBoost=false&statisticsModes=None' \
              f'&skip=0' \
              f'&take=1500' \
              f'&sortBy=Tags' \
              f"&from={utc.format('YYYY-MM-DDTHH:00:00')}.000Z" \
              f"&to={utc2.format('YYYY-MM-DDTHH:00:00')}.000Z"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        url,
                        proxy=await bk.get_one_proxy(self.proxies),
                        proxy_auth=self.proxy_auth,
                        timeout=20,
                ) as response:
                    data = await response.json()
        except OSError as e:
            logging.info(f'{e}')
            return
        matches_list = await self.get_matches_list(data, sport)
        logging.info(f"{self.BOOKIE} has {len(matches_list)} matches in {sport}")
        return matches_list

    @staticmethod
    async def get_sport_id(sport: str) -> int:
        sport_id = 4
        if sport == 'Football':
            sport_id = 4
        return sport_id

    @staticmethod
    async def convert_kickoff(kickoff_: str) -> int:
        kickoff_ = kickoff_.split('T')
        now = datetime.datetime.now()
        hour, minute = int(kickoff_[1].split(':')[0]), int(kickoff_[1].split(':')[1])
        year, month, day = kickoff_[0].split('-')
        kickoff = now.replace(year=int(year), month=int(month), day=int(day), hour=hour, minute=minute, second=0)
        kickoff = int(kickoff.timestamp()) + 10800
        return kickoff

    async def get_matches_list(self, data, sport):
        matches_list = []
        for event in data.get('fixtures'):
            id_ = event.get('id')
            match = event.get('name').get('value')
            league = event.get('competition', {}).get('name', {}).get('value')
            country = event.get('region', {}).get('name', {}).get('value')
            link = f"https://sports.bwin.com/en/sports/events/" \
                   f"{match.lower().replace(' - ', '-').replace(' ', '-')}-{event.get('id')}"
            kickoff = await self.convert_kickoff(event.get('startDate'))
            match_ = {
                'info': {
                    'bookmaker': self.BOOKIE,
                    'id': id_,
                    'url': link,
                    'match': match,
                    'sport': sport,
                    'country': country,
                    'league': league,
                    'kickoff': kickoff,
                },
                'converted_markets': []
            }
            markets = []
            for market in event.get('optionMarkets'):
                if market.get('name', {}).get('value') == "Match Result":
                    type_name = '1X2'
                    line = '0.0'
                elif market.get('name', {}).get('value') == "Total Goals":
                    type_name = 'Totals'
                    line = market.get('attr').replace(',', '.')
                elif market.get('name', {}).get('value') == "Both Teams To Score":
                    type_name = 'Both'
                    line = '0.0'
                else:
                    continue
                for outcome in market.get('options'):
                    if outcome.get('sourceName') is not None:
                        type_ = outcome.get('sourceName').get('value')
                    else:
                        type_ = outcome.get('name').get('value')
                    odds = outcome.get('price', {}).get('odds')
                    ctsf = {'type_name': type_name, 'type': type_[:1], 'line': line, 'odds': odds}
                    markets.append(ctsf)
            match_['converted_markets'] = markets
            matches_list.append(match_)
        return matches_list

    async def run(self):
        tasks = []
        sem = asyncio.Semaphore(self.WORKERS)
        async with ClientSession(trust_env=True) as session:
            for sport in self.ALLOWED_SPORTS:
                try:
                    task = asyncio.ensure_future(self.get_matches(sport))
                    tasks.append(task)
                except Exception as e:
                    print(e)
            responses = await asyncio.gather(*tasks)
            matches = []
            for response in responses:
                matches += response
                await asyncio.sleep(0)
            return matches


if __name__ == "__main__":
    launcher = BwinCom()
    logging.info(f"Start Bwin scraper...")
    filename = '../cache/Bwin_cache.json'
    while True:
        try:
            loop = asyncio.get_event_loop()
            future = asyncio.ensure_future(launcher.run())
            loop.run_until_complete(future)
            logging.info(f"Bwin {len(future.result())} matches found")

            # loopf = asyncio.get_event_loop()
            # future = asyncio.ensure_future(launcher.run(future.result()))
            # loopf.run_until_complete(future)
            with open(filename, 'w') as f:
                json.dump(future.result(), f, indent=4)

            sleep_time = 10
            logging.info(f"{sleep_time} seconds sleep.")
            time.sleep(sleep_time)
        except Exception as e:
            # raise e
            logging.error(f"{e}")
            time.sleep(10)