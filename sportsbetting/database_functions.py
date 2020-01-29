"""
Fonctions de gestion de la base de données des noms d'équipe/joueur/compétition
"""

import sqlite3
import urllib
import datetime
import re
import unidecode
from bs4 import BeautifulSoup

def get_id_formated_competition_name(competition, sport):
    """
    Retourne l'id et le nom tel qu'affiché sur comparateur-de-cotes.fr. Par
    exemple, "Ligue 1" devient "France - Ligue 1"
    """
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
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
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
    c = conn.cursor()
    c.execute("""
    SELECT url_{} FROM competitions WHERE id='{}'
    """.format(str(site), _id))
    return c.fetchone()[0]

def get_formated_name(name, site, sport):
    """
    Uniformisation d'un nom d'équipe/joueur d'un site donné conformément aux noms disponibles sur
    comparateur-de-cotes.fr. Par exemple, "OM" devient "Marseille"
    """
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
    c = conn.cursor()
    res = list(c.execute("""
    SELECT name FROM names WHERE sport="{}" AND name_{}="{}"
    """.format(sport, site, name)))
    c.close()
    try:
        return res[0][0]
    except IndexError:
        print(name, site)
        return "unknown team/player ".upper()+name


def get_competition_id(name, sport):
    """
    Retourne l'id d'une compétition
    """
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
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
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
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
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
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
    url = "http://www.comparateur-de-cotes.fr/comparateur/"+sport
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "-ed" in line["href"] and line.text and sport in line["href"]:
            import_teams_by_url(unidecode.unidecode("http://www.comparateur-de-cotes.fr/"
                                                    +line["href"]))


def is_id_in_db(_id):
    """
    Vérifie si l'id est dans la base de données
    """
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
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
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
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
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
    c = conn.cursor()
    c.execute("""
    SELECT id FROM names WHERE sport="{}" AND name_{}="{}"
    """.format(sport, site, name))
    for line in c.fetchall():
        return line

def get_formated_name_by_id(_id):
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
    c = conn.cursor()
    c.execute("""
    SELECT name FROM names WHERE id='{}'
    """.format(_id))
    try:
        return c.fetchone()[0]
    except TypeError:
        url = "http://www.comparateur-de-cotes.fr/comparateur/football/Angers-td"+str(_id)
        soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
        for line in soup.findAll("a", {"class": "otn"}):
            if str(_id) in line["href"]:
                print(line.text)
                sport = line["href"].split("/")[1]
                print(sport)
                conn = sqlite3.connect("sportsbetting/resources/teams.db")
                c = conn.cursor()
                c.execute("""
                INSERT INTO names (id, name, sport)
                VALUES ({}, "{}", "{}")
                """.format(_id, line.text, sport))
                conn.commit()
                c.close()
                return line.text
    

def add_name_to_db(_id, name, site):
    """
    Ajoute le nom de l'équipe/joueur tel qu'il est affiché sur un site dans la base de données
    """
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
    c = conn.cursor()
    name_is_potential_double = any(x in name for x in ["-", "/", "&"])
    id_is_potential_double = "&" in get_formated_name_by_id(_id)
    if is_id_available_for_site(_id, site) and (not (name_is_potential_double ^ id_is_potential_double)):
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
        c.execute("""
        SELECT sport, name, name_{} FROM names
        WHERE id = {}
        """.format(site, _id))
        sport, formated_name, name_site = c.fetchone()
        if name != name_site:
            ans = input("Créer une nouvelle entrée pour {} sur {} "
                        "(entrée déjà existante : {}, nouvelle entrée : {}) (y/n)"
                        .format(formated_name, site, name_site, name))
            if ans == 'y':
                c.execute("""
                INSERT INTO names (id, name, sport, name_{})
                VALUES ({}, "{}", "{}", "{}")
            """.format(site, _id, formated_name, sport, name))
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
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
    c = conn.cursor()
    c.execute("""
    SELECT name_{} FROM names WHERE id = {}
    """.format(site, _id))
    for line in c.fetchall():
        if line[0] is None:
            return True
    return False


def get_close_name(name, sport, site):
    """
    Cherche un nom similaire dans la base de données
    """
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
    c = conn.cursor()
    c.execute("""
    SELECT id, name FROM names WHERE sport='{}' AND name_{} IS NULL
    """.format(sport, site))
    for line in c.fetchall():
        if (unidecode.unidecode(name.lower()) in unidecode.unidecode(line[1].lower())
                or unidecode.unidecode(line[1].lower()) in unidecode.unidecode(name.lower())):
            return line


def get_close_name2(name, sport, site):
    """
    Cherche un nom similaire dans la base de données en ignorant tous les sigles. Par exemple,
    "Paris SG" devient "Paris"
    """
    split_name = re.split(' |\\.|-|,', name)
    split_name2 = " ".join([string for string in split_name if (len(string) > 2
                                                                or string != string.upper())])
    set_name = set(map(lambda x: unidecode.unidecode(x.lower()), split_name))
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
    c = conn.cursor()
    c.execute("""
    SELECT id, name FROM names WHERE sport='{}' AND name_{} IS NULL
    """.format(sport, site))
    for line in c.fetchall():
        split_line = re.split(' |\\.|-|,', line[1])
        split_line2 = " ".join([string for string in split_line if (len(string) > 2
                                                                    or string != string.upper())])
        if (unidecode.unidecode(split_name2.lower()) in unidecode.unidecode(split_line2.lower())
                or unidecode.unidecode(split_line2.lower()) in unidecode.unidecode(split_name2
                                                                                   .lower())):
            return line
        set_line = set(map(lambda x: unidecode.unidecode(x.lower()), split_line))
        if set_line.issubset(set_name):
            return line


def get_close_name3(name, sport, site):
    """
    Cherche un nom proche dans la base de données si le nom est de la forme "Initiale prénom + Nom"
    Par exemple "R. Nadal" renverra "Rafael Nadal"
    """
    if "." in name:
        splitted_name = name.split("(")[0].split(".")
        if len(splitted_name) == 2 and len(splitted_name[0]) == 1:
            init_first_name = splitted_name[0]
            last_name = splitted_name[1].strip()
            reg_exp = r'{}[a-z]+\s{}'.format(init_first_name, last_name)
            conn = sqlite3.connect("sportsbetting/resources/teams.db")
            c = conn.cursor()
            c.execute("""
            SELECT id, name FROM names WHERE sport='{}' AND name_{} IS NULL
            """.format(sport, site))
            for line in c.fetchall():
                if re.match(reg_exp, line[1]):
                    return line


def get_id_by_site(name, sport, site):
    """
    Retourne l'id d'une équipe/joueur sur un site donné
    """
    conn = sqlite3.connect("sportsbetting/resources/teams.db")
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
    url = "http://www.comparateur-de-cotes.fr/comparateur/football/Nice-td"+str(id_opponent)
    date_match = matches[name_site_match]["date"]
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
                        if abs(date_time-date_match) < datetime.timedelta(days=2):
                            get_next_id = True
                    except TypeError: #live
                        pass
    return


def are_same_double(team1, team2):
    """
    Vérifie si deux équipes de double au tennis sont potentiellement identiques
    """
    return ((team1[0] in team2[0] and team1[1] in team2[1])
            or (team1[0] in team2[1] and team1[1] in team2[0])
            or (team2[0] in team1[0] and team2[1] in team1[1])
            or (team2[0] in team1[1] and team2[1] in team1[0]))


def get_double_team_tennis(team, site):
    """
    Trouve l'équipe de double la plus proche d'une équipe donnée
    """
    if site in ["netbet"]:
        separator_team = "-"
    elif site in ["betclic", "winamax", "pmu", "zebet"]:
        separator_team = " / "
    elif site in ["bwin", "joa", "parionssport", "pasinobet", "unibet"]:
        separator_team = "/"
    elif site in ["betstars"]:
        separator_team = " & "
    if separator_team in team:
        complete_names = unidecode.unidecode(team).lower().strip().split(separator_team)
        if site in ["betstars", "pasinobet", "pmu"]:
            players = list(map(lambda x: x.split(" ")[-1], complete_names))
        elif site in ["netbet", "winamax"]:
            players = list(map(lambda x: x.split(".")[-1], complete_names))
        elif site in ["joa", "parionssport"]:
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
        elif site in ["zebet"]:
            players = list(map(lambda x: x.split(".")[-1].split("(")[0].strip(), complete_names))
        conn = sqlite3.connect("sportsbetting/resources/teams.db")
        c = conn.cursor()
        c.execute("""
        SELECT id, name FROM names WHERE sport='tennis' AND name LIKE '% & %'
        """)
        for line in c.fetchall():
            compared_players = unidecode.unidecode(line[1]).lower().split(" & ")
            if are_same_double(players, compared_players):
                return line
