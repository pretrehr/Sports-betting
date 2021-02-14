"""
ParionsSport odds scraper
"""

import datetime

from bs4 import BeautifulSoup

import sportsbetting as sb
from sportsbetting import selenium_init
from sportsbetting.auxiliary_functions import merge_dicts, scroll

def parse_parionssport(url):
    """
    Retourne les cotes disponibles sur ParionsSport
    """
    is_sport_page = "paris-" in url.split("/")[-1] and "?" not in url
    is_basket = False  # "basket" in url
    selenium_init.DRIVER["parionssport"].get(url)
    if "maintenance technique" in selenium_init.DRIVER["parionssport"].execute_script(
            "return document.body.innerHTML"):
        raise sb.UnavailableSiteException
    if (selenium_init.DRIVER["parionssport"].current_url
            == "https://www.enligne.parionssport.fdj.fr/"):
        raise sb.UnavailableSiteException
    if (not is_sport_page) and selenium_init.DRIVER["parionssport"].current_url == "/".join(url.split("?")[0].split("/")[:4]):
        raise sb.UnavailableCompetitionException
    if is_sport_page:
        scroll(selenium_init.DRIVER["parionssport"],
               "parionssport", "wpsel-desc", 5)
    match_odds_hash = {}
    urls_basket = []
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = " " + str(today.year)
    date = ""
    match = ""
    date_time = None
    live = False
    for _ in range(10):
        inner_html = selenium_init.DRIVER["parionssport"].execute_script(
            "return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.findAll():
            if is_basket:
                if ("href" in line.attrs and list(line.stripped_strings)
                        and "+" in list(line.stripped_strings)[0]):
                    urls_basket.append(
                        "https://www.enligne.parionssport.fdj.fr" + line["href"])
            else:
                if "Nous vous prions de bien vouloir nous en excuser" in line:
                    raise sb.UnavailableCompetitionException
                if "class" in line.attrs and "wpsel-titleRubric" in line["class"]:
                    if line.text.strip() == "aujourd'hui":
                        date = datetime.date.today().strftime("%A %d %B %Y")
                    else:
                        date = line.text.strip().lower() + year
                if "class" in line.attrs and "wpsel-timerLabel" in line["class"]:
                    try:
                        date_time = datetime.datetime.strptime(date + " " + line.text,
                                                               "%A %d %B %Y À %Hh%M")
                        if date_time < today:
                            date_time = date_time.replace(
                                year=date_time.year + 1)
                    except ValueError:
                        date_time = "undefined"
                if "class" in line.attrs and "wpsel-desc" in line["class"]:
                    match = line.text.split(" À")[0].strip().replace("  ", " ")
                if "class" in line.attrs and "tag__stateLive" in line["class"]:
                    live = True
                if "class" in line.attrs and "buttonLine" in line["class"]:
                    if live:
                        live = False
                        continue
                    try:
                        odds = list(map(lambda x: float(x.replace(",", ".")),
                                        list(line.stripped_strings)))
                        match_odds_hash[match] = {}
                        match_odds_hash[match]['odds'] = {"parionssport": odds}
                        match_odds_hash[match]['date'] = date_time
                    except ValueError:
                        pass
        if match_odds_hash:
            return match_odds_hash
        elif urls_basket:
            list_odds = []
            for match_url in urls_basket:
                if sb.ABORT:
                    break
                list_odds.append(parse_match_nba_parionssport(match_url))
            return merge_dicts(list_odds)
    return match_odds_hash


def parse_match_nba_parionssport(url):
    """
    Recupere les cotes d'un match de NBA
    """
    selenium_init.DRIVER["parionssport"].get(url)
    match_odds = {}
    date_time = "undefined"
    match = ""
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = " " + str(today.year)
    for _ in range(10):
        inner_html = selenium_init.DRIVER["parionssport"].execute_script(
            "return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.findAll():
            if "class" in line.attrs and "header-banner-event-date-section" in line["class"]:
                date_time = datetime.datetime.strptime(list(line.stripped_strings)[0] + year,
                                                       "Le %d %B à %H:%M %Y")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year + 1)
            elif "class" in line.attrs and "headband-eventLabel" in line["class"]:
                match = list(line.stripped_strings)[0]
                print("\t" + match)
            elif "class" in line.attrs and "wpsel-market-detail" in line["class"] and match:
                strings = list(line.stripped_strings)
                odds = list(map(lambda x: float(x.replace(",", ".")),
                                strings[2::2]))
                match_odds[match] = {"date": date_time,
                                     "odds": {"parionssport": odds}}
                return match_odds
    return match_odds
