"""
Pasinobet odds scraper
"""

import datetime

import asyncio
import ssl
import re
import json

import websockets

from sportsbetting.auxiliary_functions import merge_dicts, reverse_match_odds

async def get_json_pasinobet_api(id_league, barrierebet, vbet):
    """
    Get odds JSON from league id
    """
    site_id = "599"
    if barrierebet:
        site_id = "1869622"
    elif vbet:
        site_id = "277"
    async with websockets.connect('wss://swarm-2.vbet.fr/', ssl=ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)) as websocket:
        data = {"command":"request_session",
                "params":{"language":"fra", "site_id":site_id}}
        await websocket.send(json.dumps(data))
        response = await websocket.recv()
        data = ('{"command":"get","params":{"source":"betting","what":{"region":["name"], "competition":["name", "teams_reversed"], '
                '"game":["id", "is_blocked", "start_ts","team1_name","team2_name","is_started"],'
                '"market":["event"],"event":["price","order"]},'
                '"where":{"competition":{"id":'+str(id_league)+'},"game":{"@or":[{"type":{"@in":[0,2]}},'
                '{"visible_in_prematch":1,"type":1}]},"market":{"display_key":"WINNER", "type":{"@in":["P1P2", "P1XP2"]}}}}}')
        await websocket.send(data)
        response = await websocket.recv()
        parsed = json.loads(response)
        return parsed



async def get_json_sport_pasinobet_api(sport, barrierebet, vbet):
    """
    Get odds JSON from sport
    """
    site_id = "599"
    if barrierebet:
        site_id = "1869622"
    elif vbet:
        site_id = "277"
    async with websockets.connect('wss://swarm-2.vbet.fr/', ssl=ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)) as websocket:
        data = {"command":"request_session",
                "params":{"language":"fra", "site_id":site_id}}
        await websocket.send(json.dumps(data))
        response = await websocket.recv()
        data = {"command":"get",
                "params":{"source":"betting",
                          "what":{"competition":["id", "name"]},
                          "where":{"sport":{"name":sport},
                                   "game":{"@or":[{"type":{"@in":[0, 2]}},
                                                  {"visible_in_prematch":1, "type":1}]}}}}
        await websocket.send(json.dumps(data))
        response = await websocket.recv()
        parsed = json.loads(response)
        list_odds = []
        for league in parsed["data"]["data"]["competition"].values():
            if "Compétition" in league["name"]:
                continue
            data = ('{"command":"get","params":{"source":"betting","what":{"region":["name"], "competition":["name", "teams_reversed"], '
                    '"game":["id", "is_blocked", "start_ts","team1_name","team2_name","is_started"],'
                    '"market":["event"],"event":["price","order"]},'
                    '"where":{"competition":{"id":'+str(league["id"])+'},"game":{"@or":[{"type":{"@in":[0,2]}},'
                    '{"visible_in_prematch":1,"type":1}]},"market":{"display_key":"WINNER", "type":{"@in":["P1P2", "P1XP2"]}}'
                    '}}}}')
            await websocket.send(data)
            response = await websocket.recv()
            parsed_league = json.loads(response)
            odds_league = get_odds_from_league_json(parsed_league, barrierebet, vbet)
            list_odds.append(odds_league)
        return merge_dicts(list_odds)


def get_odds_from_league_json(parsed_league, barrierebet, vbet):
    """
    Get odds from league json
    """
    bookmaker = "pasinobet"
    if barrierebet:
        bookmaker = "barrierebet"
    elif vbet:
        bookmaker = "vbet"
    regions = parsed_league["data"]["data"]["region"]
    odds_league = {}
    for region in regions.values():
        region_name = region["name"]
        competitions = region["competition"]
        for competition in competitions.values():
            competition_name = competition["name"]
            reversed_odds = competition["teams_reversed"]
            games = competition["game"]
            for game in games.values():
                if "is_started" in game and game["is_started"]:
                    continue
                if "is_blocked" in game and game["is_blocked"]:
                    continue
                if not game.get("team1_name") or not game.get("team2_name"):
                    continue
                match_id = str(game["id"])
                name = game["team1_name"].strip() + " - " + game["team2_name"].strip()
                date = datetime.datetime.fromtimestamp(game["start_ts"])
                markets = game["market"]
                for market in markets.values():
                    odds = []
                    for event in sorted(market["event"].values(), key=lambda x: x["order"]):
                        odds.append(event["price"])
                if reversed_odds:
                    name, odds = reverse_match_odds(name, odds)
                odds_league[name] = {"date":date, "odds":{bookmaker:odds}, "id":{bookmaker:match_id}, "competition": region_name + " - " + competition_name}
    return odds_league


def parse_pasinobet_api(id_league, barrierebet, vbet):
    """
    Get Pasinobet odds from league id
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    parsed = asyncio.get_event_loop().run_until_complete(get_json_pasinobet_api(id_league, barrierebet, vbet))
    return get_odds_from_league_json(parsed, barrierebet, vbet)


def parse_pasinobet_sport(sport, barrierebet, vbet):
    """
    Get Pasinobet odds from sport ("Tennis ", "Football " ...)
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return asyncio.get_event_loop().run_until_complete(get_json_sport_pasinobet_api(sport, barrierebet, vbet))


def parse_pasinobet(url, barrierebet=False, vbet=False):
    """
    Get Pasinobet odds from url
    """
    if not "https://" in url:
        return parse_pasinobet_sport(url, barrierebet, vbet)
    id_league = re.findall(r'\/\d+', url)[0].strip("/")
    return parse_pasinobet_api(id_league, barrierebet, vbet)
