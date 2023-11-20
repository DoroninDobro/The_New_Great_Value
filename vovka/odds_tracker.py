from datetime import datetime, timedelta


class OddsHistory:
    def __init__(self, initial_odds):
        self.history = [(datetime.now(), initial_odds)]

    def update(self, new_odds):
        self.history.append((datetime.now(), new_odds))

    def get_significant_drops(self, time_span_minutes, significance_percent):
        now = datetime.now()
        significant_drops = []
        for time, odds in self.history:
            if now - time <= timedelta(minutes=time_span_minutes):
                for past_time, past_odds in self.history:
                    if past_time < time:
                        if past_odds > odds and ((past_odds - odds) / past_odds) * 100 >= significance_percent:
                            significant_drops.append((time, past_odds, odds))
        return significant_drops
        
    def is_stale(self, stale_time_hours=1):
        if not self.history:
            return True
        return datetime.now() - self.history[-1][0] > timedelta(hours=stale_time_hours)


class OddsTracker:
    def __init__(self, significance_percent, time_span_minutes):
        self.odds_data = {}
        self.match_data = {}
        self.significance_percent = significance_percent
        self.time_span_minutes = time_span_minutes
        self.recorded_drops = set()  # Добавляем множество для хранения уже записанных строк

    def update_data(self, new_data):
        for market in new_data:
            # Проверяем, существует ли ключ 'converted_markets' и не равен ли он None
            #!
            #!
            # Тут надо добавить исчезновение кэфов
            #!
            #!
            if 'converted_markets' in market and market['converted_markets'] is not None:
                sport = market['info']['sport']
                market_id = market['info']['id']
                self.match_data[market_id] = {'sport': sport, 'match': market['info']['match'], 'league': market['info']['league']}
                for odds_info in market['converted_markets']:
                    if odds_info['odds'] < 4.5:
                        key = (market_id, odds_info['type'], odds_info['line'])
                        if key not in self.odds_data:
                            self.odds_data[key] = OddsHistory(odds_info['odds'])
                        else:
                            self.odds_data[key].update(odds_info['odds'])
                            
    def check_for_significant_drops(self):
        for key, history in self.odds_data.items():
            drops = history.get_significant_drops(self.time_span_minutes, self.significance_percent)
            if drops:
                market_id, market_type, line = key
                match_info = self.get_match_info(market_id)
                formatted_drops = [(drop_time.strftime('%Y-%m-%d %H:%M:%S'), old_odds, new_odds) for drop_time, old_odds, new_odds in drops]
                #print(f"Significant drops for {match_info['match']} in {match_info['league']}: {formatted_drops}")
                print('SUCCESS!')
                self.save_drops_to_file(match_info, market_type, line, formatted_drops, 'significant_drops.txt')

    def save_drops_to_file(self, match_info, market_type, line, drops, file_path):
        # здесь название спорта нету
        with open(file_path, 'a') as file:
            for drop in drops:
                formatted_time, old_odds, new_odds = drop
                sport = match_info.get('sport', 'Unknown Sport')
                # Форматируем строку без времени для проверки уникальности
                drop_info = f"Sport: {sport}, League: {match_info['league']}, Match: {match_info['match']}, Market: {market_type} {line}, Old Odds: {old_odds}, New Odds: {new_odds}"

                # Проверяем, нужно ли исключить строку на основе значения Market
                if any(substr in market_type for substr in ['1H']):
                    continue
                if any(substr in line for substr in ['.25']) or any(substr in line for substr in ['.75']):
                    continue

                # Проверяем, была ли такая строка уже записана
                if drop_info not in self.recorded_drops:
                    self.recorded_drops.add(drop_info)
                    file.write(f"{drop_info}, Time: {formatted_time}\n")


    def get_match_info(self, market_id):
            # Возвращаем информацию о матче, используя market_id как ключ
            return self.match_data.get(market_id, {'match': 'Unknown', 'league': 'Unknown'})

        
    def remove_stale_data(self):
        to_remove = [key for key, history in self.odds_data.items() if history.is_stale()]
        for key in to_remove:
            del self.odds_data[key]
