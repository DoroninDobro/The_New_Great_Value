import json
import time
import logging
import asyncio
import aiohttp
import aiofiles
from typing import Dict

from libs.helper import Helper
from libs.models import Settings


helper = Helper()


class Telegram:
    def __init__(self):
        self.settings: Settings = helper.get_settings()
        self.offset = ''
        self.pause_list = []

    async def set_bank(self, message: str) -> None:
        print(message)
        split_message = message.split(' ')
        if len(split_message) != 3:
            await self.answer(f"Wrong command. Right example: \n /bank 1win 1000")
        bookie = split_message[1]
        try:
            bankroll = int(split_message[2])
        except ValueError:
            await self.answer(f"bankroll must be integer.")
            return
        if not isinstance(bankroll, int):
            await self.answer(f"bankroll must be integer.")
        is_done = await helper.set_bankroll(bankroll, bookie)
        if is_done:
            await self.answer(f"Bankroll for {bookie} updated")
        elif is_done is False:
            await self.answer(f"We haven't such bookie!")
        else:
            await self.answer(f"{is_done}")

    @staticmethod
    async def message_to_dict(message: str) -> dict:
        to_list = message.split('\n')
        if len(to_list) == 15:
            to_list[2] = f"{to_list[2]}{to_list[3]}"
            to_list.remove(to_list[3])
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
        while True:
            action = ''
            # callback_query_id = ''
            # kickoff = time.time() + 84000
            # match_data = {}
            time_now = int(time.time())
            messages: Dict = await self.get_updates()
            if messages.get('ok'):
                for message in messages['result']:
                    if message.get('callback_query') is not None:
                        callback_user_id = message["callback_query"]["from"]["id"]
                        match_data = await self.message_to_dict(message["callback_query"]["message"]["text"])
                        match_id = message["callback_query"]["data"].split('||')[1]
                        kickoff = int(message["callback_query"]["data"].split('||')[2])
                        callback_query_id = message["callback_query"]['id']
                        self.offset = message['update_id'] + 1
                        if callback_user_id in self.settings.telegram.admin_id\
                                and "complete:" in message["callback_query"]["data"]:
                            await self.do_action('complete', match_id, kickoff, match_data, callback_query_id)
                        if callback_user_id in self.settings.telegram.admin_id\
                                and "skip:" in message["callback_query"]["data"]:
                            await self.do_action('skip', match_id, kickoff, match_data, callback_query_id)
                    if message.get('message') is not None:
                        if (time_now - message['message']['date']) < 120:
                            user_id = message["message"]["from"]["id"]
                            message_body = message.get("message", {}).get("text")
                            if user_id in self.settings.telegram.admin_id and '/bank' in message_body:
                                self.offset = message['update_id'] + 1
                                await self.set_bank(message_body)
                            if user_id in self.settings.telegram.admin_id and message_body == "stop":
                                action = 'stop'
                                self.offset = message['update_id'] + 1
                            if user_id in self.settings.telegram.admin_id\
                                    and "pause" in message["message"]["text"].lower():
                                bookie = message["message"]["text"].split('pause ')[1]
                                self.offset = message['update_id'] + 1
                                if bookie in self.settings['filter_by_bookie']:
                                    self.pause_list.append(bookie)
                            if user_id in self.settings.telegram.admin_id\
                                    and "play" in message["message"]["text"].lower():
                                bookie = message["message"]["text"].split('play ')[1]
                                self.offset = message['update_id'] + 1
                                if bookie in self.settings['filter_by_bookie']:
                                    self.pause_list.remove(bookie)
                            elif user_id in self.settings.telegram.admin_id and message["message"]["text"] == "start":
                                action = 'start'
                                self.offset = message['update_id'] + 1
                    await asyncio.sleep(0)
            if action in ['start', 'stop']:
                status = json.dumps({"status": f"{action}"})
                async with aiofiles.open('cache/action.json', 'w') as f:
                    await f.write(status)
                logging.info(f'{action} value_bet')
            await asyncio.sleep(1)

    async def do_action(self, action: str, match_id: int, kickoff: int, match_data: dict, callback_query_id: int):
        text = f'Match {action if action != "skip" else "skippe"}d!'
        while True:
            try:
                async with aiofiles.open(f'cache/_{action}.json', 'r') as f:
                    cache = json.loads(await f.read())
                    break
            except (json.decoder.JSONDecodeError, FileNotFoundError):
                await asyncio.sleep(0)
                continue
            await asyncio.sleep(0)
        # print(match_id, cache.keys())
        # print(type(match_id), type(list(cache.keys())[0]))
        if match_id in cache.keys():
            logging.info(f"Match already is in {action} list")
            text = f'Match already was added to {action} list!'
        else:
            cache[match_id] = {'match': match_data.get('match'), 'kickoff': kickoff}
            async with aiofiles.open(f'cache/_{action}.json', 'w') as f:
                await f.write(json.dumps(cache, indent=4))
            async with aiofiles.open('cache/statistics.txt', 'a') as f:
                await f.write(f'{json.dumps(match_data)}\n')
            logging.info(f"{match_data.get('match')} added to exclusions")
        url_delete_msg = f"https://api.telegram.org/bot{self.settings.telegram.token}/answerCallbackQuery" \
                         f"?chat_id=38481876&callback_query_id={callback_query_id}&text={text}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url_delete_msg) as response:
                await response.json()

    async def cleaner(self):
        while True:
            bet_already: dict = await self.read_cache('complete')
            if bet_already != {}:
                await self.clean_bet_already_if_match_has_ended(bet_already, 'complete')
            skip: dict = await self.read_cache('skip')
            if skip != {}:
                await self.clean_bet_already_if_match_has_ended(skip, 'skip')
            already_was: dict = await self.read_cache('was')
            if already_was != {}:
                await self.clean_already_was_if_time_out(already_was)
            await asyncio.sleep(60)

    @staticmethod
    async def read_cache(filename) -> dict:
        try:
            async with aiofiles.open(f'cache/_{filename}.json', 'r') as f:
                data = json.loads(await f.read())
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            return {}
        return data

    @staticmethod
    async def clean_already_was_if_time_out(already_was: dict) -> None:
        cleaned_already_was = {}
        for event, x in already_was.items():
            if time.time() - x.get('time', 0) < 180:
                cleaned_already_was[event] = x
            else:
                logging.info(f"{event} already was. Delete from already was list.")
            await asyncio.sleep(0)
        if cleaned_already_was != already_was:
            async with aiofiles.open('cache/_was.json', 'w') as f:
                await f.write(json.dumps(cleaned_already_was, indent=4))

    @staticmethod
    async def clean_bet_already_if_match_has_ended(bet_already: dict, action: str) -> None:
        cleaned_bet_already = {}
        for event, x in bet_already.items():
            if x.get('kickoff', 10000000000000000) + 84000 - time.time() > 0:
                cleaned_bet_already[event] = x
            else:
                logging.info(f"{event} already was. Delete from {action} list.")
            await asyncio.sleep(0)
        if cleaned_bet_already != bet_already:
            async with aiofiles.open(f'cache/_{action}.json', 'w') as f:
                await f.write(json.dumps(cleaned_bet_already, indent=4))

    @staticmethod
    async def check_status():
        try:
            async with aiofiles.open('cache/action.json', 'r') as f:
                status = await f.read()
                status = json.loads(status)
                if status['status'] == 'start':
                    return True
                else:
                    return False
        except FileNotFoundError:
            logging.info(f'action file is empty')
            return True

    async def answer(self, text: str, callback_data=False) -> None:
        url = f"https://api.telegram.org/bot{self.settings.telegram.token}/sendMessage"
        params = {
            'chat_id': self.settings.telegram.chat_id,
            'text': text,
            'parse_mode': 'MarkDown',
            'disable_web_page_preview': True
        }
        if callback_data:
            params['reply_markup'] = json.dumps(callback_data)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, json=params) as response:
                r = await response.json()
                print(r)

    async def get_updates(self) -> Dict:
        url = f"https://api.telegram.org/bot{self.settings.telegram.token}/getUpdates?offset={self.offset}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                messages = await response.json()
        return messages

    async def send_to_telegram(self, message, params):
        async with aiohttp.ClientSession() as session:
            send_message_url = f"https://api.telegram.org/bot{self.settings.telegram.token}/sendMessage"
            async with session.get(send_message_url, json=params) as response:
                # logging.info('message sent')
                logging.debug(f"{await response.json()}")
