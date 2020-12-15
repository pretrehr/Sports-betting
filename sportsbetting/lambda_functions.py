from sportsbetting.basic_functions import gain, gain2


def get_best_odds(one_site):
    def aux(best_odds, odds_site, i):
        if one_site:
            return odds_site
        return best_odds[:i] + [odds_site[i]] + best_odds[i + 1:]
    return aux


def get_profit(stake, one_site):
    def aux(odds_to_check, i):
        if one_site:
            return gain(odds_to_check, stake) - stake
        return gain2(odds_to_check, i, stake)
    return aux
