"""
ZeBet odds scraper
"""

import datetime
import re
import urllib
import urllib.error
import urllib.request

from bs4 import BeautifulSoup
from collections import defaultdict

import sportsbetting as sb
from sportsbetting.database_functions import is_player_in_db, add_player_to_db, is_player_added_in_db

def parse_zebet(url):
    """
    Retourne les cotes disponibles sur zebet
    """
    if "/sport/" in url:
        return parse_sport_zebet(url)
    try:
        soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    except urllib.error.URLError:
        raise sb.UnavailableCompetitionException
    match_odds_hash = {}
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = str(today.year) + "/"
    date_time = None
    for line in soup.find_all():
        if "Zebet rencontre actuellement des difficultés techniques." in line.text:
            raise sb.UnavailableSiteException
        if "class" in line.attrs and "bet-time" in line["class"]:
            try:
                date_time = datetime.datetime.strptime(year + " ".join(line.text.strip().split()),
                                                       "%Y/%d/%m %H:%M")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year + 1)
            except ValueError:
                date_time = "undefined"
        elif "class" in line.attrs and "competition" in line["class"]:
            strings = list(line.stripped_strings)
            match = (strings[1] + " - " + strings[-3])
            odds = []
            for i, val in enumerate(strings):
                if not i % 4:
                    odds.append(float(val.replace(",", ".")))
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"zebet": odds}
            match_odds_hash[match]['date'] = date_time
        elif "href" in line.attrs and "/fr/event/" in line["href"]:
            match_id = line["href"].split("-")[0].split("/")[-1]
            match_odds_hash[match]['id'] = {"zebet": match_id}
            
    return match_odds_hash


def parse_sport_zebet(url):
    """
    Retourne les cotes disponibles sur zebet pour un sport donné
    """
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = str(today.year) + "/"
    date_time = None
    for line in soup.find_all():
        if "Zebet rencontre actuellement des difficultés techniques." in line.text:
            raise sb.UnavailableSiteException
        if "class" in line.attrs and "bet-event" in line["class"]:
            match = format_zebet_names(line.text.strip())
        if "class" in line.attrs and "bet-time" in line["class"]:
            try:
                date_time = datetime.datetime.strptime(year + " ".join(line.text.strip().split()),
                                                       "%Y/%d/%m %H:%M")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year + 1)
            except ValueError:
                date_time = "undefined"
        if "class" in line.attrs and "pari-1" in line["class"]:
            odds = list(map(lambda x: float(x.replace(",", ".")),
                            list(line.stripped_strings)[1::2]))
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"zebet": odds}
            match_odds_hash[match]['date'] = date_time
    return match_odds_hash


def format_zebet_names(match):
    """
    Returns match from a string available on ZeBet html
    """
    strings = match.split(" / ")
    if len(strings) == 2:
        return " - ".join(strings)
    if len(strings) == 4:
        return " - ".join(map(" / ".join, [strings[0:2], strings[2:4]]))
    if len(strings) == 3:
        reg_exp = r'[A-z]+\.[A-z\-]+\-[A-z]+\.[A-z\-]+'
        if re.findall(reg_exp, strings[0]):
            return " - ".join([strings[0], " / ".join(strings[1:3])])
        if re.findall(reg_exp, strings[2]):
            return " - ".join([" / ".join(strings[0:2]), strings[2]])
        if len(strings[0]) > max(len(strings[1]), len(strings[2])):
            return " - ".join([strings[0], " / ".join(strings[1:3])])
        if len(strings[2]) > max(len(strings[1]), len(strings[0])):
            return " - ".join([" / ".join(strings[0:2]), strings[2]])
    return ""


def get_sub_markets_players_basketball_zebet(id_match):
    if not id_match:
        return {}
    url = 'https://www.zebet.fr/fr/event/' + id_match + '-'
    markets_to_keep = {'Nombre de passes décisives pour le joueur (prolongations incluses) ?':'Passes',  'Nombre de rebonds pour le joueur (prolongations incluses) ?':'Rebonds'}
    soup = BeautifulSoup((urllib.request.urlopen(url)), features='lxml')
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    market_name = None
    for line in soup.find_all():
        if 'Zebet rencontre actuellement des difficultés techniques.' in line.text:
            raise sb.UnavailableSiteException
        if 'class' in line.attrs and 'bet-question' in line['class']:
            if line.text.strip() in markets_to_keep:
                market_name = line.text.strip()
        if market_name:
            if 'class' in line.attrs:
                if 'pmq-cote' in line['class']:
                    odd = float(line.text.strip().replace(',', '.'))
            if 'class' in line.attrs and 'pmq-cote-acteur' in line['class']:
                plus = "+" in line.text
                player = re.split('\s[\-|\+]', line.text.strip())[0].split()[1].strip()
                limit = re.split('\s[\-|\+]', line.text.strip())[(-1)].strip().replace(",", ".")
                player = re.split('\s[\-|\+]', line.text.strip())[0].strip()
                ref_player = player
                if is_player_added_in_db(player, "zebet"):
                    ref_player = is_player_added_in_db(player, "zebet")
                elif is_player_in_db(player):
                    add_player_to_db(player, "zebet")
                else:
                    if sb.DB_MANAGEMENT:
                        print(player, "zebet")
                    continue
                last = -1
                key_player = ref_player + "_" + limit
                key_market = markets_to_keep[market_name]
                if key_player not in sub_markets[key_market]:
                    sub_markets[key_market][key_player] = {"odds":{"zebet":[]}}
                if plus:
                    sub_markets[key_market][key_player]["odds"]["zebet"].insert(0, odd)
                    last = 0
                else:
                    sub_markets[key_market][key_player]["odds"]["zebet"].append(odd)
                if len(sub_markets[key_market][key_player]["odds"]["zebet"]) > 2:
                    del sub_markets[key_market][key_player]["odds"]["zebet"][last]
    
    for sub_market in sub_markets:
        sub_markets[sub_market] = dict(sub_markets[sub_market])
    
    return sub_markets
