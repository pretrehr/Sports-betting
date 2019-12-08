"""
Fonctions auxiliaires (peu utiles pour l'utilisateur)
"""

import copy
from database_functions import get_formated_name

def valid_odds(all_odds, sport):
    """
    Retire les cotes qui ne comportent pas le bon nombre d'issues. Par exemple, si l'on n'a que 2
    cotes disponibles pour un match de football, alors ces cotes sont invalides et doivent être
    retiréess
    """
    n = 2 + (sport not in ["tennis", "volleyball", "basketball"])
    copy_all_odds = copy.deepcopy(all_odds)
    for match in all_odds:
        for site in all_odds[match]["odds"]:
            if len(all_odds[match]["odds"][site]) != n:
                del copy_all_odds[match]["odds"][site]
    return copy_all_odds

def adapt_names(odds, site, sport):
    """
    Uniformisation des noms d'équipe/joueur d'un site donnée conformément aux noms disponibles sur
    comparateur-de-cotes.fr. Par exemple, le match "OM - PSG" devient "Marseille - Paris SG"
    """
    new_dict = {}
    for match in odds:
        new_match = " - ".join(list(map(lambda x: get_formated_name(x, site, sport),
                                        match.split(" - "))))
        if "UNKNOWN TEAM/PLAYER" not in new_match:
            new_dict[new_match] = odds[match]
    return new_dict

def format_team_names(dict_odds, sport):
    """
    Uniformisation des noms d'équipe/joueur entre tous les sites conformément aux noms disponibles
    sur comparateur-de-cotes.fr. Par exemple, le match "OM - PSG" devient "Marseille - Paris SG"
    """
    list_odds = []
    for site in dict_odds:
        if site in ["netbet", "zebet", "france_pari", "joa"]:
            list_odds.append(adapt_names(dict_odds[site], "netbet", sport))
        else:
            list_odds.append(adapt_names(dict_odds[site], site, sport))
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
                site = list(list(odds.values())[0]["odds"].keys())[0]
                if match in odds.keys() and odds[match]["odds"][site]:
                    if not date_found and odds[match]["date"] != "undefined":
                        new_dict[match]["date"] = odds[match]["date"]
                        date_found = True
                    new_dict[match]["odds"][site] = odds[match]["odds"][site]
    return new_dict

def merge_dicts(dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result
