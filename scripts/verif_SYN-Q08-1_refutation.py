# -*- coding: utf-8 -*-
"""
Contre-expertise SYN Q08 — thème verbatim « Foncier disponible / prix »
Dashboard : 43% (3/7). Premier auditeur : 57% (4/7).
On compte, parmi les 7 réponses à la question ouverte
« principaux atouts du territoire pour l'industrie et les TPE/PME » (col index 8),
celles qui mentionnent le foncier (racine 'fonci', insensible casse/accents non nécessaires ici).
Sortie : effectifs agrégés + contexte court (±70 caractères) autour de chaque
occurrence, pour vérifier le rattachement au thème "disponibilité / prix".
Aucune donnée en dur, aucun verbatim complet écrit dans resultats/.
"""
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

PATH = "/home/user/dashboard-gpect-issoudun-2026/data/04_syndicats.xlsx"
COL_IDX = 8  # Q08 atouts du territoire

df = pd.read_excel(PATH, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")
col = df.columns[COL_IDX]
print(f"Colonne [{COL_IDX}] : {col!r}")

serie = df[col]
n_college = len(serie)
non_vides = serie.dropna().astype(str).str.strip()
non_vides = non_vides[non_vides != ""]
n_question = len(non_vides)
print(f"n collège = {n_college} ; n réponses non vides à Q08 = {n_question}")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower()


pattern = re.compile(r"fonci")
hits = 0
for i, (idx, txt) in enumerate(serie.items(), start=1):
    rid = f"S{i:02d}"
    if not isinstance(txt, str) or not txt.strip():
        print(f"{rid}: (vide)")
        continue
    t = norm(txt)
    matches = list(pattern.finditer(t))
    if matches:
        hits += 1
        for m in matches:
            a, b = max(0, m.start() - 70), min(len(t), m.end() + 70)
            snippet = t[a:b].replace("\n", " / ")
            print(f"{rid}: MATCH 'fonci' -> ...{snippet}...")
    else:
        print(f"{rid}: pas de mention 'fonci'")

print(f"\nMentions 'fonci' : {hits}/{n_question} réponses")
for base, lbl in ((n_question, "base répondants question"), (n_college, "base collège n=7")):
    pct = int(Decimal(hits) / Decimal(base) * 100).__class__  # placeholder
    pct = Decimal(hits * 100) / Decimal(base)
    pct_r = int(pct.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    print(f"  {hits}/{base} = {pct_r}% ({lbl})")

# Contrôle croisé : les autres thèmes du dashboard, pour valider la méthode
themes = {
    "Axes routiers / logistique (43% affiché)": r"axe|routier|autoroute|logistiq|aeroport|a20|nord.sud",
    "Tissu industriel implanté (29% affiché)": r"tissu",
    "Proximité pouvoirs publics (29% affiché)": r"pouvoirs publics|proximite.*(elus|institution|pouvoir)|collectivit",
    "Data center / numérique (14% affiché)": r"data ?cent|numeri",
}
print("\nContrôle croisé des autres thèmes (comptage lexical indicatif) :")
for lbl, pat in themes.items():
    rx = re.compile(pat)
    c = sum(1 for txt in non_vides if rx.search(norm(txt)))
    pct = Decimal(c * 100) / Decimal(n_question)
    pct_r = int(pct.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    print(f"  {lbl}: {c}/{n_question} = {pct_r}%")
