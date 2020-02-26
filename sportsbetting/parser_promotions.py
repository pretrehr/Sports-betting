#!/usr/bin/env python3

"""
Parseur pour récupérer les promotions en cours
"""

import urllib
from pprint import pprint
import selenium
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from sportsbetting import selenium_init

def get_promotions_france_pari():
    """
    Affiche les promotions proposées sur france pari
    """
    url = "https://www.france-pari.fr/promotions"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    for line in soup.find_all('a'):
        if "href" in line.attrs and "promo/" in line["href"]:
            if "1118" in line["href"] or "1375" in line["href"]:
                return
            print(parse_promotion_france_pari("https://www.france-pari.fr"+line["href"]))

def parse_promotion_france_pari(url):
    """
    Parsing d'une page de promotion sur france-pari.fr
    """
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    for line in soup.find_all():
        if "class" in line.attrs and "promotion-content" in line["class"]:
            out = ""
            for string in list(line.stripped_strings):
                if string == "Termes et Conditions" or string in ["Exemples :", "Exemple :"]:
                    return out
                if out and out[-1] in [","]:
                    out += " "+string
                elif string[0].isupper() or string[0] in ["+"]:
                    out += "\n"+string
                elif string[0] in ["."]:
                    out += string
                else:
                    out += " "+string


def get_promotions_netbet():
    """
    Affiche les promotions proposées sur netbet
    """
    url = "https://www.netbet.fr/promotions"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    for line in soup.find_all():
        if "class" in line.attrs and "resume-promo" in line["class"]:
            promotion = list(line.stripped_strings)
            promotion.remove("En savoir plus")
            print("\n".join(promotion))
            print()

def get_promotions_betclic():
    """
    Affiche les promotions proposées sur betclic
    """
    url = "https://www.betclic.fr/sport/"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    urls_promo = []
    for line in soup.find_all():
        if "class" in line.attrs and "nav-window-promo" in line["class"]:
            children = line.findChildren("a", recursive=False)
            for child in children:
                url_promo = child["href"]
                if url_promo not in ["https://www.betclic.fr/calendrier-0?Streaming=true&Live=true",
                                     "https://www.betclic.fr/sponsoring_sponsoring.aspx"]:
                    urls_promo.append(url_promo)
    for url_promo in urls_promo:
        parse_promotion_betclic(url_promo)
    if not urls_promo:
        print("Pas de promotion en cours")

def parse_promotion_betclic(url_promo):
    """
    Affiche une promotion telle qu'affichée sur betclic
    """
    url = "https://www.betclic.fr/happy-loser-10-au-12-janvier-g4161"
    url = "https://www.betclic.fr/cashback-sports-us-g4147"
    url = "https://www.betclic.fr/cashback-foot-g4053"
    url = "https://www.betclic.fr/mission-us-semaine-2-g4011"
    url = url_promo
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    print(soup.find("title").text)
    dict_steps = {}
    dict_infos = {}
    for line in soup.find_all():
        if (("id" in line.attrs and "step-event-page" in line["id"])
                or ("class" in line.attrs and "module__title" in line["class"])):
            infos = list(line.stripped_strings)
            dict_steps[infos[0]] = infos[1]
            for string in infos[2:]:
                if not(string[0].isupper() or "€" in string):
                    dict_steps[infos[0]] += " "+string
                else:
                    break
        if "class" in line.attrs and (any(x in line["class"] for x in ["content-bloc-event-page",
                                                                       "module__bloc--50",
                                                                       "module__bloc--100"])):
            infos = list(line.stripped_strings)
            try:
                dict_infos[infos[0]] = infos[1]
            except IndexError:
                if "autres" in dict_infos:
                    dict_infos["autres"] += "\n"+infos[0]
                else:
                    dict_infos["autres"] = infos[0]
    print("Étapes :")
    pprint(dict_steps)
    print("Infos :")
    pprint(dict_infos)

def get_promotions_pmu():
    """
    Affiche les promotions proposées sur pmu
    """
    url = "https://paris-sportifs.pmu.fr/promotions/3"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    out = ""
    for line in soup.find_all():
        if "class" in line.attrs and "node-pmu-promotions" in line["class"]:
            promotion = list(line.stripped_strings)
            if "PARRAINAGE" in promotion[0]:
                if out:
                    print(out)
                else:
                    print("Aucune promotion")
            out += "\n"+promotion.pop(0)+"\n"
            for string in promotion:
                if "Les cotes" in string or string == "Pariez":
                    break
                if (string[0].isupper() and out[-1] in [".", "!", "?", "…", ":", ")", "€"]
                        or string[0] in ["-", "*"]
                        or out[-1].isnumeric()):
                    out += "\n"+string
                elif string[0] in [".", ","] or out[-1] == "\n":
                    out += string
                else:
                    out += " "+string
            out += "\n"


def get_promotions_parionssport():
    url = "https://www.enligne.parionssport.fdj.fr/paris-sportifs/promotions"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    urls_promo = []
    for line in soup.findAll("div", {"class": "active"}):
        child = line.findChildren("a", recursive=False)[0]
        if "idop" in child["href"]:
            urls_promo.append(child["href"])
    for url_promo in urls_promo:
        parse_promotion_parionssport(url_promo)
    if not urls_promo:
        print("Pas de promotion en cours")


def parse_promotion_parionssport(url):
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    dict_infos = {}
    desc = " ".join(soup.findAll("div", {"class": "left"})[0].stripped_strings)
    print("Description :")
    print(desc)
    text_list = list(soup.findAll("div", {"class": "right"})[0].stripped_strings)
    for line in zip(text_list[::2], text_list[1::2]):
        dict_infos[line[0]] = line[1]
    print("\nInfos :")
    pprint(dict_infos)
    print("\n")

def get_promotions_unibet():
    selenium_init.start_selenium()
    selenium_init.DRIVER.get("https://www.unibet.fr/promotions.do")
    WebDriverWait(selenium_init.DRIVER, 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "headline-item"))
    )
    inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
    soup = BeautifulSoup(inner_html, features="lxml")
    urls = []
    for line in soup.find_all("li", {"data-headline-display":"HAD"}):
        child = line.findChildren("a", recursive=False)[0]
        if "par-ami" in child["href"]:
            break
        urls.append("https://www.unibet.fr"+child["href"])
    for url in urls:
        parse_promotion_unibet(url)
    if not urls:
        print("Pas de promotion en cours")
    selenium_init.DRIVER.quit()

def parse_promotion_unibet(url):
    selenium_init.DRIVER.get(url)
    WebDriverWait(selenium_init.DRIVER, 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "steps"))
    )
    inner_html = selenium_init.DRIVER.execute_script("return document.body.innerHTML")
    soup = BeautifulSoup(inner_html, features="lxml")
    dict_steps = {}
    out = ""
    step_number = "1"
    head_html = selenium_init.DRIVER.execute_script("return document.head.innerHTML")
    head_soup = BeautifulSoup(head_html, features="lxml")
    print(head_soup.find("title").text)
    for line in soup.find_all("div", {"class":"steps"}):
        strings = list(line.stripped_strings)[1:]
        for string in strings:
            if string.isdigit():
                dict_steps[step_number] = out.strip()
                step_number = string
                out = ""
            elif string == ".":
                out = out[:-1]
                out += ". "
            else:
                out += string+" "
        dict_steps[step_number] = out.strip()
        pprint(dict_steps)
        print()



def get_promotions_zebet():
    """
    Affiche les promotions proposées sur zebet
    """
    url = "https://www.zebet.fr/fr/page/promotions"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    url = soup.find_all("iframe")[1]["src"]
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    out = ""
    title = ""
    dict_table = {}
    dict_conditions = {}
    is_key = False
    for line in soup.find_all(attrs={"class":"accordion-image", "style":"display: yes;"}):
        elem = line.next_element.next_element.next_element.next_element.next_element.next_element
        for child in elem.findChildren("table", recursive=True):
            strings = list(child.stripped_strings)
            title = "Tableau des {} en fonction des {}".format(strings[1].lower(),
                                                               strings[0].lower())
            for key, value in zip(strings[2::2], strings[3::2]):
                dict_table[key] = value
                
        strings = list(elem.stripped_strings)
        promotion = ""
        promotion_reseau = False
        for string in strings:
            if "tirage au sort" in string or "réseau" in string:
                promotion_reseau = True
                break
            if "Les exemples :" in string:
                break
            if string in dict_table or string.lower() in title:
                break
            if string[-1] == ":":
                is_key = True
                key = string.strip(" -:")
            elif is_key:
                dict_conditions[key] = string.strip(" -:")
                is_key = False
            else:
                promotion += string.strip(" -") + "\n"
        if not promotion_reseau:
            print(promotion)
            if dict_conditions:
                print("Conditions :")
                pprint(dict_conditions)
            if dict_table:
                print(promotion_reseau)
                print("\n"+title)
                pprint(dict_table)
            print("\n")
        dict_conditions = {}
        dict_table = {}
