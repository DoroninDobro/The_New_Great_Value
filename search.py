import json
from fuzzywuzzy import fuzz
# from transliterate import translit
import logging

from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)

ALLOWED_SPORTS = ['Футбол', 'Хоккей', 'Баскетбол',
                      'Теннис', 'Гандбол', 'Настольный теннис',
                      'Волейбол', 'Бейсбол', 'Киберхоккей',
                      'Кибербаскетбол', 'Крикет',
                      'Киберспорт']

RATIO = settings['ratio']

FILTER_BY_SPORT = [
# 'Футбол',
    #"Теннис",
    # 'Настольный теннис',
    # 'Киберспорт',
    # 'Киберхоккей', 'Кибербаскетбол',
    # 'Крикет',
    # 'Флорбол',
    # 'Гольф',
    # 'Снукер',
]
FILTER_BY_BOOKIE = [
    'Xstavka',
    'Baltbet',
    'Sunbet',
    'Olimp'
]


class SearchCoincidence:

    def launcher(self, pinnacle, matches):
        logging.info(f"{len(matches)} matches found")
        coins_matches = self.start_search_coincidence(pinnacle, matches)
        return coins_matches

    def prepare_team(self, match):
        teams = match.split((' - '))
        if len(teams) == 1:
            teams = match.split((' — '))
        if len(teams) == 1:
            teams = match.split(('-vs-'))
        home_team = teams[0].lower()
        away_team = teams[1].lower()
        # print(home_team, '----------------',away_team)
        return home_team, away_team

    def check_match_is_allowed(self, match):
        if ' - ' in match or ' — ' in match:
            if 'УГЛ' in match:
                return False
            if 'офсайды' in match:
                return False
            if 'фолы' in match:
                return False
            if 'штанги' in match:
                return False
            if 'удары' in match:
                return False
            if 'голы' in match:
                return False
            if 'кол-во' in match:
                return False
            if 'ЖК' in match:
                return False
            if '(ауты)' in match:
                return False
            else:
                return True
        else:
            return False

    def check_match_is_allowed_by_bookie(self, bookie):
        if len(FILTER_BY_SPORT) == 0:
            return True
        if bookie not in FILTER_BY_BOOKIE:
            return False
        else:
            return True

    def filter_by_sport(self, sport):
        if len(FILTER_BY_SPORT) == 0:
            return True
        if sport not in FILTER_BY_SPORT:
            return False
        else:
            return True

    def start_search_coincidence(self, pinnacle, matches):
        try:
            with open('cache/bet_already.json', 'r') as f:
                bet_already = json.load(f)
                f.close()
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            bet_already = []
        nu_list = []
        # already_checked = []
        empty_matches = 0
        for i, v in enumerate(pinnacle):
            if v is None:
                empty_matches += 1
                continue
            if v['info']['match'] in bet_already:
                logging.info(f"{v['info']['match']} already has stake")
                continue
            # print(v)
            if not v:
                continue
            try:
                home_team_v, away_team_v = self.prepare_team(v['info']['match'])
            except IndexError:
                continue
            for ii, vv in enumerate(matches):
                if v['info']['sport'] != vv['info']['sport']:
                    if v['info']['sport'] == 'Soccer' and vv['info']['sport'] != 'Football':
                        continue
                # if vv['info']['bookmaker'] not in ['Betfair', 'Marathonbet']:  #, 'Snai', 'Admiralbet']:
                if vv['info']['bookmaker'] not in ['Betfair']:  #, 'Snai', 'Admiralbet']:
                    if v['info']['kickoff'] != vv['info']['kickoff']:
                        # print(v['info']['kickoff'], vv['info']['kickoff'])
                        continue

                try:
                    home_team_vv, away_team_vv = self.prepare_team(vv['info']['match'])
                except IndexError:
                    continue
                compare_home = fuzz.partial_ratio(home_team_v, home_team_vv)
                compare_away = fuzz.partial_ratio(away_team_v, away_team_vv)
                ratio_ = RATIO
                if v['info']['sport'] == 'Tennis':
                    ratio_ = 60
                if compare_home > ratio_ and compare_away > ratio_:
                    if v['info']['sport'] != 'Tennis':
                        check_by_league = self.check_by_league(v, vv)
                        if check_by_league is True:
                            # print(bookie_v, bookie_vv)
                            logging.info(f"Skip {v['info']['league']} * {v['info']['match']}"
                                         f" *** {vv['info']['league']} * {vv['info']['match']}")
                            continue
                    nu_list.append([v, vv])
        # print(nu_list)
        logging.warning(f"{empty_matches} pinnacle matches with None markets.")
        return nu_list

    def check_if_already_checked(self, already, check_this):
        for already_ in already:
            if sorted(already_) == sorted(check_this):
                # print(sorted(already_), sorted(check_this))
                return True

    def check_by_league(self, v, vv):
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

    def define_coins(self, nu_list):
        # print(nu_list)
        lists = sorted([sorted(x) for x in nu_list]) #Sorts lists in place so you dont miss things. Trust me, needs to be done.
        resultlist = []  # Create the empty result list.
        if len(lists) >= 1:  # If your list is empty then you dont need to do anything.
            resultlist = [lists[0]]  # Add the first item to your resultset
            if len(lists) > 1:  # If there is only one list in your list then you dont need to do anything.
                for l in lists[1:]:  # Loop through lists starting at list 1
                    listset = set(l)  # Turn you list into a set
                    merged = False  # Trigger
                    for index in range(len(resultlist)):  # Use indexes of the list for speed.
                        rset = set(resultlist[index])  # Get list from you resultset as a set
                        if len(listset & rset) != 0: # If listset and rset have a common value then the len will be greater than 1
                            resultlist[index] = list(listset | rset) # Update the resultlist with the updated union of listset and rset
                            merged = True # Turn trigger to True
                            break  # Because you found a match there is no need to continue the for loop.
                    if not merged:  # If there was no match then add the list to the resultset, so it doesnt get left out.
                        resultlist.append(l)
        logging.info(f"Found {len(resultlist)} coincidence")
        return resultlist

    @staticmethod
    def print_coins(self, matches, resultlist):
        for smil in resultlist:
            print('------')
            for il in smil:
                print(matches[il][1], matches[il][5], matches[il][4])
        print(resultlist)
