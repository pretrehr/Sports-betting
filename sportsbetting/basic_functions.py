#!/usr/bin/env python3
"""
Assistant de paris sportifs
"""

import copy
from itertools import product, combinations, permutations
import numpy as np


def gain(cotes, mise=1):
    """
    :param cotes: Cotes au format décimal
    :type cotes: list[float]
    :param mise: Mise à répartir sur toutes les cotes
    :type mise: float
    :return: Gain pour une somme des mises égale à mise
    :rtype: int
    """
    return mise / sum(map(lambda x: 1 / x, cotes))


def gain2(cotes, i, mise=1):
    """
    :param cotes: Cotes au format décimal
    :type cotes: list[float]
    :param i: Indice de la cote sur laquelle miser
    :type i: int
    :param mise: Mise à placer sur une unique issue
    :type mise: float
    :return: Plus-value générée
    :rtype: float
    """
    return cotes[i] * mise - sum(mises2(cotes, mise, i))


def mises(cotes, mise=1, output=False, freebet_display=False):
    """
    :param cotes: Cotes au format décimal
    :type cotes: list[float]
    :param mise: Mise à répartir sur toutes les cotes
    :param output: Affichage des détails
    :type output: bool
    :return: Répartition optimale des mises
    :rtype: list[float] or None
    """
    gains = gain(cotes, mise)
    mises_reelles = list(map(lambda x: gains / x, cotes))
    if output:
        mis = list(map(lambda x: round(x, 2), mises_reelles))
        if freebet_display:
            print("gain sur freebet =", round(gains + mise - sum(mis), 2))
            print("gain sur freebet / mise freebet =", round(gains + mise - sum(mis), 2) / mise)
            print("gain =", round(gains, 2))
            print("mise totale =", round(sum(mis), 2))
            print("mises arrondies =", mis)
            return
        print("taux de retour au joueur =", round(gain(cotes)*100, 3), "%")
        print("somme des mises =", round(sum(mis), 2))
        print("gain min =", min([round(mis[i] * cotes[i], 2)
                                 for i in range(len(mis))]))
        print("gain max =", max([round(mis[i] * cotes[i], 2)
                                 for i in range(len(mis))]))
        print("plus-value max =",
              round(min([round(mis[i] * cotes[i], 2)
                         for i in range(len(mis))]) - sum(mis), 2))
        print("mises arrondies =", mis)
        return
    return mises_reelles


def mises2(cotes, mise_requise, choix=-1, output=False, bonus_miles=0):
    """
    Calcule la repartition des mises en pariant mise_requise sur l'une des
    issues. Par défaut, mise_requise est placée sur la cote la plus basse.

    :param cotes: Cotes au format décimal
    :type cotes: list[float]
    :param mise_requise: Mise à répartir sur toutes les cotes
    :type mise_requise: float
    :param choix: Indice de la cote sur laquelle miser
    :type choix: int
    :param output: Affichage des détails
    :type output: bool
    :return: Répartition optimale des mises
    :rtype: list[float] or None
    """
    if not cotes:
        if output:
            return
        return []
    if choix == -1:
        choix = np.argmin(cotes)
    gains = mise_requise * cotes[choix]
    mises_reelles = list(map(lambda x: gains / x, cotes))
    if output:
        mis = list(map(lambda x: round(x, 2), mises_reelles))
        print("taux de retour au joueur =", round(gain(cotes)*100, 3), "%")
        print("somme des mises =", round(sum(mis), 2))
        print("gain min =", min([round(mis[i] * cotes[i]+bonus_miles, 2)
                                 for i in range(len(mis))]))
        print("gain max =", max([round(mis[i] * cotes[i]+bonus_miles, 2)
                                 for i in range(len(mis))]))
        print("plus-value min =",
              round(min([round(mis[i] * cotes[i], 2)
                         for i in range(len(mis))]) - sum(mis)+bonus_miles, 2))
        print("plus-value max =",
              round(max([round(mis[i] * cotes[i], 2)
                         for i in range(len(mis))]) - sum(mis)+bonus_miles, 2))
        print("mises arrondies =", mis)
        return
    return mises_reelles


def mises3(odds, best_odds, stake, minimum_odd, output=False, miles=False, rate_eur_miles=0, multiplicator=1):
    """
    Répartition optimale d'une certaine somme sur les différentes cotes en prenant en compte les cotes des autres
    bookmakers
    """
    assert len(odds) == len(best_odds)
    n = len(odds)
    indices_valid_odds = [i for i in range(n) if odds[i] >= minimum_odd]
    n_valid_odds = len(indices_valid_odds)
    profit = -stake
    odds_best_profit = []
    best_combination = []
    reference_stake = []
    best_stakes = []
    nb_miles = 0
    for i in range(n_valid_odds):
        for combination in combinations(indices_valid_odds, i+1):
            odds_to_check = []
            for j in range(n):
                odd = odds[j] if j in combination else best_odds[j]
                odds_to_check.append(odd)
            odds_site = [odds[k] for k in combination]
            first_stake_site = mises(odds_site, stake)[0]
            profit_combination = gain2(odds_to_check, combination[0], first_stake_site)
            stakes = mises2(odds_to_check, first_stake_site, combination[0])
            if miles:
                profit_combination += rate_eur_miles * sum(stakes[outcome]*0.4*(1-1/odds[outcome]) for outcome in combination)
            if profit_combination > profit:
                reference_stake = first_stake_site
                best_stakes = stakes
                odds_best_profit = copy.deepcopy(odds_to_check)
                best_combination = copy.deepcopy(combination)
                profit = profit_combination
    if miles:
        nb_miles = round(sum(best_stakes[outcome]*0.4*(1-1/odds[outcome]) for outcome in best_combination)*multiplicator, 2)
    if output:
        if miles:
            print("miles =", nb_miles)
            print("miles convertis =", round(nb_miles*rate_eur_miles, 2))
        mises2(odds_best_profit, reference_stake, best_combination[0], True, round(nb_miles*rate_eur_miles, 2))
        print("cotes =", odds_best_profit)
        return
    if best_combination:
        return mises2(odds_best_profit, reference_stake, best_combination[0], False, round(nb_miles*rate_eur_miles, 2)), best_combination
    return


def gain3(odds, best_odds, stake, minimum_odd, miles=False, rate_eur_miles=0, multiplicator=1):
    """
    Profit avec répartition optimale d'une certaine somme sur les différentes cotes en prenant en compte les cotes des autres
    bookmakers
    """
    assert len(odds) == len(best_odds)
    n = len(odds)
    indices_valid_odds = [i for i in range(n) if odds[i] >= minimum_odd]
    n_valid_odds = len(indices_valid_odds)
    profit = -float("inf")
    best_combination = []
    for i in range(n_valid_odds):
        for combination in combinations(indices_valid_odds, i+1):
            odds_to_check = []
            for j in range(n):
                odd = odds[j] if j in combination else best_odds[j]
                odds_to_check.append(odd)
            odds_site = [odds[k] for k in combination]
            first_stake_site = mises(odds_site, stake)[0]
            profit_combination = gain2(odds_to_check, combination[0], first_stake_site)
            stakes = mises2(odds_to_check, first_stake_site, combination[0])
            if miles:
                profit_combination += rate_eur_miles * sum(stakes[outcome]*0.4*(1-1/odds[outcome]) for outcome in combination) * multiplicator
            if profit_combination > profit:
                profit = profit_combination
    return profit


def equivalent_middle_odd(odds):
    risque = 1-gain(odds)
    gain_brut = gain(odds)
    return gain_brut/risque

def mises_defi_rembourse_ou_gagnant(odds, stake, winning_outcome, output=False):
    stakes = []
    for i, odd in enumerate(odds):
        if i == winning_outcome:
            stakes.append(stake)
            continue
        parameter = sum([1/x for j, x in enumerate(odds) if j not in [i, winning_outcome]])
        stakes.append(stake/(odd*(1-parameter)-1))
    if output:
        rounded_stakes = list(map(lambda x: round(x, 2), stakes))
        print("taux de retour au joueur =", round(gain(odds)*100, 3), "%")
        print("gain min =", min([round(rounded_stakes[i] * odds[i], 2)
                                 for i in range(len(odds))]))
        print("gain max =", max([round(rounded_stakes[i] * odds[i], 2)
                                 for i in range(len(odds))]))
        print("plus-value min =",
              round(min([round(rounded_stakes[i] * odds[i], 2)
                         for i in range(len(odds))]) - sum(rounded_stakes), 2))
        print("plus-value max =",
              round(max([round(rounded_stakes[i] * odds[i], 2)
                         for i in range(len(odds))]) - sum(rounded_stakes), 2))
        print("mises arrondies =", rounded_stakes)
        return
    return stakes


def gain_defi_rembourse_ou_gagnant(odds, stake, winning_outcome):
    stakes = []
    for i, odd in enumerate(odds):
        if i == winning_outcome:
            stakes.append(stake)
            continue
        parameter = sum([1/x for j, x in enumerate(odds) if j not in [i, winning_outcome]])
        stake_i = stake/(odd*(1-parameter)-1)
        if stake_i < 0:
            return float("-inf")
        stakes.append(stake_i)
    return stake * odds[winning_outcome] - sum(stakes)


def cotes_freebet(cotes):
    """
    Calcule les cotes d'un match joué avec des paris gratuits

    :param cotes: Cotes au format décimal
    :type cotes: list[float]
    :return: Cotes réduites de 1
    :rtype: list[float]
    """
    return list(map(lambda x: (x - 1 if x > 1 else 0.01), cotes))


def mises_freebets(cotes, mise):
    """
    Calcule la repartition des mises en paris gratuits pour maximiser les gains
    avec une mise totale égale à mise
    :param cotes:
    :type cotes:
    :param mise:
    :type mise:
    :return:
    :rtype:

    """
    return mises(cotes_freebet(cotes), mise)


def mises_freebet(cotes, freebet, issue=-1, output=False):
    """
    Calcule la repartition des mises en presence d'un freebet a placer sur l'une
    des issues. Par defaut, le freebet est place sur la cote la plus haute.
    """
    if issue == -1:
        issue = np.argmax(cotes)
    mises_reelles = mises2(cotes[:issue] + [cotes[issue] - 1] + cotes[issue + 1:], freebet, issue)
    gains = mises_reelles[issue] * (cotes[issue] - 1)
    if output:
        mis = list(map(lambda x: round(x, 2), mises_reelles))
        conversion_rate = round(gains + freebet - sum(mis), 2) / freebet if gain(cotes) < 1 else (cotes[issue] - 1)/cotes[issue]
        print("gain sur freebet =", round(gains + freebet - sum(mis), 2))
        print("taux de conversion =", round(conversion_rate * 100, 3), "%")
        print("gain =", round(gains, 2))
        print("mise totale (hors freebet) =", round(sum(mis) - freebet, 2))
        print("mises arrondies =", mis)
        return
    return mises_reelles


def mises_freebet2(cotes, freebet, issue=-1, output=False):
    """
    Calcule la repartition des mises en presence de 2 freebets a placer sur des issues d'un même
    match. Le 2e freebet est placé automatiquement.
    """
    i_max = np.argmax(cotes)
    if issue == -1:
        issue = i_max
    mises_reelles = mises2(cotes[:issue] + [cotes[issue] - 1] + cotes[issue + 1:], freebet, issue)
    gains = mises_reelles[issue] * (cotes[issue] - 1)
    issue2 = int(np.argmax(cotes[:i_max] + [0] + cotes[i_max + 1:]) if issue == i_max else i_max)
    mis = list(map(lambda x: round(x, 2), mises_reelles))
    rapport_gain = (gains + freebet - sum(mis)) / freebet
    if rapport_gain < (cotes[issue2] - 1) / cotes[issue2]:
        mises_reelles[issue2] = round(gains / (cotes[issue2] - 1), 2)
        mis = list(map(lambda x: round(x, 2), mises_reelles))
        freebet += mis[issue2]
    if output:
        print("gain sur freebet =", round(gains + freebet - sum(mis), 2))
        print("gain sur freebet / mise freebet =", round(gains + freebet - sum(mis), 2) / freebet)
        print("gain =", round(gains, 2))
        print("mise totale (hors freebet) =", round(sum(mis) - freebet, 2))
        print("mises arrondies =", mis)
        return issue2
    return mises_reelles


def gain_freebet2(cotes, freebet, issue=-1):
    """
    Calcule le taux de gain si l'on place deux freebets sur un match même match.
    """
    i_max = np.argmax(cotes)
    if issue == -1:
        issue = i_max
    mises_reelles = mises2(cotes[:issue] + [cotes[issue] - 1] + cotes[issue + 1:], freebet, issue)
    gains = mises_reelles[issue] * (cotes[issue] - 1)
    issue2 = int(np.argmax(cotes[:i_max] + cotes[i_max + 1:]) if issue == i_max else i_max)
    mis = list(map(lambda x: round(x, 2), mises_reelles))
    rapport_gain = (gains + freebet - sum(mis)) / freebet
    if rapport_gain < (cotes[issue2] - 1) / cotes[issue2]:
        mis[issue2] = round(gains / (cotes[issue2] - 1), 2)
        freebet += mis[issue2]
    return (gains + freebet - sum(mis)) / freebet


def cotes_combine(cotes):
    """
    Calcule les cotes de plusieurs matches combines
    """
    return [round(np.prod(i), 4) for i in product(*cotes)]


def gain_pari_rembourse_si_perdant(cotes, mise_max, rang=-1, remb_freebet=False,
                                   taux_remboursement=1):
    """
    Calcule le bénéfice lorsque l'un des paris est rembourse. Par
    defaut, la mise remboursee est placee sur la cote la plus haute et le
    remboursement est effectue en argent reel
    """
    taux = ((not remb_freebet) + 0.77 * remb_freebet) * taux_remboursement
    if rang == -1:
        rang = np.argmax(cotes)
    gains = mise_max * cotes[rang]
    mis = list(map(lambda x: (gains - mise_max * taux) / x, cotes))
    mis[rang] = mise_max
    return gains - sum(mis)


def mises_pari_rembourse_si_perdant(cotes, mise_max, rang=-1, remb_freebet=False,
                                    taux_remboursement=1, output=False):
    """
    Calcule les mises lorsque l'un des paris est rembourse. Par
    defaut, la mise remboursee est placee sur la cote la plus haute et le
    remboursement est effectue en argent reel
    """
    taux = ((not remb_freebet) + 0.77 * remb_freebet) * taux_remboursement
    if rang == -1:
        rang = np.argmax(cotes)
    gains = mise_max * cotes[rang]
    mis_reelles = list(map(lambda x: (gains - mise_max * taux) / x, cotes))
    mis_reelles[rang] = mise_max
    if output:
        mis = list(map(lambda x: round(x, 2), mis_reelles))
        print("gain net =", round(gains - sum(mis), 2))
        print("taux de retour au joueur =", round(gain(cotes)*100, 3), "%")
        print("mises arrondies =", mis)
        return
    return mis_reelles


def mises_promo_gain_cote(cotes, mise_minimale, rang, output=False):
    """
    Calcule la répartition des mises pour la promotion "gain en freebet de la cote gagnée"
    """
    mis = []
    gains = cotes[rang] * 0.77 + mise_minimale * cotes[rang]
    for cote in cotes:
        mis.append((gains / cote))
    mis[rang] = mise_minimale
    if output:
        print("somme mises=", sum(mis))
        print("gain=", gains)
    return mis


def gain_promo_gain_cote(cotes, mise_minimale, rang):
    """
    Calcule le gain pour la promotion "gain en freebet de la cote gagnée"
    """
    mis = []
    gains = cotes[rang] * 0.77 + mise_minimale * cotes[rang]
    for cote in cotes:
        mis.append((gains / cote))
    mis[rang] = mise_minimale
    return gains - sum(mis)


def cote_boostee(cote, boost_selon_cote=True, freebet=True, boost=1):
    """
    Calcul de cote boostee pour promotion Betclic
    """
    mult_freebet = 1 * (not freebet) + 0.8 * freebet
    if not boost_selon_cote:
        return cote + (cote - 1) * boost * mult_freebet
    if cote < 2:
        return cote
    if cote < 2.51:
        return cote + (cote - 1) * 0.25 * mult_freebet
    if cote < 3.51:
        return cote + (cote - 1) * 0.5 * mult_freebet
    return cote + (cote - 1) * mult_freebet


def taux_boost(cote, boost_selon_cote=True, boost=1):
    """
    Calcul du taux de boost pour promotion Betclic
    """
    if not boost_selon_cote:
        return boost
    if cote < 2:
        return 0
    if cote < 2.51:
        return 0.25
    if cote < 3.51:
        return 0.5
    return 1


def mises_gains_nets_boostes(cotes, gain_max, boost_selon_cote=True, freebet=True, boost=1, output=False):
    """
    Optimisation de gain pour promotion Betclic de type "Cotes boostees"
    """
    new_cotes = list(map(lambda x: cote_boostee(x, boost_selon_cote, freebet, boost), cotes))
    benefice_max = -float("inf")
    meilleures_mises = []
    for i, cote in enumerate(cotes):
        if not taux_boost(cote, boost_selon_cote, boost):
            continue
        mise = gain_max / ((cotes[i] - 1) * taux_boost(cote, boost_selon_cote, boost))
        mises_possibles = mises2(new_cotes, mise, i)
        mises_corrigees = []
        benefice = 0
        for j, mis in enumerate(mises_possibles):
            if mis * ((cotes[j] - 1) * taux_boost(cotes[j], boost_selon_cote, boost)) > gain_max + 0.1:
                mises_corrigees.append(mise * cote / cotes[j])
            else:
                mises_corrigees.append(mis)
                benefice = mises_corrigees[j] * new_cotes[j]
        benefice -= sum(mises_corrigees)
        if benefice > benefice_max:
            benefice_max = benefice
            meilleures_mises = mises_corrigees
    if output:
        print("somme des mises =", sum(meilleures_mises))
        print("plus-value =", round(benefice_max, 2))
    return meilleures_mises


def gain_gains_nets_boostes(cotes, gain_max, boost_selon_cote=True, freebet=True, boost=1):
    """
    Optimisation de gain pour promotion Betclic de type "Cotes boostees"
    """
    new_cotes = list(map(lambda x: cote_boostee(x, boost_selon_cote, freebet, boost), cotes))
    benefice_max = -float("inf")
    for i, cote in enumerate(cotes):
        mise = gain_max / ((cotes[i] - 1) * taux_boost(cote, boost_selon_cote, boost))
        mises_possibles = mises2(new_cotes, mise, i)
        mises_corrigees = []
        benefice = 0
        for j, mis in enumerate(mises_possibles):
            if mis * ((cotes[j] - 1) * taux_boost(cotes[j], boost_selon_cote, boost)) > gain_max + 0.1:
                mises_corrigees.append(mise * cote / cotes[j])
            else:
                mises_corrigees.append(mis)
                benefice = mises_corrigees[j] * new_cotes[j]
        benefice -= sum(mises_corrigees)
        if benefice > benefice_max:
            benefice_max = benefice
    return benefice_max


def paris_rembourses_si_perdants(cotes, remboursement_max, freebet, taux_remboursement):
    """
    Calcule les mises à placer lorsque tous les paris perdants sont remboursés
    """
    rg_max = int(np.argmax(cotes))
    n = len(cotes)
    facteur = (1 - 0.2 * freebet) * taux_remboursement
    systeme = []
    for i, cote in enumerate(cotes):
        line = [facteur for _ in range(n + 1)]
        line[-1] = -1
        line[i] = cote
        systeme.append(line)
    line = [taux_remboursement for _ in range(n + 1)]
    line[rg_max] = 0
    line[-1] = 0
    systeme.append(line)
    a = np.array(systeme)
    values = [0 for _ in range(n + 1)]
    values[-1] = remboursement_max
    b = np.array(values)
    x = np.linalg.solve(a, b)
    print("Bénéfice net:", x[-1] - sum(x[:-1]))
    print(x[:-1])


def mises_pari_rembourse_si_perdant_paliers(cotes, output=False):
    """
    Optimisation de la promotion Zebet qui attribue un unique cashback en fonction de la plus haute
    mise perdue
    """

    def aux(mise):
        if mise > 25:
            return 10
        if mise > 20:
            return 8
        if mise > 15:
            return 6
        if mise > 10:
            return 4
        if mise > 5:
            return 2
        return 0

    sorted_cotes = sorted(cotes)
    mise_max = 25.01
    gain_approx = mise_max * sorted_cotes[0]
    retour_approx = aux(gain_approx / sorted_cotes[1])
    gains = gain_approx + retour_approx * 0.8
    while aux((gains - aux(mise_max) * 0.8) / sorted_cotes[1]) != retour_approx:
        retour_approx -= 2
        gains = gain_approx + retour_approx
    mis_reelles = []
    for cote in cotes:
        mis_reelles.append((gains - aux(mise_max) * 0.8) / cote)
    mis_reelles[int(np.argmin(cotes))] = mise_max
    if output:
        mis = list(map(lambda x: round(x, 2), mis_reelles))
        print("gain net =", gains - sum(mis))
        print("mises arrondies =", mis)
        return
    return mis_reelles

def combine_reduit_rec(combi_to_keep, nb_outcomes):
    n = len(combi_to_keep)
    if n <= 1:
        return [[[i] for i in range(nb_outcomes)]]
    out = []
    for i in range(n):
        ref_combi = combi_to_keep[:i]+combi_to_keep[i+1:]
        combines_partiels = combine_reduit_rec(ref_combi, nb_outcomes)
        for list_combi in combines_partiels:
            new_combi = []
            for combi in list_combi:
                if combi != ref_combi:
                    copy_combi = copy.deepcopy(combi)
                    copy_combi.insert(i, float("inf"))
                    new_combi.append(copy_combi)
                else:
                    for j in range(nb_outcomes):
                        copy_combi = copy.deepcopy(combi)
                        copy_combi.insert(i, j)
                        new_combi.append(copy_combi)
            out.append(new_combi)
    return out


def mises_combine_optimise(odds, combination, stake, minimum_odd, output=False):
    nb_outcomes = len(odds[0])
    best_odds = []
    best_profit = float("-inf")
    best_combination = []
    for outcomes in combine_reduit_rec(combination, nb_outcomes):
        tmp_odds = []
        for i, combi in enumerate(outcomes):
            odd = 1
            if combi == combination:
                i_tmp = i
            for j, outcome in enumerate(combi):
                if outcome == float("inf"):
                    continue
                odd *= odds[j][outcome]
            if odd < minimum_odd:
                break
            tmp_odds.append(odd)
        else:
            tmp_profit = gain2(tmp_odds, i_tmp, stake)
            if tmp_profit > best_profit:
                best_odds = tmp_odds
                best_profit = tmp_profit
                best_combination = outcomes
    if not best_combination:
        return
    if output:
        mises2(best_odds, stake, best_combination.index(combination), output)
        print("combinaisons = ", best_combination)
    else:
        return mises2(best_odds, stake, best_combination.index(combination), output), best_combination


def gain_combine_optimise(odds, combination, stake, minimum_odd):
    nb_outcomes = len(odds[0])
    best_profit = float("-inf")
    for outcomes in combine_reduit_rec(combination, nb_outcomes):
        tmp_odds = []
        for i, combi in enumerate(outcomes):
            odd = 1
            if combi == combination:
                i_tmp = i
            for j, outcome in enumerate(combi):
                if outcome == float("inf"):
                    continue
                odd *= odds[j][outcome]
            if odd < minimum_odd:
                break
            tmp_odds.append(odd)
        else:
            tmp_profit = gain2(tmp_odds, i_tmp, stake)
            if tmp_profit > best_profit:
                best_profit = tmp_profit
    return best_profit

def cotes_combine_optimise(odds):
    """
    Calcule les cotes optimisees de plusieurs matches combines
    """
    nb_outcomes = len(odds[0])
    nb_matches = len(odds)
    all_odds = []
    all_outcomes = []
    for combination in permutations(range(nb_outcomes), nb_matches):
        for outcomes in combine_reduit_rec(list(combination), nb_outcomes):
            tmp_odds = []
            if outcomes in all_outcomes:
                continue
            all_outcomes.append(outcomes)
            for i, combi in enumerate(outcomes):
                odd = 1
                for j, outcome in enumerate(combi):
                    if outcome == float("inf"):
                        continue
                    odd *= odds[j][outcome]
                tmp_odds.append(round(odd, 4))
            all_odds.append(tmp_odds)
    return all_odds, all_outcomes

