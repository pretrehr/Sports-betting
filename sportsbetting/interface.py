from tkinter import *
from tkinter import ttk
from sportsbetting.database_functions import get_all_sports, get_all_competitions
from sportsbetting.user_functions import parse_competitions


class Interface(Frame):
    
    """Notre fenêtre principale.
    Tous les widgets sont stockés comme attributs de cette fenêtre."""
    
    def __init__(self, fenetre, **kwargs):
        Frame.__init__(self, fenetre, width=768, height=576, **kwargs)
        self.pack(fill=BOTH)
        self.nb_clic = 0
        
        # Création de nos widgets
        self.message = Label(self, text="Vous n'avez pas cliqué sur le bouton.")
        self.message.pack()
        
        self.sport_list = Listbox(self)
        self.sport_list.pack()
        
        sports = get_all_sports()
        for sport in sports:
            self.sport_list.insert(END, sport)
        self.bouton_valider_sport = Button(self, text="Valider sport", command=self.valider_sport)
        self.bouton_valider_sport.pack()
        self.sport_list.bind("<Double-1>", lambda x: self.valider_sport())
        
        self.bouton_quitter = Button(self, text="Quitter", command=fenetre.destroy)
        self.bouton_quitter.pack(side="left")
        
        self.bouton_cliquer = Button(self, text="Cliquez ici", fg="red",
                command=self.cliquer)
        self.bouton_cliquer.pack(side="right")
    
    def cliquer(self):
        """Il y a eu un clic sur le bouton.
        
        On change la valeur du label message."""
        
        self.nb_clic += 1
        self.message["text"] = "Vous avez cliqué {} fois.".format(self.nb_clic)
    
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
        parse_competitions(self.selected_competitions, self.sport, *self.sites)
        

fenetre = Tk()
interface = Interface(fenetre)

interface.mainloop()