"""
PMU odds scraper
"""

import datetime
import json
import urllib
import urllib.error
import urllib.request

from bs4 import BeautifulSoup

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
                if not is_rugby_13:
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
            if live:
                live = False
                continue
            if not handicap:
                odds = list(
                    map(lambda x: float(x.replace(",", ".")), list(line.stripped_strings)))
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"pmu": odds}
            match_odds_hash[match]['date'] = date_time
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
    id_sport = {"football": 8, "tennis": 11, "rugby": 7,
                "hockey-sur-glace": 44, "basketball": 5}
    i = 0
    _id = id_sport[sport]
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
