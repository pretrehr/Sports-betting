#!/usr/bin/env python3

import urllib
import urllib.error
import urllib.request
from pprint import pprint
from database import (find_competition, find_competition_id, import_teams_in_db,
                      is_in_db_site, import_sport_teams_in_db)
from parser_bookmakers import (parse_betclic, parse_betstars, parse_bwin,
                               parse_france_pari, parse_netbet, parse_parionssport,
                               parse_pasinobet, parse_pmu, parse_unibet,
                               parse_winamax, parse_zebet, merge_dict_odds,
                               adapt_names_to_all, add_names_to_db_complete,
                               parse_joa)
from bet_functions import merge_dicts      
import time                         

def parse_competition(competition, sport, *sites_not_to_parse):
    sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet', 'parionssport', 'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']
    for site in sites_not_to_parse:
        sites.remove(site)
    res_parsing = {}
    for site in sites:
        print(site)
        url = find_competition(competition, sport, site)
        try:
            if url:
                exec("res_parsing['{}'] = parse_{}('{}')".format(site, site, url))
        except urllib.error.URLError:
            print("Site non accessible (délai écoulé)")
        except KeyboardInterrupt:
            res_parsing[site] = {}
    res = adapt_names_to_all(res_parsing, sport)
    return merge_dict_odds(res)

def parse_main_competitions():
    competitions = ["france ligue 1", "angleterre premier league", "espagne liga", "italie serie", "allemagne bundesliga", "ligue des champions"]
    list_odds = []
    for competition in competitions:
        print("\n"+competition.title())
        list_odds.append(parse_competition(competition, "football"))
    return merge_dicts(list_odds)

def add_names_to_db_all_sites(competition, sport, *sites_not_to_parse):
    id = find_competition_id(competition, sport)
    if competition==sport:
        import_sport_teams_in_db(sport)
    else:
        import_teams_in_db("http://www.comparateur-de-cotes.fr/comparateur/"+sport+"/a-ed"+str(id))
    sites = ['betclic', 'betstars', 'bwin', 'netbet', 'parionssport', 'pasinobet', 'pmu', 'unibet', 'winamax']
    for site in sites_not_to_parse:
        sites.remove(site)
    for site in sites:
        print(site)
        url = find_competition(competition, sport, site)
        if url:
            try:
                add_names_to_db_complete(site, sport, url)
            except KeyboardInterrupt:
                pass
            except urllib.error.URLError:
                print("Site non accessible (délai écoulé)")
    