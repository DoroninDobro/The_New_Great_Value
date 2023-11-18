import random
import time
import json
import logging
from datetime import datetime, date, timedelta
import asyncio
import aiohttp

import nest_asyncio
nest_asyncio.apply()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)

MAIN_LOOP = 1
sport = 1
proxy_auth = aiohttp.BasicAuth('', '')  # login, password
proxy_token = ''

class AdmiralbetMe:
    BOOKIE = "Admiralbet"
    MAIN_URL = "https://admiralbet.me"
    WORKERS = 200
    ALLOWED_SPORTS = [
        'Football',
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

    async def get_live(self):
        headers = {
            'Language': 'en-US',
            'OfficeId': '1175',
        }
        date_in = time.strftime('%Y-%m-%dT%H:%M:%S.000')
        date_out = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S.000')

        async with aiohttp.ClientSession() as session:
            url = "https://webapi.admiralbet.me/SportBookCacheWeb/api/offer/tree/null/true/true/true" \
                  f"/{date_in}" \
                  f"/{date_out}" \
                  "/false"
            len_proxy = len(self.proxies)
            choice_1 = random.randint(0, len_proxy - 1)
            proxy = f"http://{self.proxies[choice_1]['proxy_address']}:{self.proxies[choice_1]['port']}"
            try:
                async with session.get(
                    url,
                    headers=headers,
                    proxy_auth=proxy_auth,
                        proxy=proxy,
                    timeout=120
                ) as response:
                    data = await response.json()
            except Exception as e:
                logging.info("Admiralbet ERROR")
                # raise e
                logging.debug(e)
                logging.warning(f"Could not get all live list")
                return []
            # all_data['data'] += data['data']
        regions = {}
        for d in data:
            if d['name'] in ['Football', 'Basketball']:
                for country in d['regions']:
                    if country['eventsCount'] >= 1:
                        regions[country['id']] = {'id': country['id'], 'sport_id': country['sportId']}
        # print(regions)

        tasks = []
        sem = asyncio.Semaphore(self.WORKERS)

        for key, region in regions.items():
            try:
                task = asyncio.ensure_future(self.fetch_matches(region, sem))
                tasks.append(task)
            except Exception as e:
                print(e)
        responses = await asyncio.gather(*tasks)
        # print(responses)
        data = []
        for response in responses:
            data += response


        try:
            matches_ = await self.matches_from_json(data)
        except AttributeError:
            raise e
            return []
        return matches_

    async def fetch_matches(self, region, sem):
        async with sem:
            date_in = time.strftime('%Y-%m-%dT%H:%M:%S.000')
            date_out = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S.000')

            async with aiohttp.ClientSession() as session:
                headers = {
                    'Language': 'en-US',
                    'OfficeId': '1175',
                }
                url = "https://webapi.admiralbet.me/SportBookCacheWeb/api/offer/getWebEventsSelections?" \
                      "pageId=3" \
                      f"&sportId={region['sport_id']}" \
                      f"&regionId={region['id']}" \
                      "&isLive=false" \
                      f"&dateFrom={date_in}" \
                      f"&dateTo={date_out}"
                len_proxy = len(self.proxies)
                choice_1 = random.randint(0, len_proxy - 1)
                proxy = f"http://{self.proxies[choice_1]['proxy_address']}:{self.proxies[choice_1]['port']}"
                try:
                    async with session.get(
                            url,
                            headers=headers,
                            proxy_auth=proxy_auth,
                            proxy=proxy,
                            timeout=120
                    ) as response:
                        data = await response.json()
                except Exception as e:
                    logging.info("Admiralbet ERROR")
                    # raise e
                    logging.debug(e)
                    logging.warning(f"Could not get all live list")
                    return []
        # print(data)
        return data


    async def matches_from_json(self, data):
        today = date.today()
        today = today.strftime("%Y-%m-%d")
        matches = []
        for ii, dd in enumerate(data):
            for i, d in enumerate(data):
                if d['mappingTypeId'] > 1:
                    logging.info(f"skip bonus matches {d['name']}")
                    continue
                # print(json.dumps(d))
                try:
                    try:
                        start_time = int(datetime.fromisoformat(d['dateTime']).timestamp()) + 10800
                    except Exception as e:
                        logging.error(f"time incorrect format: {e}")
                        continue
                    url = f"https://admiralbet.me/sport-prematch?sport={d['sportName']}" \
                          f"&region={d['regionName'].replace(' ', '_')}" \
                          f"&competition={d['competitionName'].replace(' ', '_')}" \
                          f"&competitionId={d['sportId']}-{d['regionId']}-{d['competitionId']}&" \
                          f"event={d['id']}" \
                          f"&eventName={d['name'].replace(' ', '_')}"
                    # start_time = str(start_time).split(' ')[0]
                except TypeError:
                    start_time = None
                # if start_time != today:
                #     continue
                match = ["id", "name", "link", "champ", "sport", "country", "book", "kickoff", "market"]
                match[0] = d['id']
                match[1] = d['name']
                match[2] = url
                match[3] = d['competitionName']
                match[4] = d['sportName']
                match[5] = d['regionName']
                match[6] = self.BOOKIE
                match[7] = start_time
                match[8] = d['bets']
                matches.append(match)
            return matches

    async def bound_fetch(self, match, sem):
        betAttribute = {
            'match_id': match[0],
            "info": {
                "bookmaker": self.BOOKIE,
                "match_id": match[0],
                "match": match[1],
                "sport": match[4],
                "league": match[3],
                'url': match[2],
                'kickoff': match[7]
            }
        }
        markets = await self.convert_to_scanner_format(match[8])
        betAttribute["converted_markets"] = markets
        return betAttribute

    @staticmethod
    def scanner_format_bet(ctsf):
        scanner_format_bet = {
                        'type_name': ctsf['type_name'],
                        'type': ctsf['type'],
                        'line': ctsf['line'],
                        'odds': ctsf['odds']
                    }
        return scanner_format_bet

    async def convert_to_scanner_format(self, markets):
        type_name = ''
        type_ = ''
        line = '0.0'
        odds = 0.0
        converted_list = []
        for market in markets:
            for i, outcome in enumerate(market['betOutcomes']):
                ctsf = await self.convert_to_scanner_format_(market, outcome)
                if ctsf is False:
                    continue
                converted_list.append(ctsf)
        return converted_list

    async def convert_to_scanner_format_(self, game_name, one_bet):
        type_name = ''
        if one_bet['betTypeId'] in [135]:
            return {
                'type_name': '1X2',
                'type': one_bet['name'],
                'line': '0.0',
                'odds': one_bet['odd']
            }
        elif one_bet['betTypeId'] in [186]:
            return {
                'type_name': '12',
                'type': one_bet['name'],
                'line': '0.0',
                'odds': one_bet['odd']
            }
        elif one_bet['betTypeId'] in [137, 213]:

            if one_bet['name'] in ['Manje', 'Under']:
                type_ = 'U'
            elif one_bet['name'] in ['Vise', 'Over']:
                type_ = 'O'
            return {
                'type_name': 'Totals',
                'type': type_,
                'line': one_bet['sBV'],
                'odds': one_bet['odd']
            }
        elif one_bet['betTypeId'] in [196, 788]:
            return {
                'type_name': 'Handicap',
                'type': f"H{one_bet['name']}",
                'line': one_bet['sBV'],
                'odds': one_bet['odd']
            }
        else:
            return False

    @staticmethod
    async def fetch(url, session):
        try:
            async with session.get(
                    url,
                    timeout=20,
                    # proxy=proxy,
                    ) as response:
                resp = await response.json(content_type=None)
                return resp
        except Exception as e:
            logging.debug(e)
            return

    async def run(self, matches):
        async with aiohttp.ClientSession(trust_env=True) as session:
            tasks = []
            sem = asyncio.Semaphore(self.WORKERS)

            for match in matches:
                try:
                    task = asyncio.ensure_future(self.bound_fetch(match, sem))
                    tasks.append(task)
                except Exception as e:
                        print(e)
            responses = await asyncio.gather(*tasks)
            return responses


if __name__ == "__main__":
    launcher = AdmiralbetMe()
    logging.info(f"Start Admiralbet scraper...")
    filename = '../cache/Admiralbet_cache.json'
    while True:
        try:
            loop = asyncio.get_event_loop()
            future = asyncio.ensure_future(launcher.get_live())
            loop.run_until_complete(future)
            logging.info(f"{len(future.result())} matches found")

            loopf = asyncio.get_event_loop()
            future = asyncio.ensure_future(launcher.run(future.result()))
            loopf.run_until_complete(future)
            if len(future.result()) > 0:
                with open(filename, 'w') as f:
                    json.dump(future.result(), f)

            sleep_time = 5
            logging.info(f"{sleep_time} seconds sleep.")
            time.sleep(sleep_time)
        except Exception as e:
            # raise
            logging.error(f"{e}")
            time.sleep(60)
