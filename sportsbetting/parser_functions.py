"""
Fonctions de parsing
"""

import sys
import locale
import urllib
import urllib.error
import urllib.request
import datetime
import json
import time
import re
from itertools import chain
import selenium
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sportsbetting
from sportsbetting import selenium_init
from sportsbetting.auxiliary_functions import merge_dicts, get_future_opponents
from sportsbetting.database_functions import (is_in_db, is_in_db_site, add_name_to_db,
                                              get_close_name, get_close_name2, get_id_by_site,
                                              get_id_by_opponent, get_double_team_tennis,
                                              get_close_name3)


if sys.platform == "win32":
    locale.setlocale(locale.LC_TIME, "fr")
else:
    locale.setlocale(locale.LC_TIME, "fr_FR.utf8")

def parse_betclic(url=""):
    """
    Retourne les cotes disponibles sur betclic
    """
    if url in ["tennis", "rugby-a-xv", "football", "basket-ball", "hockey-sur-glace", "handball"]:
        return parse_sport_betclic(url)
    if not url:
        url = "https://www.betclic.fr/football/ligue-1-conforama-e4"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    one_match_page = False
    for line in soup.find_all():
        if "Nous nous excusons pour cette interruption momentanée du site." in line.text:
            print("Betclic non accessible")
            return {}
        if "Vous allez être redirigé sur notre page calendrier dans 5 secondes" in line.text:
            raise sportsbetting.UnavailableCompetitionException
        if line.name == "time":
            date = line["datetime"]
        elif "class" in line.attrs and "hour" in line["class"]:
            hour = line.text
        elif "class" in line.attrs and "match-name" in line["class"]:
            match = list(line.stripped_strings)[0]
            date_time = datetime.datetime.strptime(date+" "+hour, "%Y-%m-%d %H:%M")
        elif "class" in line.attrs and "match-odds" in line["class"]:
            odds = list(map(lambda x: float(x.replace(",", ".").replace("---", "1")),
                            list(line.stripped_strings)))
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"betclic":odds}
            match_odds_hash[match]['date'] = date_time
        elif "class" in line.attrs and "section-header-left" in line["class"]:
            strings = list(line.stripped_strings)
            date_time = datetime.datetime.strptime(strings[0], "%A %d %B %Y - %H:%M")
            match = strings[1]
            one_match_page = True
        elif (one_match_page and "class" in line.attrs and "expand-selection-bet" in line["class"]
              and " - " in match):
            try:
                opponents = match.split(" - ")
                if opponents[0].isnumeric() or opponents[1].isnumeric():
                    break
                odds = list(map(lambda x: float(x.replace(",", ".")),
                                list(line.stripped_strings)[1::2]))
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {"betclic":odds}
                match_odds_hash[match]['date'] = date_time
            except ValueError:
                pass
            break
    return match_odds_hash

def parse_sport_betclic(sport):
    """
    Retourne les cotes disponibles sur betclic pour un sport donné
    """
    url = "https://www.betclic.fr"
    soup = BeautifulSoup(urllib.request.urlopen(url+"/sport/"), features="lxml")
    odds = []
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "/"+sport+"/" in line["href"]:
            if "https://" in line["href"]:
                link = line["href"]
            else:
                link = url+line["href"]
            if not("onclick" in line.attrs and "Paris sur la compétition" in line["onclick"]):
                odds.append(parse_betclic(link))
    return merge_dicts(odds)


def parse_betstars(url=""):
    """
    Retourne les cotes disponibles sur betstars
    """
    if url in ["tennis", "handball", "basketball", "soccer", "handball", "rugby_union", "ice_hockey"]:
        return parse_sport_betstars(url)
    if not url:
        url = "https://www.betstars.fr/#/soccer/competitions/2152298"
    selenium_init.DRIVER.get(url)
    match_odds_hash = {}
    match = ""
    odds = []
    is_12 = False
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = str(today.year)
    try:
        WebDriverWait(selenium_init.DRIVER, 15).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "match-time"))
        )
        inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.findAll():
            if "id" in line.attrs and "participants" in line["id"] and not is_12:
                match = " - ".join(list(map(lambda x:x.replace(" - ", "-"), line.stripped_strings)))
            if "class" in line.attrs and "afEvt__link" in line["class"]:
                is_12 = True
                match = list(line.stripped_strings)[0]
                if "@" in match:
                    teams = match.split(" @ ")
                    match = teams[1]+" - "+teams[0]
                odds = []
            if "class" in line.attrs and ("market-AB" in line["class"]
                                          or "market-BAML" in line["class"]):
                try:
                    odds.append(float(list(line.stripped_strings)[0]))
                except ValueError: #cote non disponible (OTB)
                    odds.append(1)
            if "class" in line.attrs and "match-time" in line["class"]:
                strings = list(line.stripped_strings)
                date = strings[0]+" "+year
                hour = strings[1]
                try:
                    date_time = datetime.datetime.strptime(date+" "+hour, "%d %b, %Y %H:%M")
                except ValueError:
                    date = datetime.datetime.today().strftime("%d %b %Y")
                    hour = strings[0]
                    date_time = datetime.datetime.strptime(date+" "+hour, "%d %b %Y %H:%M")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year+1)
                match = match.replace("  ", " ")
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {"betstars":odds}
                match_odds_hash[match]['date'] = date_time
            if "class" in line.attrs and "prices" in line["class"]:
                try:
                    odds = list(map(lambda x: float(x.replace(",", ".")),
                                    list(line.stripped_strings)))
                except ValueError:
                    odds = []
        if match_odds_hash:
            return match_odds_hash
    except selenium.common.exceptions.TimeoutException:
        inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
        if "Nous procédons à une mise à jour afin d'améliorer votre expérience." in inner_html:
            print("Betstars inaccessible")
            return dict()
    return match_odds_hash

def parse_sport_betstars(sport):
    """
    Retourne les cotes disponibles sur betstars pour un sport donné
    """
    selenium_init.DRIVER.get("https://www.betstars.fr/#/{}/competitions".format(sport))
    urls = []
    competitions = []
    for _ in range(100):
        inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
        if "Nous procédons à une mise à jour afin d'améliorer votre expérience." in inner_html:
            print("Betstars inaccessible")
            return dict()
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.findAll(["a"]):
            if ("href" in line.attrs and sport+"/competitions/" in line["href"]
                    and "data-leagueid" in line.attrs):
                url = "https://www.betstars.fr/"+line["href"]
                if url not in urls:
                    urls.append(url)
                    competitions.append(line.text.strip())
        if urls:
            break
    list_odds = []
    for url, competition in zip(urls, competitions):
        print("\t"+competition)
        try:
            odds = parse_betstars(url)
            list_odds.append(odds)
        except KeyboardInterrupt:
            pass
    return merge_dicts(list_odds)

def parse_bwin(url=""):
    """
    Retourne les cotes disponibles sur bwin
    """
    if not url:
        url = "https://sports.bwin.fr/fr/sports/football-4/paris-sportifs/france-16/ligue-1-4131"
    if url in ["europa", "ldc", "élim"]:
        return parse_bwin_coupes_europe(url)
    driver_bwin = selenium_init.DRIVER
    if "handball" in url:
        options = selenium.webdriver.ChromeOptions()
        prefs = {'profile.managed_default_content_settings.images':2, 'disk-cache-size': 4096}
        options.add_argument('log-level=3')
        options.add_experimental_option("prefs", prefs)
        driver_bwin = selenium.webdriver.Chrome("sportsbetting/resources/chromedriver", options=options)
    driver_bwin.get(url)
    match_odds_hash = {}
    is_1n2 = False
    match = ""
    n = 3
    is_hockey = "hockey" in url
    is_us = "nba" in url or "nhl" in url
    odds = []
    odds_unavailable = False
    WebDriverWait(driver_bwin, 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "participants-pair-game"))
    )
    inner_html = driver_bwin.execute_script("return document.body.innerHTML")
    soup = BeautifulSoup(inner_html, features="lxml")
    i = 0
    date_time = "undefined"
    for line in soup.findAll():
        if (is_hockey and "class" in line.attrs and "href" in line.attrs
                and "grid-event-wrapper" in line["class"]):
            odds = parse_bwin_hockey("https://sports.bwin.fr"+line["href"])
        if "class" in line.attrs and "participants-pair-game" in line["class"]:
            if (len(odds) == n and match and ("handball" in url or not odds_unavailable)
                    and not is_hockey):
                if is_us:
                    odds.reverse()
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {"bwin":odds}
                match_odds_hash[match]['date'] = date_time
            strings = list(line.stripped_strings)
            if "@" in strings and not is_us:
                return
            if len(strings) == 4:
                match = strings[0]+" ("+strings[1]+") - "+strings[2]+" ("+strings[3]+")"
            else:
                try:
                    match = strings[2]+" - "+strings[0] if is_us else " - ".join(strings)
                except IndexError:
                    match = strings[1]+" - "+strings[0] if is_us else " - ".join(strings)
            i = 0
            if is_hockey:
                print("\t"+match)
            else:
                odds = []
            odds_unavailable = False
        if "class" in line.attrs and "starting-time" in line["class"]:
            try:
                date_time = datetime.datetime.strptime(line.text, "%d/%m/%Y %H:%M")
            except ValueError:
                if "Demain" in line.text:
                    date = (datetime.datetime.today()
                            +datetime.timedelta(days=1)).strftime("%d %b %Y")
                    hour = line.text.split(" / ")[1]
                    date_time = datetime.datetime.strptime(date+" "+hour, "%d %b %Y %H:%M")
                elif "Aujourd'hui" in line.text:
                    date = datetime.datetime.today().strftime("%d %b %Y")
                    hour = line.text.split(" / ")[1]
                    date_time = datetime.datetime.strptime(date+" "+hour, "%d %b %Y %H:%M")
                elif "Commence dans" in line.text:
                    date_time = datetime.datetime.strptime(datetime.datetime.today()
                                                           .strftime("%d %b %Y %H:%M"),
                                                           "%d %b %Y %H:%M")
                    date_time += datetime.timedelta(minutes=int(line.text.split("dans ")[1]
                                                                .split("min")[0]))
                elif "Commence maintenant" in line.text:
                    date_time = datetime.datetime.strptime(datetime.datetime.today()
                                                           .strftime("%d %b %Y %H:%M"),
                                                           "%d %b %Y %H:%M")
                else:
                    print(match, line.text)
                    date_time = "undefined"
            if is_hockey:
                if is_us:
                    odds.reverse()
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {"bwin":odds}
                match_odds_hash[match]['date'] = date_time
        if "class" in line.attrs and "group-title" in line["class"] and not is_1n2:
            is_1n2 = (line.text == "Résultat 1 X 2")
        if "class" in line.attrs and "offline" in line["class"] and not is_hockey:
            odds_unavailable = True
        if "class" in line.attrs and "option-indicator" in line["class"] and not is_hockey:
            if is_1n2:
                n = 3
            else:
                n = 2
            if i < n:
                odds.append(float(line.text))
                i += 1
    if len(odds) == n and match and ("handball" in url or not odds_unavailable):
        if is_us:
            odds.reverse()
        match_odds_hash[match] = {}
        match_odds_hash[match]['odds'] = {"bwin":odds}
        match_odds_hash[match]['date'] = date_time
    if "handball" in url:
        driver_bwin.quit()
    return match_odds_hash


def parse_bwin_coupes_europe(coupe):
    """
    Retourne les cotes disponibles sur bwin en coupe d'Europe
    """
    base_url = "https://sports.bwin.fr/fr/sports/football-4/paris-sportifs/europe-7"
    selenium_init.DRIVER.get(base_url)
    urls = {}
    for _ in range(50):
        inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.findAll(["a"]):
            if ("href" in line.attrs and list(line.stripped_strings)
                    and coupe.lower() in list(line.stripped_strings)[0].lower()
                    and "groupe" in list(line.stripped_strings)[0].lower()
                    and "football" in line["href"]):
                urls[list(line.stripped_strings)[0]] = "https://sports.bwin.fr"+line["href"]
        if urls:
            break
    list_odds = []
    for name, url in urls.items():
        print(name)
        list_odds.append(parse_bwin(url))
    return merge_dicts(list_odds)

def parse_bwin_hockey(url):
    """
    Retourne les cotes 1N2 d'un match de hockey
    """
    selenium_init.DRIVER.get(url)
    WebDriverWait(selenium_init.DRIVER, 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "option-panel"))
    )
    inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
    soup = BeautifulSoup(inner_html, features="lxml")
    for line in soup.findAll():
        if "class" in line.attrs and "option-panel" in line["class"]:
            if "1X2 (temps réglementaire)" in line.text:
                return list(map(float, list(line.stripped_strings)[2::2]))

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
    year = " "+str(today.year)
    for line in soup.find_all():
        if "class" in line.attrs and "date" in line["class"]:
            date = line.text+year
        elif "class" in line.attrs and "odd-event-block" in line["class"]:
            strings = list(line.stripped_strings)
            if "snc-odds-date-lib" in line["class"]:
                hour = strings[0]
                try:
                    i = strings.index("/")
                    date_time = datetime.datetime.strptime(date+" "+hour, "%A %d %B %Y %H:%M")
                    if date_time < today:
                        date_time = date_time.replace(year=date_time.year+1)
                    match = " ".join(strings[1:i])+" - "+" ".join(strings[i+1:])
                    reg_exp = (r'\[[0-7]\/[0-7]\s?([0-7]\/[0-7]\s?)*\]'
                               r'|\[[0-7]\-[0-7]\s?([0-7]\-[0-7]\s?)*\]')
                    if list(re.finditer(reg_exp, match)): #match tennis live
                        match = match.split("[")[0].strip()
                except ValueError:
                    pass
            else:
                odds = []
                for i, val in enumerate(strings):
                    if i%2:
                        odds.append(float(val.replace(",", ".")))
                try:
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"france_pari":odds}
                    match_odds_hash[match]['date'] = date_time
                except UnboundLocalError:
                    pass
    return match_odds_hash

def parse_joa(url):
    """
    Retourne les cotes disponibles sur joa
    """
    if "http" not in url:
        return parse_sport_joa(url)
    if not url:
        url = "https://www.joa-online.fr/fr/sport/paris-sportifs/844/54287323"
    selenium_init.DRIVER.get(url)
    match_odds_hash = {}
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = str(today.year)
    date_time = ""
    odds_class = ""
    for _ in range(10):
        WebDriverWait(selenium_init.DRIVER, 15).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "bet-event-name"))
        )
        inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.find_all():
            if "class" in line.attrs and "bet-event-name" in line["class"]:
                match = " - ".join(line.stripped_strings)
                match = match.replace("Nouvelle - Zélande Breakers", "Nouvelle-Zélande Breakers")
            elif "class" in line.attrs and "bet-outcomes-caption-list" in line["class"]:
                if (["1", "2"] == list(line.stripped_strings)
                        or ["1", "X", "2"] == list(line.stripped_strings)):
                    odds_class = line.attrs["class"][-1]
            elif ("class" in line.attrs
                    and "bet-outcome-list" in line["class"]
                    and odds_class in line["class"]):
                odds = []
                for odd in line.stripped_strings:
                    odds.append(float(odd.replace("-", "1")))
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {"joa":odds}
                match_odds_hash[match]['date'] = date_time
            elif "class" in line.attrs and "bet-event-date-col" in line["class"]:
                strings = list(line.stripped_strings)
                if strings[0] == "Demain":
                    date = (datetime.datetime.today()
                            +datetime.timedelta(days=1)).strftime("%d %b %Y")
                    hour = strings[1]
                    date_time = datetime.datetime.strptime(date+" "+hour, "%d %b %Y %H:%M")
                elif strings[0] == "Aujourd'hui":
                    date = datetime.datetime.today().strftime("%d %b %Y")
                    hour = strings[1]
                    date_time = datetime.datetime.strptime(date+" "+hour, "%d %b %Y %H:%M")
                else:
                    date = strings[0]+"/"+year
                    hour = strings[1]
                    try:
                        date_time = datetime.datetime.strptime(date+" "+hour, "%d/%m/%Y %H:%M")
                    except ValueError:
                        date = datetime.datetime.today().strftime("%d/%m/%Y")
                        hour = strings[0]
                        date_time = datetime.datetime.strptime(date+" "+hour, "%d/%m/%Y %H:%M")
                    if date_time < today:
                        date_time = date_time.replace(year=date_time.year+1)
        selenium_init.DRIVER.get("about:blank")
        return match_odds_hash
    selenium_init.DRIVER.get("about:blank")

    

def parse_netbet(url=""):
    """
    Retourne les cotes disponibles sur netbet
    """
    if "http" not in url:
        return parse_sport_netbet(url)
    if not url:
        url = "https://www.netbet.fr/football/france/96-ligue-1-conforama"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    date = ""
    year = " "+str(today.year)
    for line in soup.find_all():
        if "class" in line.attrs and "nb-date-large" in line["class"]:
            date = list(line.stripped_strings)[0]+year
            if "Aujourd'hui" in date:
                date = datetime.datetime.today().strftime("%A %d %B %Y")
        elif "class" in line.attrs and "time" in line["class"]:
            hour = line.text
            try:
                date_time = datetime.datetime.strptime(date+" "+hour, "%A %d %B %Y %H:%M")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year+1)
            except ValueError:
                date_time = "undefined"
        elif "class" in line.attrs and "bet-libEvent" in line["class"]:
            match = list(line.stripped_strings)[0].replace("/", "-")
            reg_exp = r'\[[0-7]\/[0-7]\s?([0-7]\/[0-7]\s?)*\]|\[[0-7]\-[0-7]\s?([0-7]\-[0-7]\s?)*\]'
            if list(re.finditer(reg_exp, match)): #match tennis live
                match = match.split("[")[0].strip()
        elif ("class" in line.attrs and "mainOdds" in line["class"]
              and "uk-margin-remove" in line["class"]):
            try:
                odds = list(map(lambda x: float(x.replace(",", ".")), list(line.stripped_strings)))
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {"netbet":odds}
                match_odds_hash[match]['date'] = date_time
            except ValueError: #match live (cotes non disponibles)
                pass
    return match_odds_hash


def parse_sport_netbet(sport):
    url = "https://www.netbet.fr"
    odds = []
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    for line in soup.find_all("a", {"data-type-event":"sport"}):
        if sport == line.text.lower():
            print(line.text)
            for child in line.findParent().findChildren("a", {"data-type-event":"competition"}):
                link = url+child["href"]
                odds.append(parse_netbet(link))
    return merge_dicts(odds)


def parse_parionssport(url=""):
    """
    Retourne les cotes disponibles sur ParionsSport
    """
    if not url:
        url = "https://www.enligne.parionssport.fdj.fr/paris-football/france/ligue-1-conforama"
    selenium_init.DRIVER.get(url)
    match_odds_hash = {}
    if "basket" in url:
        return parse_parionssport_nba(url)
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = " "+str(today.year)
    for _ in range(10):
        inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.findAll():
            if "class" in line.attrs and "wpsel-titleRubric" in line["class"]:
                if line.text.strip() == "Aujourd'hui":
                    date = datetime.date.today().strftime("%A %d %B %Y")
                else:
                    date = line.text.strip().lower()+year
            if "class" in line.attrs and "wpsel-timerLabel" in line["class"]:
                try:
                    date_time = datetime.datetime.strptime(date+" "+line.text,
                                                           "%A %d %B %Y À %Hh%M")
                    if date_time < today:
                        date_time = date_time.replace(year=date_time.year+1)
                except ValueError:
                    date_time = "undefined"
            if "class" in line.attrs and "wpsel-desc" in line["class"]:
                match = line.text.strip()
            if "class" in line.attrs and "buttonLine" in line["class"]:
                try:
                    odds = list(map(lambda x: float(x.replace(",", ".")),
                                    list(line.stripped_strings)))
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"parionssport":odds}
                    match_odds_hash[match]['date'] = date_time
                except ValueError: #Live
                    pass
        if match_odds_hash:
            return match_odds_hash
    return match_odds_hash

def parse_parionssport_nba(url=""):
    """
    Recupere les cotes de NBA
    """
    if not url:
        url = "https://www.enligne.parionssport.fdj.fr/paris-basketball/usa/nba"
    selenium_init.DRIVER.get(url)
    urls = []
    for _ in range(10):
        inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.findAll(["a"]):
            if ("href" in line.attrs and list(line.stripped_strings)
                    and "+" in list(line.stripped_strings)[0]):
                urls.append("https://www.enligne.parionssport.fdj.fr"+line["href"])
        if urls:
            break
    list_odds = []
    for match_url in urls:
        try:
            list_odds.append(parse_match_nba_parionssport(match_url))
        except KeyboardInterrupt:
            break
    return merge_dicts(list_odds)

def parse_match_nba_parionssport(url):
    """
    Recupere les cotes d'un match de NBA
    """
    selenium_init.DRIVER.get(url)
    odds = []
    match_odds = {}
    date_time = "undefined"
    match = ""
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = " "+str(today.year)
    for _ in range(10):
        inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.findAll():
            if "class" in line.attrs and "header-banner-event-date-section" in line["class"]:
                date_time = datetime.datetime.strptime(list(line.stripped_strings)[0]+year,
                                                       "Le %d %B à %H:%M %Y")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year+1)
            elif "class" in line.attrs and "headband-eventLabel" in line["class"]:
                match = list(line.stripped_strings)[0]
                print("\t"+match)
            elif "class" in line.attrs and "wpsel-market-detail" in line["class"] and match:
                strings = list(line.stripped_strings)
                odds = list(map(lambda x: float(x.replace(",", ".")),
                                strings[2::2]))
                match_odds[match] = {"date":date_time, "odds":{"parionssport":odds}}
                return match_odds
    return match_odds

def parse_pasinobet(url=""):
    """
    Retourne les cotes disponibles sur pasinobet
    """
    if not url:
        url = "https://www.pasinobet.fr/#/sport/?type=0&competition=20896&sport=1&region=830001"
    if "http" not in url:
        return parse_pasinobet_sport(url)
    selenium_init.DRIVER.get(url)
    is_basketball = "sport=3" in url
    is_us = "region=5000" in url
    date = ""
    if is_basketball:
        all_odds = []
        links = []
        for _ in range(100):
            links = selenium_init.DRIVER.find_elements_by_class_name('team-name-tc')
            if links:
                break
        for match_link in links:
            match_link.click()
            time.sleep(0.8)
            inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
            soup = BeautifulSoup(inner_html, features="lxml")
            for line in soup.findAll():
                if "data-title" in line.attrs and "Vainqueur du match" in line["data-title"]:
                    odds = list(map(float, list(line.find_parent().stripped_strings)[1::2]))
                    all_odds.append(odds)
                    break
            else:
                all_odds.append([])
        iter_odds = iter(all_odds)
    match_odds_hash = {}
    for _ in range(100):
        inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.findAll():
            if ("class" in line.attrs and "game-events-view-v3" in line["class"]
                    and "vs" in line.text):
                strings = list(line.stripped_strings)
                date_time = datetime.datetime.strptime(date+" "+strings[0], "%d.%m.%y %H:%M")
                i = strings.index("vs")
                match = (strings[i+1]+" - "+strings[i-1] if is_us
                         else strings[i-1]+" - "+strings[i+1])
                odds = []
                next_odd = False
                for string in strings:
                    if string == "Max:":
                        next_odd = True
                    elif next_odd:
                        odds.append(float(string))
                        next_odd = False
                match_odds_hash[match] = {}
                if is_basketball:
                    try:
                        odds = next(iter_odds)
                    except StopIteration:
                        pass
                if is_us:
                    odds.reverse()
                match_odds_hash[match]['odds'] = {"pasinobet":odds}
                match_odds_hash[match]['date'] = date_time
            elif "class" in line.attrs and "time-title-view-v3" in line["class"]:
                date = line.text
        if match_odds_hash:
            selenium_init.DRIVER.get("about:blank")
            return match_odds_hash
    selenium_init.DRIVER.get("about:blank")
    return match_odds_hash

def parse_pasinobet_sport(sport):
    """
    Retourne les cotes disponibles sur pasinobet pour un sport donné
    """
    all_odds = []
    date = ""
    selenium_init.DRIVER.get("https://www.pasinobet.fr/#/sport/?type=0")
    WebDriverWait(selenium_init.DRIVER, 15).until(
        EC.element_to_be_clickable((By.TAG_NAME, "button"))
    )
    buttons = selenium_init.DRIVER.find_elements_by_tag_name("button")
    for button in buttons:
        try:
            if "ACCEPTER" in button.text:
                button.click()
                break
        except selenium.common.exceptions.StaleElementReferenceException:
            pass
    text_elements = []
    while "Football" not in text_elements:
        try:
            active_elements = selenium_init.DRIVER.find_elements_by_class_name("active")
            text_elements = [el.text.replace("\n", "") for el in active_elements]
            #utile pour vérifier que tout est bien stocké
        except selenium.common.exceptions.StaleElementReferenceException:
            pass
    for elem in active_elements:
        try:
            if elem.text:
                try:
                    if "Moins" not in elem.text:
                        elem.click()
                except selenium.common.exceptions.ElementClickInterceptedException:
                    pass
        except selenium.common.exceptions.StaleElementReferenceException:
            pass
    sports = selenium_init.DRIVER.find_elements_by_class_name("sports-item-v3")
    for sport_selected in sports:
        if sport.capitalize() == sport_selected.text.split("\n")[0]:
            try:
                sport_selected.click()
            except selenium.common.exceptions.ElementClickInterceptedException:
                pass
    regions = selenium_init.DRIVER.find_elements_by_class_name("region-item-v3")
    for region in regions:
        if region.text:
            try:
                region.click()
                competitions = WebDriverWait(selenium_init.DRIVER, 10).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "competition-title-v3"))
                )
                list_competitions = list(filter(None, [competition.text
                                                       for competition in competitions]))
                while len(list_competitions) == 0:
                    competitions = WebDriverWait(selenium_init.DRIVER, 10).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "competition-title-v3"))
                    )
                    list_competitions = list(filter(None, [competition.text
                                                           for competition in competitions]))
                for competition in competitions:
                    if competition.text and "Compétition" not in competition.text:
                        try:
                            competition.click()
                            print("\t"+competition.text.replace("\n", " "))
                            match_odds_hash = {}
                            for _ in range(10):
                                inner_html = (selenium_init.DRIVER
                                              .execute_script("return document.body.innerHTML"))
                                soup = BeautifulSoup(inner_html, features="lxml")
                                for line in soup.findAll():
                                    if ("class" in line.attrs
                                            and "game-events-view-v3" in line["class"]
                                            and "vs" in line.text):
                                        strings = list(line.stripped_strings)
                                        date_time = datetime.datetime.strptime(date+" "+strings[0],
                                                                               "%d.%m.%y %H:%M")
                                        i = strings.index("vs")
                                        match = strings[i-1]+" - "+strings[i+1]
                                        odds = []
                                        next_odd = False
                                        for string in strings:
                                            if string == "Max:":
                                                next_odd = True
                                            elif next_odd:
                                                odds.append(float(string))
                                                next_odd = False
                                        match_odds_hash[match] = {}
                                        match_odds_hash[match]['odds'] = {"pasinobet":odds}
                                        match_odds_hash[match]['date'] = date_time
                                    elif ("class" in line.attrs
                                          and "time-title-view-v3" in line["class"]):
                                        date = line.text
                                if match_odds_hash:
                                    break
                            all_odds.append(match_odds_hash)
                        except selenium.common.exceptions.ElementClickInterceptedException:
                            print("pas cliqué"+competition.text.replace("\n", " "))
                region.click()
            except selenium.common.exceptions.ElementClickInterceptedException:
                pass
    selenium_init.DRIVER.quit()
    return merge_dicts(all_odds)

def parse_pmu(url=""):
    """
    Retourne les cotes disponibles sur pmu
    """
    if "http" not in url:
        return parse_sport_pmu(url)
    if not url:
        url = "https://paris-sportifs.pmu.fr/pari/competition/169/football/ligue-1-conforama"
#     url = "https://paris-sportifs.pmu.fr/pari/competition/441/tennis/open-daustralie-h"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    match = ""
    date_time = "undefined"
    live = False
    handicap = False
    for line in soup.find_all():
        if "data-date" in line.attrs and "shadow" in line["class"]:
            date = line["data-date"]
        elif "class" in line.attrs and "trow--live--remaining-time" in line["class"]:
            hour = line.text
            try:
                date_time = datetime.datetime.strptime(date+" "+hour, "%Y-%m-%d %Hh%M")
            except ValueError:
                date_time = "undefined"
        elif "class" in line.attrs and "trow--event--name" in line["class"]:
            string = "".join(list(line.stripped_strings))
            try:
                if "//" in string:
                    live = line.find_parent("a")["data-name"] == "sportif.clic.paris_live.details"
                    if not live:
                        handicap = False
                        if "Egalité" in string:
                            handicap = True
                            match, odds = parse_page_match_pmu("https://paris-sportifs.pmu.fr"
                                                               +line.parent["href"])
                            match_odds_hash[match] = {}
                            match_odds_hash[match]['odds'] = {"pmu":odds}
                            match_odds_hash[match]['date'] = date_time
                        elif "hockey" in url:
                            handicap = True
                            odds = parse_page_match_pmu("https://paris-sportifs.pmu.fr"
                                                        +line.parent["href"])[1]
                            if "nhl" in url:
                                odds.reverse()
                            match = string.replace("//", "-")
                            match_odds_hash[match] = {}
                            match_odds_hash[match]['odds'] = {"pmu":odds}
                            match_odds_hash[match]['date'] = date_time
                        else:
                            match = string.replace(" - ", "-")
                            match = match.replace("//", "-")
            except TypeError:
                pass
        elif "class" in line.attrs and "event-list-odds-list" in line["class"] and not handicap:
            if not live:
                odds = list(map(lambda x: float(x.replace(",", ".")), list(line.stripped_strings)))
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {"pmu":odds}
                match_odds_hash[match]['date'] = date_time
    return match_odds_hash

def parse_page_match_pmu(url):
    """
    Retourne les cotes d'une page de match sur pmu
    """
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    _id = "-1"
    odds = []
    name = soup.find("title").text.split(" - ")[0].replace("//", "-")
    print("\t"+name)
    for line in soup.find_all(["option", "a"]):
        if line.text in ["Vainqueur du match", "1N2 à la 60e minute"]:
            _id = line["data-market-id"]
        if "data-ev_mkt_id" in line.attrs and line["data-ev_mkt_id"] == _id:
            odds.append(float(line.text.replace(",", ".")))
    return name, odds

def parse_sport_pmu(sport):
    url = "https://paris-sportifs.pmu.fr/pari/sport/25/football"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    odds = []
    links = []
    competitions = []
    for line in soup.find_all(["a"], {"class" : "tc-track-element-events"}):
        if "/"+sport+"/" in line["href"]:
            if "http" not in line["href"]:
                link = "https://paris-sportifs.pmu.fr"+line["href"]
            else:
                link = line["href"]
            if link not in links:
                links.append(link)
                competitions.append(line.text)
    for line, competition in zip(links, competitions):
        print("\t"+competition)
        odds.append(parse_pmu(line))
    return merge_dicts(odds)
    

def parse_unibet(url=""):
    """
    Retourne les cotes disponibles sur unibet
    """
    if "http" not in url:
        return parse_sport_unibet(url)
    if not url:
        url = "https://www.unibet.fr/sport/football/ligue-1-conforama"
    selenium_init.DRIVER.get(url)
    match_odds_hash = {}
    match = ""
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = str(today.year)+"/"
    for _ in range(10):
        inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
        for line in soup.findAll():
            if "class" in line.attrs and "cell-event" in line["class"]:
                match = line.text.strip().replace("Bordeaux - Bègles", "Bordeaux-Bègles")
                match = match.replace("Flensburg - Handewitt", "Flensburg-Handewitt")
                match = match.replace("TSV Hannovre - Burgdorf", "TSV Hannovre-Burgdorf")
                match = match.replace("Tremblay - en - France", "Tremblay-en-France")
                match = match.replace("FC Vion Zlate Moravce - Vrable",
                                      "FC Vion Zlate Moravce-Vrable")
                match = match.replace("Toulon St - Cyr Var (F)", "Toulon St-Cyr Var (F)")
                match = match.replace("Châlons - Reims", "Châlons-Reims")
                match = match.replace("Colo - Colo", "Colo-Colo")
                match = match.replace("Bourg - en - Bresse", "Bourg-en-Bresse")
                match = match.replace("Grande - Bretagne", "Grande-Bretagne")
                match = match.replace("Rostov - Don (F)", "Rostov-Don (F)")
                match = match.replace("CS Hammam - Lif", "CS Hammam-Lif")
                if match.count(" - ")>1:
                    print(match)
                    match = input("Réentrez le nom du match :")
                if "-" not in match:
                    break
                reg_exp = r'\(\s?[0-7]-[0-7]\s?(,\s?[0-7]-[0-7]\s?)*([1-9]*[0-9]\/[1-9]*[0-9])*\)'
                if list(re.finditer(reg_exp, match)): #match tennis live
                    match = match.split("(")[0].strip()
                    if " - " not in match:
                        match = match.replace("-", " - ")
            if "class" in line.attrs and "datetime" in line["class"]:
                date_time = datetime.datetime.strptime(year+line.text, "%Y/%d/%m %H:%M")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year+1)
            if "class" in line.attrs and "oddsbox" in line["class"]:
                odds = []
                for i, val in enumerate(list(line.stripped_strings)):
                    if i%4 == 2:
                        try:
                            odds.append(float(val))
                        except ValueError:
                            break
                if match:
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"unibet":odds}
                    match_odds_hash[match]['date'] = date_time
        if match_odds_hash:
            return match_odds_hash
    return match_odds_hash

def parse_sport_unibet(sport):
    selenium_init.DRIVER.get("https://www.unibet.fr/sport")
    urls = []
    competitions = []
    WebDriverWait(selenium_init.DRIVER, 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "sportsmenu"))
    )
    for elem in selenium_init.DRIVER.find_elements_by_class_name("SPORT_"+sport.replace("-15", "axv")
                                                                 .replace("-", "").upper()):
        if elem.tag_name == "li":
            elem.click()
    for _ in range(10):
        inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(inner_html, features="lxml")
#         for line in soup.findAll(["span"], {"class":"SPORT_FOOTBALL"}):
#             line.findParent().click()
#             print(list(line.stripped_strings))
        for line in soup.findAll(["a"], {"class":"linkaction"}):
            if "href" in line.attrs and "sport/"+sport+"/" in line["href"]:
                if "http" in line["href"]:
                    url = line["href"]
                else:
                    url = "https://www.unibet.fr"+line["href"]
                if url not in urls and "competition" not in url and "compétition" not in url and url.count("/")==6:
                    urls.append(url)
                    competition = url.split(sport+"/")[1].replace("-", " ").replace("matchs", "").replace("/", " ").title()
                    competitions.append(competition)
        if urls:
            break
    list_odds = []
    for url, competition in zip(urls, competitions):
        print("\t"+competition)
        try:
            odds = parse_unibet(url)
            list_odds.append(odds)
        except KeyboardInterrupt:
            pass
    return merge_dicts(list_odds)
    


def parse_winamax(url=""):
    """
    Retourne les cotes disponibles sur winamax
    """
    if "http" not in url:
        return parse_sport_winamax(url)
    if not url:
        url = "https://www.winamax.fr/paris-sportifs/sports/1/7/4"
    ids = url.split("/sports/")[1]
    try:
        tournament_id = int(ids.split("/")[2])
    except IndexError:
        tournament_id = -1
    sport_id = int(ids.split("/")[0])
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    for line in soup.find_all(['script']):
        if "PRELOADED_STATE" in line.text:
            json_text = (line.text.split("var PRELOADED_STATE = ")[1]
                         .split(";var BETTING_CONFIGURATION")[0])
            dict_matches = json.loads(json_text)
            for match in dict_matches["matches"].values():
                if (tournament_id in (match['tournamentId'], -1) and match["competitor1Id"] != 0
                        and match['sportId'] == sport_id):
                    try:
                        match_name = match["title"]
                        date_time = datetime.datetime.fromtimestamp(match["matchStart"])
                        main_bet_id = match["mainBetId"]
                        odds_ids = dict_matches["bets"][str(main_bet_id)]["outcomes"]
                        odds = [dict_matches["odds"][str(x)] for x in odds_ids]
                        match_odds_hash[match_name] = {}
                        match_odds_hash[match_name]['odds'] = {"winamax":odds}
                        match_odds_hash[match_name]['date'] = date_time
                    except KeyError:
                        pass
            return match_odds_hash
    print("Winamax non accessible")
    return {}


def parse_sport_winamax(sport):
    url = "https://www.winamax.fr/paris-sportifs/sports/"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    urls = []
    competitions = []
    list_odds = []
    for line in soup.find_all(['script']):
        if "PRELOADED_STATE" in line.text:
            json_text = (line.text.split("var PRELOADED_STATE = ")[1]
                         .split(";var BETTING_CONFIGURATION")[0])
            dict_data = json.loads(json_text)
            for id_sport in dict_data["sports"]:
                if dict_data["sports"][id_sport]["sportName"] == sport.capitalize():
                    break
            categories = dict_data["sports"][id_sport]["categories"]
            for id_category in categories:
                tournaments = dict_data["categories"][str(id_category)]["tournaments"]
                category_name = dict_data["categories"][str(id_category)]["categoryName"]
                for id_tournament in tournaments:
                    url = "https://www.winamax.fr/paris-sportifs/sports/{}/{}/{}".format(id_sport,
                                                                                         id_category,
                                                                                         id_tournament)
                    urls.append(url)
                    tournament_name = dict_data["tournaments"][str(id_tournament)]["tournamentName"]
                    competition = category_name+" - "+tournament_name
                    competitions.append(competition)
                    print("\t"+competition)
                    try:
                        odds = parse_winamax(url)
                        list_odds.append(odds)
                    except urllib.error.HTTPError:
                        print("forbidden")
                        pass
#     list_odds = []
#     for url, competition in zip(urls, competitions):
#         print("\t"+competition)
#         if "Norvège" in competition:
#             pass
#         try:
#             odds = parse_winamax(url)
#             list_odds.append(odds)
#         except KeyboardInterrupt:
#             pass
    return merge_dicts(list_odds)


def parse_zebet(url=""):
    """
    Retourne les cotes disponibles sur zebet
    """
    if not url:
        url = "https://www.zebet.fr/fr/competition/96-ligue_1_conforama"
    if "http" not in url:
        return parse_sport_zebet(url)
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    year = str(today.year)+"/"
    for line in soup.find_all():
        if "class" in line.attrs and "bet-time" in line["class"]:
            try:
                date_time = datetime.datetime.strptime(year+" ".join(line.text.strip().split()),
                                                       "%Y/%d/%m %H:%M")
                if date_time < today:
                    date_time = date_time.replace(year=date_time.year+1)
            except ValueError:
                date_time = "undefined"
        elif "class" in line.attrs and "competition" in line["class"]:
            strings = list(line.stripped_strings)
            match = (strings[1]+" - "+strings[-3])
            odds = []
            for i, val in enumerate(strings):
                if not i%4:
                    odds.append(float(val.replace(",", ".")))
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"zebet":odds}
            match_odds_hash[match]['date'] = date_time
    return match_odds_hash

def parse_sport_zebet(sport):
    """
    Retourne les cotes disponibles sur zebet pour un sport donné
    """
    url = "https://www.zebet.fr/"
    odds = []
    soup = BeautifulSoup(urllib.request.urlopen(url+"fr/"), features="lxml")
    for line in soup.find_all():
        if ("class" in line.attrs and "menu-sport-cat" in line["class"]
                and sport in list(line.stripped_strings)[0].lower()):
            for child in line.findChildren():
                if ("href" in child.attrs and "fr/category/" in child["href"]
                        and "uk-visible-small" in child["class"]):
                    link = url+child["href"][2:]
                    odds.append(parse_zebet(link))
    return merge_dicts(odds)

def parse(site, url=""):
    """
    Retourne les cotes d'un site donné
    """
    return eval("parse_{}('{}')".format(site, url))

def parse_and_add_to_db(site, sport, competition):
    """
    Ajoute à la base de données les noms d'équipe/joueur pour une competition donnée et un site
    donné
    """
    if any(sub in competition for sub in ["http", "tennis", "europa", "ldc", "élim", "handball",
                                          "basketball", "soccer", "handball", "rugby_union",
                                          "ice_hockey", "rugby-a-xv", "football", "basket-ball",
                                          "hockey-sur-glace", "hockey/glace", "rugby",
                                          "hockey sur glace", "rugbyaxv"]):
        url = competition
    else:
        return
    odds = parse(site, url)
    if site == "france_pari":
        site = "netbet"
    matches = odds.keys()
    teams = list(set(chain.from_iterable(list(map(lambda x: x.split(" - "), list(matches))))))
    teams = list(map(lambda x: x.strip(), teams))
    print(teams)
    teams_not_in_db_site = []
    teams_1st_round = []
    teams_2nd_round = []
    teams_3rd_round = []
    teams_4th_round = []
    teams_5th_round = []
    teams_6th_round = []
    teams_7th_round = []
    teams_8th_round = []
    teams_9th_round = []
    for team in teams:
        line = is_in_db_site(team, sport, site)
        if not line:
            teams_not_in_db_site.append(team)
    print(0, teams_not_in_db_site)
    for team in teams_not_in_db_site:
        line = is_in_db(team, sport, site)
        if line:
            success = add_name_to_db(line[0], team, site)
            if not success:
                teams_1st_round.append(team)
        else:
            teams_1st_round.append(team)
    print(1, teams_1st_round)
    for team in teams_1st_round:
        line = get_close_name(team, sport, site)
        if line:
            success = add_name_to_db(line[0], team, site)
            if not success:
                teams_2nd_round.append(team)
        else:
            teams_2nd_round.append(team)
    print(2, teams_2nd_round)
    for team in teams_2nd_round:
        future_opponents, future_matches = get_future_opponents(team, matches)
        found = False
        for future_opponent, future_match in zip(future_opponents, future_matches):
            id_opponent = get_id_by_site(future_opponent, sport, site)
            id_to_find = get_id_by_opponent(id_opponent, future_match, odds)
            if id_to_find:
                found = True
                success = add_name_to_db(id_to_find, team, site)
                if not success:
                    teams_3rd_round.append(team)
        if not found:
            teams_3rd_round.append(team)
    print(3, teams_3rd_round)
    for team in teams_3rd_round:
        line = get_close_name2(team, sport, site)
        if line:
            success = add_name_to_db(line[0], team, site)
            if not success:
                teams_4th_round.append(team)
        else:
            teams_4th_round.append(team)
    print(4, teams_4th_round)
    for team in teams_4th_round:
        future_opponents, future_matches = get_future_opponents(team, matches)
        found = False
        for future_opponent, future_match in zip(future_opponents, future_matches):
            id_opponent = get_id_by_site(future_opponent, sport, site)
            id_to_find = get_id_by_opponent(id_opponent, future_match, odds)
            if id_to_find:
                found = True
                success = add_name_to_db(id_to_find, team, site)
                if not success:
                    teams_5th_round.append(team)
        if not found:
            teams_5th_round.append(team)
    print(5, teams_5th_round)
    if sport == "tennis":
        for team in teams_5th_round:
            line = get_close_name3(team, sport, site)
            if line:
                success = add_name_to_db(line[0], team, site)
                if not success:
                    teams_6th_round.append(team)
            else:
                teams_6th_round.append(team)
        print(6, teams_6th_round)
        for team in teams_6th_round:
            future_opponents, future_matches = get_future_opponents(team, matches)
            found = False
            for future_opponent, future_match in zip(future_opponents, future_matches):
                id_opponent = get_id_by_site(future_opponent, sport, site)
                id_to_find = get_id_by_opponent(id_opponent, future_match, odds)
                if id_to_find:
                    found = True
                    success = add_name_to_db(id_to_find, team, site)
                    if not success:
                        teams_7th_round.append(team)
            if not found:
                teams_7th_round.append(team)
        print(7, teams_7th_round)
        for team in teams_7th_round:
            line = get_double_team_tennis(team, site)
            if line:
                success = add_name_to_db(line[0], team, site)
                if not success:
                    teams_8th_round.append(team)
            else:
                teams_8th_round.append(team)
        print(8, teams_8th_round)
        for team in teams_8th_round:
            future_opponents, future_matches = get_future_opponents(team, matches)
            found = False
            for future_opponent, future_match in zip(future_opponents, future_matches):
                id_opponent = get_id_by_site(future_opponent, sport, site)
                id_to_find = get_id_by_opponent(id_opponent, future_match, odds)
                if id_to_find:
                    success = add_name_to_db(id_to_find, team, site)
                    if not success:
                        teams_9th_round.append(team)
            if not found:
                teams_9th_round.append(team)
        print(9, teams_9th_round)
    if teams_5th_round:
        return site, sport, competition, teams_5th_round

def parse_buteurs_betclic(url):
    """
    Stocke les cotes des duels de buteurs disponibles sur Betclic
    """
    options = selenium.webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images':2, 'disk-cache-size': 4096}
    options.add_argument('log-level=3')
    options.add_experimental_option("prefs", prefs)
    driver = selenium.webdriver.Chrome("sportsbetting/resources/chromedriver", options=options)
    driver.maximize_window()
    match_odds_hash = {}
    driver.get(url)
    inner_html = driver.execute_script("return document.body.innerHTML")
    categories = driver.find_elements_by_class_name("marketTypeCodeName")
    for cat in categories:
        if "Qui marquera le plus" in cat.text or "Duel de buteurs" in cat.text:
            cat.click()
            inner_html = driver.execute_script("return document.body.innerHTML")
            soup = BeautifulSoup(inner_html, features="lxml")
            for line in soup.find_all():
                if line.name == "time":
                    date = line["datetime"]
                elif "class" in line.attrs and "hour" in line["class"]:
                    hour = line.text
                elif "class" in line.attrs and "expand-selection-bet" in line["class"]:
                    strings = list(line.stripped_strings)
                    try:
                        match = strings[0]+" - "+strings[-2]
                    except IndexError:
                        match = strings[0]
                    odds = list(map(lambda x: float(x.replace(",", ".")), strings[1::2]))
                    if len(odds) == 3:
                        match_odds_hash[match] = {}
                        match_odds_hash[match]['odds'] = {"betclic":odds}
                        match_odds_hash[match]['date'] = (datetime.datetime
                                                          .strptime(date+" "+hour,
                                                                    "%Y-%m-%d %H:%M"))
    driver.quit()
    return match_odds_hash


def parse_buteurs_betclic_match(url):
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    for line in soup.find_all():
        if "class" in line.attrs and "time" in line["class"]:
            date_time = datetime.datetime.strptime(list(line.stripped_strings)[0], "%A %d %B %Y - %H:%M")
        if "data-track-bloc-title" in line.attrs and (line["data-track-bloc-title"] == "Duel de buteurs"
                                                      or "Qui marquera le plus ?" in line["data-track-bloc-title"]):
            for child in line.findChildren("tr", recursive=True):
                match = " - ".join(list(child.stripped_strings)[::2])
                match = match.replace(" - Nul", "")
                odds = list(map(lambda x : float(x.replace(",", ".")), list(child.stripped_strings)[1::2]))
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {"betclic":odds}
                match_odds_hash[match]['date'] = date_time
    return match_odds_hash
