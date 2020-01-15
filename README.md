
# Sports-betting
Sports betting assistant which optimizes earnings regarding odds and offers

(English version below)

Assistant de pari sportifs avec optimisation des gains en fonction des cotes et des promotions

## Installation
- Téléchargez ou clonez le dépôt
- Allez à la racine du projet
- Exécutez la commande
```
pip install -r requirements.txt
```
- Lancez python3
```
>>> import sportsbetting
>>> from sportsbetting.user_functions import *
```
- Vous pouvrez alors utiliser toutes les fonctions disponibles dans le fichier `user_functions.py`

## Initialisation
Avant de pouvoir pleinement utiliser toutes les fonctions du fichier `user_functions.py`, il est nécessaire d'initialiser la base de matches sur lesquels on peut potentiellement parier. Par exemple, si l'on veut uniquement se concentrer sur les matches de Ligue 1 Française, et que l'on veut seulement parier sur Betclic et Winamax, on écrira :
```
>>> parse_competition("ligue 1 france", "football", "betclic", "winamax")
```
On notera que si vous ne précisez pas de bookmaker, l'algorithme récupèrera les cotes des matches de la compétition sur tous les bookmakers agréés par l'ARJEL.
Si vous n'avez pas de compétition ou de sport cible, il est conseillé d'appeler
```
>>> parse_football()
```
ou, par exemple,
```
>>> parse_football("betclic", "winamax")
```
Ces fonctions vont récupérer les cotes des matches disponibles chez les différents bookmakers pour les 5 grands championnats européens de football (Ligue 1, Premier League, LaLiga, Serie A, Bundesliga), car ce sont ces compétitions qui, généralement, générent le plus de rendement.
On précisera que dans le cas du tennis où il n'y a pas de compétition fixe, il faut appeler la fonction:
```
>>> parse_tennis()
```
ou, par exemple,
```
>>> parse_tennis("betclic", "winamax")
```
Cette commande aura pour effet de récupérer les cotes de matches de tennis des compétitions actuellement disputées.




## Exemples d'utilisation:

Les bonus reçus sont quasi systématiquement des freebets (ou paris gratuits). Un tel bonus signifie que lorsque l'on mise, par exemple, sur une cote à 3 avec un freebet de 10€, si le pari s'avère gagnant, alors on récupère 3×10-10 = 20€ (contre 30€ pour un pari standard), cela équivaut donc à miser avec un pari normal sur une cote réduite de 1.
On verra plus tard qu'il est possible de récupérer de manière certaine, 80% de la valeur d'un freebet. Ainsi, un freebet de 10€ équivaut à 10 × 0.8 = 8€.

Les exemples ci-dessous sont des exemples de promotions qui reviennent régulièrement chez les différents bookmakers. Vous y trouverez une description de comment exploiter au mieux ces promotions. Bien-sûr, cette liste n'est pas exhaustive et il vous appartient d'adapter ces exemples aux conditions des promotions que vous rencontrerez à l'avenir.
### Exemple 1 : Bonus reçu dans tous les cas si l'on mise sur un match donné
France-pari propose très souvent une promotion qui consiste à miser un pari de 20€ sur un match précis de Ligue 1 à une cote minimale de 2 pour recevoir un freebet de 5€.
Par exemple, pour la 20e journée de Ligue 1 2019/2020, le match proposé était Dijon - Metz.
Il suffit alors d'exécuter:
```
>>> parse_competition("ligue 1", "football") #Si non exécuté précédemment
>>> best_stakes_match("Dijon - Metz", "france_pari", 20, 2, "football")
```
Si la plus-value minimum est supérieure à 5 × 0.8 = 4€, alors cette promotion est rentable et on peut répartir nos mises telles qu'elles sont décrites.


### Exemple 2 : Bonus reçu dans tous les cas si l'on mise sur un match quelconque, éventuellement d'une compétition donnée / d'un sport donné
S'il n'y a aucune condition sur le match à jouer, on peut éxécuter
```
>>> parse_football()
```
car, comme dit plus haut, ce sont ces matches qui vont générer le plus de rendement.

Si on doit miser sur un match de NBA, on peut exécuter
```
>>> parse_competition("nba", "basketball")
```

Si on doit miser sur un match de tennis, on peut exécuter
```
>>> parse_tennis()
```

On notera par ailleurs qu'il n'est en général pas possible de récupérer les cotes de tous les matches d'un sport donné, car cela peu être très couteux en temps d'exécution. Il faut donc choisir la ou les compétition(s) la (les) plus populaire(s) pour le sport choisi, car ce sont ces matches qui génèreront le plus de rendement.
Le tableau ci-dessous indique quelle fonction appeler pour chaque sport.



| Sport  | Fonction à appeler |
| ------------- | ------------- |
| Football  | `parse_football()`  |
| Basketball  | `parse_nba()` (raccourci de `parse_competition("nba", "basketball")`)|
| Tennis  | `parse_tennis()`  |
| Rugby  | `parse_competitions(["top 14", "champions cup", "six nations"], "rugby")`  |
| Hockey sur glace  | `parse_nhl()`  (raccourci de `parse_competition("nhl", "hockey-sur-glace")`)  |

Une fois votre ensemble de matches choisi, on peut alors utiliser la fonction `best_match_under_conditions`

Par exemple, France-pari propose régulièrement une promotion qui consiste à rembourser, en freebet, 10% des mises engagées sur des cotes supérieures à 1,70 et dans une limite de 100€ remboursés. L'objectif est alors de miser 1000€ afin de récupérer le bonus maximal. Ainsi, si l'on suppose que la promotion se déroule entre le 3 janvier 2020 à minuit et le 12 janvier 2020 à 23h59, on peut exécuter :
```
best_match_under_conditions("france_pari", 1.7, 1000, "football", "3/1/2020", "0h00", "12/1/2020", "23h59")
```
Si la perte affichée est inférieure à 100 × 0.8 = 80€, alors cette promotion est rentable et on peut répartir nos mises telles qu'elles sont décrites.

### Exemple 3 : Bonus reçu si au moins *n* matches gagnés
*Nota Bene: À partir de cet exemple, on supposera que l'on a préalablement appelé une fonction d'initialisation des matches voulus (du type* `parse_...`*), en fonction des besoins de la promotion.*

Parfois, il est nécessaire de gagner un certain nombre de paris pour recevoir un bonus. Dans ces cas-là, il faut miser sur le même bookmaker sur chacune des issues d'un même match. Betclic propose par exemple parfois de recevoir 10€ de freebet pour 3 paris gagnés, de 5€ chacun, misés sur des cotes d'au moins 1.7 et placés sur 3 matches différents. On peut alors exécuter
```
best_match_pari_gagnant("betclic", 1.7, 5, "tennis")
```
Cette fonction donnera le meilleur match sur lequel parier à un instant donné. Si la perte affichée est inférieure à (10 × 0.8)/3, alors on peut supposer que cette promotion est rentable et on peut répartir nos mises telles qu'elles sont décrites. Cela constituera le premier pari gagnant. Un peu plus tard (par exemple lorsque le match en question a été joué), on peut réitérer ce procédé afin de savoir sur quel match doit on jouer pour gagner le 2ème pari de la série et ainsi de suite jusqu'à atteindre 3 paris gagnants. À noter, que dans ce cas précis, il est nécessaire de ré-exécuter la fonction `parse_tennis()` une fois qu'on a gagné un pari, car dans le cas contraire, le résultat renvoyé par la fonction `best_match_pari_gagnant` serait identique au résultat de l'exécution précédente.

### Exemple 4 : Bonus reçu si un pari est perdant.
Il s'agit d'un type de promotion très courant, notamment en ce qui concerne les offres de bienvenue, mais pas seulement.
Par exemple, à l'été 2018, Winamax proposait à ses utilisateurs de rembourser en cash (donc pas en freebet) 100% leur premier pari de 200€ maximum si celui-ci est perdant. On notera par ailleurs que sur Winamax (comme sur la plupart des autres bookmakers), on ne peut parier que sur des cotes supérieures (ou égales) à 1.10. On peut alors exécuter
```
best_match_cashback("winamax", 1.1, 200, "football", freebet=False)
```

### Conversion des freebets en cash
#### Méthode 1 : Si l'on n'a que des freebets fractionnables
Chez les bookmakers suivant : Betclic, Unibet, ParionsSport et Zebet, il est possible de fractionner les freebets gagnés en plusieurs paris. Par exemple, si l'on a gagné 10€ de freebets, il est possible de miser 8€ puis 2€.
Pour optimiser le gain, l'idée va alors être de couvrir toutes les issues avec des freebets sur un combiné de 2 matches de football (ce qui représente donc 9 issues à couvrir).
Par exemple, si on dispose de 10€ de freebet, on va alors exécuter
```
best_matches_freebet_one_site("betclic", 10)
```

#### Méthode 2: Si l'on a quelques freebets non fractionnables et suffisamment de freebets fractionnables
Chez tous les bookmakers sauf Betclic, Unibet, ParionsSport et Zebet, il n'est pas possible de séparer un freebet en plusieurs paris. 
Supposons que l'on dispose de 100€ de freebets fractionnables sur Betclic, 1 freebet de 10€ sur Winamax et 2 freebets de 5€ sur France-pari. 
L'idée serait alors de répartir nos 100€ de freebets fractionnables sur un combiné de 2 matches comme dans la méthode 1, puis de remplacer (totalement ou en partie) certaines mises par des freebets non fractionnables des autres bookmakers. De cette manière on répartit les freebets non fractionnables sur plusieurs issues d'un combiné et on comble les différences avec des freebets fractionnables. On aura donc vraisemblablement des issues couvertes uniquement par un freebet non fractionnable, d'autres couvertes en partie par un freebet non fractionnable et un freebet fractionnable, et d'autres couvertes uniquement en freebet fractionnable. Dans cet exemple, on exécute alors
```
best_matches_freebet(["betclic"], [[10, "winamax"], [5, "france_pari"], [5, "france_pari"]])
```
Cette deuxième méthode doit, lorsqu'elle est possible, être celle à privilégier lorsque l'on dispose de freebets non fractionnables car c'est elle qui offre le meilleur rendement. La première méthode est elle aussi très rentable mais il est préférable de conserver les freebets fractionnables pour justement appliquer la 2e méthode lorsque l'on disposera de freebets non fractionnables.


#### Méthode 3 : Si l'on dispose de freebets non fractionnables et pas assez de freebets fractionnables
Par ailleurs, chez tous les bookmakers sauf Betclic, Unibet et Zebet, les freebets ont une date limite d'utilisation, allant de 2-3 jours pour Bwin, à 1 mois pour France-pari. Il peut donc être nécessaire de les jouer rapidement et il se peut également que l'on n'ait pas assez de freebets fractionnables pour pouvoir appliquer la 2e méthode. Dans cette situation, il est plus efficace de parier sur un unique match plutôt que sur un combiné. Il est également nécessaire de couvrir un pari en freebet avec de l'argent réel. De plus, avec cette méthode, on ne peut jouer qu'un freebet à la fois. Ainsi si l'on dispose d'un freebet de 15€ chez Betstars, on exécute alors
```
best_match_freebet("betstars", 15, "football")
```
*Nota-Bene: Ne pas confondre* `best_match_freebet` *de* `best_matches_freebet`.
On notera par ailleurs que certains sites comme NetBet ou PMU proposent parfois des freebets qui ne sont jouables que sur un unique sport. Auquel cas, il faut adapter le sport à la situation.
Cette méthode est en moyenne beaucoup moins rentable et beaucoup plus volatile que les deux précédentes. Les deux premières méthodes assurent un taux de revient situé entre 80 et 85% de la somme de freebets engagés. Avec la 3ème méthode, il faut s'attendre à un taux de revient situé entre 55 et 70%.


### *English version*
## Installation
- Download the repository
- Go to the root of the repository
```
pip install -r requirements.txt
```
- Launch python3
```
>>> import sportsbetting
>>> from sportsbetting.user_functions import *
```
- You can now use any function from `user_functions.py`



## Initialization
Before you can fully use all the functions in the `user_functions.py` file, it is necessary to initialize the database of matches you can potentially bet on. For example, if you only want to focus on French Ligue 1 matches, and you only want to bet on Betclic and Winamax, you would write :
```
>>> parse_competition("ligue 1 france", "football", "betclic", "winamax")
```
Note that if you do not specify a bookmaker, the algorithm will retrieve the odds of the matches of the competition from all bookmakers approved by the ARJEL.
If you do not have a specific competition or target sport, it is advisable to call
```
>>> parse_football()
```
or, for example,
```
>>> parse_football("betclic", "winamax")
```
These functions will retrieve the odds of the matches available at the various bookmakers for the 5 major European football championships (Ligue 1, Premier League, LaLiga, Serie A, Bundesliga), as these competitions generally generate the highest returns.
It should be pointed out that in the case of tennis where there is no fixed competition, it is necessary to call the function:
```
>>> parse_tennis()
```
or, for example,
```
>>> parse_tennis("betclic", "winamax")
```
This command will retrieve the odds of tennis matches from the competitions currently being played.




## Examples of use:

The bonuses received are almost always freebets (or paris gratuits). Such a bonus means that when you bet, for example, on an odds equals to 3 with a €10 freebet, if the bet turns out to be winning, then you get 3×10-10 = €20 (compared to €30 for a standard bet), so it is equivalent to betting with a normal bet on an odds reduced by 1.
We will see later that it is possible to win back 80% of the value of a freebet with certainty. Thus, a €10 freebet is equivalent to 10 × 0.8 = €8.

The examples below are examples of promotions that regularly appear at the different bookmakers. You will find a description of how to get the most out of these promotions. This list is naturally not exhaustive and it is up to you to adapt these examples to the conditions of the promotions you will encounter in the future.
### Example 1: Bonus received in all cases if you bet on a given match
France-pari very often offers a promotion which consists in betting a €20 bet on a specific Ligue 1 match at a minimum odds of 2 to receive a €5 freebet.
For example, for the 20th round of Ligue 1 2019/2020, the proposed match was Dijon - Metz.
You just have to execute:
```
>>> parse_competition("ligue 1", "football") #If not previously executed
>>> best_stakes_match("Dijon - Metz", "france_pari", 20, 2, "football")
```
If the minimum raise is more than 5 × 0.8 = €4, then this promotion is profitable and we can split our bets as specified.


### Example 2: Bonus received in all cases if you bet on any match, possibly from a given competition / sport
If there are no conditions on the game to be played, we can execute
```
>>> parse_football()
```
because, as mentioned above, it is these matches that will generate the most returns.

If we're betting on an NBA game, we can execute...
```
>>> parse_competition("nba", "basketball")
```

If we're going to bet on a tennis match, we can execute
```
>>> parse_tennis()
```

It should also be noted that it is generally not possible to retrieve the odds of all the matches of a given sport, as this can be very costly in terms of execution time. It is therefore necessary to choose the most popular competition(s) for the chosen sport, as it is these matches that will generate the most returns.
The table below indicates which function to call for each sport.



| Sport | Function to call |
| ------------- | ------------- |
| Football | `parse_football()` |
| Basketball | `parse_nba()` (short for `parse_competition("nba", "basketball")`)|
| Tennis | `parse_tennis()` |
| Rugby | `parse_competitions(("top 14", "champions cup", "six nations"), "rugby")` |
| Ice Hockey | `parse_nhl()` (short for `parse_competition("nhl", "ice hockey")`) |

Once you have chosen your set of matches, you can then use the `best_match_under_conditions` function.

For example, France-pari regularly offers a promotion which consists in reimbursing, in freebet, 10% of the stakes engaged on odds higher than 1.70 and within a limit of €100 reimbursed. The objective is then to bet €1000 in order to recover the maximum bonus. Thus, if we assume that the promotion takes place between January 3, 2020 at midnight and January 12, 2020 at 11:59 pm, we can execute :
```
best_match_under_conditions("france_pari", 1.7, 1000, "football", "3/1/2020", "0h00", "12/1/2020", "23h59")
```
If the displayed loss is less than 100 × 0.8 = €80, then this promotion is profitable and we can distribute our stakes as described.

### Example 3: Bonus received if at least *n* matches are won
*Note Bene: From this example, we'll assume that we previously called a function to initialize the desired matches (of the type* `parse_...`*), according to the needs of the promotion.*

Sometimes it is necessary to win a certain number of bets to receive a bonus. In these cases, it is necessary to bet on the same bookmaker on each of the outcomes of the same match. For example, Betclic sometimes offers to receive a €10 freebet for 3 bets won, of €5 each, bet on odds of at least 1.7 and placed on 3 different matches. You can then execute
```
best_match_winning_between("betclic", 1.7, 5, "tennis")
```
This feature will give you the best match to bet on at any given time. If the displayed loss is less than (10 × 0.8)/3, then we can assume that this promotion is profitable and we can distribute our stakes as described. This will be the first winning bet. A little later (e.g. when the match in question has been played), we can repeat this procedure to find out which match we need to play to win the 2nd bet in the series and so on until we reach 3 winning bets. Note that in this case, it is necessary to re-execute the `parse_tennis()` function once you have won a bet, because otherwise the result returned by the `best_match_winning bet` function would be identical to the result of the previous execution.

### Example 4: Bonus received if a bet is lost.
This is a very common type of promotion, especially but not only for welcome offers.
For example, in the summer of 2018, Winamax offered its users to pay back in cash (not freebet) 100% of their first bet of €200 maximum if they lost. It should also be noted that on Winamax (as on most other bookmakers), you can only bet on odds greater than (or equal to) 1.10. You can then run
```
best_match_cashback("winamax", 1.1, 200, "football", freebet=False)
```

### Converting freebets to cash
#### Method 1: If you only have fractionable freebets
At the following bookmakers: Betclic, Unibet, ParionsSport and Zebet, it is possible to split the won freebets into several bets. For example, if you have won €10 in freebets, you can bet €8 and then €2.
To optimize the win, the idea will be to cover all the outcomes with freebets on a combination of 2 football matches (which represents 9 outcomes to cover).
For example, if you have €10 of freebet, you will then run
```
best_matches_freebet_one_site("betclic", 10)
```

#### Method 2: If you have a few non-fractionable freebets and enough fractionable freebets
At all bookmakers except Betclic, Unibet, ParionsSport and Zebet, it is not possible to split a freebet into several bets. 
Let's suppose that you have €100 fractionable freebets on Betclic, 1 freebet of €10 on Winamax and 2 freebets of €5 on France-pari. 
The idea would then be to spread our €100 of fractionable freebets over a combination of 2 games as in method 1, then replace (totally or partially) some stakes with non-fractionable freebets from other bookmakers. In this way we spread the non-fractionable freebets over several outcomes of a handset and compensate the differences with fractionable freebets. So you are likely to have some outcomes covered only by a non-fractionable freebet, others covered partly by a non-fractionable freebet and a fractionable freebet, and others covered only by a fractionable freebet. In this example, we then execute
```
best_matches_freebet(["betclic"], [[10, "winamax"], [5, "france_pari"], [5, "france_pari"])
```
This second method should, where possible, be the preferred method when non-fractionable freebets are available, as it offers the best return. The first method is also very profitable but it is preferable to keep the fractionable freebets in order to apply the second method when you have non-fractionable freebets.

#### Method 3: If you have non-fractionable freebets and not enough fractionable freebets
At all bookmakers except Betclic, Unibet and Zebet, freebets have a time limit, ranging from 2-3 days for Bwin, to 1 month for France-pari. It may therefore be necessary to bet them quickly and there may not be enough fractionable freebets to be able to apply the 2nd method. In this situation, it is more efficient to bet on a single match rather than on a combination. It is also necessary to cover a freebet with real money. Furthermore, with this method, you can only play one freebet at a time. So if you have a €15 freebet at Betstars, then you can execute
```
best_match_freebet("betstars", 15, "football")
```
*Nota-Bene: Be careful not to confuse* `best_match_freebet` *with* `best_matches_freebet`.
Note that some sites like NetBet or PMU sometimes offer freebets that are only playable on a single sport. In this case, you have to adapt the sport to the situation.
This method is on average much less profitable and much more volatile than the first two. The first two methods ensure a return rate of between 80 and 85% of the sum of freebets placed.  With the third method, a return rate between 55 and 70% is to be expected.
