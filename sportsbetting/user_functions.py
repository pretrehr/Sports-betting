#!/usr/bin/env python3
"""
Fonctions principales d'assistant de paris
"""


from pprint import pprint
import inspect
import urllib
import urllib.error
import copy
import time
import sqlite3
from itertools import combinations, permutations
import urllib3
import numpy as np
import unidecode
import selenium
from bs4 import BeautifulSoup
try:
    from win10toast import ToastNotifier
except ImportError:
    import subprocess
import sportsbetting
from sportsbetting import selenium_init
from sportsbetting.database_functions import (get_id_formated_competition_name,
                                              get_competition_by_id, get_competition_url,
                                              import_teams_by_sport, import_teams_by_url)
from sportsbetting.parser_functions import parse_and_add_to_db, parse, parse_buteurs_betclic, parse_buteurs_betclic_match
from sportsbetting.auxiliary_functions import (valid_odds, format_team_names, merge_dict_odds,
                                               merge_dicts, afficher_mises_combine,
                                               cotes_combine_all_sites, defined_bets,
                                               best_match_base, generate_sites)
from sportsbetting.basic_functions import (gain2, mises2, gain, mises, mises_freebet, cotes_freebet,
                                           gain_pari_rembourse_si_perdant, gain_freebet2,
                                           mises_freebet2, mises_pari_rembourse_si_perdant,
                                           cotes_combine, gain_promo_gain_cote,
                                           mises_promo_gain_cote, cote_boostee,
                                           gain_gains_nets_boostes, mises_gains_nets_boostes)
from sportsbetting.parser_promotions import (get_promotions_betclic, get_promotions_france_pari,
                                             get_promotions_netbet, get_promotions_pmu,
                                             get_promotions_zebet, get_promotions_unibet,
                                             get_promotions_parionssport)

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
        return
    print(formated_name)
    if not sites:
        sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet',
                 'parionssport', 'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']
    selenium_sites = {"betstars", "bwin", "joa", "parionssport", "pasinobet", "unibet"}
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
                try:
                    res_parsing[site] = parse(site, url)
                except urllib3.exceptions.MaxRetryError:
                    selenium_init.DRIVER.quit()
                    print("Redémarrage de selenium")
                    selenium_init.start_selenium()
                    res_parsing[site] = parse(site, url)
        except urllib.error.URLError:
            print("Site non accessible (délai écoulé)")
        except KeyboardInterrupt:
            res_parsing[site] = {}
        except selenium.common.exceptions.TimeoutException:
            print("Element non trouvé par selenium")
        except sportsbetting.UnavailableCompetitionException:
            print("Compétition non disponible")
            break
#         sportsbetting.PROGRESS += 100/(len(sites)*sportsbetting.SUBPROGRESS_LIMIT)
    if selenium_required:
        selenium_init.DRIVER.quit()
    if inspect.currentframe().f_back.f_code.co_name == "<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])
#     if len(sites) > 1:
    res = format_team_names(res_parsing, sport)
    out = valid_odds(merge_dict_odds(res), sport)
#     else:
#         out = valid_odds(res_parsing[sites[0]], sport)
    if inspect.currentframe().f_back.f_code.co_name != "<module>":
        return out
    sportsbetting.ODDS[sport] = out


def parse_competitions(competitions, sport="football", *sites):
    """
    Retourne les cotes de plusieurs competitions
    """
    selenium_sites = {"betstars", "bwin", "joa", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name in ["<module>", "parse_thread"]
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    list_odds = []
    sportsbetting.PROGRESS = 0
    sportsbetting.SUBPROGRESS_LIMIT = len(competitions)
    for competition in competitions:
        list_odds.append(parse_competition(competition, sport, *sites))
        print()
    if selenium_required:
        selenium_init.DRIVER.quit()
#     if inspect.currentframe().f_back.f_code.co_name == "<module>":
#         try:
#             toaster = ToastNotifier()
#             toaster.show_toast("Sports-betting", "Fin du parsing")
#         except NameError:
#             subprocess.Popen(['notify-send', "Fin du parsing"])
#     if inspect.currentframe().f_back.f_code.co_name != "<module>":
#         return merge_dicts(list_odds)
    sportsbetting.ODDS[sport] = merge_dicts(list_odds)

def parse_competitions_site(competitions, sport, site):
    selenium_sites = {"betstars", "bwin", "joa", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name in ["<module>", "parse_thread"]
                         and site in selenium_sites)
    if selenium_required:
        selenium_init.start_selenium()
    list_odds = []
    for competition in competitions:
        list_odds.append(parse_competition(competition, sport, site))
        sportsbetting.PROGRESS += 100/(len(competitions)*sportsbetting.SUBPROGRESS_LIMIT)
    print()
    if selenium_required:
        selenium_init.DRIVER.quit()
    return merge_dict_odds(list_odds)

def parse_competitions2(competitions, sport="football", *sites):
    if not sites:
        sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet',
                    'parionssport', 'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']
    selenium_sites = {"betstars", "bwin", "joa", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name in ["<module>", "parse_thread"]
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    list_odds = []
    sportsbetting.PROGRESS = 0
    sportsbetting.SUBPROGRESS_LIMIT = len(sites)
    for site in sites:
        print(site)
        list_odds.append(parse_competitions_site(competitions, sport, site))
    if selenium_required:
        selenium_init.DRIVER.quit()
    sportsbetting.ODDS[sport] = merge_dict_odds(list_odds)
    


def parse_football(*sites):
    """
    Stocke les cotes des principaux championnats de football en global
    """
    selenium_sites = {"betstars", "bwin", "joa", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    competitions = ["france ligue 1", "angleterre premier league",
                    "espagne liga", "italie serie", "allemagne bundesliga",
                    "ligue des champions"]
    sportsbetting.ODDS["football"] = parse_competitions(competitions, "football", *sites)
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
    selenium_sites = {"betstars", "bwin", "joa", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    sportsbetting.ODDS["tennis"] = parse_competition("tennis", "tennis", *sites)
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
    selenium_sites = {"betstars", "bwin", "joa", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    sportsbetting.ODDS["nba"] = parse_competition("nba", "basketball", *sites)
    sportsbetting.ODDS["basketball"] = sportsbetting.ODDS["nba"]
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
    selenium_sites = {"betstars", "bwin", "joa", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    sportsbetting.ODDS["handball"] = parse_competition("champions", "handball", *sites)
    if selenium_required:
        selenium_init.DRIVER.quit()
    if inspect.currentframe().f_back.f_code.co_name == "<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])


def parse_nhl(*sites):
    """
    Stocke les cotes de NHL en global
    """
    selenium_sites = {"betstars", "bwin", "joa", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    sportsbetting.ODDS["nhl"] = parse_competition("nhl", "hockey-sur-glace", *sites)
    sportsbetting.ODDS["hockey-sur-glace"] = sportsbetting.ODDS["nhl"]
    if selenium_required:
        selenium_init.DRIVER.quit()
    if inspect.currentframe().f_back.f_code.co_name == "<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])


def parse_buteurs():
    """
    Stocke les cotes des duels de buteurs disponibles sur Betclic
    """
    competitions = ["france ligue 1", "espagne liga", "italie serie", "allemagne bundesliga"]
    competitions = ["laliga"]
    list_odds = []
    for competition in competitions:
        print(get_id_formated_competition_name(competition, "football")[1])
        url = get_competition_url(competition, "football", "betclic")
        list_odds.append(parse_buteurs_betclic(url))
    if inspect.currentframe().f_back.f_code.co_name == "<module>":
        try:
            toaster = ToastNotifier()
            toaster.show_toast("Sports-betting", "Fin du parsing")
        except NameError:
            subprocess.Popen(['notify-send', "Fin du parsing"])
    if inspect.currentframe().f_back.f_code.co_name != "<module>":
        return merge_dicts(list_odds)
    sportsbetting.ODDS["buteurs"] = merge_dicts(list_odds)

def parse_buteurs_match(url):
    sportsbetting.ODDS["buteurs"] = parse_buteurs_betclic_match(url)



def odds_match(match, sport="football"):
    """
    Retourne les cotes d'un match donné sur tous les sites de l'ARJEL
    """
    all_odds = sportsbetting.ODDS[sport]
    opponents = match.split('-')
    match_name = ""
    for match_name in all_odds:
        if (opponents[0].lower().strip() in unidecode.unidecode(match_name.split("-")[0].lower())
                and opponents[1].lower().strip() in unidecode.unidecode(match_name.split("-")[1]
                                                                        .lower())):
            break
    else:
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


def best_match_under_conditions(site, minimum_odd, bet, sport="football", date_max=None,
                                time_max=None, date_min=None, time_min=None, one_site=False,
                                live=False):
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


def best_match_freebet2(site, freebet, sport="football", live=False, date_max=None, time_max=None,
                        date_min=None, time_min=None):
    """
    Retourne le match qui génère le meilleur gain pour un unique freebet placé,
    couvert avec de l'argent réel.
    """
    fact_live = 1-0.2*live
    odds_function = lambda best_odds, odds_site, i: (best_odds[:i]+[odds_site[i]*fact_live-1]
                                                     +best_odds[i+1:])
    profit_function = lambda x, i: gain_freebet2(x[:i]+[x[i]+1]+x[i+1:], freebet, i)
    criteria = lambda odds_to_check, i: True
    display_function = lambda x, i: mises_freebet2(x[:i]+[x[i]+1]+x[i+1:], freebet, i, True)
    result_function = lambda x, i: mises_freebet2(x[:i]+[x[i]+1]+x[i+1:], freebet, i, False)
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


def best_matches_combine(site, minimum_odd, bet, sport="football", nb_matches=2, one_site=False,
                         date_max=None, time_max=None, date_min=None, time_min=None,
                         minimum_odd_selection=1.01):
    """
    Retourne les meilleurs matches sur lesquels miser lorsqu'on doit miser une somme
    donnée à une cote donnée sur un combiné
    """
    all_odds = sportsbetting.ODDS[sport]
    sportsbetting.ALL_ODDS_COMBINE = {}
    for combine in combinations(all_odds.items(), nb_matches):
        try:
            if all([odd >= minimum_odd_selection for odds in list(all_odds[match[0]]["odds"][site]
                                                                  for match in combine)
                    for odd in odds]):
                (sportsbetting
                 .ALL_ODDS_COMBINE[" / "
                                   .join([match[0]
                                          for match
                                          in combine])]) = cotes_combine_all_sites(*[match[1]
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
                    time_min, True, nb_matches, one_site=one_site)

def best_matches_combine_cashback_une_selection_perdante(site, cote_minimale_selection, combi_max=0,
                                                         nb_matches=2, date_max=None, time_max=None,
                                                         date_min=None, time_min=None):
    """
    Calcule la meilleure combinaison de matches et les mises à jouer pour une promotion du type
    "Combiné remboursé si une seule selection perdante, sans limite du nombre de paris remboursés"
    """
    sport = "football"
    bet = 10000
    all_odds = sportsbetting.ODDS[sport]
    sportsbetting.ALL_ODDS_COMBINE = {}
    for combine in combinations(all_odds.items(), nb_matches):
        try:
            if all([odd >= cote_minimale_selection for odds in list(all_odds[match[0]]["odds"][site]
                                                                    for match in combine)
                    for odd in odds]):
                (sportsbetting
                 .ALL_ODDS_COMBINE[" / "
                                   .join([match[0]
                                          for match
                                          in combine])]) = cotes_combine_all_sites(*[match[1]
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
    all_odds = sportsbetting.ODDS[sport]
    sportsbetting.ALL_ODDS_COMBINE = {}
    for combine in combinations(all_odds.items(), nb_matches):
        (sportsbetting
         .ALL_ODDS_COMBINE[" / "
                           .join([match[0]
                                  for match
                                  in combine])]) = cotes_combine_all_sites(*[match[1]
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

def best_match_stakes_to_bet(stakes,nb_matches=1, sport="football"):
    second_sites = {stake[1] for stake in stakes}
    main_sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet',
                  'parionssport', 'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']
    new_odds = sportsbetting.ODDS[sport]
    all_odds = {}
    for match in new_odds:
        if (not(any([site not in new_odds[match]["odds"].keys() for site in second_sites]))):
            if new_odds[match]["odds"]:
                all_odds[match] = new_odds[match]
    best_rate = 0
    best_profit = -sum(stake[0] for stake in stakes)
    n = 3**nb_matches
    nb_stakes = len(stakes)
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
        all_odds_combine[match_combine] = cotes_combine_all_sites(*[match[1] for match in combine])
        main_sites_distribution = [main_sites[0] for _ in range(n)]
        main_site_odds = copy.deepcopy(all_odds_combine[match_combine]["odds"][main_sites[0]])
        for main in main_sites[1:]:
            try:
                potential_odds = all_odds_combine[match_combine]["odds"][main]
                for j, odd in enumerate(potential_odds):
                    if odd > main_site_odds[j]:
                        main_site_odds[j] = odd
                        main_sites_distribution[j] = main
            except KeyError:
                pass
        second_odds = {second_site:all_odds_combine[match_combine]["odds"][second_site]
                       for second_site in second_sites}
        dict_combine_odds = copy.deepcopy(second_odds)
        for perm in permutations(range(n), nb_stakes):
            defined_second_sites = [[perm[i], stake[0], stake[1]]
                                    for i, stake in enumerate(stakes)]
            defined_bets_temp = defined_bets(main_site_odds, dict_combine_odds,
                                             main_sites_distribution,
                                             defined_second_sites)
            profit = defined_bets_temp[0] - np.sum(defined_bets_temp[1])
            if profit > best_profit:
                best_profit = profit
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
    print("Plus-value =", best_profit)
    print("Gain référence =", best_bets[0])
    print("Somme des mises =", np.sum(best_bets[1]))
    afficher_mises_combine([x[0] for x in best_combine], best_bets[2], best_bets[1],
                           all_odds_combine[best_match_combine]["odds"], "football")


def best_matches_freebet(main_sites, freebets, sport="football", *matches):
    """
    Compute of best way to bet freebets following the model
    [[bet, bookmaker], ...]
    """
    second_sites = {freebet[1] for freebet in freebets}
    if not second_sites:
        print("Veuillez sélectionner des freebets secondaires")
        return
    if matches:
        new_odds = {}
        for match in matches:
            match_name, odds = odds_match(match)
            new_odds[match_name] = odds
    else:
        new_odds = sportsbetting.ODDS[sport]
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
        main_site_odds = copy.deepcopy(all_odds_combine[match_combine]["odds"][main_sites[0]])
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
    all_odds = sportsbetting.ODDS[sport]
    sportsbetting.ALL_ODDS_COMBINE = {}
    for combine in combinations(all_odds.items(), nb_matches):
        (sportsbetting
         .ALL_ODDS_COMBINE[" / ".join([match[0]
                                       for match
                                       in combine])]) = cotes_combine_all_sites(*[match[1]
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

def best_match_gain_cote(site, bet, sport="football", date_max=None, time_max=None, date_min=None,
                         time_min=None):
    """
    Retourne le match sur lequel miser pour optimiser une promotion du type "gain de la cote gagnée"
    """
    odds_function = lambda best_odds, odds_site, i: best_odds[:i]+[odds_site[i]]+best_odds[i+1:]
    profit_function = lambda odds_to_check, i: gain_promo_gain_cote(odds_to_check, bet, i)
    criteria = lambda odds_to_check, i: True
    display_function = lambda best_overall_odds, best_rank: mises_promo_gain_cote(best_overall_odds,
                                                                                  bet, best_rank,
                                                                                  True)
    result_function = lambda best_overall_odds, best_rank: mises_promo_gain_cote(best_overall_odds,
                                                                                 bet, best_rank,
                                                                                 False)
    best_match_base(odds_function, profit_function, criteria, display_function, result_function,
                    site, sport, date_max, time_max, date_min, time_min)


def best_match_cotes_boostees(site, gain_max, sport="football", date_max=None, time_max=None,
                              date_min=None, time_min=None):
    odds_function = lambda best_odds, odds_site, i: odds_site
    profit_function = lambda odds_to_check, i : gain_gains_nets_boostes(odds_to_check, gain_max, False)
    criteria = lambda odds_to_check, i: odds_to_check[i]>=1.5
    display_function = lambda odds_to_check, i : mises_gains_nets_boostes(odds_to_check, gain_max, False, True)
    result_function = lambda odds_to_check, i : mises_gains_nets_boostes(odds_to_check, gain_max, False, False)
    best_match_base(odds_function, profit_function, criteria, display_function, result_function,
                    site, sport, date_max, time_max, date_min, time_min)

def add_names_to_db(competition, sport="football", *sites):
    """
    Ajoute à la base de données les noms d'équipe/joueur pour une competition donnée sur tous les
    sites
    """
    try:
        id_competition, formated_name = get_id_formated_competition_name(competition, sport)
    except TypeError:
        print("Competition inconnue")
        return {}
    print(formated_name)
    if competition == sport or "Tout le" in competition:
        import_teams_by_sport(sport)
    else:
        import_teams_by_url("http://www.comparateur-de-cotes.fr/comparateur/"+sport+"/a-ed"
                            +str(id_competition))
    if not sites:
        sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet', 'parionssport',
                 'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']
    selenium_sites = {"betstars", "bwin", "joa", "parionssport", "pasinobet", "unibet"}
    selenium_required = (inspect.currentframe().f_back.f_code.co_name == "<module>"
                         and (selenium_sites.intersection(sites) or not sites))
    if selenium_required:
        selenium_init.start_selenium()
    for site in sites:
        print(site)
        url = get_competition_url(competition, sport, site)
        if url:
            try:
                teams = parse_and_add_to_db(site, sport, url)
                if teams:
                    sportsbetting.TEAMS_NOT_FOUND.append(teams)
            except KeyboardInterrupt:
                print("Recommencez pour arrêter le parsing")
                time.sleep(1)
            except urllib3.exceptions.MaxRetryError:
                selenium_init.DRIVER.quit()
                print("Redémarrage de selenium")
                selenium_init.start_selenium()
                teams = parse_and_add_to_db(site, sport, url)
                if teams:
                    sportsbetting.TEAMS_NOT_FOUND.append(teams)
            except selenium.common.exceptions.TimeoutException:
                pass
            except urllib.error.HTTPError:
                pass
    if selenium_required:
        selenium_init.DRIVER.quit()

def update_all_database(start="", *sites):
    """
    Ajoute les noms manquants dans toute la base de données
    """
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
    c = conn.cursor()
    c.execute("""
    SELECT sport, competition FROM competitions
    """)
    if start:
        start_found = False
    else:
        start_found = True
    selenium_init.start_selenium()
    for line in c.fetchall():
        try:
            if start in line[1]:
                start_found = True
            if start_found:
                add_names_to_db(line[1], line[0], *sites)
        except KeyboardInterrupt:
            pass
        except sportsbetting.UnavailableCompetitionException:
            pass
    selenium_init.DRIVER.quit()


def add_competition_to_db(sport):
    """
    Ajout des competitions d'un sport donné disponibles sur comparateur-de-cotes
    """
    url = "http://www.comparateur-de-cotes.fr/comparateur/"+sport
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
    c = conn.cursor()
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    sport = soup.find("title").string.split()[-1].lower()
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "-ed" in line["href"] and line.text and sport in line["href"]:
            try:
                c.execute("""
                INSERT INTO competitions (id, competition, sport)
                VALUES ({}, "{}", "{}")
                """.format(line["href"].split("-ed")[-1], line.text.strip(), sport))
                print(line.text.strip())
            except sqlite3.IntegrityError:
                pass
    conn.commit()
    c.close()


def add_urls_to_db():
    """
    Complète les url France-pari et ZEbet manquants à partir des url NetBet existants
    """
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
    c = conn.cursor()
    c.execute("""
    SELECT url_netbet
    FROM competitions 
    WHERE ((url_zebet ISNULL OR url_france_pari ISNULL) AND url_netbet IS NOT NULL)
    """)
    for line in c.fetchall():
        try:
            url_netbet = line[0]
            url_france_pari, url_zebet = generate_sites(url_netbet)
            c_2 = conn.cursor()
            c_2.execute("""
            UPDATE competitions
            SET url_france_pari = "{0}" WHERE url_netbet = "{1}"
            """.format(url_france_pari, url_netbet))
            c_3 = conn.cursor()
            c_3.execute("""
            UPDATE competitions
            SET url_zebet = "{0}" WHERE url_netbet = "{1}"
            """.format(url_zebet, url_netbet))
            c_2.close()
            c_3.close()
        except TypeError:
            pass
    conn.commit()
    c.close()


def get_promotions(site):
    exec("get_promotions_"+site+"()")
