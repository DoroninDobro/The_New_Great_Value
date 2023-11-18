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

headers = {
            'Content-Type': 'application/json',
            'tokenp12': 'jwt-0c2c227d-c1ce-4dbd-9d7a-0c0f1dcdf099',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
        }

class SnaiIt:
    BOOKIE = "Snai"
    MAIN_URL = "https://snai.it"
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
                  '&country_code__in=IT'
            async with session_.get(
                    url, headers={"Authorization": proxy_token}) as response:
                proxies = await response.json()
        return proxies.get('results')

    async def get_payload(self):
        sport_id = 1
        sport_name = 'CALCIO'

        payload = {
            "Sport": {
                "IconDefault": False,
                "image": f"sports_{sport_id}_orange.png",
                "selected": True,
                "cod_disciplina": sport_id,
                "des_sport": sport_name,
                "counter": 1008,
                "max_num_esiti": 0
            },
            "Manifestazione": {
                "Preferita": False,
                "Expanded": False,
                "cod_manif": 2,
                "cod_disciplina": sport_id,
                "group_id": 0,
                "antepost": 0,
                # "des_manif": "PROX 24 ORE - TOP SCOMMESSE",
                "des_manif": "PROSSIME 24 ORE",
                "counter": 157,
                "Tipo": "PrimoPiano",
                "FiltroPrimoPiano": {
                    "CodiciTipiScommesse": "",  # "3,-115,18,7989,8,8333,4,7,15529,569,23182,9942,22286,13527",
                    "Tipo": "mins",
                    "Valore": "1440"
                }
            },
            "GruppoTipoScommessa": {
                "Active": True,
                "cod_gruppo": 1,
                "cod_disciplina": sport_id,
                "cod_manif": 4,
                "des_gruppo": "PRINCIPALI",
                "flag_antepost": 0,
                "flg_picker": 0
            },
            "TipoScommessa": {
                "cod_tipo_sco": 3,
                "cod_disciplina": sport_id,
                "cod_manif": 0,
                "cod_gruppo": 1,
                "info_agg": "00000000",
                "des_tipo_sco": "1X2 FINALE",
                "aggr": "no",
                "flag_antepost": 0,
                "cod_stato_sco": 0,
                "priorita_scom": 1,
                "tipo_info_agg": 0,
                "minimo_avv": 0,
                "massimo_avv": 0,
                "NumeroAvvenimento": 0,
                "Configurazione": "Default"
            }
        }
        return payload

    async def get_live(self):
        async with aiohttp.ClientSession() as session:
            url = "https://appsport.snai.it/api/Mobile/GetAvvenimenti"
            len_proxy = len(self.proxies)
            choice_1 = random.randint(0, len_proxy - 1)
            proxy = f"http://{self.proxies[choice_1]['proxy_address']}:{self.proxies[choice_1]['port']}"
            payload = await self.get_payload()
            try:
                async with session.post(
                    url,
                    headers=headers,
                    proxy_auth=proxy_auth,
                    proxy=proxy,
                    json=payload,
                    timeout=120
                ) as response:
                    # print(await response.text())
                    data = await response.json()
            except Exception as e:
                logging.info("Snai ERROR")
                # raise e
                logging.debug(e)
                logging.warning(f"Could not get all live list")
                return []

        matches_list = []
        for item in data:
            if item.get('Avvenimento') is not None:
                matches_list.append(item.get('Avvenimento'))
        return matches_list

    async def convert_to_scanner_format(self, data):
        type_name, line, type_ = '', '', ''
        if data.get('des_tipo_sco') == '1X2 FINALE':
            type_name = '1X2'
            line = '0.0'
            type_ = data.get('des_evento')
        elif data.get('des_evento') in ['OVER', 'UNDER']:
            type_ = data.get('des_evento')[:1]
            type_name = 'Totals'
            line = str((int(data.get('extra_info')) / 10))
        elif data.get('des_tipo_sco') == 'T/T HANDICAP':
            type_name = 'Handicap'
            type_ = f"H{data.get('des_evento')}"
            line = str((int(data.get('extra_info')) / 10))
        bet = {
            'type_name': type_name,
            'type': type_,
            'line': line,
            'odds': data.get('quota') / 100
        }
        return bet

    async def collect_all(self, data):
        outcomes = []
        for item in data:
            if item.get('Evento1') is not None:
                # print(item.get('Evento1'))

                if item.get('Evento1').get('des_tipo_sco') in ['1X2 FINALE', 'UNDER/OVER', 'T/T HANDICAP']:
                    bet = await self.convert_to_scanner_format(item.get('Evento1'))
                    outcomes.append(bet)
                    if item.get('Evento2') is not None:
                        bet = await self.convert_to_scanner_format(item.get('Evento2'))
                        outcomes.append(bet)
                    if item.get('Evento3') is not None:
                        bet = await self.convert_to_scanner_format(item.get('Evento3'))
                        outcomes.append(bet)
        sport_ = item.get('Evento1').get('sigla_sport')
        sport_ = 'Football' if sport_ == 'CALCIO' else sport_
        kickoff = int(datetime.fromisoformat(item.get('Evento1').get('data_ora_avv')).timestamp()) + 3600
        match = {
            'info':
            {
                'id': item.get('Evento1').get('br_match_id'),
                'kickoff': kickoff,
                'url': 'https://appsport.snai.it/mobile/main/ricerca',
                'sport': sport_,
                'bookmaker': self.BOOKIE,
                'match': item.get('Evento1').get('des_avvenimento'),
                'league': item.get('Evento1').get('des_manif')
            },
            'converted_markets': outcomes,
        }
        return match

    async def get_event_payload(self, match):
        payload = {
            "Sport": {
                "IconDefault": False,
                "image": "sports_1_grey.png",
                "selected": False,
                "cod_disciplina": 1,
                "des_sport": "CALCIO",
                "counter": 0,
                "max_num_esiti": 0
            },
            "Manifestazione": {
                "Preferita": False,
                "Expanded": False,
                "cod_manif": match['cod_manif']
            },
            "GruppoTipoScommessa": {
                "Active": False,
                "cod_gruppo": 1,
                "cod_disciplina": 1,
                "cod_manif": 21,
                "des_gruppo": "PRINCIPALI",
                "flag_antepost": 0,
                "flg_picker": 0
            },
            "Avvenimento": match,
            "FlagLive": 0,
            "Virtual": False
        }
        return payload

    async def fetch_matches(self, match, sem):
        async with sem:
            async with aiohttp.ClientSession() as session:
                url = "https://appsport.snai.it/api/Mobile/GetTipiScommesseAvvenimento"
                len_proxy = len(self.proxies)
                choice_1 = random.randint(0, len_proxy - 1)
                proxy = f"http://{self.proxies[choice_1]['proxy_address']}:{self.proxies[choice_1]['port']}"
                payload = await self.get_event_payload(match)
                try:
                    async with session.post(
                            url,
                            headers=headers,
                            proxy_auth=proxy_auth,
                            proxy=proxy,
                            json=payload,
                            timeout=120
                    ) as response:
                        if response.status != 200:
                            logging.warning(f"{match.get('des_avvenimento')} return status code {response.status}")
                            return None
                        data = await response.json()
                except Exception as e:
                    logging.info("Snai ERROR")
                    # raise e
                    logging.debug(e)
                    logging.warning(f"Could not get all live list")
                    return None
        data = await self.collect_all(data)
        return data

    async def run(self, matches):
        tasks = []
        sem = asyncio.Semaphore(self.WORKERS)
        for match in matches:
            try:
                task = asyncio.ensure_future(self.fetch_matches(match, sem))
                tasks.append(task)
            except Exception as e:
                # raise
                print(e)
        responses = await asyncio.gather(*tasks)
        responses = [x for x in responses if x is not None]
        return responses


if __name__ == "__main__":
    launcher = SnaiIt()
    logging.info(f"Start Snai scraper...")
    filename = '../cache/Snai_cache.json'
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

            sleep_time = 30
            logging.info(f"{sleep_time} seconds sleep.")
            time.sleep(sleep_time)
        except Exception as e:
            raise
            logging.error(f"{e}")
            time.sleep(120)
