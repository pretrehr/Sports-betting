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

async def get_json_pasinobet_api(id_league):
    """
    Get odds JSON from league id
    """
    async with websockets.connect('wss://swarm-2.vbet.fr/', ssl=ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)) as websocket:
        data = {"command":"request_session",
                "params":{"language":"fra", "site_id":"599"}}
        await websocket.send(json.dumps(data))
        response = await websocket.recv()
        data = ('{"command":"get","params":{"source":"betting","what":{"competition":["teams_reversed"], '
                '"game":["start_ts","team1_name","team2_name","is_started"],"market":["event"],"event":["price","order"]},'
                '"where":{"competition":{"id":'+str(id_league)+'},"game":{"@or":[{"type":{"@in":[0,2]}},'
                '{"visible_in_prematch":1,"type":1}]},"market":{"display_key":"WINNER", "type":{"@in":["P1P2", "P1XP2"]}}}}}')
        await websocket.send(data)
        response = await websocket.recv()
        parsed = json.loads(response)
        return parsed


async def get_json_sport_pasinobet_api(sport):
    """
    Get odds JSON from sport
    """
    async with websockets.connect('wss://swarm-2.vbet.fr/', ssl=ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)) as websocket:
        data = {"command":"request_session",
                "params":{"language":"fra", "site_id":"599"}}
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
            data = ('{"command":"get","params":{"source":"betting","what":{"competition":["teams_reversed"], '
                    '"game":["start_ts","team1_name","team2_name","is_started"],"market":["event"],"event":["price","order"]},'
                    '"where":{"competition":{"id":'+str(league["id"])+'},"game":{"@or":[{"type":{"@in":[0,2]}},'
                    '{"visible_in_prematch":1,"type":1}]},"market":{"display_key":"WINNER", "type":{"@in":["P1P2", "P1XP2"]}}'
                    '}}}}')
            await websocket.send(data)
            response = await websocket.recv()
            parsed_league = json.loads(response)
            odds_league = get_odds_from_league_json(parsed_league)
            list_odds.append(odds_league)
        return merge_dicts(list_odds)


def get_odds_from_league_json(parsed_league):
    """
    Get odds from league json
    """
    competitions = parsed_league["data"]["data"]["competition"]
    odds_league = {}
    for competition in competitions.values():
        reversed_odds = competition["teams_reversed"]
        games = competition["game"]
        for game in games.values():
            if "is_started" in game and game["is_started"]:
                continue
            name = game["team1_name"].strip() + " - " + game["team2_name"].strip()
            date = datetime.datetime.fromtimestamp(game["start_ts"])
            markets = game["market"]
            for market in markets.values():
                odds = []
                for event in sorted(market["event"].values(), key=lambda x: x["order"]):
                    odds.append(event["price"])
            if reversed_odds:
                name, odds = reverse_match_odds(name, odds)
            odds_league[name] = {"date":date, "odds":{"pasinobet":odds}}
    return odds_league


def parse_pasinobet_api(id_league):
    """
    Get Pasinobet odds from league id
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    parsed = asyncio.get_event_loop().run_until_complete(get_json_pasinobet_api(id_league))
    return get_odds_from_league_json(parsed)


def parse_pasinobet_sport(sport):
    """
    Get Pasinobet odds from sport ("Tennis ", "Football " ...)
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return asyncio.get_event_loop().run_until_complete(get_json_sport_pasinobet_api(sport))


def parse_pasinobet(url):
    """
    Get Pasinobet odds from url
    """
    if not "https://" in url:
        return parse_pasinobet_sport(url)
    id_league = re.findall(r'\/\d+', url)[0].strip("/")
    return parse_pasinobet_api(id_league)
