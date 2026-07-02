#!/usr/bin/env python3
"""Contre-expertise CROISE Convergence 4 :
« besoins "partiellement formalisés" pour 71% des syndicats ».
Vérifie la distribution exacte de la colonne 11 du questionnaire syndicats
(« Les besoins en compétences des entreprises industrielles vous semblent
aujourd'hui : ») et teste si une modalité « partiellement formalisés »
existe, ainsi que les agrégats possibles donnant 71%.
Aucune donnée nominative n'est affichée.
"""
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

PATH = "/home/user/dashboard-gpect-issoudun-2026/data/04_syndicats.xlsx"

def pct(k, n):
    k, n = int(k), int(n)
    return int((Decimal(k) * 100 / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

df = pd.read_excel(PATH, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col = df.columns[11]
print(f"\nColonne [11] : {col}")
s = df[col].dropna().astype(str).str.strip()
s = s[s != ""]
n = len(s)
print(f"n (réponses non vides) = {n}")

print("\nDistribution des modalités exactes :")
vc = s.value_counts()
for mod, k in vc.items():
    print(f"  « {mod} » : {k}/{n} = {pct(k, n)}%")

# Test 1 : une modalité contient-elle littéralement « partiellement formalisés » ?
lit = s.str.lower().str.contains("partiellement formalis").sum()
print(f"\nRéponses contenant littéralement 'partiellement formalis…' : {lit}")

# Test 2 : agrégats candidats pour atteindre 71%
low = s.str.lower()
cand = {
    "contient 'partiellement'": low.str.contains("partiellement").sum(),
    "contient 'formalis'": low.str.contains("formalis").sum(),
    "contient 'identifi'": low.str.contains("identifi").sum(),
    "partiellement OU peu formalisés (non pleinement formalisés)":
        (low.str.contains("partiellement") | low.str.contains("peu")).sum(),
}
print("\nAgrégats candidats :")
for lab, k in cand.items():
    print(f"  {lab} : {k}/{n} = {pct(k, n)}%")

# Test 3 : vérifier aussi qu'il ne s'agit pas d'une autre colonne (balayage)
print("\nBalayage : colonnes syndicats dont des valeurs contiennent 'formalis' :")
for i, c in enumerate(df.columns):
    vals = df[c].dropna().astype(str)
    if vals.str.lower().str.contains("formalis").any():
        k = vals.str.lower().str.contains("formalis").sum()
        print(f"  [{i}] {c[:70]}… : {k} cellules")
