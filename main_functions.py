#!/usr/bin/env python3
"""
Fonctions principales d'assistant de paris
"""

from pprint import pprint
from copy import deepcopy
import urllib
import urllib.error
import datetime
import time
from itertools import combinations, permutations, product, chain
import inspect
import unidecode
import numpy as np
try:
    from win10toast import ToastNotifier
except ModuleNotFoundError:
    import subprocess
from bs4 import BeautifulSoup
import selenium_init
from bet_functions import (merge_dicts, gain2, mises2, gain, mises,
                           mises_freebet, gain_pari_rembourse_si_perdant,
                           mises_pari_rembourse_si_perdant, cotes_freebet,
                           cotes_combine_all_sites, cotes_combine,
                           afficher_mises_combine)
from database import (find_competition, get_id_formated_competition_name,
                      get_competition_by_id, find_competition_id,
                      import_sport_teams_in_db, is_in_db_site,
                      import_teams_in_db, add_name_to_db, is_in_db,
                      find_closer_result, get_id_by_site, find_closer_result_2)
from parser_bookmakers import (valid_odds, format_team_names, merge_dict_odds,
                               parse_betclic, parse_betstars, parse_bwin,
                               parse_france_pari, parse_joa, parse_netbet,
                               parse_parionssport, parse_pasinobet, parse_pmu,
                               parse_unibet, parse_winamax, parse_zebet)



def parse_competition(competition, sport="football", *sites):
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
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = inspect.currentframe().f_back.f_code.co_name=="<module>" and (selenium_sites.intersection(sites) or not sites)
    if selenium_required:
        selenium_init.start_selenium()
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
    if inspect.currentframe().f_back.f_code.co_name=="<module>" and selenium_sites.intersection(sites):
        selenium_init.driver.quit()
    if inspect.currentframe().f_back.f_code.co_name=="<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])
    if len(sites)>1:
        res = format_team_names(res_parsing, sport)
        return valid_odds(merge_dict_odds(res), sport)
    return valid_odds(res_parsing[site], sport)

def parse_main_competitions(*sites):
    """
    Retourne les cotes des principaux championnats de football
    """
    competitions = ["france ligue 1", "angleterre premier league",
                    "espagne liga", "italie serie", "allemagne bundesliga",
                    "ligue des champions"]#, "qualif"]
#     competitions = ["angleterre premier league", "espagne liga", "italie serie",
#                     "allemagne bundesliga"]
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = inspect.currentframe().f_back.f_code.co_name=="<module>" and (selenium_sites.intersection(sites) or not sites)
    if selenium_required:
        selenium_init.start_selenium()
    list_odds = []
    for competition in competitions:
        list_odds.append(parse_competition(competition, "football", *sites))
        print()
    if inspect.currentframe().f_back.f_code.co_name=="<module>" and selenium_sites.intersection(sites):
        selenium_init.driver.quit()
    if inspect.currentframe().f_back.f_code.co_name=="<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])
    return merge_dicts(list_odds)

def parse_competitions(competitions, *sites):
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = inspect.currentframe().f_back.f_code.co_name=="<module>" and (selenium_sites.intersection(sites) or not sites)
    if selenium_required:
        selenium_init.start_selenium()
    list_odds = []
    for competition in competitions:
        list_odds.append(parse_competition(competition, "football", *sites))
        print()
    if selenium_required:
        selenium_init.driver.quit()
    if inspect.currentframe().f_back.f_code.co_name=="<module>":
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
    global main_odds
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = inspect.currentframe().f_back.f_code.co_name=="<module>" and (selenium_sites.intersection(sites) or not sites)
    if selenium_required:
        selenium_init.start_selenium()
    main_odds = parse_main_competitions(*sites)
    if selenium_required:
        selenium_init.driver.quit()
    if inspect.currentframe().f_back.f_code.co_name=="<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])

def parse_tennis(*sites):
    """
    Stocke les cotes des tournois de tennis en global
    """
    global odds_tennis
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = inspect.currentframe().f_back.f_code.co_name=="<module>" and (selenium_sites.intersection(sites) or not sites)
    if selenium_required:
        selenium_init.start_selenium()
    odds_tennis = parse_competition("tennis", "tennis", *sites)
    if selenium_required:
        selenium_init.driver.quit()
    if inspect.currentframe().f_back.f_code.co_name=="<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])

def parse_nba(*sites):
    """
    Stocke les cotes de la NBA en global
    """
    global odds_nba
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = inspect.currentframe().f_back.f_code.co_name=="<module>" and (selenium_sites.intersection(sites) or not sites)
    if selenium_required:
        selenium_init.start_selenium()
    odds_nba = parse_competition("nba", "basketball", *sites)
    if selenium_required:
        selenium_init.driver.quit()
    if inspect.currentframe().f_back.f_code.co_name=="<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])

def parse_handball(*sites):
    global odds_handball
    selenium_required = inspect.currentframe().f_back.f_code.co_name=="<module>" and (selenium_sites.intersection(sites) or not sites)
    if selenium_required:
        selenium_init.start_selenium()
    odds_handball = parse_competition("champions", "handball", *sites)
    if selenium_required:
        selenium_init.driver.quit()
    if inspect.currentframe().f_back.f_code.co_name=="<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])


def odds_match(match, sport="football"):
    """
    Retourne les cotes d'un match donné sur tous les sites de l'ARJEL
    """
    all_odds = main_odds if sport=="football" else odds_tennis if sport=="tennis" else odds_handball if sport=="handball" else odds_nba
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


def best_bets_match(match, site, bet, minimum_odd, sport="football"):
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
    best_odds = deepcopy(odds_site)
    best_profit = -float("inf")
    n = len(all_odds['odds'][site])
    best_sites = [site for _ in range(n)]
    best_i = 0
    for odds in all_odds['odds'].items():
        for i in range(n):
            if odds[1][i] > best_odds[i] and (odds[1][i]>=1.1 or odds[0]=="pmu"):
                best_odds[i] = odds[1][i]
                best_sites[i] = odds[0]
    for i in range(n):
        if odds_site[i]>=minimum_odd and (odds[1][i]>=1.1 or odds[0]=="pmu"):
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
            all_odds = all_odds_combine
        else:
            all_odds = main_odds if sport=="football" else odds_tennis if sport=="tennis" else odds_handball if sport=="handball" else odds_nba
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
            best_odds = deepcopy(odds_site)
            best_sites = [site for _ in range(n)]
            if not one_site:
                for odds in all_odds[match]['odds'].items():
                    for i in range(n):
                        if odds[1][i] > best_odds[i] and (odds[1][i]>=1.1 or odds[0]=="pmu"):
                            best_odds[i] = odds[1][i]
                            best_sites[i] = odds[0]
            for odd_i, site_i in zip(best_odds, best_sites):
                if (odd_i<1.1 and site_i != "pmu"):
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
            sum_almost_won = find_almost_won_matches(best_match, result_function(best_overall_odds, best_rank), sport)
            display_function = lambda x, i : mises(x, 10000*50/sum_almost_won, True)
            result_function = lambda x, i : mises(x, 10000*50/sum_almost_won, False)
            find_almost_won_matches(best_match, result_function(best_overall_odds, best_rank), sport, True)
        display_function(best_overall_odds, best_rank)
        afficher_mises_combine(best_match.split(" / "), [sites], [result_function(best_overall_odds, best_rank)], all_odds[best_match]["odds"], sport, best_rank if freebet else None, one_site and freebet, best_overall_odds)
    except UnboundLocalError:
        print("No match found")

def find_almost_won_matches(best_matches, mises, sport, output=False):
    matches = best_matches.split(" / ")
    opponents = []
    for match in matches:
        opponents_match = match.split(" - ")
        if sport not in ["tennis", "volleyball", "basketball", "nba"]:
            opponents_match.insert(1, "Nul")
        opponents.append(opponents_match)
    dict_almost_won = {}
    n = 2 + (sport not in ["tennis", "volleyball", "basketball", "nba"])
    for combinaison in product(*opponents):
        almost_won_combis = []
        for i in range(len(combinaison)):
            for j in range(n):
                combi = list(combinaison)
                if combi[i] == opponents[i][j]:
                    pass
                else:
                    combi[i] = opponents[i][j]
                    almost_won_combis.append(" / ".join(combi))
        dict_almost_won[" / ".join(combinaison)] = almost_won_combis
    list_combi = list(map(lambda x: " / ".join(x), product(*opponents)))
    dict_index_almost_won = {}
    for gagnant in dict_almost_won:
        dict_index_almost_won[gagnant] = list(map(lambda x: list_combi.index(x), dict_almost_won[gagnant]))
    if output:
        print("bonus min =", min(sum(mises[k] for k in list_index) for list_index in dict_index_almost_won.values()))
        print("bonus max =", max(sum(mises[k] for k in list_index) for list_index in dict_index_almost_won.values()))
    return max(sum(mises[k] for k in list_index) for list_index in dict_index_almost_won.values())


def best_match_under_conditions(site, minimum_odd, bet, sport="football",
                                 one_site=False, live=False, date_max=None,
                                 time_max=None, date_min=None, time_min=None):
    """
    Retourne le meilleur match sur lequel miser lorsqu'on doit miser une somme
    donnée à une cote donnée. Cette somme peut-être sur seulement une issue
    (one_site=False) ou bien répartie sur plusieurs issues d'un même match
    (one_site=True), auquel cas, chacune des côtes du match doivent respecter le
    critère de cote minimale.
    """
    odds_function = lambda best_odds, odds_site, i : (best_odds[:i]
                                 +[odds_site[i]*0.9 if live else odds_site[i]]
                                 +best_odds[i+1:]) if not one_site else (odds_site[:i]
                                 +[odds_site[i]*0.9 if live else odds_site[i]]
                                 +odds_site[i+1:])
    profit_function = lambda odds_to_check, i : gain(odds_to_check, bet)-bet if one_site else gain2(odds_to_check, i, bet)
    criteria = lambda odds_to_check, i : ((not one_site and odds_to_check[i] >= minimum_odd)
                                          or (one_site and all(odd>=minimum_odd for odd in odds_to_check)))
    display_function = lambda best_overall_odds, best_rank : mises2(best_overall_odds, bet, best_rank, True) if not one_site else mises(best_overall_odds, bet, True)
    result_function = lambda best_overall_odds, best_rank : mises2(best_overall_odds, bet, best_rank, False) if not one_site else mises(best_overall_odds, bet, False)
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
    odds_function = lambda best_odds, odds_site, i : odds_site
    profit_function = lambda odds_to_check, i : gain2(odds_to_check, np.argmax(odds_to_check), bet)
    criteria = lambda odds_to_check, i : all(odd>=minimum_odd for odd in odds_to_check)
    display_function = lambda best_overall_odds, best_rank : mises2(best_overall_odds, bet, np.argmax(best_overall_odds), True)
    result_function = lambda best_overall_odds, best_rank : mises2(best_overall_odds, bet, np.argmax(best_overall_odds), False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport, date_max, time_max, date_min,
                    time_min, one_site=True)

def best_match_freebet(site, freebet, sport="football", date_max=None, time_max=None, date_min=None,
                    time_min=None):
    """
    Retourne le match qui génère le meilleur gain pour un unique freebet placé,
    couvert avec de l'argent réel.
    """
    odds_function = lambda best_odds, odds_site, i : (best_odds[:i]
                                     +[odds_site[i]-1]+best_odds[i+1:])
    profit_function = lambda odds_to_check, i : gain2(odds_to_check, i)+1
    criteria = lambda odds_to_check, i : True
    display_function = lambda x, i : mises_freebet(x[:i]+[x[i]+1]+x[i+1:], freebet, i, True)
    result_function = lambda x, i : mises_freebet(x[:i]+[x[i]+1]+x[i+1:], freebet, i, False)
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
                                +[combi_odd*odds_site[i]*(1+combi_max)-combi_max]
                                +best_odds[i+1:])
    profit_function = lambda odds_to_check, i : gain_pari_rembourse_si_perdant(odds_to_check, bet, i,
                                                       freebet, rate_cashback)
    criteria = lambda odds_to_check, i : (odds_to_check[i]+combi_max)/(1+combi_max) >= minimum_odd
    display_function = lambda x, i : mises_pari_rembourse_si_perdant(x, bet, i, freebet,
                                         rate_cashback, True)
    result_function = lambda x, i : mises_pari_rembourse_si_perdant(x, bet, i, freebet,
                                         rate_cashback, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport, date_max, time_max, date_min,
                    time_min)


def best_matches_combine(site, minimum_odd, bet,sport, nb_matches=2, one_site=False,
                         date_max=None, time_max=None, date_min=None, time_min=None, minimum_odd_selection=1.01):
    """
    Given a bookmaker, return on which matches you should share your freebet to
    maximize your gain
    """
    global all_odds_combine
    global main_odds
    global odds_nba
    global odds_tennis
    global odds_handball
    all_odds = main_odds if sport=="football" else odds_tennis if sport=="tennis" else odds_handball if sport=="handball" else odds_nba
    best_rate = -float('inf')
    all_odds_combine = {}
    for combine in combinations(all_odds.items(), nb_matches):
        try:
            if all([odd>=minimum_odd_selection for odds in list(all_odds[match[0]]["odds"][site] for match in combine) for odd in odds]):
                all_odds_combine[" / ".join([match[0] for match in combine])] = cotes_combine_all_sites(*[match[1] for match in combine])
        except KeyError:
            pass
    odds_function = lambda best_odds, odds_site, i : (best_odds[:i]
                                 +[odds_site[i]]
                                 +best_odds[i+1:]) if not one_site else odds_site
    profit_function = lambda odds_to_check, i : gain(odds_to_check, bet)-bet if one_site else gain2(odds_to_check, i, bet)
    criteria = lambda odds_to_check, i : ((not one_site and odds_to_check[i] >= minimum_odd)
                                          or (one_site and all(odd>=minimum_odd for odd in odds_to_check)))
    display_function = lambda best_overall_odds, best_rank : mises2(best_overall_odds, bet, best_rank, True) if not one_site else mises(best_overall_odds, bet, True)
    result_function = lambda best_overall_odds, best_rank : mises2(best_overall_odds, bet, best_rank, False) if not one_site else mises(best_overall_odds, bet, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport, date_max, time_max, date_min,
                    time_min, True, nb_matches)

def best_matches_combine_cashback_une_selection_perdante(site, cote_minimale_selection,
                                  freebet=True, combi_max=0, nb_matches=2,
                                  date_max=None, time_max=None, date_min=None,
                                  time_min=None):
    global all_odds_combine
    global main_odds
    global odds_nba
    sport = "basketball"
    bet = 10000
    all_odds = odds_nba
    best_rate = -float('inf')
    all_odds_combine = {}
    one_site = False
    for combine in combinations(all_odds.items(), nb_matches):
        try:
            if all([odd>=cote_minimale_selection for odds in list(all_odds[match[0]]["odds"][site] for match in combine) for odd in odds]):
                all_odds_combine[" / ".join([match[0] for match in combine])] = cotes_combine_all_sites(*[match[1] for match in combine])
        except KeyError:
            pass
    odds_function = lambda best_odds, odds_site, i: list(map(lambda x:x*(1+combi_max)-combi_max, odds_site))
    profit_function = lambda odds_to_check, i : gain(odds_to_check, bet)-bet
    criteria = lambda odds_to_check, i : (odds_to_check[i]+combi_max)/(1+combi_max) >= 1.1
    display_function = lambda x, i : mises(x, bet, True)
    return_function = lambda x, i : mises(x, bet, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    return_function, site, sport, date_max, time_max, date_min,
                    time_min, True, nb_matches, one_site=True, recalcul=True)

def best_matches_combine_cashback(site, minimum_odd, bet, sport="football",
                                  freebet=True, combi_max=0, rate_cashback=1,
                                  nb_matches=2, date_max=None, time_max=None,
                                  date_min=None, time_min=None):
    global all_odds_combine
    global main_odds
    global odds_nba
    global odds_tennis
    all_odds = main_odds if sport=="football" else odds_tennis if sport=="tennis" else odds_nba
    best_rate = -float('inf')
    all_odds_combine = {}
    one_site = False
    for combine in combinations(all_odds.items(), nb_matches):
        all_odds_combine[" / ".join([match[0] for match in combine])] = cotes_combine_all_sites(*[match[1] for match in combine])
    odds_function = lambda best_odds, odds_site, i: (best_odds[:i]
                                +[odds_site[i]*(1+combi_max)-combi_max]
                                +best_odds[i+1:])
    profit_function = lambda odds_to_check, i : gain_pari_rembourse_si_perdant(odds_to_check, bet, i,
                                                       freebet, rate_cashback)
    criteria = lambda odds_to_check, i : (odds_to_check[i]+combi_max)/(1+combi_max) >= minimum_odd
    display_function = lambda x, i : mises_pari_rembourse_si_perdant(x, bet, i, freebet,
                                         rate_cashback, True)
    return_function = lambda x, i : mises_pari_rembourse_si_perdant(x, bet, i, freebet,
                                         rate_cashback, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    return_function, site, sport, date_max, time_max, date_min,
                    time_min, True, nb_matches)


def defined_bets(odds_main, odds_second, main_sites, second_sites):
    """
    second_sites type : [[rank, bet, site],...]
    """
    if second_sites:
        sites = deepcopy(main_sites)
#         print(odds)
        odds_adapted = deepcopy(odds_main)
        for bet in second_sites:
            odds_adapted[bet[0]] = odds_second[bet[2]][bet[0]]
            sites[bet[0]] = bet[2]
        for bet in second_sites:
            valid = True
            bets = mises2(odds_adapted, bet[1], bet[0])
            gain_freebets = bet[1]*odds_adapted[bet[0]]
            for bet2 in second_sites:
                if bets[bet2[0]] > bet2[1]:
                    valid = False
                    break
            if valid:
                break
        for i, elem in enumerate(second_sites):
            second_sites[i][1] -= bets[elem[0]]
            if elem[1] < 1e-6:
                i_0 = i
        del second_sites[i_0]
        res = defined_bets(odds_main, odds_second, main_sites, second_sites)
        return [gain_freebets+res[0], [bets]+res[1], [sites]+res[2]]
    return [0, [], []]

def best_matches_freebet(main_sites, freebets):
    """
    Compute of best way to bet freebets following the model
    [[bet, bookmaker], ...]
    """
    second_sites = {freebet[1] for freebet in freebets}
    if not second_sites:
        print("Veuillez sélectionner des freebets secondaires")
        return
    new_odds = main_odds
    all_odds = {}
    for match in new_odds:
        if not(any([site not in new_odds[match]["odds"].keys() for site in main_sites]) or any([site not in new_odds[match]["odds"].keys() for site in second_sites])):
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
        all_odds_combine[match_combine] = cotes_combine_all_sites(*[match[1] for match in combine], freebet=True)
        main_sites_distribution = [main_sites[0] for _ in range(n)]
        main_site_odds = cotes_freebet(
            cotes_combine([combine[x][1]['odds'][main_sites[0]]
                           for x in range(nb_matches)]))
        main_site_odds = all_odds_combine[match_combine]["odds"][main_sites[0]]
        for main in main_sites[1:]:
            potential_odds = all_odds_combine[match_combine]["odds"][main]
            for j, odd in enumerate(potential_odds):
                if odd>main_site_odds[j]:
                    main_site_odds[j] = odd
                    main_sites_distribution[j] = main
        second_odds = {second_site:all_odds_combine[match_combine]["odds"][second_site] for second_site in second_sites}
        dict_combine_odds = deepcopy(second_odds)
        for perm in permutations(range(n), nb_freebets):
            defined_second_sites = [[perm[i], freebet[0], freebet[1]]
                                    for i, freebet in enumerate(freebets)]
            copy_second_sites = deepcopy(defined_second_sites)
            defined_bets_temp = defined_bets(main_site_odds, dict_combine_odds,
                                             main_sites_distribution,
                                             defined_second_sites)
            if defined_bets_temp[0]/np.sum(defined_bets_temp[1]) > best_rate:
                best_rate = defined_bets_temp[0]/np.sum(defined_bets_temp[1])
                best_combine = combine
                best_bets = defined_bets_temp
                best_defined_second_sites = copy_second_sites
                best_dict_combine_odds = dict_combine_odds
    print("Temps d'exécution =", time.time()-start)
    best_match_combine = " / ".join([match[0] for match in best_combine])
    odds_best_match = deepcopy(all_odds_combine[best_match_combine])
    all_sites = main_sites+list(second_sites)
    for site in all_odds_combine[best_match_combine]["odds"]:
        if site not in all_sites:
            del odds_best_match["odds"][site]
    print(best_match_combine)
    pprint(odds_best_match, compact=1)
    print("Taux =", best_rate)
    print("Gain référence =", best_bets[0])
    print("Somme des mises =", np.sum(best_bets[1]))
    afficher_mises_combine([x[0] for x in best_combine], best_bets[2], best_bets[1], all_odds_combine[best_match_combine]["odds"], "football", uniquement_freebet=True)

def best_matches_freebet_one_site(site, freebet, sport="football", nb_matches=2,
                                  minimum_odd=1.1, date_max=None, time_max=None,
                                  date_min=None, time_min=None):
    global all_odds_combine
    global main_odds
    global odds_nba
    global odds_tennis
    all_odds = main_odds if sport=="football" else odds_tennis if sport=="tennis" else odds_nba
    best_rate = -float('inf')
    all_odds_combine = {}
    for combine in combinations(all_odds.items(), nb_matches):
        all_odds_combine[" / ".join([match[0] for match in combine])] = cotes_combine_all_sites(*[match[1] for match in combine])
    odds_function = lambda best_odds, odds_site, i : cotes_freebet(odds_site)
    profit_function = lambda odds_to_check, i : gain(odds_to_check, freebet)-freebet
    criteria = lambda odds_to_check, i : all(odd>=minimum_odd for odd in odds_to_check)
    display_function = lambda best_overall_odds, best_rank : mises(best_overall_odds, freebet, True)
    result_function = lambda best_overall_odds, best_rank : mises(best_overall_odds, freebet, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport, date_max, time_max, date_min,
                    time_min, True, nb_matches, True, one_site=True)

def add_names_to_db_complete(site, sport, competition):
    if ("http" in competition or "tennis" in competition
        or "europa" in competition or "ldc" in competition
        or "élim" in competition or "handball" in competition):
        url = competition
    else:
        return
    odds = eval("parse_{}(url)".format(site))
    matches = odds.keys()
    teams = list(set(chain.from_iterable(list(map(lambda x: x.split(" - "), list(matches))))))
    print(teams)
    teams_not_in_db_site = []
    teams_1st_round = []
    teams_2nd_round = []
    teams_3rd_round = []
    teams_4th_round = []
    teams_5th_round = []
    for team in teams:
        line = is_in_db_site(team, sport, site)
        if line:
            add_name_to_db(line[0], team, site)
        else:
            teams_not_in_db_site.append(team)
    print(teams_not_in_db_site)
    for team in teams_not_in_db_site:
        line = is_in_db(team, sport)
        if line:
            add_name_to_db(line[0], team, site)
        else:
            teams_1st_round.append(team)
    print(teams_1st_round)
    for team in teams_1st_round:
        line = find_closer_result(team, sport, site)
        if line:
            add_name_to_db(line[0], team, site)
        else:
            teams_2nd_round.append(team)
    print(teams_2nd_round)
    for team in teams_2nd_round:
        future_opponents, future_matches = get_future_opponnents(team, matches)
        found = False
        for future_opponent, future_match in zip(future_opponents, future_matches):
            id_opponent = get_id_by_site(future_opponent, sport, site)
            id_to_find = get_id_by_opponent(id_opponent, future_match, odds)
            if id_to_find:
                found = True
                add_name_to_db(id_to_find, team, site)
        if not found:
            teams_3rd_round.append(team)
    print(teams_3rd_round)
    for team in teams_3rd_round:
        line = find_closer_result_2(team, sport, site)
        if line:
            add_name_to_db(line[0], team, site)
        else:
            teams_4th_round.append(team)
    print(teams_4th_round)
    for team in teams_4th_round:
        future_opponents, future_matches = get_future_opponnents(team, matches)
        found = False
        for future_opponent, future_match in zip(future_opponents, future_matches):
            id_opponent = get_id_by_site(future_opponent, sport, site)
            id_to_find = get_id_by_opponent(id_opponent, future_match, odds)
            if id_to_find:
                found = True
                add_name_to_db(id_to_find, team, site)
        if not found:
            teams_5th_round.append(team)
    print(teams_5th_round)

def get_future_opponnents(name, matches):
    future_opponents = []
    future_matches = []
    for match in matches:
        if name in match:
            future_matches.append(match)
            opponents = match.split(" - ")
            try:
                opponents.remove(name)
                future_opponents.append(opponents[0])
            except ValueError:
                pass
            except IndexError:
                pass
    return future_opponents, future_matches

def get_id_by_opponent(id_opponent, name_site_match, matches):
        url = "http://www.comparateur-de-cotes.fr/comparateur/football/Nice-td"+str(id_opponent)
        date_match = matches[name_site_match]["date"]
        soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
        get_next_id = False
        for line in soup.find_all(["a", "table"]):
            if get_next_id and "class" in line.attrs and "otn" in line["class"]:
                if line["href"].split("-td")[1]!=str(id_opponent):
                    return line["href"].split("-td")[1]
            if "class" in line.attrs and "bettable" in line["class"]:
                for string in list(line.stripped_strings):
                    if "à" in string:
                        date_time = datetime.datetime.strptime(string.lower(), "%A %d %B %Y à %Hh%M")
                        try:
                            if abs(date_time-date_match)<datetime.timedelta(days=2):
                                get_next_id = True
                        except TypeError: #live
                            pass
        return



def add_names_to_db_all_sites(competition, sport, *sites):
    id_competition = find_competition_id(competition, sport)
    if competition==sport:
        import_sport_teams_in_db(sport)
    else:
        import_teams_in_db("http://www.comparateur-de-cotes.fr/comparateur/"+sport+"/a-ed"+str(id_competition))
    if not sites:
        sites = ['betclic', 'betstars', 'bwin', 'netbet', 'parionssport', 'pasinobet', 'pmu', 'unibet', 'winamax']
    selenium_sites = {"betstars", "bwin", "parionssport", "pasinobet", "unibet"}
    selenium_required = inspect.currentframe().f_back.f_code.co_name=="<module>" and (selenium_sites.intersection(sites) or not sites)
    if selenium_required:
        selenium_init.start_selenium()
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
    if selenium_required:
        selenium_init.driver.quit()

