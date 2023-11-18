import logging
import time
from datetime import datetime
import json
import random
import asyncio
import aiohttp

import nest_asyncio
nest_asyncio.apply()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)

date_ = datetime.today().strftime('%Y-%m-%d')
proxy_auth = aiohttp.BasicAuth('', '')  # login, password
proxy_token = ''


class Unibet:

    BOOKIE = 'Unibet'
    MAIN_URL = 'https://www.unibet.com'
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
        self.proxies = asyncio.run(self.get_proxies())

    async def get_proxies(self):
        async with aiohttp.ClientSession() as session_:
            url = 'https://proxy.webshare.io/api/v2/proxy/list/' \
                  '?mode=direct' \
                  '&page=1' \
                  '&page_size=100,' \
                  '&country_code__in=IT,FR,ES'
            async with session_.get(
                    url, headers={"Authorization": proxy_token}) as response:
                proxies = await response.json()
        return proxies.get('results')

    async def bound_live(self, sem, sport):
        url = f'https://spectate-web.888sport.com/spectate/sportsbook-req/getUpcomingEvents/{sport.lower()}/today'
        url = f'https://www.unibet.com/sportsbook-feeds/views/filter/{sport.lower()}/all/matches' \
              '?includeParticipants=true&useCombined=true'
        len_proxy = len(self.proxies)
        choice_1 = random.randint(0, len_proxy - 1)
        proxy = f"http://{self.proxies[choice_1]['proxy_address']}:{self.proxies[choice_1]['port']}"
        prematch = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, proxy_auth=proxy_auth, proxy=proxy) as response:
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
        for section in data.get('layout', {}).get('sections'):
            if section.get('position') == 'MAIN':
                for widget in section.get('widgets'):
                    if widget.get('widgetType') == "TOURNAMENT":
                        groups = widget.get('matches', {}).get('groups', [])

        matches_list = []
        for group in groups:
            country = group.get('englishName')
            if group.get('subGroups') is None:
                continue
            for subgroup in group.get('subGroups', []):
                league = subgroup.get('englishName')
                for event in subgroup.get('events'):
                    match_id = event.get('event', {}).get('id')
                    match = event.get('event', {}).get('englishName')
                    sport = event.get('event', {}).get('sport').lower().capitalize()
                    kickoff = event.get('event', {}).get('start')
                    # print(match_id, match, sport, kickoff, league, country)
                    url = f'https://www.unibet.com/betting/sports/event/{match_id}'
                    betAttribute = {
                        'info': {
                            'id': match_id,
                            'match': match,
                            'bookmaker': self.BOOKIE,
                            'league': league,
                            'country': country,
                            # 'match_id': match_id,
                            'sport': sport,
                            'checking_time': time.ctime(),
                            'unix_time': int(time.time()),
                            'kickoff': int(datetime.fromisoformat(kickoff.replace('Z', '')).timestamp()) + 10800,
                            'url': url
                        },
                    }
                    converted_m_list = []
                    for bet_offer in event.get('betOffers', []):
                        if bet_offer.get('suspended') is False:
                            for bet in bet_offer.get('outcomes', []):
                                scanner_format_bet = await self.convert_to_scanner_format(bet, bet_offer)
                                if scanner_format_bet is False:
                                    continue
                                converted_m_list.append(scanner_format_bet)
                            betAttribute['converted_markets'] = converted_m_list
                    matches_list.append(betAttribute)
        return matches_list

    async def convert_to_scanner_format(self, bet, whole_bet):
        if bet.get('status') == 'SUSPENDED':
            return False
        if whole_bet.get('criterion').get('englishLabel') == "Full Time":
            if bet['label'] in ['1', 'X', '2']:
                if len(whole_bet.get('outcomes', [])) == 3:
                    type_name = '1X2'
                return await self.return_scanner_format(type_name, f"{bet['label']}", bet['odds'] / 1000)
        elif whole_bet.get('betOfferType').get('englishName') == "Match":
            type_name = '12'
            if bet.get('type') == 'OT_ONE':
                type_ = f"1"
            elif bet.get('type') == 'OT_TWO':
                type_ = f"2"
            return await self.return_scanner_format(type_name, type_, bet['odds'] / 1000)
        elif whole_bet.get('criterion').get('englishLabel') == "Total Goals":
            type_name = "Totals"
            line = str(bet.get('line') / 1000)
            type_ = bet.get('label', 'n')[:1]
            return await self.return_scanner_format(type_name, type_, bet['odds'] / 1000, line)
        elif whole_bet.get('criterion').get('englishLabel') in \
                ["Game Handicap", "Handicap", 'Handicap - Including Overtime']:
            type_name = "Handicap(OT)"
            line = str(bet.get('line') / 1000)
            if bet.get('type') == 'OT_ONE':
                type_ = f"H1"
            elif bet.get('type') == 'OT_TWO':
                type_ = f"H2"
            return await self.return_scanner_format(type_name, type_, bet['odds'] / 1000, line)
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
                task = asyncio.ensure_future(self.bound_live(sem, sport))
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
    ps = Unibet()
    logging.info(f"Start Unibet.com scraper...")
    filename = '../cache/Unibet_cache.json'

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
