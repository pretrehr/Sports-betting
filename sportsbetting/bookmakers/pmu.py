"""
PMU odds scraper
"""

import datetime
import json
import urllib
import urllib.error
import urllib.request

from bs4 import BeautifulSoup
from collections import defaultdict

import sportsbetting as sb
from sportsbetting.auxiliary_functions import merge_dicts, truncate_datetime

def parse_pmu(url=""):
    """
    Retourne les cotes disponibles sur pmu
    """
    if "http" not in url:
        return parse_sport_pmu(url)
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    return parse_pmu_html(soup)


def parse_pmu_html(soup):
    """
    Retourne les cotes disponibles sur une page html pmu
    """
    match_odds_hash = {}
    match = ""
    date_time = "undefined"
    live = False
    handicap = False
    date = ""
    match_id = None
    for line in soup.find_all():
        if "n'est pas accessible pour le moment !" in line.text:
            raise sb.UnavailableSiteException
        if "data-date" in line.attrs and "shadow" in line["class"]:
            date = line["data-date"]
        elif "class" in line.attrs and "trow--live--remaining-time" in line["class"]:
            hour = line.text
            if "'" in hour:
                date_time = datetime.datetime.today()+datetime.timedelta(minutes=int(hour.strip().strip("'")) + 1)
                date_time = truncate_datetime(date_time)
                continue
            try:
                date_time = datetime.datetime.strptime(
                    date + " " + hour, "%Y-%m-%d %Hh%M")
            except ValueError:
                date_time = "undefined"
        elif "class" in line.attrs and "trow--live--logo-active" in line["class"]:
            live = True
        elif "class" in line.attrs and "trow--event--name" in line["class"]:
            string = "".join(list(line.stripped_strings))
            if "//" in string:
                try:
                    is_rugby_13 = line.find_parent("a")["data-sport_id"] == "rugby_a_xiii"
                except TypeError:
                    is_rugby_13 = False
                if is_rugby_13 or live:
                    continue
                handicap = False
                if "+" in string or "Egalité" in string:
                    handicap = True
                    match, odds = parse_page_match_pmu("https://paris-sportifs.pmu.fr"
                                                        + line.parent["href"])
                else:
                    match = string.replace(" - ", "-")
                    match = match.replace(" // ", " - ")
                    match = match.replace("//", " - ")
        elif "class" in line.attrs and "event-list-odds-list" in line["class"]:
            if live or is_rugby_13:
                live = False
                is_rugby_13 = False
                continue
            if not handicap:
                odds = list(
                    map(lambda x: float(x.replace(",", ".")), list(line.stripped_strings)))
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"pmu": odds}
            match_odds_hash[match]['date'] = date_time
            match_odds_hash[match]['id'] = {"pmu": match_id}
        elif "data-ev_id" in line.attrs:
            match_id = line["data-ev_id"]
    if not match_odds_hash:
        raise sb.UnavailableCompetitionException
    return match_odds_hash


def parse_page_match_pmu(url):
    """
    Retourne les cotes d'une page de match sur pmu
    """
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    _id = "-1"
    odds = []
    name = soup.find("title").text.split(" - ")[0].replace("//", "-")
    reversed_odds = False
    if "chez les" in name:
        teams = name.split(" chez les ")
        name = teams[1] + " - " + teams[0]
        reversed_odds = True
    print("\t" + name)
    for line in soup.find_all(["option", "a"]):
        if line.text in ["Vainqueur du match", "1N2 à la 60e minute"]:
            _id = line["data-market-id"]
        if "data-ev_mkt_id" in line.attrs and line["data-ev_mkt_id"] == _id:
            odds.append(float(line.text.replace(",", ".")))
    if reversed_odds:
        odds.reverse()
    return name, odds


def parse_sport_pmu(sport):
    """
    Retourne les cotes disponibles sur pmu pour un sport donné
    """
    list_odds = []
    id_sport = {"football": [8], "tennis": [11], "rugby": [7],
                "hockey-sur-glace": [40, 44], "basketball": [5, 37]}
    i = 0
    for _id in id_sport[sport]:
        while True:
            url = "https://paris-sportifs.pmu.fr/pservices/more_events/{0}/{1}/pmu-event-list-load-more-{0}".format(_id, i)
            response = urllib.request.urlopen(url)
            data = json.loads(response.read())
            soup = BeautifulSoup(data[1]["html"], features="lxml")
            try:
                list_odds.append(parse_pmu_html(soup))
                i += 1
            except sb.UnavailableCompetitionException:
                break
    return merge_dicts(list_odds)

def get_odds_from_market_id(id_market):
    url = 'https://paris-sportifs.pmu.fr/pservices/render-market/{}?referrer_page=event'.format(id_market)
    soup = BeautifulSoup((urllib.request.urlopen(url)), features='lxml')
    fields = list(soup.find('tbody').stripped_strings)
    return (fields[1], [float(fields[2].replace(',', '.')), float(fields[5].replace(',', '.'))])

def get_sub_markets_players_basketball_pmu(id_match):
    if not id_match:
        return {}
    url = 'https://paris-sportifs.pmu.fr/event/' + id_match
    markets_to_keep = {'Passes décisives':'Passes',  'Rebonds':'Rebonds'}
    soup = BeautifulSoup((urllib.request.urlopen(url)), features='lxml')
    sub_markets = {v:defaultdict(list) for v in markets_to_keep.values()}
    market_name = None
    for line in soup.find_all():
        if 'aria-controls' in line.attrs:
            if 'table-content' in line['aria-controls']:
                id_market = line['aria-controls'].strip('table-content-')
        if 'class' in line.attrs and 'table--header-title' in line['class']:
            market_title = line.text.strip()
            if 'Rebonds' in market_title or 'Passes décisives' in market_title:
                player, market_name = market_title.split(' - ')
                player = player.split()[1]
                limit, odds = get_odds_from_market_id(id_market)
                sub_markets[markets_to_keep[market_name]][player + "_" + limit] = odds
    
    for sub_market in sub_markets:
        sub_markets[sub_market] = dict(sub_markets[sub_market])
    
    return sub_markets