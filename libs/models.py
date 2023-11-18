from pydantic import BaseModel
from typing import Dict, Optional, List, Union


class Telegram(BaseModel):
    chat_id:  Optional[int] = -883959315
    enable: Optional[bool] = False
    token: str
    logs: int
    admin_id: List[int] = [38481876]


class Bookmaker(BaseModel):
    active: Optional[int] = 1
    bankroll: Optional[int] = 100
    chat_id: Optional[int] = 0
    currency: Optional[str] = ''
    currency_rate: Optional[int] = 1
    round: Optional[int] = 0


class Settings(BaseModel):
    bookmakers: Dict
    bankroll: int = 100
    profit: float = 1.05
    bank_multiplier: Optional[float] = 1.0
    filter_by_bookie: List[str]
    telegram: Optional[Telegram] = None
    actionfile: Optional[str] = '/home/koloss/odds_checker_bohdan/action.json'
    events_path: Optional[str] = '/home/koloss/value_bet/cache/'


class Match(BaseModel):
    match_id: Union[str, int]
    match: str
    bookmaker: str
    sport: str
    country: Optional[str]
    league: Optional[str]
    url: Optional[str] = 'https://'
    kickoff: Optional[Union[str, int]] = ''
    converted_markets: Optional[List] = []
