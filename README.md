# Sports-betting
Sports betting assistant which optimizes earnings regarding odds and offers

(English version below)


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
On verra plus tard qu'il est possible de récupérer de manière certaine, 80% de la valeur d'un freebet. Ainsi, un freebet de 10€ équivaut à 10 × 0.8 = 8€

### Exemple 1 : Bonus reçu dans tous les cas si l'on mise sur un match donné
France-pari propose très souvent une promotion qui consiste à miser un pari de 20€ sur un match précis de Ligue 1 à une cote minimale de 2 pour recevoir un freebet de 5€.
Par exempe, pour la 20e journée de Ligue 1 2019/2020, le match propoosé était Dijon - Metz.
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
Le tableau ci-dessous indique quelle fonction appeler pour chaque sport



| Sport  | Fonction à appeler |
| ------------- | ------------- |
| football  | `parse_football()`  |
| basketball  | `parse_nba()` (ou `parse_competition("nba", "basketball")`)|
| tennis  | `parse_tennis()`  |
| rugby  | `parse_competitions(["top 14", "champions cup", "6 nations"], "rugby")`  |
| hockey-sur-glace  | parse_nhl()  |

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




