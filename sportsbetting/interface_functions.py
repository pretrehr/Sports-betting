import ast
import datetime
import numpy as np
import sys
import io
from sportsbetting.user_functions import (best_match_under_conditions,
                                          best_match_freebet, best_stakes_match, best_matches_freebet,
                                          best_matches_combine, best_match_cashback,
                                          best_match_stakes_to_bet)

whatWasPrintedCombine = ""

def odds_table(result):
    lines = result.split("\n")
    for i, line in enumerate(lines):
        if "}}" in line:
            break
    dict_odds = eval("".join(lines[1:i+1]))
    odds = dict_odds["odds"]
    table = []
    for key, value in odds.items():
        table.append([key]+list(map(str, value)))
    return(table)

def indicators(result):
    lines = result.split("}}\n")[1].split("\nmises arrondies")[0].split("\n")
    for line in lines:
        if not line:
            break
        yield line.split(" = ")

def stakes(result):
    return result.split("\n\n")[-1]

def infos(result):
    lines = result.split("\n")
    match = lines[0]
    if match == "No match found":
        return None, None
    for i, line in enumerate(lines):
        if "}}" in line:
            break
    dict_odds = eval("".join(lines[1:i+1]))
    date = dict_odds["date"]
    return match, date.strftime("%A %d %B %Y %H:%M")

def odds_table_combine(result):
    lines = result.split("\n")
    for i, line in enumerate(lines):
        if "}}" in line:
            break
    dict_odds = eval("".join(lines[1:i+1]))
    odds = dict_odds["odds"]
    table = []
    combinaisons = []
    for line in result.split("freebets):\n")[1].split("\n"):
        combinaisons.append(line.split("\t")[0].strip())
    del combinaisons[-1]
    combinaisons = ["Combinaison"] + combinaisons
    table.append(combinaisons)
    for key, value in odds.items():
        table.append([key]+list(map(str, value)))
    return np.transpose(table).tolist()


def best_match_under_conditions_interface(window, values):
    try:
        site = values["SITE_UNDER_CONDITION"][0]
        bet = float(values["BET_UNDER_CONDITION"])
        minimum_odd = float(values["ODD_UNDER_CONDITION"])
        sport = values["SPORT_UNDER_CONDITION"][0]
        date_min, time_min, date_max, time_max = None, None, None, None
        if values["DATE_MIN_UNDER_CONDITION_BOOL"]:
            date_min = values["DATE_MIN_UNDER_CONDITION"]
            time_min = values["TIME_MIN_UNDER_CONDITION"].replace(":", "h")
        if values["DATE_MAX_UNDER_CONDITION_BOOL"]:
            date_max = values["DATE_MAX_UNDER_CONDITION"]
            time_max = values["TIME_MAX_UNDER_CONDITION"].replace(":", "h")
        one_site = values["ONE_SITE_UNDER_CONDITION"]
        old_stdout = sys.stdout # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        best_match_under_conditions(site, minimum_odd, bet, sport, date_max, time_max, date_min, time_min, one_site)
        sys.stdout = old_stdout # Put the old stream back in place
        whatWasPrinted = buffer.getvalue() # Return a str containing the entire contents of the buffer.
        match, date = infos(whatWasPrinted)
        if match is None:
            window["MATCH_UNDER_CONDITION"].update("Aucun match trouvé")
            window["DATE_UNDER_CONDITION"].update("")
            window["ODDS_UNDER_CONDITION"].update(visible=False)
            window["RESULT_UNDER_CONDITION"].update(visible=False)
            for i in range(5):
                window["INDICATORS_UNDER_CONDITION"+str(i)].update(visible=False)
                window["RESULTS_UNDER_CONDITION"+str(i)].update(visible=False)
        else:
            window["MATCH_UNDER_CONDITION"].update(match)
            window["DATE_UNDER_CONDITION"].update(date)
            window["ODDS_UNDER_CONDITION"].update(odds_table(whatWasPrinted), visible=True)
            window["RESULT_UNDER_CONDITION"].update(stakes(whatWasPrinted), visible=True)
            for i, elem in enumerate(indicators(whatWasPrinted)):
                window["INDICATORS_UNDER_CONDITION"+str(i)].update(elem[0].capitalize(), visible=True)
                window["RESULTS_UNDER_CONDITION"+str(i)].update(elem[1], visible=True)
        buffer.close()
    except IndexError:
        pass
    except ValueError:
        pass

def best_stakes_match_interface(window, values):
    try:
        site = values["SITE_STAKE"][0]
        bet = float(values["BET_STAKE"])
        minimum_odd = float(values["ODD_STAKE"])
        sport = values["SPORT_STAKE"][0]
        match = values["MATCHES"][0]
        old_stdout = sys.stdout # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        best_stakes_match(match, site, bet, minimum_odd, sport)
        sys.stdout = old_stdout # Put the old stream back in place
        whatWasPrinted = buffer.getvalue() # Return a str containing the entire contents of the buffer.
        match, date = infos(whatWasPrinted)
        if "No match found" in whatWasPrinted:
            window["MATCH_STAKE"].update("Cote trop élevée pour le match choisi")
            window["DATE_STAKE"].update("")
            window["ODDS_STAKE"].update(visible=False)
            window["RESULT_STAKE"].update(visible=False)
            for i in range(5):
                window["INDICATORS_STAKE"+str(i)].update(visible=False)
                window["RESULTS_STAKE"+str(i)].update(visible=False)
        else:
            window["MATCH_STAKE"].update(match)
            window["DATE_STAKE"].update(date)
            window["ODDS_STAKE"].update(odds_table(whatWasPrinted), visible=True)
            window["RESULT_STAKE"].update(stakes(whatWasPrinted), visible=True)
            for i, elem in enumerate(indicators(whatWasPrinted)):
                window["INDICATORS_STAKE"+str(i)].update(elem[0].capitalize(), visible=True)
                window["RESULTS_STAKE"+str(i)].update(elem[1], visible=True)
        buffer.close()
    except IndexError:
        sg.Popup("Site ou match non défini")
    except ValueError:
        sg.Popup("Mise ou cote invalide")
    except KeyError:
        sg.Popup("Match non disponible sur {}".format(site))

def best_match_freebet_interface(window, values):
    try:
        site = values["SITE_FREEBET"][0]
        freebet = float(values["BET_FREEBET"])
        sport = values["SPORT_FREEBET"][0]
        old_stdout = sys.stdout # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        best_match_freebet(site, freebet, sport)
        sys.stdout = old_stdout # Put the old stream back in place
        whatWasPrinted = buffer.getvalue() # Return a str containing the entire contents of the buffer.
        match, date = infos(whatWasPrinted)
        window["MATCH_FREEBET"].update(match)
        window["DATE_FREEBET"].update(date)
        window["ODDS_FREEBET"].update(odds_table(whatWasPrinted), visible=True)
        window["RESULT_FREEBET"].update(stakes(whatWasPrinted), visible=True)
        for i, elem in enumerate(indicators(whatWasPrinted)):
            window["INDICATORS_FREEBET"+str(i)].update(elem[0].capitalize(), visible=True)
            window["RESULTS_FREEBET"+str(i)].update(elem[1], visible=True)
        buffer.close()
    except IndexError:
        pass
    except ValueError:
        pass
    except KeyError:
        pass

def best_match_cashback_interface(window, values):
    try:
        site = values["SITE_CASHBACK"][0]
        bet = float(values["BET_CASHBACK"])
        minimum_odd = float(values["ODD_CASHBACK"])
        sport = values["SPORT_CASHBACK"][0]
        freebet = float(values["FREEBET_CASHBACK"])
        combi_max = float(values["COMBI_MAX_CASHBACK"])/100
        combi_odd = float(values["COMBI_ODD_CASHBACK"])
        rate_cashback = float(values["RATE_CASHBACK"])/100
        date_min, time_min, date_max, time_max = None, None, None, None
        if values["DATE_MIN_CASHBACK_BOOL"]:
            date_min = values["DATE_MIN_CASHBACK"]
            time_min = values["TIME_MIN_CASHBACK"].replace(":", "h")
        if values["DATE_MAX_CASHBACK_BOOL"]:
            date_max = values["DATE_MAX_CASHBACK"]
            time_max = values["TIME_MAX_CASHBACK"].replace(":", "h")
        old_stdout = sys.stdout # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        best_match_cashback(site, minimum_odd, bet, sport, freebet, combi_max, combi_odd,
                            rate_cashback, date_max, time_max, date_min, time_min)
        sys.stdout = old_stdout # Put the old stream back in place
        whatWasPrinted = buffer.getvalue() # Return a str containing the entire contents of the buffer.
        match, date = infos(whatWasPrinted)
        if match is None:
            window["MATCH_CASHBACK"].update("Aucun match trouvé")
            window["DATE_CASHBACK"].update("")
            window["ODDS_CASHBACK"].update(visible=False)
            window["RESULT_CASHBACK"].update(visible=False)
            for i in range(5):
                window["INDICATORS_CASHBACK"+str(i)].update(visible=False)
                window["RESULTS_CASHBACK"+str(i)].update(visible=False)
        else:
            window["MATCH_CASHBACK"].update(match)
            window["DATE_CASHBACK"].update(date)
            window["ODDS_CASHBACK"].update(odds_table(whatWasPrinted), visible=True)
            window["RESULT_CASHBACK"].update(stakes(whatWasPrinted), visible=True)
            for i, elem in enumerate(indicators(whatWasPrinted)):
                window["INDICATORS_CASHBACK"+str(i)].update(elem[0].capitalize(), visible=True)
                window["RESULTS_CASHBACK"+str(i)].update(elem[1], visible=True)
        buffer.close()
    except IndexError:
        pass

def best_matches_combine_interface(window, values):
    try:
        site = values["SITE_COMBINE"][0]
        bet = float(values["BET_COMBINE"])
        minimum_odd = float(values["ODD_COMBINE"])
        minimum_odd_selection = float(values["ODD_SELECTION_COMBINE"])
        sport = values["SPORT_COMBINE"][0]
        nb_matches = int(values["NB_MATCHES_COMBINE"])
        date_min, time_min, date_max, time_max = None, None, None, None
        if values["DATE_MIN_COMBINE_BOOL"]:
            date_min = values["DATE_MIN_COMBINE"]
            time_min = values["TIME_MIN_COMBINE"].replace(":", "h")
        if values["DATE_MAX_COMBINE_BOOL"]:
            date_max = values["DATE_MAX_COMBINE"]
            time_max = values["TIME_MAX_COMBINE"].replace(":", "h")
        one_site = values["ONE_SITE_COMBINE"]
        old_stdout = sys.stdout # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        best_matches_combine(site, minimum_odd, bet, sport, nb_matches, one_site, date_max,
                                time_max, date_min, time_min, minimum_odd_selection)
        sys.stdout = old_stdout # Put the old stream back in place
        whatWasPrinted = buffer.getvalue() # Return a str containing the entire contents of the buffer.
        match, date = infos(whatWasPrinted)
        if match is None:
            window["MATCH_COMBINE"].update("Aucun match trouvé")
            window["DATE_COMBINE"].update("")
            window["ODDS_COMBINE"].update(visible=False)
            window["RESULT_COMBINE"].update(visible=False)
            for i in range(5):
                window["INDICATORS_COMBINE"+str(i)].update(visible=False)
                window["RESULTS_COMBINE"+str(i)].update(visible=False)
        else:
            window["MATCH_COMBINE"].update(match)
            window["DATE_COMBINE"].update(date)
            window["ODDS_COMBINE"].update(visible=True)
            window["RESULT_COMBINE"].update(stakes(whatWasPrinted), visible=True)
            for i, elem in enumerate(indicators(whatWasPrinted)):
                window["INDICATORS_COMBINE"+str(i)].update(elem[0].capitalize(), visible=True)
                window["RESULTS_COMBINE"+str(i)].update(elem[1], visible=True)
        buffer.close()
        return whatWasPrinted
    except IndexError:
        pass
    except ValueError:
        pass


def best_match_stakes_to_bet_interface(window, values, visible_stakes):
    global whatWasPrintedCombine
    stakes_list = []
    for i in range(visible_stakes):
        stakes_list.append([float(values["STAKE_STAKES_"+str(i)]),
                        values["SITE_STAKES_"+str(i)]])
    sites = values["SITES_STAKES"]
    old_stdout = sys.stdout # Memorize the default stdout stream
    sys.stdout = buffer = io.StringIO()
    best_match_stakes_to_bet(stakes_list)
    sys.stdout = old_stdout # Put the old stream back in place
    whatWasPrinted = buffer.getvalue() # Return a str containing the entire contents of the buffer.
    match, date = infos(whatWasPrinted)
    window["MATCH_STAKES"].update(match)
    window["DATE_STAKES"].update(date)
    window["ODDS_STAKES"].update(visible=True)
    window["RESULT_STAKES"].update(stakes(whatWasPrinted), visible=True)
    for i, elem in enumerate(indicators(whatWasPrinted)):
        window["INDICATORS_STAKES"+str(i)].update(elem[0].capitalize(), visible=True)
        window["RESULTS_STAKES"+str(i)].update(elem[1], visible=True)
    buffer.close()
    return whatWasPrinted

def best_matches_freebet_interface(window, values, visible_freebets):
    global whatWasPrintedCombine
    freebets_list = []
    for i in range(visible_freebets):
        freebets_list.append([float(values["STAKE_FREEBETS_"+str(i)]),
                        values["SITE_FREEBETS_"+str(i)]])
    sites = values["SITES_FREEBETS"]
    old_stdout = sys.stdout # Memorize the default stdout stream
    sys.stdout = buffer = io.StringIO()
    best_matches_freebet(sites, freebets_list)
    sys.stdout = old_stdout # Put the old stream back in place
    whatWasPrinted = buffer.getvalue() # Return a str containing the entire contents of the buffer.
    match, date = infos(whatWasPrinted)
    window["MATCH_FREEBETS"].update(match)
    window["DATE_FREEBETS"].update(date)
    window["ODDS_FREEBETS"].update(visible=True)
    window["RESULT_FREEBETS"].update(stakes(whatWasPrinted), visible=True)
    for i, elem in enumerate(indicators(whatWasPrinted)):
        window["INDICATORS_FREEBETS"+str(i)].update(elem[0].capitalize(), visible=True)
        window["RESULTS_FREEBETS"+str(i)].update(elem[1], visible=True)
    whatWasPrintedCombine = whatWasPrinted
    buffer.close()
    return whatWasPrinted