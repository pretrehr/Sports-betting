import sportsbetting as sb
from sportsbetting.bookmakers import betclic, parionssport, pmu, unibet, winamax, zebet
from sportsbetting.user_functions import parse_competitions
from sportsbetting.basic_functions import gain

def keep_maximum_odds(odds1, odds2, books1, books2):
    out = [[], []]
    for odd1, odd2, book1, book2 in zip(odds1, odds2, books1, books2):
        if odd2 > odd1:
            out[0].append(odd2)
            out[1].append(book2)
        else:
            out[0].append(odd1)
            out[1].append(book1)
    return out


def merge_dicts_nba(match, id_betclic, id_parionssport, id_pmu, id_unibet, id_winamax, id_zebet):
    odds = {
        "betclic": betclic.get_sub_markets_players_basketball_betclic(id_betclic),
        "parionssport": parionssport.get_sub_markets_players_basketball_parionssport(id_parionssport),
#         "pmu": pmu.get_sub_markets_players_basketball_pmu(id_pmu),
        "unibet": unibet.get_sub_markets_players_basketball_unibet(id_unibet),
        "winamax": winamax.get_sub_markets_players_basketball_winamax(id_winamax),
        "zebet" : zebet.get_sub_markets_players_basketball_zebet(id_zebet)
    }
    bookmakers = odds.keys()
    sub_markets = ['Points + passes + rebonds', 'Passes', 'Rebonds', 'Points + passes', 'Points + rebonds', 'Passes + rebonds']
    best = {}
    best_books = {}
    middles = {}
    surebets = {}
    for a, sub_market in enumerate(sub_markets):
        best[sub_market] = {}
        best_books[sub_market] = {}
        players_limits = set()
        for bookmaker in bookmakers:
            if sub_market in odds[bookmaker]:
                players_limits |= odds[bookmaker][sub_market].keys()
        previous_player = ""
        previous_limit = 0
        players = []
        for player_limit in players_limits:
            player, limit = player_limit.split("_")
            players.append([player, float(limit)])
        for player, limit in sorted(list(players)):
#             print(player)
#             print(player, limit)
            same_player = previous_player == player
            player_dict = player + "_" + str(limit)
            previous_player_dict = previous_player + "_" + str(previous_limit)
            best[sub_market][player_dict] = [1, 1]
            best_books[sub_market][player_dict] = ["", ""]
            i = 0
            for book in bookmakers:
                tmp_books = [book, book]
                if sub_market not in odds[book]:
                    continue
                if player_dict not in odds[book][sub_market]:
                    i += 1
#                     print(player, "not found", book)
                    continue
                best[sub_market][player_dict], best_books[sub_market][player_dict] = keep_maximum_odds(best[sub_market][player_dict],
                                                                                             odds[book][sub_market][player_dict],
                                                                                             best_books[sub_market][player_dict], tmp_books)
            if len(best[sub_market][player_dict])>1:# and gain(best[sub_market][player_dict]) > 0.99:
#                 print("*** surebet", player, limit, sub_market, gain(best[sub_market][player_dict]), best_books[sub_market][player_dict], best[sub_market][player_dict])
#                 surebets.append([player, limit, sub_market, best[sub_market][player_dict], gain(best[sub_market][player_dict]), best_books[sub_market][player_dict]])
                surebets[player + " / " + str(limit) + " " + sub_market] = {"match":match, "odds": best[sub_market][player_dict], "bookmakers" : best_books[sub_market][player_dict]}
            if same_player and len(best[sub_market][player_dict])>1 and len(best[sub_market][previous_player_dict])>1:
#                 print(previous_player, player)
                odds_middle = [best[sub_market][previous_player_dict][0], best[sub_market][player_dict][1]]
                books_middle = [best_books[sub_market][previous_player_dict][0], best_books[sub_market][player_dict][1]]
#                 print(odds_middle, gain(odds_middle))
#                 if gain(odds_middle)>0.80 and limit < 10 or abs(float(limit)-float(previous_limit))>1:
#                     print("*** middle", previous_player, previous_limit, player, limit, sub_market, odds_middle, gain(odds_middle), books_middle)
#                     middles.append([player, previous_limit, limit, sub_market, odds_middle, gain(odds_middle), books_middle])
                middles[player + " / " + str(previous_limit) + " - " + str(limit) + " " + sub_market] = {"odds": odds_middle, "bookmakers" : books_middle, "match":match}
            previous_player, previous_limit = player, limit
    return surebets, middles


def get_surebets_players_nba(reload_matches=False):
    if reload_matches:
        parse_competitions(["Etats-Unis - NBA"], "basketball", "betclic", "parionssport", "unibet", "winamax", "zebet")
    surebets = {}
    middles = {}
    sb.PROGRESS = 0
    n = len(sb.ODDS["basketball"])
    for match in sb.ODDS["basketball"]:
        if "id" not in sb.ODDS["basketball"][match]:
            continue
#         print(match)
        id_betclic = sb.ODDS["basketball"][match]["id"].get("betclic")
        id_parionssport = sb.ODDS["basketball"][match]["id"].get("parionssport")
        id_pmu = 0# sb.ODDS["basketball"][match]["id"].get("pmu")
        id_unibet = sb.ODDS["basketball"][match]["id"].get("unibet")
        id_winamax = sb.ODDS["basketball"][match]["id"].get("winamax")
        id_zebet = sb.ODDS["basketball"][match]["id"].get("zebet")
        surebets_match, middles_match = merge_dicts_nba(match, id_betclic, id_parionssport, id_pmu, id_unibet, id_winamax, id_zebet)
        surebets = {**surebets, **surebets_match}
        middles = {**middles, **middles_match}
        sb.PROGRESS += 100/n
    return surebets, middles
    