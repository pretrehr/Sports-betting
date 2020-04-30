#!/usr/bin/env python3

import PySimpleGUI as sg
import threading
import sportsbetting
from sportsbetting.user_functions import (parse_competitions, best_match_under_conditions,
                                          best_match_freebet, best_stakes_match,
                                          best_matches_combine, best_match_cashback)
from sportsbetting.database_functions import get_all_sports, get_all_competitions
from sportsbetting.interface_functions import (odds_table, indicators, stakes, infos,
                                               odds_table_combine)
import sys
import io
import pickle

try:
    sportsbetting.ODDS = pickle.load(open("data.pickle", "rb"))
except FileNotFoundError:
    pass

sports = get_all_sports()
sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet', 'parionssport',
         'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']

# All the stuff inside your window.
parsing_layout = [  
            [
                sg.Listbox(sports, size=(20, 6), key="SPORT", enable_events=True),
                sg.Listbox((), size=(20, 12), key='COMPETITIONS', select_mode='multiple'),
                sg.Column([[sg.Listbox(sites, size=(20, 12), key="SITES", select_mode='multiple')], [sg.Button("Tout sélectionner", key="SELECT_ALL")]])
            ],
            [sg.Button('Ok'), sg.ProgressBar(max_value=100, orientation='h', size=(20, 20), key='progress', visible=False)]
        ]

column_text_under_condition = [[sg.Text("Mise")], [sg.Text("Cote minimale")]]
column_fields_under_condition = [[sg.InputText(key='BET_UNDER_CONDITION', size=(6,1))],
                                 [sg.InputText(key='ODD_UNDER_CONDITION', size=(6,1))]]

column_under_condition = [[sg.Column(column_text_under_condition), sg.Column(column_fields_under_condition)],
                                [sg.Listbox(sports, size=(20, 6), key="SPORT_UNDER_CONDITION")]]


options_under_condition = [[sg.Text("Options")],
[sg.Checkbox("Date/Heure minimale ", key="DATE_MIN_UNDER_CONDITION_BOOL"), sg.InputText(tooltip="DD/MM/YYYY", size=(12,1), key="DATE_MIN_UNDER_CONDITION"), sg.InputText(tooltip="HH:MM", size=(7,1), key="TIME_MIN_UNDER_CONDITION")],
         [sg.Checkbox("Date/Heure maximale", key="DATE_MAX_UNDER_CONDITION_BOOL"), sg.InputText(tooltip="DD/MM/YYYY", size=(12,1), key="DATE_MAX_UNDER_CONDITION"), sg.InputText(tooltip="HH:MM", size=(7,1), key="TIME_MAX_UNDER_CONDITION")],
         [sg.Checkbox("Mise à répartir sur toutes les issues d'un même match", key="ONE_SITE_UNDER_CONDITION")]]


column_indicators_under_condition = [[sg.Text("", size=(15, 1), key="INDICATORS_UNDER_CONDITION"+str(_), visible=False)] for _ in range(5)]

column_results_under_condition = [[sg.Text("", size=(30, 1), key="RESULTS_UNDER_CONDITION"+str(_), visible=False)] for _ in range(5)]


match_under_condition_layout = [
                                [sg.Listbox(sites, size=(20, 12), key="SITE_UNDER_CONDITION"),
                                 sg.Column(column_under_condition),
                                 sg.Column(options_under_condition)],
                                [sg.Button("Calculer", key="BEST_MATCH_UNDER_CONDITION")],
                                [sg.Text("", size=(30, 1), key="MATCH_UNDER_CONDITION"),
                                 sg.Text("", size=(30, 1), key="DATE_UNDER_CONDITION")],
                                [sg.Table([["parionssport", "0000", "0000", "0000"]], headings=["Cotes", "1", "N", "2"], key="ODDS_UNDER_CONDITION", visible=False, hide_vertical_scroll=True, size=(None, 12)),
                                 sg.MLine(size=(90, 12), key="RESULT_UNDER_CONDITION", font="Consolas 10", visible=False)],
                                [sg.Column(column_indicators_under_condition),
                                 sg.Column(column_results_under_condition)]
                            ]

column_text_stake = [[sg.Text("Mise")], [sg.Text("Cote minimale")]]
column_fields_stake = [[sg.InputText(key='BET_STAKE', size=(6,1))],
                        [sg.InputText(key='ODD_STAKE', size=(6,1))]]

column_stake = [[sg.Column(column_text_stake), sg.Column(column_fields_stake)],
                [sg.Listbox(sports, size=(20, 6), key="SPORT_STAKE", enable_events=True)]]

column_indicators_stake = [[sg.Text("", size=(15, 1), key="INDICATORS_STAKE"+str(_), visible=False)] for _ in range(5)]

column_results_stake = [[sg.Text("", size=(30, 1), key="RESULTS_STAKE"+str(_), visible=False)] for _ in range(5)]

stake_layout = [
                [sg.Listbox(sites, size=(20, 12), key="SITE_STAKE"),
                sg.Column(column_stake),
                sg.Listbox([], size=(40, 12), key="MATCHES")],
                [sg.Button("Calculer", key="BEST_STAKE")],
                [sg.Text("", size=(30, 1), key="MATCH_STAKE"),
                sg.Text("", size=(30, 1), key="DATE_STAKE")],
                [sg.Table([["parionssport", "0000", "0000", "0000"]], headings=["Cotes", "1", "N", "2"], key="ODDS_STAKE", visible=False, hide_vertical_scroll=True, size=(None, 12)),
                    sg.MLine(size=(90, 12), key="RESULT_STAKE", font="Consolas 10", visible=False)],
                [sg.Column(column_indicators_stake),
                    sg.Column(column_results_stake)]
            ]


column_freebet = [[sg.Text("Freebet"), sg.InputText(key='BET_FREEBET', size=(6,1))],
                                [sg.Listbox(sports, size=(20, 6), key="SPORT_FREEBET")]]


column_indicators_freebet = [[sg.Text("", size=(15, 1), key="INDICATORS_FREEBET"+str(_), visible=False)] for _ in range(5)]

column_results_freebet = [[sg.Text("", size=(30, 1), key="RESULTS_FREEBET"+str(_), visible=False)] for _ in range(5)]


freebet_layout = [
                            [sg.Listbox(sites, size=(20, 12), key="SITE_FREEBET"),
                                sg.Column(column_freebet)],
                            [sg.Button("Calculer", key="BEST_MATCH_FREEBET")],
                            [sg.Text("", size=(30, 1), key="MATCH_FREEBET"),
                                sg.Text("", size=(30, 1), key="DATE_FREEBET")],
                            [sg.Table([["parionssport", "0000", "0000", "0000"]], headings=["Cotes", "1", "N", "2"], key="ODDS_FREEBET", visible=False, hide_vertical_scroll=True, size=(None, 12)),
                                sg.MLine(size=(90, 12), key="RESULT_FREEBET", font="Consolas 10", visible=False)],
                            [sg.Column(column_indicators_freebet),
                                sg.Column(column_results_freebet)]
                        ]
                        
column_text_cashback = [[sg.Text("Mise")], [sg.Text("Cote minimale")]]
column_fields_cashback = [[sg.InputText(key='BET_CASHBACK', size=(6,1))],
                                 [sg.InputText(key='ODD_CASHBACK', size=(6,1))]]

column_cashback = [[sg.Column(column_text_cashback), sg.Column(column_fields_cashback)],
                                [sg.Listbox(sports, size=(20, 6), key="SPORT_CASHBACK")]]


options_cashback = [[sg.Text("Options", font="bold")],
[sg.Checkbox("Remboursement en freebet", default=True, key="FREEBET_CASHBACK")],
[sg.Text("Taux de remboursement"), sg.InputText(size=(5,1), key="RATE_CASHBACK", default_text=100), sg.Text("%")],
[sg.Text("Bonus combiné"), sg.InputText(size=(5,1), key="COMBI_MAX_CASHBACK", default_text=0), sg.Text("%")],
[sg.Text("Cote combiné"), sg.InputText(size=(5,1), key="COMBI_ODD_CASHBACK", default_text=1)],
[sg.Checkbox("Date/Heure minimale ", key="DATE_MIN_CASHBACK_BOOL"), sg.InputText(tooltip="DD/MM/YYYY", size=(12,1), key="DATE_MIN_CASHBACK"), sg.InputText(tooltip="HH:MM", size=(7,1), key="TIME_MIN_CASHBACK")],
         [sg.Checkbox("Date/Heure maximale", key="DATE_MAX_CASHBACK_BOOL"), sg.InputText(tooltip="DD/MM/YYYY", size=(12,1), key="DATE_MAX_CASHBACK"), sg.InputText(tooltip="HH:MM", size=(7,1), key="TIME_MAX_CASHBACK")]]


column_indicators_cashback = [[sg.Text("", size=(15, 1), key="INDICATORS_CASHBACK"+str(_), visible=False)] for _ in range(5)]

column_results_cashback = [[sg.Text("", size=(30, 1), key="RESULTS_CASHBACK"+str(_), visible=False)] for _ in range(5)]


cashback_layout = [
                    [sg.Listbox(sites, size=(20, 12), key="SITE_CASHBACK"),
                        sg.Column(column_cashback),
                        sg.Column(options_cashback)],
                    [sg.Button("Calculer", key="BEST_MATCH_CASHBACK")],
                    [sg.Text("", size=(30, 1), key="MATCH_CASHBACK"),
                        sg.Text("", size=(30, 1), key="DATE_CASHBACK")],
                    [sg.Table([["parionssport", "0000", "0000", "0000"]], headings=["Cotes", "1", "N", "2"], key="ODDS_CASHBACK", visible=False, hide_vertical_scroll=True, size=(None, 12)),
                        sg.MLine(size=(90, 12), key="RESULT_CASHBACK", font="Consolas 10", visible=False)],
                    [sg.Column(column_indicators_cashback),
                        sg.Column(column_results_cashback)]
                ]


column_text_combine = [[sg.Text("Mise")],
                       [sg.Text("Cote minimale")],
                       [sg.Text("Nombre de matches")],
                       [sg.Text("Cote minimale par sélection")]]
column_fields_combine = [[sg.InputText(key='BET_COMBINE', size=(6,1))],
                         [sg.InputText(key='ODD_COMBINE', size=(6,1))],
                         [sg.InputText(key='NB_MATCHES_COMBINE', size=(6,1), default_text=2)],
                         [sg.InputText(key='ODD_SELECTION_COMBINE', size=(6,1), default_text=1.01)]]

column_combine = [[sg.Column(column_text_combine), sg.Column(column_fields_combine)],
                                [sg.Listbox(sports, size=(20, 6), key="SPORT_COMBINE")]]


options_combine = [[sg.Text("Options")],
[sg.Checkbox("Date/Heure minimale ", key="DATE_MIN_COMBINE_BOOL"), sg.InputText(tooltip="DD/MM/YYYY", size=(12,1), key="DATE_MIN_COMBINE"), sg.InputText(tooltip="HH:MM", size=(7,1), key="TIME_MIN_COMBINE")],
         [sg.Checkbox("Date/Heure maximale", key="DATE_MAX_COMBINE_BOOL"), sg.InputText(tooltip="DD/MM/YYYY", size=(12,1), key="DATE_MAX_COMBINE"), sg.InputText(tooltip="HH:MM", size=(7,1), key="TIME_MAX_COMBINE")],
         [sg.Checkbox("Mise à répartir sur toutes les issues d'un même combiné", key="ONE_SITE_COMBINE")]]


column_indicators_combine = [[sg.Text("", size=(15, 1), key="INDICATORS_COMBINE"+str(_), visible=False)] for _ in range(5)]

column_results_combine = [[sg.Text("", size=(6, 1), key="RESULTS_COMBINE"+str(_), visible=False)] for _ in range(5)]


combine_layout = [
                    [sg.Listbox(sites, size=(20, 12), key="SITE_COMBINE"),
                        sg.Column(column_combine),
                        sg.Column(options_combine)],
                    [sg.Button("Calculer", key="BEST_MATCHES_COMBINE")],
                    [sg.Text("", size=(100, 1), key="MATCH_COMBINE")],
                    [sg.Text("", size=(30, 1), key="DATE_COMBINE")],
                    [sg.Column([[sg.Button("Voir les cotes combinées", key="COTES_COMBINE", visible=False)],
                                [sg.Column(column_indicators_combine),
                                 sg.Column(column_results_combine)]
                                ]),
                     sg.MLine(size=(120, 12), key="RESULT_COMBINE", font="Consolas 10", visible=False)
                    ]
                    
                ]



layout = [[sg.TabGroup([[sg.Tab('Récupération des cotes', parsing_layout),
                         sg.Tab('Pari simple', match_under_condition_layout),
                         sg.Tab('Pari sur un match donné', stake_layout),
                         sg.Tab('Freebet unique', freebet_layout),
                         sg.Tab('Cashback', cashback_layout),
                         sg.Tab('Pari combiné', combine_layout)]])],
            [sg.Button('Quitter')]]

# Create the Window
window = sg.Window('Paris sportifs', layout, location=(0,0))
progress_bar = window.FindElement('progress')
sportsbetting.PROGRESS = 0
thread = None
window_odds_active = False
sport = ''

# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read(timeout=100)
    progress_bar.UpdateBar(sportsbetting.PROGRESS, 100)
    try:
        if not thread.is_alive():
            pickle.dump(sportsbetting.ODDS, open("data.pickle", "wb"))
            progress_bar.Update(visible=False)
    except AttributeError:
        pass
    if event == "SPORT":
        sport = values["SPORT"][0]
        competitions = get_all_competitions(sport)
        window.Element('COMPETITIONS').Update(values=competitions)
    if event == "SELECT_ALL":
        sport_listbox = window.FindElement('SITES')
        sport_listbox.Update(set_to_index = [i for i,_ in enumerate(sites)])
    if event in (None, 'Quitter'):   # if user closes window or clicks cancel
        break
    if event == 'Ok':
        selected_competitions = values["COMPETITIONS"]
        selected_sites = values["SITES"]
        if selected_competitions and selected_sites:
            def parse_thread():
                sportsbetting.PROGRESS = 0
                parse_competitions(selected_competitions, sport, *selected_sites)
            thread = threading.Thread(target=parse_thread)
            thread.start()
            progress_bar.Update(visible=True)
    if event == "BEST_MATCH_UNDER_CONDITION":
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
    if event == "SPORT_STAKE":
        try:
            matches = sorted(list(sportsbetting.ODDS[values["SPORT_STAKE"][0]]))
            window.Element('MATCHES').Update(values=matches)
        except KeyError:
            window.Element('MATCHES').Update(values=[])
    if event == "BEST_STAKE":
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
#             print(display_results(whatWasPrinted))
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
#             window["RESULT_UNDER_CONDITION"].set_size((400, whatWasPrinted.count("\n")))
            buffer.close()
        except IndexError:
            sg.Popup("Site ou match non défini")
        except ValueError:
            sg.Popup("Mise ou cote invalide")
        except KeyError:
            sg.Popup("Match non disponible sur {}".format(site))
    if event == "BEST_MATCH_FREEBET":
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
    if event == "BEST_MATCH_CASHBACK":
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
    if event == "BEST_MATCHES_COMBINE":
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
                window["COTES_COMBINE"].update(visible=False)
                window["RESULT_COMBINE"].update(visible=False)
                for i in range(5):
                    window["INDICATORS_COMBINE"+str(i)].update(visible=False)
                    window["RESULTS_COMBINE"+str(i)].update(visible=False)
            else:
                window["MATCH_COMBINE"].update(match)
                window["DATE_COMBINE"].update(date)
                window["COTES_COMBINE"].update(visible=True)
                window["RESULT_COMBINE"].update(stakes(whatWasPrinted), visible=True)
                for i, elem in enumerate(indicators(whatWasPrinted)):
                    window["INDICATORS_COMBINE"+str(i)].update(elem[0].capitalize(), visible=True)
                    window["RESULTS_COMBINE"+str(i)].update(elem[1], visible=True)
                whatWasPrintedCombine = whatWasPrinted
            buffer.close()
        except IndexError:
            pass
        except ValueError:
            pass
    if not window_odds_active and event == "COTES_COMBINE":
        window_odds_active = True
        table = odds_table_combine(whatWasPrintedCombine)
        layout2 = [[sg.Text('Window 2')],
                   [sg.Table(table[1:], headings=table[0], size=(None, 20))]]
        win2 = sg.Window('Window 2', layout2)
    if window_odds_active:
        ev2, vals2 = win2.Read(timeout=100)
        if ev2 is None or ev2 == 'Exit':
            window_odds_active  = False
            win2.close()
    

window.close()