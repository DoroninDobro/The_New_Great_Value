# задача 1: сейчас берутся только матчи за сегодня, а надо бы за 24 часа (функция get_prematch)
# задача 2: добавить исчезнование матча, но при этом важно учесть начало матча, чтобы исключить исчезновение по этой причине. А еще наверное бывают просто закрытые кэфы
# задача 3: нужно добавить разницу времени, а не только время появления события

#TODO: different percents for different odds
#TODO: another sports check carefully (why no bets?)
#TODO: add odds after 10, 30 and 120 mins
#TODO: find matches and markets in 1win
#TODO: check odds for Value
#TODO: make bets with check odds in basket

import asyncio
from datetime import datetime
import logging
import time

from ps3838Com import Ps3838Com
from odds_tracker import OddsTracker
import nest_asyncio
nest_asyncio.apply()


async def main():
    MAIN_LOOP = 1
    limit_time = 12  # limit time in hours
    mk = 1
    date_ = datetime.today().strftime('%Y-%m-%d')
    ps = Ps3838Com()
    await ps.setup()  # Инициализируем сессию здесь
    tracker = OddsTracker(significance_percent=5, time_span_minutes=15)
    while True:
        try:
            matches = await ps.get_prematch()
            data = await ps.run(matches)
            tracker.update_data(data)
            tracker.check_for_significant_drops()
            tracker.remove_stale_data()

            sleep_time = 20
            await asyncio.sleep(sleep_time)
        except Exception as e:
            await asyncio.sleep(20)
            continue
#            logging.error(f"{e}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S'
    )

    logging.info("Start Pinnacle scraper...")
    asyncio.run(main())
