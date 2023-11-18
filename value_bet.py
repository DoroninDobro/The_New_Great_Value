import logging
import json
import time
import asyncio
import aiohttp
import aiofiles

from search import SearchCoincidence
from settings import settings

import nest_asyncio
nest_asyncio.apply()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)


BOOKERS = settings['filter_by_bookie']
WORKERS = len(BOOKERS)


class ForkScanner:

    def __init__(self):
        self.offset = ''

    async def open_cache(self, bookie):
        cache = []
        try:
            filename = f"cache/{bookie}_cache.json"
            async with aiofiles.open(filename, mode='r') as f:
                contents = await f.read()
            cache = json.loads(contents)
            logging.info(f"{bookie} has {len(cache)} matches")
        except Exception as e:
            logging.error(f"{e}")
            await self.open_cache(bookie)
        return cache

    async def run(self, countries=None):
        tasks = []
        sem = asyncio.Semaphore(WORKERS)
        for bookmaker in BOOKERS:
            task = asyncio.ensure_future(self.open_cache(bookmaker))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        return responses

    def get_3way_opposite_type(self, type_, ps3838):
        if type_ == '1':
            oppose_type_1 = 'X'
            oppose_type_2 = '2'
        elif type_ == 'X':
            oppose_type_1 = '1'
            oppose_type_2 = '2'
        elif type_ == '2':
            oppose_type_1 = '1'
            oppose_type_2 = 'X'
        if type_ == '1X':
            oppose_type_1 = '12'
            oppose_type_2 = 'X2'
        elif type_ == '12':
            oppose_type_1 = '1X'
            oppose_type_2 = 'X2'
        elif type_ == 'X2':
            oppose_type_1 = '1X'
            oppose_type_2 = '12'
        if type_ == '1H1':
            oppose_type_1 = '1HX'
            oppose_type_2 = '1H2'
        elif type_ == '1HX':
            oppose_type_1 = '1H1'
            oppose_type_2 = '1H2'
        elif type_ == '1H2':
            oppose_type_1 = '1H1'
            oppose_type_2 = '1HX'
        if type_ == '1H1X':
            oppose_type_1 = '1H12'
            oppose_type_2 = '1HX2'
        elif type_ == '1H12':
            oppose_type_1 = '1H1X'
            oppose_type_2 = '1HX2'
        elif type_ == '1HX2':
            oppose_type_1 = '1H1X'
            oppose_type_2 = '1H12'
        return oppose_type_1, oppose_type_2

    def get_2way_opposite_type(self, type_, line):
        if type_ == 'H1':
            oppose_type = 'H2'
            if line[:1] == '-':
                oppose_line = line[1:]
            else:
                if line == '0.0':
                    oppose_line = line
                else:
                    oppose_line = f'-{line}'
        elif type_ == 'H2':
            oppose_type = 'H1'
            if line[:1] == '-':
                oppose_line = line[1:]
            else:
                if line == '0.0':
                    oppose_line = line
                else:
                    oppose_line = f'-{line}'
        if type_ == '1HH1':
            oppose_type = '1HH2'
            if line[:1] == '-':
                oppose_line = line[1:]
            else:
                if line == '0.0':
                    oppose_line = line
                else:
                    oppose_line = f'-{line}'
        elif type_ == '1HH2':
            oppose_type = '1HH1'
            if line[:1] == '-':
                oppose_line = line[1:]
            else:
                if line == '0.0':
                    oppose_line = line
                else:
                    oppose_line = f'-{line}'
        elif type_ == 'O':
            oppose_type = 'U'
            oppose_line = line
        elif type_ == 'U':
            oppose_type = 'O'
            oppose_line = line
        elif type_ == '1HO':
            oppose_type = '1HU'
            oppose_line = line
        elif type_ == '1HU':
            oppose_type = '1HO'
            oppose_line = line
        elif type_ == '1':
            oppose_type = '2'
            oppose_line = line
        elif type_ == '2':
            oppose_type = '1'
            oppose_line = line
        # elif type_ == '1H1':
        #     oppose_type = '1H2'
        #     oppose_line = line
        # elif type_ == '1H2':
        #     oppose_type = '1H1'
        #     oppose_line = line
        return oppose_type, oppose_line

    def get_2way_opposite_odds(self, type_, line, ps3838):
        opposite_type, opposite_line = self.get_2way_opposite_type(type_, line)
        opposite_odds = [x['odds'] for x in ps3838['converted_markets']
                         if x['type'] == opposite_type and x['line'] == opposite_line][0]
        return opposite_odds

    def get_3way_opposite_odds(self, type_, ps3838):
        opposite_type_1, opposite_type_2 = self.get_3way_opposite_type(type_, ps3838)
        opposite_odds_1 = [x['odds'] for x in ps3838['converted_markets'] if x['type'] == opposite_type_1][0]
        opposite_odds_2 = [x['odds'] for x in ps3838['converted_markets'] if x['type'] == opposite_type_2][0]
        return opposite_odds_1, opposite_odds_2

    def get_margin(self, ps, ps3838):
        if ps['type_name'] in ['1X2', 'Double Chance', 'First Half 1X2']:
            opposite_odds_1, opposite_odds_2 = self.get_3way_opposite_odds(ps['type'], ps3838)
            margin = (1 / float(ps['odds']) + 1 / float(opposite_odds_1) + 1 / float(opposite_odds_2)) - 1
            n = 3
        else:
            opposite_odds = self.get_2way_opposite_odds(ps['type'], ps['line'], ps3838)
            margin = (1 / float(ps['odds']) + 1 / float(opposite_odds)) - 1
            n = 2
        return margin, n

    async def send_to_telegram(self, message, params):
        return
        async with aiohttp.ClientSession() as session:
            send_message_url = f"https://api.telegram.org/bot{settings['tg_bot']['token']}/sendMessage"
            # async with session.get(send_message_url, params=params):
            async with session.get(send_message_url, json=params) as response:
                print(response)
                logging.info('message sent')

    def search_difference(self, ps3838, bookie):
        if ps3838['converted_markets'] is None:
            return []
        if ps3838.get('info', {}).get('kickoff') - time.time() > 86400:
            return []
        # try:
        #     with open('cache/cache.json', 'r') as f:
        #         already_was = json.load(f)
        #         f.close()
        # except (json.decoder.JSONDecodeError, FileNotFoundError):
        #     already_was = []
        all = []
        for ps in ps3838.get('converted_markets', []):
            for boo in bookie.get('converted_markets', []):
                if ps is None or boo is None:
                    continue
                if ps['type'] == boo['type'] and ps['line'] == boo['line'] and ps['type_name'] == boo['type_name']:
                    if ps['odds'] <= settings['coef_max_limit'] and ps['odds'] >= settings['coef_min_limit']:
                        margin, n = self.get_margin(ps, ps3838)
                        Ofair = n * ps['odds'] / (n - margin * ps['odds'])
                        min_bet_value = round(Ofair * settings['profit'], 2)
                        roi = round((boo['odds'] / Ofair - 1) * 100, 3)
                        if boo['odds'] >= min_bet_value:
                            K = (settings['profit'] - 1) / (min_bet_value - 1)
                            size_of_stake = 0
                            currency = 'rub'
                            currency_rate = 1
                            if bookie['info']['bookmaker'] == 'Crocobet':
                                currency_rate = 25
                                currency = 'gel'
                                size_of_stake = round(int(K * settings['bankroll']) / currency_rate)
                            elif bookie['info']['bookmaker'] == '1xbet':
                                currency_rate = 75
                                currency = 'usd'
                                size_of_stake = round(int(K * settings['bankroll']) / currency_rate)
                            else:
                                size_of_stake = round(int(K * settings['bankroll']) / currency_rate, -1)
                            print('------------------------------------------------------------')
                            message = f"{roi}%  {bookie['info']['bookmaker']}  {bookie['info']['sport']}\n"
                            message += f"margin: {round(margin * 100, 3)}, Ofair: {round(Ofair, 3)}\n"
                            # message += f"{bookie['info']['league']} * {bookie['info']['match']}\n"
                            message += f"`{bookie['info']['match'].split(' - ')[0]}`" \
                                       f" - " \
                                       f"`{bookie['info']['match'].split(' - ')[1]}`\n"

                            if boo['type'] in ['1', '2', 'X', '1X', '12', 'X2', '1H1',
                                               '1H2', '1HX', '1H1X', '1H12', '1HX2']:
                                message += f"{boo['type']} ---> min bet value: {min_bet_value}\n"
                                message += f"size of stake: {size_of_stake} {currency}" \
                                           f"      K={round(K, 2)}%\n\n"
                            else:
                                message += f"{boo['type']} {boo['line']} " \
                                           f" ---> min bet value: {min_bet_value}\n"
                                message += f"size of stake: {size_of_stake} {currency}" \
                                           f"      K={round(K, 2) * 100}%\n\n"

                            if boo['type'] in ['1', '2', 'X', '1X', '12', 'X2', '1H1',
                                               '1H2', '1HX', '1H1X', '1H12', '1HX2']:
                                message += f"{bookie['info']['url']}  —> {boo['type']} ({boo['odds']})\n"
                            else:
                                message += f"{bookie['info']['url']}  —> {boo['type']} {boo['line']} ({boo['odds']})\n"
                            message += f"********************\n"
                            message += f"Ps3838 league: {ps3838['info']['league']}\n"
                            message += f"{bookie['info']['bookmaker']} league: {bookie['info']['league']}\n"
                            message += f"****************\n"

                            message += f"{ps3838['info']['url'].replace(' ', '%20')}\n"
                            if ps['type'] in ['1', '2', 'X', '1X', '12', 'X2', '1H1',
                                              '1H2', '1HX', '1H1X', '1H12', '1HX2']:
                                message += f"`{ps3838['info']['match']}`   —> {ps['type']} ({ps['odds']})\n"
                            else:
                                message += f"`{ps3838['info']['match']}`   —> {ps['type']} {ps['line']} ({ps['odds']})\n"
                            message += '====================================\n'
                            print(message)
                            print(ps3838['info']['kickoff'], bookie['info']['kickoff'])
                            j = {ps3838['info']['id']: {
                                'match': ps3838['info']['match'],
                                'type': f"{ps['type']} {ps['line']}",
                                'pin_odds': ps['odds'],
                                'bookie_odds': boo['odds'],
                                'bookmaker': bookie['info']['bookmaker'],
                                'sport': ps3838['info']['sport'],
                                'league': ps3838['info']['league'],
                                'stake': size_of_stake,
                                'currency': currency,
                                'roi': roi,
                                'Ofair': Ofair,
                                'k': K,
                                'margin': margin,
                                'min_bet_value': min_bet_value
                            }}
                            params = {
                                'chat_id': settings['tg_bot']['chat_id'],
                                'text': message,
                                'parse_mode': 'MarkDown',
                                'disable_web_page_preview': True,
                                'reply_markup': json.dumps({
                                    "inline_keyboard": [[{
                                        "text": "complete",
                                        "callback_data": f"complete:{ps3838['info']['match']}"}]]
                                        # "callback_data": j}]]
                                })
                            }
                            # if ps not in already_was:
                            #     # asyncio.run(self.send_to_telegram(message, params))
                            #     already_was.append(ps)

                            if settings['profit'] < roi < 18:
                                print('HEEEREEE Make bettt')
                                # result = self.ma.make_bet(betdata)
                                result = True
                            else:
                                print('---------------------------------------------')
                                print('Check it manually!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                                print('---------------------------------------------')
                                result = False
                            if result is not False:
                                print('SLLLLLLLLLLLLLLLLEEEEEEEEEEEEEEEEEEEEEEEEEePPPPPPPPPPPPPPPP')
                                # time.sleep(10)
                            event = {
                                "id": ps3838['info']['id'],
                                "odds_ps": ps['odds'],
                                "type_name_ps": ps['type_name'],
                                "type_ps": ps['type'],
                                "boo_type": boo['type'],
                                "boo_line": boo['line'],
                                "line_ps": ps['line'],
                                "odds": boo['odds'],
                                "type_name": boo['type_name'],
                                "type": boo['type'],
                                "line": boo['line'],
                                "match": bookie['info']['match'],
                                "league_ps": ps3838['info']['league'],
                                "boo_league": bookie['info']['league'],
                                "match_ps": ps3838['info']['match'],
                                "matchcode": 1,
                                "margin": margin,
                                "n": n,
                                "setting_profit": settings['profit'],

                                # "boo_match": bookie['info']['match'],
                                # "boo_league": bookie['info']['league'],
                                # "boo_matchcode": bookie['info']['match'],
                                "sport_id": 29,
                                "sport": bookie['info']['sport'],
                                "bookmaker": "Ps3838",
                                "bookmaker_": bookie['info']['bookmaker'],
                                "boo_odds": boo['odds'],
                                "boo_url": bookie['info']['url'],
                                "ps_url": ps3838['info']['url'],
                                'roi': roi,
                                'K': K,
                                'O': Ofair,
                                "min_bet_value": min_bet_value,
                                "bankroll": settings['bankroll'],
                                "size_of_stake": 0,
                                "chat_id": -643582107,
                                # "pinncale_url":

                            }
                            # already_was.append(ps)
                            all.append(event)

        # with open('cache/cache.json', 'w') as f:
        #     json.dump(already_was, f)
        #     f.close()

        # if len(all) > 0:
        with open(f"cache/ps3838_vs_{bookie['info']['bookmaker']}.json", 'w') as f:
            json.dump(all, f)
            f.close()
        # return None
        return all

    def start(self):
        logging.debug(f'Start first async loop')
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self.run())
        loop.run_until_complete(future)
        search_coins = SearchCoincidence()
        pinnacle = future.result()[0]
        matches = []
        for i, one_booker_matches in enumerate(future.result()):
            if i == 0:
                continue
            # print(one_booker_matches[0]['info']['bookmaker'])
            matches_ = search_coins.launcher(pinnacle, one_booker_matches)
            try:
                logging.info(f"{len(matches_)} coincidence between pinnacle and {one_booker_matches[0]['info']['bookmaker']}")
            except IndexError:
                logging.error(f"!!!!!!!!!!!!!!!!!!!!!!hz whats error")
            matches += matches_
            try:
                len(matches)
            except TypeError:
                logging.warning(f'no bookerlists after searching coincidence')



        all = []
        for match in matches:
            ttt = self.search_difference(match[0], match[1])
            all += ttt

        for boo in settings['filter_by_bookie']:
            if boo == 'Ps3838':
                continue
            matches___ = []
            for value_match in all:
                if boo != value_match['bookmaker_']:
                    continue
                matches___.append(value_match)
            with open(f"cache/ps3838_vs_{boo}.json", 'w') as f:
                json.dump(matches___, f, indent=4)
                f.close()

    def loop2(self, fork):
        for n in range(1):
            logging.debug(f'Start first async loop')
            loop = asyncio.get_event_loop()
            future = asyncio.ensure_future(self.check_again_before_bet(fork))
            loop.run_until_complete(future)
            if fork.bets[0].local_bet in future.result()[0] and fork.bets[1].local_bet in future.result()[1]:
                index = future.result()[0].index(fork.bets[0].local_bet)
                return future.result()[0][index][1], 1
            return -1, 0

    @staticmethod
    async def message_to_dict(message: str) -> dict:
        to_list = message.split('\n')
        match_data = {
            'match': to_list[-2].split('   —> ')[0],
            'type': to_list[-2].split('   —> ')[1].split(' (')[0],
            'pin_odds': float(to_list[-2].split('   —> ')[1].split(' (')[1].replace(')', '')),
            'bookie_odds': float(to_list[6].split('  —> ')[1].split('(')[1].split(')')[0]),
            'bookmaker': to_list[0].split('  ')[1],
            'sport': to_list[0].split('  ')[-1],
            'league': to_list[8],
            'bookie_league': to_list[9],
            'stake': float(to_list[4].split('      ')[0].split(': ')[1].split(' ')[0]),
            'currency': to_list[4].split('      ')[0].split(': ')[1].split(' ')[1],
            'roi': float(to_list[0].split('%')[0]),
            'Ofair': float(to_list[1].split(',')[1].split(': ')[1]),
            'k': float(to_list[4].split('K=')[1].split('%')[0]),
            'margin': float(to_list[1].split(',')[0].split(': ')[1]),
            'min_bet_value': float(to_list[3].split('min bet value: ')[1])
        }
        return match_data

    async def get_telegram_status(self):
        action = ''
        url = f"https://api.telegram.org/bot{settings['tg_bot']['token']}/getUpdates?offset={self.offset}"
        time_now = int(time.time())
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                messages = await response.json()
        if messages.get('ok') is True:
            for message in messages['result']:
                if message.get('callback_query') is not None:
                    if message["callback_query"]["from"]["id"] == 38481876 and\
                            "complete:" in message["callback_query"]["data"]:
                        action = 'complete'
                        match_data = await self.message_to_dict(message["callback_query"]["message"]["text"])
                        callback_query_id = message["callback_query"]['id']
                        self.offset = message['update_id'] + 1
                if message.get('message') is not None:
                    if (time_now - message['message']['date']) < 120:
                        if message["message"]["from"]["id"] == 38481876 and message["message"]["text"] == "stop":
                            action = 'stop'
                            self.offset = message['update_id'] + 1
                        elif message["message"]["from"]["id"] == 38481876 and message["message"]["text"] == "start":
                            action = 'start'
                            self.offset = message['update_id'] + 1
                        elif message["message"]["from"]["id"] == 38481876 and message["message"]["text"] == "clear":
                            action = 'clear'
                            self.offset = message['update_id'] + 1
                        elif message["message"]["from"]["id"] == 38481876 and message["message"]["text"] == "clear_all":
                            action = 'clear_all'
                            self.offset = message['update_id'] + 1
        if action != '':
            if action in ['start', 'stop']:
                status = json.dumps({"status": f"{action}"})
                async with aiofiles.open('cache/action.json', 'w') as f:
                    await f.write(status)
                logging.info(f'{action} value_bet')
            if action in ['clear', 'clear_all']:
                async with aiofiles.open('cache/cache.json', 'w') as f:
                    await f.write(json.dumps([]))
                logging.info(f'cache was cleared')
            if action == 'clear_all':
                async with aiofiles.open('cache/bet_already.json', 'w') as f:
                    await f.write(json.dumps([]))
                logging.info(f'bet already cache was cleared')
            if action == 'complete':
                try:
                    with open('cache/bet_already.json', 'r') as f:
                        bet_already = json.load(f)
                        f.close()
                except (json.decoder.JSONDecodeError, FileNotFoundError):
                    bet_already = []
                if match_data['match'] in bet_already:
                    logging.info(f"match already is in bet_already cache")
                    text = 'Match already was added!'
                else:
                    bet_already.append(match_data['match'])
                    async with aiofiles.open('cache/bet_already.json', 'w') as f:
                        await f.write(json.dumps(bet_already))
                    async with aiofiles.open('cache/staistics.txt', 'a') as f:
                        await f.write(f'{json.dumps(match_data)}\n')
                    logging.info(f"{match_data['match']} added to exclusions")
                    text = 'Match completed!'
                url_delete_msg = f"https://api.telegram.org/bot{settings['tg_bot']['token']}/answerCallbackQuery" \
                                     f"?chat_id=38481876&callback_query_id={callback_query_id}&text={text}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url_delete_msg) as response:
                        await response.json()

    async def check_status(self):
        try:
            async with aiofiles.open('cache/action.json', 'r') as f:
                status = await f.read()
                status = json.loads(status)
                if status['status'] == 'start':
                    return True
                else:
                    return False
        except Exception as e:
            logging.info(f'action file is empty')
            return False


if __name__ == "__main__":
    start = ForkScanner()
    while True:
        try:
            status = asyncio.run(start.check_status())
            if status:
                logging.info(f'Start Scanner...')
                start.start()
                logging.info(f'Finish Scanner...')
            time.sleep(5)
            asyncio.run(start.get_telegram_status())
        except Exception as e:
            # raise e
            logging.error(f'{e}')
            time.sleep(5)
