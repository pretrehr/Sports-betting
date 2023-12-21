"""
Bwin odds scraper
"""

import datetime
import json
import os
import re
import urllib

import dateutil.parser
import seleniumwire.webdriver

import sportsbetting as sb
from sportsbetting.auxiliary_functions import reverse_match_odds, truncate_datetime



def get_bwin_token():
    """
    Get Bwin token to access the API
    """
    token = ""
    if os.path.exists(sb.PATH_TOKENS):
        with open(sb.PATH_TOKENS, "r") as file:
            lines = file.readlines()
            for line in lines:
                bookmaker, token = line.split()
                if bookmaker == "bwin":
                    return token
    print("Récupération du token de connexion de Bwin")
    options = seleniumwire.webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images': 2,
             'disk-cache-size': 4096}
    options.add_argument('log-level=3')
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--headless")
    options.add_argument("--disable-extensions")
    driver = seleniumwire.webdriver.Chrome(options=options)
    driver.get("https://sports.bwin.fr/fr/sports")
    for request in driver.requests:
        if request.response and "x-bwin-accessid=" in request.url:
            token = request.url.split("x-bwin-accessid=")[1].split("&")[0]
            with open(sb.PATH_TOKENS, "a+") as file:
                file.write("bwin {}\n".format(token))
            break
    driver.quit()
    return token

def parse_bwin_api(parameter):
    """
    Get Bwin odds from API
    """
    token = get_bwin_token()
    if not token:
        return {}
    url = ("https://cds-api.bwin.fr/bettingoffer/fixtures?x-bwin-accessid={}&lang=fr&country=FR&userCountry=FR"
           "&fixtureTypes=Standard&state=Latest&offerMapping=Filtered&offerCategories=Gridable&fixtureCategories=Gridable"
           "&{}&skip=0&take=1000&sortBy=Tags".format(token, parameter))
    content = urllib.request.urlopen(url).read()
    parsed = json.loads(content)
    fixtures = parsed["fixtures"]
    odds_match = {}
    for fixture in fixtures:
        if fixture["stage"] == "Live":
            continue
        reversed_odds = " chez " in fixture["name"]["value"] # not ok
        odds = []
        participants = fixture["participants"] #ok
        name = " - ".join(map(lambda x: x["name"]["value"], participants)) #ok
        optionMarkets = fixture["optionMarkets"]
        id_match = str(fixture["id"])
        for optionMarket in optionMarkets:
            odds_type = optionMarket["name"]["value"]
            if odds_type not in ["1 X 2", "Pari sur le vainqueur (US)", "1X2 (temps réglementaire)", "Vainqueur 1 2", "Résultat du match"]:
                continue
            for result in optionMarket["options"]:
                odds.append(result["price"]["odds"])
            break
        date = truncate_datetime(dateutil.parser.isoparse(fixture["startDate"]))+datetime.timedelta(hours=2)
        if reversed_odds:
            name, odds = reverse_match_odds(name, odds)
        odds_match[name] = {"date": date, "odds":{"bwin":odds}, "id":{"bwin":id_match}}
    return odds_match


def parse_bwin(url):
    """
    Get Bwin odds from url
    """
    parameter = ""
    if "/0" in url:
        id_sport = re.findall(r'\d+', url)[0]
        parameter = "sportIds=" + id_sport
    elif "0:" in url:
        id_virtual_league = url.split("0:")[-1]
        parameter = "virtualCompetitionIds=" + id_virtual_league
    else:
        id_league = re.findall(r'\d+', url)[-1]
        parameter = "competitionIds=" + id_league
    return parse_bwin_api(parameter)
