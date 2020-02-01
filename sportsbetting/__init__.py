"""
initialisation du module
"""

ALL_ODDS_COMBINE = {}
ODDS = {}

class UnavailableCompetitionException(Exception):
    """
    Exception renvoyée lorsqu'une compétition est introuvable
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
