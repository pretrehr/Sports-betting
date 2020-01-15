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




