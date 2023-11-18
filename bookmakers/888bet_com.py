import logging
import time
from datetime import datetime
import json
import random

import asyncio
from aiohttp import ClientSession, CookieJar


import nest_asyncio
nest_asyncio.apply()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)

MAIN_LOOP = 1
limit_time = 12  # limit time in hours
mk = 1  # Today
date_ = datetime.today().strftime('%Y-%m-%d')
# date_ = '2023-01-20'


class _888bet:

    BOOKIE = '888bet'
    MAIN_URL = 'https://www.888sport.com'
    LIVE_URL = '='
    EXPAND_MODE = False
    USE_PROXY = 0
    WORKERS = 500
    SPECIALS = 'true'
    PRIMARY_ONLY = 'true'
    ALLOWED_SPORTS = [
            # 'Badminton',
            # 'Baseball',
            'Basketball',
            # 'Boxing',
            # 'E Sports',
            'Football',
            # 'Handball',
            # 'Hockey',
            # 'Rugby Union',
            # 'Snooker',
            # 'Soccer',
            # 'Tennis',
            # 'Volleyball'
                      ]


    def __init__(self):
        self.session = asyncio.run(self.get_cookies())

    async def get_session(self):
        session = ClientSession(cookie_jar=self.cookies_jar)
        return session

    async def get_cookies(self):
        session = ClientSession()
        session.headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
                                        " (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

        url = 'https://www.888sport.com/football/'
        async with session.get(url) as response:
            print(response.status)

        payloads = {
            'currency_code': 'EUR',
            'language': 'eng',
            'sub_brand_id': 8,
            'brand_id': 8,
            'marketing_brand_id': 1,
            'regulation_type_id': 4,
            'timezone': -4,
            'browsing_country_code': 'GEO',
            'product_package_id': 112,
            'user_mode': 'Anonymous',
            'spectate_timezone': 'Asia/Tbilisi',
            'device': 'PC',
            'region': 'tb',
            'theme_mode': 1,
        }
        session.headers['X-Spectateclient-V'] = "2.29"
        url = 'https://spectate-web.888sport.com/spectate/load/state'
        async with session.post(url, data=payloads) as response:
            print(response.status)
            print(response.headers)
        return session

    async def bound_live(self, sem, session, sport):
        url = f'https://spectate-web.888sport.com/spectate/sportsbook-req/getUpcomingEvents/{sport.lower()}/today'
        prematch = []
        print(session.headers)
        try:
            async with session.post(url) as response:
                prematch = await response.json()
        except OSError as e:
            logging.info(f'{e}')
        try:
            if len(prematch) == 0:
                return
        except TypeError:
            return
        prematches_list = await self.get_matches_list(sem, prematch)
        return prematches_list

    async def random_proxy(self):
        proxies = [
        ]
        return random.choice(proxies)

    async def get_matches_list(self, sem, data):
        matches_list = []
        for id_, event in data['events'].items():
            url = f"https://www.888sport.com{event.get('event_url')}-e-{event.get('id')}"
            country = event.get('category_name')
            match_id = event.get('id')
            match = event.get('name').replace(' v ', ' - ')
            sport_name = event.get('sport_name')
            league = event.get('tournament_name')
            kickoff = int(datetime.fromisoformat(event.get('start_time')).timestamp())
            betAttribute = {
                'info': {
                    'id': match_id,
                    'match': match,
                    'bookmaker': self.BOOKIE,
                    'league': league,
                    'country': country,
                    # 'match_id': match_id,
                    'sport': sport_name,
                    'checking_time': time.ctime(),
                    'unix_time': int(time.time()),
                    'kickoff': kickoff,
                    'url': url
                },
            }
            converted_m_list = []
            for num_of_outcomes, type_ in event.get('markets').items():
                if not type_['selections']:
                    continue
                for key_, one_bet in type_['selections'].items():
                    scanner_format_bet = await self.convert_to_scanner_format(one_bet, type_['name'], num_of_outcomes)
                    if scanner_format_bet is False:
                        continue
                    converted_m_list.append(scanner_format_bet)
            betAttribute['converted_markets'] = converted_m_list
            matches_list.append(betAttribute)
        return matches_list

    async def convert_to_scanner_format(self, bet, type_, num_of_outcomes):
        if type_ == "Full Time Result":
            if bet['type'] in ['1', 'X', '2']:
                if int(num_of_outcomes) == 3:
                    type_name = '1X2'
                return await self.return_scanner_format(type_name, f"{bet['type']}", float(bet['decimal_price']))
        elif type_ == "Point Spread":
            type_name = "Handicap(OT)"
            line = bet['special_odds_value']
            return await self.return_scanner_format(type_name, f"H{bet['type']}", float(bet['decimal_price']), line)
        elif type_ == "Total Points Over/Under":
            type_name = "Totals(OT)"
            line = bet['special_odds_value']
            return await self.return_scanner_format(type_name, bet['type'][:1], float(bet['decimal_price']), line)
        elif type_ == "Money Line":
            type_name = "12"
            return await self.return_scanner_format(type_name, bet['type'], float(bet['decimal_price']))
        elif type_ == "To Win Match":
            type_name = "12"
            return await self.return_scanner_format(type_name, bet['type'], float(bet['decimal_price']))
        else:
            return False

    @staticmethod
    async def return_scanner_format(type_name: str, type_: str, odds: float, line='0.0') -> dict:
        scanner_format = {
            'type_name': type_name,
            'type': type_,
            'line': line,
            'odds': odds
        }
        return scanner_format

    async def get_matches(self):
        tasks = []
        sem = asyncio.Semaphore(self.WORKERS)
        for sport in self.ALLOWED_SPORTS:
            try:
                task = asyncio.ensure_future(self.bound_live(sem, self.session, sport))
                tasks.append(task)
            except Exception as e:
                print(e)
        responses = await asyncio.gather(*tasks)
        matches = []
        for matches_ in responses:
            matches += matches_
        logging.info(f"{self.BOOKIE} has {len(matches)} events")
        return matches


if __name__ == '__main__':
    ps = _888bet()
    logging.info(f"Start 888bet.com scraper...")
    filename = '../cache/888bet_cache.json'

    while True:
        try:
            date_ = datetime.today().strftime('%Y-%m-%d')
            loopf = asyncio.get_event_loop()
            future = asyncio.ensure_future(ps.get_matches())
            loopf.run_until_complete(future)
            with open(filename, 'w') as f:
                json.dump(future.result(), f, indent=4)
            sleep_time = 10
            logging.info(f"{sleep_time} seconds sleep.")
            time.sleep(sleep_time)
        except Exception as e:
            # raise e
            logging.error(f"{e}")
            time.sleep(120)
