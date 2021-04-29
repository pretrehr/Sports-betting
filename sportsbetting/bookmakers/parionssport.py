"""
ParionsSport odds scraper
"""

import datetime
import json
import os
import re
import urllib

import OpenSSL
import seleniumwire

from collections import defaultdict

import sportsbetting as sb
from sportsbetting.auxiliary_functions import merge_dicts
from sportsbetting.database_functions import is_player_in_db, add_close_player_to_db, is_player_added_in_db

def get_parionssport_token():
    """
    Get ParionsSport token to access the API
    """
    token = ""
    if os.path.exists(sb.PATH_TOKENS):
        with open(sb.PATH_TOKENS, "r") as file:
            lines = file.readlines()
            for line in lines:
                bookmaker, token = line.split()
                if bookmaker == "parionssport":
                    return token
    print("Récupération du token de connexion de Parions Sport")
    options = seleniumwire.webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images': 2,
             'disk-cache-size': 4096}
    options.add_argument('log-level=3')
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--headless")
    options.add_argument("--disable-extensions")
    driver = seleniumwire.webdriver.Chrome(sb.PATH_DRIVER, options=options)
    driver.get("https://enligne.parionssport.fdj.fr")
    for request in driver.requests:
        if request.response:
            token = request.headers.get("X-LVS-HSToken")
            if token:
                with open(sb.PATH_TOKENS, "a+") as file:
                    file.write("parionssport {}\n".format(token))
                break
    driver.quit()
    return token



def parse_parionssport_match_basketball(id_match):
    """
    Get ParionsSport odds from baskteball match id
    """
    url = ("https://www.enligne.parionssport.fdj.fr/lvs-api/ff/{}?originId=3&lineId=1&showMarketTypeGroups=true&ext=1"
           "&showPromotions=true".format(id_match))
    req = urllib.request.Request(url, headers={'X-LVS-HSToken': sb.TOKENS["parionssport"]})
    content = urllib.request.urlopen(req).read()
    parsed = json.loads(content)
    items = parsed["items"]
    odds = []
    odds_match = {}
    for item in items:
        if not item.startswith("o"):
            continue
        odd = items[item]
        market = items[odd["parent"]]
        if not "desc" in market:
            continue
        if not market["desc"] == "Face à Face":
            continue
        if not "period" in market:
            continue
        if not market["period"] == "Match":
            continue
        event = items[market["parent"]]
        if "date" not in odds_match:
            odds_match["date"] = datetime.datetime.strptime(event["start"], "%y%m%d%H%M") + datetime.timedelta(hours=2)
        odds.append(float(odd["price"].replace(",", ".")))
    if not odds:
        return odds_match
    odds_match["odds"] = {"parionssport" : odds}
    odds_match["id"] = {"parionssport" : market["parent"]}
    return odds_match



def parse_parionssport_api(id_league):
    """
    Get ParionsSport odds from league id
    """
    url = ("https://www.enligne.parionssport.fdj.fr/lvs-api/next/50/{}?originId=3&lineId=1&breakdownEventsIntoDays=true"
           "&eType=G&showPromotions=true".format(id_league))
    req = urllib.request.Request(url, headers={'X-LVS-HSToken': sb.TOKENS["parionssport"]})
    content = urllib.request.urlopen(req).read()
    parsed = json.loads(content)
    odds_match = {}
    if "items" not in parsed:
        return odds_match
    items = parsed["items"]
    for item in items:
        if not item.startswith("o"):
            continue
        odd = items[item]
        market = items[odd["parent"]]
        if not market["style"] in ["WIN_DRAW_WIN", "TWO_OUTCOME_LONG"]:
            continue
        event = items[market["parent"]]
        name = event["a"] + " - " + event["b"]
        competition = event["path"]["Category"] + " - " + event["path"]["League"]
        if event["code"] == "BASK":
            if name not in odds_match:
                odds = parse_parionssport_match_basketball(market["parent"])
                if odds:
                    odds_match[name] = odds
        else:
            if not name in odds_match:
                odds_match[name] = {}
                odds_match[name]["date"] = (datetime.datetime.strptime(event["start"], "%y%m%d%H%M")
                                            + datetime.timedelta(hours=2))
                odds_match[name]["odds"] = {"parionssport":[]}
            odds_match[name]["odds"]["parionssport"].append(float(odd["price"].replace(",", ".")))
            odds_match[name]["id"] = {"parionssport":market["parent"]}
            odds_match[name]["competition"] = competition
    return odds_match

def parse_sport_parionssport(sport):
    """
    Get ParionsSport odds from sport
    """
    sports_alias = {
        "football"          : "FOOT",
        "basketball"        : "BASK",
        "tennis"            : "TENN",
        "handball"          : "HAND",
        "rugby"             : "RUGU",
        "hockey-sur-glace"  : "ICEH"
    }
    url = "https://www.enligne.parionssport.fdj.fr/lvs-api/leagues?sport={}".format(sports_alias[sport])
    req = urllib.request.Request(url, headers={'X-LVS-HSToken': sb.TOKENS["parionssport"]})
    content = urllib.request.urlopen(req).read()
    competitions = json.loads(content)
    list_odds = []
    for competition in competitions:
        for id_competition in competition["items"]:
            if "Cotes Boostées" in competition["name"]:
                continue
            list_odds.append(parse_parionssport_api(id_competition))
    return merge_dicts(list_odds)


def parse_parionssport(url):
    """
    Get ParionsSport odds from url
    """
    if "parionssport" not in sb.TOKENS:
        try:
            token = get_parionssport_token()
            sb.TOKENS["parionssport"] = token
        except OpenSSL.crypto.Error:
            return {}
    if "paris-" in url.split("/")[-1] and "?" not in url:
        sport = url.split("/")[-1].split("paris-")[-1]
        return parse_sport_parionssport(sport)
    regex = re.findall(r'\d+', url)
    if regex:
        id_league = regex[-1]
        try:
            return parse_parionssport_api("p" + str(id_league))
        except TypeError:
            return {}
    return {}


def get_sub_markets_players_basketball_parionssport(id_match):
    if not id_match:
        return {}
    url = ("https://www.enligne.parionssport.fdj.fr/lvs-api/ff/{}?originId=3&lineId=1&showMarketTypeGroups=true&ext=1"
           "&showPromotions=true".format(id_match))
    req = urllib.request.Request(url, headers={'X-LVS-HSToken': sb.TOKENS["parionssport"]})
    content = urllib.request.urlopen(req).read()
    parsed = json.loads(content)
    items = parsed["items"]
    odds = []
    odds_match = {}
    markets_to_keep = { 'Performance du Joueur - Total Passes décisives':'Passes', 
                        'Performance du Joueur - Total Rebonds':'Rebonds', 
                        'Performance du Joueur - Total Points + Passes':'Points + passes', 
                        'Performance du Joueur - Total Points + Rebonds':'Points + rebonds',
                        'Performance du Joueur - Total Rebonds + Passes':'Passes + rebonds',
                        'Performance du joueur - Total Points (Supérieur à la valeur affichée)':'Points'}
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    for item in items:
        if not item.startswith("o"):
            continue
        odd = items[item]
        market = items[odd["parent"]]
        if not "desc" in market:
            continue
        if not market["desc"] in markets_to_keep:
            continue
        if not odd.get("price"):
            continue
        if "flags" in odd and "hidden" in odd["flags"]:
            continue
        event = items[market["parent"]]
        limit = odd["desc"].split()[-1].replace(",", ".")
        player = odd["desc"].split(" - ")[0].split("(")[0].strip()
        if player == odd["desc"]:
            player = odd["desc"].split("- ")[0].strip()
        ref_player = add_close_player_to_db(player, "parionssport")
        if is_player_added_in_db(player, "parionssport"):
            ref_player = is_player_added_in_db(player, "parionssport")
        elif not ref_player:
            if sb.DB_MANAGEMENT:
                print(player, "parionssport")
            continue
        key_player = (ref_player + "_" + limit).split(".5")[0] + ".5"
        key_market = markets_to_keep[market["desc"]]
        if key_player not in sub_markets[key_market]:
            sub_markets[key_market][key_player] = {"odds":{"parionssport":[]}}
        sub_markets[key_market][key_player]["odds"]["parionssport"].append(float(odd["price"].replace(",", ".")))
        if key_market == "Points":
            sub_markets[key_market][key_player]["odds"]["parionssport"].append(1.01)
    for sub_market in sub_markets:
        sub_markets[sub_market] = dict(sub_markets[sub_market])
    return sub_markets
