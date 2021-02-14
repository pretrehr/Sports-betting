"""
Betclic odds scraper
"""

import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from bs4 import BeautifulSoup

import sportsbetting as sb
from sportsbetting import selenium_init
from sportsbetting.auxiliary_functions import scroll


def parse_betclic(url):
    """
    Gets the odds available on a Betclic url
    """
    selenium_init.DRIVER["betclic"].get(url)
    is_sport_page = len([x for x in url.split("/") if x]) == 3
    match_odds_hash = {}
    match = None
    date_time = None
    today = datetime.datetime.today().strftime("%d/%m/%Y")
    tomorrow = (datetime.datetime.today() +
                datetime.timedelta(days=1)).strftime("%d/%m/%Y")
    if (selenium_init.DRIVER["betclic"].current_url
            == "https://www.betclic.fr/"):
        raise sb.UnavailableCompetitionException
    WebDriverWait(selenium_init.DRIVER["betclic"], 15).until(
        EC.invisibility_of_element_located(
            (By.TAG_NAME, "app-preloader")) or sb.ABORT
    )
    if sb.ABORT:
        raise sb.AbortException
    if is_sport_page:
        scroll(selenium_init.DRIVER["betclic"], "betclic", "betBox_match", 10)
    for _ in range(10):
        inner_html = selenium_init.DRIVER["betclic"].execute_script(
            "return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        if "Désolé, cette compétition n'est plus disponible." in str(soup):
            raise sb.UnavailableCompetitionException
        for line in soup.findAll():
            if "class" in line.attrs and "betBox_matchName" in line["class"]:
                match = " - ".join(list(line.stripped_strings))
            if line.name == "app-date":
                string = " ".join(line.text.replace(
                    "Aujourd'hui", today).replace("Demain", tomorrow).split())
                date_time = datetime.datetime.strptime(
                    string, "%d/%m/%Y %H:%M")
            if "class" in line.attrs and "betBox_odds" in line["class"]:
                try:
                    odds = list(map(lambda x: float(x.text.replace(",", ".")),
                                    list(line.findChildren("span", {"class": "oddValue"}))))
                    if match:
                        match_odds_hash[match] = {}
                        match_odds_hash[match]['odds'] = {"betclic": odds}
                        match_odds_hash[match]['date'] = date_time
                        match = None
                except ValueError:
                    pass
        if match_odds_hash:
            return match_odds_hash
    return match_odds_hash
