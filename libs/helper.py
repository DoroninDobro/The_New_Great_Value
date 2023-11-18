import time
import asyncio
import json
import logging
import yaml
import aiofiles

from typing import List, Dict, Union

from libs.models import Settings


class Helper:

    def __init__(self):
        self.settings_file = 'settings.yaml'
        self.settings = self.get_settings()
        self.bookmaker_settings = self.settings.bookmakers

    @staticmethod
    async def get_data(file: str) -> Dict:
        try:
            async with aiofiles.open(file, 'r') as f:
                events = json.loads(await f.read())
        except json.decoder.JSONDecodeError:
            events = {}
            logging.error('action-list is empty')
        except FileNotFoundError:
            logging.error('file not found')
            events = {}
        return events

    @staticmethod
    async def save_data(file: str, array: Union[List, Dict]) -> None:
        try:
            async with aiofiles.open(file, 'w') as f:
                to_string = json.dumps(array, indent=4)
                await f.write(to_string)
        except json.decoder.JSONDecodeError:
            raise

    async def clean_old_matches(self) -> None:
        action = await self.get_data('action.json')
        new_action = {}
        for key, item in action.items():
            if time.time() - item.get('added_time', 1000000) > 172800:
                new_action[key] = item
            await asyncio.sleep(0)
        await self.save_data(new_action)

    def get_settings(self) -> Settings:
        with open(self.settings_file) as f:
            try:
                settings = yaml.safe_load(f)
                settings = Settings(**settings)
            except yaml.YAMLError as exception:
                logging.info(exception)
        return settings

    async def set_bankroll(self, bankroll: int, bookie: str) -> bool:
        with open(self.settings_file) as f:   # This block scripts
            try:
                settings = yaml.safe_load(f)
            except yaml.YAMLError as exception:
                logging.info(exception)
        if bookie in list(settings['bookmakers'].keys()):
            settings['bookmakers'][bookie]['bankroll'] = bankroll
            with open(self.settings_file, 'w') as f:  # This block scripts
                yaml.dump(settings, f)
            return True
        else:
            return False
