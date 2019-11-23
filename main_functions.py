#!/usr/bin/env python3
"""
Fonctions principales d'assistant de paris
"""

from pprint import pprint
from copy import deepcopy
import winsound
from itertools import combinations, permutations
import numpy as np
import time
from bet_functions import (merge_dicts, gain2, mises2, gain, mises,
                           mises_freebet, gain_pari_rembourse_si_perdant,
                           mises_pari_rembourse_si_perdant, cotes_freebet,
                           cotes_combine_all_sites, cotes_combine,
                           afficher_mises_combine)
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
    """
    Retourne les cotes des principaux championnats de football
    """
    competitions = ["france ligue 1", "angleterre premier league",
                    "espagne liga", "italie serie", "allemagne bundesliga",
                    "ligue des champions"]#, "qualif"]
    list_odds = []
    for competition in competitions:
        list_odds.append(parse_competition(competition, "football", *sites))
        print()
    return merge_dicts(list_odds)

def parse_football(*sites):
    """
    Stocke les cotes des principaux championnats de football en global
    """
    global main_odds
    main_odds = parse_main_competitions(*sites)
    winsound.Beep(262, 1000)
    winsound.Beep(330, 1000)
    winsound.Beep(392, 1000)

def parse_tennis(*sites):
    """
    Stocke les cotes des tournois de tennis en global
    """
    global odds_tennis
    odds_tennis = parse_competition("tennis", "tennis", *sites)

def parse_nba(*sites):
    """
    Stocke les cotes de la NBA en global
    """
    global odds_nba
    odds_nba = parse_competition("nba", "basketball", *sites)


def odds_match(match, sport="football"):
    """
    Retourne les cotes d'un match donné sur tous les sites de l'ARJEL
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
    Pour un match, un bookmaker, une somme à miser sur ce bookmaker et une cote
    minimale donnés, retourne la meilleure combinaison de paris à placer
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
        print(best_overall_odds, sites, sep='\n')
        return mises2(best_overall_odds, bet, best_i, True)
    except UnboundLocalError:
        print("No match found")




def best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport="football", date_max=None,
                    time_max=None, date_min=None, time_min=None, combine=False,
                    nb_matches_combine=2, freebet=False):
    """
    Fonction de base de détermination du meilleur match sur lequel parier en
    fonction de critères donnés
    """
    try:
        if combine:
            all_odds = all_odds_combine
        else:
            all_odds = main_odds if sport=="football" else odds_tennis if sport=="tennis" else odds_nba
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
        pprint(all_odds[best_match])
        display_function(best_overall_odds, best_rank)
        afficher_mises_combine(best_match.split(" + "), [sites], [result_function(best_overall_odds, best_rank)], all_odds[best_match]["odds"], sport, best_rank if freebet else None)
    except UnboundLocalError:
        print("No match found")



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
                    time_min)

def best_match_freebet(site, freebet, sport, date_max=None, time_max=None, date_min=None,
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


def best_matches_combine(site, minimum_odd, bet,sport, nb_matches=2, date_max=None,
                                 time_max=None, date_min=None, time_min=None):
    """
    Given a bookmaker, return on which matches you should share your freebet to
    maximize your gain
    """
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
        res = defined_bets2(odds_main, odds_second, main_sites, second_sites)
        return [gain_freebets+res[0], [bets]+res[1], [sites]+res[2]]
    return [0, [], []]

def best_matches_freebet(main_sites, freebets):
    """
    Compute of best way to bet freebets following the model
    [[bet, bookmaker], ...]
    """
    second_sites = {freebet[1] for freebet in freebets}
#     all_odds = merge_dicts([parse(url, *main_sites, *second_sites)
#                             for url in MAIN_CHAMPIONSHIPS])
#     all_odds = parse(LIGUE1, *main_sites, *second_sites)
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
#     for combine in combinations(all_odds.items(), nb_matches):
#         match_combine = " / ".join([match[0] for match in combine])
#         all_odds_combine[match_combine] = cotes_combine_all_sites(*[match[1] for match in combine], freebet=True)
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
#             potential_odds = cotes_freebet(
#                 cotes_combine([combine[x][1]['odds'][main]
#                                for x in range(nb_matches)]))
            potential_odds = all_odds_combine[match_combine]["odds"][main]
            for j, odd in enumerate(potential_odds):
                if odd>main_site_odds[j]:
                    main_site_odds[j] = odd
                    main_sites_distribution[j] = main
#         second_odds = {second_site:cotes_freebet(cotes_combine(
#             combine[x][1]['odds'][second_site] for x in range(nb_matches)))
#                        for second_site in second_sites}
        second_odds = {second_site:all_odds_combine[match_combine]["odds"][second_site] for second_site in second_sites}
#         dict_combine_odds = merge_dicts([{}, second_odds])
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
    
