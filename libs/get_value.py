import json
import time
import asyncio
import aiofiles
import logging
from typing import List, Dict


from koloss_settings import settings
from libs.telegram import Telegram
from libs.outcomes import Outcomes
from libs.helper import Helper
from libs.models import Settings, Bookmaker


outcomes = Outcomes()
tg = Telegram()
helper = Helper()


class GetValue:

    def __init__(self):
        self.settings: Settings = helper.get_settings()

    @staticmethod
    async def check_in_cache(action) -> dict:
        i = 0
        while True:
            try:
                async with aiofiles.open(f'cache/_{action}.json', 'r') as f:
                    cache = await f.read()
                    return json.loads(cache)
            except (json.decoder.JSONDecodeError, FileNotFoundError):
                logging.error(f"Can't read {action} file")
                await asyncio.sleep(0)
                i += 1
                if action == 'was' and i > 10:
                    return {}
                continue

    async def check_if_we_must_skip(self, ps3838: Dict) -> bool:
        if ps3838.get('converted_markets') is None:
            return True
        match_id = str(ps3838.get('info', {}).get('id'))
        if ps3838.get('info', {}).get('kickoff') - time.time() > 86400:
            return True
        bet_already = await self.check_in_cache('complete')
        if match_id in bet_already.keys():
            return True
        skip = await self.check_in_cache('skip')
        if match_id in skip.keys():
            return True
        was_already = await self.check_in_cache('was')
        if match_id in was_already.keys():
            return True
        return False

    async def search_difference(self, ps3838: Dict, bookie: Dict) -> List:
        self.settings: Settings = helper.get_settings()
        bookmaker_name = bookie.get('info', {}).get('bookmaker')
        bookie_settings = Bookmaker(**self.settings.bookmakers[bookmaker_name])
        check: bool = await self.check_if_we_must_skip(ps3838)
        already_was: Dict = await self.check_in_cache('was')
        if check:
            return []
        all = []
        for ps in ps3838['converted_markets']:
            for boo in bookie['converted_markets']:
                if type(ps) is bool or boo is bool:
                    continue
                if ps['type'] == boo['type'] and ps['line'] == boo['line'] and ps['type_name'] == boo['type_name']:
                    if (ps['odds'] <= settings['coef_max_limit'] and ps['odds'] >= settings['coef_min_limit']):
                        margin, n = await outcomes.get_margin(ps, ps3838)
                        Ofair = n * ps['odds'] / (n - margin * ps['odds'])
                        min_bet_value = round(Ofair * self.settings.profit, 2)
                        roi = round((boo['odds'] / Ofair - 1) * 100, 3)
                        if boo['odds'] >= min_bet_value:
                            K = (self.settings.profit - 1) / (min_bet_value - 1)
                            size_of_stake = int(K * bookie_settings.bankroll * self.settings.bank_multiplier)
                            size_of_stake = round(size_of_stake / bookie_settings.currency_rate, bookie_settings.round)
                            print('------------------------------------------------------------')
                            message = f"{roi}%  {bookie['info']['bookmaker']}  {bookie['info']['sport']}\n"
                            message += f"margin: {round(margin * 100, 3)}, Ofair: {round(Ofair, 3)}\n"
                            message += f"`{bookie['info']['match'].split(' - ')[0]}`" \
                                       f" - " \
                                       f"`{bookie['info']['match'].split(' - ')[1]}`\n"

                            if boo['type'] in ['1', '2', 'X', '1X', '12', 'X2', '1H1',
                                               '1H2', '1HX', '1H1X', '1H12', '1HX2']:
                                message += f"{boo['type']} ---> min bet value: {min_bet_value}\n"
                                message += f"size of stake: {size_of_stake} {bookie_settings.currency}" \
                                           f"      K={round(K, 2)}%\n\n"
                            else:
                                message += f"{boo['type']} {boo['line']} " \
                                           f" ---> min bet value: {min_bet_value}\n"
                                message += f"size of stake: {size_of_stake} {bookie_settings.currency}" \
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
                            if roi > 50:
                                message += '!!!!!!!!!!!!!!HIGH ROI TAKE A LOOK!!!!!!!!!!!!!!!!!'
                            print(message)
                            print(ps3838['info']['kickoff'], bookie['info']['kickoff'])
                            params = {
                                'chat_id': self.settings.telegram.chat_id,
                                'text': message,
                                'parse_mode': 'MarkDown',
                                'disable_web_page_preview': True,
                                'reply_markup': json.dumps({
                                    "inline_keyboard": [[
                                        {
                                            "text": "skip",
                                            "callback_data": f"skip:||{ps3838['info']['id']}"
                                                             f"||{ps3838['info']['kickoff']}"
                                        },
                                        {
                                            "text": "complete",
                                            "callback_data": f"complete:||{ps3838['info']['id']}"
                                                             f"||{ps3838['info']['kickoff']}"
                                        },
                                    ]
                                    ]
                                })
                            }
                            if self.settings.telegram.enable:
                                await tg.send_to_telegram(message, params)
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
                            }
                            all.append(event)
                            already_was[ps3838['info']['id']] = {'time': time.time()}
                await asyncio.sleep(0)
            await asyncio.sleep(0)

        # async with aiofiles.open('cache/_was.json', 'w') as f:
        #     data = json.dumps(already_was, indent=4)
        #     await f.write(data)
        with open('cache/_was.json', 'w') as f:
            f.write(json.dumps(already_was, indent=4))
            f.close()

        # if len(all) > 0:
        # with open(f"cache/ps3838_vs_{bookie['info']['bookmaker']}.json", 'w') as f:
        #     json.dump(all, f)
        #     f.close()
        # return None
        return all
