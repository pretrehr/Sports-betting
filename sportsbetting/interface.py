from tkinter import *
from tkinter import ttk
from sportsbetting.database_functions import get_all_sports, get_all_competitions
from sportsbetting.user_functions import parse_competitions
from sportsbetting.selenium_init import start_selenium
import threading


class Parsing(Frame):
    
    """Notre fenêtre principale.
    Tous les widgets sont stockés comme attributs de cette fenêtre."""
    
    def __init__(self, fenetre, **kwargs):
        Frame.__init__(self, fenetre, width=768, height=576, **kwargs)
        self.pack(fill=BOTH)

        
        self.sport_list = Listbox(self)
        self.sport_list.pack()
        
        sports = get_all_sports()
        for sport in sports:
            self.sport_list.insert(END, sport)
        self.bouton_valider_sport = Button(self, text="Valider sport", command=self.valider_sport)
        self.bouton_valider_sport.pack()
        self.sport_list.bind("<Double-1>", lambda x: self.valider_sport())
    
    def valider_sport(self):
        self.sport = get_all_sports()[int(self.sport_list.curselection()[0])]
        competitions = get_all_competitions(self.sport)
        self.sport_list.pack_forget()
        self.bouton_valider_sport.pack_forget()
        self.competition_list = Listbox(self, selectmode='multiple')
        self.competition_list.pack()
        self.bouton_valider_competitions = Button(self, text="Valider competitions", command=self.valider_competitions)
        self.bouton_valider_competitions.pack()
        for competition in competitions:
            self.competition_list.insert(END, competition)
    
    def valider_competitions(self):
        sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet', 'parionssport',
                 'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']
        self.selected_competitions = [self.competition_list.get(i) for i in self.competition_list.curselection()]
        self.competition_list.pack_forget()
        self.bouton_valider_competitions.pack_forget()
        self.sites_list = Listbox(self, selectmode='multiple')
        self.sites_list.pack()
        self.bouton_valider_sites = Button(self, text="Valider sites", command=self.valider_sites)
        self.bouton_valider_sites.pack()
        for site in sites:
            self.sites_list.insert(END, site)
    
    
    def valider_sites(self):
        self.sites = [self.sites_list.get(i) for i in self.sites_list.curselection()]
        def parse_thread():
            parse_competitions(self.selected_competitions, self.sport, *self.sites)
        thread = threading.Thread(target=parse_thread)
        thread.start()
        sportsbetting.PROGRESS = 0
        self.progress_bar = ttk.Progressbar(self, orient=HORIZONTAL,
                                            length=100,
                                            mode='determinate')
        self.progress_bar.pack()
        while sportsbetting.PROGRESS < 100:
            self.progress_bar["value"] = sportsbetting.PROGRESS
            self.progress_bar.update()
        self.progress_bar.pack_forget()
        self.parsing_completed = Label(self, text="Récupération des cotes terminée")
        self.parsing_completed.pack()
        self.after(3000, lambda: self.parsing_completed.pack_forget())
            
class Best_match_under_conditions(Frame):
    def __init__(self, fenetre, **kwargs):
        Frame.__init__(self, fenetre, width=768, height=576, **kwargs)
        self.pack(fill=BOTH)
        sites = ['betclic', 'betstars', 'bwin', 'france_pari', 'joa', 'netbet', 'parionssport',
                 'pasinobet', 'pmu', 'unibet', 'winamax', 'zebet']
        self.sites_list = Listbox(self, exportselection=False)
        for site in sites:
            self.sites_list.insert(END, site)
        self.sites_list.pack()
        self.min_odd_entry = Entry(self)
        self.min_odd_entry.pack()
        self.bet_entry = Entry(self)
        self.bet_entry.pack()
        self.sport_list = Listbox(self, exportselection=False)
        self.sport_list.pack()
        sports = get_all_sports()
        for sport in sports:
            self.sport_list.insert(END, sport)
        validate = Button(self, text="Calculer", command=self.calcul)
        validate.pack()
    
    def calcul(self):
        site = self.sites_list.get(self.sites_list.curselection())
        sport = self.sport_list.get(self.sport_list.curselection())
        minimum_odd = float(self.min_odd_entry.get())
        bet = float(self.bet_entry.get())
        def parse_thread():
            best_match_under_conditions(site, minimum_odd, bet, sport)
        thread = threading.Thread(target=parse_thread)
        thread.start()
        
    
    
fenetre = Tk()
fenetre.title("Sports betting")
tabControl = ttk.Notebook(fenetre)
tab1 = ttk.Frame(tabControl)
tab2 = ttk.Frame(tabControl)


tabControl.add(tab1, text ='Récupération des cotes') 
tabControl.add(tab2, text ='Best match under conditions') 
tabControl.pack(expand = 1, fill ="both")
n_tabs = tabControl.index(END)
if not sportsbetting.ODDS:
    for i in range(1, n_tabs):
        tabControl.tab(i, state="disabled")
parsing = Parsing(tab1)
parsing.pack()
match_under_condition = Best_match_under_conditions(tab2)
match_under_condition.pack()
Button(fenetre, text="Quitter", command=fenetre.destroy).pack(side="left")

fenetre.mainloop()