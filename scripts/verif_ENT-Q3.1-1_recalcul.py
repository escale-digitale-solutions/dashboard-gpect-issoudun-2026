#!/usr/bin/env python3
"""
Contre-expertise ENT Q3.1 — recomptage du codage thématique des verbatims
« métiers clés ou en tension » (colonne index 24 de data/01_entreprises.xlsx).

Vérifie en particulier le thème « Bureau études / méthodes / CAO »
(dashboard : 29 % soit 6/21 ; premier auditeur : 7/21 soit 33 %).

Règles :
- n = nombre de réponses non vides à la question.
- 1 répondant compte 1 fois pour un thème s'il cite au moins un métier du thème.
- % arrondi à l'entier (round half up), base répondants à la question.
- Aucune donnée en dur dans ce script ; sortie = comptages agrégés + identifiants
  anonymes E01..E21 (jamais de verbatim complet ni de nom).
"""
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
COL_IDX = 24  # Q3.1 — Listez vos 3 à 5 métiers clés ou en tension

def norm(txt: str) -> str:
    """Majuscules + suppression des accents pour un matching robuste."""
    t = unicodedata.normalize("NFKD", str(txt))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.upper()

# Grille de codage (mots-clés sur texte normalisé sans accents, en capitales).
# 'kw' = sous-chaînes ; 'rx' = regex (pour les sigles à frontière de mot).
THEMES = {
    "Usinage / réglage CN / mécanique": {
        "kw": ["USINAGE", "REGLEUR", "COMMANDE NUMERIQUE", "PROGRAMMEUR",
               "MECANICIEN", "FORGE"],
        "rx": [r"\bCN\b"],
    },
    "Bureau études / méthodes / CAO": {
        "kw": ["BUREAU D'ETUDE", "BUREAU ETUDE", "METHODE", "DESSINATEUR",
               "PROJETEUR"],
        "rx": [r"\bBE\b", r"\bCAO\b", r"\bDAO\b"],
    },
    "Encadrement / management": {
        "kw": ["CHEF DE PROJET", "CHEF D'EQUIPE", "RESPONSABLE", "RESP ",
               "ENCADR", "MANAGER", "MANAGEMENT"],
        "rx": [],
    },
    "Qualité / contrôle / HSE": {
        "kw": ["QUALITE", "CONTROLE", "CONTROLEUR", "QHSE", "CERTIFICATEUR"],
        "rx": [r"\bHSE\b"],
    },
    "Conduite / transport": {
        "kw": ["CONDUCTEUR", "CHAUFFEUR", "ROUTIER"],
        "rx": [r"\bSPL\b"],
    },
    "Maintenance": {
        "kw": ["MAINTENANCE", "ELECTROMECANICIEN"],
        "rx": [],
    },
    "Logistique / cariste": {
        "kw": ["LOGISTIQUE", "CARISTE", "MAGASINIER", "SUPPLY"],
        "rx": [],
    },
    "Soudure / chaudronnerie": {
        "kw": ["SOUDEUR", "SOUDURE", "CHAUDRON"],
        "rx": [],
    },
}

DASHBOARD = {  # valeurs affichées (% sur n=21) pour comparaison
    "Usinage / réglage CN / mécanique": 33,
    "Bureau études / méthodes / CAO": 29,
    "Encadrement / management": 29,
    "Qualité / contrôle / HSE": 24,
    "Conduite / transport": 24,
    "Maintenance": 19,
    "Logistique / cariste": 19,
    "Soudure / chaudronnerie": 10,
}

def pct(k: int, n: int) -> int:
    """% arrondi à l'entier, round half up (convention dashboard)."""
    return int((Decimal(k) * 100 / Decimal(n))
               .quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def main():
    df = pd.read_excel(XLSX, engine="openpyxl")
    col = df.columns[COL_IDX]
    print(f"Fichier : {XLSX}")
    print(f"Dimensions : {df.shape[0]} lignes x {df.shape[1]} colonnes")
    print(f"Colonne [{COL_IDX}] : {col}")

    serie = df[col]
    answered = serie.notna() & serie.astype(str).str.strip().ne("")
    n = int(answered.sum())
    print(f"n (réponses non vides) = {n}\n")

    print(f"{'Thème':40s} {'recalc':>7s} {'%rec':>5s} {'dash%':>6s}  écart")
    print("-" * 78)
    for theme, rules in THEMES.items():
        hits = []
        for i, v in enumerate(serie):
            if not answered.iloc[i]:
                continue
            t = norm(v)
            match = any(k in t for k in rules["kw"]) or \
                    any(re.search(r, t) for r in rules["rx"])
            if match:
                hits.append(f"E{i+1:02d}")
        p = pct(len(hits), n)
        d = DASHBOARD[theme]
        flag = "OK" if p == d else f"ECART ({d}% affiché)"
        print(f"{theme:40s} {len(hits):>4d}/{n:<2d} {p:>4d}% {d:>5d}%  {flag}")
        print(f"{'':40s} répondants : {', '.join(hits)}")
    print()

    # Focus sur le thème contesté : détail des mots-clés déclencheurs
    theme = "Bureau études / méthodes / CAO"
    rules = THEMES[theme]
    print(f"Détail du thème contesté « {theme} » :")
    for i, v in enumerate(serie):
        if not answered.iloc[i]:
            continue
        t = norm(v)
        trig = [k for k in rules["kw"] if k in t] + \
               [r for r in rules["rx"] if re.search(r, t)]
        if trig:
            print(f"  E{i+1:02d} -> mots-clés : {trig}")

if __name__ == "__main__":
    main()
