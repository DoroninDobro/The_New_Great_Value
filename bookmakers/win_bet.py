import logging
import json
import time
import random

import asyncio
import aiohttp
from aiohttp import ClientSession

import nest_asyncio
nest_asyncio.apply()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)

API_URL = 'https://1win.direct/microservice/ask'
proxy_auth = aiohttp.BasicAuth('', '')  # login, password
proxy_token = ''


class WinBet:
    BOOKIE = '1win'
    MAIN_URL = 'https://1win.ru'

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
        self.TOURNAMENTS = asyncio.run(self.get_tournament())
        self.COUNTRIES = asyncio.run(self.get_countries())
        self.proxies = asyncio.run(self.get_proxies())

    async def get_proxies(self):
        async with ClientSession() as session_:
            url = 'https://proxy.webshare.io/api/v2/proxy/list/' \
                  '?mode=direct' \
                  '&page=1' \
                  '&page_size=100,' \
                  '&country_code__in=IT,FR,ES,DE,BE'
            async with session_.get(
                    url, headers={"Authorization": proxy_token}) as response:
                proxies = await response.json()
        return proxies.get('results')

    async def get_tournament(self):
        while True:
            async with ClientSession() as session:
                proxy_auth = aiohttp.BasicAuth('', '')  # login, password
                url = 'https://1win.direct/microservice/ask'
                payload = {
                    "name": "MATCH-STORAGE-PARSED:tournaments-list",
                    "payload": {"localeId": 31, "lang":"en", "service": "prematch"}
                }
                async with session.post(
                        API_URL, json=payload, proxy="http://156.238.5.176:5517", proxy_auth=proxy_auth) as response:
                    res = await response.json()
                tournaments = []
                for tournament in res['tournaments']:
                    if tournament['sportId'] == 18:
                        tournaments.append(tournament)
                if len(tournaments) > 0:
                    break
        return tournaments

    async def get_countries(self):
        async with ClientSession() as session:
            proxy_auth = aiohttp.BasicAuth('', '')  # login, password
            payload = {"name": "MATCH-STORAGE-PARSED:categories-list", "payload": {"lang": "en", "service": "prematch"}}
            async with session.post(
                    API_URL, json=payload, proxy="http://156.238.5.176:5517", proxy_auth=proxy_auth) as response:
                res = data_ = await response.json()
            countries = []
            for cat in res['categories']:
                if cat['sportId'] == 18 or cat['sportId'] == 23 or cat['sportId'] == 27:
                    countries.append(cat)
        return countries

    async def bound_live(self, sem, session, league_id):
        prematch = []
        try:
            prematch = await self.get_live_(sem, session, league_id)
        except OSError as e:
            logging.info(f'{e}')
        try:
            if len(prematch) == 0:
                return
        except TypeError:
            return
        prematches_list = await self.get_matches_list(sem, prematch)
        return prematches_list

    async def get_live_(self, sem, session, league_id):
        async with sem:
            payload = {
                "name": "MATCH-STORAGE-PARSED:matches-list",
                "payload": {
                    "lang": "en",
                    "localeId": 31,
                    "service": "prematch",
                    "timeFilter": {
                        "date": False,
                        "hoursToStart": 10
                    },
                    "categoryId": league_id,
                    "onlyOutrights": False
                }
            }

            logging.debug(f'Following {API_URL}')
            try:
                proxy_auth = aiohttp.BasicAuth('', '')  # login, password
                async with session.post(API_URL, timeout=30, json=payload, proxy="http://156.238.5.176:5517",
                                        proxy_auth=proxy_auth) as response:
                    data_ = await response.json()
                return data_
            except Exception as e:
                logging.debug(e)
                logging.warning(f'Could not get all live list')
                return

    async def get_matches_list(self, sem, live_list):
        matches_list = []
        for i, d in enumerate(live_list['matches']):
            # print(d)
            url = f"https://1wpyun.xyz/bets/prematch/{d.get('sportId')}/" \
                  f"{d.get('categoryId')}/{d.get('tournamentId')}/{d['id']}"
            try:
                league = [x['name'] for x in self.TOURNAMENTS if d['tournamentId'] == x['id']][0]
            except IndexError:
                league = None
            try:
                matches_list.append(
                    [d['id'],  # local id
                     f"{d['homeTeamName']} - {d['awayTeamName']}",  # match name
                     url,  # event url
                     league,  # Champ name
                     await self.get_sport_by_id(d.get('sportId')),  # sport name
                     [x['name'] for x in self.COUNTRIES if d['categoryId'] == x['id']][0],
                     self.BOOKIE,  # bookie
                     d.get('baseOdds'),
                     d.get('dateOfMatch')
                     ])
            except KeyError:
                # raise
                logging.error(f'd: {d}')
                continue
            # print(matches_list)
        return matches_list

    @staticmethod
    async def get_sport_by_id(id_):
        sport = ''
        if id_ == 18:
            sport = 'Soccer'
        elif id_ == 23:
            sport = 'Basketball'
        elif id_ == 27:
            sport = 'Volleyball'
        elif id_ == 35:
            sport = 'Hockey'
        return sport

    async def bound_fetch(self, sem, session, match):
        async with sem:
            response = {'odds': []}
            payload = {
                "name": "MATCH-STORAGE-PARSED:odds-list",
                "payload": {"providerId": 1, "lang": "en", "localeId": 31, "service": "prematch",
                            "matchId": str(match[0])
                            }
            }
            url = 'https://1win.direct/microservice/ask'
            # response = await self.fetch(url, payload, session)
            # print(response)

            try:
                betAttribute = {
                    'match_id': match[0],
                    'info': {
                        'bookmaker': self.BOOKIE,
                        'match_id': match[0],
                        'match': match[1],
                        'sport': match[4],
                        'country': match[5],
                        'league': match[3],
                        'url': match[2],
                        'kickoff': match[8]
                    },
                }
                converted_m_list = []
                if response.get('odds') is not None:
                    if match[7] is None:
                        markets = [] + response.get('odds')
                    else:
                        markets = match[7] + response['odds']
                else:
                    markets = match[7]
                for i, one_bet in enumerate(markets):
                    # print(one_bet)
                    ctsf = await self.convert_to_scanner_format(one_bet, match[4])
                    if ctsf is False:
                        continue
                    scanner_format_bet = {
                        'type_name': ctsf['type_name'],
                        'type': ctsf['type'],
                        'line': ctsf['line'],
                        'odds': ctsf['odds'],
                        'market-id': ctsf['market_id']
                    }
                    converted_m_list.append(scanner_format_bet)
            except Exception as e:
                raise e
            except AttributeError:
                logging.debug('AttributeError')
                return
            except ValueError:  # includes simplejson.decoder.JSONDecodeError
                logging.debug('Decoding JSON has failed')
                return
            except TypeError:
                logging.debug("TypeError: 'NoneType' object is not subscriptable")
                return
            except KeyError:
                logging.debug("KeyError: 'markets'")
                return
            betAttribute['converted_markets'] = converted_m_list
            # print(betAttribute)
            return betAttribute

    async def convert_to_scanner_format(self, one_bet, sport):
        ot = ''
        add_to_type = ''
        add_to_type_name = ''
        add_to_end_type_name = ''
        if one_bet['group'] in [6481, 6483]:
            add_to_end_type_name = "(Corners)"
        if one_bet['group'] in [6476, 6478]:
            add_to_end_type_name = "(Yellow cards)"
        if 7 in one_bet['subGamesId']:
            add_to_type = '1H'
            add_to_type_name = 'First Half '
        if 8 in one_bet['subGamesId'] or one_bet['blocked'] is True:
            return False
        if sport == 'Basketball':
            ot = '(OT)'
        if one_bet['name'] in ['W1', 'X', 'W2']:
            if sport == 'Basketball' and one_bet['type'] != "401":
                return False
            type_name = '12'
            if sport == 'Soccer':
                type_name = '1X2'

            if one_bet['outCome'] == 'x':
                one_bet['outCome'] = 'X'
            return {
                    'type_name': f"{add_to_type_name}{type_name}{add_to_end_type_name}",
                    'type': f"{add_to_type}{one_bet['outCome']}",
                    'line': '0.0',
                    'odds': one_bet['coefficient'],
                    'market_id': one_bet['id']
            }

        if one_bet['outCome'] == 'under':
            return {
                    'type_name': f"Totals{ot}{add_to_end_type_name}",
                    'type': f"{add_to_type}U",
                    'line': one_bet['specialValue'],
                    'odds': one_bet['coefficient'],
                    'market_id': one_bet['id']
            }
        if one_bet['outCome'] == 'over':
            return {
                    'type_name': f"Totals{ot}{add_to_end_type_name}",
                    'type': f"{add_to_type}O",
                    'line': one_bet['specialValue'],
                    'odds': one_bet['coefficient'],
                    'market_id': one_bet['id']
            }

        if one_bet['type'] in ['7', '8', '3829', '3830']:

            return {
                    'type_name': f"Handicap{ot}",
                    'type': f"{add_to_type}H{one_bet['outCome']}",
                    'line': one_bet['specialValue'],
                    'odds': one_bet['coefficient'],
                    'market_id': one_bet['id']
            }


        else:
            return False

    async def fetch(self, url, payload, session):
        proxy = random.choice(self.proxies)
        proxy = f"http://{proxy['proxy_address']}:{proxy['port']}"
        try:
            async with session.post(
                    url,
                    json=payload,
                    timeout=20,
                    proxy_auth=proxy_auth,
                    proxy=proxy,
                    ) as response:
                resp = await response.json()
                return resp
        except Exception as e:
            logging.debug(e)
            return

    def get_sport_id(self, sport_name):
        sports_id = {
            'Football': 1,
            'Tennis': 33,
            'Basketball': 3,
            # 'Football': 15,
            # 'Baseball': 3,
            'Golf': 17,
            'Hockey': 19,
            'Volleyball': 34,
            'Mixed Martial Arts': 22,
            'Handball': 18,
            'E Sports': 12,
            'Badminton': 1,
            'Boxing': 6,
            'Politics': 24,
            'Rugby Union': 27,
            'Snooker': 28,
            'Alpine Skiing': 40,
            'Biathlon': 41,
            'Ski Jumping': 42,
            'Formula 1': 44,
            'Chess': 7,
            'Entertainment': 58
        }
        return sports_id[sport_name]

    async def run(self, matches):
        tasks = []
        sem = asyncio.Semaphore(self.WORKERS)
        async with ClientSession(trust_env=True) as session:
            try:
                for match in matches:
                    task = asyncio.ensure_future(self.bound_fetch(sem, session, match))
                    tasks.append(task)
            except Exception as e:
                print(e)
            responses = await asyncio.gather(*tasks)
        return responses

    async def get_live(self):
        tasks = []
        sem = asyncio.Semaphore(self.WORKERS)
        async with ClientSession() as session:
            # aiohttp.BasicAuth('nwebznfk', 'fi5c9d9ldvc9')
            for league_id in list(map(lambda x: x['id'], self.COUNTRIES)):
                # league = self.get_sport_id(sport_)
                try:
                    task = asyncio.ensure_future(
                        self.bound_live(
                            sem, session, league_id
                        ))
                    tasks.append(task)
                    await asyncio.sleep(0.1)
                except Exception as e:
                    raise e
                    print(e)
            responses = await asyncio.gather(*tasks)
        matches = []
        for i, m in enumerate(responses):
            # print(m[0])
            if m is None:
                m = []
            matches += m
        matches_ = []
        for m in matches:
            if m == 0:
                continue
            matches_.append(m)
            # print(matches)
        logging.info(f"1win has {len(matches_)} matches")
        return matches_

if __name__ == "__main__":
    launcher = WinBet()
    logging.info("Start 1Win scraper...")
    filename = '../cache/1win_cache.json'
    while True:
        try:
            loop = asyncio.get_event_loop()
            future = asyncio.ensure_future(launcher.get_live())
            loop.run_until_complete(future)
            logging.info(f"{len(future.result())} matches found")

            loopf = asyncio.get_event_loop()
            future = asyncio.ensure_future(launcher.run(future.result()))
            loopf.run_until_complete(future)
            with open(filename, 'w') as f:
                json.dump(future.result(), f)

            sleep_time = 30
            logging.info(f"{sleep_time} seconds sleep.")
            time.sleep(sleep_time)
        except Exception as e:
            # raise
            logging.error(f"{e}")
            time.sleep(120)
