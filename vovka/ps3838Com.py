import asyncio
from aiohttp import ClientSession, CookieJar
import logging
import time
from datetime import datetime

MAIN_LOOP = 1
limit_time = 12  # limit time in hours
mk = 1

class Ps3838Com:

    BOOKIE = 'Ps3838'
    MAIN_URL = 'https://www.ps3838.com'
    LIVE_URL = '='
    EXPAND_MODE = False
    USE_PROXY = 0
    WORKERS = 500
    SPECIALS = 'true'
    PRIMARY_ONLY = 'true'
    ALLOWED_SPORTS = [
            #'Basketball',
            #'E Sports',
            #'Football',
            #'Handball',
            #'Hockey',
            #'Rugby Union',
            'Soccer',
            #'Tennis',
            #'Volleyball'
                      ]


    def __init__(self):
        self.mk = 1 #сегодня
        self.date_ = datetime.today().strftime('%Y-%m-%d')
        self.MAIN_LOOP = 1
        self.limit_time = 12
        self.cookies_jar = CookieJar(unsafe=True)
        self.cookies_path = 'cache/pinnacle_cookies.txt'
        try:
            self.cookies_jar.load(self.cookies_path)
        except EOFError:
            pass
        self.session = None

        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
                          ' (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'

    async def setup(self):
        self.session = await self.get_session()
        
    async def get_session(self):
        session = ClientSession(cookie_jar=self.cookies_jar)
        return session

    async def check_login(self):
        balance_url = 'https://761gsge.tender88.com/member-service/v1/account-balance?locale=en_US'
        headers = {'user-agent': self.user_agent}
        try:
            async with self.session.post(balance_url, json={}, headers=headers) as res:
                response = await res.json()
        except Exception as e:
            response = {'success': False}
            # raise
        if response['success'] is False:
            logging.info(f"Not active session on pinnacle. Let's refresh it.")
            await self.lets_login()
        elif response['success'] is True:
            logging.info(f"Session on pinnacle is active")

    async def lets_login(self):
        headers = {'user-agent': self.user_agent}
        url = 'https://api.piwi247.com/api/users/login'
        payload = {"email": "ikasin635@gmail.com", "password": "MyWin12!!", "loginType": 1, "remember": False}

        # мы значит с логином и паролем заходим на пиви через запрос без браузера
        async with self.session.post(url, json=payload, headers=headers) as response:
            response = await response.json()
        # получаем от сюда токен, между прочим баланс тоже виден
        token = response['data']['token']['pinnacle']['token']
        logging.info(f'access_token: {token}')

        # формируем новый урл и идем уже туда
        login_url = f"https://761gsge.tender88.com/member-service/v1/login-token?oddsFormat=HK" \
                    f"&token={token}==&locale=en&detectedUrl=https://761gsge.tender88.com"
        headers = {
            'referer': 'https://761gsge.tender88.com',
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent
        }
        # новый запрос мы делаем запрещая перенаправление на другие страницы
        async with self.session.get(login_url, headers=headers, allow_redirects=False) as response:
            cookies = response.cookies
        self.cookies_jar.update_cookies(cookies)
        self.cookies_jar.save(self.cookies_path)
        await self.check_login()

    # тут мы отправляем собирать матчи прематч 
    async def bound_live(self, sem, session, sport_id):
        prematch = []
        try:
            prematch = await self.get_prematch_(sem, session, sport_id)
        except OSError as e:
            logging.info(f'{e}')
        try:
            if len(prematch) == 0:
                return
        except TypeError:
            return
        prematches_list = await self.get_matches_list(sem, prematch)
        return prematches_list
        
    async def fetch(self, url):
        try:
            async with self.session.get(url, timeout=40) as response:
                return await response.json()
        except Exception as e:
            logging.debug(e)
            return
    
    async def loop_markets(self, markets_, match):
        sport_id = self.get_sport_id(match[4])
        jmarkets = markets_[sport_id]
        converted_m_list = []
        try:
            markett = list(filter(lambda dict: dict[0] == match[8], jmarkets['n'][0][2]))[0][2]
            markett = list(filter(lambda dict: dict[0] == match[0], markett))[0]
        except KeyError:
            return
            raise
        except IndexError:
            # raise
            logging.info(f"{match[0]} IndexError: list index out of range")
            return

        # Handicaps
        try:
            llllooop = list(markett[8].keys())
            for period in llllooop:
                add_to_type_name = ''
                if period == '0' and match[4] == 'Soccer':
                    add_to_type_name = ''
                    add_to_type = ''
                    marketts = markett[8]['0'][1]
                if period == '0' and match[4] != 'Soccer':
                    add_to_type_name = '(OT)'
                    add_to_type = ''
                    marketts = markett[8]['0'][1]
                elif period == '1':
                    add_to_type_name = ''
                    add_to_type = '1H'
                    marketts = markett[8]['1'][1]
                elif period == '6':
                    add_to_type_name = ''
                    marketts = markett[8]['0'][1]
                for handicaps in markett[8][period][0]:
                    for ii, price in enumerate(handicaps):
                        if ii >= 2:
                            break
                        scanner_format_bet = await self.get_handicaps(ii, handicaps, add_to_type_name, add_to_type)
                        converted_m_list.append(scanner_format_bet)
        except (KeyError, IndexError):
            # raise
            logging.info(f"no market yet")
            return


        # Totals
        try:
            llllooop = list(markett[8].keys())
            for period in llllooop:
                if period == '0' and match[4] == 'Soccer':
                    add_to_type_name = ''
                    add_to_type = ''
                    marketts = markett[8]['0'][1]
                if period == '0' and match[4] != 'Soccer':
                    add_to_type_name = '(OT)'
                    add_to_type = ''
                    marketts = markett[8]['0'][1]
                elif period == '1':
                    add_to_type_name = ''
                    add_to_type = '1H'
                    marketts = markett[8]['1'][1]
                elif period == '6':
                    add_to_type_name = ''
                    marketts = markett[8]['0'][1]
                for totals in marketts:
                    for ii, price in enumerate(totals):
                        if ii >= 2:
                            break
                        scanner_format_bet = await self.get_totals(ii, totals, add_to_type_name, add_to_type)
                        converted_m_list.append(scanner_format_bet)
        except (KeyError, ValueError):
            raise
            logging.info(f"no market yet")
            return
        if markett[8].get('0') is not None:
            if markett[8]['0'][2] is not None:
                for ii, price in enumerate(markett[8]['0'][2]):
                    type_name = '1X2'
                    if markett[8]['0'][2][2] is None:
                        type_name = '12'
                    if ii >= 3:
                        break
                    if price is None:
                        break
                    if ii == 0:
                        type_ = '2'
                    elif ii == 1:
                        type_ = '1'
                    elif ii == 2:
                        type_ = 'X'

                    try:
                        price = float(price)
                    except ValueError:
                        price = 0
                    scanner_format_bet = {
                        'type_name': type_name,
                        'type': type_,
                        'line': '0.0',
                        'odds': price
                    }
                    converted_m_list.append(scanner_format_bet)

        try:
            markett[8]['1'][2]
        except KeyError:
            # raise
            logging.info(f"no market yet")
            return
        if markett[8]['1'][2] is not None:
            for ii, price in enumerate(markett[8]['1'][2]):
                type_name = 'First Half 1X2'
                if markett[8]['1'][2][2] is None:
                    type_name = 'First Half 12'
                if ii >= 3:
                    break
                if price is None:
                    break
                if ii == 0:
                    type_ = '1H2'
                elif ii == 1:
                    type_ = '1H1'
                elif ii == 2:
                    type_ = '1HX'
                try:
                    price = float(price)
                except ValueError:
                    price = 0
                scanner_format_bet = {
                    'type_name': type_name,
                    'type': type_,
                    'line': '0.0',
                    'odds': price
                }
                converted_m_list.append(scanner_format_bet)
        return converted_m_list
        
    async def get_handicaps(self, i, handicaps, add_to_type_name, add_to_type):
        try:
            type_ = f'{add_to_type}H{i+1}'
            if i == 0:
                line = f"{handicaps[1]}"
                price = float(handicaps[3])
            elif i == 1:
                line = f"{handicaps[0]}"
                price = float(handicaps[4])
            scanner_format_bet = {
                'type_name': f'Handicap{add_to_type_name}',
                'type': type_,
                'line': line,
                'odds': price
            }
        except Exception as e:
            logging.error(f'get_handicap error: {e}')
            return False
        return scanner_format_bet

    async def get_totals(self, i, totals, add_to_type_name, add_to_type):
        if i == 0:
            type_ = f'{add_to_type}O'
            line = f"{totals[1]}"
            price = float(totals[2])
        elif i == 1:
            type_ = f'{add_to_type}U'
            line = f"{totals[1]}"
            price = float(totals[3])
        scanner_format_bet = {
            'type_name': f'Totals{add_to_type_name}',
            'type': type_,
            'line': line,
            'odds': price
        }
        return scanner_format_bet
        
    async def bound_fetch(self, match, markets_):
        if markets_ is None:
            return await self.bet_attribute_none(match)
        try:
            betAttribute = {
                'info': {
                    'id': match[0],
                    'match': match[1],
                    'bookmaker': self.BOOKIE,
                    'league': match[3],
                    'match_id': match[0],
                    'sport': match[4],
                    'checking_time': time.ctime(),
                    'unix_time': int(time.time()),
                    'kickoff': match[7],
                    'url': match[2]
                },
            }
            try:
                converted_m_list = await self.loop_markets(markets_, match)
            except (NameError, TypeError):
                raise
                logging.debug(f"NameError, TypeError 184")
                return
        except Exception as e:
            logging.debug('AttributeError')
            return
        betAttribute['converted_markets'] = converted_m_list
        return betAttribute
        
    async def bound_fetch1(self, sem, sport_id):
        async with sem:
            date_ = datetime.today().strftime('%Y-%m-%d')
            # api_match_url = f"https://www.ps3838.com/sports-service/sv/compact/" \
            api_match_url = f"https://761gsge.tender88.com/sports-service/sv/compact/" \
                  f"events?_g=1&btg=1&c=&cl=100&d={date_}&ev=&g=&hle=true" \
                  f"&l=100&lg=&lv=&me=0&mk={mk}&more=false&o=1&ot=1&pa=0&pn=-1" \
                  f"&sp={sport_id}&tm=0&v=0&wm=&locale=en_US&_=" \
                  f"&withCredentials=true"
            try:
                response = await self.fetch(api_match_url,
                                            # headers=headers
                                            )
                try:
                    return {sport_id: response}
                except AttributeError:
                    raise
                    logging.debug('AttributeError')
                    return
                except ValueError:  # includes simplejson.decoder.JSONDecodeError
                    raise
                    logging.debug('Decoding JSON has failed')
                    return
            except Exception as e:
                logging.debug(getattr(e, 'message', repr(e)))
                return

#    async def random_proxy(self):
#        proxies = [
#        ]
#        return random.choice(proxies)

    async def market_run(self):
        tasks = []
        sem = asyncio.Semaphore(self.WORKERS)
        # async with ClientSession(trust_env=True) as session:
        for sport_ in self.ALLOWED_SPORTS:
            sport_id = self.get_sport_id(sport_)
            try:
                task = asyncio.ensure_future(self.bound_fetch1(sem, sport_id))
                tasks.append(task)
            except Exception as e:
                print(e)
        responses = await asyncio.gather(*tasks)
        return responses

    async def get_prematch_(self, sem, session, sport_id):
            date_ = datetime.today().strftime('%Y-%m-%d')
        # async with sem:
        #     url = f"https://www.ps3838.com/sports-service/sv/compact/" \
            url = f"https://761gsge.tender88.com/sports-service/sv/compact/" \
                  f"events?_g=1&btg=1&c=&cl=3&d={date_}&ev=&g=&hle=false" \
                  f"&l=3&lg=&lv=&me=0&mk={mk}&more=false&o=1&ot=1&pa=0&pn=-1" \
                  f"&sp={sport_id}&tm=0&v=0&wm=&locale=en_US&_=1647853021429" \
                  f"&withCredentials=true"
            logging.debug(f'Following {url}')
            try:
                async with session.get(
                        url,
                        timeout=30,
                ) as response:

                    return await response.json()
            except Exception as e:
                logging.debug(e)
                logging.warning(f'Could not get all live list')
                return

    async def get_matches_list(self, sem, live_list_):
        matches_list = []
        live_list = live_list_['n'][0][2]
        for i, d in enumerate(live_list):
            for m in d[2]:
                if limit_time > 0 and (int(time.time()) + (limit_time * 60 * 60)) < int(m[4]/1000):
                    continue
                sport_name = live_list_['n'][0][1]
                league_name = d[1]
                league_id = d[0]
                local_id = m[0]
                match_name = f"{m[1]}-vs-{m[2]}"
                country_name = ''
                start_match_time = int(m[4]/1000)
                time_before_start = int(start_match_time) - int(time.time())
                home = m[1]
                url = f"https://www.start567.com/en/compact/search/{home.replace(' ', '-')}"
                matches_list.append([
                    local_id,  # local id
                    match_name,  # match name
                    url,  # event url
                    league_name,  # Champ name
                    sport_name,  # sport
                    self.BOOKIE,  # bookie
                    country_name,  # country
                    start_match_time,  # Time of start
                    league_id
                    ])
        return matches_list

    def get_sport_id(self, sport_name):
        sports_id = {
            'Soccer': 29,
            'Tennis': 33,
            'Basketball': 4,
            'Football': 15,
            'Baseball': 3,
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

    async def run_(self, matches, markets):
        tasks = []
        sem = asyncio.Semaphore(self.WORKERS)
        async with ClientSession(trust_env=True) as session:
            for match in matches:
                try:
                    task = asyncio.ensure_future(self.bound_fetch(match, markets))
                    tasks.append(task)
                except Exception as e:
                    raise e
                    print(e)
            responses = await asyncio.gather(*tasks)
            return responses

    # на данный момент эдд_дейс не используется
    async def run2(self, add_days: int):
        tasks = []
        sem = asyncio.Semaphore(self.WORKERS)
        # async with ClientSession() as session:
        for sport_ in self.ALLOWED_SPORTS:
            sport_id = self.get_sport_id(sport_)
            try:
                task = asyncio.ensure_future(
                    self.bound_live(
                        sem, self.session, sport_id
                    ))
                tasks.append(task)
            except Exception as e:
                print(e)
        responses = await asyncio.gather(*tasks)
        return responses
    
    # я так понимаю где-то здесь мы берем кэфы...
    async def run(self, matches):
        login = await self.check_login()
        market_get_loop = asyncio.get_event_loop()
        future_market = asyncio.ensure_future(self.market_run())
        market_get_loop.run_until_complete(future_market)
        all_sport_markets = future_market.result()
        markets = {}
        for all in all_sport_markets:
            if all:
                markets[list(all)[0]] = all[list(all)[0]]
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self.run_(matches, markets))
        loop.run_until_complete(future)
        logging.info(f'finished scan markets')
        return future.result()
    
    async def get_prematch(self):
        logging.info(f'Start Ps3838 Scanner...')

        logging.info('Collecting prematch list')
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self.run2(10))
        loop.run_until_complete(future)
        matches_list = [x for x in future.result() if x is not None]
        matches_list = [y for x in matches_list for y in x]  # from [[],[[],[],[]],[[],[]]] to [[],[],[],[],[],[],[]]
        logging.info(f"{self.BOOKIE} has {len(matches_list)} matches")
        return matches_list
