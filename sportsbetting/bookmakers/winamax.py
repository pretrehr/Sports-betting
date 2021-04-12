"""
Winamax odds scraper
"""

import datetime
import json
import urllib
import urllib.error
import urllib.request

from bs4 import BeautifulSoup
from collections import defaultdict

import sportsbetting as sb
from sportsbetting.database_functions import is_player_in_db, add_player_to_db, is_player_added_in_db

def parse_winamax(url):
    """
    Retourne les cotes disponibles sur winamax
    """
    ids = url.split("/sports/")[1]
    try:
        tournament_id = int(ids.split("/")[2])
    except IndexError:
        tournament_id = -1
    sport_id = int(ids.split("/")[0])
    try:
        req = urllib.request.Request(
            url, headers={'User-Agent': sb.USER_AGENT})
        webpage = urllib.request.urlopen(req, timeout=10).read()
        soup = BeautifulSoup(webpage, features="lxml")
    except urllib.error.HTTPError:
        raise sb.UnavailableSiteException
    match_odds_hash = {}
    for line in soup.find_all(['script']):
        if "PRELOADED_STATE" in str(line.string):
            json_text = (line.string.split("var PRELOADED_STATE = ")[1]
                         .split(";var BETTING_CONFIGURATION")[0])
            if json_text[-1] == ";":
                json_text = json_text[:-1]
            dict_matches = json.loads(json_text)
            if "matches" in dict_matches:
                for match in dict_matches["matches"].values():
                    if (tournament_id in (match['tournamentId'], -1) and match["competitor1Id"] != 0
                            and match['sportId'] == sport_id and 'isOutright' not in match.keys()):
                        try:
                            match_name = match["title"].strip().replace("  ", " ")
                            date_time = datetime.datetime.fromtimestamp(match["matchStart"])
                            if date_time < datetime.datetime.today():
                                continue
                            main_bet_id = match["mainBetId"]
                            odds_ids = dict_matches["bets"][str(
                                main_bet_id)]["outcomes"]
                            odds = [dict_matches["odds"]
                                    [str(x)] for x in odds_ids]
                            match_odds_hash[match_name] = {}
                            match_odds_hash[match_name]['odds'] = {
                                "winamax": odds}
                            match_odds_hash[match_name]['date'] = date_time
                            match_odds_hash[match_name]['id'] = {
                                "winamax": str(match["matchId"])}
                        except KeyError:
                            pass
            if not match_odds_hash:
                raise sb.UnavailableCompetitionException
            return match_odds_hash
    raise sb.UnavailableSiteException

def get_sub_markets_players_basketball_winamax(id_match):
    if not id_match:
        return {}
    url = 'https://www.winamax.fr/paris-sportifs/match/' + id_match
    try:
        req = urllib.request.Request(url,
        headers={'User-Agent': sb.USER_AGENT})
        webpage = urllib.request.urlopen(req, timeout=10).read()
        soup = BeautifulSoup(webpage, features='lxml')
    except urllib.error.HTTPError:
        raise sb.UnavailableSiteException
    
    markets_to_keep = {'9017':'Points + passes + rebonds', 
    '9016':'Passes', 
    '9015':'Rebonds', 
    '9007':'Points + passes + rebonds', 
    '9006':'Passes', 
    '9005':'Rebonds'}
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    for line in soup.find_all(['script']):
        if 'PRELOADED_STATE' not in str(line.string):
            continue
        json_text = line.string.split('var PRELOADED_STATE = ')[1].split(';var BETTING_CONFIGURATION')[0]
        if json_text[(-1)] == ';':
            json_text = json_text[:-1]
        dict_matches = json.loads(json_text)
        for bet in dict_matches['bets'].values():
            if str(bet['marketId']) not in markets_to_keep:
                continue
            id_outcomes = bet['outcomes']
            for id_outcome in id_outcomes:
                label = dict_matches['outcomes'][str(id_outcome)]['label']
                code = dict_matches['outcomes'][str(id_outcome)]['code']
                player = label.split(' - ')[0].split()[1]
                limit = code.split('_')[(-1)].replace(",", ".")
                odd = dict_matches['odds'][str(id_outcome)]
                player = label.split(' - ')[0].split('- Plus de ')[0].strip()
                ref_player = player
                if is_player_added_in_db(player, "winamax"):
                    ref_player = is_player_added_in_db(player, "winamax")
                elif is_player_in_db(player):
                    add_player_to_db(player, "winamax")
                else:
                    if sb.DB_MANAGEMENT:
                        print(player, "winamax")
                    continue
                sub_markets[markets_to_keep[str(bet['marketId'])]][ref_player + "_" + limit].append(odd)
    
    for sub_market in sub_markets:
        sub_markets[sub_market] = dict(sub_markets[sub_market])
    return dict(sub_markets)