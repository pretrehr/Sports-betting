#!/usr/bin/env python3
"""
Fonctions principales d'assistant de paris
"""
import sportsbetting
import copy
import datetime
import requests
import socket
import sys
import traceback
import urllib
import urllib.error
import urllib.request

from itertools import combinations, permutations, product
from multiprocessing.pool import ThreadPool
from pprint import pprint

import numpy as np
import selenium
import selenium.common
import tabulate

import sportsbetting as sb
from sportsbetting import selenium_init
from sportsbetting.database_functions import (get_id_from_competition_name, get_competition_by_id, import_teams_by_url,
                                              import_teams_by_sport, import_teams_by_competition_id_thesportsdb)
from sportsbetting.parser_functions import parse
from sportsbetting.auxiliary_functions import (valid_odds, format_team_names, merge_dict_odds, afficher_mises_combine,
                                               cotes_combine_all_sites, defined_bets, binomial, best_match_base,
                                               filter_dict_dates, get_nb_outcomes, best_combine_reduit,
                                               filter_dict_minimum_odd, cotes_combine_reduit_all_sites, copy_to_clipboard)
from sportsbetting.basic_functions import (gain2, mises2, gain, mises, mises_freebet, cotes_freebet,
                                           gain_pari_rembourse_si_perdant, gain_freebet2, mises_freebet2,
                                           mises_pari_rembourse_si_perdant, gain_promo_gain_cote, mises_promo_gain_cote,
                                           gain_gains_nets_boostes, mises_gains_nets_boostes, gain3, mises3, cotes_combine_optimise,
                                           gain_defi_rembourse_ou_gagnant, mises_defi_rembourse_ou_gagnant)
from sportsbetting.lambda_functions import get_best_odds, get_profit


def parse_competition(competition, sport, *sites):
    """
    Retourne les cotes d'une competition donnée pour un ou plusieurs sites de
    paris. Si aucun site n'est choisi, le parsing se fait sur l'ensemble des
    bookmakers reconnus par l'ARJEL
    """
    if sb.ABORT:
        raise sb.AbortException
    try:
        _id = get_id_from_competition_name(competition, sport)
    except TypeError:
        print("Competition inconnue")
        return
    print(competition, *sites)
    if not sites:
        sites = sb.BOOKMAKERS
    res_parsing = {}
    for site in sites:
        if len(sites) > 1:
            print(site)
        database_site = site if site not in ["barrierebet", "vbet"] else "pasinobet"
        url = get_competition_by_id(_id, database_site)
        try:
            if url:
                res_parsing[site] = parse(site, url)
            else:
                print("Pas d'url en base pour {} sur {}".format(competition, site))
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
        except requests.exceptions.SSLError:
            print("Max retries ({} sur {})".format(competition, site))
    res = format_team_names(res_parsing, sport, competition)
    out = valid_odds(merge_dict_odds(res), sport)
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
    return merge_dict_odds(list_odds)


def parse_competitions(competitions, sport, *sites):
    sites_order = ['betfair', 'joa', 'betway', 'pmu', 'barrierebet', 'pasinobet', 'vbet', 'france_pari', 'netbet', 'zebet',
                   'winamax', 'pinnacle', 'betclic', 'pokerstars', 'unibet', 'unibet_boost', 'bwin', 'parionssport']
    if not sites:
        sites = sites_order
    sb.EXPECTED_TIME = 28 + len(competitions) * 12.5
    sites = [site for site in sites_order if site in sites]
    sb.PROGRESS = 0
    selenium_sites = sb.SELENIUM_SITES.intersection(sites)
    for site in selenium_sites:
        selenium_init.start_driver(site)
        sb.PROGRESS += 100/len(selenium_sites)
    sb.PROGRESS = 0
    sb.SUB_PROGRESS_LIMIT = len(sites)
    if sb.DB_MANAGEMENT:
        for competition in competitions:
            if competition == sport or "Tout le" in competition:
                import_teams_by_sport(sport)
            else:
                id_competition = get_id_from_competition_name(competition, sport)
                if id_competition < 0:
                    import_teams_by_competition_id_thesportsdb(id_competition)
                else:
                    import_teams_by_url("http://www.comparateur-de-cotes.fr/comparateur/" + sport
                                        + "/a-ed" + str(id_competition))
    list_odds = []
    try:
        sb.IS_PARSING = True
        list_odds = ThreadPool(3).map(lambda x: parse_competitions_site(competitions, sport, x), sites)
        sb.ODDS[sport] = merge_dict_odds(list_odds)
    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
    sb.IS_PARSING = False
    sb.ABORT = False
    sb.SEEN_SUREBET[sport] = False
    print("Dernière récupération des cotes à", datetime.datetime.today().strftime("%H:%M"))


def odds_match(match, sport="football"):
    """
    Retourne les cotes d'un match donné sur tous les sites de l'ARJEL
    """
    odds_match = sb.ODDS[sport].get(match)
    if odds_match:
        return match, copy.deepcopy(odds_match)
    return None, None


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
        if odds[0] == "unibet_boost":
            continue
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
        afficher_mises_combine(best_match.split(" / "), [sites], [bets], all_odds["odds"], sport, profit=best_profit)
    else:
        print("No match found")


def best_match_under_conditions(site, minimum_odd, bet, sport="football", date_max=None,
                                time_max=None, date_min=None, time_min=None, one_site=False):
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
                                 time_max=None, date_min=None, time_min=None, miles=False, rate_eur_miles=0, multiplicator=1):
    all_odds = filter_dict_dates(sb.ODDS[sport], date_max, time_max, date_min, time_min)
    best_profit = -float("inf")
    best_match = None
    sites = None
    nb_matches = len(all_odds)
    n = get_nb_outcomes(sport)
    for match in all_odds:
        sb.PROGRESS += 100 / nb_matches
        if site in all_odds[match]['odds']:
            odds_site = all_odds[match]['odds'][site]
            best_odds = copy.deepcopy(odds_site)
            best_sites = [site for _ in range(n)]
            for odds in all_odds[match]['odds'].items():
                if odds[0] == "unibet_boost":
                    continue
                for i in range(n):
                    if odds[1][i] > best_odds[i] and (odds[1][i] >= 1.1 or odds[0] == "pmu"):
                        best_odds[i] = odds[1][i]
                        best_sites[i] = odds[0]
            for odd_i, site_i in zip(best_odds, best_sites):
                if odd_i < 1.1 and site_i != "pmu":
                    break
            else:
                profit = gain3(odds_site, best_odds, stake, minimum_odd, miles, rate_eur_miles, multiplicator)
                if profit > best_profit:
                    best_profit = profit
                    best_odds_site = copy.deepcopy(odds_site)
                    best_best_odds = copy.deepcopy(best_odds)
                    best_match = match
                    stakes, best_indices = mises3(odds_site, best_odds, stake, minimum_odd, False, miles, rate_eur_miles, multiplicator)
                    sites = [site if i in best_indices else best_sites[i] for i in range(n)]
    if best_match:
        print(best_match)
        pprint(all_odds[best_match])
        mises3(best_odds_site, best_best_odds, stake, minimum_odd, True, miles, rate_eur_miles, multiplicator)
        afficher_mises_combine([best_match], [sites], [stakes],
                               all_odds[best_match]["odds"], sport, profit=best_profit)
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
    n = get_nb_outcomes(sport)
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
    criteria = lambda odds_to_check, i: (odds_to_check[i] + combi_max) / (1 + combi_max) >= minimum_odd
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
            sb.ALL_ODDS_COMBINE[" / ".join([match[0] for match in combine])] = cotes_combine_all_sites(
                *[match[1] for match in combine]
            )
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
                sb.ALL_ODDS_COMBINE[" / ".join([match[0] for match in combine])] = cotes_combine_all_sites(
                    *[match[1] for match in combine]
                )
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
        sb.ALL_ODDS_COMBINE[" / ".join([match[0] for match in combine])] = cotes_combine_all_sites(
            *[match[1] for match in combine]
        )
    odds_function = lambda best_odds, odds_site, i: (best_odds[:i]
                                                     + [odds_site[i] * (1 + combi_max) - combi_max]
                                                     + best_odds[i + 1:])
    profit_function = lambda odds_to_check, i: gain_pari_rembourse_si_perdant(odds_to_check, bet, i,
                                                                              freebet,
                                                                              rate_cashback)
    criteria = lambda odds_to_check, i: (odds_to_check[i] + combi_max) / (1 + combi_max) >= minimum_odd
    display_function = lambda x, i: mises_pari_rembourse_si_perdant(x, bet, i, freebet,
                                                                    rate_cashback, True)
    return_function = lambda x, i: mises_pari_rembourse_si_perdant(x, bet, i, freebet,
                                                                   rate_cashback, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    return_function, site, sport, date_max, time_max, date_min,
                    time_min, True, nb_matches, combine_opt=True, taux_cashback=rate_cashback, cashback_freebet=freebet)


def best_match_stakes_to_bet(stakes, nb_matches=1, sport="football", date_max=None, time_max=None, identical_stakes=False):
    second_sites = {stake[1] for stake in stakes}
    main_sites = sb.BOOKMAKERS
    all_odds = filter_dict_dates(sb.ODDS[sport], date_max, time_max)
    best_profit = -sum(stake[0] for stake in stakes)
    n = get_nb_outcomes(sport) ** nb_matches
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
                               all_odds_combine[best_match_combine]["odds"], sport, profit=best_profit)
    else:
        print("No match found")


def best_matches_freebet(main_sites, freebets, sport, *matches):
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
    best_combine = None
    real_odds = {}
    for combine in combis:
        match_combine = " / ".join([match[0] for match in combine])
        all_odds_combine[match_combine] = cotes_combine_all_sites(*[match[1] for match in combine],
                                                                  freebet=True)
        real_odds[match_combine] = cotes_combine_all_sites(*[match[1] for match in combine])
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
    if best_combine:
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
                               real_odds[best_match_combine]["odds"], "football",
                               uniquement_freebet=True, profit=best_rate)


def best_matches_freebet_one_site(site, freebet, sport="football", nb_matches=2,
                                  minimum_odd=1.1, date_max=None, time_max=None,
                                  date_min=None, time_min=None):
    """
    Calcule la répartition des paris gratuits sur un unique site
    """
    all_odds = sb.ODDS[sport]
    sb.ALL_ODDS_COMBINE = {}
    for combine in combinations(all_odds.items(), nb_matches):
        sb.ALL_ODDS_COMBINE[" / ".join([match[0] for match in combine])] = cotes_combine_all_sites(
            *[match[1] for match in combine]
        )
    odds_function = lambda best_odds, odds_site, i: cotes_freebet(odds_site)
    profit_function = lambda odds_to_check, i: gain(odds_to_check, freebet) - freebet
    criteria = lambda odds_to_check, i: all(odd >= minimum_odd for odd in odds_to_check)
    display_function = lambda best_overall_odds, best_rank: mises(best_overall_odds, freebet, True, True)
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


def best_combine_booste_progressif(matches, combinaison_boostee, site_combinaison, mise, sport, cote_boostee):
    outcomes = []
    odds = []
    bookmakers = []
    stakes = []
    simulated_odds = []
    outcome_boost = []
    matches.sort(key=lambda x: sb.ODDS[sport][x]["date"], reverse=True)
    time_intervals = [sb.ODDS[sport][x]["date"] - sb.ODDS[sport][y]["date"] for x, y in zip(matches[:-1], matches[1:])]
    print("Répartition des mises (les totaux affichés prennent en compte les éventuels freebets):")
    if time_intervals and min(time_intervals) < datetime.timedelta(hours=2):
        print("Methode impossible (pas assez de temps entre 2 matches)")
        return
    reference_gain = round(mise * cote_boostee, 2)
    sum_stakes = 0
    for j, match in enumerate(matches):
        sum_stakes_match = 0
        teams = match.split(" - ")
        if get_nb_outcomes(sport) == 3:
            teams.insert(1, "Nul ({} - {})".format(*teams))
        _, bookmakers_match, odds_match = trj_match(sb.ODDS[sport][match])
        for i, team in enumerate(teams):
            if combinaison_boostee[j] == i:
                outcome_boost.append(team)
                continue
            outcomes.append(team)
            odds.append(odds_match[i])
            bookmakers.append(bookmakers_match[i])
            stake = round((reference_gain - sum_stakes) / odds_match[i], 2)
            stakes.append(stake)
            sum_stakes_match += stake
            simulated_odds.append(reference_gain / stake)
        sum_stakes += sum_stakes_match
    outcomes.append(" / ".join(outcome_boost))
    odds.append(cote_boostee)
    bookmakers.append(site_combinaison)
    stakes.append(mise)
    simulated_odds.append(cote_boostee)
    totals = [round(stake * odd, 2) for (stake, odd) in zip(stakes, odds)]
    table = {"Issue": reversed(outcomes), "Bookmaker": reversed(bookmakers), "Cote": reversed(odds), "Mise": reversed(stakes), "Total": reversed(totals), "TRJ":[round(100*gain(simulated_odds), 3), "Bénéfice", round(reference_gain-sum(stakes), 2)]}
    text = tabulate.tabulate(table, headers='keys', tablefmt='fancy_grid')
    print(text)
    print("Ne couvrir un match qu'une fois le résultat du match précédent connu")
    if sys.platform.startswith("win"):
        copy_to_clipboard(text)
    
    


def trj_match(match_odds):
    odds = []
    bookmakers = []
    for bookmaker in match_odds["odds"]:
        if bookmaker == "unibet_boost":
            continue
        tmp_odds = match_odds["odds"][bookmaker]
        tmp_bookmakers = [bookmaker for _ in tmp_odds]
        if not odds:
            odds = copy.deepcopy(tmp_odds)
            bookmakers = copy.deepcopy(tmp_bookmakers)
            continue
        for i, tmp_odd in enumerate(tmp_odds):
            if not odds[i]:
                odds[i] = 1.01
            if not tmp_odd:
                continue
            try:
                if tmp_odd > odds[i]:
                    odds[i] = tmp_odd
                    bookmakers[i] = bookmaker
            except TypeError:
                print(match_odds, tmp_odd, odds[i])
    if not odds or 1.01 in odds:
        return 0, bookmakers, odds
    return gain(odds), bookmakers, odds

def get_values(match_odds, rate):
    odds = []
    bookmakers = []
    sums = []
    for bookmaker in match_odds["odds"]:
        if bookmaker == "unibet_boost":
            continue
        tmp_odds = match_odds["odds"][bookmaker]
        tmp_bookmakers = [bookmaker for _ in tmp_odds]
        if not odds:
            odds = copy.deepcopy(tmp_odds)
            sums = copy.deepcopy(tmp_odds)
            bookmakers = copy.deepcopy(tmp_bookmakers)
            continue
        for i, tmp_odd in enumerate(tmp_odds):
            sums[i] += tmp_odd
            if tmp_odd > odds[i]:
                odds[i] = tmp_odd
                bookmakers[i] = bookmaker
    values = []
    best_rate = rate-1
    n = len(match_odds["odds"])
    i = 0
    has_pinnacle = "pinnacle" in match_odds["odds"]
    for odd, sum, bookmaker in zip(odds, sums, bookmakers):
        if odd < 1.1:
            return 0, []
        ref = sum/n if not has_pinnacle else match_odds["odds"]["pinnacle"][i]
        if ref < 1.1:
            return 0, []
        rate_tmp = odd/ref-1
        if rate_tmp >= rate:
            best_rate = max(best_rate, rate_tmp)
        value = [odd, rate_tmp, bookmaker]
        values.append(value)
        i += 1
    return best_rate, values


def best_matches_combine2(site, minimum_odd, bet, sport, minimum_odd_selection, date_max=None, time_max=None,
                          date_min=None, time_min=None):
    nb_matches = 2
    all_odds = filter_dict_dates(sb.ODDS[sport], date_max, time_max, date_min, time_min)
    all_odds = filter_dict_minimum_odd(all_odds, minimum_odd_selection, site)
    odds_combine_opt = [{} for _ in range(6)]
    nb_combine = binomial(len(all_odds), nb_matches)
    sb.PROGRESS = 0
    combis = cotes_combine_optimise([[1 for _ in range(3)] for i in range(nb_matches)])[1]
    print(combis)
    def compute_all_odds_combine_optimise(nb_combine, combine, odds_combine_opt):
        sb.PROGRESS += 100/nb_combine
        try:
            cotes_combination = cotes_combine_reduit_all_sites(
                *[match[1] for match in combine]
            )
            for i in range(6):
                odds_combine_opt[i][" / ".join([match[0] for match in combine])] = cotes_combination[i]
#                 combis[i] = cotes_combination[i][1]
        except KeyError:
            pass
    ThreadPool(4).map(lambda x: compute_all_odds_combine_optimise(nb_combine, x, odds_combine_opt),
                      combinations(all_odds.items(), nb_matches))
    sb.PROGRESS = 0
    odds_function = get_best_odds(False)
    profit_function = get_profit(bet, False)
    criteria = lambda odds_to_check, i: all(odd >= minimum_odd for odd in odds_to_check)
    for i, combination in enumerate(combis):
        sb.ALL_ODDS_COMBINE = odds_combine_opt[i]
#         display_function = lambda odds_to_check, i: mises_combine_optimise(odds_to_check, combination, bet, minimum_odd, True)
#         result_function = lambda odds_to_check, i: mises_combine_optimise(odds_to_check, combination, bet, minimum_odd, False)
        display_function = lambda best_overall_odds, best_rank: mises2(best_overall_odds, bet, best_rank, True)
        result_function = lambda best_overall_odds, best_rank: mises2(best_overall_odds, bet, best_rank, False)
        best_match_base(odds_function, profit_function, criteria, display_function, result_function, site, sport, date_max, time_max, date_min,
                    time_min, True, nb_matches, combine_opt=True)


def best_matches_combine3(site, minimum_odd, bet, sport="football",
                          date_max=None, time_max=None, date_min=None,
                          time_min=None, nb_matches_combine=2):
    stakes = []
    for _ in range(5):
        stakes.append([bet, site, minimum_odd])
    best_match_stakes_to_bet2(stakes, nb_matches_combine, sport, date_max, time_max, True)


def convert_indices_to_opponents(combination_indices, matches, sport):
    combination_opponents = []
    matches_outcomes = [match.split(" - ") for match in matches]
    if get_nb_outcomes(sport) == 3:
        for match in matches_outcomes:
            match.insert(1, "Nul")
    for indices in combination_indices:
        opponents = []
        for i, index in enumerate(indices):
            if index == float("inf"):
                continue
            opponents.append(matches_outcomes[i][index])
        combination_opponents.append(tuple(opponents))
    return combination_opponents

def best_match_stakes_to_bet2(stakes, nb_matches=2, sport="football", date_max=None, time_max=None, identical_stakes=False):
    second_sites = {stake[1] for stake in stakes if stake[1] != "unibet_boost"}
    main_sites = sb.BOOKMAKERS
    all_odds = get_matches_with_best_trj(sport, 20)
    all_odds = filter_dict_dates(all_odds, date_max, time_max)
    best_profit = -sum(stake[0] for stake in stakes)
    n = 5#get_nb_outcomes(sport) ** nb_matches
    nb_stakes = len(stakes)
    all_odds_combine = [{} for _ in range(6)]
    combis = list(combinations(all_odds.items(), nb_matches))
    nb_combis = len(combis)
    best_combine = None
    best_bets = None
    main_site_odds = []
    main_sites_distribution = []
    sb.PROGRESS = 0
    list_combinations = cotes_combine_optimise([[1 for _ in range(3)] for i in range(nb_matches)])[1]
    for k in range(6):
        for i, combine in enumerate(combis):
            sb.PROGRESS += 100 / nb_combis
            match_combine = " / ".join([match[0] for match in combine])
            cotes_combination = cotes_combine_reduit_all_sites(
                *[match[1] for match in combine]
            )
#             print(cotes_combination[k])
            all_odds_combine[k][match_combine] = cotes_combination[k]
            for main0 in main_sites:
                try:
                    main_sites_distribution = [main0 for _ in range(n)]
                    main_site_odds = copy.deepcopy(all_odds_combine[k][match_combine]["odds"][main0])
                    break
                except KeyError:
                    pass
            for main in main_sites[:i] + main_sites[i + 1:]:
                try:
                    potential_odds = all_odds_combine[k][match_combine]["odds"][main]
                    for j, odd in enumerate(potential_odds):
                        if odd > main_site_odds[j]:
                            main_site_odds[j] = odd
                            main_sites_distribution[j] = main
                except KeyError:
                    pass
            second_odds = {second_site: all_odds_combine[k][match_combine]["odds"][second_site]
                        for second_site in second_sites if second_site in all_odds_combine[k][match_combine]["odds"]}
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
                    best_combination = k
                if identical_stakes:
                    break
    if best_combine:
        best_match_combine = " / ".join([match[0] for match in best_combine])
        odds_best_match = copy.deepcopy(all_odds_combine[best_combination][best_match_combine])
        all_sites = main_sites + list(second_sites)
        for site in all_odds_combine[best_combination][best_match_combine]["odds"]:
            if site not in all_sites:
                del odds_best_match["odds"][site]
        print(best_match_combine)
        pprint(odds_best_match, compact=1)
        print("Plus-value =", round(best_profit, 2))
        print("Gain référence =", round(best_bets[0], 2))
        print("Somme des mises =", round(np.sum(best_bets[1]), 2))
        afficher_mises_combine([x[0] for x in best_combine], best_bets[2], best_bets[1],
                               all_odds_combine[best_combination][best_match_combine]["odds"], sport,
                               combinaisons=convert_indices_to_opponents(list_combinations[best_combination], [x[0] for x in best_combine], sport), profit=best_profit)
    else:
        print("No match found")

def best_matches_freebet2(site, freebet, sport, nb_matches=2):
#     all_odds = sb.ODDS[sport]
    all_odds = get_matches_with_best_trj(sport, 10, site)
    best_profit = float("-inf")
    combis = list(combinations(all_odds.items(), nb_matches))
    if not combis:
        print("No match found")
        return
    nb_combis = len(combis)
    best_combine = None
    best_bets = None
    best_matches = []
    best_choice = [0 for _ in range(nb_matches)]
    best_odd = 1.01
    choices = list(product(*[range(get_nb_outcomes(sport)) for _ in range(nb_matches)]))
    for combi in combis:
        if any([site not in x[1]["odds"] for x in combi]):
            continue
        matches = [x[0] for x in combi]
        for choice in choices:
            choice_list = list(choice)
            odd = 1
            for match, outcome in zip(combi, choice_list):
                odd *= match[1]["odds"][site][outcome]
            profit = best_combine_reduit(matches, choice_list, site, freebet, sport, odd-1, output=False)
            if profit < best_profit:
                continue
            best_profit = profit
            best_matches = matches
            best_choice = choice_list
            best_odd = odd
    best_combine_reduit(best_matches, best_choice, site, freebet, sport, best_odd-1, freebet=True)

def get_matches_with_best_trj(sport, nb_matches, site=None):
    matches = sorted(filter(lambda x: not site or site in x[1]["odds"], sb.ODDS[sport].items()), key=lambda x:trj_match(x[1])[0], reverse=True)[:nb_matches]
    return {match:odds for match, odds in matches}
    

def best_match_defi_rembourse_ou_gagnant(site, minimum_odd, stake, sport, date_max=None,
                                         time_max=None, date_min=None, time_min=None):
    odds_function = get_best_odds(False)
    profit_function = lambda best_overall_odds, best_rank: gain_defi_rembourse_ou_gagnant(best_overall_odds, stake, best_rank, True)
    profit_function = lambda odds_to_check, i: gain_defi_rembourse_ou_gagnant(odds_to_check, stake, i)
    criteria = lambda odds_to_check, i: odds_to_check[i] >= minimum_odd
    display_function = lambda best_overall_odds, best_rank: mises_defi_rembourse_ou_gagnant(best_overall_odds, stake, best_rank, True)
    result_function = lambda best_overall_odds, best_rank: mises_defi_rembourse_ou_gagnant(best_overall_odds, stake, best_rank, False)
    best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport, date_max, time_max, date_min,
                    time_min)

def get_sports_with_surebet():
    sports_with_surebet = []
    for sport in sb.SPORTS:
        if sb.SEEN_SUREBET[sport]:
            continue
        if sport not in sb.ODDS:
            continue
        for match in sb.ODDS[sport]:
            if trj_match(sb.ODDS[sport][match])[0]>=1:
                sports_with_surebet.append(sport)
                break
    return sports_with_surebet
    
