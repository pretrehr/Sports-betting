#!/usr/bin/env python3
"""
Fonctions principales d'assistant de paris
"""

from pprint import pprint
import inspect
import urllib
import urllib.error
import datetime
import copy
import time
from itertools import combinations, permutations
import numpy as np
import unidecode
try:
    from win10toast import ToastNotifier
except ModuleNotFoundError:
    import subprocess
import selenium_init
from database_functions import (get_id_formated_competition_name, get_competition_by_id,
                                get_competition_url, get_competition_id, import_teams_by_sport,
                                import_teams_by_url)
from parser_functions import parse_and_add_to_db, parse
from auxiliary_functions import (valid_odds, format_team_names, merge_dict_odds, merge_dicts,
                                 afficher_mises_combine, find_almost_won_matches,
                                 cotes_combine_all_sites, defined_bets)
from basic_functions import (gain2, mises2, gain, mises, mises_freebet, cotes_freebet,
                             gain_pari_rembourse_si_perdant, mises_pari_rembourse_si_perdant,
                             cotes_combine)

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
                res_parsing[site] = parse(site, url)
        except urllib.error.URLError:
            print("Site non accessible (délai écoulé)")
        except KeyboardInterrupt:
            res_parsing[site] = {}
    if selenium_required:
        selenium_init.DRIVER.quit()
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
        selenium_init.DRIVER.quit()
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
        selenium_init.DRIVER.quit()
    if inspect.currentframe().f_back.f_code.co_name == "<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])


def parse_tennis(*sites):
    """
    Stocke les cotes des tournois de tennis en global
    """
    global ODDS_TENNIS
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    ODDS_TENNIS = parse_competition("tennis", "tennis", *sites)
    if selenium_required:
        selenium_init.DRIVER.quit()
    if inspect.currentframe().f_back.f_code.co_name == "<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])

def parse_nba(*sites):
    """
    Stocke les cotes de la NBA en global
    """
    global ODDS_NBA
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    ODDS_NBA = parse_competition("nba", "basketball", *sites)
    if selenium_required:
        selenium_init.DRIVER.quit()
    if inspect.currentframe().f_back.f_code.co_name == "<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])

def parse_handball(*sites):
    """
    Stocke les cotes de handball en global
    """
    global ODDS_HANDBALL
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    ODDS_HANDBALL = parse_competition("champions", "handball", *sites)
    if selenium_required:
        selenium_init.DRIVER.quit()
    if inspect.currentframe().f_back.f_code.co_name == "<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])


def odds_match(match, sport="football"):
    """
    Retourne les cotes d'un match donné sur tous les sites de l'ARJEL
    """
    all_odds = (MAIN_ODDS if sport == "football"
                else (ODDS_TENNIS if sport == "tennis"
                      else (ODDS_HANDBALL if sport == "handball"
                            else ODDS_NBA)))
    opponents = match.split('-')
    match_name = ""
    for match_name in all_odds:
        if (opponents[0].lower().strip() in unidecode.unidecode(match_name.lower())
                and opponents[1].lower().strip() in unidecode.unidecode(match_name.lower())):
            break
    else:
        return
    print(match_name)
    return match_name, all_odds[match_name]


def best_stakes_match(match, site, bet, minimum_odd, sport="football"):
    """
    Pour un match, un bookmaker, une somme à miser sur ce bookmaker et une cote
    minimale donnés, retourne la meilleure combinaison de paris à placer
    """
    best_match, all_odds = odds_match(match, sport)
    if not all_odds:
        print("No match found")
        return
    pprint(all_odds)
    odds_site = all_odds['odds'][site]
    best_odds = copy.deepcopy(odds_site)
    best_profit = -float("inf")
    n = len(all_odds['odds'][site])
    best_sites = [site for _ in range(n)]
    best_i = 0
    for odds in all_odds['odds'].items():
        for i in range(n):
            if odds[1][i] > best_odds[i] and (odds[1][i] >= 1.1 or odds[0] == "pmu"):
                best_odds[i] = odds[1][i]
                best_sites[i] = odds[0]
    for i in range(n):
        if odds_site[i] >= minimum_odd:
            odds_to_check = (best_odds[:i]+[odds_site[i]]+best_odds[i+1:])
            profit = gain2(odds_to_check, i, bet)
            if profit > best_profit:
                best_profit = profit
                best_overall_odds = odds_to_check
                sites = best_sites[:i]+[site]+best_sites[i+1:]
                bets = mises2(odds_to_check, bet, i)
                best_i = i
    try:
        mises2(best_overall_odds, bet, best_i, True)
        afficher_mises_combine(best_match.split(" / "), [sites], [bets], all_odds["odds"], sport)
    except UnboundLocalError:
        print("No match found")


def best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport="football", date_max=None,
                    time_max=None, date_min=None, time_min=None, combine=False,
                    nb_matches_combine=2, freebet=False, one_site=False, recalcul=False):
    """
    Fonction de base de détermination du meilleur match sur lequel parier en
    fonction de critères donnés
    """
    try:
        if combine:
            all_odds = ALL_ODDS_COMBINE
        else:
            all_odds = (MAIN_ODDS if sport == "football"
                        else (ODDS_TENNIS if sport == "tennis"
                              else (ODDS_HANDBALL if sport == "handball"
                                    else ODDS_NBA)))
    except NameError:
        print("""
        Merci de définir les côtes de base, appelez la fonction parse_football,
        parse_nba ou parse_tennis selon vos besoins""")
        return
    best_profit = -float("inf")
    best_rank = 0
    hour_max, minute_max = 0, 0
    hour_min, minute_min = 0, 0
    if combine:
        n = (2 + (sport not in ["tennis", "volleyball", "basketball", "nba"]))**nb_matches_combine
    else:
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
            best_odds = copy.deepcopy(odds_site)
            best_sites = [site for _ in range(n)]
            if not one_site:
                for odds in all_odds[match]['odds'].items():
                    for i in range(n):
                        if odds[1][i] > best_odds[i] and (odds[1][i] >= 1.1 or odds[0] == "pmu"):
                            best_odds[i] = odds[1][i]
                            best_sites[i] = odds[0]
            for odd_i, site_i in zip(best_odds, best_sites):
                if (odd_i < 1.1 and site_i != "pmu"):
                    break
            else:
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
        pprint(all_odds[best_match], compact=True)
        if recalcul:
            sum_almost_won = find_almost_won_matches(best_match,
                                                     result_function(best_overall_odds,
                                                                     best_rank),
                                                     sport)
            display_function = lambda x, i: mises(x, 10000*50/sum_almost_won, True)
            result_function = lambda x, i: mises(x, 10000*50/sum_almost_won, False)
            find_almost_won_matches(best_match, result_function(best_overall_odds, best_rank),
                                    sport, True)
        display_function(best_overall_odds, best_rank)
        afficher_mises_combine(best_match.split(" / "), [sites],
                               [result_function(best_overall_odds, best_rank)],
                               all_odds[best_match]["odds"], sport, best_rank if freebet else None,
                               one_site and freebet, best_overall_odds)
    except UnboundLocalError:
        print("No match found")

def best_match_under_conditions(site, minimum_odd, bet, sport="football", one_site=False,
                                live=False, date_max=None, time_max=None, date_min=None,
                                time_min=None):
    """
    Retourne le meilleur match sur lequel miser lorsqu'on doit miser une somme
    donnée à une cote donnée. Cette somme peut-être sur seulement une issue
    (one_site=False) ou bien répartie sur plusieurs issues d'un même match
    (one_site=True), auquel cas, chacune des cotes du match doivent respecter le
    critère de cote minimale.
    """
    odds_function = lambda best_odds, odds_site, i: ((best_odds[:i]
                                                      +[odds_site[i]*0.9 if live else odds_site[i]]
                                                      +best_odds[i+1:]) if not one_site
                                                     else (odds_site[:i]
                                                           +[odds_site[i]*0.9 if live
                                                             else odds_site[i]]
                                                           +odds_site[i+1:]))
    profit_function = lambda odds_to_check, i: (gain(odds_to_check, bet)-bet if one_site
                                                else gain2(odds_to_check, i, bet))
    criteria = lambda odds_to_check, i: ((not one_site and odds_to_check[i] >= minimum_odd)
                                         or (one_site and all(odd >= minimum_odd
                                                              for odd in odds_to_check)))
    display_function = lambda best_overall_odds, best_rank: (mises2(best_overall_odds, bet,
                                                                    best_rank, True) if not one_site
                                                             else mises(best_overall_odds, bet,
                                                                        True))
    result_function = lambda best_overall_odds, best_rank: (mises2(best_overall_odds, bet,
                                                                   best_rank, False) if not one_site
                                                            else mises(best_overall_odds, bet,
                                                                       False))
    best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport, date_max, time_max, date_min,
                    time_min, one_site=one_site)

def best_match_pari_gagnant(site, minimum_odd, bet, sport="football",
                            date_max=None, time_max=None, date_min=None,
                            time_min=None):
    """
    Retourne le meilleur match sur lequel miser lorsqu'on doit gagner un pari à
    une cote donnée sur un site donné.
    """
    odds_function = lambda best_odds, odds_site, i: odds_site
    profit_function = lambda odds_to_check, i: gain2(odds_to_check, np.argmax(odds_to_check), bet)
    criteria = lambda odds_to_check, i: all(odd >= minimum_odd for odd in odds_to_check)
    display_function = lambda best_overall_odds, best_rank: mises2(best_overall_odds, bet,
                                                                   np.argmax(best_overall_odds),
                                                                   True)
    result_function = lambda best_overall_odds, best_rank: mises2(best_overall_odds, bet,
                                                                  np.argmax(best_overall_odds),
                                                                  False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport, date_max, time_max, date_min,
                    time_min, one_site=True)

def best_match_freebet(site, freebet, sport="football", live=False, date_max=None, time_max=None,
                       date_min=None, time_min=None):
    """
    Retourne le match qui génère le meilleur gain pour un unique freebet placé,
    couvert avec de l'argent réel.
    """
    fact_live = 1-0.2*live
    odds_function = lambda best_odds, odds_site, i: (best_odds[:i]+[odds_site[i]*fact_live-1]
                                                     +best_odds[i+1:])
    profit_function = lambda odds_to_check, i: gain2(odds_to_check, i)+1
    criteria = lambda odds_to_check, i: True
    display_function = lambda x, i: mises_freebet(x[:i]+[x[i]+1]+x[i+1:], freebet, i, True)
    result_function = lambda x, i: mises_freebet(x[:i]+[x[i]+1]+x[i+1:], freebet, i, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport, date_max, time_max, date_min,
                    time_min, freebet=True)

def best_match_cashback(site, minimum_odd, bet, sport="football", freebet=True,
                        combi_max=0, combi_odd=1, rate_cashback=1, date_max=None,
                        time_max=None, date_min=None, time_min=None):
    """
    Retourne le match qui génère le meilleur gain pour une promotion de type
    "Pari remboursé si perdant". Le bonus combi-max, la côte des sélections
    supposées sûres (dans le cadre d'une promotion sur combiné) ainsi que le
    bonus combi-max sont également paramétrables
    """
    odds_function = lambda best_odds, odds_site, i: (best_odds[:i]
                                                     +[combi_odd*odds_site[i]
                                                       *(1+combi_max)-combi_max]
                                                     +best_odds[i+1:])
    profit_function = lambda odds_to_check, i: gain_pari_rembourse_si_perdant(odds_to_check, bet, i,
                                                                              freebet,
                                                                              rate_cashback)
    criteria = lambda odds_to_check, i: (odds_to_check[i]+combi_max)/(1+combi_max) >= minimum_odd
    display_function = lambda x, i: mises_pari_rembourse_si_perdant(x, bet, i, freebet,
                                                                    rate_cashback, True)
    result_function = lambda x, i: mises_pari_rembourse_si_perdant(x, bet, i, freebet,
                                                                   rate_cashback, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport, date_max, time_max, date_min,
                    time_min)


def best_matches_combine(site, minimum_odd, bet, sport, nb_matches=2, one_site=False,
                         date_max=None, time_max=None, date_min=None, time_min=None,
                         minimum_odd_selection=1.01):
    """
    Given a bookmaker, return on which matches you should share your freebet to
    maximize your gain
    """
    global ALL_ODDS_COMBINE
    global MAIN_ODDS
    global ODDS_NBA
    global ODDS_TENNIS
    global ODDS_HANDBALL
    all_odds = (MAIN_ODDS if sport == "football"
                else (ODDS_TENNIS if sport == "tennis"
                      else (ODDS_HANDBALL if sport == "handball"
                            else ODDS_NBA)))
    ALL_ODDS_COMBINE = {}
    for combine in combinations(all_odds.items(), nb_matches):
        try:
            if all([odd >= minimum_odd_selection for odds in list(all_odds[match[0]]["odds"][site]
                                                                  for match in combine)
                    for odd in odds]):
                ALL_ODDS_COMBINE[" / ".join([match[0]
                                             for match
                                             in combine])] = cotes_combine_all_sites(*[match[1]
                                                                                       for match
                                                                                       in combine])
        except KeyError:
            pass
    odds_function = lambda best_odds, odds_site, i: ((best_odds[:i]+[odds_site[i]]
                                                      +best_odds[i+1:]) if not one_site
                                                     else odds_site)
    profit_function = lambda odds_to_check, i: (gain(odds_to_check, bet)-bet if one_site
                                                else gain2(odds_to_check, i, bet))
    criteria = lambda odds_to_check, i: ((not one_site and odds_to_check[i] >= minimum_odd)
                                         or (one_site and all(odd >= minimum_odd for
                                                              odd in odds_to_check)))
    display_function = lambda best_overall_odds, best_rank: (mises2(best_overall_odds, bet,
                                                                    best_rank, True) if not one_site
                                                             else mises(best_overall_odds, bet,
                                                                        True))
    result_function = lambda best_overall_odds, best_rank: (mises2(best_overall_odds, bet,
                                                                   best_rank, False) if not one_site
                                                            else mises(best_overall_odds, bet,
                                                                       False))
    best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport, date_max, time_max, date_min,
                    time_min, True, nb_matches)

def best_matches_combine_cashback_une_selection_perdante(site, cote_minimale_selection, combi_max=0,
                                                         nb_matches=2, date_max=None, time_max=None,
                                                         date_min=None, time_min=None):
    """
    Calcule la meilleure combinaison de matches et les mises à jouer pour une promotion du type
    "Combiné remboursé si une seule selection perdante, sans limite du nombre de paris remboursés"
    """
    global ALL_ODDS_COMBINE
    global MAIN_ODDS
    global ODDS_NBA
    sport = "football"
    bet = 10000
    all_odds = MAIN_ODDS
    ALL_ODDS_COMBINE = {}
    for combine in combinations(all_odds.items(), nb_matches):
        try:
            if all([odd >= cote_minimale_selection for odds in list(all_odds[match[0]]["odds"][site]
                                                                    for match in combine)
                    for odd in odds]):
                ALL_ODDS_COMBINE[" / ".join([match[0]
                                             for match
                                             in combine])] = cotes_combine_all_sites(*[match[1]
                                                                                       for match
                                                                                       in combine])
        except KeyError:
            pass
    odds_function = lambda best_odds, odds_site, i: list(map(lambda x: x*(1+combi_max)-combi_max,
                                                             odds_site))
    profit_function = lambda odds_to_check, i: gain(odds_to_check, bet)-bet
    criteria = lambda odds_to_check, i: (odds_to_check[i]+combi_max)/(1+combi_max) >= 1.1
    display_function = lambda x, i: mises(x, bet, True)
    return_function = lambda x, i: mises(x, bet, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    return_function, site, sport, date_max, time_max, date_min,
                    time_min, True, nb_matches, one_site=True, recalcul=True)

def best_matches_combine_cashback(site, minimum_odd, bet, sport="football",
                                  freebet=True, combi_max=0, rate_cashback=1,
                                  nb_matches=2, date_max=None, time_max=None,
                                  date_min=None, time_min=None):
    """
    Calcule la répartition des mises lorsqu'un unique combiné est remboursé s'il est perdant
    """
    global ALL_ODDS_COMBINE
    global MAIN_ODDS
    global ODDS_NBA
    global ODDS_TENNIS
    global ODDS_HANDBALL
    all_odds = (MAIN_ODDS if sport == "football"
                else (ODDS_TENNIS if sport == "tennis"
                      else (ODDS_HANDBALL if sport == "handball"
                            else ODDS_NBA)))
    ALL_ODDS_COMBINE = {}
    for combine in combinations(all_odds.items(), nb_matches):
        ALL_ODDS_COMBINE[" / ".join([match[0]
                                     for match
                                     in combine])] = cotes_combine_all_sites(*[match[1]
                                                                               for match
                                                                               in combine])
    odds_function = lambda best_odds, odds_site, i: (best_odds[:i]
                                                     +[odds_site[i]*(1+combi_max)-combi_max]
                                                     +best_odds[i+1:])
    profit_function = lambda odds_to_check, i: gain_pari_rembourse_si_perdant(odds_to_check, bet, i,
                                                                              freebet,
                                                                              rate_cashback)
    criteria = lambda odds_to_check, i: (odds_to_check[i]+combi_max)/(1+combi_max) >= minimum_odd
    display_function = lambda x, i: mises_pari_rembourse_si_perdant(x, bet, i, freebet,
                                                                    rate_cashback, True)
    return_function = lambda x, i: mises_pari_rembourse_si_perdant(x, bet, i, freebet,
                                                                   rate_cashback, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    return_function, site, sport, date_max, time_max, date_min,
                    time_min, True, nb_matches)


def best_matches_freebet(main_sites, freebets):
    """
    Compute of best way to bet freebets following the model
    [[bet, bookmaker], ...]
    """
    second_sites = {freebet[1] for freebet in freebets}
    if not second_sites:
        print("Veuillez sélectionner des freebets secondaires")
        return
    new_odds = MAIN_ODDS
    all_odds = {}
    for match in new_odds:
        if (not(any([site not in new_odds[match]["odds"].keys() for site in main_sites])
                or any([site not in new_odds[match]["odds"].keys() for site in second_sites]))):
            if new_odds[match]["odds"]:
                all_odds[match] = new_odds[match]
    best_rate = 0
    nb_matches = 2
    n = 3**nb_matches
    nb_freebets = len(freebets)
    all_odds_combine = {}
    combis = list(combinations(all_odds.items(), nb_matches))
    nb_combis = len(combis)
    progress = 10
    start = time.time()
    for i, combine in enumerate(combis):
        if i == 20:
            print("appr. time to wait:", int((time.time()-start)*nb_combis/20), "s")
        if i/nb_combis*100 > progress:
            print(str(progress)+"%")
            progress += 10
        match_combine = " / ".join([match[0] for match in combine])
        all_odds_combine[match_combine] = cotes_combine_all_sites(*[match[1] for match in combine],
                                                                  freebet=True)
        main_sites_distribution = [main_sites[0] for _ in range(n)]
        main_site_odds = cotes_freebet(
            cotes_combine([combine[x][1]['odds'][main_sites[0]]
                           for x in range(nb_matches)]))
        main_site_odds = all_odds_combine[match_combine]["odds"][main_sites[0]]
        for main in main_sites[1:]:
            potential_odds = all_odds_combine[match_combine]["odds"][main]
            for j, odd in enumerate(potential_odds):
                if odd > main_site_odds[j]:
                    main_site_odds[j] = odd
                    main_sites_distribution[j] = main
        second_odds = {second_site:all_odds_combine[match_combine]["odds"][second_site]
                       for second_site in second_sites}
        dict_combine_odds = copy.deepcopy(second_odds)
        for perm in permutations(range(n), nb_freebets):
            defined_second_sites = [[perm[i], freebet[0], freebet[1]]
                                    for i, freebet in enumerate(freebets)]
            defined_bets_temp = defined_bets(main_site_odds, dict_combine_odds,
                                             main_sites_distribution,
                                             defined_second_sites)
            if defined_bets_temp[0]/np.sum(defined_bets_temp[1]) > best_rate:
                best_rate = defined_bets_temp[0]/np.sum(defined_bets_temp[1])
                best_combine = combine
                best_bets = defined_bets_temp
    print("Temps d'exécution =", time.time()-start)
    best_match_combine = " / ".join([match[0] for match in best_combine])
    odds_best_match = copy.deepcopy(all_odds_combine[best_match_combine])
    all_sites = main_sites+list(second_sites)
    for site in all_odds_combine[best_match_combine]["odds"]:
        if site not in all_sites:
            del odds_best_match["odds"][site]
    print(best_match_combine)
    pprint(odds_best_match, compact=1)
    print("Taux =", best_rate)
    print("Gain référence =", best_bets[0])
    print("Somme des mises =", np.sum(best_bets[1]))
    afficher_mises_combine([x[0] for x in best_combine], best_bets[2], best_bets[1],
                           all_odds_combine[best_match_combine]["odds"], "football",
                           uniquement_freebet=True)

def best_matches_freebet_one_site(site, freebet, sport="football", nb_matches=2,
                                  minimum_odd=1.1, date_max=None, time_max=None,
                                  date_min=None, time_min=None):
    """
    Calcule la répartition des paris gratuits sur un unique site
    """
    global ALL_ODDS_COMBINE
    all_odds = (MAIN_ODDS if sport == "football"
                else (ODDS_TENNIS if sport == "tennis"
                      else (ODDS_HANDBALL if sport == "handball"
                            else ODDS_NBA)))
    ALL_ODDS_COMBINE = {}
    for combine in combinations(all_odds.items(), nb_matches):
        ALL_ODDS_COMBINE[" / ".join([match[0]
                                     for match
                                     in combine])] = cotes_combine_all_sites(*[match[1]
                                                                               for match
                                                                               in combine])
    odds_function = lambda best_odds, odds_site, i: cotes_freebet(odds_site)
    profit_function = lambda odds_to_check, i: gain(odds_to_check, freebet)-freebet
    criteria = lambda odds_to_check, i: all(odd >= minimum_odd for odd in odds_to_check)
    display_function = lambda best_overall_odds, best_rank: mises(best_overall_odds, freebet, True)
    result_function = lambda best_overall_odds, best_rank: mises(best_overall_odds, freebet, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport, date_max, time_max, date_min,
                    time_min, True, nb_matches, True, one_site=True)


def add_names_to_db(competition, sport, *sites):
    """
    Ajoute à la base de données les noms d'équipe/joueur pour une competition donnée sur tous les
    sites
    """
    id_competition = get_competition_id(competition, sport)
    if competition == sport:
        import_teams_by_sport(sport)
    else:
        import_teams_by_url("http://www.comparateur-de-cotes.fr/comparateur/"+sport+"/a-ed"
                            +str(id_competition))
    if not sites:
        sites = ['betclic', 'betstars', 'bwin', 'netbet', 'parionssport', 'pasinobet', 'pmu',
                 'unibet', 'winamax']
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    for site in sites:
        print(site)
        url = get_competition_url(competition, sport, site)
        if url:
            try:
                parse_and_add_to_db(site, sport, url)
            except KeyboardInterrupt:
                pass
            except urllib.error.URLError:
                print("Site non accessible (délai écoulé)")
    if selenium_required:
        selenium_init.DRIVER.quit()
