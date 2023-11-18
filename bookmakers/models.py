from pydantic import BaseModel
from typing import Optional, List, Union


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
