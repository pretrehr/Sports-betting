#!/usr/bin/env python3
"""
Assistant de paris sportifs
"""


from itertools import combinations, product
from math import log, exp
import numpy as np
import pandas as pd

def prod(data):
    """
    Calcule le produit des donnees d'un tableau
    """
    if 0 in data:
        return 0
    return exp(sum([log(_) for _ in data]))

def somme_vect(vect1, vect2):
    """
    Calcule la somme de deux vecteurs
    """
    return [vect1[i]+vect2[i] for i in range(len(vect1))]

def gain(cotes, mise=1):
    """
    Calcule le gain pour une somme des mises egale a mise
    """
    somme = 0
    taille = len(cotes)
    for combi in combinations(cotes, taille-1):
        somme += prod(combi)
    produit = prod(cotes)
    return mise*produit/somme

def gain2(cotes, rang, mise=1):
    """
    Benefice gagne en misant mise sur la rang-ieme cote de cotes
    """
    return cotes[rang]*mise-sum(mises2(cotes, mise, rang))


def mises(cotes, mise=1, output=False):
    """
    Calcule la repartition des mises pour minimiser les pertes
    avec une mise totale egale a mise
    """
    somme = 0
    taille = len(cotes)
    for combi in combinations(cotes, taille-1):
        somme += prod(combi)
    produit = prod(cotes)
    out = []
    for i in range(taille):
        out.append(mise*produit/(somme*cotes[i]))
    if output and mise != 1:
        print(round(sum(out), 2))
    return out

def troncature(nombre, precision=2):
    """
    Effectue une troncature a n chiffres apres la virgule
    """
    return int(nombre*10**precision)/10**precision

def mises2(cotes, mise_requise, choix=-1, output=False):
    """
    Calcule la repartition des mises en pariant mise_requise sur l'une des
    issues. Par defaut, mise_requise est placee sur la cote la plus basse.
    """
    mis = mises(cotes)
    if choix == -1:
        rapport = max(mis)
    else:
        rapport = mis[choix]
    for i, elem in enumerate(mis):
        mis[i] = round(mise_requise*elem/rapport, 2)
    if output:
        print("somme des mises =", sum(mis))
        print("gain min =", min([troncature(mis[i]*cotes[i])
                                 for i in range(len(mis))]))
        print("gain max =", max([troncature(mis[i]*cotes[i])
                                 for i in range(len(mis))]))
        print("perte max =",
              round(min([troncature(mis[i]*cotes[i])
                         for i in range(len(mis))])-sum(mis), 2))
    return mis

def cotes_freebet(cotes):
    """
    Calcule les cotes d'un match joue avec des paris gratuits
    """
    return list(map(lambda x: (x-1 if x>1 else 0.01), cotes))

def mises_freebets(cotes, mise):
    """
    Calcule la repartition des mises en paris gratuits pour maximiser les gains
    avec une mise totale egale a mise
    """
    return mises(cotes_freebet(cotes), mise)


def mises_freebet(cotes, freebet, issue=-1, output=False):
    """
    Calcule la repartition des mises en presence d'un freebet a placer sur l'une
    des issues. Par defaut, le freebet est place sur la cote la plus haute.
    """
    mis = []
    if issue > -1:
        cote_max = cotes[issue]
    else:
        cote_max = max(cotes)
    gains = (cote_max-1)*freebet
    max_trouve = False
    for cote in cotes:
        if cote == cote_max and not max_trouve:
            mis.append(freebet)
            max_trouve = True
        else:
            mis.append(round(gains/cote, 2))
    if output:
        print("gain sur freebet =", round(gains+freebet-sum(mis), 2))
        print("mise totale =", sum(mis))
    return mis


def cotes_combine(cotes):
    """
    Calcule les cotes de plusieurs matches combines
    """
    out = []
    res = list(product(*cotes))
    for i in res:
        out.append(round(prod(i), 4))
    return out


def meilleurs_parmi(cotes, nomb):
    """
    Calcule les n meilleurs matches parmi un ensemble de matches
    """
    return sorted(cotes, key=gain, reverse=True)[:nomb]


def pari_rembourse_si_perdant(cotes, mise_max, rang=-1, remb_freebet=False,
                              taux_remboursement=1, output=False):
    """
    Calcule les mises lorsque l'un des paris est totalement rembourse. Par
    defaut, la mise remboursee est placee sur la cote la plus basse et le
    remboursement est effectue en argent reel
    """
    taux = ((not remb_freebet) + 0.77*remb_freebet)*taux_remboursement
    if rang == -1:
        cote_max = max(cotes)
        for elem, i in enumerate(cotes):
            if i == cote_max:
                rang = elem
    gains = mise_max*cotes[rang]
    mis = []
    for i, elem in enumerate(cotes):
        if i == rang:
            mis.append(mise_max)
        else:
            mis.append((gains-mise_max*taux)/elem)
    if output:
        print("gain net =", gains-sum(mis))
        print(mis)
    return gains-sum(mis)

def promo_zebet(cotes):
    """
    Optimisation de la promotion "gain en freebet de la cote gagnee"
    """
    mis = []
    maxi = max(cotes)
    gains = maxi*2+maxi*0.77
    for cote in cotes:
        mis.append((gains-cote*0.77)/cote)
    print("somme mises=", sum(mis))
    print("gain=", gains)
    return mis

def gains_nets_boostes(cotes, taux_boost, gain_max, freebet=True, output=False):
    mise = gain_max/(max(cotes)-1)/taux_boost
    new_cotes = list(map(lambda x:x+(x-1)*taux_boost*(1-0.23*freebet), cotes))
    argmax = np.argmax(new_cotes)
    return mises2(new_cotes, mise, argmax, output = output)
