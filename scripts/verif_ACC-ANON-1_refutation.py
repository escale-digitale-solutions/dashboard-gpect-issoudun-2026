# -*- coding: utf-8 -*-
"""
Contre-expertise ACC-ANON-1 — ré-identification possible du plus gros répondant.
Vérifie, sur data/01_entreprises.xlsx (export 30/06/2026, 21 répondants) :
  - la colonne effectif Q1.4 (index 14) : max, effectif cumulé, part du max
  - avec la convention round half up à l'entier pour les %
Aucune donnée nominative n'est lue ni écrite : uniquement des agrégats.
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"

df = pd.read_excel(XLSX, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col = df.columns[14]
# on n'affiche que le libellé de la question (pas de donnée)
print(f"Colonne [14] : {col}")

s_raw = df[col]
print(f"Type brut : {s_raw.dtype}")
s = pd.to_numeric(s_raw, errors="coerce").dropna()
n = len(s)
total = s.sum()
mx = s.max()
nb_max = int((s == mx).sum())

def pct_half_up(x):
    return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

part = 100 * mx / total
part_arr = pct_half_up(part)

print(f"n réponses valides Q1.4 = {n} (non vides = {s_raw.notna().sum()})")
print(f"Effectif cumulé = {total:.0f}")
print(f"Max = {mx:.0f} (nb d'établissements à ce max : {nb_max})")
print(f"2e valeur la plus élevée = {s.sort_values(ascending=False).iloc[1]:.0f}")
print(f"Part du max = {part:.2f}% -> arrondi half-up = {part_arr}%")
print(f"Effectif cumulé SANS le max = {total - mx:.0f}")

# contrôle : le chiffre du dashboard « environ 1 550 salariés »
print(f"Le max est-il ~1550 ? {abs(mx - 1550) < 1}")
