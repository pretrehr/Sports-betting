#!/usr/bin/env python3
"""
Fonctions principales d'assistant de paris
"""

from pprint import pprint
import inspect
import urllib
import urllib.error
try:
    from win10toast import ToastNotifier
except ModuleNotFoundError:
    import subprocess
import selenium_init
from database_functions import get_id_formated_competition_name, get_competition_by_id
from parser_functions import (parse_betclic, parse_betstars, parse_bwin, parse_france_pari,
                              parse_joa, parse_netbet, parse_parionssport, parse_pasinobet,
                              parse_pmu, parse_unibet, parse_winamax, parse_zebet)
from auxiliary_functions import valid_odds, format_team_names, merge_dict_odds, merge_dicts

def parse_competition(competition, sport="football", *sites):
    """
    Retourne les cotes d'une competition donnée pour un ou plusieurs sites de
    paris. Si aucun site n'est choisi, le parsing se fait sur l'ensemble des
    bookmakers reconnus par l'ARJEL
    """
    try:
        _id, formated_name = get_id_formated_competition_name(competition, sport)
    except TypeError:
        print("Competition inconnue")
        return {}
    print(formated_name)
    if not sites:
        sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet',
                 'parionssport', 'pasinobet', 'pmu', 'unibet', 'winamax',
                 'zebet']
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    res_parsing = {}
    for site in sites:
        if len(sites) > 1:
            print(site)
        url = get_competition_by_id(_id, site)
        try:
            if url:
                res_parsing[site] = eval("parse_{}('{}')".format(site, url))
        except urllib.error.URLError:
            print("Site non accessible (délai écoulé)")
        except KeyboardInterrupt:
            res_parsing[site] = {}
    if selenium_required:
        selenium_init.driver.quit()
    if inspect.currentframe().f_back.f_code.co_name == "<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])
    if len(sites) > 1:
        res = format_team_names(res_parsing, sport)
        return valid_odds(merge_dict_odds(res), sport)
    return valid_odds(res_parsing[sites[0]], sport)


def parse_competitions(competitions, *sites):
    """
    Retourne les cotes de plusieurs competitions
    """
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    list_odds = []
    for competition in competitions:
        list_odds.append(parse_competition(competition, "football", *sites))
        print()
    if selenium_required:
        selenium_init.driver.quit()
    if inspect.currentframe().f_back.f_code.co_name == "<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])
    return merge_dicts(list_odds)


def parse_football(*sites):
    """
    Stocke les cotes des principaux championnats de football en global
    """
    global MAIN_ODDS
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    competitions = ["france ligue 1", "angleterre premier league",
                    "espagne liga", "italie serie", "allemagne bundesliga",
                    "ligue des champions"]
    MAIN_ODDS = parse_competitions(competitions, *sites)
    if selenium_required:
        selenium_init.driver.quit()
    if inspect.currentframe().f_back.f_code.co_name == "<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])
