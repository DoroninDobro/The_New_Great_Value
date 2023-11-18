import asyncio
import json
from fuzzywuzzy import fuzz
import logging
import aiofiles

from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)

RATIO = settings['ratio']


class SearchCoincidence:

    async def launcher(self, pinnacle, matches):
        logging.info(f"{len(matches)} matches found")
        coins_matches = await self.start_search_coincidence(pinnacle, matches)
        return coins_matches

    @staticmethod
    async def prepare_team(match: str) -> str:
        teams = match.split((' - '))
        if len(teams) == 1:
            teams = match.split((' — '))
        if len(teams) == 1:
            teams = match.split(('-vs-'))
        home_team = teams[0].lower()
        away_team = teams[1].lower()
        return home_team, away_team

    async def start_search_coincidence(self, pinnacle: list, matches: list) -> list:
        try:
            async with aiofiles.open('../cache/bet_already_koloss.json', 'r') as f:
                bet_already = json.loads(await f.read())
                f.close()
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            bet_already = {}
        nu_list = []
        empty_matches = 0
        for i, v in enumerate(pinnacle):
            if v is None:
                empty_matches += 1
                continue
            if v['info']['match'] in bet_already:
                logging.info(f"{v['info']['match']} already has stake")
                continue
            if not v:
                continue
            try:
                home_team_v, away_team_v = await self.prepare_team(v['info']['match'])
            except IndexError:
                continue
            for ii, vv in enumerate(matches):
                if v['info']['sport'] != vv['info']['sport']:
                    if v['info']['sport'] == 'Soccer' and vv['info']['sport'] != 'Football':
                        continue
                if vv['info']['bookmaker'] not in ['Betfair']:  #, 'Snai', 'Admiralbet']:
                    if v['info']['kickoff'] != vv['info']['kickoff']:
                        continue
                try:
                    home_team_vv, away_team_vv = await self.prepare_team(vv['info']['match'])
                except IndexError:
                    continue
                compare_home = fuzz.partial_ratio(home_team_v, home_team_vv)
                compare_away = fuzz.partial_ratio(away_team_v, away_team_vv)
                ratio_ = RATIO
                if v['info']['sport'] == 'Tennis':
                    ratio_ = 60
                if compare_home > ratio_ and compare_away > ratio_:
                    if v['info']['sport'] != 'Tennis':
                        check_by_league = await self.check_by_league(v, vv)
                        if check_by_league is True:
                            logging.info(f"{vv['info']['bookmaker']}: Skip {v['info']['league']} * {v['info']['match']}"
                                         f" *** {vv['info']['league']} * {vv['info']['match']}")
                            continue
                    nu_list.append([v, vv])
                await asyncio.sleep(0)
            await asyncio.sleep(0)
        if empty_matches > 0:
            logging.warning(f"{empty_matches} pinnacle matches with None markets.")
        return nu_list

    @staticmethod
    async def check_by_league(v: dict, vv: dict) -> bool:
        match_name_v = v['info']['match']
        league_v = v['info']['league']
        match_name_vv = vv['info']['match']
        league_vv = vv['info']['league']
        if league_vv is None:
            return False
        if 'reserve' in league_v.lower() or 'reserve' in match_name_v.lower():
            if 'reserve' not in league_vv.lower() and 'reserve' not in match_name_vv.lower():
                return True
        if 'u19' in league_v.lower() or 'u19' in match_name_v.lower():
            if 'u19' not in league_vv.lower() and 'u19' not in match_name_vv.lower():
                return True
        if 'u20' in league_v.lower() or 'u20' in match_name_v.lower():
            if 'u20' not in league_vv.lower() and 'u20' not in match_name_vv.lower():
                return True
        if 'u21' in league_v.lower() or 'u21' in match_name_v.lower():
            if 'u21' not in league_vv.lower() and 'u21' not in match_name_vv.lower():
                return True
        if 'u23' in league_v.lower() or 'u23' in match_name_v.lower():
            if 'u23' not in league_vv.lower() and 'u23' not in match_name_vv.lower():
                return True
        if 'women' in league_v.lower()\
                or 'women' in match_name_v.lower()\
                or 'frauen' in league_v.lower() \
                or 'femminile' in league_v.lower()\
                or 'feminine' in league_v.lower()\
                or 'femenina' in league_v.lower()\
                or 'fem.' in league_v.lower()\
                or 'femm.' in league_v.lower()\
                or ' w ' in match_name_v.lower()\
                or '(wom)' in match_name_v.lower()\
                or '(w)' in match_name_v.lower():
            if 'women' not in league_vv.lower()\
                    and 'women' not in match_name_vv.lower()\
                    and 'frauen' not in league_vv.lower() \
                    and 'femminile' not in league_vv.lower()\
                    and 'feminine' not in league_vv.lower()\
                    and 'femenina' not in league_vv.lower()\
                    and 'fem.' not in league_vv.lower()\
                    and 'femm.' not in league_vv.lower()\
                    and ' w ' not in match_name_vv.lower()\
                    and '(wom)' not in match_name_vv.lower()\
                    and '(w)' not in match_name_vv.lower():
                return True
        if 'reserve' in league_vv.lower() or 'reserve' in match_name_vv.lower():
            if 'reserve' not in league_v.lower() and 'reserve' not in match_name_v.lower():
                return True
        if 'u19' in league_vv.lower() or 'u19' in match_name_vv.lower():
            if 'u19' not in league_v.lower() and 'u19' not in match_name_v.lower():
                return True
        if 'u20' in league_vv.lower() or 'u20' in match_name_vv.lower():
            if 'u20' not in league_v.lower() and 'u20' not in match_name_v.lower():
                return True
        if 'u21' in league_vv.lower() or 'u21' in match_name_vv.lower():
            if 'u21' not in league_v.lower() and 'u21' not in match_name_v.lower():
                return True
        if 'u23' in league_vv.lower() or 'u23' in match_name_vv.lower():
            if 'u23' not in league_v.lower() and 'u23' not in match_name_v.lower():
                return True
        if 'women' in league_vv.lower() or 'women' in match_name_vv.lower() or 'frauen' in league_vv.lower() \
                or 'femminile' in league_vv.lower()\
                or 'feminine' in league_vv.lower()\
                or 'fem.' in league_vv.lower()\
                or 'femm.' in league_vv.lower()\
                or 'femenina' in league_vv.lower()\
                or ' w ' in match_name_vv.lower()\
                or '(wom)' in match_name_vv.lower()\
                or '(w)' in match_name_vv.lower():
            if 'women' not in league_v.lower()\
                    and 'women' not in match_name_v.lower()\
                    and 'frauen' not in league_v.lower()\
                    and 'femminile' not in league_v.lower()\
                    and 'feminine' not in league_v.lower()\
                    and 'fem.' not in league_v.lower()\
                    and 'femm.' not in league_v.lower()\
                    and 'femenina' not in league_v.lower()\
                    and ' w ' not in match_name_v.lower()\
                    and '(wom)' not in match_name_v.lower()\
                    and '(w)' not in match_name_v.lower():
                return True
        return False
