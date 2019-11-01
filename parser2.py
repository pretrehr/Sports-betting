def parse_competition(competition, sport, *sites_not_to_parse):
    sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'netbet', 'parionssport', 'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']
    for site in sites_not_to_parse:
        sites.remove(site)
    res_parsing = {}
    for site in sites:
        print(site)
        try:
            exec("res_parsing['{}'] = parse_{}('{}')".format(site, site, find_competition(competition, sport, site)))
        except urllib.error.URLError:
            print("Site non accessible (délai écoulé)")
    res = adapt_names_to_all(res_parsing, sport)
    return merge_dict_odds(res)

def parse_main_competitions():
    competitions = ["france ligue 1", "angleterre premier league", "espagne liga", "italie serie", "allemagne bundesliga"]
    list_odds = []
    for competition in competitions:
        print("\n"+competition.title())
        list_odds.append(parse_competition(competition, "football"))
    return merge_dicts(list_odds)

def add_names_to_db_all_sites(competition, sport, *sites_not_to_parse):
    id = find_competition_id(competition, sport)
    import_teams_in_db("http://www.comparateur-de-cotes.fr/comparateur/"+sport+"/a-ed"+str(id))
    sites = ['betclic', 'betstars', 'bwin', 'netbet', 'parionssport', 'pasinobet', 'pmu', 'unibet', 'winamax']
    for site in sites_not_to_parse:
        sites.remove(site)
    for site in sites:
        print(site)
        add_names_to_db_complete(site, sport, find_competition(competition, sport, site))
    