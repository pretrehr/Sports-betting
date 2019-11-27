#!/usr/bin/env python3
"""
Assistant de paris sportifs
"""


from itertools import combinations, product
from math import log, exp

def prod(data):
    """
    Calcule le produit des donnees d'un tableau
    """
    if 0 in data:
        return 0
    return exp(sum([log(_) for _ in data]))


def gain(cotes, mise=1):
    """
    Calcule le gain pour une somme des mises egale a mise
    """
    return mise/sum(map(lambda x:1/x, cotes))


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
    gains = gain(cotes, mise)
    mises_reelles = list(map(lambda x: gains/x, cotes))
    if output:
        mis = list(map(lambda x:round(x, 2), mises_reelles))
        print("somme des mises =", round(sum(mis), 2))
        print("gain min =", min([round(mis[i]*cotes[i], 2)
                                 for i in range(len(mis))]))
        print("gain max =", max([round(mis[i]*cotes[i], 2)
                                 for i in range(len(mis))]))
        print("plus-value max =",
              round(min([round(mis[i]*cotes[i], 2)
                         for i in range(len(mis))])-sum(mis), 2))
        print("mises arrondies =", mis)
    else:
        return mises_reelles


def mises2(cotes, mise_requise, choix=-1, output=False):
    """
    Calcule la repartition des mises en pariant mise_requise sur l'une des
    issues. Par defaut, mise_requise est placee sur la cote la plus basse.
    """
    if choix==-1:
        choix = np.argmin(cotes)
    gains = mise_requise*cotes[choix]
    mises_reelles = list(map(lambda x:gains/x, cotes))
    if output:
        mis = list(map(lambda x:round(x, 2), mises_reelles))
        print("somme des mises =", round(sum(mis), 2))
        print("gain min =", min([round(mis[i]*cotes[i], 2)
                                 for i in range(len(mis))]))
        print("gain max =", max([round(mis[i]*cotes[i], 2)
                                 for i in range(len(mis))]))
        print("plus-value min =",
              round(min([round(mis[i]*cotes[i], 2)
                         for i in range(len(mis))])-sum(mis), 2))
        print("plus-value max =",
              round(max([round(mis[i]*cotes[i], 2)
                         for i in range(len(mis))])-sum(mis), 2))
        print("mises arrondies =", mis)
    else:
        return mises_reelles

def cotes_freebet(cotes):
    """
    Calcule les cotes d'un match joue avec des paris gratuits
    """
    return list(map(lambda x: (x-1 if x > 1 else 0.01), cotes))

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
    if issue==-1:
        issue = np.argmax(cotes)
    mises_reelles = mises2(cotes[:issue]+[cotes[issue]-1]+cotes[issue+1:], freebet, issue)
    gains = mises_reelles[issue]*(cotes[issue]-1)
    if output:
        mis = list(map(lambda x:round(x, 2), mises_reelles))
        print("gain sur freebet =", round(gains+freebet-sum(mis), 2))
        print("gain sur freebet / mise freebet =", round(gains+freebet-sum(mis), 2)/freebet)
        print("gain =", round(gains, 2))
        print("mise totale (hors freebet) =", round(sum(mis)-freebet, 2))
        print("mises arrondies =", mis)
    else:
        return mises_reelles  


def cotes_combine(cotes):
    """
    Calcule les cotes de plusieurs matches combines
    """
    out = []
    res = list(product(*cotes))
    for i in res:
        out.append(round(prod(i), 4))
    return out


def gain_pari_rembourse_si_perdant(cotes, mise_max, rang=-1, remb_freebet=False,
                                   taux_remboursement=1):
    """
    Calcule le bénéfice lorsque l'un des paris est rembourse. Par
    defaut, la mise remboursee est placee sur la cote la plus haute et le
    remboursement est effectue en argent reel
    """
    taux = ((not remb_freebet) + 0.77*remb_freebet)*taux_remboursement
    if rang == -1:
        rang = np.argmax(cotes)
    gains = mise_max*cotes[rang]
    mis = list(map(lambda x: (gains-mise_max*taux)/x, cotes))
    mis[rang] = mise_max
    return gains-sum(mis)


def mises_pari_rembourse_si_perdant(cotes, mise_max, rang=-1, remb_freebet=False,
                                   taux_remboursement=1, output=False):
    """
    Calcule les mises lorsque l'un des paris est rembourse. Par
    defaut, la mise remboursee est placee sur la cote la plus haute et le
    remboursement est effectue en argent reel
    """
    taux = ((not remb_freebet) + 0.77*remb_freebet)*taux_remboursement
    if rang == -1:
        rang = np.argmax(cotes)
    gains = mise_max*cotes[rang]
    mis_reelles = list(map(lambda x: (gains-mise_max*taux)/x, cotes))
    mis_reelles[rang] = mise_max
    if output:
        mis = list(map(lambda x:round(x, 2), mis_reelles))
        print("gain net =", gains-sum(mis))
        print("mises arrondies =", mis)
    else:
        return mis_reelles

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

def cote_boostee(cote, boost_selon_cote = True):
    """
    Calcul de cote boostee pour promotion Betclic
    """
    if not boost_selon_cote:
        return cote+(cote-1)*0.8
    if cote < 2:
        return cote
    if cote < 2.51:
        return cote+(cote-1)*0.25*0.8
    if cote < 3.51:
        return cote+(cote-1)*0.5*0.8
    return cote+(cote-1)*0.8

def taux_boost(cote, boost_selon_cote = True):
    """
    Calcul du taux de boost pour promotion Betclic
    """
    if not boost_selon_cote:
        return 1
    if cote < 2:
        return 0
    if cote < 2.51:
        return 0.25
    if cote < 3.51:
        return 0.5
    return 1

def gains_nets_boostes(cotes, gain_max, boost_selon_cote = True, output=False):
    """
    Optimisation de gain pour promotion Betclic de type "Cotes boostees"
    """
    new_cotes = list(map(lambda x:cote_boostee(x, boost_selon_cote), cotes))
    benefice_max = 0
    for i, cote in enumerate(cotes):
        mise = gain_max/((cotes[i]-1)*taux_boost(cote, boost_selon_cote))
        mises_possibles = mises2(new_cotes, mise, i)
        mises_corrigees = []
        gain = 0
        for j, mis in enumerate(mises_possibles):
            if mis*((cotes[j]-1)*taux_boost(cotes[j], boost_selon_cote)) > gain_max+0.1:
                mises_corrigees.append(mise*cote/cotes[j])
            else:
                mises_corrigees.append(mis)
                gain=mises_corrigees[j]*new_cotes[j]
        gain-=sum(mises_corrigees)
        if gain>benefice_max:
            benefice_max = gain
            meilleures_mises = mises_corrigees
    if output:
        print("somme des mises =", sum(meilleures_mises))
        print("plus-value =", round(benefice_max, 2))
    return meilleures_mises

def pari_rembourse_si_perdant2(cotes, remboursement_max, freebet, taux_remboursement):
    rg_max = np.argmax(cotes)
    n = len(cotes)
    facteur = (1-0.23*freebet)*taux_remboursement
    systeme = []
    for i, cote in enumerate(cotes):
        line = [facteur for _ in range(n+1)]
        line[-1] = -1
        line[i] = cote
        systeme.append(line)
    line = [taux_remboursement for _ in range(n+1)]
    line[rg_max] = 0
    line[-1] = 0
    systeme.append(line)
    a = np.array(systeme)
    values = [0 for _ in range(n+1)]
    values[-1] = remboursement_max
    b = np.array(values)
    x = np.linalg.solve(a, b)
    print("Bénéfice net:", x[-1]-sum(x[:-1]))
    print(x[:-1])


def merge_dicts(dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def cotes_combine_all_sites(*matches, freebet=False):
    sites = set(matches[0]["odds"].keys())
    for match in matches:
        sites = sites.intersection(match["odds"].keys())
    combine_dict = {}
    combine_dict["date"] = max([match["date"] for match in matches])
    combine_dict["odds"] = {}
    for site in sites:
        if freebet:
            combine_dict["odds"][site] = cotes_freebet(cotes_combine([match["odds"][site] for match in matches]))
        else:
            combine_dict["odds"][site] = cotes_combine([match["odds"][site] for match in matches])
    return combine_dict


def afficher_mises_combine(matches, sites, mises, cotes, sport="football",
                           rang_freebet=None, uniquement_freebet=False,
                           cotes_boostees=None):
    opponents = []
    is1N2 = sport not in ["tennis", "volleyball", "basketball", "nba"]
    for match in matches:
        opponents_match = match.split(" - ")
        if is1N2:
            opponents_match.insert(1, "Nul")
        opponents.append(opponents_match)
#     pprint(list(product(*opponents)))
    dict_mises = {}
    dict_combinaison = {}
    print("\nRépartition des mises (les totaux affichés prennent en compte les "
          "éventuels freebets):")
    for i, combinaison in enumerate(product(*opponents)):
        sites_bet_combinaison = {}
        for j, list_sites in enumerate(sites):
            if list_sites[i] in sites_bet_combinaison:
                if rang_freebet == i or uniquement_freebet:
                    sites_bet_combinaison[list_sites[i]]["mise freebet"] += mises[j][i]
                else:
                    sites_bet_combinaison[list_sites[i]]["mise"] += mises[j][i]
            else:
                sites_bet_combinaison[list_sites[i]] = {}
                if rang_freebet == i or uniquement_freebet:
                    sites_bet_combinaison[list_sites[i]]["mise freebet"] = mises[j][i]
                    sites_bet_combinaison[list_sites[i]]["cote"] = cotes[list_sites[i]][i]+1
                else:
                    sites_bet_combinaison[list_sites[i]]["mise"] = mises[j][i]
                    sites_bet_combinaison[list_sites[i]]["cote"] = cotes[list_sites[i]][i]
        for site in sites_bet_combinaison:
            try:
                sites_bet_combinaison[site]["mise"] = round(sites_bet_combinaison[site]["mise"], 2)
            except KeyError:
                sites_bet_combinaison[site]["mise freebet"] = round(sites_bet_combinaison[site]["mise freebet"], 2)
        if cotes_boostees and cotes_boostees[i]>cotes[list_sites[i]][i]:
            sites_bet_combinaison["total boosté"] = round(cotes_boostees[i]*sites_bet_combinaison[list_sites[i]]["mise"],2)
        else:
            try:
                sites_bet_combinaison["total"] = round(sum(x["cote"]*x["mise"] for x in sites_bet_combinaison.values()), 2)
            except KeyError:
                sites_bet_combinaison["total"] = round(sum((x["cote"]-1)*x["mise freebet"] for x in sites_bet_combinaison.values()), 2)
        dict_combinaison[combinaison] = sites_bet_combinaison
        print(" / ".join(combinaison)+"\t", sites_bet_combinaison)
