"""
Unibet odds scraper
"""

import datetime
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from bs4 import BeautifulSoup

import sportsbetting as sb
from sportsbetting import selenium_init
from sportsbetting.auxiliary_functions import scroll

def parse_unibet(url):
    """
    Retourne les cotes disponibles sur unibet
    """
    selenium_init.DRIVER["unibet"].get(url)
    match_odds_hash = {}
    is_sport_page = len([x for x in url.split("/") if x]) == 4
    match = ""
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    date_time = None
    WebDriverWait(selenium_init.DRIVER["unibet"], 30).until(
        EC.invisibility_of_element_located(
            (By.CLASS_NAME, "ui-spinner")) or sb.ABORT
    )
    if sb.ABORT:
        raise sb.AbortException
    if is_sport_page:
        scroll(selenium_init.DRIVER["unibet"], "unibet", "calendar-event", 1)
    for _ in range(10):
        inner_html = selenium_init.DRIVER["unibet"].execute_script(
            "return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        if any(x in str(soup) for x in ["La page à laquelle vous souhaitez accéder n'existe plus.", "Aucun marché trouvé."]):
            raise sb.UnavailableCompetitionException
        for line in soup.findAll():
            if "class" in line.attrs and "cell-event" in line["class"]:
                match = line.text.strip()
                if match.count(" - ") > 1:
                    opponents = list(line.find_parent(attrs={"class":"calendar-event"})
                                     .findChildren(attrs={"class":"odd-longlabel"}))
                    match = opponents[0].text.replace(" - ", "-") + " - " + opponents[-1].text.replace(" - ", "-")
                if "-" not in match:
                    match = None
                    break
                reg_exp = re.compile(
                    r'\(\s?[0-7]-[0-7]\s?(,\s?[0-7]-[0-7]\s?)*([1-9]*[0-9]\/[1-9]*[0-9])*\)'
                    r'|\([0-7]\-[0-7](\s[0-7]\-[0-7])*\)'
                )
                if list(re.finditer(reg_exp, match)):  # match tennis live
                    match = match.split("(")[0].strip()
                    if " - " not in match:
                        match = match.replace("-", " - ")
            if "class" in line.attrs and "datetime" in line["class"]:
                date_time = datetime.datetime.strptime(
                    line.text, "%d/%m/%Y %H:%M")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year + 1)
            if "class" in line.attrs and "oddsbox" in line["class"]:
                odds = [float(child.text) for child in line.findChildren("span", {"class": "price"}) if child.text]
                if match:
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"unibet": odds}
                    match_odds_hash[match]['date'] = date_time
                    match = None
        if match_odds_hash:
            return match_odds_hash
    return match_odds_hash
