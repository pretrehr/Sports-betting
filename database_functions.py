"""
Fonctions de gestion de la base de données des noms d'équipe/joueur/compétition
"""

import sqlite3

def get_id_formated_competition_name(competition, sport):
    """
    Retourne l'id et le nom tel qu'affiché sur comparateur-de-cotes.fr. Par
    exemple, "Ligue 1" devient "France - Ligue 1"
    """
    conn = sqlite3.connect('teams.db')
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
    conn = sqlite3.connect('teams.db')
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
