all_odds = []
odds = []
soup = BeautifulSoup(open("/home/raphael/Documents/vendredi13").read(), "html.parser")
strings = list(soup.stripped_strings)
for i, el in enumerate(strings):
    if "," in el:
        try:
            odds.append(float(el.replace(",", ".")))
            continue
        except ValueError:
            pass
    print(odds)
    if odds:
        if all(odd>=1.7 for odd in odds):
            all_odds.append((strings[i-len(odds)-1], odds, mises2(odds, 5, np.argmax(odds))))
        odds = []
all_odds.sort(key=lambda x: gain2(x[1], np.argmax(x[1])))

