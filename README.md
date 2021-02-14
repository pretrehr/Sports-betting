[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

[![Build Status](https://travis-ci.org/pretrehr/Sports-betting.svg?branch=master)](https://travis-ci.org/pretrehr/Sports-betting)
[![GitHub license](https://img.shields.io/github/license/pretrehr/Sports-betting.svg)](https://github.com/pretrehr/Sports-betting/blob/master/LICENSE)
[![Requirements Status](https://requires.io/github/pretrehr/Sports-betting/requirements.svg?branch=master)](https://requires.io/github/pretrehr/Sports-betting/requirements/?branch=master)

# Sports-betting
Sports betting assistant which optimizes earnings regarding odds and offers

[(English version below)](#english-version)

Assistant de paris sportifs avec optimisation des gains en fonction des cotes et des promotions

<details>
<summary>Sommaire</summary>

* [Installation](#installation)
* [Initialisation](#initialisation)
* [Exemples d'utilisation](#exemples-dutilisation)
  * [Exemple 1 : Bonus reçu dans tous les cas si l'on mise sur un match donné](#exemple-1--bonus-reçu-dans-tous-les-cas-si-lon-mise-sur-un-match-donné)
  * [Exemple 2 : Bonus reçu dans tous les cas si l'on mise sur un match quelconque, éventuellement d'une compétition donnée / d'un sport donné](#exemple-2--bonus-reçu-dans-tous-les-cas-si-lon-mise-sur-un-match-quelconque-éventuellement-dune-compétition-donnée--dun-sport-donné)
  * [Exemple 3 : Bonus reçu si au moins *n* matches gagnés](#exemple-3--bonus-reçu-si-au-moins-n-matches-gagnés)
  * [Exemple 4 : Bonus reçu si un pari est perdant.](#exemple-4--bonus-reçu-si-un-pari-est-perdant)
* [Conversion des freebets en cash](#conversion-des-freebets-en-cash)
  * [Méthode 1 : Si l'on n'a que des freebets fractionnables](#méthode-1--si-lon-na-que-des-freebets-fractionnables)
  * [Méthode 2 : Si l'on a quelques freebets non fractionnables et suffisamment de freebets fractionnables](#méthode-2--si-lon-a-quelques-freebets-non-fractionnables-et-suffisamment-de-freebets-fractionnables)
  * [Méthode 3 : Si l'on dispose de freebets non fractionnables et pas assez de freebets fractionnables](#méthode-3--si-lon-dispose-de-freebets-non-fractionnables-et-pas-assez-de-freebets-fractionnables)

</details>

## Prérequis
- Python 3.6 ou ultérieur
- Google Chrome

## Installation
- Téléchargez ou clonez le dépôt
- Allez à la racine du projet
- Exécutez la commande
```bash
pip install -r requirements.txt
```

Si vous choisissez d'utiliser l'interface utilisateur, il suffit alors de lancer la commande
```bash
python interface_pysimplegui.py
```

Vous obtenez alors cette fenêtre :
![image](https://user-images.githubusercontent.com/43851883/82161447-08042c00-989d-11ea-96c9-5c2fb978ee4d.png)

Sinon, vous pouvez aussi utiliser le package en ligne de commande
- Lancez python3
```python
>>> import sportsbetting
>>> from sportsbetting.user_functions import *
```
- Vous pouvrez alors utiliser toutes les fonctions disponibles dans le fichier [user_functions.py](https://github.com/pretrehr/Sports-betting/blob/master/sportsbetting/user_functions.py).

## Initialisation
Avant de pouvoir pleinement utiliser toutes les fonctions du fichier [user_functions.py](https://github.com/pretrehr/Sports-betting/blob/master/sportsbetting/user_functions.py), il est nécessaire d'initialiser la base de matches sur lesquels on peut potentiellement parier. Par exemple, si l'on veut uniquement se concentrer sur les matches de Ligue 1 Française, et que l'on veut seulement parier sur Betclic et Winamax, on écrira :
```python
>>> parse_competition("ligue 1 france", "football", "betclic", "winamax")
```
On notera que si vous ne précisez pas de bookmaker, l'algorithme récupèrera les cotes des matches de la compétition sur la plupart des bookmakers agréés par l'ARJEL.
Si vous n'avez pas de compétition ou de sport cible, il est conseillé d'appeler
```python
>>> parse_football()
```
ou, par exemple,
```python
>>> parse_football("betclic", "winamax")
```
Ces fonctions vont récupérer les cotes des matches disponibles chez les différents bookmakers pour les 5 grands championnats européens de football (Ligue 1, Premier League, LaLiga, Serie A, Bundesliga), car ce sont ces compétitions qui, généralement, générent le plus de rendement.
On précisera que dans le cas du tennis où il n'y a pas de compétition fixe, il faut appeler la fonction:
```python
>>> parse_tennis()
```
ou, par exemple,
```python
>>> parse_tennis("betclic", "winamax")
```
Cette commande aura pour effet de récupérer les cotes de matches de tennis des compétitions actuellement disputées.

Vous trouverez ci-dessous un tableau récapitulatif des différents bookmakers agréés par l'ARJEL avec la chaîne de caractères associée dans le package.

| Bookmaker  | Chaîne de caractères |
| ------------- | ------------- |
| [Betclic](https://www.betclic.fr/sport/)  | `"betclic"`  |
| [BetStars](https://www.betstars.fr/)  | `"betstars"`  |
| [Bwin](https://sports.bwin.fr/fr/sports)  | `"bwin"`  |
| [France Pari](https://www.france-pari.fr/)  | `"france_pari"`  |
| [JOA](https://www.joa-online.fr/fr/sport)  | `"joa"` |
| [NetBet](https://www.netbet.fr/)  | `"netbet"` |
| [Parions Sport](https://www.enligne.parionssport.fdj.fr/) |`"parionssport"` |
| [PasinoBet](https://www.pasinobet.fr/) |`"pasinobet"` |
| [PMU](https://paris-sportifs.pmu.fr/) |`"pmu"` |
| [Unibet](https://www.unibet.fr/sport) |`"unibet"` |
| [Winamax](https://www.winamax.fr/paris-sportifs/sports/) |`"winamax"` |
| [Zebet](https://www.zebet.fr/fr/) |`"zebet"` |

*Nota bene*: Il n'est pour l'instant pas possible d'utiliser le package pour les bookmakers suivant :
- [Feelingbet](https://feelingbet.fr/) qui propose très peu de promotions. Mais au besoin, les cotes disponibles sur ce site sont identiques à celles disponibles sur [France Pari](https://www.france-pari.fr/)
- [Genybet](https://sport.genybet.fr/) qui est davantage axé sur les paris hippiques plutôt que sportifs
- [Vbet](https://www.vbet.fr/paris-sportifs) qui propose des promotions nombreuses mais très restrictives et donc peu rentables

La récupération des cotes peut être facilement utilisée depuis l'interface sur l'onglet "Récupération des cotes". Il suffit alors de choisir le sport, le (ou les) championnat(s) et le (ou les) bookmaker(s) souhaités. Une barre de chargement apparaît alors, la récupération des cotes est terminée lorsque la barre disparaît.

![image](https://user-images.githubusercontent.com/43851883/82161583-5534cd80-989e-11ea-928d-c94c821cd873.png)

À titre informatif, toutes les cotes récupérées sont consultables depuis l'onglet "Cotes" de l'interface. Dans cet onglet vous pouvez ainsi facilement comparer les cotes d'un même match entre les différents bookmakers. Vous avez également la possibilité de supprimer un match que vous ne souhaitez pas prendre en compte dans les calculs futurs.

![image](https://user-images.githubusercontent.com/43851883/82209315-5e10b800-990d-11ea-9b5a-db1065d316eb.png)

## Exemples d'utilisation

Les bonus reçus sont quasi systématiquement des freebets (ou paris gratuits). Un tel bonus signifie que lorsque l'on mise, par exemple, sur une cote à 3 avec un freebet de 10€, si le pari s'avère gagnant, alors on récupère 3×10-10 = 20€ (contre 30€ pour un pari standard), cela équivaut donc à miser avec un pari normal sur une cote réduite de 1.
On verra plus tard qu'il est possible de récupérer de manière certaine, 80% de la valeur d'un freebet. Ainsi, un freebet de 10€ équivaut à 10 × 0.8 = 8€.

Les exemples ci-dessous sont des exemples de promotions qui reviennent régulièrement chez les différents bookmakers. Vous y trouverez une description de comment exploiter au mieux ces promotions. Bien-sûr, cette liste n'est pas exhaustive et il vous appartient d'adapter ces exemples aux conditions des promotions que vous rencontrerez à l'avenir.
Pour chacun des exemples, vous trouverez une explication de comment rentabiliser une promotion similaire en ligne de commande ou à l'aide de l'interface.

### Exemple 1 : Bonus reçu dans tous les cas si l'on mise sur un match donné
France-pari propose très souvent une promotion qui consiste à miser un pari de 20€ sur un match précis de Ligue 1 à une cote minimale de 2 pour recevoir un freebet de 5€.
Par exemple, pour la 20e journée de Ligue 1 2019/2020, le match proposé était Toulouse - Brest.
Il suffit alors d'exécuter:
```python
>>> parse_competition("ligue 1", "football") #Si non exécuté précédemment
>>> best_stakes_match("Toulouse - Brest", "france_pari", 20, 2, "football")
```
Si la plus-value minimum est supérieure à 5 × 0.8 = 4€, alors cette promotion est rentable et on peut répartir nos mises telles qu'elles sont décrites.

Pour effectuer ce calcul depuis l'interface, il suffit de vous rendre sur l'onglet "Pari sur un match donné" et de sélectionner les paramètres souhaités.
![image](https://user-images.githubusercontent.com/43851883/82214782-a1bbef80-9916-11ea-8c4e-62f8187a09b5.png)

### Exemple 2 : Bonus reçu dans tous les cas si l'on mise sur un match quelconque, éventuellement d'une compétition donnée / d'un sport donné
S'il n'y a aucune condition sur le match à jouer, on peut éxécuter
```python
>>> parse_football()
```
car, comme dit plus haut, ce sont ces matches qui vont générer le plus de rendement.

Si on doit miser sur un match de NBA, on peut exécuter
```python
>>> parse_competition("nba", "basketball")
```

Si on doit miser sur un match de tennis, on peut exécuter
```python
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
```python
>>> best_match_under_conditions("france_pari", 1.7, 1000, "football", "3/1/2020", "0h00", "12/1/2020", "23h59")
```
Si la perte affichée est inférieure à 100 × 0.8 = 80€, alors cette promotion est rentable et on peut répartir nos mises telles qu'elles sont décrites.

Depuis l'interface, cela revient à se rendre sur l'onglet "Pari simple" et rentrer les paramètres adéquats.
![image](https://user-images.githubusercontent.com/43851883/82214951-e21b6d80-9916-11ea-8c95-2c3daf1a5b03.png)


### Exemple 3 : Bonus reçu si au moins *n* matches gagnés
*Nota bene*: À partir de cet exemple, on supposera que l'on a préalablement appelé une fonction d'initialisation des matches voulus (du type `parse_...`), en fonction des besoins de la promotion.

Parfois, il est nécessaire de gagner un certain nombre de paris pour recevoir un bonus. Dans ces cas-là, il faut miser sur le même bookmaker sur chacune des issues d'un même match. Betclic propose par exemple parfois de recevoir 10€ de freebet pour 3 paris gagnés, de 5€ chacun, misés sur des cotes d'au moins 1.7 et placés sur 3 matches différents. On peut alors exécuter
```python
>>> best_match_pari_gagnant("betclic", 1.7, 5, "tennis")
```
Cette fonction donnera le meilleur match sur lequel parier à un instant donné. Si la perte affichée est inférieure à (10 × 0.8)/3, alors on peut supposer que cette promotion est rentable et on peut répartir nos mises telles qu'elles sont décrites. Cela constituera le premier pari gagnant. Un peu plus tard (par exemple lorsque le match en question a été joué), on peut réitérer ce procédé afin de savoir sur quel match doit on jouer pour gagner le 2ème pari de la série et ainsi de suite jusqu'à atteindre 3 paris gagnants. À noter, que dans ce cas précis, il est nécessaire de ré-exécuter la fonction `parse_tennis` une fois qu'on a gagné un pari, car dans le cas contraire, le résultat renvoyé par la fonction `best_match_pari_gagnant` serait identique au résultat de l'exécution précédente.

Depuis l'interface, il vous suffit de vous rendre sur l'onglet "Pari gagnant" et de rentrer les paramètres voulus.
![image](https://user-images.githubusercontent.com/43851883/82216530-5a832e00-9919-11ea-9e62-5e0eeb10fe3d.png)

Une fois le pari placé, vous avez la possibilité de supprimer le match obtenu de la base de données depuis l'onglet "Cotes".
De cette manière, vous obtienez un résultat différent lorsque vous réexécutez le calcul depuis l'onglet "Pari gagnant".
![image](https://user-images.githubusercontent.com/43851883/82234278-7bf01400-9931-11ea-836b-e0a53a31deb6.png)


### Exemple 4 : Bonus reçu si un pari est perdant.
Il s'agit d'un type de promotion très courant, notamment en ce qui concerne les offres de bienvenue, mais pas seulement.
Par exemple, à l'été 2018, Winamax proposait à ses utilisateurs de rembourser en cash (donc pas en freebet) 100% leur premier pari de 200€ maximum si celui-ci est perdant. On notera par ailleurs que sur Winamax (comme sur la plupart des autres bookmakers), on ne peut parier que sur des cotes supérieures (ou égales) à 1.10. On peut alors exécuter
```python
>>> best_match_cashback("winamax", 1.1, 200, "football", freebet=False)
```

Ce calcul est également accessible depuis l'interface, dans l'onglet "Cashback".
![image](https://user-images.githubusercontent.com/43851883/82234484-c6719080-9931-11ea-8357-191bd9f58a78.png)


## Conversion des freebets en cash
### Méthode 1 : Si l'on n'a que des freebets fractionnables
Chez les bookmakers suivant : Betclic, Unibet, ParionsSport et Zebet, il est possible de fractionner les freebets gagnés en plusieurs paris. Par exemple, si l'on a gagné 10€ de freebets, il est possible de miser 8€ puis 2€.
Pour optimiser le gain, l'idée va alors être de couvrir toutes les issues avec des freebets sur un combiné de 2 matches de football (ce qui représente donc 9 issues à couvrir).
Par exemple, si on dispose de 10€ de freebet, on va alors exécuter
```python
>>> best_matches_freebet_one_site("betclic", 10)
```



### Méthode 2 : Si l'on a quelques freebets non fractionnables et suffisamment de freebets fractionnables
Chez tous les bookmakers sauf Betclic, Unibet, ParionsSport et Zebet, il n'est pas possible de séparer un freebet en plusieurs paris. 
Supposons que l'on dispose de 100€ de freebets fractionnables sur Betclic, 1 freebet de 10€ sur Winamax et 2 freebets de 5€ sur France-pari. 
L'idée serait alors de répartir nos 100€ de freebets fractionnables sur un combiné de 2 matches comme dans la méthode 1, puis de remplacer (totalement ou en partie) certaines mises par des freebets non fractionnables des autres bookmakers. De cette manière on répartit les freebets non fractionnables sur plusieurs issues d'un combiné et on comble les différences avec des freebets fractionnables. On aura donc vraisemblablement des issues couvertes uniquement par un freebet non fractionnable, d'autres couvertes en partie par un freebet non fractionnable et un freebet fractionnable, et d'autres couvertes uniquement en freebet fractionnable. Dans cet exemple, on exécute alors
```python
>>> best_matches_freebet(["betclic"], [[10, "winamax"], [5, "france_pari"], [5, "france_pari"]])
```

Depuis l'interface, l'onglet "Freebets à placer" effectue le même calcul, on obtient alors:
![image](https://user-images.githubusercontent.com/43851883/82235094-924a9f80-9932-11ea-95d9-e6c49d25fc00.png)


Cette deuxième méthode doit, lorsqu'elle est possible, être celle à privilégier lorsque l'on dispose de freebets non fractionnables car c'est elle qui offre le meilleur rendement. La première méthode est elle aussi très rentable mais il est préférable de conserver les freebets fractionnables pour justement appliquer la 2e méthode lorsque l'on disposera de freebets non fractionnables.



### Méthode 3 : Si l'on dispose de freebets non fractionnables et pas assez de freebets fractionnables
Par ailleurs, chez tous les bookmakers sauf Betclic, Unibet et Zebet, les freebets ont une date limite d'utilisation, allant de 2-3 jours pour Bwin, à 1 mois pour France-pari. Il peut donc être nécessaire de les jouer rapidement et il se peut également que l'on n'ait pas assez de freebets fractionnables pour pouvoir appliquer la 2e méthode. Dans cette situation, il est plus efficace de parier sur un unique match plutôt que sur un combiné. Il est également nécessaire de couvrir un pari en freebet avec de l'argent réel. De plus, avec cette méthode, on ne peut jouer qu'un freebet à la fois. Ainsi si l'on dispose d'un freebet de 15€ chez Betstars, on exécute alors
```python
>>> best_match_freebet("betstars", 15, "football")
```
*Nota bene* : Ne pas confondre `best_match_freebet` et `best_matches_freebet`.

On notera par ailleurs que certains sites comme NetBet ou PMU proposent parfois des freebets qui ne sont jouables que sur un unique sport. Auquel cas, il faut adapter le sport à la situation.


On peut appliquer cette méthode depuis l'interface dans l'onglet "Freebet unique".
![image](https://user-images.githubusercontent.com/43851883/82234834-3122cc00-9932-11ea-8709-6dec63176058.png)



Cette méthode est en moyenne beaucoup moins rentable et beaucoup plus volatile que les deux précédentes. Les deux premières méthodes assurent un taux de revient situé entre 77 et 85% de la somme de freebets engagés. Avec la 3ème méthode, il faut s'attendre à un taux de revient situé entre 55 et 70%.


## Avertissement
Ce projet a pour but d'aider l'utilisateur à dégager de l'argent en se rapprochant au maximum de l'absence de risque. Néanmoins, il est important de préciser que le risque zéro n'existe pas et que les cotes publiées par les bookmakers sont destinées à évoluer au cours du temps. Il est donc de votre ressort de vous assurer que les informations affichées par l'application Sports-betting sont fiables. En tant que créateur, je ne pourrai, en aucun cas, être tenu responsable de toute perte de capital survenue lors de l'utilisation 
de ce projet.

### *English version*

<details>
<summary>Table of contents</summary>

- [Installation](#installation)
- [Initialization](#initialization)
- [Examples of use](#examples-of-use)
  * [Example 1: Bonus received in all cases if you bet on a given match](#example-1-bonus-received-in-all-cases-if-you-bet-on-a-given-match)
  * [Example 2: Bonus received in all cases if you bet on any match, possibly from a given competition / sport](#example-2-bonus-received-in-all-cases-if-you-bet-on-any-match-possibly-from-a-given-competition--sport)
  * [Example 3: Bonus received if at least *n* matches are won](#example-3-bonus-received-if-at-least-n-matches-are-won)
  * [Example 4: Bonus received if a bet is lost.](#example-4-bonus-received-if-a-bet-is-lost)
- [Converting freebets to cash](#converting-freebets-to-cash)
  * [Method 1: If you only have fractionable freebets](#method-1-if-you-only-have-fractionable-freebets)
  * [Method 2: If you have a few non-fractionable freebets and enough fractionable freebets](#method-2-if-you-have-a-few-non-fractionable-freebets-and-enough-fractionable-freebets)
  * [Method 3: If you have non-fractionable freebets and not enough fractionable freebets](#method-3-if-you-have-non-fractionable-freebets-and-not-enough-fractionable-freebets)
</details>

## Installation
- Download the repository
- Go to the root of the repository
```bash
pip install -r requirements.txt
```
- Launch python3
```python
>>> import sportsbetting
>>> from sportsbetting.user_functions import *
```
- You can now use any function from [user_functions.py](https://github.com/pretrehr/Sports-betting/blob/master/sportsbetting/user_functions.py)



## Initialization
Before you can fully use all the functions in the [user_functions.py](https://github.com/pretrehr/Sports-betting/blob/master/sportsbetting/user_functions.py) file, it is necessary to initialize the database of matches you can potentially bet on. For example, if you only want to focus on French Ligue 1 matches, and you only want to bet on Betclic and Winamax, you would write :
```python
>>> parse_competition("ligue 1 france", "football", "betclic", "winamax")
```
Note that if you do not specify a bookmaker, the algorithm will retrieve the odds of the matches of the competition from most of the bookmakers approved by the ARJEL (French Regulatory authority for online games).
If you do not have a specific competition or target sport, it is advisable to call
```python
>>> parse_football()
```
or, for example,
```python
>>> parse_football("betclic", "winamax")
```
These functions will retrieve the odds of the matches available at the various bookmakers for the 5 major European football championships (Ligue 1, Premier League, LaLiga, Serie A, Bundesliga), as these competitions generally generate the highest returns.
It should be pointed out that in the case of tennis where there is no fixed competition, it is necessary to call the function:
```python
>>> parse_tennis()
```
or, for example,
```python
>>> parse_tennis("betclic", "winamax")
```
This command will retrieve the odds of tennis matches from the competitions currently being played.

You will find below a summary table of the different French bookmakers with the associated string in the package.

| Bookmaker | String |
| ------------- | ------------- |
| [Betclic](https://www.betclic.fr/sport/) | ``"betclic"" |
| [BetStars](https://www.betstars.fr/) | ``betstars"` |
| [Bwin](https://sports.bwin.fr/fr/sports) | "bwin" |
| [France Pari](https://www.france-pari.fr/) | `"france_pari"` |
| [JOA](https://www.joa-online.fr/fr/sport) | "joa"` |
| [NetBet](https://www.netbet.fr/) | `"netbet"` |
| [Pariels Sport](https://www.enligne.parionssport.fdj.fr/) |
| [PasinoBet](https://www.pasinobet.fr/) ||"pasinobet"` |
| [PMU](https://paris-sportifs.pmu.fr/) |"pmu"` |
| [Unibet](https://www.unibet.fr/sport) |
| [Winamax](https://www.winamax.fr/paris-sportifs/sports/) |
| [Zebet](https://www.zebet.fr/fr/) |

*Note bene*: It is currently not possible to use the package for the following bookmakers:
- [Feelingbet](https://feelingbet.fr/) which offers very few promotions. But if necessary, the odds available on this site are identical to those available on [France Pari](https://www.france-pari.fr/).
- [Genybet](https://sport.genybet.fr/) which focuses more on horse betting rather than sports betting.
- Vbet](https://www.vbet.fr/paris-sportifs) which offers numerous but very restrictive and therefore unprofitable promotions.


## Examples of use

The bonuses received are almost always freebets (or paris gratuits). Such a bonus means that when you bet, for example, on an odds equals to 3 with a €10 freebet, if the bet turns out to be winning, then you get 3×10-10 = €20 (compared to €30 for a standard bet), so it is equivalent to betting with a normal bet on an odds reduced by 1.
We will see later that it is possible to win back 80% of the value of a freebet with certainty. Thus, a €10 freebet is equivalent to 10 × 0.8 = €8.

The examples below are examples of promotions that regularly appear at the different bookmakers. You will find a description of how to get the most out of these promotions. This list is naturally not exhaustive and it is up to you to adapt these examples to the conditions of the promotions you will encounter in the future.
### Example 1: Bonus received in all cases if you bet on a given match
France-pari very often offers a promotion which consists in betting a €20 bet on a specific Ligue 1 match at a minimum odds of 2 to receive a €5 freebet.
For example, for the 20th round of Ligue 1 2019/2020, the proposed match was Dijon - Metz.
You just have to execute:
```python
>>> parse_competition("ligue 1", "football") #If not previously executed
>>> best_stakes_match("Dijon - Metz", "france_pari", 20, 2, "football")
```
If the minimum raise is more than 5 × 0.8 = €4, then this promotion is profitable and we can split our bets as specified.


### Example 2: Bonus received in all cases if you bet on any match, possibly from a given competition / sport
If there are no conditions on the game to be played, we can execute
```python
>>> parse_football()
```
because, as mentioned above, it is these matches that will generate the most returns.

If we're betting on an NBA game, we can execute...
```python
>>> parse_competition("nba", "basketball")
```

If we're going to bet on a tennis match, we can execute
```python
>>> parse_tennis()
```

It should also be noted that it is generally not possible to retrieve the odds of all the matches of a given sport, as this can be very costly in terms of execution time. It is therefore necessary to choose the most popular competition(s) for the chosen sport, as it is these matches that will generate the most returns.
The table below indicates which function to call for each sport.



| Sport | Function to call |
| ------------- | ------------- |
| Football | `parse_football()` |
| Basketball | `parse_nba()` (short for `parse_competition("nba", "basketball")`)|
| Tennis | `parse_tennis()` |
| Rugby | `parse_competitions(["top 14", "champions cup", "six nations"], "rugby")` |
| Ice Hockey | `parse_nhl()` (short for `parse_competition("nhl", "hockey-sur-glace")`) |

Once you have chosen your set of matches, you can then use the `best_match_under_conditions` function.

For example, France-pari regularly offers a promotion which consists in reimbursing, in freebet, 10% of the stakes engaged on odds higher than 1.70 and within a limit of €100 reimbursed. The objective is then to bet €1000 in order to recover the maximum bonus. Thus, if we assume that the promotion takes place between January 3, 2020 at midnight and January 12, 2020 at 11:59 pm, we can execute :
```python
>>> best_match_under_conditions("france_pari", 1.7, 1000, "football", "3/1/2020", "0h00", "12/1/2020", "23h59")
```
If the displayed loss is less than 100 × 0.8 = €80, then this promotion is profitable and we can distribute our stakes as described.

### Example 3: Bonus received if at least *n* matches are won
Please note: From this example, we'll assume that we previously called a function to initialize the desired matches (of the type `parse_...`), according to the needs of the promotion.

Sometimes it is necessary to win a certain number of bets to receive a bonus. In these cases, it is necessary to bet on the same bookmaker on each of the outcomes of the same match. For example, Betclic sometimes offers to receive a €10 freebet for 3 bets won, of €5 each, bet on odds of at least 1.7 and placed on 3 different matches. You can then execute
```python
>>> best_match_pari_gagnant("betclic", 1.7, 5, "tennis")
```
This feature will give you the best match to bet on at any given time. If the displayed loss is less than (10 × 0.8)/3, then we can assume that this promotion is profitable and we can distribute our stakes as described. This will be the first winning bet. A little later (e.g. when the match in question has been played), we can repeat this procedure to find out which match we need to play to win the 2nd bet in the series and so on until we reach 3 winning bets. Note that in this case, it is necessary to re-execute the `parse_tennis` function once you have won a bet, because otherwise the result returned by the `best_match_pari_gagnant` function would be identical to the result of the previous execution.

### Example 4: Bonus received if a bet is lost.
This is a very common type of promotion, especially but not only for welcome offers.
For example, in the summer of 2018, Winamax offered its users to pay back in cash (not freebet) 100% of their first bet of €200 maximum if they lost. It should also be noted that on Winamax (as on most other bookmakers), you can only bet on odds greater than (or equal to) 1.10. You can then run
```python
>>> best_match_cashback("winamax", 1.1, 200, "football", freebet=False)
```

## Converting freebets to cash
### Method 1: If you only have fractionable freebets
At the following bookmakers: Betclic, Unibet, ParionsSport and Zebet, it is possible to split the won freebets into several bets. For example, if you have won €10 in freebets, you can bet €8 and then €2.
To optimize the win, the idea will be to cover all the outcomes with freebets on a combination of 2 football matches (which represents 9 outcomes to cover).
For example, if you have €10 of freebet, you will then run
```python
>>> best_matches_freebet_one_site("betclic", 10)
```

### Method 2: If you have a few non-fractionable freebets and enough fractionable freebets
At all bookmakers except Betclic, Unibet, ParionsSport and Zebet, it is not possible to split a freebet into several bets. 
Let's suppose that you have €100 fractionable freebets on Betclic, 1 freebet of €10 on Winamax and 2 freebets of €5 on France-pari. 
The idea would then be to spread our €100 of fractionable freebets over a combination of 2 games as in method 1, then replace (totally or partially) some stakes with non-fractionable freebets from other bookmakers. In this way we spread the non-fractionable freebets over several outcomes of a handset and compensate the differences with fractionable freebets. So you are likely to have some outcomes covered only by a non-fractionable freebet, others covered partly by a non-fractionable freebet and a fractionable freebet, and others covered only by a fractionable freebet. In this example, we then execute
```python
>>> best_matches_freebet(["betclic"], [[10, "winamax"], [5, "france_pari"], [5, "france_pari"])
```
This second method should, where possible, be the preferred method when non-fractionable freebets are available, as it offers the best return. The first method is also very profitable but it is preferable to keep the fractionable freebets in order to apply the second method when you have non-fractionable freebets.

### Method 3: If you have non-fractionable freebets and not enough fractionable freebets
At all bookmakers except Betclic, Unibet and Zebet, freebets have a time limit, ranging from 2-3 days for Bwin, to 1 month for France-pari. It may therefore be necessary to bet them quickly and there may not be enough fractionable freebets to be able to apply the 2nd method. In this situation, it is more efficient to bet on a single match rather than on a combination. It is also necessary to cover a freebet with real money. Furthermore, with this method, you can only play one freebet at a time. So if you have a €15 freebet at Betstars, then you can execute
```python
>>> best_match_freebet("betstars", 15, "football")
```
Please note: Be careful not to confuse `best_match_freebet` with `best_matches_freebet`.

Note that some sites like NetBet or PMU sometimes offer freebets that are only playable on a single sport. In this case, you have to adapt the sport to the situation.
This method is on average much less profitable and much more volatile than the first two. The first two methods ensure a return rate of between 77 and 85% of the sum of freebets placed.  With the third method, a return rate between 55 and 70% is to be expected.


## Disclaimer
This project aims to help the user to free up money by getting as close as possible to the absence of risk. Nevertheless, it is important to specify that zero risk does not exist and that the odds published by bookmakers are intended to evolve over time. It is therefore your responsibility to make sure that the information displayed by the Sports-betting application is reliable. As the creator, I cannot be held responsible for any loss of capital that may occur during the use of the application.
