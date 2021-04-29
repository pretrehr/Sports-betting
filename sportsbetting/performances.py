import sportsbetting as sb
from sportsbetting.auxiliary_functions import merge_dict_odds, valid_odds
from sportsbetting.bookmakers import betclic, parionssport, pinnacle, pmu, unibet, winamax, zebet
from sportsbetting.user_functions import parse_competitions
from sportsbetting.basic_functions import gain

def keep_maximum_odds(odds1, odds2, books1, books2):
    out = [[], []]
    for odd1, odd2, book1, book2 in zip(odds1, odds2, books1, books2):
        if not (odd1 and odd2):
            continue
        if odd2 > odd1:
            out[0].append(odd2)
            out[1].append(book2)
        else:
            out[0].append(odd1)
            out[1].append(book1)
    return out

def get_middle_odds(odds1, odds2):
    bookmakers = odds1.keys() | odds2.keys()
    valid = False
    odds = {bookmaker:[1.01, 1.01] for bookmaker in bookmakers}
    for bookmaker1 in odds1:
        odds[bookmaker1][0] = odds1[bookmaker1][0]
    for bookmaker2 in odds2:
        if odds2[bookmaker2][1] != 1.01:
            valid = True
        odds[bookmaker2][1] = odds2[bookmaker2][1]
    if not valid:
        return None
    return odds

def merge_dicts_nba(match, id_betclic, id_parionssport, id_pinnacle, id_pmu, id_unibet, id_winamax, id_zebet):
    odds = [
        betclic.get_sub_markets_players_basketball_betclic(id_betclic),
        parionssport.get_sub_markets_players_basketball_parionssport(id_parionssport),
        pinnacle.get_sub_markets_players_basketball_pinnacle(id_pinnacle),
        pmu.get_sub_markets_players_basketball_pmu(id_pmu),
        unibet.get_sub_markets_players_basketball_unibet(id_unibet),
        winamax.get_sub_markets_players_basketball_winamax(id_winamax),
        zebet.get_sub_markets_players_basketball_zebet(id_zebet)
    ]
    bookmakers = ["betclic", "pasionssport", "pinnacle", "pmu", "unibet", "winamax", "zebet"]
    sub_markets = ['Points + passes + rebonds', 'Passes', 'Rebonds', 'Points + passes', 'Points + rebonds', 'Passes + rebonds', 'Points', '3 Points']
    best = {}
    best_books = {}
    middles = {}
    surebets = {}
    for sub_market in sub_markets:
        odds_sub_market = valid_odds(merge_dict_odds([x.get(sub_market, {}) for x in odds], False), "basketball")
        players_limits = odds_sub_market.keys()
        previous_player = ""
        previous_limit = 0
        players = []
        for player_limit in players_limits:
            player, limit = player_limit.split("_")
            players.append([player, float(limit)])
        for player, limit in sorted(list(players)):
            same_player = previous_player == player
            player_dict = player + "_" + str(limit)
            previous_player_dict = previous_player + "_" + str(previous_limit)
            surebets[player + " / " + str(limit) + " " + sub_market] = {"match":match, "odds": odds_sub_market[player_dict]["odds"]}
            if same_player:
                odds_middle = get_middle_odds(odds_sub_market[previous_player_dict]["odds"], odds_sub_market[player_dict]["odds"])
                if odds_middle:
                    middles[player + " / " + str(previous_limit) + " - " + str(limit) + " " + sub_market] = {"odds": odds_middle, "match":match}
            previous_player, previous_limit = player, limit
    return surebets, middles


def get_surebets_players_nba(bookmakers, competition):
    parse_competitions([competition], "basketball", *bookmakers)
    surebets = {}
    middles = {}
    sb.PROGRESS = 0
    n = len(sb.ODDS["basketball"])
    for match in sb.ODDS["basketball"]:
        if "id" not in sb.ODDS["basketball"][match]:
            continue
        id_betclic = sb.ODDS["basketball"][match]["id"].get("betclic")
        id_parionssport = sb.ODDS["basketball"][match]["id"].get("parionssport")
        id_pinnacle = sb.ODDS["basketball"][match]["id"].get("pinnacle")
        id_pmu = sb.ODDS["basketball"][match]["id"].get("pmu")
        id_unibet = sb.ODDS["basketball"][match]["id"].get("unibet")
        id_winamax = sb.ODDS["basketball"][match]["id"].get("winamax")
        id_zebet = sb.ODDS["basketball"][match]["id"].get("zebet")
        surebets_match, middles_match = merge_dicts_nba(match, id_betclic, id_parionssport, id_pinnacle, id_pmu, id_unibet, id_winamax, id_zebet)
        surebets = {**surebets, **surebets_match}
        middles = {**middles, **middles_match}
        sb.PROGRESS += 100/n
    return surebets, middles
    