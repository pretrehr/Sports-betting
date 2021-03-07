"""
JOA odds scraper
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


COOKIES_ACCEPTED = False


def accept_cookies_joa():
    """
    Accept cookies on JOA
    """
    global COOKIES_ACCEPTED
    try:
        cookies = WebDriverWait(selenium_init.DRIVER["joa"], 15).until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, "cc-cookie-accept")) or sb.ABORT
        )
        if sb.ABORT:
            raise sb.AbortException
        cookies.click()
    except selenium.common.exceptions.TimeoutException:
        pass
    COOKIES_ACCEPTED = True
    

def parse_joa(url):
    """
    Retourne les cotes disponibles sur joa
    """
    global COOKIES_ACCEPTED
    if "sport/sport" in url:
        return parse_joa_sport(url)
    selenium_init.DRIVER["joa"].get(url)
    if not COOKIES_ACCEPTED:
        accept_cookies_joa()
    match_odds_hash = {}
    try:
        WebDriverWait(selenium_init.DRIVER["joa"], 30).until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "bet-event-name")) or sb.ABORT
        )
        if sb.ABORT:
            raise sb.AbortException
    except selenium.common.exceptions.TimeoutException:
        raise sb.UnavailableCompetitionException
    for _ in range(10):
        inner_html = selenium_init.DRIVER["joa"].execute_script(
            "return document.body.innerHTML")
        match_odds_hash = parse_joa_html(inner_html)
        if match_odds_hash:
            return match_odds_hash
    return match_odds_hash


def parse_joa_html(inner_html):
    """
    Retourne les cotes disponibles sur une page html joa
    """
    match_odds_hash = {}
    match = None
    date_time = None
    soup = BeautifulSoup(inner_html, features="lxml")
    for line in soup.findAll():
        if "class" in line.attrs and "bet-event-name" in line["class"]:
            match = " - ".join(map(lambda x: x.replace(" - ",
                                                       "-"), list(line.stripped_strings)[2:4]))
        if "class" in line.attrs and "bet-event-date-info-top" in line["class"]:
            date_time = format_joa_time(line.text)
        if "class" in line.attrs and "bet-outcome-list" in line["class"]:
            if match:
                try:
                    odds = list(map(float, list(line.stripped_strings)))
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"joa": odds}
                    match_odds_hash[match]['date'] = date_time
                except ValueError:
                    pass
                match = None
    return match_odds_hash


def parse_joa_sport(url):
    """
    Retourne les cotes disponibles sur joa pour un sport donné
    """
    global COOKIES_ACCEPTED
    selenium_init.DRIVER["joa"].maximize_window()
    selenium_init.DRIVER["joa"].get(url)
    if not COOKIES_ACCEPTED:
        accept_cookies_joa()
    list_odds = []
    try:
        filtres = WebDriverWait(selenium_init.DRIVER["joa"], 15).until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "Filtres")) or sb.ABORT
        )
        if sb.ABORT:
            raise sb.AbortException
    except selenium.common.exceptions.TimeoutException:
        raise sb.UnavailableCompetitionException
    for i, _ in enumerate(filtres):
        selenium_init.DRIVER["joa"].execute_script("window.scrollTo(0, 0)")
        selenium_init.DRIVER["joa"].execute_script(
            'document.getElementsByClassName("Filtres")[{}].click()'.format(i))
        match_odds_hash = {}
        try:
            WebDriverWait(selenium_init.DRIVER["joa"], 15).until(
                EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, "bet-event-name")) or sb.ABORT
            )
            if sb.ABORT:
                raise sb.AbortException
        except selenium.common.exceptions.TimeoutException:
            raise sb.UnavailableCompetitionException
        while True:
            try:
                show_more = WebDriverWait(selenium_init.DRIVER["joa"], 5).until(
                    EC.presence_of_all_elements_located(
                        (By.CLASS_NAME, "show-more-leagues")) or sb.ABORT
                )[0]
                if sb.ABORT:
                    raise sb.AbortException
                show_more.find_element_by_tag_name("button").click()
            except selenium.common.exceptions.TimeoutException:
                break
            except selenium.common.exceptions.WebDriverException:
                break
        inner_html = selenium_init.DRIVER["joa"].execute_script(
            "return document.body.innerHTML")
        match_odds_hash = parse_joa_html(inner_html)
        if match_odds_hash:
            list_odds.append(match_odds_hash)
    return merge_dicts(list_odds)

def format_joa_time(string):
    """
    Gets the time information from a string on html JOA page
    """
    if "Aujourd'hui" in string or "Demain" in string:
        today = datetime.datetime.today().strftime("%d/%m/%Y ")
        tomorrow = (datetime.datetime.today()+datetime.timedelta(days=1)).strftime("%d/%m/%Y ")
        string = " ".join(string.replace("Aujourd'hui", today).replace("Demain", tomorrow).split())
        return datetime.datetime.strptime(string, "%d/%m/%Y %H:%M")
    date_time = None
    year = str(datetime.datetime.today().year)
    string += year
    date_time = datetime.datetime.strptime(string, "%d/%m%H:%M%Y")
    if date_time < datetime.datetime.today():
        date_time = date_time.replace(year=date_time.year + 1)
    return date_time
