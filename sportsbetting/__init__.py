"""
initialisation du module
"""
import collections
import json
import os
import queue
import re
import sys
import urllib.error

import chromedriver_autoinstaller
from fake_useragent import UserAgent

ALL_ODDS_COMBINE = {}
ODDS = {}
TEAMS_NOT_FOUND = []
PROGRESS = 0
SUB_PROGRESS_LIMIT = 1
SITE_PROGRESS = collections.defaultdict(int)
QUEUE_TO_GUI = queue.Queue()
QUEUE_FROM_GUI = queue.Queue()
ODDS_INTERFACE = ""
EXPECTED_TIME = 0
INTERFACE = False
IS_PARSING = False
ABORT = False
SPORTS = ["basketball", "football", "handball", "hockey-sur-glace", "rugby", "tennis"]
PATH_DRIVER = ""
SELENIUM_SITES = {"joa"}
BOOKMAKERS = ["betclic", "barrierebet", "bwin", "france_pari", "joa", "netbet", "parionssport",
              "pasinobet", "pinnacle", "pmu", "pokerstars", "unibet", "winamax", "zebet"]
TEST = False
DB_MANAGEMENT = False
TOKENS = {}
COOKIES_JOA_ACCEPTED = False
TRANSLATION = {}
BETA = False
SUREBETS = {}
MIDDLES = {}
MILES_RATES = {"5€" : 385, "10€" : 770, "20€" : 1510, "50€" : 3700, "100€": 7270, "200€" : 14290, "500€" : 35090, "1000€" : 69000, "2000€":135600, "5000€": 333330}


class UnavailableCompetitionException(Exception):
    """
    Exception renvoyée lorsqu'une compétition est introuvable
    """

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class UnavailableSiteException(Exception):
    """
    Exception renvoyée lorsqu'un bookmaker est indisponible
    """

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class AbortException(Exception):
    """
    Exception renvoyée lorsqu'on interropt le parsing
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)



def grp(pat, txt):
    res = re.search(pat, txt)
    return res.group(0) if res else '&'

def find_files(filename, search_path):
    for root, _, files in os.walk(search_path):
        if filename in files:
            return os.path.abspath(os.path.join(root, filename))


ua = UserAgent(verify_ssl=False)
USER_AGENT = sorted(ua.data_browsers["chrome"], key=lambda a: grp(r'Chrome/[^ ]+', a))[-1]
try:
    PATH_DRIVER = chromedriver_autoinstaller.install(True)
except IndexError:
    PATH_DRIVER = find_files("chromedriver.exe", ".")
#except urllib.error.URLError:
#    print("Aucune connection internet")
#    sys.exit()
print(PATH_DRIVER)

PATH_DB = os.path.dirname(__file__) + "/resources/teams.db"
print(PATH_DB)

PATH_TOKENS = os.path.dirname(__file__) + "/bookmakers/tokens.txt"

PATH_TRANSLATION = os.path.dirname(__file__) + "/resources/translation.json"
with open(PATH_TRANSLATION, encoding='utf-8') as file:
    TRANSLATION = json.load(file)

