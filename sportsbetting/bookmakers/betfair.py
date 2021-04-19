import datetime
import json
import os
import requests
import time

import dateutil.parser
import seleniumwire


import sportsbetting as sb
from sportsbetting.auxiliary_functions import merge_dicts, truncate_datetime


def get_betfair_token():
    """
    Get Betfair token to access the API
    """
    token = ""
    if os.path.exists(sb.PATH_TOKENS):
        with open(sb.PATH_TOKENS, "r") as file:
            lines = file.readlines()
            for line in lines:
                bookmaker, token = line.split()
                if bookmaker == "betfair":
                    return token
    print("Récupération du token de connexion de Betfair")
    options = seleniumwire.webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images': 2,
             'disk-cache-size': 4096}
    options.add_argument('log-level=3')
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--headless")
    options.add_argument("--disable-extensions")
    driver = seleniumwire.webdriver.Chrome(sb.PATH_DRIVER, options=options)
    driver.get("https://www.betfair.com/exchange/plus/en/football-betting-1")
    time.sleep(10)
    for request in driver.requests:
        if "https://www.betfair.com/www/sports/navigation/facet/v1/search?_ak=" in str(request):
            token = str(request).split("_ak=")[1].split("&")[0]
            with open(sb.PATH_TOKENS, "a+") as file:
                file.write("betfair {}\n".format(token))
            break
    driver.quit()
    return token
    
def get_event_ids(id_league):
    token = get_betfair_token()
    url = "https://www.betfair.com/www/sports/navigation/v2/graph/bynode?_ak={}&alt=json&currencyCode=EUR&locale=en_GB&maxInDistance=10&maxOutDistance=3&maxResults=1&nodeIds=COMP:{}&outs=MENU".format(token, id_league)
    content = requests.get(url).content
    if "Error reference number" in str(content):
        raise sb.UnavailableSiteException
    parsed = json.loads(content)
    nodes = parsed.get("nodes", {})
    event_ids = []
    for node in nodes:
        if any([x in node.get("name", "") for x in [" v ", " @ "]]):
            event_ids.append(str(node["nodeId"].strip("MENU:")))
    return event_ids

def get_back_lay_markets(event_ids):
    back_lay_markets = []
    token = get_betfair_token()
    url = "https://ero.betfair.com/www/sports/exchange/readonly/v1/byevent?_ak={}&alt=json&currencyCode=EUR&locale=fr_FR&eventIds={}&rollupLimit=10&rollupModel=STAKE&types=MARKET_DESCRIPTION,EVENT,RUNNER_DESCRIPTION".format(token, ",".join(event_ids[:5]))
    content = requests.get(url).content
    parsed = json.loads(content)
    event_type = parsed.get("eventTypes", {})
    if not event_type:
        return []
    event_nodes = event_type[0].get("eventNodes", {})
    for event in event_nodes:
        event_back_lay = {"back":None, "lay":None}
        for market_node in event.get("marketNodes", {}):
            if market_node["description"]["marketType"] == "MATCH_ODDS":
                event_back_lay["back"] = market_node["marketId"]
            elif market_node["description"]["marketType"] == "DOUBLE_CHANCE":
                event_back_lay["lay"] = market_node["marketId"]
        back_lay_markets.append(event_back_lay)
    return back_lay_markets

def get_odds_from_back_lay_market_ids(back_lay_markets):
    market_ids = [item for sublist in [list(x.values()) for x in back_lay_markets] for item in sublist if item]
    token = get_betfair_token()
    odds_match = {}
    url = "https://ero.betfair.com/www/sports/exchange/readonly/v1/bymarket?_ak={}&alt=json&currencyCode=EUR&locale=fr_FR&marketIds={}&rollupLimit=10&rollupModel=STAKE&types=MARKET_DESCRIPTION,EVENT,RUNNER_DESCRIPTION,RUNNER_EXCHANGE_PRICES_BEST".format(token, ",".join(market_ids))
    content = requests.get(url).content
    parsed = json.loads(content)
    event_type = parsed.get("eventTypes", {})
    if not event_type:
        return {}
    event_nodes = event_type[0].get("eventNodes", {})
    for event in event_nodes:
        reversed_odds = False
        event_back_lay = {}
        name = event["event"]["eventName"].replace(" v ", " - ")
        if " @ " in name:
            name = " - ".join(reversed(event["event"]["eventName"].split(" @ ")))
            reversed_odds = True
        date = truncate_datetime(dateutil.parser.isoparse(event["event"]["openDate"])+datetime.timedelta(hours=2))
        event_id = str(event["eventId"])
        odds = [[], []]
        for i, market_node in enumerate(event.get("marketNodes", {})):
            runners = market_node.get("runners", {})
            back_eq_lay = len(runners) == 2
            for runner in runners:
                exchange = runner.get("exchange", {})
                lay = i%2
                if back_eq_lay or not lay:
                    odd_back = float(exchange.get("availableToBack", [{"price":1.01}])[0]["price"])
                    odd = round(1 + (1 – 0.03) * (odd_back – 1), 3)
                    if runner["description"]["runnerName"] in ["Match Nul"]:
                        odds[0].insert(1, odd)
                    else:
                        odds[0].append(odd)
                if back_eq_lay or lay:
                    odd_lay = float(exchange.get("availableToLay", [{"price":100}])[0]["price"])
                    odd = round(1+(1-0.03)/(odd_lay-1), 3)
                    if runner["description"]["runnerName"] in ["Home or Away"]:
                        odds[1].insert(1, odd)
                    else:
                        odds[1].append(odd)
            odds[1].reverse()
        best_odds = odds[0]
        if odds[1] and len(odds[0]) == len(odds[1]):
            best_odds = [max(odd_lay, odd_back) for odd_lay, odd_back in zip(*odds)]
        if reversed_odds:
            best_odds.reverse()
        odds_match[name] = {"odds":{"betfair":best_odds},
                            "date":date,
                            "id":{"betfair":event_id}}
    return odds_match
        
def parse_betfair(id_league):
    event_ids = get_event_ids(id_league)
    split_events = [event_ids[x:x+5] for x in range(0, len(event_ids), 5)]
    odds = []
    for event_group in split_events:
        odds.append(get_odds_from_back_lay_market_ids(get_back_lay_markets(event_group)))
    return merge_dicts(odds)
        