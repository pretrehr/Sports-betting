"""
Pokerstars odds scraper
"""

import datetime
import json
import re
import urllib

from sportsbetting.auxiliary_functions import merge_dicts


def parse_betstars_api(id_league):
    """
    Get Betstars odds from league id
    """
    url = ("https://sports.pokerstarssports.fr/sportsbook/v1/api/getCompetitionEvents?competitionId={}"
           "&marketTypes=SOCCER%3AFT%3AAXB%2CMRES,BASKETBALL%3AFTOT%3AML,AB,RUGBYUNION%3AFT%3AMRES,HANDBALL%3AFT%3AMRES,"
           "ICEHOCKEY%3AFT%3AAXB&includeOutrights=false&channelId=11&locale=fr-fr&siteId=32".format(id_league))
    content = urllib.request.urlopen(url).read()
    parsed = json.loads(content)
    matches = parsed["event"]
    odds_match = {}
    for match in matches:
        if match["isInplay"]:
            continue
        participants = match["participants"]
        if not participants:
            continue
        name_home = ""
        name_away = ""
        for participant in participants["participant"]:
            if participant["type"] == "AWAY":
                name_away = participant["names"]["longName"].replace("&apos;", "'")
            elif participant["type"] == "HOME":
                name_home = participant["names"]["longName"].replace("&apos;", "'")
        name = name_home + " - " + name_away
        date = datetime.datetime.fromtimestamp(match["eventTime"]/1000)
        markets = match["markets"]
        if not markets:
            continue
        odd_home, odd_away, odd_draw = 0, 0, 0
        for selection in markets[0]["selection"]:
            odd = selection["odds"]["dec"]
            if odd == "-":
                odd = "1.01"
            if selection["type"] in ["A", "AH", "playerA"]:
                odd_home = float(odd)
            elif selection["type"] in ["B", "BH", "playerB"]:
                odd_away = float(odd)
            elif selection["type"] in ["D", "Draw"]:
                odd_draw = float(odd)
            else:
                print(selection["type"])
        odds = []
        if odd_draw:
            odds = [odd_home, odd_draw, odd_away]
        else:
            odds = [odd_home, odd_away]
        odds_match[name] = {}
        odds_match[name]["date"] = date
        odds_match[name]["odds"] = {"betstars":odds}
    return odds_match

def parse_sport_betstars(sport):
    """
    Get Betstars odds from sport
    """
    url = ("https://sports.pokerstarssports.fr/sportsbook/v1/api/getSportTree?sport={}&includeOutrights=false"
           "&includeEvents=false&includeCoupons=true&channelId=11&locale=fr-fr&siteId=32".format(sport.upper()))
    content = urllib.request.urlopen(url).read()
    parsed = json.loads(content)
    list_odds = []
    competitions = parsed["categories"]
    for competition in competitions:
        id_competition = competition["id"]
        list_odds.append(parse_betstars_api(id_competition))
    return merge_dicts(list_odds)

def parse_betstars(url):
    """
    Get Betstars odds from url
    """
    if not "https://" in url:
        return parse_sport_betstars(url)
    id_league = re.findall(r'\d+', url)[-1]
    return parse_betstars_api(id_league)
