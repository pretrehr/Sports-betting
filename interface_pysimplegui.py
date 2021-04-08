#!/usr/bin/env python3
"""
Interface
"""

# pyinstaller --onefile --add-binary
# "sportsbetting\resources\chromedriver.exe;sportsbetting\resources" --add-data
# "sportsbetting\resources\teams.db;sportsbetting\resources" interface_pysimplegui.py --noconfirm
import collections
import queue
import threading
import os
import sys
import time
from math import ceil

import PySimpleGUI as sg

import colorama
import termcolor
import sportsbetting as sb
from sportsbetting.auxiliary_functions import get_nb_outcomes, load_odds, save_odds
from sportsbetting.database_functions import get_all_competitions
from sportsbetting.user_functions import parse_competitions, get_sports_with_surebet, trj_match
from sportsbetting.interface_functions import (odds_table_combine,
                                               best_match_under_conditions_interface,
                                               best_match_freebet_interface,
                                               best_match_cashback_interface,
                                               best_matches_combine_interface,
                                               best_match_stakes_to_bet_interface,
                                               best_stakes_match_interface,
                                               best_matches_freebet_interface,
                                               best_match_pari_gagnant_interface,
                                               odds_match_interface, delete_odds_interface,
                                               delete_site_interface,
                                               get_current_competitions_interface,
                                               best_combine_reduit_interface,
                                               find_surebets_interface, odds_match_surebets_interface,
                                               find_values_interface, odds_match_values_interface,
                                               open_bookmaker_odds, find_perf_players, display_middle_info,
                                               display_surebet_info, best_match_miles_interface)

PATH_DATA = os.path.dirname(sb.__file__) + "/resources/data.json"

print(r"""
   _____                  __             __         __  __  _            
  / ___/____  ____  _____/ /______      / /_  ___  / /_/ /_(_)___  ____ _
  \__ \/ __ \/ __ \/ ___/ __/ ___/_____/ __ \/ _ \/ __/ __/ / __ \/ __ `/
 ___/ / /_/ / /_/ / /  / /_(__  )_____/ /_/ /  __/ /_/ /_/ / / / / /_/ / 
/____/ .___/\____/_/   \__/____/     /_.___/\___/\__/\__/_/_/ /_/\__, /  
    /_/                                                         /____/   
""")

try:
    sb.ODDS = load_odds(PATH_DATA)
except FileNotFoundError:
    pass

sb.DB_MANAGEMENT = "--db" in sys.argv
sb.BETA = "--beta" in sys.argv
nb_bookmakers = len(sb.BOOKMAKERS)


# All the stuff inside your window.
sg.set_options(enable_treeview_869_patch=False)
parsing_layout = [
    [
        sg.Listbox(sb.SPORTS, size=(20, 6), key="SPORT", enable_events=True),
        sg.Column([[sg.Listbox((), size=(27, 12), key='COMPETITIONS', select_mode='multiple')],
                   [sg.Button("Tout désélectionner", key="SELECT_NONE_COMPETITION")],
                   [sg.Button("Compétitions actuelles", key="CURRENT_COMPETITIONS", visible=sb.DB_MANAGEMENT)],
                   [sg.Button("Big 5", key="MAIN_COMPETITIONS", visible=False)]]),
        sg.Column([[sg.Listbox(sb.BOOKMAKERS, size=(20, nb_bookmakers), key="SITES", select_mode='multiple')],
                   [sg.Button("Tout sélectionner", key="SELECT_ALL")],
                   [sg.Button("Tout désélectionner", key="SELECT_NONE_SITE")]])
    ],
    [sg.Text("", size=(100, 1), key="SUREBET_PARSING", visible=False)],
    [sg.Col([[sg.Button('Démarrer', key="START_PARSING")]]),
     sg.Col([[sg.Button('Récupérer tous les sports', key="START_ALL_PARSING", visible=sb.BETA)]]),
     sg.Col([[sg.Button('Stop', key="STOP_PARSING", button_color=("white", "red"), visible=False)]]),
     sg.Col([[sg.ProgressBar(max_value=100, orientation='h', size=(20, 20), key='PROGRESS_PARSING',
                             visible=False)]]),
     sg.Col([[sg.Text("Initialisation de selenium en cours", key="TEXT_PARSING", visible=False)]]),
     sg.Col([[sg.Text("8:88:88", key="REMAINING_TIME_PARSING", visible=False)]])],
    [sg.Col([[sg.ProgressBar(max_value=100, orientation='v', size=(10, 20),
                             key="PROGRESS_{}_PARSING".format(site), visible=False)],
             [sg.Text(site, key="TEXT_{}_PARSING".format(site), visible=False)]],
            element_justification="center") for site in sb.BOOKMAKERS]
]

column_text_under_condition = [[sg.Text("Mise")], [sg.Text("Cote minimale")]]
column_fields_under_condition = [[sg.InputText(key='BET_UNDER_CONDITION', size=(6, 1))],
                                 [sg.InputText(key='ODD_UNDER_CONDITION', size=(6, 1))]]
column_under_condition = [[sg.Column(column_text_under_condition),
                           sg.Column(column_fields_under_condition)],
                          [sg.Listbox(sb.SPORTS, size=(20, 6), key="SPORT_UNDER_CONDITION")]]
options_under_condition = [[sg.Text("Options")],
                           [sg.Checkbox("Date/Heure minimale ",
                                        key="DATE_MIN_UNDER_CONDITION_BOOL"),
                            sg.InputText(tooltip="DD/MM/YYYY", size=(12, 1),
                                         key="DATE_MIN_UNDER_CONDITION"),
                            sg.InputText(tooltip="HH:MM", size=(7, 1),
                                         key="TIME_MIN_UNDER_CONDITION")],
                           [sg.Checkbox("Date/Heure maximale", key="DATE_MAX_UNDER_CONDITION_BOOL"),
                            sg.InputText(tooltip="DD/MM/YYYY", size=(12, 1),
                                         key="DATE_MAX_UNDER_CONDITION"),
                            sg.InputText(tooltip="HH:MM", size=(7, 1),
                                         key="TIME_MAX_UNDER_CONDITION")],
                           [sg.Checkbox("Mise à répartir sur plusieurs issues d'un même match",
                                        key="ONE_SITE_UNDER_CONDITION")]]
column_indicators_under_condition = [[sg.Text("", size=(18, 1),
                                              key="INDICATORS_UNDER_CONDITION" + str(_),
                                              visible=False)] for _ in range(6)]
column_results_under_condition = [[sg.Text("", size=(8, 1),
                                           key="RESULTS_UNDER_CONDITION" + str(_),
                                           visible=False)] for _ in range(6)]
match_under_condition_layout = [[sg.Listbox(sb.BOOKMAKERS, size=(20, nb_bookmakers), key="SITE_UNDER_CONDITION"),
                                 sg.Column(column_under_condition),
                                 sg.Column(options_under_condition),
                                 sg.Column([[sg.Text("", size=(30, 1), key="MATCH_UNDER_CONDITION")],
                                            [sg.Text("", size=(30, 1), key="DATE_UNDER_CONDITION")],
                                            [sg.Table([["parionssport", "0000", "0000", "0000"]],
                                                        headings=["Cotes", "1", "N", "2"],
                                                        key="ODDS_UNDER_CONDITION",
                                                        visible=False, hide_vertical_scroll=True,
                                                        size=(None, nb_bookmakers))]]),],
                                [sg.Button("Calculer", key="BEST_MATCH_UNDER_CONDITION")],
                                [sg.Button("Ignorer ce match", key="DELETE_MATCH_UNDER_CONDITION", visible=False)],
                                [sg.Button("Réinitialiser les matches", key="RELOAD_ODDS_UNDER_CONDITION", visible=False)],
                                [sg.Column(column_indicators_under_condition),
                                 sg.Column(column_results_under_condition),
                                 sg.Column([[sg.Text(
                                     "Répartition des mises (les totaux affichés prennent en "
                                     "compte les éventuels freebets) :",
                                     key="TEXT_UNDER_CONDITION", visible=False)],
                                     [sg.MLine(size=(100, 12), key="RESULT_UNDER_CONDITION",
                                               font="Consolas 10", visible=False)]])],
                                ]

column_text_stake = [[sg.Text("Mise")], [sg.Text("Cote minimale")]]
column_fields_stake = [[sg.InputText(key='BET_STAKE', size=(6, 1))],
                       [sg.InputText(key='ODD_STAKE', size=(6, 1))]]
column_stake = [[sg.Column(column_text_stake), sg.Column(column_fields_stake)],
                [sg.Listbox(sb.SPORTS, size=(20, 6), key="SPORT_STAKE", enable_events=True)]]
column_indicators_stake = [[sg.Text("", size=(18, 1), key="INDICATORS_STAKE" + str(_),
                                    visible=False)] for _ in range(6)]
column_results_stake = [[sg.Text("", size=(8, 1), key="RESULTS_STAKE" + str(_),
                                 visible=False)] for _ in range(6)]
stake_layout = [
    [sg.Listbox(sb.BOOKMAKERS, size=(20, nb_bookmakers), key="SITE_STAKE"),
     sg.Column(column_stake),
     sg.Listbox([], size=(40, 12), key="MATCHES"),
     sg.Column([[sg.Text("", size=(30, 1), key="MATCH_STAKE")],
                [sg.Text("", size=(30, 1), key="DATE_STAKE")],
                [sg.Table([["parionssport", "0000", "0000", "0000"]],
                            headings=["Cotes", "1", "N", "2"],
                            key="ODDS_STAKE",
                            visible=False, hide_vertical_scroll=True,
                            size=(None, nb_bookmakers))]]),],
    [sg.Button("Calculer", key="BEST_STAKE")],
    [sg.Column(column_indicators_stake),
     sg.Column(column_results_stake),
     sg.Column([[sg.Text(
         "Répartition des mises (les totaux affichés prennent en compte les éventuels freebets) :",
         key="TEXT_STAKE", visible=False)],
         [sg.MLine(size=(100, 12), key="RESULT_STAKE", font="Consolas 10", visible=False)]])]
]

column_freebet = [[sg.Text("Freebet"), sg.InputText(key='BET_FREEBET', size=(6, 1)), sg.Checkbox("Fractionnable", key='SPLIT_FREEBET')],
                  [sg.Listbox(sb.SPORTS, size=(20, 6), key="SPORT_FREEBET")],
                  [sg.Text("Nombre de matches combinés"), sg.Spin([i for i in range(1, 4)], initial_value=1, key="NB_MATCHES_FREEBET", visible=sb.BETA)],
                  ]
column_indicators_freebet = [[sg.Text("", size=(18, 1), key="INDICATORS_FREEBET" + str(_),
                                      visible=False)] for _ in range(5)]
column_results_freebet = [[sg.Text("", size=(8, 1), key="RESULTS_FREEBET" + str(_),
                                   visible=False)] for _ in range(5)]
freebet_layout = [
    [sg.Listbox(sb.BOOKMAKERS, size=(20, nb_bookmakers), key="SITE_FREEBET"),
     sg.Column(column_freebet),
     sg.Column([[sg.Text("", size=(30, 1), key="MATCH_FREEBET")],
                [sg.Text("", size=(30, 1), key="DATE_FREEBET")],
                [sg.Table([["parionssport", "0000", "0000", "0000"]],
                        headings=["Cotes", "1", "N", "2"], key="ODDS_FREEBET", visible=False,
                        hide_vertical_scroll=True, size=(None, nb_bookmakers))]])],
    [sg.Button("Calculer", key="BEST_MATCH_FREEBET")],
    [sg.Button("Ignorer ce match", key="DELETE_MATCH_FREEBET", visible=False)],
    [sg.Button("Réinitialiser les matches", key="RELOAD_ODDS_FREEBET", visible=False)],
    [sg.Column(column_indicators_freebet),
     sg.Column(column_results_freebet),
     sg.Column([[sg.Text("Répartition des mises (les totaux affichés prennent en compte les éventuels freebets) :",
                         key="TEXT_FREEBET", visible=False)],
                [sg.MLine(size=(120, 12), key="RESULT_FREEBET", font="Consolas 10", visible=False)]])],
]

column_text_cashback = [[sg.Text("Mise")], [sg.Text("Cote minimale")]]
column_fields_cashback = [[sg.InputText(key='BET_CASHBACK', size=(6, 1))],
                          [sg.InputText(key='ODD_CASHBACK', size=(6, 1))]]
column_cashback = [[sg.Column(column_text_cashback), sg.Column(column_fields_cashback)],
                   [sg.Listbox(sb.SPORTS, size=(20, 6), key="SPORT_CASHBACK")]]
options_cashback = [
    [sg.Text("Options", font="bold")],
    [sg.Checkbox("Remboursement en freebet", default=True, key="FREEBET_CASHBACK")],
    [sg.Text("Taux de remboursement"), sg.InputText(size=(5, 1), key="RATE_CASHBACK",
                                                    default_text="100"), sg.Text("%")],
    [sg.Text("Bonus combiné"), sg.InputText(size=(5, 1), key="COMBI_MAX_CASHBACK",
                                            default_text="0"), sg.Text("%")],
    [sg.Text("Cote combiné"), sg.InputText(size=(5, 1), key="COMBI_ODD_CASHBACK",
                                           default_text="1")],
    [sg.Checkbox("Date/Heure minimale ", key="DATE_MIN_CASHBACK_BOOL"),
     sg.InputText(tooltip="DD/MM/YYYY", size=(12, 1), key="DATE_MIN_CASHBACK"),
     sg.InputText(tooltip="HH:MM", size=(7, 1), key="TIME_MIN_CASHBACK")],
    [sg.Checkbox("Date/Heure maximale", key="DATE_MAX_CASHBACK_BOOL"),
     sg.InputText(tooltip="DD/MM/YYYY", size=(12, 1), key="DATE_MAX_CASHBACK"),
     sg.InputText(tooltip="HH:MM", size=(7, 1), key="TIME_MAX_CASHBACK")],
    [sg.Text("Nombre de matches combinés"),
     sg.Spin([i for i in range(1, 4)], initial_value=1, key="NB_MATCHES_CASHBACK")],
]
column_indicators_cashback = [[sg.Text("", size=(15, 1), key="INDICATORS_CASHBACK" + str(_),
                                       visible=False)] for _ in range(5)]
column_results_cashback = [[sg.Text("", size=(30, 1), key="RESULTS_CASHBACK" + str(_),
                                    visible=False)] for _ in range(5)]
cashback_layout = [
    [sg.Listbox(sb.BOOKMAKERS, size=(20, nb_bookmakers), key="SITE_CASHBACK"),
     sg.Column(column_cashback), sg.Column(options_cashback)],
    [sg.Button("Calculer", key="BEST_MATCH_CASHBACK")],
    [sg.Text("", size=(30, 1), key="MATCH_CASHBACK"),
     sg.Text("", size=(30, 1), key="DATE_CASHBACK")],
    [sg.Table([["parionssport", "0000", "0000", "0000"]],
              headings=["Cotes", "1", "N", "2"], key="ODDS_CASHBACK", visible=False,
              hide_vertical_scroll=True, size=(None, nb_bookmakers)),
     sg.Column([[sg.Text(
         "Répartition des mises (les totaux affichés prennent en compte les éventuels freebets) :",
         key="TEXT_CASHBACK", visible=False)],
         [sg.MLine(size=(100, 12), key="RESULT_CASHBACK", font="Consolas 10",
                   visible=False)]])],
    [sg.Column(column_indicators_cashback), sg.Column(column_results_cashback)]
]

column_text_combine = [[sg.Text("Mise")],
                       [sg.Text("Cote minimale")],
                       [sg.Text("Nombre de matches")],
                       [sg.Text("Cote minimale par sélection")]]
column_fields_combine = [[sg.InputText(key='BET_COMBINE', size=(6, 1))],
                         [sg.InputText(key='ODD_COMBINE', size=(6, 1))],
                         [sg.InputText(key='NB_MATCHES_COMBINE', size=(6, 1), default_text="2")],
                         [sg.InputText(key='ODD_SELECTION_COMBINE', size=(6, 1),
                                       default_text="1.01")]]
column_combine = [[sg.Column(column_text_combine), sg.Column(column_fields_combine)],
                  [sg.Listbox(sb.SPORTS, size=(20, 6), key="SPORT_COMBINE")]]
options_combine = [[sg.Text("Options")],
                   [sg.Checkbox("Date/Heure minimale ", key="DATE_MIN_COMBINE_BOOL"),
                    sg.InputText(tooltip="DD/MM/YYYY", size=(12, 1), key="DATE_MIN_COMBINE"),
                    sg.InputText(tooltip="HH:MM", size=(7, 1), key="TIME_MIN_COMBINE")],
                   [sg.Checkbox("Date/Heure maximale", key="DATE_MAX_COMBINE_BOOL"),
                    sg.InputText(tooltip="DD/MM/YYYY", size=(12, 1), key="DATE_MAX_COMBINE"),
                    sg.InputText(tooltip="HH:MM", size=(7, 1), key="TIME_MAX_COMBINE")],
                   [sg.Checkbox("Mise à répartir sur plusieurs issues d'un même combiné",
                                key="ONE_SITE_COMBINE")]]
column_indicators_combine = [[sg.Text("", size=(15, 1), key="INDICATORS_COMBINE" + str(_),
                                      visible=False)] for _ in range(5)]
column_results_combine = [[sg.Text("", size=(6, 1), key="RESULTS_COMBINE" + str(_),
                                   visible=False)] for _ in range(5)]
combine_layout = [[sg.Listbox(sb.BOOKMAKERS, size=(20, nb_bookmakers), key="SITE_COMBINE"), sg.Column(column_combine),
                   sg.Column(options_combine)],
                  [sg.Button("Calculer", key="BEST_MATCHES_COMBINE"),
                   sg.ProgressBar(100, orientation='h', size=(20, 20), key='PROGRESS_COMBINE', visible=False)],
                  [sg.Text("", size=(100, 1), key="MATCH_COMBINE")],
                  [sg.Text("", size=(30, 1), key="DATE_COMBINE")],
                  [sg.Column([[sg.Button("Voir les cotes combinées", key="ODDS_COMBINE",
                                         visible=False)],
                              [sg.Column(column_indicators_combine),
                               sg.Column(column_results_combine)]]),
                   sg.Column([[sg.Text(
                       "Répartition des mises (les totaux affichés prennent en compte les "
                       "éventuels freebets) :",
                       key="TEXT_COMBINE", visible=False)],
                       [sg.MLine(size=(120, 12), key="RESULT_COMBINE", font="Consolas 10",
                                 visible=False)]])
                   ]]

column_stakes = [[sg.Text("Site"), sg.Text("Mises")],
                 [sg.Combo(sb.BOOKMAKERS, key="SITE_STAKES_0"),
                  sg.Input(key="STAKE_STAKES_0", size=(6, 1))],
                 *([sg.Combo(sb.BOOKMAKERS, key="SITE_STAKES_" + str(i), visible=False),
                    sg.Input(key="STAKE_STAKES_" + str(i), size=(6, 1), visible=False)]
                   for i in range(1, 9)),
                 [sg.Button("Retirer mise", key="REMOVE_STAKES"),
                  sg.Button("Ajouter mise", key="ADD_STAKES")]]

visible_stakes = 1
column_indicators_stakes = [[sg.Text("", size=(15, 1), key="INDICATORS_STAKES" + str(_),
                                     visible=False)] for _ in range(5)]
column_results_stakes = [[sg.Text("", size=(6, 1), key="RESULTS_STAKES" + str(_),
                                  visible=False)] for _ in range(5)]
stakes_layout = [
    [sg.Text("Site\t\t"), sg.Text("Mise"), sg.Text("Cote minimale"),
     sg.Button("Retirer mise", key="REMOVE_STAKES"), sg.Text("Nombre de matches"),
     sg.Spin([i for i in range(1, 4)], initial_value=1, key="NB_MATCHES_STAKES"),
     sg.Text("Sport"),
     sg.Combo(sb.SPORTS, default_value="football", key="SPORT_STAKES")],
    [sg.Col([[sg.Combo(sb.BOOKMAKERS, key="SITE_STAKES_0")]]),
     sg.Col([[sg.Input(key="STAKE_STAKES_0", size=(6, 1))]]),
     sg.Col([[sg.Input(key="ODD_STAKES_0", size=(6, 1))]]),
     sg.Button("Ajouter mise", key="ADD_STAKES"),
     sg.Checkbox("Date/Heure maximale", key="DATE_MAX_STAKES_BOOL"),
     sg.InputText(tooltip="DD/MM/YYYY", size=(12, 1), key="DATE_MAX_STAKES"),
     sg.InputText(tooltip="HH:MM", size=(7, 1), key="TIME_MAX_STAKES")],
    *([sg.Col([[sg.Combo(sb.BOOKMAKERS, key="SITE_STAKES_" + str(i), visible=False)]]),
       sg.Col([[sg.Input(key="STAKE_STAKES_" + str(i), size=(6, 1), visible=False)]]),
       sg.Col([[sg.Input(key="ODD_STAKES_" + str(i), size=(6, 1), visible=False)]])]
      for i in range(1, 9)),
    [sg.Button("Calculer", key="BEST_MATCH_STAKES"),
     sg.ProgressBar(100, orientation='h', size=(20, 20), key='PROGRESS_STAKES', visible=False)],
    [sg.Text("", size=(100, 1), key="MATCH_STAKES")],
    [sg.Text("", size=(30, 1), key="DATE_STAKES")],
    [sg.Column([[sg.Button("Voir les cotes combinées", key="ODDS_STAKES", visible=False)],
                [sg.Column(column_indicators_stakes),
                 sg.Column(column_results_stakes)]
                ]),
     sg.Column([[sg.Text(
         "Répartition des mises (les totaux affichés prennent en compte les éventuels freebets) :",
         key="TEXT_STAKES", visible=False)],
         [sg.MLine(size=(120, 12), key="RESULT_STAKES", font="Consolas 10", visible=False)]])
     ]]

column_sites_freebets = [[sg.Text("Site")],
                         [sg.Combo(sb.BOOKMAKERS, key="SITE_FREEBETS_0")],
                         *([sg.Combo(sb.BOOKMAKERS, key="SITE_FREEBETS_" + str(i),
                                     visible=False)] for i in range(1, 9)),
                         [sg.Button("Ajouter mise", key="ADD_FREEBETS")]]

column_freebets_freebets = [[sg.Text("Mises")],
                            [sg.Input(key="STAKE_FREEBETS_0", size=(6, 1))],
                            *([sg.Input(key="STAKE_FREEBETS_" + str(i), size=(6, 1),
                                        visible=False)] for i in range(1, 9)),
                            [sg.Button("Retirer mise", key="REMOVE_FREEBETS")]]

visible_freebets = 1

column_matches_freebets = [[sg.Checkbox("Matchs définis", key="MATCHES_FREEBETS")],
                           [sg.Combo([], size=(60, 10), key="MATCH_FREEBETS_0", visible=False)],
                           [sg.Combo([], size=(60, 10), key="MATCH_FREEBETS_1", visible=False)]]

column_indicators_freebets = [[sg.Text("", size=(15, 1), key="INDICATORS_FREEBETS" + str(_),
                                       visible=False)] for _ in range(5)]

column_results_freebets = [[sg.Text("", size=(6, 1), key="RESULTS_FREEBETS" + str(_),
                                    visible=False)] for _ in range(5)]

freebets_layout = [[sg.Column(column_sites_freebets),
                    sg.Column(column_freebets_freebets),
                    sg.Listbox(sb.BOOKMAKERS, size=(20, nb_bookmakers), key="SITES_FREEBETS", select_mode='multiple'),
                    sg.Column(column_matches_freebets)],
                   [sg.Button("Calculer", key="BEST_MATCH_FREEBETS")],
                   [sg.Text("", size=(100, 1), key="MATCH_FREEBETS")],
                   [sg.Text("", size=(30, 1), key="DATE_FREEBETS")],
                   [sg.Column([[sg.Button("Voir les cotes combinées", key="ODDS_FREEBETS",
                                          visible=False)],
                               [sg.Column(column_indicators_freebets),
                                sg.Column(column_results_freebets)]
                               ]),
                    sg.Column([[sg.Text(
                        "Répartition des mises (les totaux affichés prennent en compte les "
                        "éventuels freebets) :",
                        key="TEXT_FREEBETS", visible=False)],
                        [sg.MLine(size=(120, 12), key="RESULT_FREEBETS", font="Consolas 10",
                                  visible=False)]])
                    ]]

column_text_gagnant = [[sg.Text("Mise")], [sg.Text("Cote minimale")]]
column_fields_gagnant = [[sg.InputText(key='BET_GAGNANT', size=(6, 1))],
                         [sg.InputText(key='ODD_GAGNANT', size=(6, 1))]]
column_gagnant = [[sg.Column(column_text_gagnant), sg.Column(column_fields_gagnant)],
                  [sg.Listbox(sb.SPORTS, size=(20, 6), key="SPORT_GAGNANT")]]
options_gagnant = [[sg.Text("Options")],
                   [sg.Checkbox("Date/Heure minimale ", key="DATE_MIN_GAGNANT_BOOL"),
                    sg.InputText(tooltip="DD/MM/YYYY", size=(12, 1), key="DATE_MIN_GAGNANT"),
                    sg.InputText(tooltip="HH:MM", size=(7, 1), key="TIME_MIN_GAGNANT")],
                   [sg.Checkbox("Date/Heure maximale", key="DATE_MAX_GAGNANT_BOOL"),
                    sg.InputText(tooltip="DD/MM/YYYY", size=(12, 1), key="DATE_MAX_GAGNANT"),
                    sg.InputText(tooltip="HH:MM", size=(7, 1), key="TIME_MAX_GAGNANT")],
                   [sg.Text("Nombre de matches combinés"), sg.Spin([i for i in range(1, 4)], initial_value=1, key="NB_MATCHES_GAGNANT")],
                   [sg.Checkbox("Combiné risqué", key="RISKY_GAGNANT")],
                   [sg.Checkbox("Défi remboursé ou gagnant", key="DEFI_REMBOURSE_OU_GAGNANT", visible=sb.BETA)]]
column_indicators_gagnant = [[sg.Text("", size=(18, 1), key="INDICATORS_GAGNANT" + str(_),
                                      visible=False)] for _ in range(5)]
column_results_gagnant = [[sg.Text("", size=(8, 1), key="RESULTS_GAGNANT" + str(_),
                                   visible=False)] for _ in range(5)]
gagnant_layout = [
    [sg.Listbox(sb.BOOKMAKERS, size=(20, nb_bookmakers), key="SITE_GAGNANT"),
     sg.Column(column_gagnant),
     sg.Column(options_gagnant),
     sg.Column([[sg.Text("", size=(60, 1), key="MATCH_GAGNANT")],
                [sg.Text("", size=(30, 1), key="DATE_GAGNANT")],
                [sg.Table([["parionssport", "0000", "0000", "0000"]], headings=["Cotes", "1", "N", "2"],
                          key="ODDS_GAGNANT", visible=False, hide_vertical_scroll=True, size=(None, nb_bookmakers))],
                [sg.Button("Voir les cotes combinées", key="ODDS_COMBINE_GAGNANT", visible=False)]])],
    [sg.Button("Calculer", key="BEST_MATCH_GAGNANT")],
    [sg.Button("Ignorer ce match", key="DELETE_MATCH_GAGNANT", visible=False)],
    [sg.Button("Réinitialiser les matches", key="RELOAD_ODDS_GAGNANT", visible=False)],
    [sg.Column(column_indicators_gagnant),
     sg.Column(column_results_gagnant),
     sg.Column([[sg.Text(
         "Répartition des mises (les totaux affichés prennent en compte les éventuels freebets) :",
         key="TEXT_GAGNANT", visible=False)],
         [sg.MLine(size=(120, 12), key="RESULT_GAGNANT", font="Consolas 10",
                   visible=False)]])]
]

odds_layout = [
    [sg.Listbox(sb.SPORTS, size=(20, 6), key="SPORT_ODDS", enable_events=True),
     sg.Col([[sg.InputText(key='SEARCH_ODDS', size=(40, 1), enable_events=True)],
             [sg.Listbox([], size=(40, 12), key="MATCHES_ODDS", enable_events=True)],
             [sg.Button("Trier par TRJ", key="TRJ_SORT_ODDS"), 
              sg.Button("Trier par nom", key="NAME_SORT_ODDS")]]),
     sg.Col([[sg.Text("", size=(30, 1), key="MATCH_ODDS", visible=False)],
             [sg.Text("", size=(30, 1), key="TRJ_ODDS")],
             [sg.Text("", size=(50, 1), key="INFOS_ODDS")],
             [sg.Text("", size=(30, 1), key="DATE_ODDS", visible=False)],
             [sg.Table([["parionssport", "0000", "0000", "0000"]],
                       headings=["Cotes", "1", "N", "2"], key="ODDS_ODDS", visible=False,
                       hide_vertical_scroll=True, size=(None, nb_bookmakers))],
             [sg.Button("Aller sur la page du match", key="GOTO_SITE_ODDS", visible=False)],
             [sg.Button("Supprimer le bookmaker", key="DELETE_SITE_ODDS", visible=False)],
             [sg.Button("Supprimer le match", key="DELETE_MATCH_ODDS", visible=False)]])
     ]
]

visible_combi_opt = 1
column_indicators_combi_opt = [[sg.Text("", size=(18, 1), key="INDICATORS_COMBI_OPT" + str(_),
                                     visible=False)] for _ in range(5)]
column_results_combi_opt = [[sg.Text("", size=(8, 1), key="RESULTS_COMBI_OPT" + str(_),
                                  visible=False)] for _ in range(5)]
column_text_combi_opt = [[sg.Text("Mise maximale")], [sg.Text("Cote boostée")], [sg.Text("Site boosté")]]
column_fields_combi_opt = [[sg.InputText(key='STAKE_COMBI_OPT', size=(6, 1))],
                                 [sg.InputText(key='ODD_COMBI_OPT', size=(6, 1))],
                                 [sg.Combo(sb.BOOKMAKERS, key="SITE_COMBI_OPT")]]
column_combi_opt = [[sg.Column(column_text_combi_opt),
                           sg.Column(column_fields_combi_opt)]]

combi_opt_layout = [
    [sg.Column(column_combi_opt), sg.Listbox(sb.SPORTS, size=(20, 6), key="SPORT_COMBI_OPT", enable_events=True)],
    [sg.Text("Match"),
     sg.Button("Retirer match", key="REMOVE_COMBI_OPT"),
     sg.Button("Ajouter match", key="ADD_COMBI_OPT"),  sg.Text("\t\t\t\tIssue boostée")],
    [sg.Col([[sg.InputText(size=(60, 1), key="SEARCH_MATCH_COMBI_OPT_0", enable_events=True)], [sg.Combo([], size=(60, 10), key="MATCH_COMBI_OPT_0")]]),
     sg.Col([[sg.Radio('1', "RES_COMBI_OPT_0", key="1_RES_COMBI_OPT_0", default=True)]]),
     sg.Col([[sg.Radio('N', "RES_COMBI_OPT_0", key="N_RES_COMBI_OPT_0")]]),
     sg.Col([[sg.Radio('2', "RES_COMBI_OPT_0", key="2_RES_COMBI_OPT_0")]])],
     *([sg.Col([[sg.InputText(size=(60, 1), key="SEARCH_MATCH_COMBI_OPT_" + str(i), enable_events=True, visible=False)],
                [sg.Combo([], size=(60, 10), key="MATCH_COMBI_OPT_" + str(i), visible=False)]]),
     sg.Col([[sg.Radio('1', "RES_COMBI_OPT_" + str(i), key="1_RES_COMBI_OPT_" + str(i), visible=False, default=True)]]),
     sg.Col([[sg.Radio('N', "RES_COMBI_OPT_" + str(i), key="N_RES_COMBI_OPT_" + str(i), visible=False)]]),
     sg.Col([[sg.Radio('2', "RES_COMBI_OPT_" + str(i), key="2_RES_COMBI_OPT_" + str(i), visible=False)]])]
     for i in range(1,9)),
    [sg.Button("Calculer", key="BEST_COMBI_OPT")],
    [sg.Text("", size=(100, 1), key="MATCH_COMBI_OPT")],
    [sg.Text("", size=(30, 1), key="DATE_COMBI_OPT")],
    [sg.Column([[sg.Button("Voir les cotes combinées", key="ODDS_COMBI_OPT", visible=False)],
                [sg.Column(column_indicators_combi_opt),
                 sg.Column(column_results_combi_opt)]
                ]),
     sg.Column([[sg.Text(
         "Répartition des mises (les totaux affichés prennent en compte les éventuels freebets) :",
         key="TEXT_COMBI_OPT", visible=False)],
         [sg.MLine(size=(120, 12), key="RESULT_COMBI_OPT", font="Consolas 10", visible=False)]])
     ]]

surebets_layout = [
    [
        sg.Column([[sg.Text("Cet onglet sera bientôt supprimé, utilisez plutôt l'onglet \"Cotes\"", text_color="red")],
                   [sg.Listbox(sb.SPORTS, size=(20, 6), key="SPORT_SUREBETS")],
                   [sg.Text("TRJ minimal", size=(10, 1)), sg.InputText(key='TRJ_SUREBETS', size=(6, 1), default_text="100"), sg.Text("%", size=(3, 1))],
                   [sg.Button("Chercher", key="FIND_SUREBETS")],
                   [sg.Text("", size=(30, 1), key="MESSAGE_SUREBETS")]
                   ]),
        sg.Listbox([], size=(40, 12), key="MATCHES_SUREBETS", enable_events=True),
        sg.Col([[sg.Text("", size=(30, 1), key="MATCH_SUREBETS", visible=False)],
                [sg.Text("", size=(30, 1), key="INFOS_TRJ_SUREBETS")],
                [sg.Text("", size=(50, 1), key="INFOS_ODDS_SUREBETS")],
                [sg.Text("", size=(30, 1), key="DATE_SUREBETS", visible=False)],
                [sg.Table([["parionssport", "0000", "0000", "0000"]],
                            headings=["Cotes", "1", "N", "2"], key="ODDS_SUREBETS", visible=False,
                            hide_vertical_scroll=True, size=(None, nb_bookmakers))]])
     ]
]

values_layout = [
    [
        sg.Column([[sg.Listbox(sb.SPORTS, size=(20, 6), key="SPORT_VALUES")],
                   [sg.Text("Value minimale", size=(12, 1)), sg.InputText(key='RATE_VALUES', size=(6, 1), default_text="20"), sg.Text("%", size=(3, 1))],
                   [sg.Text("TRJ minimal", size=(12, 1)), sg.InputText(key='TRJ_VALUES', size=(6, 1), default_text="95"), sg.Text("%", size=(3, 1))],
                   [sg.Button("Chercher", key="FIND_VALUES")],
                   [sg.Text("", size=(30, 1), key="MESSAGE_VALUES")]
                   ]),
        sg.Listbox([], size=(40, 12), key="MATCHES_VALUES", enable_events=True),
        sg.Col([[sg.Text("", size=(30, 1), key="MATCH_VALUES", visible=False)],
                [sg.Text("", size=(30, 1), key="INFOS_VALUE_VALUES")],
                [sg.Text("", size=(30, 1), key="INFOS_TRJ_VALUES")],
                [sg.Text("", size=(70, 1), key="INFOS_ODDS_VALUES")],
                [sg.Text("", size=(30, 1), key="DATE_VALUES", visible=False)],
                [sg.Table([["parionssport", "0000", "0000", "0000"]],
                            headings=["Cotes", "1", "N", "2"], key="ODDS_VALUES", visible=False,
                            hide_vertical_scroll=True, size=(None, nb_bookmakers))]])
     ]
]

perf_players_layout = [
    [sg.Listbox(["betclic", "parionssport", "pinnacle", "unibet", "winamax", "zebet"], size=(20, 6), key="SITES_PERF", select_mode='multiple', 
                default_values=["betclic", "parionssport", "pinnacle", "unibet", "winamax", "zebet"])],
    [sg.Button("Chercher middle bets et surebets", key="FIND_PERF"),
     sg.ProgressBar(100, orientation='h', size=(20, 20), key='PROGRESS_PERF', visible=False)],
    [sg.Col([[sg.Listbox([], size=(50, 10), key="SUREBETS_PERF", enable_events=True)],
             [sg.Text("Surebets")]]),
     sg.Col([[sg.Listbox([], size=(50, 10), key="MIDDLES_PERF", enable_events=True)],
             [sg.Text("Middle bets")]]),
     sg.Col([[sg.Text("", size=(30, 1), key="MATCH_PERF")],
             [sg.Text("", size=(30, 1), key="PLAYER_PERF")],
             [sg.Text("", size=(30, 1), key="MARKET_PERF")],
             [sg.Text("", size=(30, 1), key="OUTCOME0_PERF")],
             [sg.Text("", size=(30, 1), key="OUTCOME1_PERF")],
             [sg.Text("", size=(30, 1), key="TRJ_PERF")]])
    ]
]

column_text_miles = [[sg.Text("Mise")]]
column_fields_miles = [[sg.InputText(key='BET_MILES', size=(6, 1))]]
column_miles = [[sg.Column(column_text_miles),
                           sg.Column(column_fields_miles)],
                          [sg.Listbox(sb.SPORTS, size=(20, 6), key="SPORT_MILES")]]
options_miles = [[sg.Text("Ticket cash visé")],
                          [sg.Listbox(list(sb.MILES_RATES), size=(20, 6), key="TICKET_MILES")],
                 [sg.Text("Multiplicateur statut VIP"), sg.Input(1, size=(6,1), key="MULTIPLICATOR_MILES")],
                          [sg.Text("Options")],
                           [sg.Checkbox("Date/Heure maximale", key="DATE_MAX_MILES_BOOL"),
                            sg.InputText(tooltip="DD/MM/YYYY", size=(12, 1),
                                         key="DATE_MAX_MILES"),
                            sg.InputText(tooltip="HH:MM", size=(7, 1),
                                         key="TIME_MAX_MILES")]]
column_indicators_miles = [[sg.Text("", size=(18, 1),
                                              key="INDICATORS_MILES" + str(_),
                                              visible=False)] for _ in range(8)]
column_results_miles = [[sg.Text("", size=(8, 1),
                                           key="RESULTS_MILES" + str(_),
                                           visible=False)] for _ in range(8)]
miles_layout = [[sg.Column(column_miles),
                                 sg.Column(options_miles),
                                 sg.Column([[sg.Text("", size=(30, 1), key="MATCH_MILES")],
                                            [sg.Text("", size=(30, 1), key="DATE_MILES")],
                                            [sg.Table([["parionssport", "0000", "0000", "0000"]],
                                                        headings=["Cotes", "1", "N", "2"],
                                                        key="ODDS_MILES",
                                                        visible=False, hide_vertical_scroll=True,
                                                        size=(None, nb_bookmakers))]]),],
                                [sg.Button("Calculer", key="BEST_MATCH_MILES")],
                                [sg.Button("Ignorer ce match", key="DELETE_MATCH_MILES", visible=False)],
                                [sg.Button("Réinitialiser les matches", key="RELOAD_ODDS_MILES", visible=False)],
                                [sg.Column(column_indicators_miles),
                                 sg.Column(column_results_miles),
                                 sg.Column([[sg.Text(
                                     "Répartition des mises (les totaux affichés prennent en "
                                     "compte les éventuels freebets) :",
                                     key="TEXT_MILES", visible=False)],
                                     [sg.MLine(size=(100, 12), key="RESULT_MILES",
                                               font="Consolas 10", visible=False)]])],
                                ]


layout = [[sg.TabGroup([[sg.Tab('Récupération des cotes', parsing_layout),
                         sg.Tab('Cotes', odds_layout),
                         sg.Tab('Pari simple', match_under_condition_layout),
                         sg.Tab('Pari sur un match donné', stake_layout),
                         sg.Tab('Cashback', cashback_layout),
                         sg.Tab('Pari gagnant', gagnant_layout),
                         sg.Tab('Pari combiné', combine_layout),
                         # sg.Tab('Paris à placer', stakes_layout),
                         sg.Tab('Freebet unique', freebet_layout),
                         sg.Tab('Freebets à placer', freebets_layout),
                         sg.Tab('Combiné optimisé', combi_opt_layout),
                         sg.Tab('Surebets', surebets_layout),
                         sg.Tab('Values', values_layout, visible=sb.BETA),
                         sg.Tab('Perf players', perf_players_layout, visible=sb.BETA),
                         sg.Tab('Miles', miles_layout, visible=sb.BETA)
                         ]])],
          [sg.Button('Quitter', button_color=("white", "red"))]]

# Create the Window
window = sg.Window('Paris sportifs', layout, location=(0, 0))
event, values = window.read(timeout=0)
sb.PROGRESS = 0
thread = None
thread_stakes = None
thread_combine = None
thread_perf = None
window_odds_active = False
sport = ''
old_stdout = sys.stdout
window_odds = None
sb.INTERFACE = True
start_time = time.time()
elapsed_time = 0
start_parsing = 0
palier = 0
matches_freebets = False

# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read(timeout=100)
    try:
        if sb.ABORT or not thread.is_alive():
            save_odds(sb.ODDS, PATH_DATA)
            window['PROGRESS_PARSING'].update(0, 100, visible=False)
            window["TEXT_PARSING"].update(visible=sb.ABORT)
            window["REMAINING_TIME_PARSING"].update(visible=False)
            window["STOP_PARSING"].update(visible=False)
            for site in sb.BOOKMAKERS:
                window["TEXT_{}_PARSING".format(site)].update(visible=False)
                window["PROGRESS_{}_PARSING".format(site)].update(0, 100, visible=False)
            if not sb.ABORT:
                window["START_PARSING"].update(visible=True)
                window["START_ALL_PARSING"].update(visible=sb.BETA)
                window['SUREBET_PARSING'].update("Recherche de surebet en cours", text_color="white", visible=sb.BETA)
                sports_with_surebet = get_sports_with_surebet()
                if sports_with_surebet:
                    window['SUREBET_PARSING'].update("Surebet disponible ({})".format(", ".join(sports_with_surebet)), text_color="red")
                else:
                    window['SUREBET_PARSING'].update("Aucun surebet")
                sg.SystemTray.notify('Sports-betting', 'Fin du parsing', display_duration_in_ms=750,
                                    fade_in_duration=125)
                thread = None
                print("Elapsed time : {} s\n".format(round(elapsed_time)))
        else:
            window['PROGRESS_PARSING'].update(ceil(sb.PROGRESS), 100)
            for site in sb.BOOKMAKERS:
                (window["PROGRESS_{}_PARSING".format(site)]
                 .update(ceil(sb.SITE_PROGRESS[site]), 100))
            now = time.time()
            if sb.IS_PARSING and not start_parsing:
                start_parsing = now
            elapsed_time = now - start_time
            elapsed_time_parsing = now - start_parsing
            if sb.IS_PARSING and sb.PROGRESS > palier:
                palier += 5
                sb.EXPECTED_TIME = elapsed_time * (100 / sb.PROGRESS - 1)
                time_to_display = sb.EXPECTED_TIME
                start_parsing = time.time()
            else:
                if start_parsing:
                    window["TEXT_PARSING"].update("Récupération des cotes en cours")
                    time_to_display = sb.EXPECTED_TIME - elapsed_time_parsing
                    window["REMAINING_TIME_PARSING"].update(visible=True)
                else:
                    window["TEXT_PARSING"].update("Initialisation de selenium en cours")
                    time_to_display = sb.EXPECTED_TIME - elapsed_time
            # sb.EXPECTED_TIME = int(max(0, sb.EXPECTED_TIME - 0.1))
            m, s = divmod(max(0, int(time_to_display)), 60)
            window["REMAINING_TIME_PARSING"].update('{:02d}:{:02d}'.format(int(m), int(s)))
            if sb.IS_PARSING and 100 - sb.PROGRESS < 1e-6:
                window["TEXT_PARSING"].update("Finalisation")
                window["REMAINING_TIME_PARSING"].update(visible=False)
    except AttributeError:
        pass
    try:
        if not thread_stakes.is_alive():
            window["PROGRESS_STAKES"].update(0, 100, visible=False)
            thread_stakes = None
        else:
            window["PROGRESS_STAKES"].update(ceil(sb.PROGRESS), 100)
    except AttributeError:
        pass
    try:
        if not thread_combine.is_alive():
            window["PROGRESS_COMBINE"].update(0, 100, visible=False)
            thread_combine = None
        else:
            window["PROGRESS_COMBINE"].update(ceil(sb.PROGRESS), 100)
    except AttributeError:
        pass
    try:
        if not thread_perf.is_alive():
            window["PROGRESS_PERF"].update(0, 100, visible=False)
            thread_perf = None
        else:
            window["PROGRESS_PERF"].update(ceil(sb.PROGRESS), 100)
    except AttributeError:
        pass
    try:  # see if something has been posted to Queue
        message = sb.QUEUE_TO_GUI.get_nowait()
        sb.QUEUE_FROM_GUI.put(sg.popup_yes_no(message))
    except queue.Empty:  # get_nowait() will get exception when Queue is empty
        pass  # break from the loop if no more messages are queued up
    if event == "SPORT":
        sport = values["SPORT"][0]
        competitions = get_all_competitions(sport)
        window['COMPETITIONS'].update(values=competitions)
        window['MAIN_COMPETITIONS'].update(visible=sport=="football")
    elif event == "SELECT_NONE_COMPETITION":
        window['COMPETITIONS'].update(set_to_index=[])
    elif event == "CURRENT_COMPETITIONS":
        thread_competitions = threading.Thread(target=lambda : get_current_competitions_interface(window, values))
        thread_competitions.start()
    elif event == "MAIN_COMPETITIONS":
        competitions = get_all_competitions(sport)
        big_five = ["France - Ligue 1", "Angleterre - Premier League", "Allemagne - Bundesliga", "Italie - Serie A", "Espagne - LaLiga"]
        window['COMPETITIONS'].update(set_to_index=[i for i, competition in enumerate(competitions) if competition in big_five])
    elif event == "SELECT_ALL":
        window['SITES'].update(set_to_index=[i for i, _ in enumerate(sb.BOOKMAKERS)])
    elif event == "SELECT_NONE_SITE":
        window['SITES'].update(set_to_index=[])
    elif event == 'START_PARSING':
        selected_competitions = values["COMPETITIONS"]
        selected_sites = values["SITES"]
        window["MATCHES_ODDS"].update([])
        window["MATCHES"].update([])
        if selected_competitions and selected_sites:
            window["STOP_PARSING"].update(visible=True)
            window["START_PARSING"].update(visible=False)
            window["START_ALL_PARSING"].update(visible=False)
            def parse_thread():
                """
                :return: Crée un thread pour le parsing des compétitions
                """
                sb.PROGRESS = 0
                parse_competitions(selected_competitions, sport, *selected_sites)


            thread = threading.Thread(target=parse_thread)
            thread.start()
            start_time = time.time()
            start_parsing = 0
            palier = 20
            window['PROGRESS_PARSING'].update(0, 100, visible=True)
            window["TEXT_PARSING"].update(visible=True)
            window["REMAINING_TIME_PARSING"].update(sb.EXPECTED_TIME)
            sb.SITE_PROGRESS = collections.defaultdict(int)
            for site in selected_sites:
                window["TEXT_{}_PARSING".format(site)].update(visible=True)
                window["PROGRESS_{}_PARSING".format(site)].update(0, 100, visible=True)
    elif event == 'START_ALL_PARSING':
        selected_sites = values["SITES"]
        window["MATCHES_ODDS"].update([])
        window["MATCHES"].update([])
        if selected_sites:
            window["STOP_PARSING"].update(visible=True)
            window["START_PARSING"].update(visible=False)
            window["START_ALL_PARSING"].update(visible=False)
            def parse_all_thread():
                """
                :return: Crée un thread pour le parsing des compétitions
                """
                sb.PROGRESS = 0
                for sport in ["football", "tennis", "basketball"]:
                    parse_competitions(["Tout le {}".format(sport)], sport, *selected_sites)


            thread = threading.Thread(target=parse_all_thread)
            thread.start()
            start_time = time.time()
            start_parsing = 0
            palier = 20
            window['PROGRESS_PARSING'].update(0, 100, visible=True)
            window["TEXT_PARSING"].update(visible=True)
            window["REMAINING_TIME_PARSING"].update(sb.EXPECTED_TIME)
            sb.SITE_PROGRESS = collections.defaultdict(int)
    elif event == "STOP_PARSING":
        window["STOP_PARSING"].update(visible=False)
        window["TEXT_PARSING"].update("Interruption en cours")
        sb.ABORT = True
    elif event == "BEST_MATCH_UNDER_CONDITION":
        best_match_under_conditions_interface(window, values)
    elif event == "DELETE_MATCH_UNDER_CONDITION":
        match_under_condition = window["MATCH_UNDER_CONDITION"].get()
        sport_under_condition = window["SPORT_UNDER_CONDITION"].get()
        if sport_under_condition and match_under_condition in sb.ODDS[sport_under_condition[0]]:
            del sb.ODDS[sport_under_condition[0]][match_under_condition]
    elif event == "RELOAD_ODDS_UNDER_CONDITION":
        sb.ODDS = load_odds(PATH_DATA)
    elif event == "SPORT_STAKE":
        try:
            matches = sorted(list(sb.ODDS[values["SPORT_STAKE"][0]]))
            window['MATCHES'].update(values=matches)
        except KeyError:
            window['MATCHES'].update(values=[])
    elif event == "BEST_STAKE":
        best_stakes_match_interface(window, values)
    elif event == "BEST_MATCH_FREEBET":
        best_match_freebet_interface(window, values)
    elif event == "DELETE_MATCH_FREEBET":
        match_freebet = window["MATCH_FREEBET"].get()
        sport_freebet = window["SPORT_FREEBET"].get()
        if sport_freebet and match_freebet in sb.ODDS[sport_freebet[0]]:
            del sb.ODDS[sport_freebet[0]][match_freebet]
    elif event == "RELOAD_ODDS_FREEBET":
        sb.ODDS = load_odds(PATH_DATA)
    elif event == "BEST_MATCH_CASHBACK":
        best_match_cashback_interface(window, values)
    elif event == "BEST_MATCHES_COMBINE":
        def combine_thread():
            best_matches_combine_interface(window, values)


        thread_combine = threading.Thread(target=combine_thread)
        thread_combine.start()
        window["PROGRESS_COMBINE"].update(0, 100, visible=True)
    elif not window_odds_active and event in ["ODDS_COMBINE", "ODDS_STAKES", "ODDS_FREEBETS", "ODDS_COMBI_OPT", "ODDS_COMBINE_GAGNANT"]:
        window_odds_active = True
        table = odds_table_combine(sb.ODDS_INTERFACE)
        layout_odds = [[sg.Table(table[1:], headings=table[0], size=(None, 20))]]
        window_odds = sg.Window('Cotes', layout_odds)
    elif window_odds_active:
        ev2, vals2 = window_odds.Read(timeout=100)
        if ev2 is None or ev2 == 'Exit':
            window_odds_active = False
            window_odds.close()
    elif event == "ADD_STAKES":
        if visible_stakes < 9:
            window["SITE_STAKES_" + str(visible_stakes)].update(visible=True)
            window["STAKE_STAKES_" + str(visible_stakes)].update(visible=True)
            window["ODD_STAKES_" + str(visible_stakes)].update(visible=True)
            visible_stakes += 1
    elif event == "REMOVE_STAKES":
        if visible_stakes > 1:
            visible_stakes -= 1
            window["SITE_STAKES_" + str(visible_stakes)].update(visible=False)
            window["STAKE_STAKES_" + str(visible_stakes)].update(visible=False)
            window["ODD_STAKES_" + str(visible_stakes)].update(visible=False)
    elif event == "BEST_MATCH_STAKES":
        def stakes_thread():
            best_match_stakes_to_bet_interface(window, values, visible_stakes)


        thread_stakes = threading.Thread(target=stakes_thread)
        thread_stakes.start()
        window["PROGRESS_STAKES"].Update(visible=True)
    elif event == "ADD_FREEBETS":
        if visible_freebets < 9:
            window["SITE_FREEBETS_" + str(visible_freebets)].update(visible=True)
            window["STAKE_FREEBETS_" + str(visible_freebets)].update(visible=True)
            visible_freebets += 1
    elif event == "REMOVE_FREEBETS":
        if visible_freebets > 1:
            visible_freebets -= 1
            window["SITE_FREEBETS_" + str(visible_freebets)].update(visible=False)
            window["STAKE_FREEBETS_" + str(visible_freebets)].update(visible=False)
    elif values and values.get("MATCHES_FREEBETS") != matches_freebets:
        matches_freebets = values["MATCHES_FREEBETS"]
        matches = sorted(list(sb.ODDS["football"])) if matches_freebets else []
        window["MATCH_FREEBETS_0"].update(visible=matches_freebets, values=matches)
        window["MATCH_FREEBETS_1"].update(visible=matches_freebets, values=matches)
    elif event == "BEST_MATCH_FREEBETS":
        sb.ODDS_INTERFACE = best_matches_freebet_interface(window, values,
                                                                      visible_freebets)
    elif event == "BEST_MATCH_GAGNANT":
        best_match_pari_gagnant_interface(window, values)
    elif event == "DELETE_MATCH_GAGNANT":
        match_gagnant = window["MATCH_GAGNANT"].get()
        sport_gagnant = window["SPORT_GAGNANT"].get()
        if sport_gagnant and match_gagnant in sb.ODDS[sport_gagnant[0]]:
            del sb.ODDS[sport_gagnant[0]][match_gagnant]
    elif event == "RELOAD_ODDS_GAGNANT":
        sb.ODDS = load_odds(PATH_DATA)
    elif event == "NAME_SORT_ODDS":
        try:
            matches = sorted(list(sb.ODDS[values["SPORT_ODDS"][0]]))
            window['MATCHES_ODDS'].update(values=matches)
        except KeyError:
            window['MATCHES_ODDS'].update(values=[])
    elif event == "SEARCH_ODDS":
        try:
            matches = sorted(list([x for x in sb.ODDS[values["SPORT_ODDS"][0]] if values["SEARCH_ODDS"].lower() in x.lower()]))
            window['MATCHES_ODDS'].update(values=matches)
        except KeyError:
            window['MATCHES_ODDS'].update(values=[])
    elif event == "MATCHES_ODDS":
        odds_match_interface(window, values)
    elif event == "SPORT_ODDS" or event == "TRJ_SORT_ODDS":
        try:
            matches = sorted(list(sb.ODDS[values["SPORT_ODDS"][0]]), key=lambda x:trj_match(sb.ODDS[values["SPORT_ODDS"][0]][x])[0], reverse=True)
            window['MATCHES_ODDS'].update(values=matches)
        except KeyError:
            window['MATCHES_ODDS'].update(values=[])    
    elif event == "DELETE_SITE_ODDS":
        delete_site_interface(window, values)
        save_odds(sb.ODDS, PATH_DATA)
    elif event == "DELETE_MATCH_ODDS":
        delete_odds_interface(window, values)
        save_odds(sb.ODDS, PATH_DATA)
    elif event == "GOTO_SITE_ODDS":
        open_bookmaker_odds(window, values)
    elif event == "ADD_COMBI_OPT":
        sport = ""
        if values["SPORT_COMBI_OPT"]:
            sport = values["SPORT_COMBI_OPT"][0]
        if visible_combi_opt < 9:
            window["MATCH_COMBI_OPT_" + str(visible_combi_opt)].update(visible=True)
            window["SEARCH_MATCH_COMBI_OPT_" + str(visible_combi_opt)].update(visible=True)
            issues = ["1", "N", "2"] if sport and get_nb_outcomes(sport) == 3 else ["1", "2"]
            for issue in issues:
                window[issue+"_RES_COMBI_OPT_" + str(visible_combi_opt)].update(visible=True)
            visible_combi_opt += 1
    elif event == "REMOVE_COMBI_OPT":
        if visible_combi_opt > 1:
            visible_combi_opt -= 1
            window["MATCH_COMBI_OPT_" + str(visible_combi_opt)].update(visible=False)
            window["SEARCH_MATCH_COMBI_OPT_" + str(visible_combi_opt)].update(visible=False)
            for issue in ["1", "N", "2"]:
                window[issue+"_RES_COMBI_OPT_" + str(visible_combi_opt)].update(visible=False)
    elif event == "BEST_COMBI_OPT":
        best_combine_reduit_interface(window, values, visible_combi_opt)
    elif event == "SPORT_COMBI_OPT":
        sport = values["SPORT_COMBI_OPT"][0]
        for i in range(visible_combi_opt):
            if get_nb_outcomes(sport) == 2:
                window["N_RES_COMBI_OPT_"+str(i)].update(visible=False)
            elif get_nb_outcomes(sport) == 3:
                window["N_RES_COMBI_OPT_"+str(i)].update(visible=True)
        for i in range(9):
            if sport in sb.ODDS:
                matches = sorted(list([x + " / " + str(sb.ODDS[sport][x]["date"]) for x in sb.ODDS[sport]]))
                window['MATCH_COMBI_OPT_'+str(i)].update(values=matches)
            else:
                window['MATCH_COMBI_OPT_'+str(i)].update(values=[])
                sg.Popup("Aucun match disponible en {}".format(sport))
                break
    elif "SEARCH_MATCH_COMBI_OPT_" in event:
        if not values["SPORT_COMBI_OPT"]:
            continue
        sport = values["SPORT_COMBI_OPT"][0]
        i = event.split("_")[-1]
        if sport in sb.ODDS:
            matches = sorted(list([x + " / " + str(sb.ODDS[sport][x]["date"]) for x in sb.ODDS[sport] if values["SEARCH_MATCH_COMBI_OPT_"+i].lower() in x.lower()]))
            window['MATCH_COMBI_OPT_' + i].update(values=matches)
    elif event in (None, 'Quitter'):  # if user closes window or clicks cancel
        break
    elif event == "FIND_SUREBETS":
        find_surebets_interface(window, values)
    elif event == "MATCHES_SUREBETS":
        odds_match_surebets_interface(window, values)
    elif event == "FIND_VALUES":
        find_values_interface(window, values)
    elif event == "MATCHES_VALUES":
        odds_match_values_interface(window, values)
    elif event == "FIND_PERF":
        def perf_thread():
            find_perf_players(window, values)


        thread_perf = threading.Thread(target=perf_thread)
        thread_perf.start()
        window["PROGRESS_PERF"].update(0, 100, visible=True)
    elif event == "MIDDLES_PERF":
        display_middle_info(window, values)
    elif event == "SUREBETS_PERF":
        display_surebet_info(window, values)
    elif event == "BEST_MATCH_MILES":
        best_match_miles_interface(window, values)
    elif event == "DELETE_MATCH_MILES":
        match_miles = window["MATCH_MILES"].get()
        sport_miles = window["SPORT_MILES"].get()
        if sport_miles and match_miles in sb.ODDS[sport_miles[0]]:
            del sb.ODDS[sport_miles[0]][match_miles]
    elif event == "RELOAD_ODDS_MILES":
        sb.ODDS = load_odds(PATH_DATA)
    else:
        pass
sb.INTERFACE = False
window.close()
sys.stdout = old_stdout
for site in sb.SELENIUM_SITES:
    if site in sb.selenium_init.DRIVER:
        sb.selenium_init.DRIVER[site].quit()
colorama.init()
print(termcolor.colored('Drivers closed{}'
                        .format(colorama.Style.RESET_ALL),
                        'green'))
colorama.deinit()
