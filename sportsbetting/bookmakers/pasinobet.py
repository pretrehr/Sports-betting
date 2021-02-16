"""
Pasinobet odds scraper
"""

import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from bs4 import BeautifulSoup

import sportsbetting as sb
from sportsbetting import selenium_init
from sportsbetting.auxiliary_functions import reverse_match_odds

def parse_pasinobet(url):
    """
    Retourne les cotes disponibles sur pasinobet
    """
    selenium_init.DRIVER["pasinobet"].get("about:blank")
    selenium_init.DRIVER["pasinobet"].get(url)
    reversed_odds = "North%20America" in url
    match_odds_hash = {}
    match = None
    date_time = None
    WebDriverWait(selenium_init.DRIVER["pasinobet"], 15).until(
        EC.invisibility_of_element_located(
            (By.CLASS_NAME, "skeleton-line")) or sb.ABORT
    )
    if sb.ABORT:
        raise sb.AbortException
    inner_html = selenium_init.DRIVER["pasinobet"].execute_script(
        "return document.body.innerHTML")
    soup = BeautifulSoup(inner_html, features="lxml")
    date = ""
    for line in soup.findAll():
        if sb.ABORT:
            raise sb.AbortException
        if "class" in line.attrs and "category-date" in line["class"]:
            date = line.text.lower()
            date = date.replace("nov", "novembre")
            date = date.replace("déc", "décembre")
            date = date.replace("jan", "janvier")
            date = date.replace("fév", "février")
            date = date.replace("mar ", "mars ")
        if "class" in line.attrs and "event-header" in line["class"]:
            match = " - ".join(map(lambda x: list(x.stripped_strings)[0],
                                   line.findChildren("div", {"class": "teams-container-layout2"})))
            time = line.findChild("div", {"class": "sbEventsList__time"}).text.strip()
            try:
                date_time = datetime.datetime.strptime(date+time, "%A, %d %B %Y%H:%M")
            except ValueError:
                date_time = "undefined"
        if "class" in line.attrs and "event-list" in line["class"]:
            if "---" not in list(line.stripped_strings):
                odds = list(map(float, line.stripped_strings))
                if reversed_odds:
                    match, odds = reverse_match_odds(match, odds)
                match_odds_hash[match] = {}
                match_odds_hash[match]["date"] = date_time
                match_odds_hash[match]["odds"] = {"pasinobet": odds}
    return match_odds_hash


# def parse_pasinobet_sport(sport):
#     selenium_init.start_selenium("pasinobet", False)
#     selenium_init.DRIVER["pasinobet"].maximize_window()
#     selenium_init.DRIVER["pasinobet"].get(
#         "https://www.pasinobet.fr/#/sport/?type=0&sport=1&region=-1")
#     sport_items = WebDriverWait(selenium_init.DRIVER["pasinobet"], 15).until(
#         EC.presence_of_all_elements_located((By.CLASS_NAME, "sport-header"))
#     )
#     for sport_item in sport_items:
#         if sport_item.text.split() and sport_item.text.split()[0] == sport:
#             sport_item.find_element_by_xpath("..").click()
#             break
#     regions = WebDriverWait(selenium_init.DRIVER["pasinobet"], 15).until(
#         EC.presence_of_all_elements_located((By.CLASS_NAME, "region"))
#     )
#     input()
#     selenium_init.DRIVER["pasinobet"].quit()
