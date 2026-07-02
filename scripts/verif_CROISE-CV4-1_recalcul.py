#!/usr/bin/env python3
"""Contre-expertise CROISE Convergence 4 :
« besoins "partiellement formalisés" pour 71% des syndicats ».
Recalcul indépendant depuis data/04_syndicats.xlsx, colonne
« Les besoins en compétences des entreprises industrielles vous semblent aujourd'hui : »
Sortie : distribution agrégée anonymisée (comptages, %, n=).
"""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
XLSX = BASE / "data" / "04_syndicats.xlsx"

df = pd.read_excel(XLSX, engine="openpyxl")
print(f"Fichier lu : {XLSX.name} — {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Identification de la colonne par son intitulé (pas par index en dur)
cible = [c for c in df.columns if "besoins en compétences des entreprises industrielles" in str(c).lower()]
assert len(cible) == 1, f"Colonne cible non unique : {cible}"
col = cible[0]
print(f"Colonne source : {col!r}")

s = df[col].dropna().astype(str).str.strip()
s = s[s != ""]
n = len(s)
print(f"n = {n} réponses non vides")

def pct(k, n):
    return int(Decimal(k * 100 / n).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

print("\nDistribution exacte des modalités :")
vc = s.value_counts()
for modalite, k in vc.items():
    print(f"  {modalite!r} : {k}/{n} ({pct(k, n)}%)")

# Test de l'agrégat allégué : modalités contenant "partiel" ou "peu formalis"
mask_agg = s.str.lower().str.contains("partiel") | s.str.lower().str.contains("peu formalis")
k_agg = int(mask_agg.sum())
print(f"\nAgrégat 'partiellement identifiés' + 'peu formalisés' : {k_agg}/{n} ({pct(k_agg, n)}%)")

# Existe-t-il une modalité exactement "partiellement formalisés" ?
exact = s.str.lower().str.contains("partiellement formalis")
print(f"Réponses contenant littéralement 'partiellement formalis…' : {int(exact.sum())}")
