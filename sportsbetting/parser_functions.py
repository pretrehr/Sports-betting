"""
Fonctions de parsing
"""

import datetime
import json
import locale
import re
import sys
import time
import http.client
import urllib
import urllib.error
import urllib.request
import fake_useragent

import selenium
import selenium.common
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup

import sportsbetting
from sportsbetting import selenium_init
from sportsbetting.auxiliary_functions import (merge_dicts, reverse_match_odds,
                                               scroll, format_bwin_names,
                                               format_bwin_time,
                                               format_joa_time,
                                               format_zebet_names)


if sys.platform == "win32":
    locale.setlocale(locale.LC_TIME, "fr")
else:  # sys.platform == "linux"
    locale.setlocale(locale.LC_TIME, "fr_FR.utf8")


def parse_betclic(url):
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
        raise sportsbetting.UnavailableCompetitionException
    WebDriverWait(selenium_init.DRIVER["betclic"], 15).until(
        EC.invisibility_of_element_located(
            (By.TAG_NAME, "app-preloader")) or sportsbetting.ABORT
    )
    if sportsbetting.ABORT:
        raise sportsbetting.AbortException
    if is_sport_page:
        scroll(selenium_init.DRIVER["betclic"], "betclic", "betBox_match", 10)
    for _ in range(10):
        inner_html = selenium_init.DRIVER["betclic"].execute_script(
            "return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        if "Désolé, cette compétition n'est plus disponible." in str(soup):
            raise sportsbetting.UnavailableCompetitionException
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


def parse_betstars(url=""):
    """
    Retourne les cotes disponibles sur betstars
    """
    if url in ["tennis", "handball", "basketball", "soccer", "handball", "rugby_union",
               "ice_hockey"]:
        return parse_sport_betstars(url)
    if not url:
        url = "https://www.betstars.fr/#/soccer/competitions/2152298"
    selenium_init.DRIVER["betstars"].get(url)
    match_odds_hash = {}
    match = ""
    odds = []
    is_12 = False
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = str(today.year)
    try:
        WebDriverWait(selenium_init.DRIVER["betstars"], 15).until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "match-time")) or sportsbetting.ABORT
        )
        if sportsbetting.ABORT:
            raise sportsbetting.AbortException
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
                    match = teams[1] + " - " + teams[0]
                odds = []
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
            raise sportsbetting.UnavailableSiteException
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
            (By.CLASS_NAME, "basicList__item")) or sportsbetting.ABORT
    )
    if sportsbetting.ABORT:
        raise sportsbetting.AbortException
    inner_html = selenium_init.DRIVER["betstars"].execute_script(
        "return document.body.innerHTML")
    if ("Nous procédons à une mise à jour" in inner_html or
            "Nous devons procéder à la correction ou à la mise à jour d’un élément"
            in inner_html):
        raise sportsbetting.UnavailableSiteException
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


def parse_bwin(url):
    selenium_init.DRIVER["bwin"].maximize_window()
    selenium_init.DRIVER["bwin"].get(url)
    match_odds_hash = {}
    match = None
    date_time = None
    index_column_result_odds = 1 if "handball" in url else 0
    is_sport_page = "/0" in url
    reversed_odds = False
    WebDriverWait(selenium_init.DRIVER["bwin"], 15).until(
        EC.presence_of_all_elements_located(
            (By.CLASS_NAME, "participants-pair-game")) or sportsbetting.ABORT
    )
    if sportsbetting.ABORT:
        raise sportsbetting.AbortException
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
                match = " - ".join(list(line.stripped_strings))
                reversed_odds = "@" in match
                match = format_bwin_names(match)
            if "class" in line.attrs and "starting-time" in line["class"]:
                date_time = format_bwin_time(line.text)
            if "class" in line.attrs and "grid-group-container" in line["class"]:
                if line.findChildren(attrs={"class": "grid-option-group"}) and "Pariez maintenant !" not in list(line.stripped_strings):
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
                        match_odds_hash[match] = {}
                        match_odds_hash[match]['odds'] = {"bwin": odds}
                        match_odds_hash[match]['date'] = date_time
                        match = None
                        date_time = "undefined"
        if match_odds_hash:
            return match_odds_hash
    return match_odds_hash


def parse_france_pari(url=""):
    """
    Retourne les cotes disponibles sur france-pari
    """
    if not url:
        url = "https://www.france-pari.fr/competition/96-parier-sur-ligue-1-conforama"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = " " + str(today.year)
    date = ""
    match = ""
    date_time = None
    for line in soup.find_all():
        if "class" in line.attrs and "date" in line["class"]:
            date = line.text + year
        elif "class" in line.attrs and "odd-event-block" in line["class"]:
            strings = list(line.stripped_strings)
            if "snc-odds-date-lib" in line["class"]:
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
                except UnboundLocalError:
                    pass
    if not match_odds_hash:
        raise sportsbetting.UnavailableCompetitionException
    return match_odds_hash


def parse_joa_html(inner_html):
    match_odds_hash = {}
    match = None
    date_time = None
    soup = BeautifulSoup(inner_html, features="lxml")
    for line in soup.findAll():
        if "class" in line.attrs and "bet-event-name" in line["class"]:
            match = " - ".join(map(lambda x: x.replace(" - ",
                                                       "-"), list(line.stripped_strings)))
        if "class" in line.attrs and "bet-event-date-info" in line["class"]:
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


def parse_joa(url):
    if "sport/sport" in url:
        return parse_joa_sport(url)
    selenium_init.DRIVER["joa"].get(url)
    match_odds_hash = {}
    try:
        WebDriverWait(selenium_init.DRIVER["joa"], 30).until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "bet-event-name")) or sportsbetting.ABORT
        )
        if sportsbetting.ABORT:
            raise sportsbetting.AbortException
    except selenium.common.exceptions.TimeoutException:
        raise sportsbetting.UnavailableCompetitionException
    for _ in range(10):
        inner_html = selenium_init.DRIVER["joa"].execute_script(
            "return document.body.innerHTML")
        match_odds_hash = parse_joa_html(inner_html)
        if match_odds_hash:
            return match_odds_hash
    return match_odds_hash


def parse_joa_sport(url):
    selenium_init.DRIVER["joa"].maximize_window()
    selenium_init.DRIVER["joa"].get(url)
    list_odds = []
    cookies = WebDriverWait(selenium_init.DRIVER["joa"], 15).until(
        EC.element_to_be_clickable(
            (By.CLASS_NAME, "cc-cookie-accept")) or sportsbetting.ABORT
    )
    if sportsbetting.ABORT:
        raise sportsbetting.AbortException
    cookies.click()
    try:
        filtres = WebDriverWait(selenium_init.DRIVER["joa"], 15).until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "Filtres")) or sportsbetting.ABORT
        )
        if sportsbetting.ABORT:
            raise sportsbetting.AbortException
    except selenium.common.exceptions.TimeoutException:
        raise sportsbetting.UnavailableCompetitionException
    for i, _ in enumerate(filtres):
        selenium_init.DRIVER["joa"].execute_script("window.scrollTo(0, 0)")
        selenium_init.DRIVER["joa"].execute_script(
            'document.getElementsByClassName("Filtres")[{}].click()'.format(i))
        match_odds_hash = {}
        try:
            WebDriverWait(selenium_init.DRIVER["joa"], 15).until(
                EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, "bet-event-name")) or sportsbetting.ABORT
            )
            if sportsbetting.ABORT:
                raise sportsbetting.AbortException
        except selenium.common.exceptions.TimeoutException:
            raise sportsbetting.UnavailableCompetitionException
        while True:
            try:
                show_more = WebDriverWait(selenium_init.DRIVER["joa"], 5).until(
                    EC.presence_of_all_elements_located(
                        (By.CLASS_NAME, "show-more-leagues")) or sportsbetting.ABORT
                )[0]
                if sportsbetting.ABORT:
                    raise sportsbetting.AbortException
                show_more.find_element_by_tag_name("button").click()
            except selenium.common.exceptions.TimeoutException:
                break
        inner_html = selenium_init.DRIVER["joa"].execute_script(
            "return document.body.innerHTML")
        match_odds_hash = parse_joa_html(inner_html)
        if match_odds_hash:
            list_odds.append(match_odds_hash)
    return merge_dicts(list_odds)


def parse_netbet(url=""):
    """
    Retourne les cotes disponibles sur netbet
    """
    sport = None
    if url in ["football", "tennis", "basketball", "hockey-glace", "rugby", "handball"]:
        sport = url
        url = "https://www.netbet.fr/top-paris"
    if not url:
        url = "https://www.netbet.fr/football/france/96-ligue-1-conforama"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
    for _ in range(3):
        try:
            request = urllib.request.Request(url, None, headers)
            response = urllib.request.urlopen(request, timeout=5)
            soup = BeautifulSoup(response, features="lxml")
            break
        except http.client.IncompleteRead:
            headers = {"User-Agent": fake_useragent.UserAgent().random}
            print("User agent change")
        except urllib.error.HTTPError:
            headers = {"User-Agent": fake_useragent.UserAgent().random}
            print("User agent change (403)")
        except urllib.error.URLError:
            headers = {"User-Agent": fake_useragent.UserAgent().random}
            print("User agent change (Timeout)")
    else:
        raise sportsbetting.UnavailableSiteException
    if soup.find(attrs={"class": "none"}):
        raise sportsbetting.UnavailableCompetitionException
    if response.geturl() == "https://www.netbet.fr/":
        raise sportsbetting.UnavailableCompetitionException
    match_odds_hash = {}
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    date = ""
    year = " " + str(today.year)
    match = ""
    date_time = None
    valid_match = True
    for line in soup.find_all():
        if sport and "class" in line.attrs and "nb-link-event" in line["class"] and "href" in line.attrs:
            valid_match = sport+"/" in line["href"]
        if "class" in line.attrs and "nb-event_datestart" in line["class"]:
            date = list(line.stripped_strings)[0] + year
            if "Auj." in date:
                date = datetime.datetime.today().strftime("%d/%m %Y")
        elif "class" in line.attrs and "nb-event_timestart" in line["class"]:
            hour = line.text
            try:
                date_time = datetime.datetime.strptime(
                    date + " " + hour, "%d/%m %Y %H:%M")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year + 1)
            except ValueError:
                date_time = "undefined"
        elif "class" in line.attrs and "nb-event_actors" in line["class"]:
            match = " - ".join(list(map(lambda x: x.replace(" - ",
                                                            "-"), line.stripped_strings)))
            reg_exp = r'\[[0-7]\/[0-7]\s?([0-7]\/[0-7]\s?)*\]|\[[0-7]\-[0-7]\s?([0-7]\-[0-7]\s?)*\]'
            if list(re.finditer(reg_exp, match)):  # match tennis live
                match = match.split("[")[0].strip()
        elif "class" in line.attrs and "nb-event_odds_wrapper" in line["class"]:
            try:
                odds = list(map(lambda x: float(x.replace(",", ".")),
                                list(line.stripped_strings)[1::2]))
                if valid_match and match and match not in match_odds_hash:
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"netbet": odds}
                    if not date_time:
                        date_time = "undefined"
                    match_odds_hash[match]['date'] = date_time
            except ValueError:  # match live (cotes non disponibles)
                pass
    return match_odds_hash


def parse_parionssport(url=""):
    """
    Retourne les cotes disponibles sur ParionsSport
    """
    if not url:
        url = "https://www.enligne.parionssport.fdj.fr/paris-football/france/ligue-1-conforama"
    is_sport_page = "paris-" in url.split("/")[-1] and "?" not in url
    is_basket = False  # "basket" in url
    selenium_init.DRIVER["parionssport"].get(url)
    if "maintenance technique" in selenium_init.DRIVER["parionssport"].execute_script(
            "return document.body.innerHTML"):
        raise sportsbetting.UnavailableSiteException
    if (selenium_init.DRIVER["parionssport"].current_url
            == "https://www.enligne.parionssport.fdj.fr/"):
        raise sportsbetting.UnavailableSiteException
    elif (not is_sport_page) and selenium_init.DRIVER["parionssport"].current_url == "/".join(url.split("?")[0].split("/")[:4]):
        raise sportsbetting.UnavailableCompetitionException
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
                    raise sportsbetting.UnavailableCompetitionException
                if "class" in line.attrs and "wpsel-titleRubric" in line["class"]:
                    if line.text.strip() == "Aujourd'hui":
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
                if "class" in line.attrs and "buttonLine" in line["class"]:
                    try:
                        odds = list(map(lambda x: float(x.replace(",", ".")),
                                        list(line.stripped_strings)))
                        match_odds_hash[match] = {}
                        match_odds_hash[match]['odds'] = {"parionssport": odds}
                        match_odds_hash[match]['date'] = date_time
                    except ValueError:  # Live
                        pass
        if match_odds_hash:
            return match_odds_hash
        elif urls_basket:
            list_odds = []
            for match_url in urls_basket:
                if sportsbetting.ABORT:
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


def parse_pasinobet(url):
    """
    Retourne les cotes disponibles sur pasinobet
    """
    selenium_init.DRIVER["pasinobet"].get("about:blank")
    selenium_init.DRIVER["pasinobet"].get(url)
    match_odds_hash = {}
    match = None
    date_time = None
    WebDriverWait(selenium_init.DRIVER["pasinobet"], 15).until(
        EC.invisibility_of_element_located(
            (By.CLASS_NAME, "skeleton-line")) or sportsbetting.ABORT
    )
    if sportsbetting.ABORT:
        raise sportsbetting.AbortException
    inner_html = selenium_init.DRIVER["pasinobet"].execute_script(
        "return document.body.innerHTML")
    soup = BeautifulSoup(inner_html, features="lxml")
    date = ""
    for line in soup.findAll():
        if sportsbetting.ABORT:
            raise sportsbetting.AbortException
        if "class" in line.attrs and "category-date" in line["class"]:
            date = line.text.lower()
            date = date.replace("nov", "novembre")
            date = date.replace("déc", "décembre")
        if "class" in line.attrs and "event-title" in line["class"]:
            match = " - ".join(map(lambda x: list(x.stripped_strings)[0],
                                   line.findChildren("div", {"class": "teams-container"})))
        if "class" in line.attrs and "time" in line["class"]:
            try:
                date_time = datetime.datetime.strptime(
                    date+line.text.strip(), "%A, %d %B %Y%H:%M")
            except ValueError:
                date_time = "undefined"
        if "class" in line.attrs and "event-list" in line["class"]:
            if "---" not in list(line.stripped_strings):
                odds = list(map(float, line.stripped_strings))
                match_odds_hash[match] = {}
                match_odds_hash[match]["date"] = date_time
                match_odds_hash[match]["odds"] = {"pasinobet": odds}
    return match_odds_hash


def parse_pasinobet_sport(sport):
    selenium_init.start_selenium("pasinobet", False)
    selenium_init.DRIVER["pasinobet"].maximize_window()
    selenium_init.DRIVER["pasinobet"].get(
        "https://www.pasinobet.fr/#/sport/?type=0&sport=1&region=-1")
    sport_items = WebDriverWait(selenium_init.DRIVER["pasinobet"], 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "sport-header"))
    )
    for sport_item in sport_items:
        if sport_item.text.split() and sport_item.text.split()[0] == sport:
            sport_item.find_element_by_xpath("..").click()
            break
    regions = WebDriverWait(selenium_init.DRIVER["pasinobet"], 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "region"))
    )
    input()
    selenium_init.DRIVER["pasinobet"].quit()


def parse_pmu(url=""):
    """
    Retourne les cotes disponibles sur pmu
    """
    if "http" not in url:
        return parse_sport_pmu(url)
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    return parse_pmu_html(soup)


def parse_pmu_html(soup):
    match_odds_hash = {}
    match = ""
    date_time = "undefined"
    live = False
    handicap = False
    date = ""
    for line in soup.find_all():
        if "n'est pas accessible pour le moment !" in line.text:
            raise sportsbetting.UnavailableSiteException
        if "data-date" in line.attrs and "shadow" in line["class"]:
            date = line["data-date"]
        elif "class" in line.attrs and "trow--live--remaining-time" in line["class"]:
            hour = line.text
            try:
                date_time = datetime.datetime.strptime(
                    date + " " + hour, "%Y-%m-%d %Hh%M")
            except ValueError:
                date_time = "undefined"
        elif "class" in line.attrs and "trow--event--name" in line["class"]:
            string = "".join(list(line.stripped_strings))
            if "//" in string:
                live = line.find_parent(
                    "a")["data-name"] == "sportif.clic.paris_live.details"
                is_rugby_13 = line.find_parent(
                    "a")["data-sport_id"] == "rugby_a_xiii"
                if not (live or is_rugby_13):
                    handicap = False
                    if "+" in string or "Egalité" in string:
                        handicap = True
                        match, odds = parse_page_match_pmu("https://paris-sportifs.pmu.fr"
                                                           + line.parent["href"])
                    else:
                        match = string.replace(" - ", "-")
                        match = match.replace("//", "-")
        elif "class" in line.attrs and "event-list-odds-list" in line["class"]:
            if not live:
                if not handicap:
                    odds = list(
                        map(lambda x: float(x.replace(",", ".")), list(line.stripped_strings)))
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {"pmu": odds}
                match_odds_hash[match]['date'] = date_time
    if not match_odds_hash:
        raise sportsbetting.UnavailableCompetitionException
    return match_odds_hash


def parse_page_match_pmu(url):
    """
    Retourne les cotes d'une page de match sur pmu
    """
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    _id = "-1"
    odds = []
    name = soup.find("title").text.split(" - ")[0].replace("//", "-")
    print("\t" + name)
    for line in soup.find_all(["option", "a"]):
        if line.text in ["Vainqueur du match", "1N2 à la 60e minute"]:
            _id = line["data-market-id"]
        if "data-ev_mkt_id" in line.attrs and line["data-ev_mkt_id"] == _id:
            odds.append(float(line.text.replace(",", ".")))
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
        except sportsbetting.UnavailableCompetitionException:
            break
    return merge_dicts(list_odds)


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
            (By.CLASS_NAME, "ui-spinner")) or sportsbetting.ABORT
    )
    if sportsbetting.ABORT:
        raise sportsbetting.AbortException
    if is_sport_page:
        scroll(selenium_init.DRIVER["unibet"], "unibet", "calendar-event", 1)
    for _ in range(10):
        inner_html = selenium_init.DRIVER["unibet"].execute_script(
            "return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        if any(x in str(soup) for x in ["La page à laquelle vous souhaitez accéder n'existe plus.", "Aucun marché trouvé."]):
            raise sportsbetting.UnavailableCompetitionException
        for line in soup.findAll():
            if "class" in line.attrs and "cell-event" in line["class"]:
                match = line.text.strip().replace("Bordeaux - Bègles", "Bordeaux-Bègles")
                match = match.replace(
                    "Flensburg - Handewitt", "Flensburg-Handewitt")
                match = match.replace(
                    "TSV Hannovre - Burgdorf", "TSV Hannovre-Burgdorf")
                match = match.replace(
                    "Tremblay - en - France", "Tremblay-en-France")
                match = match.replace("FC Vion Zlate Moravce - Vrable",
                                      "FC Vion Zlate Moravce-Vrable")
                match = match.replace(
                    "Toulon St - Cyr Var (F)", "Toulon St-Cyr Var (F)")
                match = match.replace("Châlons - Reims", "Châlons-Reims")
                match = match.replace("Colo - Colo", "Colo-Colo")
                match = match.replace("Bourg - en - Bresse", "Bourg-en-Bresse")
                match = match.replace("Grande - Bretagne", "Grande-Bretagne")
                match = match.replace("Rostov - Don (F)", "Rostov-Don (F)")
                match = match.replace("CS Hammam - Lif", "CS Hammam-Lif")
                if match.count(" - ") > 1:
                    if not sportsbetting.TEST:
                        print(match)
                        match = input("Réentrez le nom du match :")
                if "-" not in match:
                    break
                reg_exp = r'\(\s?[0-7]-[0-7]\s?(,\s?[0-7]-[0-7]\s?)*([1-9]*[0-9]\/[1-9]*[0-9])*\)|\([0-7]\-[0-7](\s[0-7]\-[0-7])*\)'
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
                odds = list(map(lambda x: float(x.text),
                                list(line.findChildren("span", {"class": "price"}))))
                if match:
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"unibet": odds}
                    match_odds_hash[match]['date'] = date_time
                    match = None
        if match_odds_hash:
            return match_odds_hash
    return match_odds_hash


def parse_winamax(url=""):
    """
    Retourne les cotes disponibles sur winamax
    """
    if not url:
        url = "https://www.winamax.fr/paris-sportifs/sports/1/7/4"
    ids = url.split("/sports/")[1]
    try:
        tournament_id = int(ids.split("/")[2])
    except IndexError:
        tournament_id = -1
    sport_id = int(ids.split("/")[0])
    try:
        req = urllib.request.Request(
            url, headers={'User-Agent': sportsbetting.USER_AGENT})
        webpage = urllib.request.urlopen(req, timeout=10).read()
        soup = BeautifulSoup(webpage, features="lxml")
    except urllib.error.HTTPError:
        raise sportsbetting.UnavailableSiteException
    match_odds_hash = {}
    for line in soup.find_all(['script']):
        if "PRELOADED_STATE" in str(line.string):
            json_text = (line.string.split("var PRELOADED_STATE = ")[1]
                         .split(";var BETTING_CONFIGURATION")[0])
            if json_text[-1] == ";":
                json_text = json_text[:-1]
            dict_matches = json.loads(json_text)
            if "matches" in dict_matches:
                for match in dict_matches["matches"].values():
                    if (tournament_id in (match['tournamentId'], -1) and match["competitor1Id"] != 0
                            and match['sportId'] == sport_id):
                        try:
                            match_name = match["title"].strip().replace("  ", " ")
                            if "-" not in match_name or "Compétition" in match_name:
                                continue
                            date_time = datetime.datetime.fromtimestamp(
                                match["matchStart"])
                            main_bet_id = match["mainBetId"]
                            odds_ids = dict_matches["bets"][str(
                                main_bet_id)]["outcomes"]
                            odds = [dict_matches["odds"]
                                    [str(x)] for x in odds_ids]
                            match_odds_hash[match_name] = {}
                            match_odds_hash[match_name]['odds'] = {
                                "winamax": odds}
                            match_odds_hash[match_name]['date'] = date_time
                        except KeyError:
                            pass
            if not match_odds_hash:
                raise sportsbetting.UnavailableCompetitionException
            return match_odds_hash
    raise sportsbetting.UnavailableSiteException


def parse_zebet(url=""):
    """
    Retourne les cotes disponibles sur zebet
    """
    if not url:
        url = "https://www.zebet.fr/fr/competition/96-ligue_1_conforama"
    if "/sport/" in url:
        return parse_sport_zebet(url)
    try:
        soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    except urllib.error.URLError:
        raise sportsbetting.UnavailableCompetitionException
    match_odds_hash = {}
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = str(today.year) + "/"
    date_time = None
    for line in soup.find_all():
        if "Zebet rencontre actuellement des difficultés techniques." in line.text:
            raise sportsbetting.UnavailableSiteException
        if "class" in line.attrs and "bet-time" in line["class"]:
            try:
                date_time = datetime.datetime.strptime(year + " ".join(line.text.strip().split()),
                                                       "%Y/%d/%m %H:%M")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year + 1)
            except ValueError:
                date_time = "undefined"
        elif "class" in line.attrs and "competition" in line["class"]:
            strings = list(line.stripped_strings)
            match = (strings[1] + " - " + strings[-3])
            odds = []
            for i, val in enumerate(strings):
                if not i % 4:
                    odds.append(float(val.replace(",", ".")))
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"zebet": odds}
            match_odds_hash[match]['date'] = date_time
    return match_odds_hash


def parse_sport_zebet(url):
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = str(today.year) + "/"
    date_time = None
    for line in soup.find_all():
        if "Zebet rencontre actuellement des difficultés techniques." in line.text:
            raise sportsbetting.UnavailableSiteException
        if "class" in line.attrs and "bet-event" in line["class"]:
            match = format_zebet_names(line.text.strip())
        if "class" in line.attrs and "bet-time" in line["class"]:
            try:
                date_time = datetime.datetime.strptime(year + " ".join(line.text.strip().split()),
                                                       "%Y/%d/%m %H:%M")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year + 1)
            except ValueError:
                date_time = "undefined"
        if "class" in line.attrs and "pari-1" in line["class"]:
            odds = list(map(lambda x: float(x.replace(",", ".")),
                            list(line.stripped_strings)[1::2]))
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"zebet": odds}
            match_odds_hash[match]['date'] = date_time
    return match_odds_hash


def parse(site, url=""):
    """
    Retourne les cotes d'un site donné
    """
    parse_functions = {
        "betclic" : parse_betclic,
        "betstars" : parse_betstars,
        "bwin" : parse_bwin,
        "france_pari" : parse_france_pari,
        "joa" : parse_joa,
        "netbet" : parse_netbet,
        "parionssport" : parse_parionssport,
        "pasinobet" : parse_pasinobet,
        "pmu" : parse_pmu,
        "unibet" : parse_unibet,
        "winamax" : parse_winamax,
        "zebet" : parse_zebet
    }
    return parse_functions[site](url)
