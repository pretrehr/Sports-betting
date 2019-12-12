import urllib
import urllib.request
import selenium
from bs4 import BeautifulSoup

url = "https://www.betclic.fr/football/ligue-europa-e3453"
options = selenium.webdriver.ChromeOptions()
prefs = {'profile.managed_default_content_settings.images':2, 'disk-cache-size': 4096}
options.add_argument('log-level=3')
options.add_experimental_option("prefs", prefs)
driver = selenium.webdriver.Chrome("chromedriver", options=options)
driver.maximize_window()
driver.get(url)
innerHTML = driver.execute_script("return document.body.innerHTML")
categories = driver.find_elements_by_class_name("marketTypeCodeName")
match_odds_hash = {}
for cat in categories:
    if "Qui marquera le plus" in cat.text:
        cat.click()
        innerHTML = driver.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(innerHTML, features="lxml")
        for line in soup.find_all():
            if "class" in line.attrs and "expand-selection-bet" in line["class"]:
                strings = list(line.stripped_strings)
                try:
                    match = strings[0]+" - "+strings[-2]
                except IndexError:
                    match = strings[0]
                odds = list(map(lambda x: float(x.replace(",", ".")), strings[1::2]))
                if len(odds)==3:
                    match_odds_hash[match] = {}
                    match_odds_hash[match]['odds'] = {"betclic":odds}
                    match_odds_hash[match]['date'] = "undefined"
driver.quit()
soup = BeautifulSoup(urllib.request.urlopen("file:///D:/Rapha%C3%ABl/Mes%20documents/Paris/Betclic%20buteurs/duel_buteurs.html"), features="lxml")
for line in soup.find_all():
    if "class" in line.attrs and "expand-selection-bet" in line["class"]:
        strings = list(line.stripped_strings)
        match = strings[0].replace("(v.", "-").replace(")", "")
        odds = list(map(lambda x: float(x.replace(",", ".")), strings[1::2]))
        if len(odds)==3:
            match_odds_hash[match] = {}
            match_odds_hash[match]['odds'] = {"betclic":odds}
            match_odds_hash[match]['date'] = "undefined"

MAIN_ODDS = match_odds_hash

