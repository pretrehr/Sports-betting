"""
initialisation du module
"""

import queue
import re

from fake_useragent import UserAgent

ALL_ODDS_COMBINE = {}
ODDS = {}
TEAMS_NOT_FOUND = []
PROGRESS = 0
SUBPROGRESS_LIMIT = 1
QUEUE_TO_GUI = queue.Queue()
QUEUE_FROM_GUI = queue.Queue()
ODDS_INTERFACE = ""
EXPECTED_TIME = 0


class UnavailableCompetitionException(Exception):
    """
    Exception renvoyée lorsqu'une compétition est introuvable
    """

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


def grp(pat, txt):
    r = re.search(pat, txt)
    return r.group(0) if r else '&'


ua = UserAgent()
USER_AGENT = sorted(ua.data_browsers["chrome"], key=lambda a: grp(r'Chrome/[^ ]+', a))[-1]
