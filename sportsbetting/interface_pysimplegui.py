import PySimpleGUI as sg
import threading
from sportsbetting.database_functions import get_all_sports, get_all_competitions

sports = get_all_sports()
sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet', 'parionssport',
         'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']

# All the stuff inside your window.
parsing_layout = [  
            [
                sg.Listbox(sports, size=(20, 6), key="SPORT", enable_events=True),
                sg.Listbox((), size=(20, 12), key='COMPETITIONS'),
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


match_under_condition_layout = [
                                [sg.Listbox(sites, size=(20, 12), key="SITE_UNDER_CONDITION"),
                                sg.Column(column_under_condition), sg.Column(options_under_condition)],
                                [sg.Button("Calculer", key="BEST_MATCH_UNDER_CONDITION")]
                            ]

column_text_stake = [[sg.Text("Mise")], [sg.Text("Cote minimale")]]
column_fields_stake = [[sg.InputText(key='BET_STAKE', size=(6,1))],
                        [sg.InputText(key='ODD_STAKE', size=(6,1))]]

column_stake = [[sg.Column(column_text_stake), sg.Column(column_fields_stake)],
                [sg.Listbox(sports, size=(20, 6), key="SPORT_STAKE", enable_events=True)]]

stake_layout = [
                [sg.Listbox(sites, size=(20, 12), key="SITE_STAKE"),
                sg.Column(column_stake),
                sg.Listbox([], size=(40, 12), key="MATCHES")],
                [sg.Button("Calculer", key="BEST_STAKE")]
            ]




layout = [[sg.TabGroup([[sg.Tab('Récupération des cotes', parsing_layout),
                         sg.Tab('Meilleur match pour pari simple', match_under_condition_layout),
                         sg.Tab('Pari sur un match donné', stake_layout)]])],
            [sg.Button('Quitter')]]

# Create the Window
window = sg.Window('Paris sportifs', layout)
progress_bar = window.FindElement('progress')
sportsbetting.PROGRESS = 0
thread = None

sport = ''
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read(timeout=100)
    progress_bar.UpdateBar(sportsbetting.PROGRESS, 100)
    try:
        if not thread.is_alive():
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
            best_match_under_conditions(site, minimum_odd, bet, sport, date_max, time_max, date_min, time_min, one_site)
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
            best_stakes_match(match, site, bet, minimum_odd, sport)
        except IndexError:
            pass
        except ValueError:
            pass
    

window.close()