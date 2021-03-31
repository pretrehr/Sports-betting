"""
France-pari odds scraper
"""

import datetime
import re
import requests

from bs4 import BeautifulSoup

import sportsbetting as sb

def parse_france_pari(url):
    """
    Retourne les cotes disponibles sur france-pari
    """
    soup = BeautifulSoup(requests.get(url).content, features="lxml")
    match_odds_hash = {}
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = " " + str(today.year)
    date = ""
    match = ""
    date_time = None
    id = None
    for line in soup.find_all():
        if "class" in line.attrs and "date" in line["class"]:
            date = line.text + year
        elif "class" in line.attrs and "odd-event-block" in line["class"]:
            strings = list(line.stripped_strings)
            if "snc-odds-date-lib" in line["class"]:
                id = line.findChild("a" , recursive=True).get("href").split("-")[0].split("/")[-1]
                hour = strings[0]
                try:
                    i = strings.index("/")
                    date_time = datetime.datetime.strptime(
                        date + " " + hour, "%A %d %B %Y %H:%M")
                    if date_time < today:
                        date_time = date_time.replace(year=date_time.year + 1)
                    match = " ".join(strings[1:i]) + \
                        " - " + " ".join(strings[i + 1:])
                    reg_exp = (r'\[[0-7]\/[0-7]\s?([0-7]\/[0-7]\s?)*\]'
                               r'|\[[0-7]\-[0-7]\s?([0-7]\-[0-7]\s?)*\]')
                    if list(re.finditer(reg_exp, match)):  # match tennis live
                        match = match.split("[")[0].strip()
                except ValueError:
                    pass
            else:
                odds = []
                for i, val in enumerate(strings):
                    if i % 2:
                        odds.append(float(val.replace(",", ".")))
                try:
                    if match:
                        match_odds_hash[match] = {}
                        match_odds_hash[match]['odds'] = {"france_pari": odds}
                        match_odds_hash[match]['date'] = date_time
                        match_odds_hash[match]['id'] = {"france_pari": id}
                except UnboundLocalError:
                    pass
    if not match_odds_hash:
        raise sb.UnavailableCompetitionException
    return match_odds_hash
