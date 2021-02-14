"""
Pokerstars odds scraper
"""

import datetime

import selenium.common
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from bs4 import BeautifulSoup

import sportsbetting as sb
from sportsbetting import selenium_init
from sportsbetting.auxiliary_functions import merge_dicts

def parse_betstars(url):
    """
    Retourne les cotes disponibles sur betstars
    """
    if url in ["tennis", "handball", "basketball", "soccer", "handball", "rugby_union",
               "ice_hockey"]:
        return parse_sport_betstars(url)
    selenium_init.DRIVER["betstars"].get(url)
    match_odds_hash = {}
    match = ""
    odds = []
    is_12 = False
    get_long_names = False
    opponents = []
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = str(today.year)
    try:
        WebDriverWait(selenium_init.DRIVER["betstars"], 15).until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "match-time")) or sb.ABORT
        )
        if sb.ABORT:
            raise sb.AbortException
        inner_html = (selenium_init.DRIVER["betstars"]
                      .execute_script("return document.body.innerHTML"))
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.findAll():
            if "id" in line.attrs and "participants" in line["id"] and not is_12:
                match = " - ".join(list(map(lambda x: x.replace(" - ", "-"),
                                            line.stripped_strings)))
            if "class" in line.attrs and "afEvt__link" in line["class"]:
                is_12 = True
                match = list(line.stripped_strings)[0]
                if "@" in match:
                    teams = match.split(" @ ")
                    match = teams[1].replace(" - ", "-") + " - " + teams[0].replace(" - ", "-")
                if match.count(" - ") > 1:
                    get_long_names = True
                    opponents = []
                odds = []
            if get_long_names and "class" in line.attrs and "teamLongName" in line["class"]:
                if opponents:
                    match = opponents[0] + " - " + line.text.strip().replace(" - ", "-")
                    get_long_names = False
                    opponents = []
                else:
                    opponents.append(line.text.strip().replace(" - ", "-"))
            if "class" in line.attrs and ("market-AB" in line["class"]
                                          #                                           or "market-BAML" in line["class"]
                                          or "market-BASKETBALL-FTOT-ML" in line["class"]):
                try:
                    odds.append(
                        float(list(line.stripped_strings)[0].replace(",", ".")))
                except ValueError:  # cote non disponible (OTB, Non publiée)
                    odds.append(1)
            if "class" in line.attrs and "match-time" in line["class"]:
                strings = list(line.stripped_strings)
                date = strings[0] + " " + year
                hour = strings[1]
                try:
                    date_time = datetime.datetime.strptime(
                        date + " " + hour, "%d %b, %Y %H:%M")
                except ValueError:
                    date = datetime.datetime.today().strftime("%d %b %Y")
                    hour = strings[0]
                    date_time = datetime.datetime.strptime(
                        date + " " + hour, "%d %b %Y %H:%M")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year + 1)
                match = match.replace("  ", " ")
                if odds:
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"betstars": odds}
                    match_odds_hash[match]['date'] = date_time
                    odds = []
            if "class" in line.attrs and "prices" in line["class"]:
                try:
                    odds = list(map(lambda x: float(x.replace(",", ".")),
                                    list(line.stripped_strings)))
                except ValueError:
                    odds = []
        if match_odds_hash:
            return match_odds_hash
    except selenium.common.exceptions.TimeoutException:
        inner_html = selenium_init.DRIVER["betstars"].execute_script(
            "return document.body.innerHTML")
        if ("Nous procédons à une mise à jour" in inner_html or
                "Nous devons procéder à la correction ou à la mise à jour d’un élément"
                in inner_html):
            raise sb.UnavailableSiteException
        else:
            print("Aucun pari prématch disponible")
    return match_odds_hash


def parse_sport_betstars(sport):
    """
    Retourne les cotes disponibles sur betstars pour un sport donné
    """
    selenium_init.DRIVER["betstars"].get(
        "https://www.pokerstarssports.fr/#/{}/competitions".format(sport))
    urls = []
    competitions = []
    WebDriverWait(selenium_init.DRIVER["betstars"], 15).until(
        EC.presence_of_element_located(
            (By.CLASS_NAME, "basicList__item")) or sb.ABORT
    )
    if sb.ABORT:
        raise sb.AbortException
    inner_html = selenium_init.DRIVER["betstars"].execute_script(
        "return document.body.innerHTML")
    if ("Nous procédons à une mise à jour" in inner_html or
            "Nous devons procéder à la correction ou à la mise à jour d’un élément"
            in inner_html):
        raise sb.UnavailableSiteException
    soup = BeautifulSoup(inner_html, features="lxml")
    for line in soup.findAll(["a"]):
        if ("href" in line.attrs and sport + "/competitions/" in line["href"]
                and "data-leagueid" in line.attrs):
            url = "https://www.pokerstarssports.fr/" + line["href"]
            if url not in urls:
                urls.append(url)
                competitions.append(line.text.strip())
    list_odds = []
    for url, competition in zip(urls, competitions):
        print("\t" + competition)
        try:
            odds = parse_betstars(url)
            list_odds.append(odds)
        except KeyboardInterrupt:
            pass
    return merge_dicts(list_odds)
