import re
import logging
import json
import time
import math
import datetime

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from aiohttp import ClientSession

from libs import helper
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

class BetfairCom:

    BOOKIE = 'Betfair'
    MAIN_URL = 'https://betfair.com'
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
        self.proxies = asyncio.run(bk.get_proxies('GB'))
        # self.headers = {'Request-Language': 'en'}
        self.proxy_auth = aiohttp.BasicAuth('', '')  # login, password

    async def get_matches(self, sport):
        url = f'https://www.betfair.com/sport/{sport.lower()}'
        proxy = await bk.get_one_proxy(self.proxies)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        url,
                        proxy=proxy,
                        proxy_auth=self.proxy_auth,
                        timeout=20,
                ) as response:

                    resp = await response.text()
                    for k, cookie in response.headers.items():
                        if k == 'Set-Cookie':
                            if 'xsrftoken=' in cookie:
                                xsrftoken = cookie.split('xsrftoken=')[1].split(';')[0]
                                break
                    totals = {}
                    for line in ['05', '15', '25', '35', '45']:
                        totals[line] = await self.get_totals(proxy, line, xsrftoken, session)
                        # print(totals[line])
        except OSError as e:
            # raise e
            logging.info(f'{e}')
            return
        matches_list = await self.get_matches_list(resp, totals, sport)
        # matches_list.append(matches_list_)
        logging.info(f"{self.BOOKIE} has {len(matches_list)} matches in {sport}")
        # print(matches_list)
        return matches_list

    async def get_matches_list(self, raw_data, totals, sport):
        matches_list = []
        bs = BeautifulSoup(raw_data, 'lxml')
        if bs.find('span', string=re.compile('Today')) is None:
            logging.warning(f"Today return None")
            return
        today = bs.find('span', string=re.compile('Today')).parent.parent.parent
        events = today.find_all('div', class_='event-information')
        for event in events:
            id_ = event.get('data-eventid')
            match = event.a.get('data-event').replace(' v ', ' - ')
            league = event.a.get('data-competition')
            link = f"https://www.betfair.com{event.a.get('href')}"
            countdown = int(event.find('span', class_="date ui-countdown").get('data-countdown')) * 60
            kickoff = int(countdown + time.time())
            kickoff = kickoff - int(str(kickoff)[-2:])
            # print(id_, match, league, link, countdown, kickoff)
            match_ = {
                'info': {
                    'bookmaker': self.BOOKIE,
                    'id': id_,
                    'url': link,
                    'match': match,
                    'sport': sport,
                    'country': '',
                    'league': league,
                    'kickoff': kickoff,
                },
                'converted_markets': []
            }
            markets = []
            # wins = event.find_all('div', class_=["details-market market-3-runners", "details-market market-2-runners"])
            # print("-----------", len(wins))
            # for win in wins:
            #     outcomes = win.find_all('span', class_=re.compile("ui-runner-price"))
            #     type_name, type_, line = ('', '', '')
            #     for i, out in enumerate(outcomes):
            #         if out.text.strip() == 'EVS':
            #             continue
            #         if len(outcomes) == 3:
            #             type_name = '1X2'
            #             line = '0.0'
            #             if i == 0:
            #                 type_ = '1'
            #             elif i == 1:
            #                 type_ = 'X'
            #             elif i == 2:
            #                 type_ = '2'
            #             if '/' in out.text.strip():
            #                 odds = out.text.strip().split('/')
            #                 odds = round((float(odds[0]) / int(odds[1])) + 1, 2)
            #             else:
            #                 odds = float(out.text.strip())
            #             markets.append(await bk.get_scanner_format(type_name, type_, line, odds))
            #     match_['converted_markets'] = markets
            #     # print(wins)
            # for line in ['05', '15', '25', '35', '45']:
            type_name, type_ = 'Totals', ''
            for line, total in totals.items():
                # line_ = f"{line[0]}.{line[1]}"
                for t in total:
                    if t.get('eventId') == int(id_) and t.get('marketType') == 'MATCH_ODDS_90' and line == '15':
                        # print(12222222222222222222222)
                        type_name = '1X2'
                        line_ = '0.0'
                        for out in t.get('runners', []):
                            if out.get('sortPriority') == 1:
                                type_ = '1'
                            elif out.get('sortPriority') == 2:
                                type_ = 'X'
                            elif out.get('sortPriority') == 3:
                                type_ = '2'
                            odds = float(out.get('prices').get('back')[0].get('price', 0))
                            market = await bk.get_scanner_format(type_name, type_, line_, odds)
                            match_['converted_markets'].append(market)
                    elif t.get('eventId') == int(id_) and t.get('marketType') == f'OVER_UNDER_{line}':
                        type_name = 'Totals'
                        line_ = f"{line[0]}.{line[1]}"
                        for out in t.get('runners', []):
                            if out.get('sortPriority') == 1:
                                type_ = 'O'
                            elif out.get('sortPriority') == 2:
                                type_ = 'U'
                            odds = float(out.get('prices').get('back')[0].get('price', 0))
                            market = await bk.get_scanner_format(type_name, type_, line_, odds)
                            match_['converted_markets'].append(market)
                # match_div = bs.find('div', {'data-eventid': id_})
                # totals_ = match_div.find('div', class_="details-market market-2-runners")
                # outcomes = totals_.find_all('span', class_=re.compile("ui-runner-price"))
                # for i, out in enumerate(outcomes):
                #     totals__ = await self.get_outcome(out, outcomes, i, f"{line[0]}.{line[1]}")
                #     if totals__:
                #         match_['converted_markets'].append(totals__)
            matches_list.append(match_)
        return matches_list

    async def get_outcome(self, outcome, outcomes, i, line_='0,0'):
        type_name, type_, line = ('', '', line_)
        if outcome.text.strip() == 'EVS':
            return False
        if len(outcomes) == 3:
            type_name = '1X2'
            line = '0.0'
            if i == 0:
                type_ = '1'
            elif i == 1:
                type_ = 'X'
            elif i == 2:
                type_ = '2'
        elif len(outcomes) == 2:
            type_name = 'Totals'
            if i == 0:
                type_ = 'O'
            elif i == 1:
                type_ = 'U'
        if '/' in outcome.text.strip():
            odds = outcome.text.strip().split('/')
            odds = round((float(odds[0]) / int(odds[1])) + 1, 2)
        else:
            odds = float(outcome.text.strip())
        if type_name != '':
            market = await bk.get_scanner_format(type_name, type_, line, odds)
        else:
            market = False
        return market

    async def get_totals(self, proxy, line, xsrftoken, session):
        url = f"https://www.betfair.com/sport/football?marketType=OVER_UNDER_{line}" \
              f"&action=changeMarketType" \
              f"&modules=multipickavb%401002" \
              f"&lastId=1048" \
              f"&isAjax=true&ts={int(time.time() * 1000)}" \
              f"&alt=json" \
              f"&xsrftoken={xsrftoken}" \
              f"&d18=Main" \
              f"&d31=Middle" \
        # print(url)
        try:
            async with session.get(
                                    url,
                                    proxy=proxy,
                                    proxy_auth=self.proxy_auth,
                                    timeout=20,
                            ) as response:
                                # print(response.status)
                                resp = await response.json()
                                arguments = resp.get('page')\
                                    .get('config')\
                                    .get('instructions')[4]\
                                    .get('arguments')
                                # exit()
                                # html = resp.get('page')\
                                #     .get('config')\
                                #     .get('instructions')[0]\
                                #     .get('arguments')\
                                #     .get('html')
                                # bs = BeautifulSoup(html, 'lxml')
                                return arguments
        except OSError as e:
            raise e
            logging.info(f'{e}')
            return

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
    launcher = BetfairCom()
    logging.info(f"Start Betfair scraper...")
    filename = '../cache/Betfair_cache.json'
    while True:
        try:
            loop = asyncio.get_event_loop()
            future = asyncio.ensure_future(launcher.run())
            loop.run_until_complete(future)
            logging.info(f"Betfair {len(future.result())} matches found")

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