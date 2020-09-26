"""
Fonctions de gestion de la base de données des noms d'équipe/joueur/compétition
"""
import colorama
import json
import os
import inspect
import sqlite3
import termcolor
import urllib
import urllib.request
import urllib.error
import datetime
import re
import unidecode
from bs4 import BeautifulSoup
import sportsbetting

PATH_DB = os.path.dirname(sportsbetting.__file__) + "/resources/teams.db"


def get_id_formatted_competition_name(competition, sport):
    """
    Retourne l'id et le nom tel qu'affiché sur comparateur-de-cotes.fr. Par
    exemple, "Ligue 1" devient "France - Ligue 1"
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT id, competition FROM competitions WHERE sport='{}'
    """.format(sport))
    for line in c.fetchall():
        strings_name = competition.lower().split()
        possible = True
        for string in strings_name:
            if string not in line[1].lower():
                possible = False
                break
        if possible:
            return line[0], line[1]


def get_competition_by_id(_id, site):
    """
    Retourne l'url d'une competition donnée sur un site donné
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT url_{} FROM competitions WHERE id='{}'
    """.format(str(site), _id))
    return c.fetchone()[0]


def get_formatted_name(name, site, sport):
    """
    Uniformisation d'un nom d'équipe/joueur d'un site donné conformément aux noms disponibles sur
    comparateur-de-cotes.fr. Par exemple, "OM" devient "Marseille"
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    res = list(c.execute("""
    SELECT name FROM names WHERE sport="{}" AND name_{}="{}"
    """.format(sport, site, name)))
    c.close()
    try:
        return res[0][0]
    except IndexError:
        colorama.init()
        print(termcolor.colored('{} {}'.format(name, site), 'red'))
        colorama.Style.RESET_ALL
        colorama.deinit()
        return "unknown team/player ".upper() + name


def get_competition_id(name, sport):
    """
    Retourne l'id d'une compétition
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT id, competition FROM competitions WHERE sport='{}'
    """.format(sport))
    for line in c.fetchall():
        strings_name = name.lower().split()
        possible = True
        for string in strings_name:
            if string not in line[1].lower():
                possible = False
                break
        if possible:
            return line[0]


def get_competition_url(name, sport, site):
    """
    Retourne l'url d'une compétition sur un site donné
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT competition, url_{} FROM competitions WHERE sport='{}'
    """.format(site, sport))
    for line in c.fetchall():
        strings_name = name.lower().split()
        possible = True
        for string in strings_name:
            if string not in line[0].lower():
                possible = False
                break
        if possible:
            return line[1]


def import_teams_by_url(url):
    """
    Ajout dans la base de données de toutes les équipes/joueurs d'une même compétition (url) ayant
    un match prévu sur comparateur-de-cotes.fr
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    sport = soup.find("title").string.split()[-1].lower()
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "-td" in line["href"] and line.text:
            _id = line["href"].split("-td")[-1]
            if not is_id_in_db(_id):
                c.execute("""
                INSERT INTO names (id, name, sport)
                VALUES ({}, "{}", "{}")
                """.format(_id, line.text, sport))
                conn.commit()
    c.close()


def import_teams_by_sport(sport):
    """
    Ajout dans la base de données de toutes les équipes/joueurs d'un même sport ayant un match prévu
    sur comparateur-de-cotes.fr
    """
    url = "http://www.comparateur-de-cotes.fr/comparateur/" + sport
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "-ed" in line["href"] and line.text and sport in line["href"]:
            import_teams_by_url(unidecode.unidecode("http://www.comparateur-de-cotes.fr/"
                                                    + line["href"]))


def import_teams_by_competition_id_thesportsdb(_id):
    url = "https://www.thesportsdb.com/api/v1/json/1/eventsnextleague.php?id=" + str(-_id)
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    dict_competition = json.loads(soup.text)
    if dict_competition["events"]:
        for event in dict_competition["events"]:
            for _id in [event["idHomeTeam"], event["idAwayTeam"]]:
                add_id_to_db_thesportsdb(-int(_id))


def is_id_in_db(_id):
    """
    Vérifie si l'id est dans la base de données
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT id FROM names WHERE id="{}"
    """.format(_id))
    for line in c.fetchall():
        return line


def is_in_db(name, sport, site):
    """
    Vérifie si le nom uniformisé de l'équipe est dans la base de données
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT id FROM names WHERE sport="{}" AND name="{}" and name_{} IS NULL
    """.format(sport, name, site))
    for line in c.fetchall():
        return line


def is_in_db_site(name, sport, site):
    """
    Vérifie si le nom de l'équipe/joueur tel qu'il est affiché sur un site est dans la base de
    données
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT id FROM names WHERE sport="{}" AND name_{}="{}"
    """.format(sport, site, name))
    for line in c.fetchall():
        return line


def get_formatted_name_by_id(_id):
    """
    Retourne le nom d'une équipe en fonction de son id dans la base de donbées
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT name FROM names WHERE id='{}'
    """.format(_id))
    try:
        return c.fetchone()[0]
    except TypeError:
        add_id_to_db(_id)
        c.execute("""
        SELECT name FROM names WHERE id='{}'
        """.format(_id))
        return c.fetchone()[0]


def add_id_to_db(_id):
    """
    Ajoute l'id d'une équipe/joueur inconnu à la base de données
    """
    if is_id_in_db(_id):  # Pour éviter les ajouts intempestifs (précaution)
        return
    url = "http://www.comparateur-de-cotes.fr/comparateur/football/Angers-td" + str(_id)
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    for line in soup.findAll("a", {"class": "otn"}):
        if str(_id) in line["href"]:
            sport = line["href"].split("/")[1]
            conn = sqlite3.connect(PATH_DB)
            c = conn.cursor()
            c.execute("""
            INSERT INTO names (id, name, sport)
            VALUES ({}, "{}", "{}")
            """.format(_id, line.text, sport))
            conn.commit()
            c.close()
            break


def add_id_to_db_thesportsdb(_id):
    if is_id_in_db(_id):  # Pour éviter les ajouts intempestifs (précaution)
        return
    url = "https://www.thesportsdb.com/api/v1/json/1/lookupteam.php?id=" + str(-_id)
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    dict_team = json.loads(soup.text)
    name = dict_team["teams"][0]["strTeam"]
    sport = (dict_team["teams"][0]["strSport"].lower().replace("soccer", "football")
             .replace("ice_hockey", "hockey-sur-glace"))
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    INSERT INTO names (id, name, sport)
    VALUES ({}, "{}", "{}")
    """.format(_id, name, sport))
    conn.commit()
    c.close()


def get_sport_by_id(_id):
    """
    Retourne le sport associé à un id d'équipe/joueur dans la base de données
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT sport FROM names WHERE id='{}'
    """.format(_id))
    try:
        return c.fetchone()[0]
    except TypeError:
        if int(_id)>0:
            add_id_to_db(_id)
        else:
            add_id_to_db_thesportsdb(_id)
        c.execute("""
        SELECT sport FROM names WHERE id='{}'
        """.format(_id))
        return c.fetchone()[0]


def add_name_to_db(_id, name, site, check=False):
    """
    Ajoute le nom de l'équipe/joueur tel qu'il est affiché sur un site dans la base de données
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    sport = get_sport_by_id(_id)
    name_is_potential_double = sport == "tennis" and any(x in name for x in ["-", "/", "&"])
    formatted_name = get_formatted_name_by_id(_id)
    id_is_potential_double = "&" in formatted_name
    if (name and is_id_available_for_site(_id, site)
            and (not name_is_potential_double ^ id_is_potential_double)):
        if check:
            if sportsbetting.INTERFACE:
                sportsbetting.QUEUE_TO_GUI.put("Créer une nouvelle donnée pour {} ({}) sur {}\n"
                                               "Nouvelle donnée : {}"
                                               .format(formatted_name, _id, site, name))
                ans = sportsbetting.QUEUE_FROM_GUI.get(True)
            else:
                ans = input("Créer une nouvelle entrée pour {} sur {} "
                            "(nouvelle entrée : {}) (y/n)"
                            .format(formatted_name, site, name))
        if not check or ans in ['y', 'Yes']:
            c.execute("""
            UPDATE names
            SET name_{0} = "{1}"
            WHERE _rowid_ = (
                SELECT _rowid_
                FROM names
                WHERE id = {2} AND name_{0} IS NULL
                ORDER BY _rowid_
                LIMIT 1
            );
            """.format(site, name, _id))
        else:
            return False
    else:
        c.execute("""
        SELECT sport, name, name_{} FROM names
        WHERE id = {}
        """.format(site, _id))
        sport, formatted_name, name_site = c.fetchone()
        if name and name != name_site:
            if sportsbetting.INTERFACE:
                sportsbetting.QUEUE_TO_GUI.put("Créer une nouvelle donnée pour {} sur {}\n"
                                               "Nouvelle donnée : {}\n"
                                               "Donnée déjà existante : {}"
                                               .format(formatted_name, site, name, name_site))
                ans = sportsbetting.QUEUE_FROM_GUI.get(True)
            else:
                ans = input("Créer une nouvelle entrée pour {} sur {} "
                            "(entrée déjà existante : {}, nouvelle entrée : {}) (y/n)"
                            .format(formatted_name, site, name_site, name))
            if ans in ['y', 'Yes']:
                if name_site:
                    c.execute("""
                    INSERT INTO names (id, name, sport, name_{})
                    VALUES ({}, "{}", "{}", "{}")
                    """.format(site, _id, formatted_name, sport, name))
                else:
                    c.execute("""
                    UPDATE names
                    SET name_{0} = "{1}"
                    WHERE _rowid_ = (
                        SELECT _rowid_
                        FROM names
                        WHERE id = {2} AND name_{0} IS NULL
                        ORDER BY _rowid_
                        LIMIT 1
                    );
                    """.format(site, name, _id))
            else:
                return False
    c.close()
    conn.commit()
    return True


def is_id_available_for_site(_id, site):
    """
    Vérifie s'il est possible d'ajouter un nom associé à un site et à un id sans créer de nouvelle
    entrée
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT name_{} FROM names WHERE id = {}
    """.format(site, _id))
    for line in c.fetchall():
        if line[0] is None:
            return True
    return False


def get_close_name(name, sport, site, only_null=True):
    """
    Cherche un nom similaire dans la base de données
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    if only_null:
        c.execute("""
        SELECT id, name FROM names WHERE sport='{}' AND name_{} IS NULL
        """.format(sport, site))
    else:
        c.execute("""
        SELECT id, name FROM names WHERE sport='{}'
        """.format(sport))
    results = []
    for line in c.fetchall():
        if (unidecode.unidecode(name.lower()) in unidecode.unidecode(line[1].lower())
                or unidecode.unidecode(line[1].lower()) in unidecode.unidecode(name.lower())):
            results.append(line)
    return results


def get_close_name2(name, sport, site, only_null=True):
    """
    Cherche un nom similaire dans la base de données en ignorant tous les sigles. Par exemple,
    "Paris SG" devient "Paris"
    """
    name = name.split("(")[0].strip()
    split_name = re.split('[ .\-,]', name)
    split_name2 = " ".join([string for string in split_name if (len(string) > 2
                                                                or string != string.upper())])
    set_name = set(map(lambda x: unidecode.unidecode(x.lower()), split_name))
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    if only_null:
        c.execute("""
        SELECT id, name FROM names WHERE sport='{}' AND name_{} IS NULL
        """.format(sport, site))
    else:
        c.execute("""
        SELECT id, name FROM names WHERE sport='{}'
        """.format(sport))
    results = []
    for line in c.fetchall():
        string_line = line[1].split("(")[0].strip()
        split_line = re.split('[ .\-,]', string_line)
        split_line2 = " ".join([string for string in split_line if (len(string) > 2
                                                                    or string != string.upper())])
        if (unidecode.unidecode(split_name2.lower()) in unidecode.unidecode(split_line2.lower())
                or unidecode.unidecode(split_line2.lower()) in unidecode.unidecode(split_name2
                                                                                   .lower())):
            results.append(line)
            continue
        set_line = set(map(lambda x: unidecode.unidecode(x.lower()), split_line))
        if set_line.issubset(set_name):
            results.append(line)
    return results


def get_close_name3(name, sport, site, only_null=True):
    """
    Cherche un nom proche dans la base de données si le nom est de la forme "Initiale prénom + Nom"
    Par exemple "R. Nadal" renverra "Rafael Nadal"
    """
    results = []
    if "." in name:
        split_name = name.split("(")[0].split(".")
        if len(split_name) == 2 and len(split_name[0]) == 1:
            init_first_name = split_name[0]
            last_name = split_name[1].strip()
            reg_exp = r'{}[a-z]+\s{}'.format(init_first_name, last_name)
            conn = sqlite3.connect(PATH_DB)
            c = conn.cursor()
            if only_null:
                c.execute("""
                SELECT id, name FROM names WHERE sport='{}' AND name_{} IS NULL
                """.format(sport, site))
            else:
                c.execute("""
                SELECT id, name FROM names WHERE sport='{}'
                """.format(sport))
            for line in c.fetchall():
                if re.match(reg_exp, line[1]):
                    results.append(line)
    return results


def get_id_by_site(name, sport, site):
    """
    Retourne l'id d'une équipe/joueur sur un site donné
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT id FROM names WHERE name_{}="{}" AND sport='{}'
    """.format(site, name, sport))
    _id = c.fetchone()
    if _id:
        return _id[0]
    return 0


def get_id_by_opponent(id_opponent, name_site_match, matches):
    """
    Trouve l'id d'une équipe/joueur grâce à l'id de ses futurs adversaires
    """
    url = "http://www.comparateur-de-cotes.fr/comparateur/football/Nice-td" + str(id_opponent)
    date_match = matches[name_site_match]["date"]
    if date_match == "undefined":
        date_match = datetime.datetime.today()
    try:
        soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    except urllib.error.HTTPError:
        return
    get_next_id = False
    for line in soup.find_all(["a", "table"]):
        if get_next_id and "class" in line.attrs and "otn" in line["class"]:
            if line["href"].split("-td")[1] != str(id_opponent):
                return line["href"].split("-td")[1]
        if "class" in line.attrs and "bettable" in line["class"]:
            for string in list(line.stripped_strings):
                if "à" in string:
                    date_time = datetime.datetime.strptime(string.lower(), "%A %d %B %Y à %Hh%M")
                    try:
                        if abs(date_time - date_match) < datetime.timedelta(days=0.5):
                            get_next_id = True
                    except TypeError:  # live
                        pass
    return


def get_id_by_opponent_thesportsdb(id_opponent, name_site_match, matches):
    url = "https://www.thesportsdb.com/api/v1/json/1/eventsnext.php?id=" + str(-id_opponent)
    date_match = matches[name_site_match]["date"]
    try:
        soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    except urllib.error.HTTPError:
        return
    dict_events = json.loads(soup.text)
    if dict_events["events"]:
        for event in dict_events["events"]:
            date_time = (datetime.datetime(*(map(int, event["dateEvent"].split("-"))),
                                           *(map(int, event["strTime"].split(":"))))
                         + datetime.timedelta(hours=2))
            if abs(date_time - date_match) < datetime.timedelta(days=0.5):
                id_home = -int(event["idHomeTeam"])
                id_away = -int(event["idAwayTeam"])
                if id_home == id_opponent:
                    return id_away
                elif id_away == id_opponent:
                    return id_home
    return

def get_time_next_match(id_competition, id_team):
    if id_competition >= 9999:
        url = "http://www.comparateur-de-cotes.fr/comparateur/football/a-td" + str(id_team)
    elif id_team > 0:
        url = "http://www.comparateur-de-cotes.fr/comparateur/football/a-ed" + str(id_competition)
    else:
        return 0
    try:
        soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
        for line in soup.find_all("a"):
            if "href" in line.attrs:
                if line["href"].split("td"+str(id_team))[0][-1] == "-":
                    strings = list(line.find_parent("tr").stripped_strings)
                    for string in strings:
                        if " à " in string:
                            return datetime.datetime.strptime(string.lower(), "%A %d %B %Y à %Hh%M")
    except urllib.error.HTTPError:
        return 0

def is_matching_next_match(id_competition, id_team, name_team, matches):
    if id_team < 0:
        return True
    try:
        date_next_match = sorted([matches[x] for x in matches.keys() if name_team in x.split(" - ")], key=lambda x: x["date"])[0]["date"]
        return date_next_match == get_time_next_match(id_competition, id_team)
    except IndexError:
        return False
        

def are_same_double(team1, team2):
    """
    Vérifie si deux équipes de double au tennis sont potentiellement identiques
    """
    return ((team1[0] in team2[0] and team1[1] in team2[1])
            or (team1[0] in team2[1] and team1[1] in team2[0])
            or (team2[0] in team1[0] and team2[1] in team1[1])
            or (team2[0] in team1[1] and team2[1] in team1[0]))


def get_double_team_tennis(team, sport, site, only_null=False):
    """
    Trouve l'équipe de double la plus proche d'une équipe donnée
    """
    if site in ["netbet", "france_pari"]:
        separator_team = "-"
    elif site in ["betclic", "winamax", "pmu", "zebet"]:
        separator_team = " / "
        if " / " not in team: # pour zebet (varie entre / et -)
            separator_team = "-"
    elif site in ["bwin", "joa", "parionssport", "pasinobet", "unibet"]:
        separator_team = "/"
    else:  # if site in ["betstars"]:
        separator_team = " & "
    results = []
    if separator_team in team:
        complete_names = unidecode.unidecode(team).lower().strip().split(separator_team)
        if site in ["betstars", "pasinobet", "pmu"]:
            players = list(map(lambda x: x.split(" ")[-1], complete_names))
        elif site in ["netbet", "france_pari", "winamax"]:
            players = list(map(lambda x: x.split(".")[-1], complete_names))
        elif site in ["parionssport"]:
            players = complete_names
        elif site in ["bwin"]:
            players = list(map(lambda x: x.split(". ")[-1], complete_names))
        elif site in ["unibet"]:
            if ", " in team:
                players = list(map(lambda x: x.split(", ")[0], complete_names))
            else:
                players = list(map(lambda x: x.split(" ")[0], complete_names))
        elif site in ["betclic"]:
            players = list(map(lambda x: x.split(" ")[0], complete_names))
        elif site in ["zebet", "joa"]:
            if "." in team:
                players = list(map(lambda x: x.split(".")[-1].split("(")[0].strip(), complete_names))
            else:
                players = list(map(lambda x: x.split(" ")[0].strip(), complete_names))
        players = list(map(lambda x:x.strip(), players))
        conn = sqlite3.connect(PATH_DB)
        c = conn.cursor()
        if only_null:
            c.execute("""
            SELECT id, name FROM names WHERE sport='tennis' AND name LIKE '% & %' AND name_{} IS NULL
            """.format(site))
        else:
            c.execute("""
            SELECT id, name FROM names WHERE sport='tennis' AND name LIKE '% & %'
            """)
        for line in c.fetchall():
            compared_players = unidecode.unidecode(line[1]).lower().split(" & ")
            if are_same_double(players, compared_players):
                results.append(line)
    return results


def get_all_competitions(sport):
    """
    Retourne toutes les compétitions d'un sport donné
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT competition FROM competitions WHERE sport='{}'
    """.format(sport))
    return sorted(list(map(lambda x: x[0], c.fetchall())))


def get_all_sports():
    """
    Retourne tous les sports disponibles dans la db
    """
    print(PATH_DB)
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT sport FROM competitions
    """)
    return sorted(list(set(map(lambda x: x[0], c.fetchall()))))


def get_competition_name_by_id(_id):
    """
    Retourne l'url d'une competition donnée sur un site donné
    """
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT competition FROM competitions WHERE id='{}'
    """.format(_id))
    try:
        return c.fetchone()[0]
    except TypeError:
        return


def get_all_current_competitions(sport):
    url = "http://www.comparateur-de-cotes.fr/comparateur/"+sport
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    id_leagues = []
    leagues = []
    for line in soup.find_all("a"):
        if "href" in line.attrs and sport in line["href"] and "ed" in line["href"]:
            id_league = int(line["href"].split("-ed")[-1])
            league_name = line.text.strip()
            id_leagues.append(id_league)
            league = get_competition_name_by_id(id_league)
            if not league:
                if sportsbetting.INTERFACE:
                    sportsbetting.QUEUE_TO_GUI.put("Créer une nouvelle compétition : {}"
                                                    .format(league_name))
                    ans = sportsbetting.QUEUE_FROM_GUI.get(True)
                    if ans == "Yes":
                        conn = sqlite3.connect(PATH_DB)
                        c = conn.cursor()
                        c.execute("""
                        INSERT INTO competitions (id, sport, competition)
                        VALUES ({}, "{}", "{}")
                        """.format(id_league, sport, league_name))
                        conn.commit()
                        c.close()
                        leagues.append(league_name)
            else:
                leagues.append(league)
    result = list(set(leagues+get_all_current_competitions_betclic(sport)))
    return result
    

def get_all_current_competitions_betclic(sport):
    """
    Retourne les compétitions disponibles sur betclic pour un sport donné
    """
    url = "https://www.betclic.fr"
    id_sports = {
        "football": (1, "football"),
        "tennis": (2, "tennis"),
        "basketball": (4, "basket-ball"),
        "rugby": (5, "rugby-a-xv"),
        "handball": (9, "hanball"),
        "hockey-sur-glace": (13, "hockey-sur-glace")
    }
    soup = BeautifulSoup(urllib.request.urlopen(url + "/" + id_sports[sport][1] + "-s" + str(id_sports[sport][0])),
                         features="lxml")
    odds = []
    links = []
    ids = []
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "/" + id_sports[sport][1] + "/" in line["href"]:
            if "https://" in line["href"]:
                link = line["href"]
            else:
                link = url + line["href"]
            if link not in links:
                links.append(link)
                if not ("onclick" in line.attrs and "Paris sur la compétition" in line["onclick"]):
                    ids.append(link.split("-e")[-1])
    def get_competition_name_by_betclic_id(_id):
        conn = sqlite3.connect(PATH_DB)
        c = conn.cursor()
        c.execute("""
        SELECT competition FROM competitions WHERE url_betclic LIKE "%-e{}"
        """.format(_id))
        result = c.fetchone()
        if result:
            return result[0]
    return [x for x in list(map(get_competition_name_by_betclic_id, ids)) if x]
    

def is_played_soon(url):
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    for line in soup.find_all("table", attrs={"class":"bettable"}):
        date_time = datetime.datetime.strptime(list(line.stripped_strings)[3].lower(), "%A %d %B %Y à %Hh%M")
        return date_time<datetime.datetime.today()+datetime.timedelta(days=7)

def get_main_competitions(sport):
    url = "http://www.comparateur-de-cotes.fr/comparateur/"+sport
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    sportsbetting.ODDS = {}
    names = []
    for line in soup.find_all(attrs={"class": "subhead"}):
        if any(x in str(line) for x in ["Événements internationaux", "Coupes européennes", "Principaux championnats", "Coupes nationales"]):
            for link in line.findParent().find_all(["a"]):
                if sport in link["href"] and is_played_soon("http://www.comparateur-de-cotes.fr/"+link["href"]):
                    names.append(link.text.strip().replace("Coupe de France", "Coupe de France FFF"))
            if "Coupes nationales" in str(line) and names:
                break
    return names

def get_google_results(query):
    for site in googlesearch.search(query+"site:wikipedia.org", lang="fr", num=1, stop=1, pause=2):
        return site

def check_consistency(team1, team2):
    return get_google_results(team1) != get_google_results(team2)


def get_all_names_from_id(_id):
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT * FROM names WHERE id="{}"
    """.format(_id))
    results = c.fetchall()
    sport, name = results[0][1:3]
    names_site = set(item for sublist in results for item in sublist[3:] if item)
    for name_site in names_site:
        yield sport, name, name_site


def add_id_to_new_db(_id):
    conn = sqlite3.connect(PATH_DB)
    for sport, name, name_site in get_all_names_from_id(_id):
        c = conn.cursor()
        c.execute("""
        INSERT INTO names_v2 (id, sport, name, name_site)
        VALUES ({}, "{}", "{}", "{}")
        """.format(_id, sport, name, name_site))
    conn.commit()

def get_all_ids():
    conn = sqlite3.connect(PATH_DB)
    c = conn.cursor()
    c.execute("""
    SELECT id FROM names
    """)
    for id_ in sorted(list(set(map(lambda x: x[0], c.fetchall())))):
        yield id_

def create_new_db():
    for _id in get_all_ids():
        if _id>133300:
            add_id_to_new_db(_id)