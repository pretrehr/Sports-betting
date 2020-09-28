#!/usr/bin/env python3
"""
Fichier de test
"""

import os
import random
import sqlite3
import urllib.request

from bs4 import BeautifulSoup

import sportsbetting
from sportsbetting.database_functions import is_id_consistent
from sportsbetting.user_functions import parse_competitions


def test_parsing():
    """
    :return:Test simple
    """
    url = "http://www.comparateur-de-cotes.fr/comparateur/football"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    sportsbetting.ODDS = {}
    names = []
    for line in soup.find_all(attrs={"class": "subhead"}):
        if "Principaux championnats" in str(line):
            for link in line.findParent().find_all(["a"]):
                names.append(link.text.strip())
            break
    name_competition = random.choice(names)
    parse_competitions([name_competition], "football", "pmu", "winamax")
    assert len(sportsbetting.ODDS) > 0

def test_consistency():
    PATH_DB = os.path.dirname(sportsbetting.__file__) + "/resources/teams.db"
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    select id, count(*) as c from names group by names.id having c>2
    """)
    results = c.fetchall()
    for result in results:
        id = result[0]
        assert is_id_consistent(id)
