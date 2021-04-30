"""
Unibet odds scraper
"""

import datetime
import json
import requests

from collections import defaultdict

import sportsbetting as sb
from sportsbetting.database_functions import is_player_in_db, add_player_to_db, is_player_added_in_db, add_new_player_to_db, is_in_db_site, get_formatted_name_by_id

def get_id_league(url):
    """
    Get league id from url
    """
    if "https://www.unibet.fr" not in url:
        return None, None
    public_url = url.split("https://www.unibet.fr")[1]
    request_url = "https://www.unibet.fr/zones/navigation.json?publicUrl="+public_url
    content = requests.get(request_url).content
    if "Nos services ne sont pas accessibles pour le moment et seront de retour au plus vite." in str(content):
        raise sb.UnavailableSiteException
    parsed = json.loads(content)
    sport = public_url.split("/")[2]
    if sport == "cotes-boostees":
        sport = public_url.split("/")[-1].split("-")[0]
    if parsed["requestData"]:
        return parsed["requestData"].get("nodeId"), sport
    return None, None


def parse_unibet_api(id_league, sport, boost):
    """
    Get Unibet odds from league id and sport
    """
    parameter = ""
    if sport == "tennis":
        parameter = "Vainqueur%2520du%2520match"
    elif "basket" in sport:
        parameter = "Vainqueur%2520du%2520match%2520%2528prolong.%2520incluses%2529"
    else:
        parameter = "R%25C3%25A9sultat%2520du%2520match"
    url = ("https://www.unibet.fr/zones/sportnode/markets.json?nodeId={}&filter=R%25C3%25A9sultat&marketname={}"
           .format(id_league, parameter))
    content = requests.get(url).content
    parsed = json.loads(content)
    markets_by_type = parsed.get("marketsByType", [])
    odds_match = {}
    site_name = "unibet" + ("_boost" if boost else "")
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
                    odds_match[name] = {"date":date, "odds":{site_name:odds}, "id":{"unibet":event["eventId"]}, "competition":event["competitionName"]}
    return odds_match

def parse_unibet(url, boost=False):
    """
    Get Unibet odds from url
    """
    id_league, sport = get_id_league(url)
    if id_league:
        return parse_unibet_api(id_league, sport, boost)
    print("Wrong unibet url")
    return {}


def get_sub_markets_players_basketball_unibet(id_match):
    if not id_match:
        return {}
    url = 'https://www.unibet.fr/zones/event.json?eventId=' + id_match
    content = requests.get(url).content
    parsed = json.loads(content)
    markets_class_list = parsed.get('marketClassList', [])
    markets_to_keep = {'Performance du Joueur (Points + Rebonds + Passes)':'Points + passes + rebonds',  'Nombre de passes du joueur':'Passes', 
    'Nombre de rebonds du joueur':'Rebonds', 
    'Performance du Joueur (Points + Passes)':'Points + passes', 
    'Performance du Joueur (Points + Rebonds)':'Points + rebonds',
    'Performance du Joueur (Passes + Rebonds)':'Passes + rebonds',
    "Joueur marquant 20 points ou plus":"Points",
    "Joueur marquant 25 points ou plus":"Points",
    "Joueur marquant 30 points ou plus":"Points",
    "Joueur marquant 35 points ou plus":"Points",
    "Joueur marquant 40 points ou plus":"Points",
    "Equipe à domicile - Nombre de 3 points marqués":"3 Points",
    "Equipe à l'exterieur - Nombre de 3 points marqués":"3 Points"}
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    for market_class_list in markets_class_list:
        market_name = market_class_list['marketName']
        if market_name not in markets_to_keep:
            continue
        markets = market_class_list['marketList']
        for market in markets:
            id_team = is_in_db_site(market.get("event{}Name".format(market["marketType"].split(" - ")[0].replace(" ", ""))), "basketball", "unibet")
            if id_team:
                ref_player = get_formatted_name_by_id(id_team[0])
            is_3_pts = "Nombre de 3 points marqués" in market["marketName"]
            selections = market['selections']
            for selection in selections:
                price_up = int(selection['currentPriceUp'])
                price_down = int(selection['currentPriceDown'])
                odd = round(price_up / price_down + 1, 2)
                limit = selection['name'].split(' de ')[(-1)].replace(",", ".")
                plus = "Plus de" in selection['name']
                if not is_3_pts:
                    player = selection['name'].split(' - ')[0]
                    ref_player = player
                    if is_player_added_in_db(player, "unibet"):
                        ref_player = is_player_added_in_db(player, "unibet")
                    elif is_player_in_db(player):
                        add_player_to_db(player, "unibet")
                    else:
                        if sb.DB_MANAGEMENT:
                            print(player, "unibet")
                            add_new_player_to_db(player)
                        else:
                            continue
                key_market = markets_to_keep[market_name]
                if key_market == "Points":
                    limit = str(float(market_name.split()[2])-0.5)
                key_player = ref_player + "_" + limit
                if key_player not in sub_markets[key_market]:
                    sub_markets[key_market][key_player] = {"odds":{"unibet":[]}}
                if plus:
                    sub_markets[key_market][key_player]["odds"]["unibet"].insert(0, odd)
                else:
                    sub_markets[key_market][key_player]["odds"]["unibet"].append(odd)
                if key_market == "3 Points":
                    sub_markets[key_market][key_player]["odds"]["unibet"].reverse()
                if key_market == "Points":
                    sub_markets[key_market][key_player]["odds"]["unibet"].append(1.01)
    
    for sub_market in sub_markets:
        sub_markets[sub_market] = dict(sub_markets[sub_market])
    
    return sub_markets