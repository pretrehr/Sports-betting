"""
ParionsSport odds scraper
"""

import datetime
import json
import re
import urllib

import seleniumwire

import sportsbetting as sb
from sportsbetting.auxiliary_functions import merge_dicts


def get_parionssport_token():
    """
    Get ParionsSport token to access the API
    """
    token = ""
    with open(sb.PATH_TOKENS, "r") as file:
        lines = file.readlines()
        for line in lines:
            bookmaker, token = line.split()
            if bookmaker == "parionssport":
                return token
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
                with open(sb.PATH_TOKENS, "a") as file:
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
            odds_match["date"] = datetime.datetime.strptime(event["start"], "%y%m%d%H%M") + datetime.timedelta(hours=1)
        odds.append(float(odd["price"].replace(",", ".")))
    if not odds:
        return odds_match
    odds_match["odds"] = {"parionssport" : odds}
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
        if event["code"] == "BASK":
            if name not in odds_match:
                odds = parse_parionssport_match_basketball(market["parent"])
                if odds:
                    odds_match[name] = odds
        else:
            if not name in odds_match:
                odds_match[name] = {}
                odds_match[name]["date"] = (datetime.datetime.strptime(event["start"], "%y%m%d%H%M")
                                            + datetime.timedelta(hours=1))
                odds_match[name]["odds"] = {"parionssport":[]}
            odds_match[name]["odds"]["parionssport"].append(float(odd["price"].replace(",", ".")))
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
            list_odds.append(parse_parionssport_api(id_competition))
    return merge_dicts(list_odds)


def parse_parionssport(url):
    """
    Get ParionsSport odds from url
    """
    if "parionssport" not in sb.TOKENS:
        token = get_parionssport_token()
        sb.TOKENS["parionssport"] = token
    if "paris-" in url.split("/")[-1] and "?" not in url:
        sport = url.split("/")[-1].split("paris-")[-1]
        return parse_sport_parionssport(sport)
    regex = re.findall(r'\d+', url)
    if regex:
        id_league = regex[-1]
        return parse_parionssport_api("p" + str(id_league))
    return {}
