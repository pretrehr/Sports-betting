#!/usr/bin/env python3

"""
Parseur pour récupérer les promotions en cours
"""

def get_promotions_france_pari():
    url = "https://www.france-pari.fr/promotions"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    for line in soup.find_all():
        if "class" in line.attrs and "promo" in line["class"]:
            if "MultiBoost" not in line.text:
                promotion = list(line.stripped_strings)
                promotion.remove("J'en\xa0profite")
                print("\n".join(promotion))
                print()

def get_promotions_netbet():
    url = "https://www.netbet.fr/promotions"
    soup = BeautifulSoup(urllib.request.urlopen(url), features="lxml")
    for line in soup.find_all():
        if "class" in line.attrs and "resume-promo" in line["class"]:
            promotion = list(line.stripped_strings)
            promotion.remove("En savoir plus")
            print("\n".join(promotion))
            print()