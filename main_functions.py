#!/usr/bin/env python3
"""
Fonctions principales d'assistant de paris
"""

from pprint import pprint
from copy import deepcopy
from bet_functions import merge_dicts, gain2, mises2, gain, mises, mises_freebet
from database import (find_competition, get_id_formated_competition_name,
                      get_competition_by_id)
from parser_bookmakers import (valid_odds, format_team_names, merge_dict_odds,
                               parse_betclic, parse_betstars, parse_bwin,
                               parse_france_pari, parse_joa, parse_netbet,
                               parse_parionssport, parse_pasinobet, parse_pmu,
                               parse_unibet, parse_winamax, parse_zebet)
import urllib
import urllib.error
import datetime

def parse_competition(competition, sport, *sites):
    """
    Retourne les cotes d'une competition donnée pour un ou plusieurs sites de
    paris. Si aucun site n'est choisi, le parsing se fait sur l'ensemble des
    bookmakers reconnus par l'ARJEL
    """
    try:
        id, formated_name = get_id_formated_competition_name(competition, sport)
    except TypeError:
        print("Competition inconnue")
        return {}
    print(formated_name)
    if not sites:
        sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet',
                 'parionssport', 'pasinobet', 'pmu', 'unibet', 'winamax',
                 'zebet']
    res_parsing = {}
    for site in sites:
        if len(sites)>1:
            print(site)
        url = get_competition_by_id(id, site)
        try:
            if url:
                exec("res_parsing['{}'] = parse_{}('{}')".format(site, site, url))
        except urllib.error.URLError:
            print("Site non accessible (délai écoulé)")
        except KeyboardInterrupt:
            res_parsing[site] = {}
    if len(sites)>1:
        res = format_team_names(res_parsing, sport)
        return valid_odds(merge_dict_odds(res), sport)
    return valid_odds(res_parsing[site], sport)

def parse_main_competitions(*sites):
    competitions = ["france ligue 1", "angleterre premier league",
                    "espagne liga", "italie serie", "allemagne bundesliga",
                    "ligue des champions", "qualif"]
    list_odds = []
    for competition in competitions:
        list_odds.append(parse_competition(competition, "football", *sites))
        print()
    return merge_dicts(list_odds)

def parse_football(*sites):
    global main_odds
    main_odds = parse_main_competitions(*sites)

def parse_tennis(*sites):
    global odds_tennis
    odds_tennis = parse_competition("tennis", "tennis", *sites)

def parse_nba(*sites):
    global odds_nba
    odds_nba = parse_competition("nba", "basketball", *sites)


def odds_match(match, sport="football"):
    """
    Return the different odds of a given match
    """
    all_odds = main_odds if sport=="football" else odds_tennis if sport=="tennis" else odds_nba
    opponents = match.split('-')
    match_name = ""
    for match_name in all_odds:
        if (opponents[0].lower().strip() in match_name.lower()
                and opponents[1].lower().strip() in match_name.lower()):
            break
    print(match_name)
    return all_odds[match_name]


def best_bets_match(match, site, bet, minimum_odd, sport="football"):
    """
    Given a match, a bookmaker and a sum to bet, return the best odds on which
    bet among different bookmakers
    """
    all_odds = odds_match(match, sport)
    pprint(all_odds)
    odds_site = all_odds['odds'][site]
    best_odds = deepcopy(odds_site)
    best_profit = -float("inf")
    n = len(all_odds['odds'][site])
    best_sites = [site for _ in range(n)]
    best_i = 0
    for odds in all_odds['odds'].items():
        for i in range(n):
            if odds[1][i] > best_odds[i]:
                best_odds[i] = odds[1][i]
                best_sites[i] = odds[0]
    for i in range(n):
        if odds_site[i]>=minimum_odd:
            odds_to_check = (best_odds[:i]+[odds_site[i]]+best_odds[i+1:])
            profit = gain2(odds_to_check, i, bet)
            if profit > best_profit:
                best_profit = profit
                best_overall_odds = odds_to_check
                sites = best_sites[:i]+[site]+best_sites[i+1:]
                bets = mises2(odds_to_check, bet, i)
                best_i = i
    print(sites, best_overall_odds, sep='\n')
    return mises2(best_overall_odds, bet, best_i, True)



def best_match_base(odds_function, profit_function, criteria, display_function,
                    site, sport="football", date_max=None, time_max=None,
                    date_min=None, time_min=None):
    """
    Given a bookmaker, return on which match you should bet to maximize your
    gain, knowing that you need to bet a bet on a minimum odd before a limit
    date
    """ 
    all_odds = main_odds if sport=="football" else odds_tennis if sport=="tennis" else odds_nba
    best_profit = -float("inf")
    best_rank = 0
    hour_max, minute_max = 0, 0
    hour_min, minute_min = 0, 0
    n = 2 + (sport not in ["tennis", "volleyball", "basketball", "nba"])
    if time_max:
        if time_max[-1] == 'h':
            hour_max = int(time_max[:-1])
        else:
            hour_max, minute_max = (int(_) for _ in time_max.split('h'))
    if date_max:
        day_max, month_max, year_max = (int(_) for _ in date_max.split('/'))
        datetime_max = datetime.datetime(year_max, month_max, day_max,
                                hour_max, minute_max)
    else:
        datetime_max = None
    if time_min:
        if time_min[-1] == 'h':
            hour_min = int(time_min[:-1])
        else:
            hour_min, minute_min = (int(_) for _ in time_min.split('h'))
    if date_min:
        day_min, month_min, year_min = (int(_) for _ in date_min.split('/'))
        datetime_min = datetime.datetime(year_min, month_min, day_min,
                                hour_min, minute_min)
    else:
        datetime_min = None
    for match in all_odds:
        if (site in all_odds[match]['odds']
                and (not date_max or all_odds[match]['date'] <= datetime_max)
                and (not date_min or all_odds[match]['date'] >= datetime_min)):
            odds_site = all_odds[match]['odds'][site]
            best_odds = deepcopy(odds_site)
            best_sites = [site for _ in range(n)]
            for odds in all_odds[match]['odds'].items():
                for i in range(n):
                    if odds[1][i] > best_odds[i]:
                        best_odds[i] = odds[1][i]
                        best_sites[i] = odds[0]
            for i in range(n):
                odds_to_check = odds_function(best_odds, odds_site, i)
                if criteria(odds_to_check, i):
                    profit = profit_function(odds_to_check, i)
                    if profit > best_profit:
                        best_rank = i
                        best_profit = profit
                        best_match = match
                        best_overall_odds = odds_to_check
                        sites = best_sites[:i]+[site]+best_sites[i+1:]
    try:
        print(best_match)
        pprint(all_odds[best_match])
#         print(best_overall_odds)
        print(sites)
        print(display_function(best_overall_odds, best_rank))
    except UnboundLocalError:
        print("No match found")


def best_match_under_conditions(site, minimum_odd, bet, sport="football",
                                 one_site=False, live=False, date_max=None,
                                 time_max=None, date_min=None, time_min=None):
    odds_function = lambda best_odds, odds_site, i : (best_odds[:i]
                                 +[odds_site[i]*0.9 if live else odds_site[i]]
                                 +best_odds[i+1:]) if not one_site else (odds_site[:i]
                                 +[odds_site[i]*0.9 if live else odds_site[i]]
                                 +odds_site[i+1:])
    profit_function = lambda odds_to_check, i : gain(odds_to_check, bet)-bet if one_site else gain2(odds_to_check, i, bet)
    criteria = lambda odds_to_check, i : ((not one_site and odds_to_check[i] >= minimum_odd) 
                                          or (one_site and all(odd>=minimum_odd for odd in odds_to_check)))
    display_function = lambda best_overall_odds, best_rank : mises2(best_overall_odds, bet, best_rank, True) if not one_site else mises(best_overall_odds, bet, True)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    site, sport, date_max=None, time_max=None, date_min=None,
                    time_min=None)

def best_match_freebet(site, freebet, sport, date_max=None, time_max=None, date_min=None,
                    time_min=None):
    odds_function = lambda best_odds, odds_site, i : (best_odds[:i]
                                     +[odds_site[i]-1]+best_odds[i+1:])
    profit_function = lambda odds_to_check, i : gain2(odds_to_check, i)+1
    criteria = lambda odds_to_check, i : True
    display_function = lambda x, i : mises_freebet(x[:i]+[x[i]+1]+x[i+1:], freebet, i, True)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    site, sport, date_max, time_max, date_min, time_min)
    