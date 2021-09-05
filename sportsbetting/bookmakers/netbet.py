"""
NetBet odds scraper
"""

import datetime
import http.client
import re
import urllib
import urllib.error
import urllib.request

import fake_useragent

from bs4 import BeautifulSoup

import sportsbetting as sb
from sportsbetting.auxiliary_functions import truncate_datetime


def parse_netbet(url):
    """
    Retourne les cotes disponibles sur netbet
    """
    sport = None
    if url in ["football", "tennis", "basketball", "hockey-glace", "rugby", "handball"]:
        sport = url
        url = "https://www.netbet.fr/top-paris"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4)"
                             "AppleWebKit/537.36 (KHTML, like Gecko)"
                             "Chrome/83.0.4103.97"
                             "Safari/537.36"}
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
        raise sb.UnavailableSiteException
    if soup.find(attrs={"class": "none"}):
        raise sb.UnavailableCompetitionException
    if response.geturl() == "https://www.netbet.fr/":
        raise sb.UnavailableCompetitionException
    match_odds_hash = {}
    today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    date = ""
    year = " " + str(today.year)
    match = ""
    competition = ""
    date_time = None
    valid_match = True
    for line in soup.find_all():
        if "class" in line.attrs and "nb-link-event" in line["class"] and "href" in line.attrs:
            if sport:
                valid_match = sport+"/" in line["href"]
            link = line["href"]
            competition = " - ".join(map(lambda x : x.replace("-", " ").title(), link.split("/")[2:4]))
        elif "class" in line.attrs and "nb-event_datestart" in line["class"]:
            date = list(line.stripped_strings)[0] + year
            if "Auj." in date:
                date = datetime.datetime.today().strftime("%d/%m %Y")
        elif "class" in line.attrs and "nb-event_timestart" in line["class"]:
            hour = line.text
            if " min" in hour:
                date_time = datetime.datetime.today()+datetime.timedelta(minutes=int(hour.strip(" min")))
                date_time = truncate_datetime(date_time)
                continue
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
                if valid_match and match and match not in match_odds_hash and date_time:
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"netbet": odds}
                    match_odds_hash[match]['date'] = date_time
                    match_odds_hash[match]['id'] = {"netbet": link}
                    match_odds_hash[match]['competition'] = competition
            except ValueError:  # match live (cotes non disponibles)
                pass
    return match_odds_hash
