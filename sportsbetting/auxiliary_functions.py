"""
Fonctions auxiliaires (peu utiles pour l'utilisateur)
"""

from itertools import product, chain
import collections
from pprint import pprint
import datetime
import copy
import itertools
import baseconvert
import sportsbetting
from sportsbetting.database_functions import (get_formatted_name, is_in_db_site, is_in_db,
                                              get_close_name, add_name_to_db,
                                              get_id_by_site, get_id_by_opponent, get_close_name2,
                                              get_close_name3, get_double_team_tennis,
                                              get_id_by_opponent_thesportsdb, get_competition_id,
                                              is_matching_next_match)

from sportsbetting.basic_functions import cotes_combine, cotes_freebet, mises2, mises, gain2


def valid_odds(all_odds, sport):
    """
    Retire les cotes qui ne comportent pas le bon nombre d'issues. Par exemple, si l'on n'a que 2
    cotes disponibles pour un match de football, alors ces cotes sont invalides et doivent être
    retirées
    """
    n = 2 + (sport not in ["tennis", "volleyball", "basketball"])
    copy_all_odds = copy.deepcopy(all_odds)
    for match in all_odds:
        for site in all_odds[match]["odds"]:
            if len(all_odds[match]["odds"][site]) != n or (all_odds[match]["date"] and all_odds[match]["date"] < datetime.datetime.today()):
                copy_all_odds[match]["odds"][site] = [1.01 for _ in range(n)]
    return copy_all_odds


def add_matches_to_db(odds, sport, site, id_competition):
    """
    :param odds: Cotes des matches
    :type odds: dict[str,int]
    :param sport: Sport
    :param site: Nom du bookmaker
    :return: Ajoute les équipes inconnues dans la base de données
    """
    matches = odds.keys()
    teams = set(chain.from_iterable(list(map(lambda x: x.split(" - "), list(matches)))))
    teams = set(map(lambda x: x.strip(), teams))
    teams_not_in_db_site = set()
    teams_sets = []
    for team in teams:
        line = is_in_db_site(team, sport, site)
        if not line:
            teams_not_in_db_site.add(team)
    if not teams_not_in_db_site:
        return
    print(list(teams_not_in_db_site), site)
    i = 0
    teams_sets.append(set())
    for team in teams_not_in_db_site:
        line = is_in_db(team, sport, site)
        if line:
            check = not is_matching_next_match(id_competition, line[0], team, odds)
            success = add_name_to_db(line[0], team, site, check)
            if not success:
                teams_sets[i].add(team)
        else:
            teams_sets[i].add(team)
    print(i, list(teams_sets[i]), site)
    if not teams_sets[i]:
        return
    get_close_name_functions = [get_close_name, get_close_name2]
    if sport == "tennis":
        get_close_name_functions.append(get_close_name3)
        get_close_name_functions.append(get_double_team_tennis)
    for only_null in [True, False]:
        for get_close_name_function in get_close_name_functions:
            i += 1
            teams_sets.append(set())
            for team in teams_sets[i - 1]:
                lines = get_close_name_function(team, sport, site, only_null)[:3] #Pour éviter d'avoir trop de résultats
                if lines:
                    for line in lines:
                        check = not is_matching_next_match(id_competition, line[0], team, odds)
                        success = add_name_to_db(line[0], team, site, check)
                        if not success:
                            teams_sets[i].add(team)
                else:
                    teams_sets[i].add(team)
            print(i, list(teams_sets[i]), site)
            if not teams_sets[i]:
                return
            i += 1
            teams_sets.append(set())
            for team in teams_sets[i - 1]:
                future_opponents, future_matches = get_future_opponents(team, matches)
                success = False
                for future_opponent, future_match in zip(future_opponents, future_matches):
                    id_opponent = get_id_by_site(future_opponent, sport, site)
                    if id_opponent < 0:
                        id_to_find = get_id_by_opponent_thesportsdb(id_opponent, future_match, odds)
                    else:
                        id_to_find = get_id_by_opponent(id_opponent, future_match, odds)
                    if id_to_find:
                        success = add_name_to_db(id_to_find, team, site)
                        if success:
                            break
                if not success:
                    teams_sets[i].add(team)
            print(i, list(teams_sets[i]), site)
            if not teams_sets[i]:
                return


def adapt_names(odds, site, sport, competition):
    """
    Uniformisation des noms d'équipe/joueur d'un site donné conformément aux noms disponibles sur
    comparateur-de-cotes.fr. Par exemple, le match "OM - PSG" devient "Marseille - Paris SG"
    """
    new_dict = {}
    id_competition = get_competition_id(competition, sport)
    add_matches_to_db(odds, sport, site, id_competition)
    for match in odds:
        new_match = " - ".join(list(map(lambda x: get_formatted_name(x.strip(), site, sport),
                                        match.split(" - "))))
        if "UNKNOWN TEAM/PLAYER" not in new_match:
            new_dict[new_match] = odds[match]
    return new_dict


def format_team_names(dict_odds, sport, competition):
    """
    Uniformisation des noms d'équipe/joueur entre tous les sites conformément aux noms disponibles
    sur comparateur-de-cotes.fr. Par exemple, le match "OM - PSG" devient "Marseille - Paris SG"
    """
    list_odds = []
    for site in dict_odds:
        list_odds.append(adapt_names(dict_odds[site], site, sport, competition))
    return list_odds


def merge_dict_odds(dict_odds):
    """
    Fusion des cotes entre les différents sites
    """
    new_dict = {}
    all_keys = set()
    for odds in dict_odds:
        all_keys = all_keys.union(odds.keys())
    for match in all_keys:
        new_dict[match] = {}
        new_dict[match]["odds"] = {}
        new_dict[match]["date"] = None
        date_found = False
        for odds in dict_odds:
            if odds:
                try:
                    site = list(list(odds.values())[0]["odds"].keys())[0]
                    if match in odds.keys() and odds[match]["odds"] and odds[match]["odds"][site]:
                        if (not date_found and odds[match]["date"] != "undefined"
                                and odds[match]["date"]):  # Si la date est None
                            new_dict[match]["date"] = odds[match]["date"]
                            date_found = True
                        new_dict[match]["odds"][site] = odds[match]["odds"][site]
                except IndexError:
                    print("ERREUR :", odds)
        if not date_found:
            new_dict[match]["date"] = datetime.datetime.today()
    return new_dict


def merge_dicts(dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    def_dict = collections.defaultdict(dict)
    for key, val in chain(*map(lambda x: x.items(), dict_args)):
        if val["date"]:
            def_dict[key]["date"] = val["date"]
        try:
            def_dict[key]["odds"].update(val["odds"])
        except KeyError:
            def_dict[key]["odds"] = val["odds"]
    return dict(def_dict)


def afficher_mises_combine(matches, sites, list_mises, cotes, sport="football",
                           rang_freebet=None, uniquement_freebet=False,
                           cotes_boostees=None, rang_2e_freebet=-1):
    """
    Affichage de la répartition des mises
    """
    opponents = []
    is_1n2 = sport not in ["tennis", "volleyball", "basketball", "nba"]
    for match in matches:
        opponents_match = match.split(" - ")
        if is_1n2:
            opponents_match.insert(1, "Nul")
        opponents.append(opponents_match)
    dict_combinaison = {}
    nb_chars = max(map(lambda x: len(" / ".join(x)), product(*opponents)))
    print("\nRépartition des mises (les totaux affichés prennent en compte les "
          "éventuels freebets):")
    for i, combinaison in enumerate(product(*opponents)):
        diff = nb_chars - len(" / ".join(combinaison))
        sites_bet_combinaison = {}
        for j, list_sites in enumerate(sites):
            if list_sites[i] in sites_bet_combinaison:
                if i in [rang_freebet, rang_2e_freebet] or uniquement_freebet:
                    sites_bet_combinaison[list_sites[i]]["mise freebet"] += list_mises[j][i]
                else:
                    sites_bet_combinaison[list_sites[i]]["mise"] += list_mises[j][i]
            else:
                sites_bet_combinaison[list_sites[i]] = {}
                if i in [rang_freebet, rang_2e_freebet] or uniquement_freebet:
                    sites_bet_combinaison[list_sites[i]]["mise freebet"] = list_mises[j][i]
                    sites_bet_combinaison[list_sites[i]]["cote"] = (cotes[list_sites[i]][i]
                                                                    + (not rang_freebet == i)
                                                                    - (rang_2e_freebet == i))
                else:
                    sites_bet_combinaison[list_sites[i]]["mise"] = list_mises[j][i]
                    sites_bet_combinaison[list_sites[i]]["cote"] = cotes[list_sites[i]][i]
        for site in sites_bet_combinaison:
            try:
                sites_bet_combinaison[site]["mise"] = round(sites_bet_combinaison[site]["mise"], 2)
            except KeyError:
                sites_bet_combinaison[site]["mise freebet"] = round((sites_bet_combinaison[site]
                ["mise freebet"]),
                                                                    2)
        if cotes_boostees and cotes_boostees[i] > cotes[sites[0][i]][i]:
            # Valable que s'il n'y a qu'un seul match
            sites_bet_combinaison["total boosté"] = round(cotes_boostees[i]
                                                          * (sites_bet_combinaison[sites[0][i]]
            ["mise"]),
                                                          2)
        else:
            try:
                sites_bet_combinaison["total"] = round(sum(x["cote"] * x["mise"]
                                                           for x in sites_bet_combinaison.values()),
                                                       2)
            except KeyError:
                sites_bet_combinaison["total"] = round(sum((x["cote"] - 1) * x["mise freebet"]
                                                           for x in sites_bet_combinaison.values()),
                                                       2)
        dict_combinaison[combinaison] = sites_bet_combinaison
        print(" / ".join(combinaison) + " " * diff + "\t", sites_bet_combinaison)


def find_almost_won_matches(best_matches, repartition_mises, sport, output=False):
    """
    Calcule la somme maximale remboursée pour une promotion du type pari rembourse si un seul
    résultat perdant, sans limite du nombre paris remboursés
    """
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
    list_combi = list(map(" / ".join, product(*opponents)))
    dict_index_almost_won = {}
    for gagnant, almost in dict_almost_won.items():
        dict_index_almost_won[gagnant] = list(map(list_combi.index, almost))
    if output:
        print("bonus min =", min(sum(repartition_mises[k] for k in list_index)
                                 for list_index in dict_index_almost_won.values()))
        print("bonus max =", max(sum(repartition_mises[k] for k in list_index)
                                 for list_index in dict_index_almost_won.values()))
    return max(sum(repartition_mises[k] for k in list_index)
               for list_index in dict_index_almost_won.values())


def cotes_combine_all_sites(*matches, freebet=False):
    """
    Calcule les cotes combinées de matches dont on connait les cotes sur plusieurs
    bookmakers
    """
    sites = set(matches[0]["odds"].keys())
    for match in matches:
        sites = sites.intersection(match["odds"].keys())
    combine_dict = {"date": max([match["date"] for match in matches]), "odds": {}}
    for site in sites:
        if freebet:
            combine_dict["odds"][site] = cotes_freebet(cotes_combine([match["odds"][site]
                                                                      for match in matches]))
        else:
            combine_dict["odds"][site] = cotes_combine([match["odds"][site] for match in matches])
    return combine_dict


def defined_bets(odds_main, odds_second, main_sites, second_sites):
    """
    second_sites type : [[rank, bet, site],...]
    """
    gain = 0
    bets = []
    if second_sites:
        sites = copy.deepcopy(main_sites)
        odds_adapted = copy.deepcopy(odds_main)
        for bet in second_sites:
            odds_adapted[bet[0]] = odds_second[bet[2]][bet[0]]
            sites[bet[0]] = bet[2]
        for bet in second_sites:
            valid = True
            bets = mises2(odds_adapted, bet[1], bet[0])
            gain = bet[1] * odds_adapted[bet[0]]
            for bet2 in second_sites:
                if bets[bet2[0]] - bet2[1] > 1e-6:  # Si on mise plus que ce qui est disponible
                    valid = False
                    break
            if valid:
                break
        index_to_del = []
        for i, elem in enumerate(second_sites):
            second_sites[i][1] -= bets[elem[0]]
            if elem[1] < 1e-6:
                index_to_del.append(i)
        for i in index_to_del[::-1]:
            del second_sites[i]
        res = defined_bets(odds_main, odds_second, main_sites, second_sites)
        return [gain + res[0], [bets] + res[1], [sites] + res[2]]
    return [0, [], []]


def get_future_opponents(name, matches):
    """
    Retourne la liste des futurs adversaires d'une équipe/joueur
    """
    future_opponents = []
    future_matches = []
    for match in matches:
        opponents = match.split(" - ")
        if name in opponents:
            try:
                opponents.remove(name)
                future_opponents.append(opponents[0].strip())
                future_matches.append(match)
            except ValueError:
                pass
            except IndexError:
                pass
    return future_opponents, future_matches

def best_combine_reduit(matches, combinaison_boostee, site_combinaison, mise, sport, cote_boostee=0):
    def get_odd(combinaison, matches, site_combinaison=None):
        sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet', 'parionssport',
                 'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']
        if site_combinaison:
            sites = [site_combinaison]
        best_odd = 1
        best_site = ""
        for site in sites:
            odd = 1
            for i, match in zip(combinaison, matches):
                if i!=float("inf"):
                    if site in sportsbetting.ODDS[sport][match]["odds"].keys():
                        odd *= sportsbetting.ODDS[sport][match]["odds"][site][i]
                    else:
                        break
            if odd > best_odd:
                best_odd = odd
                best_site = site
#         print(best_odd, best_site)
        return best_odd, best_site
    odds = {}
    for match in matches:
        odds[match] = sportsbetting.ODDS[sport][match]
    best_combinaison = []
    best_cotes = []
    best_sites = []
    best_gain = -mise
    best_i = -1
    for combinaisons in combine_reduit_rec(combinaison_boostee, sport):
        cotes = []
        sites = []
        for i, combinaison in enumerate(combinaisons):
            if list(combinaison) == combinaison_boostee:
                i_boost = i
                sites.append(site_combinaison)
                if cote_boostee:
                    cotes.append(cote_boostee)
                else:
                    cotes.append(get_odd(combinaison, matches, site_combinaison)[0])
            else:
                res = get_odd(combinaison, matches)
                cotes.append(res[0])
                sites.append(res[1])
        new_gain = gain2(cotes, i_boost, mise)
        if new_gain > best_gain:
            best_cotes = cotes
            best_sites = sites
            best_combinaison = combinaisons
            best_gain = new_gain
            best_i = i_boost
    matches_name = " / ".join(matches)
    print(matches_name)
    mises = mises2(best_cotes, mise, best_i)
    out = {}
    def get_issue(match, i, sport):
        if i==float("inf"):
            return
        elif sport in ["basketball", "tennis"]:
            return match.split(" - ")[i]
        elif i==1:
            return "Nul"
        else:
            return match.split(" - ")[i//2]
    opponents = []
    for match in matches:
        opponents_match = match.split(" - ")
        if sport not in ["basketball", "tennis"]:
            opponents_match.insert(1, "Nul")
        opponents.append(opponents_match)
    nb_chars = max(map(lambda x: len(" / ".join(x)), product(*opponents)))
    sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet', 'parionssport',
             'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']
    odds = {site: [get_odd(combine, matches, site)[0] for combine in best_combinaison] for site in sites}
    
    pprint({"date" : max(date for date in [sportsbetting.ODDS[sport][match]["date"]
                                           for match in matches]),
            "odds" :odds}, compact=True)
    print("plus-value =", round(best_gain, 2))
    print()
    print("Répartition des mises (les totaux affichés prennent en compte les éventuels freebets):")
    for combine, mise, cote, site in zip(best_combinaison, mises, best_cotes, best_sites):
        names = [opponents_match[i] if i!=float("inf") else "" for match, i, opponents_match in zip(matches, combine, opponents)]
        name_combine = " / ".join(x for x in names if x)
        diff = nb_chars - len(name_combine)
        sites_bet_combinaison = {site:{"mise":round(mise, 2), "cote":round(cote, 2)}, "total":round(round(mise, 2)*cote, 2)}
        print(name_combine + " " * diff + "\t", sites_bet_combinaison)


def best_match_base(odds_function, profit_function, criteria, display_function,
                    result_function, site, sport="football", date_max=None,
                    time_max=None, date_min=None, time_min=None, combine=False,
                    nb_matches_combine=2, freebet=False, one_site=False, recalcul=False,
                    combine_opt=False):
    """
    Fonction de base de détermination du meilleur match sur lequel parier en
    fonction de critères donnés
    """
    try:
        if combine:
            all_odds = filter_dict_dates(sportsbetting.ALL_ODDS_COMBINE, date_max, time_max,
                                         date_min, time_min)
        else:
            all_odds = filter_dict_dates(sportsbetting.ODDS[sport], date_max, time_max, date_min,
                                         time_min)
    except NameError:
        print("""
        Merci de définir les côtes de base, appelez la fonction parse_football,
        parse_nba ou parse_tennis selon vos besoins""")
        return
    best_profit = -float("inf")
    best_rank = 0
    if combine:
        n = (2 + (sport not in ["tennis", "volleyball", "basketball", "nba"])) ** nb_matches_combine
    else:
        n = 2 + (sport not in ["tennis", "volleyball", "basketball", "nba"])
    best_match = None
    best_overall_odds = None
    sites = None
    for match in all_odds:
        if site in all_odds[match]['odds']:
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
                if odd_i < 1.1 and site_i != "pmu":
                    break
            else:
                for i in range(n):
                    try:
                        odds_to_check = odds_function(best_odds, odds_site, i)
                        if criteria(odds_to_check, i):
                            profit = profit_function(odds_to_check, i)
                            if profit > best_profit:
                                best_rank = i
                                best_profit = profit
                                best_match = match
                                best_overall_odds = odds_to_check
                                sites = best_sites[:i] + [site] + best_sites[i + 1:]
                    except ZeroDivisionError:  # Si calcul freebet avec cote de 1
                        pass
    if best_match:
        if combine_opt and combine:
            ref_combinaison = list(reversed(baseconvert.base(best_rank, 10, get_nb_issues(sport))))
            n_combi = len(ref_combinaison)
            for _ in range(nb_matches_combine - n_combi):
                ref_combinaison.append(0)
            stakes = result_function(best_overall_odds, best_rank)
            best_combine_reduit(best_match.split(" / "), list(reversed(ref_combinaison)), site, stakes[best_rank], sport)
        else:
            print(best_match)
            pprint(all_odds[best_match], compact=True)
            if recalcul:
                sum_almost_won = find_almost_won_matches(best_match,
                                                        result_function(best_overall_odds,
                                                                        best_rank),
                                                        sport)
                display_function = lambda x, y: mises(x, 10000 * 50 / sum_almost_won, True)
                result_function = lambda x, y: mises(x, 10000 * 50 / sum_almost_won, False)
                find_almost_won_matches(best_match, result_function(best_overall_odds, best_rank),
                                        sport, True)
            second_rank = display_function(best_overall_odds, best_rank)
            afficher_mises_combine(best_match.split(" / "), [sites],
                                [result_function(best_overall_odds, best_rank)],
                                all_odds[best_match]["odds"], sport, best_rank if freebet else None,
                                one_site and freebet, best_overall_odds, second_rank)
    else:
        print("No match found")


def generate_sites(url_netbet):
    """
    Génère les url France-pari et ZEbet à partir d'un url NetBet
    """
    if any(char.isdigit() for char in url_netbet):
        id_ = url_netbet.split("/")[-1].split("-")[0]
        name = url_netbet.split(id_ + "-")[1]
        name_zebet = name.replace("-", "_")
        url_france_pari = "https://www.france-pari.fr/competition/{}-parier-sur-{}".format(id_,
                                                                                           name)
        url_zebet = "https://www.zebet.fr/fr/competition/{}-{}".format(id_, name_zebet)
        return url_france_pari, url_zebet

def datetime_from_strings(date_max=None, time_max=None, date_min=None, time_min=None):
    hour_max, minute_max = 0, 0
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
    hour_min, minute_min = 0, 0
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
    return datetime_max, datetime_min

def filter_dict_dates(odds, date_max=None, time_max=None, date_min=None, time_min=None):
    all_odds = copy.deepcopy(odds)
    datetime_max, datetime_min = datetime_from_strings(date_max, time_max, date_min, time_min)
    if datetime_max:
        all_odds = {k: v for k, v in all_odds.items() if v["date"] <= datetime_max}
    if datetime_min:
        all_odds = {k: v for k, v in all_odds.items() if v["date"] >= datetime_min}
    return all_odds

def combine_reduit(nb_matches, combi_to_keep, sport):
    def get_issues(combi_to_keep_aux):
        issues = [combi_to_keep_aux]
        base_issues = [i for i in range(get_nb_issues(sport))]
        for i, e in enumerate(combi_to_keep_aux):
            issue = combi_to_keep_aux[:i]
            for j in base_issues:
                if j != e:
                    issues.append(issue+[j]+[float("inf")]*(nb_matches-len(issue)-1))
        return issues
    def change_order(original, order):
        return [original[i] for i in order]
    all_issues = []
    for (i, (order, combi)) in enumerate(zip(itertools.permutations(list(range(nb_matches))),
                                             itertools.permutations(combi_to_keep)
                                             )
                                        ):
        all_issues.append(sorted(list(map(lambda x:change_order(x, order), get_issues(list(combi))))))
    return all_issues

def combine_reduit_rec(combi_to_keep, sport):
    n = len(combi_to_keep)
    if n <= 1:
        return [[[i] for i in range(get_nb_issues(sport))]]
    else:
        out = []
        for i in range(n):
            ref_combi = combi_to_keep[:i]+combi_to_keep[i+1:]
            combines_partiels = combine_reduit_rec(ref_combi, sport)
            for list_combi in combines_partiels:
                new_combi = []
                for combi in list_combi:
                    if combi != ref_combi:
                        copy_combi = copy.deepcopy(combi)
                        copy_combi.insert(i, float("inf"))
                        new_combi.append(copy_combi)
                    else:
                        for j in range(get_nb_issues(sport)):
                            copy_combi = copy.deepcopy(combi)
                            copy_combi.insert(i, j)
                            new_combi.append(copy_combi)
                out.append(new_combi)
        return out
            

def get_nb_issues(sport):
    return 2+(sport not in ["basketball", "tennis"])
