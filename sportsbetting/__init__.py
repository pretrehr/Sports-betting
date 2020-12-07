"""
initialisation du module
"""
import chromedriver_autoinstaller
import collections
import queue
import re


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
    r = re.search(pat, txt)
    return r.group(0) if r else '&'


ua = UserAgent()
USER_AGENT = sorted(ua.data_browsers["chrome"], key=lambda a: grp(r'Chrome/[^ ]+', a))[-1]
try:
    PATH_DRIVER = chromedriver_autoinstaller.install(True)
except IndexError:
    pass
