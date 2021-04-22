"""
Pinnacle odds scraper
"""

import datetime
import json
import os
import urllib
import time

import dateutil.parser
import seleniumwire

from collections import defaultdict


import sportsbetting as sb
from sportsbetting.auxiliary_functions import merge_dicts, truncate_datetime
from sportsbetting.database_functions import is_player_in_db, add_player_to_db, is_player_added_in_db


def convert_american_odds(american_odds):
    decimal_odds = []
    for odd in american_odds:
        if odd>=0:
            decimal_odds.append(round(odd/100+1, 3))
        else:
            decimal_odds.append(round(-100/odd+1, 3))
    return decimal_odds

def get_pinnacle_odds_from_match_id(id_match, all_odds):
    for odds in all_odds:
        if not (odds["matchupId"] == int(id_match) and odds["type"] == "moneyline" and odds["period"] == 0):
            continue
        if not odds["prices"] or "designation" not in odds["prices"][0]:
            continue
        odds_match = list(x["price"] for x in sorted(odds["prices"], key=lambda x: x["designation"], reverse=True))
        return convert_american_odds(odds_match)


def get_pinnacle_odds_from_market_id(id_market, all_odds):
    for odds in all_odds:
        if not (odds["matchupId"] == int(id_market) and odds["type"] == "total" and odds["period"] == 0):
            continue
        if not odds["prices"] or "price" not in odds["prices"][0] or "points" not in odds["prices"][0] or "participantId" not in odds["prices"][0]:
            continue
        odds_market = list(x["price"] for x in sorted(odds["prices"], key=lambda x: x["participantId"]))
        return convert_american_odds(odds_market), odds["prices"][0]["points"]
    return [], 0
                

def get_pinnacle_token():
    """
    Get Pinnacle token to access the API
    """
    token = ""
    if os.path.exists(sb.PATH_TOKENS):
        with open(sb.PATH_TOKENS, "r") as file:
            lines = file.readlines()
            for line in lines:
                bookmaker, token = line.split()
                if bookmaker == "pinnacle":
                    return token
    print("Récupération du token de connexion de Pinnacle")
    options = seleniumwire.webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images': 2,
             'disk-cache-size': 4096}
    options.add_argument('log-level=3')
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--headless")
    options.add_argument("--disable-extensions")
    driver = seleniumwire.webdriver.Chrome(sb.PATH_DRIVER, options=options)
    driver.get("https://www.pinnacle.com/")
    time.sleep(30)
    for request in driver.requests:
        if request.response:
            token = request.headers.get("X-API-KEY")
            if token:
                with open(sb.PATH_TOKENS, "a+") as file:
                    file.write("pinnacle {}\n".format(token))
                break
    driver.quit()
    return token

def parse_pinnacle(id_league):
    """
    Get odds from Pinnacle API
    """
    if not id_league.isnumeric():
        return parse_sport_pinnacle(id_league)
    token = get_pinnacle_token()
    url_straight = "https://guest.api.arcadia.pinnacle.com/0.1/leagues/{}/markets/straight".format(id_league)
    url_matchup = "https://guest.api.arcadia.pinnacle.com/0.1/leagues/{}/matchups".format(id_league)
    req_straight = urllib.request.Request(url_straight, headers={'x-api-key': token})
    req_matchup = urllib.request.Request(url_matchup, headers={'x-api-key': token})
    content_straight = urllib.request.urlopen(req_straight).read()
    content_matchup = urllib.request.urlopen(req_matchup).read()
    all_odds = json.loads(content_straight)
    matches = json.loads(content_matchup)
    odds_match = {}
    set_matches = set()
    sports = {"Soccer" : "football",
              "Tennis" : "tennis",
              "Basketball" : "basketball",
              "Rugby Union" : "rugby",
              "Hockey" : "hockey-sur-glace",
              "Handball" : "handball"}
    for match in matches:
        if match["isLive"]:
            continue
        if "participants" not in match:
            continue
        if "id" not in match:
            continue
        sport = sports[match["league"]["sport"]["name"]]
        id_match = match["id"]
        match_name = " - ".join(sb.TRANSLATION[sport].get(match["participants"][x]["name"], match["participants"][x]["name"]) for x in [0,1])
        if "5 Sets" in match_name:
            continue
        date_time = truncate_datetime(dateutil.parser.isoparse(match["startTime"])+datetime.timedelta(hours=2))
        odds = get_pinnacle_odds_from_match_id(id_match, all_odds)
        if odds:
            odds_match[match_name] = {"odds":{"pinnacle":odds}, "date":date_time, "id":{"pinnacle" :str(id_match)}}
    return odds_match


def parse_sport_pinnacle(sport):
    id_sports = {"football" : 29,
                 "tennis" : 33,
                 "basketball" : 4,
                 "rugby" : 27,
                 "hockey-sur-glace" :19,
                 "handball" : 18}
    url = "https://guest.api.arcadia.pinnacle.com/0.1/sports/{}/leagues?all=false".format(id_sports[sport])
    token = get_pinnacle_token()
    req = urllib.request.Request(url, headers={'x-api-key': token})
    content = urllib.request.urlopen(req).read()
    leagues = json.loads(content)
    list_odds = []
    for league in leagues:
        if any([x in league["name"] for x in ["ITF", "Challenger"]]):
            continue
        id_league = str(league["id"])
        list_odds.append(parse_pinnacle(id_league))
    return merge_dicts(list_odds)


def get_sub_markets_players_basketball_pinnacle(id_match):
    if not id_match:
        return {}
    token = get_pinnacle_token()
    url_straight = "https://guest.api.arcadia.pinnacle.com/0.1/matchups/{}/markets/related/straight".format(id_match)
    url_related = "https://guest.api.arcadia.pinnacle.com/0.1/matchups/{}/related".format(id_match)
    req_straight = urllib.request.Request(url_straight, headers={'x-api-key': token})
    req_related = urllib.request.Request(url_related, headers={'x-api-key': token})
    content_straight = urllib.request.urlopen(req_straight).read()
    content_related = urllib.request.urlopen(req_related).read()
    all_odds = json.loads(content_straight)
    markets = json.loads(content_related)
    markets_to_keep = {'PointsReboundsAssist':'Points + passes + rebonds',
                       'Assists':'Passes', 
                       'Rebounds':'Rebonds',
                       'Points':'Points'}
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    for market in markets:
        if market.get("type") != "special":
            continue
        market_type = markets_to_keep.get(market["units"])
        if not market_type:
            continue
        id_market = market["id"]
        player = market["special"]["description"].split("(")[0].strip()
        if "Total Points by" in player:
            player = player.split("Total Points by")[1].strip()
        ref_player = player
        if is_player_added_in_db(player, "pinnacle"):
            ref_player = is_player_added_in_db(player, "pinnacle")
        elif is_player_in_db(player):
            add_player_to_db(player, "pinnacle")
        else:
            if sb.DB_MANAGEMENT:
                print(player, "pinnacle")
#                 add_new_player_to_db(player)
            continue
        odds, limit = get_pinnacle_odds_from_market_id(id_market, all_odds)
        if odds:
            key_player = ref_player + "_" + str(limit)
            sub_markets[market_type][key_player] = {"odds":{"pinnacle":odds}}

    for sub_market in sub_markets:
        sub_markets[sub_market] = dict(sub_markets[sub_market])
    return sub_markets
