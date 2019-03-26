from itertools import combinations, product
from math import log, exp

def prod(data):
    """
    Calcule le produit des donnees d'un tableau
    """
    return exp(sum(map(log, data)))

def gain(cotes, mise=1):
    """
    Calcule le gain pour une somme des mises égale à mise
    """
    s = 0
    n = len(cotes)
    for combi in combinations(cotes, n-1):
        s += prod(combi)
    p = prod(cotes)
    return mise*p/s

def mises(cotes, mise=1):
    """
    Calcule la répartition des mises pour minimiser les pertes avec une mise totale égale à mise
    """
    s = 0
    n = len(cotes)
    for combi in combinations(cotes, n-1):
        s += prod(combi)
    p = prod(cotes)
    out = []
    for i in range(n):
        out.append(mise*p/(s*cotes[i]))
    if mise!=1:
        print(round(sum(out),2))
    return out

def troncature(x, n=2):
    """
    Effectue une troncature à n chiffres après la virgule
    """
    return int(x*10**n)/10**n
    
def mises2(cotes, mise_requise, choix=-1):
    """
    Calcule la répartition des mises en pariant mise_requise sur l'une des issues
    """
    m = mises(cotes)
    if choix==-1:
        rapport = max(m)
    else:
        rapport = m[choix]
    for i in range(len(m)):
        m[i] = round(mise_requise*m[i]/rapport,2)
    print("somme des mises =",sum(m))
    print("gain min =", min([troncature(m[i]*cotes[i]) for i in range(len(m))]))
    print("gain max =", max([troncature(m[i]*cotes[i]) for i in range(len(m))]))
    print("perte max =", round(min([troncature(m[i]*cotes[i]) for i in range(len(m))])-sum(m),2))
    return m

def mises_freebet(cotes, freebet, issue=-1):
    """
    Calcule la répartition des mises en présence d'un freebet à placer
    """
    m = []
    if issue>-1:
        cote_max = cotes[issue]
    else:
        cote_max = max(cotes)
    gain = (cote_max-1)*freebet
    max_trouve = False
    for c in cotes:
        if c == cote_max and not max_trouve:
            m.append(freebet)
            max_trouve = True
        else:
            m.append(round(gain/c,2))
    print("gain sur freebet =",round(gain+freebet-sum(m),2))
    print("mise totale =",sum(m))
    return m

def mises_cashback(cotes, taux_cashback, issue_concernee, cashback_max):
    """
    Calcule les mises lorsque l'une des issues est concernée par un cashback
    """
    mise_cashback = cashback_max/taux_cashback
    mises_standard = mises2(cotes, mise_cashback, issue_concernee)
    gain = mise_cashback * cotes[issue_concernee]
    for i in range(len(cotes)):
        if i!=issue_concernee:
            mises_standard[i] = round((gain-cashback_max)/cotes[i],2)
    print("somme des mises =", sum(mises_standard))
    print("gain net =", round(gain - sum(mises_standard),2))
    return mises_standard

def mises_cashback2(cotes, issue_concernee, cashback_max):
    """
    Calcule les mises lorsqu'une des issues est concernée par un cashback en freebet
    """
    c = cotes[:issue_concernee]+cotes[issue_concernee+1:]
    mises_c = mises(c,cashback_max)
    gain_c = gain(c,cashback_max)
    mise_restante = (gain_c-cashback_max*0.7)/cotes[issue_concernee]
    print("somme des mises =", sum(mises_c)+mise_restante)
    print("gain =", gain_c)
    return mises_c[:issue_concernee]+[mise_restante]+mises_c[issue_concernee:]


def cotes_combine(cotes):
    """
    Calcule les cotes de plusieurs matches combinés
    """
    out = []
    chaine = "list(product("
    for i in cotes:
        chaine += str(i)
        chaine += ", "
    chaine += "))"
    a = eval(chaine)
    for i in a:
        out.append(round(prod(i),4))
    return out

def cotes_freebet(cotes):
    """
    Calcule les cotes d'un match joué avec des paris gratuits
    """
    return list(map(lambda x:x-1,cotes))
        
            
def calcul_miles(cote, mise):
    """
    Calcule le nombre de miles remportés sur Winamax en pariant mise sur cote
    """
    return mise*0.4*(1-1/cote)
    
        
def pari_rembourse(cotes, mise_max, rang=-1, remb_freebet = False):
    """
    Calcule les mises lorsque l'un des paris est totalement remboursé
    """
    m = max(cotes)
    taux = (not remb_freebet) + 0.7*remb_freebet
    if rang>=0:
        return mises_cashback(cotes,taux,rang,mise_max*taux)
    for e,i in enumerate(cotes):
        if i==m:
            rang_max = e
    return mises_cashback(cotes,taux,rang_max,mise_max*taux)

def pari_rembourse2(cotes, mise1, mise2):
    gain1 = cotes[0]*mise1+mise2*0.7
    gain2 = cotes[1]*mise2+mise1*0.7
    mise3 = (max(gain1, gain2)-(mise1+mise2)*0.7)/cotes[2]
    print("somme mises = ", mise1+mise2+mise3)
    print("gain1=", gain1)
    print("gain2=", gain2)
    print("mise3 =", mise3)
    

def pari_rembourse_buteur(j1_marque, j1egalj2, j2supj1, mise):
    gain = mise*(1+j1_marque)
    mises = [mise]
    mises.append(gain/j1egalj2)
    mises.append((gain-mise)/j2supj1)
    print("somme des mises =", sum(mises))
    print("gain min =", gain)
    print("gain max =", 2*gain)
    print("perte max =", gain-sum(mises))
    return mises

def promo_netbet(cotes):
    mises_base = mises(cotes)
    m = sum(mises_base)-min(mises_base)
    taux = 100/m
    mis = mises(cotes, taux)
    gain = mis[0]*cotes[0]
    for i in range(3):
        print("gain net =", gain-sum(mis)+sum(mis[:i]+mis[i+1:])/2*0.6)
    return mis
        
def meilleurs_parmi(cotes,n):
    """
    Calcule les meilleurs matches parmi un ensemble de matches
    """
    return sorted(cotes, key=gain, reverse=True)[:n]


def pari_rembourse_si_perdant(cotes, mise_max, rang=-1, remb_freebet = False):
    """
    Calcule les mises lorsque l'un des paris est totalement remboursé
    """
    taux = (not remb_freebet) + 0.77*remb_freebet
    if rang==-1:
        m = max(cotes)
        for e,i in enumerate(cotes):
            if i==m:
                rang = e
    gain = mise_max*cotes[rang]
    mises = []
    for i in range(len(cotes)):
        if i==rang:
            mises.append(mise_max)
        else:
            mises.append((gain-mise_max*taux)/cotes[i])
    print("gain net =", gain-sum(mises))
    print(mises)
    return gain-sum(mises)

def meilleure_issue(fonction):
    a = max(list([0,1,2]), key=fonction)
    print("")
    fonction(a)
    return a

def mises_freebets(cotes,mise):
    return mises(cotes_freebet(cotes), mise)
    
def somme(a,b):
    return [a[i]+b[i] for i in range(len(a))]