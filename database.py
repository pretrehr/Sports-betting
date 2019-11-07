import sqlite3
import unidecode
import re
from bs4 import BeautifulSoup
import urllib
import urllib.request
import urllib.error

def print_db():
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    pprint.pprint(list(c.execute("""
    select * from names
    """)))
    c.close()
    
def get_db(sport):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    res = list(map(lambda x: x[0],list(c.execute("""
    select competition from competitions WHERE sport="{}"
    """.format(sport)))))
    c.close()
    return res

def delete_db():
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    c.execute("""
    DELETE FROM players
    """)
    conn.commit()
    c.close()

def add_column(site):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    c.execute("""
    ALTER TABLE names
    ADD "name_{}" TEXT
    """.format(site))
    conn.commit()
    c.close()

def get_formated_name(name, site, sport):
    conn = sqlite3.connect('teams.db')
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
    

def import_players_in_db(url):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    sport = soup.find("title").string.split()[-1].lower()
    teams = set()
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "-td" in line["href"] and line.text:
            try:
                c.execute("""
                INSERT INTO players (id, name, sport)
                VALUES ({}, "{}", "{}")
                """.format(line["href"].split("-td")[-1], line.text, sport))
            except sqlite3.IntegrityError:
                pass
    conn.commit()
    c.close()

def import_teams_in_db(url):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    sport = soup.find("title").string.split()[-1].lower()
    teams = set()
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "-td" in line["href"] and line.text:
            try:
                c.execute("""
                INSERT INTO names (id, name, sport)
                VALUES ({}, "{}", "{}")
                """.format(line["href"].split("-td")[-1], line.text, sport))
            except sqlite3.IntegrityError:
                pass
    conn.commit()
    c.close()

def get_id(name, sport):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    c.execute("""
    SELECT id FROM names WHERE name='{}' AND sport='{}'
    """.format(name, sport))
    id = c.fetchone()
    if id:
        return id[0]
    return 0

def get_id_by_site(name, sport, site):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    c.execute("""
    SELECT id FROM names WHERE name_{}="{}" AND sport='{}'
    """.format(site, name, sport))
    id = c.fetchone()
    if id:
        return id[0]
    return 0

def is_in_db(name, sport):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    c.execute("""
    SELECT id FROM names WHERE sport="{}" AND name="{}"
    """.format(sport, name))
    for line in c.fetchall():
        return line

def is_in_db_site(name, sport, site):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    c.execute("""
    SELECT id FROM names WHERE sport="{}" AND name_{}="{}"
    """.format(sport, site, name))
    for line in c.fetchall():
        return line


def find_closer_result(name, sport, site):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    c.execute("""
    SELECT id, name FROM names WHERE sport='{}' AND name_{} IS NULL
    """.format(sport, site))
    possible_results = []
    for line in c.fetchall():
        if (unidecode.unidecode(name.lower()) in unidecode.unidecode(line[1].lower()) 
            or unidecode.unidecode(line[1].lower()) in unidecode.unidecode(name.lower())):
                return line

def find_competition(name, sport, site):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    c.execute("""
    SELECT competition, url_{} FROM competitions WHERE sport='{}'
    """.format(site, sport))
    possible_results = []
    for line in c.fetchall():
        strings_name = name.lower().split()
        possible = True
        for string in strings_name:
            if string not in line[0].lower():
                possible = False
                break
        if possible:
            return line[1]

def find_competition_id(name, sport):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    c.execute("""
    SELECT id, competition FROM competitions WHERE sport='{}'
    """.format(sport))
    possible_results = []
    for line in c.fetchall():
        strings_name = name.lower().split()
        possible = True
        for string in strings_name:
            if string not in line[1].lower():
                possible = False
                break
        if possible:
            return line[0]

def add_name_to_db(id, name, site):
    conn = sqlite3.connect('teams.db')
    c2 = conn.cursor()
    c2.execute("""
    UPDATE names
    SET name_{} = "{}" WHERE id = {} AND name_{} IS NULL
    """.format(site, name, id, site))
    c2.close()
    conn.commit()

def add_url_to_db(competition, url, site):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    c.execute("""
    UPDATE competitions
    SET url_{} = "{}" WHERE competition = "{}" AND url_{} IS NULL
    """.format(site, url, competition, site))
    c.close()
    conn.commit()


def find_closer_result_2(name, sport, site):
    split_name = re.split(' |\\.',name)
    split_name2 = " ".join([string for string in split_name if (len(string)>2 or string!=string.upper())])
    return find_closer_result(split_name2, sport, site)

def import_site_in_db(url):
    conn = sqlite3.connect('teams.db')
    c = conn.cursor()
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    sport = soup.find("title").string.split()[-1].lower()
    print(sport)
    teams = set()
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "-ed" in line["href"] and line.text and sport in line["href"]:
            try:
                c.execute("""
                INSERT INTO competitions (id, competition, sport)
                VALUES ({}, "{}", "{}")
                """.format(line["href"].split("-ed")[-1], line.text.strip(), sport))
            except sqlite3.IntegrityError:
                pass
    conn.commit()
    c.close()

def import_sport_teams_in_db(sport):
    url = "http://www.comparateur-de-cotes.fr/comparateur/"+sport
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "-ed" in line["href"] and line.text and sport in line["href"]:
            import_teams_in_db("http://www.comparateur-de-cotes.fr/"+line["href"])
    
