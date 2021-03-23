"""
Unibet odds scraper
"""

import datetime
import json
import urllib

def get_id_league(url):
    """
    Get league id from url
    """
    if "https://www.unibet.fr" not in url:
        return None, None
    public_url = url.split("https://www.unibet.fr")[1]
    request_url = "https://www.unibet.fr/zones/navigation.json?publicUrl="+public_url
    content = urllib.request.urlopen(request_url).read()
    parsed = json.loads(content)
    sport = public_url.split("/")[2]
    if parsed["requestData"]:
        return parsed["requestData"].get("nodeId"), sport
    return None, None


def parse_unibet_api(id_league, sport):
    """
    Get Unibet odds from league id and sport
    """
    parameter = ""
    if sport == "tennis":
        parameter = "Vainqueur%2520du%2520match"
    elif sport == "basketball":
        parameter = "Vainqueur%2520du%2520match%2520%2528prolong.%2520incluses%2529"
    else:
        parameter = "R%25C3%25A9sultat%2520du%2520match"
    url = ("https://www.unibet.fr/zones/sportnode/markets.json?nodeId={}&filter=R%25C3%25A9sultat&marketname={}"
           .format(id_league, parameter))
    content = urllib.request.urlopen(url).read()
    parsed = json.loads(content)
    markets_by_type = parsed.get("marketsByType", [])
    odds_match = {}
    for market_by_type in markets_by_type:
        days = market_by_type["days"]
        for day in days:
            events = day["events"]
            for event in events:
                markets = event["markets"]
                for market in markets:
                    name = (market["eventHomeTeamName"].replace(" - ", "-")
                            + " - " + market["eventAwayTeamName"].replace(" - ", "-"))
                    date = datetime.datetime.fromtimestamp(market["eventStartDate"]/1000)
                    odds = []
                    selections = market["selections"]
                    for selection in selections:
                        price_up = int(selection["currentPriceUp"])
                        price_down = int(selection["currentPriceDown"])
                        odds.append(round(price_up / price_down + 1, 2))
                    odds_match[name] = {"date":date, "odds":{"unibet":odds}, "id":{"unibet":event["eventId"]}}
    return odds_match

def parse_unibet(url):
    """
    Get Unibet odds from url
    """
    id_league, sport = get_id_league(url)
    if id_league:
        return parse_unibet_api(id_league, sport)
    print("Wrong unibet url")
    return {}
