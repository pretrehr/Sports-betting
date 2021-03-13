"""
Fonctions de parsing
"""

import locale
import sys

from sportsbetting.bookmakers import (betclic, bwin, france_pari, joa, netbet, parionssport,
                                      pasinobet, pmu, pokerstars, unibet, winamax, zebet)


if sys.platform.startswith("win"):
    locale.setlocale(locale.LC_TIME, "fr")
elif sys.platform.startswith("linux"):
    locale.setlocale(locale.LC_TIME, "fr_FR.utf8")
else:  # sys.platform.startswith("darwin") # (Mac OS)
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

def parse(site, url=""):
    """
    Retourne les cotes d'un site donné
    """
    parse_functions = {
        "betclic" : betclic.parse_betclic,
        "pokerstars" : pokerstars.parse_pokerstars,
        "bwin" : bwin.parse_bwin,
        "france_pari" : france_pari.parse_france_pari,
        "joa" : joa.parse_joa,
        "netbet" : netbet.parse_netbet,
        "parionssport" : parionssport.parse_parionssport,
        "pasinobet" : pasinobet.parse_pasinobet,
        "pmu" : pmu.parse_pmu,
        "unibet" : unibet.parse_unibet,
        "winamax" : winamax.parse_winamax,
        "zebet" : zebet.parse_zebet
    }
    return parse_functions[site](url)
