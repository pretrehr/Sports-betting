"""
Betclic odds scraper
"""

import datetime
import json
import re
import urllib

import dateutil.parser

from collections import defaultdict

import sportsbetting as sb
from sportsbetting.auxiliary_functions import merge_dicts, truncate_datetime
from sportsbetting.database_functions import is_player_in_db, add_player_to_db, is_player_added_in_db, add_close_player_to_db

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
    competition = parsed["name"]
    for match in matches:
        if match["isLive"]:
            continue
        if "contestants" not in match:
            continue
        contestants = match["contestants"]
        if not contestants:
            continue
        name = " - ".join(contestant["name"] for contestant in contestants)
        date = dateutil.parser.isoparse(match["date"])+datetime.timedelta(hours=2)
        markets = match["markets"]
        if not markets:
            continue
        if markets[0]["name"].strip() not in ["Vainqueur du match", "Résultat du match", "Vainqueur Match", "Résultat"]:
            continue
        odds = [selection["odds"] for selection in markets[0]["selections"]]
        odds_match[name] = {}
        odds_match[name]["date"] = truncate_datetime(date)
        odds_match[name]["odds"] = {"betclic":odds}
        odds_match[name]["id"] = {"betclic":match["id"]}
        odds_match[name]["competition"] = competition
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


def get_sub_markets_players_basketball_betclic(id_match):
    if not id_match:
        return {}
    url = 'https://offer.cdn.betclic.fr/api/pub/v4/events/{}?application=2&countrycode=fr&language=fr&sitecode=frfr'.format(str(id_match))
    content = urllib.request.urlopen(url).read()
    parsed = json.loads(content)
    if not parsed:
        return {}
    markets = parsed['markets']
    markets_to_keep = {'Bkb_Ppf2':'Points + passes + rebonds',  'Bkb_Pta2':'Passes', 
    'Bkb_Ptr2':'Rebonds', 
    'Bkb_PnA':'Points + passes', 
    'Bkb_PnR':'Points + rebonds', 
    'Bkb_AeR':'Passes + rebonds',
    'Bkb_20p':'Points', 'Bkb_25p':'Points', 'Bkb_30p':'Points', 'Bkb_35p':'Points', 'Bkb_40p':'Points'}
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    for market in markets:
        if market['mtc'] not in markets_to_keep:
            continue
        is_points_market = market['mtc'][-1] == 'p'
        selections = market['selections']
        odds_market = {}
        for selection in selections:
            limit = ""
            if is_points_market:
                limit = str(int(market['mtc'].strip("Bkb_").strip('p'))-0.5)
            else:
                limit = selection['name'].split(' de ')[(-1)].replace(",", ".")
            player = re.split('\\s\\+\\s|\\s\\-\\s', selection['name'].replace(".", " "))[0].strip()
            ref_player = player
            if is_player_added_in_db(player, "betclic"):
                ref_player = is_player_added_in_db(player, "betclic")
            elif is_player_in_db(player):
                add_player_to_db(player, "betclic")
            elif add_close_player_to_db(player, "betclic"):
                ref_player = is_player_added_in_db(player, "betclic")
            else:
                if sb.DB_MANAGEMENT:
                    print(player, "betclic")
                continue
            key_player = ref_player + "_" + limit
            if key_player not in odds_market:
                odds_market[key_player] = {"odds":{"betclic":[]}}
            odds_market[ref_player + "_" + limit]["odds"]["betclic"].append(selection['odds'])
            if is_points_market:
                odds_market[ref_player + "_" + limit]["odds"]["betclic"].append(1.01)
            
    
        sub_markets[markets_to_keep[market['mtc']]] = {**dict(odds_market), **sub_markets[markets_to_keep[market['mtc']]]}
    
    return sub_markets