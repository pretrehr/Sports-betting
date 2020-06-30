#!/usr/bin/env python3
"""
Fichier de test
"""

import random
import urllib.request

from bs4 import BeautifulSoup

import sportsbetting
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
    parse_competitions([name_competition], "football", "betclic", "unibet")
    assert len(sportsbetting.ODDS) > 0
