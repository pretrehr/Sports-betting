import dateutil
import demjson
import re
import requests

from sportsbetting.auxiliary_functions import truncate_datetime

def parse_betway(url):
    if url.count("/") < 5:
        return parse_sport_betway(url)
    match_odds_hash = {}
    parsed  = str(requests.get(url).content)
    parsed  = parsed.split("prematch_event_list:")[-1]
    parsed  = parsed.split("params:{}},")[0] + "params:{}}"
    parsed = re.sub("[A-Za-z_$]{1,2}[0-9]?,", '1.01,', parsed)
    parsed = re.sub("[A-Za-z_$]{1,2}[0-9]?\]", '1.01]', parsed)
    parsed = re.sub("[A-Za-z_$]{1,2}[0-9]?\}", '1.01}', parsed)
    parsed = demjson.decode(parsed)
    data = parsed["data"]
    odds_match = {}
    for match in data:
        id_match = str(match["id"])
        odds = []
        teams = []
        date_time = truncate_datetime(dateutil.parser.isoparse(match["start"]))
        for choice in match["choices"]:
            odds.append(choice["odd"])
        name = match["label"].replace("\\u002F", "-")
        odds_match[name] = {"date":date_time, "odds":{"betway":odds}, "id": {"betway":id_match}}
    return odds_match


def parse_sport_betway(url):
    match_odds_hash = {}
    parsed  = str(requests.get(url).content)
    parsed  = parsed.split("top_bets:")[-1]
    parsed  = parsed.split("params:{}},")[0] + "params:{}}"
    parsed = re.sub("[A-Za-z_$]{1,2}[0-9]?,", '1.01,', parsed)
    parsed = re.sub("[A-Za-z_$]{1,2}[0-9]?\]", '1.01]', parsed)
    parsed = re.sub("[A-Za-z_$]{1,2}[0-9]?\}", '1.01}', parsed)
    parsed = demjson.decode(parsed)
    data = parsed["data"]
    odds_match = {}
    for group in data["eventsGroup"]:
        for match in group["events"]:
            id_match = str(match["id"])
            odds = []
            teams = []
            date_time = truncate_datetime(dateutil.parser.isoparse(match["start"]))
            for choice in match["choices"]:
                odds.append(choice["odd"])
            name = match["label"].replace("\\u002F", "-")
            odds_match[name] = {"date":date_time, "odds":{"betway":odds}, "id": {"betway":id_match}}
    return odds_match