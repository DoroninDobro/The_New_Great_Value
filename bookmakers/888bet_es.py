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


date_ = datetime.today().strftime('%Y-%m-%d')
# date_ = '2023-01-20'


class _888betES:

    BOOKIE = '888bet_es'
    MAIN_URL = 'https://www.888sport.es'
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
        # session.headers = {
        #     "Cookie": "888Attribution=1; 888Cookie=lang%3Des%26OSR%3D1927680; 888TestData=%7B%22orig-lp%22%3A%22https%3A%2F%2Fwww.888sport.es%2Ffutbol%2F%22%2C%22currentvisittype%22%3A%22Unknown%22%2C%22strategy%22%3A%22UnknownStrategy%22%2C%22strategysource%22%3A%22currentvisit%22%2C%22datecreated%22%3A%222023-07-14T07%3A47%3A10.039Z%22%2C%22expiredat%22%3A%22Fri%2C%2021%20Jul%202023%2007%3A47%3A00%20GMT%22%7D"
        # }
        session.headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
                                        " (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

        url = 'https://www.888sport.es/futbol/'
        async with session.get(url) as response:
            print(response.status)

        payloads = {
            'currency_code': 'EUR',
            'language': 'eng',
            'sub_brand_id': 110,
            'brand_id': 58,
            'marketing_brand_id': 1,
            'regulation_type_id': 2,
            'timezone': -4,
            'browsing_country_code': 'GEO',
            'product_package_id': 112,
            'user_mode': 'Anonymous',
            'spectate_timezone': 'Asia/Tbilisi',
            'device': 'PC',
            'region': 'tb',
            'theme_mode': 1,
        }
        session.headers['X-Spectateclient-V'] = "2.32"
        url = 'https://spectate-web.888sport.es/spectate/load/state'
        async with session.post(url, data=payloads) as response:
            print(response.status)
            print(response.headers)
            # print(await response.json())
        return session

    async def bound_live(self, sem, session, sport):
        url = f'https://spectate-web.888sport.es/spectate/sportsbook-req/getUpcomingEvents/{sport.lower()}/today'
        prematch = []
        try:
            session.headers['Cookies'] = 'bbsess=uT4dx4wZGorDm0mLqupPaKGt1An; lang=esp; anon_hash=475b63202e8b57d5f6c2da432f2b6190; odds_format=DECIMAL; _tgpc=ae412fc0-114c-5d56-91c1-e6b9a19cb66a; FPID=FPID2.2.9MI%2FF2rNoZdXIELzo6RgD8boWX%2FKoAiox6hwsOJaX%2F8%3D.1689319380; OptanonAlertBoxClosed=2023-07-14T07:23:22.127Z; _gcl_au=1.1.27785562.1689319402; OptanonConsent=isGpcEnabled=0&datestamp=Fri+Jul+14+2023+11%3A23%3A22+GMT%2B0400+(Georgia+Standard+Time)&version=202303.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=9e2fb34b-556b-4298-90ed-257f437f3190&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1; FPAU=1.2.376546524.1689319403; _fbp=fb.1.1689319402872.636181906; blueID=6d6f9b33-ee1a-495b-890d-8563905f1c4c; _scid=203c819f-0390-4361-91a5-bdba2f5a3e73; 888Attribution=1; 888Cookie=lang%3Des%26OSR%3D1927680; 888TestData=%7B%22orig-lp%22%3A%22https%3A%2F%2F888sport.es%2Fspectate%2Fsportsbook-req%2FgetUpcomingEvents%2F%22%2C%22currentvisittype%22%3A%22Unknown%22%2C%22strategy%22%3A%22UnknownStrategy%22%2C%22strategysource%22%3A%22currentvisit%22%2C%22datecreated%22%3A%222023-07-31T03%3A27%3A49.560Z%22%2C%22expiredat%22%3A%22Mon%2C%2007%20Aug%202023%2003%3A27%3A00%20GMT%22%7D; spectate_session=3f160981-dc4c-4b1c-949d-92ef739c9eeb%3Aanon; _ga=GA1.2.407405545.1689319380; _gid=GA1.2.1999622160.1690774071; _gat_UA-125725186-2=1; _uetsid=3b96bcb02f5211eebe3c237b57c6223c; _uetvid=93f730c0221711eea05afb61e3d41d1c; _tguatd={"sc":"(direct)"}; _tgidts={"sh":"d41d8cd98f00b204e9800998ecf8427e","ci":"3f0b2d4f-04a5-5eb1-976c-ad26aac533eb","si":"641314be-bc9f-5bd2-a797-bc7ab6ad2dce"}; _tglksd={"s":"641314be-bc9f-5bd2-a797-bc7ab6ad2dce","st":1690774072879,"sod":"(direct)","sodt":1689319381806,"sods":"o","sodst":1689324923837}; FPLC=LyCkxXCYHt0R%2FTm%2F5J02mTWlrGRivqyRPMM9StsCTJr2NvFvOsXu6KBlZTjQsVmfztZ105eKQ5fLZTvv4JXF5EkztDD92c7Z%2BpZL5fUhDSjsB%2FSKC08qKUHVKyaA4A%3D%3D; _tgsc=641314be-bc9f-5bd2-a797-bc7ab6ad2dce:-1; _ga_G49FQKZWH3=GS1.1.1690774070.4.1.1690774085.45.0.0; _tgsid={"lpd":"{\"lpu\":\"https://www.888sport.es%2Fspectate%2Fsportsbook-req%2FgetUpcomingEvents%2F\",\"lpt\":\"404%20La%20p%C3%A1gina%20no%20est%C3%A1%20disponible%20%E2%80%93%20888sport%E2%84%A2\"}","ps":"1567d556-16b2-42ff-a45d-d5ac50c529e0","ec":"3","pv":"1"}; _tgtim=641314be-bc9f-5bd2-a797-bc7ab6ad2dce:1690774075971:10'
            async with self.session.post(url) as response:
                prematch = await response.json()
                print(prematch)
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
            url = f"https://www.888sport.es{event.get('event_url')}-e-{event.get('id')}"
            country = event.get('category_name')
            match_id = event.get('id')
            match = event.get('name').replace(' v ', ' - ')
            sport_name = event.get('sport_slug').title()
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
    ps = _888betES()
    logging.info(f"Start 888bet.es scraper...")
    filename = '../cache/888bet_es_cache.json'

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
            raise e
            logging.error(f"{e}")
            time.sleep(120)
