"""
Bwin odds scraper
"""

import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from bs4 import BeautifulSoup

import sportsbetting as sb
from sportsbetting import selenium_init
from sportsbetting.auxiliary_functions import reverse_match_odds, scroll, truncate_datetime

def parse_bwin(url):
    """
    Retourne les cotes disponibles sur bwin
    """
    selenium_init.DRIVER["bwin"].maximize_window()
    selenium_init.DRIVER["bwin"].get(url)
    match_odds_hash = {}
    match = None
    date_time = None
    index_column_result_odds = 1 if "handball" in url else 0
    is_sport_page = "/0" in url
    reversed_odds = False
    live = False
    WebDriverWait(selenium_init.DRIVER["bwin"], 15).until(
        EC.presence_of_all_elements_located(
            (By.CLASS_NAME, "participants-pair-game")) or sb.ABORT
    )
    if sb.ABORT:
        raise sb.AbortException
    if is_sport_page:
        scroll(selenium_init.DRIVER["bwin"], "bwin",
               "grid-event-detail", 3, 'getElementById("main-view")')
    for _ in range(10):
        inner_html = selenium_init.DRIVER["bwin"].execute_script(
            "return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.findAll():
            if "class" in line.attrs and "grid-group" in line["class"]:
                strings = list(line.stripped_strings)
                if "Pari sur le vainqueur" in strings:
                    index_column_result_odds = strings.index(
                        "Pari sur le vainqueur")
            if "class" in line.attrs and "participants-pair-game" in line["class"]:
                teams = []
                if line.findChildren(attrs={"class": "participant-container"}):
                    names_and_countries = list(line.findChildren(attrs={"class": "participant-container"}))
                    for name_and_country in names_and_countries:
                        strings = list(name_and_country.stripped_strings)
                        if len(strings) == 2 and strings[1] != '@':
                            teams.append(strings[0] + " ("+strings[1]+")")
                        else:
                            teams.append(strings[0])
                match = " - ".join(teams)
                reversed_odds = True if line.findChildren(attrs={"class": "away-indicator"}) else False
            if "class" in line.attrs and "starting-time" in line["class"]:
                date_time = format_bwin_time(line.text)
            if "class" in line.attrs and "live-icon" in line["class"]:
                live = True
            if "class" in line.attrs and "grid-group-container" in line["class"]:
                if (line.findChildren(attrs={"class": "grid-option-group"})
                        and "Pariez maintenant !" not in list(line.stripped_strings)):
                    odds_line = line.findChildren(
                        attrs={"class": "grid-option-group"})[index_column_result_odds]
                    odds = []
                    for odd in list(odds_line.stripped_strings):
                        try:
                            odds.append(float(odd))
                        except ValueError:
                            break
                    if match:
                        if reversed_odds:
                            match, odds = reverse_match_odds(match, odds)
                        if not live:
                            match_odds_hash[match] = {}
                            match_odds_hash[match]['odds'] = {"bwin": odds}
                            match_odds_hash[match]['date'] = date_time
                        else:
                            live = False
                        match = None
                        date_time = "undefined"
        if match_odds_hash:
            return match_odds_hash
    return match_odds_hash


def format_bwin_names(string):
    """
    Returns match from a string available on bwin html
    """
    if string.count(" - ") == 3:
        string = string.replace(" - ", " (", 1)
        string = string.replace(" - ", ") - ", 1)
        string = " (".join(string.rsplit(" - ", 1))
        string += ")"
    string = string.replace("@ - ", "")
    return string

def format_bwin_time(string):
    """
    Returns time from a string available on bwin html
    """
    today = datetime.datetime.today().strftime("%d/%m/%Y ")
    tomorrow = (datetime.datetime.today()+datetime.timedelta(days=1)).strftime("%d/%m/%Y ")
    string = " ".join(string.replace("Aujourd'hui/", today).replace("Demain/", tomorrow).split())
    if "Commence dans" in string:
        date_time = truncate_datetime(datetime.datetime.today())
        date_time += datetime.timedelta(minutes=int(string.split("dans ")[1]
                                                    .split("min")[0]) + 1)
        return date_time
    if "Commence maintenant" in string:
        return truncate_datetime(datetime.datetime.today())
    return datetime.datetime.strptime(string, "%d/%m/%Y %H:%M")
