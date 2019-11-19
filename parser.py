#!/usr/bin/env python3
"""
functions for parsing odds on http://www.comparateur-de-cotes.fr
"""

from copy import deepcopy
from pprint import pprint
from itertools import combinations, permutations
import datetime
import urllib
import urllib.error
import urllib.request
import time
import os
import sys
import winsound
import copy
from bs4 import BeautifulSoup
import numpy as np
os.chdir(os.path.dirname(os.path.realpath('__file__')))
from bet_functions import (gain, gain2, mises2, cotes_combine, cotes_freebet,
                           pari_rembourse_si_perdant, mises_freebet,
                           merge_dicts)

PREFIX = "http://www.comparateur-de-cotes.fr/"
LIGUE1 = PREFIX+"comparateur/football/France-Ligue-1-ed3"
PREMIER_LEAGUE = PREFIX+"comparateur/football/Angleterre-Premier-League-ed7"
LIGA = PREFIX+"comparateur/football/Espagne-LaLiga-ed6"
BUNDESLIGA = PREFIX+"comparateur/football/Allemagne-Bundesliga-ed4"
SERIE_A = PREFIX+"comparateur/football/Italie-Serie-A-ed5"
CHAMPIONS_LEAGUE = PREFIX+"comparateur/football/Ligue-des-Champions-ed7"
EUROPA_LEAGUE = PREFIX+"comparateur/football/Ligue-Europa-ed1181"
TENNIS = PREFIX+"comparateur/tennis"
NBA = PREFIX+"comparateur/basketball/Etats-Unis-NBA-ed353"
TOP14 = PREFIX+"comparateur/rugby/France-Top-14-ed341"
OFFLINE = "file:///D:/Rapha%C3%ABl/Mes%20documents/Paris/surebet.html"
SPORTS = ["football", "basketball", "tennis", "hockey", "volleyball", "boxe",
          "rugby", "handball"]
MAIN_CHAMPIONSHIPS = [LIGUE1, PREMIER_LEAGUE, LIGA, BUNDESLIGA, SERIE_A,
                      CHAMPIONS_LEAGUE, EUROPA_LEAGUE, "http://www.comparateur-de-cotes.fr/comparateur/football/Qualifs.-Euro-2020-ed251"]

def parse(url, *particular_sites, is_1N2=True, is_basketball=False):
    """
    Given a url from 'comparateur-de-cotes.fr' and some bookmakers,
    return a hashmap of the matches and the odds of the bookmakers
    """
    if is_1N2:
        n = 3
    else:
        n = 2
    try:
        soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    except UnicodeEncodeError:
        url = url.replace('é', 'e').replace('è', 'e')
        soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    except urllib.error.URLError:
        print("No Internet connection")
        return {}
    compet_name = (url.split("-ed")[0].split(PREFIX+"comparateur/")[1]
                   .replace("-", " ").split("/")[1])
    print(compet_name, (47-len(compet_name))*" ", "last update:",
          str(soup).split("créée le  ")[1].split("</div>")[0])
    match_odds_hash = {}
    count_teams = 0
    count_odds = 0
    odds = []
    match = ""
    date = None
    surebet = False
    surebet_matches = []
    for line in soup.find_all(['a', 'td', 'img']):
        if (line.name == 'a' and 'class' in line.attrs):
            if count_teams == 0:
                sites_in_dict = True
                if match:
                    for site in particular_sites:
                        if site not in match_odds_hash[match]['odds']:
                            sites_in_dict = False
                            break
                    if (not match_odds_hash[match] or not sites_in_dict):
                        del match_odds_hash[match]
                match = ""
            match += line.text
            if count_teams == 0:
                match += ' - '
                count_teams += 1
            else:
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {}
                match_odds_hash[match]['date'] = date
                count_teams = 0
                if "surebetbox" in line.findParent().findParent()['class']:
                    surebet = True
                    surebet_matches.append(match)
        elif 'src' in line.attrs:
            if 'logop' in line['src']:
                site = line['src'].split('-')[1].split('.')[0]
        elif (line.name == 'td'
              and 'class' in line.find_parent().find_parent().attrs
              and "bettable" in line.find_parent().find_parent()['class']
              and 'à' in line.text):
            date = convert_date(list(line.stripped_strings)[3].split('à'))
        elif 'class' in line.attrs and 'bet' in line['class']:
            if ((not particular_sites) or site in particular_sites):
                if "-" not in line.text:
                    odds.append(float(line.text))
                else:
                    odds.append("-")
                if count_odds < n-1:
                    count_odds += 1
                else:
                    if is_basketball:
                        if "-" not in odds and is_basketball:
                            odds[0] /= 1.1
                            odds[2] /= 1.1
                        del odds[1]
                    match_odds_hash[match]['odds'][site] = odds
                    count_odds = 0
                    odds = []
    sites_in_dict = True
    for site in particular_sites:
        try:
            if site not in match_odds_hash[match]['odds']:
                sites_in_dict = False
                break
        except KeyError:
            pass
    if (match and not match_odds_hash[match]['odds']) or not sites_in_dict:
        del match_odds_hash[match]
    if surebet:
        print("*************************** SUREBET ***************************")
        print(surebet_matches)
    return match_odds_hash


def parse_sport(sport, *particular_sites):
    """
    Return the odds of all the matches of a given sport
    """
    match_odds_hash = {}
    try:
        _1N2 = sport not in ["volleyball", "tennis"]
#         if sport == "basketball":
#             return parse(NBA, is_basketball=True)
        competitions = []
        try:
            soup = BeautifulSoup(urllib.request.urlopen(PREFIX+"comparateur/"+sport),
                                 features="lxml")
        except urllib.error.URLError:
            print("No Internet connection")
            return match_odds_hash
        for line in soup.find_all(['a', 'td', 'img']):
            if (line.name == 'a' and 'href' in line.attrs):
                if sport in line['href'] and "ed" in line['href']:
                    competitions.append(PREFIX+line['href'])
        for url in competitions:
            if sport == "basketball":
                parsing = parse(url, *particular_sites, is_basketball=True)
            else:
                parsing = parse(url, *particular_sites, is_1N2=_1N2)
            match_odds_hash.update(parsing)
    except KeyboardInterrupt:
        try:
            print("Sport skipped, repress to end process")
            instant = time.time()
            while time.time()-instant < 1:
                pass
        except KeyboardInterrupt:
            match_odds_hash["KeyboardInterrupt"] = True
    return match_odds_hash

def parse_all_1N2(*particular_sites):
    """
    Return the odds of all the matches where draw is possible
    """
    match_odds_hash = {}
    for sport in SPORTS:
        if sport not in ["tennis", "volleyball", "basketball"]:
            print("\n"+sport.capitalize())
            parsing = parse_sport(sport, *particular_sites)
            if "KeyboardInterrupt" in parsing:
                del parsing["KeyboardInterrupt"]
                print("Process ended\n")
                match_odds_hash.update(parsing)
                break
            match_odds_hash.update(parsing)
    return match_odds_hash

def parse_all_12(*particular_sites):
    """
    Return the odds of all the matches where tie is not possible
    """
    match_odds_hash = {}
    for sport in ["tennis", "volleyball", "basketball"]:
        print(sport)
        parsing = parse_sport(sport, *particular_sites)
        if "KeyboardInterrupt" in parsing:
            print(sport)
            del parsing["KeyboardInterrupt"]
            match_odds_hash.update(parsing)
            break
        match_odds_hash.update(parsing)
    return match_odds_hash

def parse_all(*particular_sites):
    """
    Return the odds of all the matches
    """
    match_odds_hash = parse_all_1N2(*particular_sites)
    match_odds_hash.update(parse_all_12(*particular_sites))
    return match_odds_hash


def best_matches_freebet_tennis(site, nb_matches=5):
    """
    Given a bookmaker, return on which tennis matches you should share your
    freebet to maximize your gain
    """
    all_odds = parse_sport("tennis", site)
    best_rate = 0
    for combine in combinations(all_odds.items(), nb_matches):
        odds = cotes_combine([combine[x][1]['odds'][site]
                              for x in range(nb_matches)])
        freebet_odds = cotes_freebet(odds)
        rate = gain(freebet_odds)
        if rate > best_rate:
            best_rate = rate
            best_matches = combine
    print(best_rate if best_rate > 0 else '')
    try:
        return best_matches
    except UnboundLocalError:
        print("No match found")

def best_matches_freebet(site, nb_matches=2):
    """
    Given a bookmaker, return on which matches you should share your freebet to
    maximize your gain
    """
#     all_odds = parse_sport("football")
    all_odds = main_odds
    best_rate = 0
    for combine in combinations(all_odds.items(), nb_matches):
        odds = cotes_combine([combine[x][1]['odds'][site] if site in combine[x][1]['odds'] else [0]
                              for x in range(nb_matches)])
        freebet_odds = cotes_freebet(odds)
        rate = gain(freebet_odds)
        if rate > best_rate:
            best_rate = rate
            best_matches = combine
    print(best_rate if best_rate > 0 else '')
    try:
        return best_matches
    except UnboundLocalError:
        print("No match found")

def best_matches_freebet2(main_site, second_site, nb_matches=2):
    """
    Given two bookmakers, return on which matches you should share your freebets
    to maximize your gain, knowing you bet only once on second_site
    """
#     all_odds = parse_all_1N2(main_site, second_site)
#     all_odds = parse_sport("rugby", main_site, second_site)
    new_odds = copy.deepcopy(main_odds)
    all_odds = {}
    for match in new_odds:
        if main_site in new_odds[match]["odds"].keys() and second_site in new_odds[match]["odds"].keys():
            all_odds[match] = new_odds[match]
    best_rate = 0
    n = 3**nb_matches
    for combine in combinations(all_odds.items(), nb_matches):
        main_site_odds = cotes_freebet(cotes_combine(
            [combine[x][1]['odds'][main_site] for x in range(nb_matches)]))
        second_odds = cotes_freebet(cotes_combine(
            [combine[x][1]['odds'][second_site] for x in range(nb_matches)]))
        for i, e in enumerate(second_odds):
            odds_to_check = main_site_odds[:i]+[e]+main_site_odds[i+1:]
            rate = gain(odds_to_check)
            if rate > best_rate:
                best_rate = rate
                best_odds = odds_to_check
                best_matches = combine
                sites_combine = [main_site]*i+[second_site]+[main_site]*(n-1-i)
    print(best_rate)
    print(sites_combine)
    print(best_odds)
    return best_matches

def best_matches_freebet3(main_site, second_site, nb_freebet_second_site,
                          nb_matches=2):
    """
    Given two bookmakers, return on which matches you should share your freebets
    to maximize your gain, knowing you bet nb_freebet_second_site times on
    second_site
    """
    championships = [LIGUE1, PREMIER_LEAGUE, LIGA, BUNDESLIGA, SERIE_A,
                     EUROPA_LEAGUE, CHAMPIONS_LEAGUE]
    all_odds = merge_dicts([parse(url, main_site, second_site)
                            for url in championships])
    best_rate = 0
    n = 3**nb_matches
    for combine in combinations(all_odds.items(), nb_matches):
        main_odds = cotes_freebet(cotes_combine(
            [combine[x][1]['odds'][main_site] for x in range(nb_matches)]))
        second_odds = cotes_freebet(cotes_combine(
            [combine[x][1]['odds'][second_site] for x in range(nb_matches)]))
        for combi in combinations(list(range(n)), nb_freebet_second_site):
            i = combi[0]
            j = combi[1]
            odds_to_check = (main_odds[:i]+[second_odds[i]]+main_odds[i+1:j]
                             +[second_odds[j]]+main_odds[j+1:])
            rate = gain(odds_to_check)
            if rate > best_rate:
                best_rate = rate
                best_odds = odds_to_check
                best_matches = combine
                sites_combine = [main_site]*n
                sites_combine[i] = second_site
                sites_combine[j] = second_site
    print(best_rate)
    print(sites_combine)
    print(best_odds)
    return best_matches


def best_matches_freebet4(main_site, freebets):
    """
    Compute of best way to bet freebets following the model
    [[bet, bookmaker], ...]
    """
    second_sites = {freebet[1] for freebet in freebets}
#     all_odds = merge_dicts([parse(url, main_site, *second_sites)
#                             for url in MAIN_CHAMPIONSHIPS])
    print(second_sites)
    new_odds = copy.deepcopy(main_odds)
    all_odds = {}
    for match in new_odds:
        if not(any([site not in new_odds[match]["odds"].keys() for site in list(second_sites)+[main_site]])):
#             if match in ['Lyon - Benfica', 'Borussia Dortmund - Inter Milan']:
                all_odds[match] = new_odds[match]
    best_rate = 0
    nb_matches = 2
    n = 3**nb_matches
    nb_freebets = len(freebets)
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
        main_site_odds = cotes_freebet(
            cotes_combine([combine[x][1]['odds'][main_site]
                           for x in range(nb_matches)]))
        second_odds = {second_site:cotes_freebet(cotes_combine(
            combine[x][1]['odds'][second_site] for x in range(nb_matches)))
                       for second_site in second_sites}
        dict_combine_odds = merge_dicts([{main_site:main_site_odds}, second_odds])
        for perm in permutations(range(n), nb_freebets):
            defined_second_sites = [[perm[i], freebet[0], freebet[1]]
                                    for i, freebet in enumerate(freebets)]
            copy_second_sites = deepcopy(defined_second_sites)
            defined_bets_temp = defined_bets(dict_combine_odds,
                                             main_site, defined_second_sites)
            if defined_bets_temp[0]/np.sum(defined_bets_temp[1]) > best_rate:
                best_rate = defined_bets_temp[0]/np.sum(defined_bets_temp[1])
                best_combine = combine
                best_bets = defined_bets_temp
                best_defined_second_sites = copy_second_sites
                best_dict_combine_odds = dict_combine_odds
    pprint((best_rate, best_combine[0][0], best_combine[1][0], best_bets))
    pprint(best_dict_combine_odds)
    pprint(best_defined_second_sites)
    print(time.time()-start)
    return best_bets[1]

def best_matches_freebet5(main_sites, freebets):
    """
    Compute of best way to bet freebets following the model
    [[bet, bookmaker], ...]
    """
    second_sites = {freebet[1] for freebet in freebets}
#     all_odds = merge_dicts([parse(url, *main_sites, *second_sites)
#                             for url in MAIN_CHAMPIONSHIPS])
#     all_odds = parse(LIGUE1, *main_sites, *second_sites)
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
        main_sites_distribution = [main_sites[0] for _ in range(n)]
        main_site_odds = cotes_freebet(
            cotes_combine([combine[x][1]['odds'][main_sites[0]]
                           for x in range(nb_matches)]))
        for main in main_sites[1:]:
            potential_odds = cotes_freebet(
                cotes_combine([combine[x][1]['odds'][main]
                               for x in range(nb_matches)]))
            for j, odd in enumerate(potential_odds):
                if odd>main_site_odds[j]:
                    main_site_odds[j] = odd
                    main_sites_distribution[j] = main
        second_odds = {second_site:cotes_freebet(cotes_combine(
            combine[x][1]['odds'][second_site] for x in range(nb_matches)))
                       for second_site in second_sites}
        dict_combine_odds = merge_dicts([{}, second_odds])
        for perm in permutations(range(n), nb_freebets):
            defined_second_sites = [[perm[i], freebet[0], freebet[1]]
                                    for i, freebet in enumerate(freebets)]
            copy_second_sites = deepcopy(defined_second_sites)
            defined_bets_temp = defined_bets2(main_site_odds, dict_combine_odds,
                                              main_sites_distribution,
                                              defined_second_sites)
            if defined_bets_temp[0]/np.sum(defined_bets_temp[1]) > best_rate:
                best_rate = defined_bets_temp[0]/np.sum(defined_bets_temp[1])
                best_combine = combine
                best_bets = defined_bets_temp
                best_defined_second_sites = copy_second_sites
                best_dict_combine_odds = dict_combine_odds
    pprint((best_rate, best_combine[0][0], best_combine[1][0], best_bets))
    pprint(best_dict_combine_odds)
    pprint(best_defined_second_sites)
    print(time.time()-start)
    return best_bets[1]

def defined_bets(odds, main_site, second_sites):
    """
    second_sites type : [[rank, bet, site],...]
    """
    if second_sites:
        odds_adapted = deepcopy(odds[main_site])
        sites = [main_site for _ in odds[main_site]]
        for bet in second_sites:
            odds_adapted[bet[0]] = odds[bet[2]][bet[0]]
            sites[bet[0]] = bet[2]
        for bet in second_sites:
            valid = True
            bets = mises2(odds_adapted, bet[1], bet[0])
            gain_freebets = bets[0]*odds_adapted[0]
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
        res = defined_bets(odds, main_site, second_sites)
        return [gain_freebets+res[0], [bets]+res[1], [sites]+res[2]]
    return [0, [], []]

def defined_bets2(odds_main, odds_second, main_sites, second_sites):
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
            gain_freebets = bets[0]*odds_adapted[0]
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


def best_match_freebet_tennis_basket(site, sport='tennis', freebet=None):
    """
    Given a bookmaker and a sport (nba or tennis), return on which match you
    should bet your freebet to maximize your gain.
    """
#     all_odds = parse_sport("tennis") if sport == 'tennis' else parse_sport("basketball")
#     all_odds = nba_odds
    all_odds = odds_tennis if sport == 'tennis' else odds_nba
    best_profit = 0
    for match in all_odds.keys():
        if site in all_odds[match]['odds']:
            odds_site = all_odds[match]['odds'][site]
            best_odds = deepcopy(odds_site)
            best_sites = [site, site]
            for odds in all_odds[match]['odds'].items():
                for i in range(2):
                    if odds[1][i] > best_odds[i]:
                        best_odds[i] = odds[1][i]
                        best_sites[i] = odds[0]
            for i in range(2):
                if odds_site[i] > 1:
                    odds_to_check = (best_odds[:i]
                                     +[odds_site[i]-1]+best_odds[i+1:])
                else:
                    odds_to_check = best_odds[:i]+[0.01]+best_odds[i+1:]
                profit = gain2(odds_to_check, i)+1
                if profit > best_profit:
                    best_rank = i
                    odds_to_check[i] += 1
                    best_profit = profit
                    best_match = match
                    best_overall_odds = odds_to_check
                    sites = best_sites[:i]+[site]+best_sites[i+1:]
    try:
        print(best_match, all_odds[best_match]["date"], best_profit, sites, best_overall_odds, sep='\n')
        if freebet:
            print(mises_freebet(best_overall_odds, freebet, best_rank, True))
    except UnboundLocalError:
        print("No match found, you're looking for matches of {} available on {}"
              .format(sport, site))

def best_match_freebet_football(site, freebet=None):
    """
    Given a bookmaker, return on which match you should bet your freebet to
    maximize your gain.
    """
#     all_odds = merge_dicts([parse_sport("rugby"), parse_sport("football")])
#     del all_odds['Namibie - Canada']
#     del all_odds['Australie - Uruguay']
    all_odds = main_odds
    best_profit = 0
    for match in all_odds:
        if site in all_odds[match]['odds']:
            odds_site = all_odds[match]['odds'][site]
            best_odds = deepcopy(odds_site)
            best_sites = [site, site, site]
            for odds in all_odds[match]['odds'].items():
                for i in range(3):
                    if odds[1][i] > best_odds[i]:
                        best_odds[i] = odds[1][i]
                        best_sites[i] = odds[0]
            for i in range(3):
                if odds_site[i] > 1:
                    odds_to_check = (best_odds[:i]
                                     +[odds_site[i]-1]+best_odds[i+1:])
                else:
                    odds_to_check = best_odds[:i]+[0.01]+best_odds[i+1:]
                profit = gain2(odds_to_check, i)+1
                if profit > best_profit:
                    best_rank = i
                    odds_to_check[i] += 1
                    best_profit = profit
                    best_match = match
                    best_overall_odds = odds_to_check
                    sites = best_sites[:i]+[site]+best_sites[i+1:]
    try:
        print(best_match, all_odds[best_match]["date"], best_profit, sites, best_overall_odds, sep='\n')
        if freebet:
            print(mises_freebet(best_overall_odds, freebet, best_rank, True))
    except UnboundLocalError:
        print("No match found")

def best_match_under_conditions(site, minimum_odd, bet, one_site=False, live=False,
                                date_max=None, time_max=None,
                                date_min=None, time_min=None):
    """
    Given a bookmaker, return on which match you should bet to maximize your
    gain, knowing that you need to bet a bet on a minimum odd before a limit
    date
    """ 
#     all_odds = parse_sport("football")
#     all_odds = parse(LIGUE1)
    all_odds = main_odds
    best_profit = -bet
    best_rank = 0
    hour_max, minute_max = 0, 0
    hour_min, minute_min = 0, 0
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
            best_sites = [site, site, site]
            if not one_site:
                for odds in all_odds[match]['odds'].items():
                    for i in range(3):
                        if odds[1][i] > best_odds[i]:
                            best_odds[i] = odds[1][i]
                            best_sites[i] = odds[0]
            for i in range(3):
                odds_to_check = (best_odds[:i]
                                 +[odds_site[i]*0.9 if live else odds_site[i]]
                                 +best_odds[i+1:])
                if odds_to_check[i] >= minimum_odd:
                    profit = gain(odds_to_check, bet)-bet if one_site else gain2(odds_to_check, i, bet)
                    if profit > best_profit:
                        best_rank = i
                        best_profit = profit
                        best_match = match
                        best_overall_odds = odds_to_check
                        sites = best_sites[:i]+[site]+best_sites[i+1:]
    try:
        print(best_match)
        print(all_odds[best_match]['date'])
        print(best_overall_odds, sites)
        if one_site:
            print(mises(best_overall_odds, bet, True))
        else:
            print(mises2(best_overall_odds, bet, best_rank, True))
    except UnboundLocalError:
        print("No match found")

def best_match_under_conditions_tennis_basket(site, sport, minimum_odd, bet,
                                              date_max=None, time_max=None,
                                              date_min=None, time_min=None):
    """
    Given a bookmaker, return on which match you should bet to maximize your
    gain, knowing that you need to bet a bet on a minimum odd before a limit
    date
    """
#     all_odds = parse_sport("basketball") if sport == 'nba' else parse_sport("tennis")
    all_odds = odds_tennis if sport == "tennis" else odds_nba
    best_profit = -bet
    best_rank = 0
    hour_max, minute_max = 0, 0
    hour_min, minute_min = 0, 0
    if time_max:
        if time_max[-1] == 'h':
            hour_max = int(time_max[:-1])
        else:
            hour_max, minute_max = (int(_) for _ in time_max.split('h'))
    if date_max:
        day_max, month_max, year_max = (int(_) for _ in date_max.split('/'))
        datetime_max = datetime.datetime(year_max, month_max, day_max, hour_max,
                                minute_max)
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
            best_sites = [site, site]
            for odds in all_odds[match]['odds'].items():
                for i in range(2):
                    if odds[1][i] > best_odds[i]:
                        best_odds[i] = odds[1][i]
                        best_sites[i] = odds[0]
            for i in range(2):
                odds_to_check = best_odds[:i]+[odds_site[i]]+best_odds[i+1:]
                if odds_to_check[i] >= minimum_odd:
                    profit = gain2(odds_to_check, i, bet)
                    if profit > best_profit:
                        best_rank = i
                        best_profit = profit
                        best_match = match
                        best_overall_odds = odds_to_check
                        sites = best_sites[:i]+[site]+best_sites[i+1:]
    try:
        print(best_match)
        print(all_odds[best_match]['date'])
        print(best_overall_odds, sites)
        print(mises2(best_overall_odds, bet, best_rank, True))
    except UnboundLocalError:
        print("No match found")

def convert_date(date):
    """
    Given a date array like ["Samedi 1 décembre 2011", "9h45"], return
    datetime.datetime(2011, 12, 1, 9, 45)
    """
    months = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
              "août", "septembre", "octobre", "novembre", "décembre"]
    date_array = date[0].split()
    del date_array[0]
    date_array[1] = months.index(date_array[1])+1
    hour_array = date[1].split('h')
    return datetime.datetime(int(date_array[2]), date_array[1], int(date_array[0]),
                    int(hour_array[0]), int(hour_array[1]))

def best_match_cashback(site, minimum_odd, bet, freebet=True, combi_max=0,
                        combi_odd=1, rate_cashback=1, date_max=None,
                        time_max=None, date_min=None, time_min=None):
    """
    Given several conditions, return the best match to bet on to maximize
    the gain with a cashback-like promotion
    """
#     all_odds = parse_all_1N2()
#     all_odds = parse(LIGUE1)
#     all_odds = parse_sport("football", "betclic")
#     all_odds = merge_dicts([parse(url) for url in MAIN_CHAMPIONSHIPS])
    all_odds = main_odds
    best_profit = -bet
    best_rank = 0
    hour_max, minute_max = 0, 0
    hour_min, minute_min = 0, 0
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
            best_sites = [site, site, site]
            for odds in all_odds[match]['odds'].items():
                for i in range(3):
                    if odds[1][i] > best_odds[i]:
                        best_odds[i] = odds[1][i]
                        best_sites[i] = odds[0]
            for i in range(3):
                odds_to_check = (best_odds[:i]
                                +[combi_odd*odds_site[i]]
                                +best_odds[i+1:])
                if odds_to_check[i] >= minimum_odd:
                    odds_to_check[i] = odds_to_check[i]*(1+combi_max)-combi_max
                    profit = pari_rembourse_si_perdant(odds_to_check, bet, i,
                                                       freebet, rate_cashback)
                    if profit > best_profit:
                        best_rank = i
                        best_profit = profit
                        best_match = match
                        best_overall_odds = odds_to_check
                        sites = best_sites[:i]+[site]+best_sites[i+1:]
    try:
        print(best_match)
        print(all_odds[best_match]['date'])
        print(best_overall_odds, sites)
        return pari_rembourse_si_perdant(best_overall_odds, bet, best_rank, freebet,
                                         rate_cashback, True)
    except UnboundLocalError:
        print("No match found")

def best_match_cashback_tennis_basket(site, sport, minimum_odd, bet,
                                      freebet=True, combi_max=0,
                                      combi_odd=1, rate_cashback=1,
                                      date_max=None, time_max=None,
                                      date_min=None, time_min=None):
    """
    Given several conditions, return the best match to bet on to maximize
    the gain with a cashback-like promotion
    """
#     all_odds = parse_sport("basketball") if sport == 'nba' else parse_sport("tennis")
#     all_odds = parse("http://www.comparateur-de-cotes.fr/comparateur/basketball/Coupe-du-Monde-FIBA-(H)-ed1487", is_basketball=1)
    all_odds = odds_tennis if sport == "tennis" else odds_nba
    best_profit = 0
    best_rank = 0
    hour_max, minute_max = 0, 0
    hour_min, minute_min = 0, 0
    if time_max:
        if time_max[-1] == 'h':
            hour_max = int(time_max[:-1])
        else:
            hour_max, minute_max = (int(_) for _ in time_max.split('h'))
    if date_max:
        day_max, month_max, year_max = (int(_) for _ in date_max.split('/'))
        datetime_max = datetime.datetime(year_max, month_max, day_max, hour_max,
                                minute_max)
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
            best_sites = [site, site]
            for odds in all_odds[match]['odds'].items():
                for i in range(2):
                    if odds[1][i] > best_odds[i]:
                        best_odds[i] = odds[1][i]
                        best_sites[i] = odds[0]
            for i in range(2):
                odds_to_check = (best_odds[:i]
                                +[combi_odd*odds_site[i]]
                                +best_odds[i+1:])
                if odds_to_check[i] >= minimum_odd:
                    odds_to_check[i] = odds_to_check[i]*(1+combi_max)-combi_max
                    profit = pari_rembourse_si_perdant(odds_to_check, bet, i,
                                                    freebet, rate_cashback)
                    if profit > best_profit:
                        best_rank = i
                        best_profit = profit
                        best_match = match
                        best_overall_odds = odds_to_check
                        sites = best_sites[:i]+[site]+best_sites[i+1:]
    try:
        print(best_match)
        print(all_odds[best_match]['date'])
        print(best_overall_odds, sites)
        return pari_rembourse_si_perdant(best_overall_odds, bet, best_rank, freebet,
                                  rate_cashback, True)
    except UnboundLocalError:
        print("No match found")

def odds_basket():
    """
    Estimate the odds of 12 when having 1N2 on NBA matches
    """
    #TODO
    file = open("D:/Raphaël/Mes documents/Paris/basket_odds_betclic.csv")
    lines = file.readlines()
    file.close()
    odds = []
    for line in lines:
        line.replace(',', '.')
        odds.append([float(_)
                     for _ in line.strip().replace(',', '.').split(';')])
    return odds

def odds_match(match, sport="football"):
    """
    Return the different odds of a given match
    """
#     all_odds = parse_all()
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
    print(best_profit, sites, best_overall_odds, bets, sep='\n')

def repeat_research():
    while True:        
        saved_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        res_football = best_match_cashback("winamax", 1.1, 100, rate_cashback=0.9)
        res_tennis = best_match_cashback_tennis_basket("winamax", "tennis", 1.1, 100, rate_cashback=0.9)
        sys.stdout = saved_stdout
        print(res_football, res_tennis)
        winsound.Beep(262, 1000)
        winsound.Beep(330, 1000)
        winsound.Beep(392, 1000)
        sys.stdout = open(os.devnull, "w")
        while (res_football<50 and res_tennis<50):
            res_football = best_match_cashback("winamax", 1.1, 100, rate_cashback=0.9)
            res_tennis = best_match_cashback_tennis_basket("winamax", "tennis", 1.1, 100, rate_cashback=0.9)
            if res_football is None:
                break
        if res_football is None:
            sys.stdout = saved_stdout
            break

def best_odds(match_odds):
    best_odds_list = list(match_odds.values())[0]
    n = len(best_odds_list)
    default_site = list(match_odds.keys())[0]
    best_sites = [default_site for _ in range(n)]
    for site, odds in match_odds.items():
        for i, odd in enumerate(odds):
            if odd>best_odds_list[i]:
                best_odds_list[i] = odd
                best_sites[i] = site
    return best_odds_list, best_sites

def find_surebets(list_matches):
    surebets = []
    for match, values in list_matches.items():
        odds, sites = best_odds(values["odds"])
        if gain(odds)>=1:
            surebets.append((match, odds, sites))
    if surebets:
        print("*************************** SUREBET ***************************")
        return surebets
    
        