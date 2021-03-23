"""
Betclic odds scraper
"""

import datetime
import json
import re
import urllib

import dateutil.parser

from sportsbetting.auxiliary_functions import merge_dicts, truncate_datetime


def parse_betclic_api(id_league):
    """
    Get odds from Betclic API
    """
    url = ("https://offer.cdn.betclic.fr/api/pub/v2/competitions/{}?application=2&countrycode=fr"
           "&fetchMultipleDefaultMarkets=true&language=fr&sitecode=frfr".format(id_league))
    content = urllib.request.urlopen(url).read()
    parsed = json.loads(content)
    odds_match = {}
    if (not parsed) or "unifiedEvents" not in parsed:
        return odds_match
    matches = parsed["unifiedEvents"]
    for match in matches:
        if match["isLive"]:
            continue
        if "contestants" not in match:
            continue
        contestants = match["contestants"]
        if not contestants:
            continue
        name = " - ".join(contestant["name"] for contestant in contestants)
        date = dateutil.parser.isoparse(match["date"])+datetime.timedelta(hours=1)
        markets = match["markets"]
        if not markets:
            continue
        odds = [selection["odds"] for selection in markets[0]["selections"]]
        odds_match[name] = {}
        odds_match[name]["date"] = truncate_datetime(date)
        odds_match[name]["odds"] = {"betclic":odds}
        odds_match[name]["id"] = {"betclic":match["id"]}
    return odds_match


def parse_betclic(url):
    """
    Get odds from Betclic url
    """
    if "-s" in url and url.split("-s")[-1].isdigit():
        return parse_sport_betclic(url.split("-s")[-1])
    id_league = re.findall(r'\d+', url)[-1]
    return parse_betclic_api(id_league)


def parse_sport_betclic(id_sport):
    """
    Get odds from Betclic sport id
    """
    url = ("https://offer.cdn.betclic.fr/api/pub/v2/sports/{}?application=2&countrycode=fr&language=fr&sitecode=frfr"
           .format(id_sport))
    content = urllib.request.urlopen(url).read()
    parsed = json.loads(content)
    list_odds = []
    competitions = parsed["competitions"]
    for competition in competitions:
        id_competition = competition["id"]
        list_odds.append(parse_betclic_api(id_competition))
    return merge_dicts(list_odds)
