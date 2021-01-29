#!/usr/bin/env python3
"""
Fonctions principales d'assistant de paris
"""

import colorama
import copy
import inspect
import socket
import sqlite3
import sys
import termcolor
import time
import traceback
import urllib
import urllib.error
import urllib.request
from itertools import combinations, permutations
from pprint import pprint

import numpy as np
import selenium
import selenium.common
import unidecode
import urllib3
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool
import sportsbetting as sb
from sportsbetting import selenium_init
from sportsbetting.database_functions import (get_id_formatted_competition_name, get_competition_by_id, import_teams_by_url,
                                              import_teams_by_sport, import_teams_by_competition_id_thesportsdb)
from sportsbetting.parser_functions import parse
from sportsbetting.auxiliary_functions import (valid_odds, format_team_names, merge_dict_odds, afficher_mises_combine,
                                               cotes_combine_all_sites, defined_bets, binomial, best_match_base,
                                               filter_dict_dates, get_nb_issues, best_combine_reduit, filter_dict_minimum_odd)
from sportsbetting.basic_functions import (gain2, mises2, gain, mises, mises_freebet, cotes_freebet,
                                           gain_pari_rembourse_si_perdant, gain_freebet2, mises_freebet2,
                                           mises_pari_rembourse_si_perdant, gain_promo_gain_cote, mises_promo_gain_cote,
                                           gain_gains_nets_boostes, mises_gains_nets_boostes, gain3, mises3)
from sportsbetting.lambda_functions import get_best_odds, get_profit


def parse_competition(competition, sport="football", *sites):
    """
    Retourne les cotes d'une competition donnée pour un ou plusieurs sites de
    paris. Si aucun site n'est choisi, le parsing se fait sur l'ensemble des
    bookmakers reconnus par l'ARJEL
    """
    if sb.ABORT:
        raise sb.AbortException
    try:
        _id, formatted_name = get_id_formatted_competition_name(competition, sport)
    except TypeError:
        print("Competition inconnue")
        return
    print(formatted_name, *sites)
    if not sites:
        sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet',
                 'parionssport', 'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']
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
                    selenium_init.DRIVER[site].quit()
                    print("Redémarrage de selenium")
                    selenium_init.start_selenium(site, timeout=20)
                    res_parsing[site] = parse(site, url)
                except sqlite3.OperationalError:
                    print("Erreur dans la base de données, redémarrage en cours")
                    res_parsing[site] = parse(site, url)
        except urllib.error.URLError:
            print("{} non accessible sur {} (délai écoulé)".format(competition, site))
        except KeyboardInterrupt:
            res_parsing[site] = {}
        except selenium.common.exceptions.TimeoutException:
            print("Element non trouvé par selenium ({} sur {})".format(competition, site))
        except sb.UnavailableCompetitionException:
            print("{} non disponible sur {}".format(competition, site))
        except socket.timeout:
            print("{} non accessible sur {} (timeout socket)".format(competition, site))
        except selenium.common.exceptions.StaleElementReferenceException:
            print("StaleElement non trouvé par selenium ({} sur {})".format(competition, site))
        except selenium.common.exceptions.WebDriverException:
            print("Connection closed ({} sur {})".format(competition, site))
    res = format_team_names(res_parsing, sport, competition)
    out = valid_odds(merge_dict_odds(res), sport)
    if inspect.currentframe().f_back.f_code.co_name != "<module>":
        return out


def parse_competitions_site(competitions, sport, site):
    list_odds = []
    if len(competitions) > 40 and site == "winamax":  # to avoid being blocked by winamax
        competitions = competitions[:40]
    sb.SITE_PROGRESS[site] = 0
    try:
        for competition in competitions:
            list_odds.append(parse_competition(competition, sport, site))
            sb.PROGRESS += 100 / (len(competitions) * sb.SUB_PROGRESS_LIMIT)
            sb.SITE_PROGRESS[site] += 100 / len(competitions)
    except sb.UnavailableSiteException:
        print("{} non accessible".format(site))
        sb.SITE_PROGRESS[site] = 100
    except sb.AbortException:
        print("Interruption", site)
    if site in sb.SELENIUM_SITES:
        selenium_init.DRIVER[site].quit()
    return merge_dict_odds(list_odds)


def parse_competitions(competitions, sport="football", *sites):
    sites_order = ['bwin', 'parionssport', 'betstars', 'pasinobet', 'joa', 'unibet', 'betclic',
                   'pmu', 'france_pari', 'netbet', 'winamax', 'zebet']
    if not sites:
        sites = sites_order
    sb.EXPECTED_TIME = 28 + len(competitions) * 12.5
    selenium_sites = sb.SELENIUM_SITES.intersection(sites)
    selenium_required = ((inspect.currentframe().f_back.f_code.co_name
                          in ["<module>", "parse_thread"]
                          or 'test' in inspect.currentframe().f_back.f_code.co_name)
                         and (selenium_sites or not sites))
    sb.SELENIUM_REQUIRED = selenium_required
    sites = [site for site in sites_order if site in sites]
    sb.PROGRESS = 0
    if selenium_required:
        for site in selenium_sites:
            while True:
                headless = sport != "handball" or site != "bwin"
                if sb.ABORT or selenium_init.start_selenium(site, headless, timeout=15):
                    break
                colorama.init()
                print(termcolor.colored('Restarting', 'yellow'))
                colorama.Style.RESET_ALL
                colorama.deinit()
            sb.PROGRESS += 100/len(selenium_sites)
    sb.PROGRESS = 0
    sb.SUB_PROGRESS_LIMIT = len(sites)
    for competition in competitions:
        if competition == sport or "Tout le" in competition:
            import_teams_by_sport(sport)
        else:
            id_competition = get_id_formatted_competition_name(competition, sport)[0]
            if id_competition < 0:
                import_teams_by_competition_id_thesportsdb(id_competition)
            else:
                import_teams_by_url("http://www.comparateur-de-cotes.fr/comparateur/" + sport
                                    + "/a-ed" + str(id_competition))
    list_odds = []
    try:
        sb.IS_PARSING = True
        list_odds = ThreadPool(7).map(lambda x: parse_competitions_site(competitions, sport, x), sites)
        sb.ODDS[sport] = merge_dict_odds(list_odds)
    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
    sb.IS_PARSING = False
    if selenium_required:
        colorama.init()
        print(termcolor.colored('Drivers closed', 'green'))
        colorama.Style.RESET_ALL
        colorama.deinit()
    sb.ABORT = False


def odds_match(match, sport="football"):
    """
    Retourne les cotes d'un match donné sur tous les sites de l'ARJEL
    """
    match = unidecode.unidecode(match)
    all_odds = sb.ODDS[sport]
    opponents = match.split('-')
    for match_name in all_odds:
        if (opponents[0].lower().strip() in unidecode.unidecode(match_name.split("-")[0].lower())
                and opponents[1].lower().strip() in unidecode.unidecode(match_name.split("-")[1].lower())):
            break
    else:
        for match_name in all_odds:
            if (opponents[0].lower().strip() in unidecode.unidecode(match_name.lower())
                    and opponents[1].lower().strip() in unidecode.unidecode(match_name.lower())):
                break
        else:
            return None, None
    return match_name, copy.deepcopy(all_odds[match_name])


def best_stakes_match(match, site, bet, minimum_odd, sport="football"):
    """
    Pour un match, un bookmaker, une somme à miser sur ce bookmaker et une cote
    minimale donnés, retourne la meilleure combinaison de paris à placer
    """
    best_match, all_odds = odds_match(match, sport)
    if not all_odds:
        print("No match found")
        return
    print(best_match)
    pprint(all_odds)
    odds_site = all_odds['odds'][site]
    best_odds = copy.deepcopy(odds_site)
    best_profit = -float("inf")
    n = len(all_odds['odds'][site])
    best_sites = [site for _ in range(n)]
    best_i = 0
    best_overall_odds = None
    bets = None
    sites = None
    for odds in all_odds['odds'].items():
        for i in range(n):
            if odds[1][i] > best_odds[i] and (odds[1][i] >= 1.1 or odds[0] == "pmu"):
                best_odds[i] = odds[1][i]
                best_sites[i] = odds[0]
    for i in range(n):
        if odds_site[i] >= minimum_odd:
            odds_to_check = (best_odds[:i] + [odds_site[i]] + best_odds[i + 1:])
            profit = gain2(odds_to_check, i, bet)
            if profit > best_profit:
                best_profit = profit
                best_overall_odds = odds_to_check
                sites = best_sites[:i] + [site] + best_sites[i + 1:]
                bets = mises2(odds_to_check, bet, i)
                best_i = i
    if best_overall_odds:
        mises2(best_overall_odds, bet, best_i, True)
        afficher_mises_combine(best_match.split(" / "), [sites], [bets], all_odds["odds"], sport)
    else:
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
    odds_function = get_best_odds(one_site)
    profit_function = get_profit(bet, one_site)
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

def best_match_under_conditions2(site, minimum_odd, stake, sport="football", date_max=None,
                                time_max=None, date_min=None, time_min=None):
    all_odds = filter_dict_dates(sb.ODDS[sport], date_max, time_max, date_min, time_min)
    best_profit = -float("inf")
    best_match = None
    best_overall_odds = None
    sites = None
    nb_matches = len(all_odds)
    n = get_nb_issues(sport)
    for match in all_odds:
        sb.PROGRESS += 100 / nb_matches
        if site in all_odds[match]['odds']:
            odds_site = all_odds[match]['odds'][site]
            best_odds = copy.deepcopy(odds_site)
            best_sites = [site for _ in range(n)]
            for odds in all_odds[match]['odds'].items():
                for i in range(n):
                    if odds[1][i] > best_odds[i] and (odds[1][i] >= 1.1 or odds[0] == "pmu"):
                        best_odds[i] = odds[1][i]
                        best_sites[i] = odds[0]
            for odd_i, site_i in zip(best_odds, best_sites):
                if odd_i < 1.1 and site_i != "pmu":
                    break
            else:
                profit = gain3(odds_site, best_odds, stake, minimum_odd)
                if profit > best_profit:
                    best_profit = profit
                    best_odds_site = copy.deepcopy(odds_site)
                    best_best_odds = copy.deepcopy(best_odds)
                    best_match = match
                    stakes, best_indices = mises3(odds_site, best_odds, stake, minimum_odd)
                    sites = [site if i in best_indices else best_sites[i] for i in range(n)]
    if best_match:
        print(best_match)
        pprint(all_odds[best_match])
        mises3(best_odds_site, best_best_odds, stake, minimum_odd, True)
        afficher_mises_combine([best_match], [sites], [stakes],
                               all_odds[best_match]["odds"], sport)
    else:
        print("No match found")


def best_match_pari_gagnant(site, minimum_odd, bet, sport="football",
                            date_max=None, time_max=None, date_min=None,
                            time_min=None, nb_matches_combine=1):
    """
    Retourne le meilleur match sur lequel miser lorsqu'on doit gagner un pari à
    une cote donnée sur un site donné.
    """
    stakes = []
    n = 2 + (sport not in ["tennis", "volleyball", "basketball", "nba"])
    for _ in range(n**nb_matches_combine):
        stakes.append([bet, site, minimum_odd])
    best_match_stakes_to_bet(stakes, nb_matches_combine, sport, date_max, time_max, True)


def best_match_freebet(site, freebet, sport="football", live=False, date_max=None, time_max=None,
                       date_min=None, time_min=None):
    """
    Retourne le match qui génère le meilleur gain pour un unique freebet placé,
    couvert avec de l'argent réel.
    """
    fact_live = 1 - 0.2 * live
    odds_function = lambda best_odds, odds_site, i: (best_odds[:i] + [odds_site[i] * fact_live - 1]
                                                     + best_odds[i + 1:])
    profit_function = lambda odds_to_check, i: gain2(odds_to_check, i) + 1
    criteria = lambda odds_to_check, i: True
    display_function = lambda x, i: mises_freebet(x[:i] + [x[i] + 1] + x[i + 1:], freebet, i, True)
    result_function = lambda x, i: mises_freebet(x[:i] + [x[i] + 1] + x[i + 1:], freebet, i, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport, date_max, time_max, date_min,
                    time_min, freebet=True)


def best_match_freebet2(site, freebet, sport="football", live=False, date_max=None, time_max=None,
                        date_min=None, time_min=None):
    """
    Retourne le match qui génère le meilleur gain pour un unique freebet placé,
    couvert avec de l'argent réel.
    """
    fact_live = 1 - 0.2 * live
    odds_function = lambda best_odds, odds_site, i: (best_odds[:i] + [odds_site[i] * fact_live - 1]
                                                     + best_odds[i + 1:])
    profit_function = lambda x, i: gain_freebet2(x[:i] + [x[i] + 1] + x[i + 1:], freebet, i)
    criteria = lambda odds_to_check, i: True
    display_function = lambda x, i: mises_freebet2(x[:i] + [x[i] + 1] + x[i + 1:], freebet, i, True)
    result_function = lambda x, i: mises_freebet2(x[:i] + [x[i] + 1] + x[i + 1:], freebet, i, False)
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
                                                     + [combi_odd * odds_site[i]
                                                        * (1 + combi_max) - combi_max]
                                                     + best_odds[i + 1:])
    profit_function = lambda odds_to_check, i: gain_pari_rembourse_si_perdant(odds_to_check, bet, i,
                                                                              freebet,
                                                                              rate_cashback)
    criteria = lambda odds_to_check, i: (odds_to_check[i] + combi_max) / (
            1 + combi_max) >= minimum_odd
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
    all_odds = filter_dict_dates(sb.ODDS[sport], date_max, time_max, date_min, time_min)
    all_odds = filter_dict_minimum_odd(all_odds, minimum_odd_selection, site)
    sb.ALL_ODDS_COMBINE = {}
    nb_combine = binomial(len(all_odds), nb_matches)
    sb.PROGRESS = 0

    def compute_all_odds_combine(nb_combine, combine):
        sb.PROGRESS += 100/nb_combine
        try:
            sb.ALL_ODDS_COMBINE[" / ".join([match[0] for match in combine])] = cotes_combine_all_sites(*[match[1]
                                                                                        for match
                                                                                        in combine])
        except KeyError:
            pass
    
    ThreadPool(4).map(lambda x: compute_all_odds_combine(nb_combine, x),
                      combinations(all_odds.items(), nb_matches))
    sb.PROGRESS = 0
    odds_function = get_best_odds(one_site)
    profit_function = get_profit(bet, one_site)
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
                    time_min, True, nb_matches, one_site=one_site, combine_opt=True)


def best_matches_combine_cashback_une_selection_perdante(site, cote_minimale_selection, combi_max=0,
                                                         nb_matches=2, date_max=None, time_max=None,
                                                         date_min=None, time_min=None):
    """
    Calcule la meilleure combinaison de matches et les mises à jouer pour une promotion du type
    "Combiné remboursé si une seule selection perdante, sans limite du nombre de paris remboursés"
    """
    sport = "football"
    bet = 10000
    all_odds = sb.ODDS[sport]
    sb.ALL_ODDS_COMBINE = {}
    for combine in combinations(all_odds.items(), nb_matches):
        try:
            if all([odd >= cote_minimale_selection for odds in list(all_odds[match[0]]["odds"][site]
                                                                    for match in combine)
                    for odd in odds]):
                (sb
                    .ALL_ODDS_COMBINE[" / "
                    .join([match[0]
                           for match
                           in combine])]) = cotes_combine_all_sites(*[match[1]
                                                                      for match
                                                                      in combine])
        except KeyError:
            pass
    odds_function = lambda best_odds, odds_site, i: list(
        map(lambda x: x * (1 + combi_max) - combi_max,
            odds_site))
    profit_function = lambda odds_to_check, i: gain(odds_to_check, bet) - bet
    criteria = lambda odds_to_check, i: (odds_to_check[i] + combi_max) / (1 + combi_max) >= 1.1
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
    all_odds = sb.ODDS[sport]
    sb.ALL_ODDS_COMBINE = {}
    for combine in combinations(all_odds.items(), nb_matches):
        (sb
            .ALL_ODDS_COMBINE[" / "
            .join([match[0]
                   for match
                   in combine])]) = cotes_combine_all_sites(*[match[1]
                                                              for match
                                                              in combine])
    odds_function = lambda best_odds, odds_site, i: (best_odds[:i]
                                                     + [odds_site[i] * (1 + combi_max) - combi_max]
                                                     + best_odds[i + 1:])
    profit_function = lambda odds_to_check, i: gain_pari_rembourse_si_perdant(odds_to_check, bet, i,
                                                                              freebet,
                                                                              rate_cashback)
    criteria = lambda odds_to_check, i: (odds_to_check[i] + combi_max) / (
            1 + combi_max) >= minimum_odd
    display_function = lambda x, i: mises_pari_rembourse_si_perdant(x, bet, i, freebet,
                                                                    rate_cashback, True)
    return_function = lambda x, i: mises_pari_rembourse_si_perdant(x, bet, i, freebet,
                                                                   rate_cashback, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    return_function, site, sport, date_max, time_max, date_min,
                    time_min, True, nb_matches)


def best_match_stakes_to_bet(stakes, nb_matches=1, sport="football", date_max=None, time_max=None, identical_stakes=False):
    second_sites = {stake[1] for stake in stakes}
    main_sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet',
                  'parionssport', 'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']
    all_odds = filter_dict_dates(sb.ODDS[sport], date_max, time_max)
    best_profit = -sum(stake[0] for stake in stakes)
    n = get_nb_issues(sport) ** nb_matches
    nb_stakes = len(stakes)
    all_odds_combine = {}
    combis = list(combinations(all_odds.items(), nb_matches))
    nb_combis = len(combis)
    best_combine = None
    best_bets = None
    main_site_odds = []
    main_sites_distribution = []
    sb.PROGRESS = 0
    for i, combine in enumerate(combis):
        sb.PROGRESS += 100 / nb_combis
        match_combine = " / ".join([match[0] for match in combine])
        all_odds_combine[match_combine] = cotes_combine_all_sites(*[match[1] for match in combine])
        for main0 in main_sites:
            try:
                main_sites_distribution = [main0 for _ in range(n)]
                main_site_odds = copy.deepcopy(all_odds_combine[match_combine]["odds"][main0])
                break
            except KeyError:
                pass
        for main in main_sites[:i] + main_sites[i + 1:]:
            try:
                potential_odds = all_odds_combine[match_combine]["odds"][main]
                for j, odd in enumerate(potential_odds):
                    if odd > main_site_odds[j]:
                        main_site_odds[j] = odd
                        main_sites_distribution[j] = main
            except KeyError:
                pass
        second_odds = {second_site: all_odds_combine[match_combine]["odds"][second_site]
                       for second_site in second_sites if second_site in all_odds_combine[match_combine]["odds"]}
        if not second_odds:
            continue
        dict_combine_odds = copy.deepcopy(second_odds)
        for perm in permutations(range(n), nb_stakes):
            valid_perm = True
            defined_second_sites = [[perm[j], stake[0], stake[1]]
                                    for j, stake in enumerate(stakes)]
            for j, stake in enumerate(stakes):
                if dict_combine_odds[defined_second_sites[j][2]][defined_second_sites[j][0]] < stake[2]:
                    valid_perm = False
                    break
            if not valid_perm:
                if identical_stakes:
                    break
                continue
            defined_bets_temp = defined_bets(main_site_odds, dict_combine_odds,
                                             main_sites_distribution,
                                             defined_second_sites)
            profit = defined_bets_temp[0] - np.sum(defined_bets_temp[1])
            if profit > best_profit:
                best_profit = profit
                best_combine = combine
                best_bets = defined_bets_temp
            if identical_stakes:
                break
    if best_combine:
        best_match_combine = " / ".join([match[0] for match in best_combine])
        odds_best_match = copy.deepcopy(all_odds_combine[best_match_combine])
        all_sites = main_sites + list(second_sites)
        for site in all_odds_combine[best_match_combine]["odds"]:
            if site not in all_sites:
                del odds_best_match["odds"][site]
        print(best_match_combine)
        pprint(odds_best_match, compact=1)
        print("Plus-value =", round(best_profit, 2))
        print("Gain référence =", round(best_bets[0], 2))
        print("Somme des mises =", round(np.sum(best_bets[1]), 2))
        afficher_mises_combine([x[0] for x in best_combine], best_bets[2], best_bets[1],
                               all_odds_combine[best_match_combine]["odds"], sport)
    else:
        print("No match found")


def best_matches_freebet(main_sites, freebets, sport="football", *matches):
    """
    Compute of the best way to bet freebets following the model
    [[bet, bookmaker], ...]
    :param main_sites:
    :type freebets: List[List[List[str] or str]]
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
        new_odds = sb.ODDS[sport]
    all_odds = {}
    for match in new_odds:
        if (not (any([site not in new_odds[match]["odds"].keys() for site in main_sites])
                 or any([site not in new_odds[match]["odds"].keys() for site in second_sites]))):
            if new_odds[match]["odds"]:
                all_odds[match] = new_odds[match]
    best_rate = 0
    nb_matches = 2
    n = 3 ** nb_matches
    nb_freebets = len(freebets)
    all_odds_combine = {}
    combis = list(combinations(all_odds.items(), nb_matches))
    nb_combis = len(combis)
    progress = 10
    start = time.time()
    for i, combine in enumerate(combis):
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
        second_odds = {second_site: all_odds_combine[match_combine]["odds"][second_site]
                       for second_site in second_sites}
        dict_combine_odds = copy.deepcopy(second_odds)
        for perm in permutations(range(n), nb_freebets):
            defined_second_sites = [[perm[i], freebet[0], freebet[1]]
                                    for i, freebet in enumerate(freebets)]
            defined_bets_temp = defined_bets(main_site_odds, dict_combine_odds,
                                             main_sites_distribution,
                                             defined_second_sites)
            if defined_bets_temp[0] / np.sum(defined_bets_temp[1]) > best_rate:
                best_rate = defined_bets_temp[0] / np.sum(defined_bets_temp[1])
                best_combine = combine
                best_bets = defined_bets_temp
    #     print("Temps d'exécution =", time.time()-start)
    best_match_combine = " / ".join([match[0] for match in best_combine])
    odds_best_match = copy.deepcopy(all_odds_combine[best_match_combine])
    all_sites = main_sites + list(second_sites)
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
    all_odds = sb.ODDS[sport]
    sb.ALL_ODDS_COMBINE = {}
    for combine in combinations(all_odds.items(), nb_matches):
        (sb
            .ALL_ODDS_COMBINE[" / ".join([match[0] for match
                                          in combine])]) = cotes_combine_all_sites(*[match[1]
                                                                                     for match
                                                                                     in combine])
    odds_function = lambda best_odds, odds_site, i: cotes_freebet(odds_site)
    profit_function = lambda odds_to_check, i: gain(odds_to_check, freebet) - freebet
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
    odds_function = get_best_odds(False)
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
    odds_function = get_best_odds(True)
    profit_function = lambda odds_to_check, i: gain_gains_nets_boostes(odds_to_check, gain_max,
                                                                       False)
    criteria = lambda odds_to_check, i: odds_to_check[i] >= 1.5
    display_function = lambda odds_to_check, i: mises_gains_nets_boostes(odds_to_check, gain_max,
                                                                         False, True)
    result_function = lambda odds_to_check, i: mises_gains_nets_boostes(odds_to_check, gain_max,
                                                                        False, False)
    best_match_base(odds_function, profit_function, criteria, display_function, result_function,
                    site, sport, date_max, time_max, date_min, time_min)

def best_combine_booste(matches, combinaison_boostee, site_combinaison, mise, sport, cote_boostee):
    best_combine_reduit(matches, combinaison_boostee, site_combinaison, mise, sport, cote_boostee)



def add_competition_to_db(sport):
    """
    Ajout des competitions d'un sport donné disponibles sur comparateur-de-cotes
    """
    url = "http://www.comparateur-de-cotes.fr/comparateur/" + sport
    conn = sqlite3.connect(sb.PATH_DB)
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
