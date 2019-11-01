import datetime
import locale
import time
import json
from bs4 import BeautifulSoup
import urllib
import urllib.request
import urllib.error
import selenium
import itertools
from selenium.webdriver.chrome.options import Options

locale.setlocale(locale.LC_TIME, "fr")

try:
    driver.quit()
except NameError:
    pass
options = selenium.webdriver.ChromeOptions()
prefs = {'profile.managed_default_content_settings.images':2, 'disk-cache-size': 4096}
options.add_experimental_option("prefs", prefs)
options.add_argument("--headless")
driver = selenium.webdriver.Chrome("D:/Raphaël/git/Sports-betting/chromedriver", options=options)


URLs = {"comparateur":"http://www.comparateur-de-cotes.fr/comparateur/football",
        "betclic":"https://www.betclic.fr/sport/",
        "france_pari":"https://www.france-pari.fr/",
        "pmu":"https://paris-sportifs.pmu.fr/pari/sport/25/football",
        "zebet":"https://www.zebet.fr/fr/",
        "netbet":"https://www.netbet.fr/",
        "winamax":"https://www.winamax.fr/paris-sportifs/",
        "betstars":"https://www.betstars.fr/",
        "parionssport":"https://enligne.parionssport.fdj.fr/",
        "vbet":"https://www.vbet.fr/",
        "unibet":"https://www.unibet.fr/sport/",
        "bwin":"https://sports.bwin.fr/fr/sports/football-4/paris-sportifs/monde-6/"}
        
def test_ligue1():
    sites = ["betclic", "netbet", "france_pari", "zebet", "pasinobet", "pmu", "betstars", "winamax", "unibet", "parionssport", "bwin"]
    list_odds = {}
    for site in sites:
        print(site)
        exec("list_odds['{}'] = parse_{}()".format(site, site))
    return list_odds

def test_tennis():
    sites = ["betclic"]
    list_odds ={}
    list_odds["betclic"] = parse_betclic("https://www.betclic.fr/tennis/vienne-atp-e282")
    return list_odds

def adapt_names(odds, site, sport):
    new_dict = {}
    for match in odds:
        new_match = " - ".join(list(map(lambda x:get_formated_name(x, site, sport), match.split(" - "))))
        if "UNKNOWN TEAM/PLAYER" not in new_match:
            new_dict[new_match] = odds[match]
    return new_dict

def adapt_names_to_all(dict_odds, sport):
    list_odds = []
    for site in dict_odds:
        if site in ["netbet", "zebet", "france_pari"]:
            list_odds.append(adapt_names(dict_odds[site], "netbet", sport))
        else:
            list_odds.append(adapt_names(dict_odds[site], site, sport))
    return list_odds

def merge_dict_odds(dict_odds):
    new_dict = {}
    all_keys = set()
    for odds in dict_odds:
        all_keys = all_keys.union(odds.keys())
    for match in all_keys:
        new_dict[match] = {}
        new_dict[match]["odds"] = {}
        new_dict[match]["date"] = None
        date_found = False
        for odds in dict_odds:
            if odds:
                site = list(list(odds.values())[0]["odds"].keys())[0]
                if match in odds.keys():
                    if not date_found and odds[match]["date"]!="undefined":
                        new_dict[match]["date"] = odds[match]["date"]
                        date_found = True
                    new_dict[match]["odds"][site] = odds[match]["odds"][site]
    return new_dict
            

def algo_final():
    dict_odds = test_ligue1()
    res = adapt_names_to_all(dict_odds, "football")
    res.append(ligue1_vbet)
    return merge_dict_odds(res)



def get_link(site, competition, sport="", country=""):
    if site == "winamax":
        soup = BeautifulSoup(urllib.request.urlopen(URLs[site]), features="lxml")
        for line in soup.find_all(['script']):
            if "PRELOADED_STATE" in line.text:
                json_text = line.text.split("var PRELOADED_STATE = ")[1].split(";var BETTING_CONFIGURATION")[0]
                dict = json.loads(json_text)
                tournaments = dict["tournaments"]
                categories = dict["categories"]
                for id_tournament in tournaments:
                    strings = competition.split()
                    possibleId = True
                    for string in strings:
                        if string not in tournaments[id_tournament]["tournamentName"].lower():
                            possibleId = False
                            break
                    if possibleId:
                        print(tournaments[id_tournament]["tournamentName"])
                        return URLs[site]+"sports/1/1/"+str(id_tournament)
                for id_category in categories:
                    strings = competition.split()
                    possibleId = True
                    for string in strings:
                        if string not in categories[id_category]["categoryName"].lower():
                            possibleId = False
                            break
                    if possibleId:
                        print(categories[id_category]["categoryName"])
                        return URLs[site]+"sports/1/"+str(id_category)
    if site in ["bwin", "unibet", "parionssport", "betstars", "vbet"]:
        driver = selenium.webdriver.Chrome("D:/Raphaël/git/Sports-betting/chromedriver")
        driver.get(URLs[site])
        innerHTML = driver.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(innerHTML)
    else:
        soup = BeautifulSoup(urllib.request.urlopen(URLs[site]), features="lxml")
    radical = URLs[site].split(".fr/")[0]+".fr/"
    for line in soup.find_all(["a"]):
        if "href" in line.attrs:
            strings = competition.split()
            possible_link = True
            for string in strings:
                if string not in line["href"].lower():
                    possible_link = False
                    break
            if possible_link:
                if "http" in line["href"]:
                    radical = ""
                parts_link = line["href"].lower().split("/")
                parts_link.reverse()
                for i, part in enumerate(parts_link):
                    if any([x in part for x in strings]):
                        parts_link.reverse()
                        if i:
                            return radical+"/".join(parts_link[:-i])
                        return radical+line["href"]



def parse_betclic(url=""):
    if not url:
        url = "https://www.betclic.fr/football/ligue-1-conforama-e4"
#     url = 'https://www.betclic.fr/football/angl-premier-league-e3'
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    for line in soup.find_all():
        if line.name == "time":
            date = line["datetime"]
        elif "class" in line.attrs and "hour" in line["class"]:
            time = line.text
        elif "class" in line.attrs and "match-name" in line["class"]:
            match = list(line.stripped_strings)[0] 
            date_time = datetime.datetime.strptime(date+" "+time, "%Y-%m-%d %H:%M")
        elif "class" in line.attrs and "match-odds" in line["class"]:
            odds = list(map(lambda x:float(x.replace(",", ".")), list(line.stripped_strings)))
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"betclic":odds}
            match_odds_hash[match]['date'] = date_time
    return match_odds_hash

def parse_sport_betclic(sport):
    url = "https://www.betclic.fr"
    soup = BeautifulSoup(urllib.request.urlopen(url+"/sport/"), features="lxml")
    odds = []
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "/"+sport+"/" in line["href"]:
            link = url+line["href"]
            odds.append(parse_betclic(link))
    return merge_dicts(odds)

def get_url_betclic(sport):
    url = "https://www.betclic.fr"
    soup = BeautifulSoup(urllib.request.urlopen(url+"/sport/"), features="lxml")
    dict_urls = {}
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "/"+sport+"/" in line["href"] and "onclick" in line.attrs:
            link = url+line["href"]
            dict = json.loads(('{"Category'+line["onclick"].split("Category")[1].split("}")[0]+"}").replace("'", "\""))
            dict_urls[dict["Level 2"]] = link
    return dict_urls

def compare_string_sets(set1, set2):
    dict_comp = collections.defaultdict(lambda: [0, ""])
    for string1 in set1:
        split1 = set(re.split(' | - |\\. ',unidecode.unidecode(string1.lower())))
        for string2 in set2:
            split2 = set(re.split(' | - |\\. ',unidecode.unidecode(string2.lower())))
            c = split2.intersection(split1)
            jac_dist = float(len(c)) / (len(split1) + len(split2) - len(c))
            if jac_dist>dict_comp[string1][0]:
                dict_comp[string1] = [jac_dist, string2]
            if jac_dist>dict_comp[string2][0]:
                dict_comp[string2] = [jac_dist, string1]
    for string1 in set1:
        if string1 == dict_comp[dict_comp[string1][1]][1]:
            yield string1, dict_comp[string1][1]
            
#         print(string1 +  "/"+ dict_comp[string1][1], "/", dict_comp[dict_comp[string1][1]][1])
                
            
            
            
    

def parse_france_pari(url=""):
    if not url:
        url = "https://www.france-pari.fr/competition/96-parier-sur-ligue-1-conforama"
#     url = "https://www.france-pari.fr/sport/21-parier-sur-tennis"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    for line in soup.find_all():
        if "class" in line.attrs and "date" in line["class"]:
            date = line.text+" 2019"
        elif "class" in line.attrs and "odd-event-block" in line["class"]:
            strings = list(line.stripped_strings)
            if "snc-odds-date-lib" in line["class"]:
                time = strings[0]
                i = strings.index("/")
                date_time = datetime.datetime.strptime(date+" "+time, "%A %d %B %Y %H:%M")
                match = " ".join(strings[1:i])+" - "+" ".join(strings[i+1:])
            else:
                odds = []
                for i, val in enumerate(strings):
                    if i%2:
                        odds.append(float(val.replace(",", ".")))
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {"france_pari":odds}
                match_odds_hash[match]['date'] = date_time
    return match_odds_hash
    
    

def parse_sport_france_pari(sport):
    url = "https://www.france-pari.fr"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    links = []
    odds = []
    for line in soup.find_all(["a"]):
        if "href" in line.attrs and "parier-sur-"+sport in line["href"]:
            link = url+line["href"]
            if link not in links:
                links.append(link)
                odds.append(parse_france_pari(link))
    print(links)
    return merge_dicts(odds)

def parse_pmu(url=""):
    if not url:
        url = "https://paris-sportifs.pmu.fr/pari/competition/169/football/ligue-1-conforama"
#     url = "https://paris-sportifs.pmu.fr/pari/sport/9/tennis"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    match = ""
    date_time = "undefined"
    for line in soup.find_all():
        if "data-date" in line.attrs and "shadow" in line["class"]:
            date = line["data-date"]
        elif "class" in line.attrs and "trow--live--remaining-time" in line["class"]:
            time = line.text
            try:
                date_time = datetime.datetime.strptime(date+" "+time, "%Y-%m-%d %Hh%M")
            except ValueError:
                date_time= "undefined"
        elif "class" in line.attrs and "trow--event--name" in line["class"]:
            string = "".join(list(line.stripped_strings))
            if "//" in string:
                match = string.replace("//", "-").replace("St ", "Saint-")
        elif "class" in line.attrs and "event-list-odds-list" in line["class"]:
            odds = list(map(lambda x:float(x.replace(",", ".")), list(line.stripped_strings)))
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"pmu":odds}
            match_odds_hash[match]['date'] = date_time
    return match_odds_hash

def parse_sport_pmu(sport):
    url = "https://paris-sportifs.pmu.fr"
    dict_sport = {'football': 25, 'tennis': 9, 'basket-euro': 59, 'basket-us': 12, 'rugby': 8, 'aviron': 45, 'bobsleigh': 217, 'luge': 213, 'jo': 114, 'patinage-de-vitesse': 215, 'patinage-de-vitesse-sur-piste-courte': 220, 'skeleton': 214, 'freestyle': 218, 'snowboard': 219, 'athl%C3%A9tisme': 15, 'baseball': 14, 'beach-volley': 151, 'biathlon': 84, 'billard-am%C3%A9ricain': 166, 'boxe': 11, 'cano%C3%AB-kayak': 184, 'curling': 144, 'cyclisme': 36, 'escrime': 152, 'football-am%C3%A9ricain': 164, 'golf': 4, 'halt%C3%A9rophilie': 197, 'handball': 54, 'hockey-sur-glace-eu': 160, 'hockey-sur-glace-us': 161, 'hockey-sur-gazon': 195, 'judo': 203, 'lutte': 192, 'natation': 72, 'petanque': 246, 'pentathlon-moderne': 187, 'rugby-%C3%A0-xiii': 100, 'ski-alpin': 82, 'ski-de-fond': 146, 'snooker': 159, 'sports-m%C3%A9caniques': 5, 'taekwondo': 155, 'tennis-de-table': 77, 'tir-%C3%A0-larc': 183, 'triathlon': 190, 'voile': 124, 'volley-ball': 57, 'water-polo': 168}
    return parse_pmu(url+"/pari/sport/"+str(dict_sport[sport])+"/a")
    

    

def parse_zebet(url=""):
    if not url:
        url = "https://www.zebet.fr/fr/competition/96-ligue_1_conforama"
# #     url = "https://www.zebet.fr/fr/competition/206-nba"
#     url = "https://www.zebet.fr/fr/category/143-coupe_du_monde_2019"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    for line in soup.find_all():
        if "class" in line.attrs and "bet-time" in line["class"]:
            try:
                date_time = datetime.datetime.strptime("2019/"+line.text, "%Y/%d/%m %H:%M")            
            except ValueError:
                date_time = "undefined"
        elif "class" in line.attrs and "competition" in line["class"]:
            strings = list(line.stripped_strings)
            match = (strings[1]+" - "+strings[-3]) 
            del strings[-4], strings[-3], strings[1], strings[0]
            odds = []
            for i, val in enumerate(strings):
                if not i%2:
                    odds.append(float(val.replace(",", ".")))
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"zebet":odds}
            match_odds_hash[match]['date'] = date_time
    return match_odds_hash

def parse_sport_zebet(sport):
    url = "https://www.zebet.fr/"
    links = []
    odds = []
    soup = BeautifulSoup(urllib.request.urlopen(url+"fr/"), features="lxml")
    for line in soup.find_all():
        if "class" in line.attrs and "menu-sport-cat" in line["class"] and sport in list(line.stripped_strings)[0].lower():
            for child in line.findChildren():
                if "href" in child.attrs and "fr/category/" in child["href"] and "uk-visible-small" in child["class"]:
                    link = url+child["href"]
                    odds.append(parse_zebet(link))
    return merge_dicts(odds)

def parse_netbet(url=""):
    if not url:
        url = "https://www.netbet.fr/football/france/96-ligue-1-conforama"
#     url = "https://www.netbet.fr/tennis"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    for line in soup.find_all():
        if "class" in line.attrs and "nb-date-large" in line["class"]:
            date = list(line.stripped_strings)[0]+" 2019"
            if "Aujourd'hui" in date:
                date = datetime.datetime.today().strftime("%A %d %B %Y")
        elif "class" in line.attrs and "time" in line["class"]:
            time = line.text
            try:
                date_time = datetime.datetime.strptime(date+" "+time, "%A %d %B %Y %H:%M")
            except ValueError:
                date_time = "undefined"
        elif "class" in line.attrs and "bet-libEvent" in line["class"]:
            match = list(line.stripped_strings)[0].replace("/", "-") 
        elif "class" in line.attrs and "mainOdds" in line["class"] and "uk-margin-remove" in line["class"]:
            odds = list(map(lambda x:float(x.replace(",", ".")), list(line.stripped_strings)))
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"netbet":odds}
            match_odds_hash[match]['date'] = date_time
    return match_odds_hash

def parse_sport_netbet(sport):
    return parse_netbet("https://www.netbet.fr/"+sport)

def parse_winamax(url=""):
    if not url:
        url = "https://www.winamax.fr/paris-sportifs/sports/1/7/4"
#     url = "https://www.winamax.fr/paris-sportifs/sports/5/3/77053"
    ids = url.split("/sports/")[1]
    sportId = int(ids.split("/")[0])
    try:
        categoryId = int(ids.split("/")[1])
        tournamentId = int(ids.split("/")[2])
    except IndexError:
        categoryId = -1
        tournamentId = -1
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    match_odds_hash = {}
    for line in soup.find_all(['script']):
        if "PRELOADED_STATE" in line.text:
            json_text = line.text.split("var PRELOADED_STATE = ")[1].split(";var BETTING_CONFIGURATION")[0]
            dict = json.loads(json_text)
            for matchId in dict["matches"]:
                match = dict["matches"][matchId]
#                 if (match["sportId"] == sportId 
#                     and (match["categoryId"] == categoryId or categoryId==-1)
#                     and (match["tournamentId"] == tournamentId or tournamentId==-1)
#                     and match["competitor1Id"]!=0):
                if ((match["tournamentId"]==tournamentId or tournamentId==-1)
                    and match["competitor1Id"]!=0):
                    try:
                        match_name = match["title"] 
                        date_time = datetime.datetime.fromtimestamp(match["matchStart"])
                        main_bet_id = match["mainBetId"]
                        odds_ids = dict["bets"][str(main_bet_id)]["outcomes"]
                        odds = list(map(lambda x: dict["odds"][str(x)], odds_ids))
                        match_odds_hash[match_name] = {}
                        match_odds_hash[match_name]['odds'] = {"winamax":odds}
                        match_odds_hash[match_name]['date'] = date_time
                    except KeyError:
                        pass
            return match_odds_hash
    print("Winamax non accessible")
    return {}

def parse_sport_winamax(sport):
    url = "https://www.winamax.fr/paris-sportifs/sports/"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    for line in soup.find_all(['script']):
        if "PRELOADED_STATE" in line.text:
            json_text = line.text.split("var PRELOADED_STATE = ")[1].split(";var BETTING_CONFIGURATION")[0]
            dict = json.loads(json_text)
            for key in dict["sports"]:
                if dict["sports"][key]["sportName"].lower()==sport:
                    return parse_winamax(url+key)
    


def parse_betstars(url=""): #TODO NBA
    if not url:
        url = "https://www.betstars.fr/#/soccer/competitions/2152298"
#     url = "https://www.betstars.fr/#/tennis/daily/1571004000000"
#     driver = selenium.webdriver.PhantomJS("D:/Raphaël/git/Sports-betting/phantomjs-2.1.1-windows/bin/phantomjs")
    driver.get(url)
    match_odds_hash = {}
    match = ""
    odds = []
    is_12 = False
    while not match_odds_hash:
        innerHTML = driver.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(innerHTML)
        for line in soup.findAll():
            if "Nous procédons à une mise à jour afin d'améliorer votre expérience." in line.text:
                print("Betstars inaccessible")
                return dict()
            if "id" in line.attrs and "participants" in line["id"] and not is_12:
                match = " - ".join(list(line.stripped_strings))
            if "class" in line.attrs and "afEvt__link" in line["class"]:
                is_12 = True
                match = list(line.stripped_strings)[0]
                if "@" in match:
                    teams = match.split(" @ ")
                    match = teams[1]+" - "+teams[0]
                odds = []
            if "class" in line.attrs and ("market-AB" in line["class"] or "market-BAML" in line["class"]):
                odds.append(float(list(line.stripped_strings)[0]))
            if "class" in line.attrs and "match-time" in line["class"]:
                strings = list(line.stripped_strings)
                date = strings[0]+" 2019"
                time = strings[1]
                try:
                    date_time = datetime.datetime.strptime(date+" "+time, "%d %b, %Y %H:%M")
                except ValueError:
                    date = datetime.datetime.today().strftime("%d %b %Y")
                    time = strings[0]
                    date_time = datetime.datetime.strptime(date+" "+time, "%d %b %Y %H:%M")
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {"betstars":odds}
                match_odds_hash[match]['date'] = date_time
            if "class" in line.attrs and "prices" in line["class"]:
                odds = list(map(lambda x:float(x.replace(",", ".")), list(line.stripped_strings)))
    return match_odds_hash

def parse_parionssport(url=""):
    if not url:
        url = "https://www.enligne.parionssport.fdj.fr/paris-football/france/ligue-1-conforama"
#     url = "https://www.enligne.parionssport.fdj.fr/paris-tennis"
#     url = "https://www.enligne.parionssport.fdj.fr/paris-rugby"
    driver.get(url)
    match_odds_hash = {}
    while not match_odds_hash:
        innerHTML = driver.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(innerHTML)
        for line in soup.findAll():
            if "class" in line.attrs and "wpsel-titleRubric" in line["class"]:
                if line.text.strip() == "Aujourd'hui":
                    date = datetime.date.today().strftime("%A %d %B %Y")
                else:
                    date = line.text.strip().lower()+" 2019"
            if "class" in line.attrs and "wpsel-timerLabel" in line["class"]:
                try:
                    date_time = datetime.datetime.strptime(date+" "+line.text, "%A %d %B %Y À %Hh%M")
                except ValueError:
                    date_time = "undefined"
            if "class" in line.attrs and "wpsel-desc" in line["class"]:
                match = line.text.strip().replace("St ", "Saint-")
            if "class" in line.attrs and "buttonLine" in line["class"]:
                try:
                    odds = list(map(lambda x:float(x.replace(",", ".")), list(line.stripped_strings)))
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"parionssport":odds}
                    match_odds_hash[match]['date'] = date_time
                except ValueError: #Live
                    pass
    return match_odds_hash

def parse_sport_parionssport(sport):
    return parse_parionssport("https://www.enligne.parionssport.fdj.fr/paris-"+sport)

def parse_pasinobet(url=""):
    if not url:
        url = "https://www.pasinobet.fr/#/sport/?type=0&competition=20896&sport=1&region=830001"
    driver.get(url)
    is_NBA = "competition=756" in url
    match_odds_hash = {}
#     soup = offline_soup
    while not match_odds_hash:
        innerHTML = driver.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(innerHTML)
        for line in soup.findAll():
            if "class" in line.attrs and "game-events-view-v3" in line["class"] and "vs" in line.text:
                strings = list(line.stripped_strings)
                date_time = datetime.datetime.strptime(date+" "+strings[0], "%d.%m.%y %H:%M")
                i = strings.index("vs")
                match = strings[i+1]+" - "+strings[i-1] if is_NBA else strings[i-1]+" - "+strings[i+1]
                odds = []
                next = False
                for string in strings:
                    if string == "Max:":
                        next = True
                    elif next:
                        odds.append(float(string))
                        next = False
                match_odds_hash[match] = {}
                if is_NBA:
                    odds.reverse()
                match_odds_hash[match]['odds'] = {"pasinobet":odds}
                match_odds_hash[match]['date'] = date_time         
            elif "class" in line.attrs and "time-title-view-v3" in line["class"]:
                date = line.text
    return match_odds_hash

def parse_vbet(url=""):
    if not url:
        url = "https://www.vbet.fr/paris-sportifs#/Soccer/France/548/15148040"
        url = "https://www.vbet.fr/paris-sportifs#/Soccer/France/548/15295031"
#     url = "https://www.vbet.fr/paris-sportifs#/Tennis/Russia/1321/15328921"
#     url = "https://www.vbet.fr/paris-sportifs#/RugbyUnion/World/12035/15148041"
    driver.get(url)
    match_odds_hash = {}
    while not match_odds_hash:
        innerHTML = driver.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(innerHTML)
        for line in soup.findAll():
            if "class" in line.attrs and "event-title" in line["class"]:
                match = " - ".join(list(line.stripped_strings)) 
            if "class" in line.attrs and "category-date" in line["class"]:
                date = line.text.lower()
            if "class" in line.attrs and "time" in line["class"]:
                date_time = datetime.datetime.strptime(date+" "+line.text, "%A, %d %B %Y %H:%M")
            if "class" in line.attrs and "event-list" in line["class"]:
                odds = []
                for i, val in enumerate(list(line.stripped_strings)):
                    if i%2:
                        odds.append(float(val))
                match_odds_hash[match] = {}
                match_odds_hash[match]['odds'] = {"vbet":odds}
                match_odds_hash[match]['date'] = date_time
    return match_odds_hash
    
def parse_unibet(url=""):
    if not url:
        url = "https://www.unibet.fr/sport/football/ligue-1-conforama"
#     url = "https://www.unibet.fr/sport/tennis"
    driver.get(url)
    match_odds_hash = {}
    match = ""
    while not match_odds_hash:
        innerHTML = driver.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(innerHTML)
        for line in soup.findAll():
            if "class" in line.attrs and "cell-event" in line["class"]:
                match = line.text.strip()
            if "class" in line.attrs and "datetime" in line["class"]:
                date_time = datetime.datetime.strptime("2019/"+line.text, "%Y/%d/%m %H:%M")
            if "class" in line.attrs and "oddsbox" in line["class"]:
                odds = []
                for i, val in enumerate(list(line.stripped_strings)):
                    if i%4==2:
                        try:
                            odds.append(float(val))
                        except ValueError:
                            break
                if match:
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"unibet":odds}
                    match_odds_hash[match]['date'] = date_time
    return match_odds_hash

def parse_bwin(url = ""):
    if not url:
        url = "https://sports.bwin.fr/fr/sports/football-4/paris-sportifs/france-16/ligue-1-4131"
#     url = "https://sports.bwin.fr/fr/sports/football-4/paris-sportifs/angleterre-14/premier-league-46"
#     url = "https://sports.bwin.fr/fr/sports/tennis-5"
#     url = "https://sports.bwin.fr/fr/sports/football-4"
    driver.get(url)
    match_odds_hash = {}
    is_1N2 = False
    match = ""
    n=3
    is_NBA = "nba" in url
    while not match_odds_hash:
        innerHTML = driver.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(innerHTML)
        i=0
        odds=[]
        date_time = "undefined"
        for line in soup.findAll():
            if "class" in line.attrs and "participants-pair-game" in line["class"]:
                if match and len(odds)==n:
                    if is_NBA:
                        odds.reverse()
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"bwin":odds}
                    match_odds_hash[match]['date'] = date_time
                strings = list(line.stripped_strings)
                if len(strings) == 4:
                    match = strings[0]+" ("+strings[1]+") - "+strings[2]+" ("+strings[3]+")"
                else:
                    match = strings[1]+" - "+strings[0] if is_NBA else " - ".join(strings)
                i = 0
                odds = []
            if "class" in line.attrs and "starting-time" in line["class"]:
                try:
                    date_time = datetime.datetime.strptime(line.text, "%d/%m/%Y %H:%M")
                except ValueError:
                    if "Demain" in line.text:
                        date = (datetime.datetime.today()+datetime.timedelta(days=1)).strftime("%d %b %Y")
                        time = line.text.split(" / ")[1]
                        date_time = datetime.datetime.strptime(date+" "+time, "%d %b %Y %H:%M")
                    elif "Aujourd'hui" in line.text:
                        date = datetime.datetime.today().strftime("%d %b %Y")
                        time = line.text.split(" / ")[1]
                        date_time = datetime.datetime.strptime(date+" "+time, "%d %b %Y %H:%M")
                    elif "Commence dans" in line.text:
                        date_time = datetime.datetime.strptime(datetime.datetime.today().strftime("%d %b %Y %H:%M"), "%d %b %Y %H:%M")
                        date_time += datetime.timedelta(minutes=int(line.text.split("dans ")[1].split("min")[0]))
                    elif "Commence maintenant" in line.text:
                        date_time = datetime.datetime.strptime(datetime.datetime.today().strftime("%d %b %Y %H:%M"), "%d %b %Y %H:%M")
                    else:
                        print(match, line.text)
                        date_time = "undefined"
            if "class" in line.attrs and "group-title" in line["class"] and not is_1N2:
                is_1N2 = (line.text == "Résultat 1 X 2")
            if "class" in line.attrs and "option-indicator" in line["class"]:
                if is_1N2:
                    n = 3
                else:
                    n = 2
                if i<n:
                    odds.append(float(line.text))
                    i+=1
    if match and len(odds)==n:
        if is_NBA:
            odds.reverse()
        match_odds_hash[match] = {}
        match_odds_hash[match]['odds'] = {"bwin":odds}
        match_odds_hash[match]['date'] = date_time
    return match_odds_hash

def get_teams_ligue1(site):
    exec(site+"_ligue1 = parse_"+site+"()")
    return eval('list(set(itertools.chain.from_iterable(list(map(lambda x: x.split(" - "), list('+site+'_ligue1.keys()))))))')

def get_future_opponnents(name, matches):
    future_opponents = []
    future_matches = []
    for match in matches:
        if name in match:
            future_matches.append(match)
            opponents = match.split(" - ")
            opponents.remove(name)
            future_opponents.append(opponents[0])
    return future_opponents, future_matches
    

def get_id_by_opponent(id_opponent, name_site_match, site, matches):
        url = "http://www.comparateur-de-cotes.fr/comparateur/football/Nice-td"+str(id_opponent)
        date_match = matches[name_site_match]["date"]
        soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
        opponent_ids = []
        i = 0
        get_next_id = False
        for line in soup.find_all(["a", "table"]):
            if get_next_id and "class" in line.attrs and "otn" in line["class"]:
                if line["href"].split("-td")[1]!=str(id_opponent):
                    return line["href"].split("-td")[1]
            if "class" in line.attrs and "bettable" in line["class"]:
                for string in list(line.stripped_strings):
                    if "à" in string:
                        date_time = datetime.datetime.strptime(string.lower(), "%A %d %B %Y à %Hh%M")
                        if abs(date_time-date_match)<datetime.timedelta(days=2):
                            get_next_id = True

def add_url_to_db_complete(site, sport, urls):
    set_db = set(get_db(sport))
    set_site = urls.keys()
    for compet_db, compet_site in compare_string_sets(set_db, set_site):
        add_url_to_db(compet_db, urls[compet_site], site)  
        
    

def add_names_to_db_complete(site, sport, competition):
    if "http" in competition:
        url = competition
    else:
        url = get_link(site, competition)
        print(url)
        ans = input("ok ?")
        if ans.strip() == "url":
            url = input("url:")
            ans = ""
        while ans or not url:
            competition = input("Enter competition name:")
            url = get_link(site, competition)
            print(url)
            ans = input("ok ?")
            if ans.strip() == "url":
                url = input("url:")
                ans = ""
    odds = eval("parse_{}(url)".format(site))
    matches = odds.keys()
    teams = list(set(itertools.chain.from_iterable(list(map(lambda x: x.split(" - "), list(matches))))))
    print(teams)
    teams_not_in_db_site = []
    teams_1st_round = []
    teams_2nd_round = []
    teams_3rd_round = []
    teams_4th_round = []
    teams_5th_round = []
    for team in teams:
        line = is_in_db_site(team, sport, site)
        if line:
            add_name_to_db(line[0], team, site)
        else:
            teams_not_in_db_site.append(team)
    print(teams_not_in_db_site)
    for team in teams_not_in_db_site:
        line = is_in_db(team, sport)
        if line:
            add_name_to_db(line[0], team, site)
        else:
            teams_1st_round.append(team)
    print(teams_1st_round)
    for team in teams_1st_round:
        line = find_closer_result(team, sport, site)
        if line:
            add_name_to_db(line[0], team, site)
        else:
            teams_2nd_round.append(team)
    print(teams_2nd_round)
    for team in teams_2nd_round:
        future_opponents, future_matches = get_future_opponnents(team, matches)
        found = False
        for future_opponent, future_match in zip(future_opponents, future_matches):
            id_opponent = get_id_by_site(future_opponent, sport, site)
            id = get_id_by_opponent(id_opponent, future_match, site, odds)
            if id:
                found = True
                add_name_to_db(id, team, site)
        if not found:
            teams_3rd_round.append(team)
    print(teams_3rd_round)
    for team in teams_3rd_round:
        line = find_closer_result_2(team, sport, site)
        if line:
            add_name_to_db(line[0], team, site)
        else:
            teams_4th_round.append(team)
    print(teams_4th_round)
    for team in teams_4th_round:
        future_opponents, future_matches = get_future_opponnents(team, matches)
        found = False
        for future_opponent, future_match in zip(future_opponents, future_matches):
            id_opponent = get_id_by_site(future_opponent, sport, site)
            id = get_id_by_opponent(id_opponent, future_match, site, odds)
            if id:
                found = True
                add_name_to_db(id, team, site)
        if not found:
            teams_5th_round.append(team)
    print(teams_5th_round)



def get_jaccard_sim(str1, str2): 
    a = set(str1.split()) 
    b = set(str2.split())
    c = a.intersection(b)
    return float(len(c)) / (len(a) + len(b) - len(c))