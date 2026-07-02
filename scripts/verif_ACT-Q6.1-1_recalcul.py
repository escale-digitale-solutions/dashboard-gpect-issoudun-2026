#!/usr/bin/env python3
"""Contre-expertise ACT Q6.1 — Offre de formation locale.
Recalcul de la moyenne globale (n=7) et des sous-groupes
Intérim (n=3) / Public (n=4), avec arrondi half-up à 1 décimale.
Dashboard : global 2,3 · intérim 2,3 · public 2,2.
Aucune donnée en dur : lecture directe du xlsx.
"""
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/03_acteurs_emploi.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col_q01 = df.columns[4]   # Q0.1 type de structure
col_q61 = df.columns[53]  # Q6.1 offre de formation locale
print(f"Colonne Q0.1 : {col_q01}")
print(f"Colonne Q6.1 : {col_q61}")

# Répartition des types de structure (agrégée, non nominative)
vc = df[col_q01].value_counts(dropna=False)
print("\nRépartition Q0.1 :")
for k, v in vc.items():
    print(f"  {k} : n={v}")

# Sous-groupe intérim = mention explicite d'intérim dans Q0.1
mask_interim = df[col_q01].astype(str).str.contains("intérim|interim", case=False, na=False)
print(f"\nIntérim : n={mask_interim.sum()} · Public : n={(~mask_interim).sum()}")

def stats(serie, label):
    s = pd.to_numeric(serie, errors="coerce").dropna()
    if len(s) == 0:
        print(f"{label} : aucune réponse")
        return
    m = s.mean()
    m_half_up = Decimal(str(m)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    print(f"{label} : n={len(s)} · somme={s.sum():.0f} · moyenne exacte={m!r} "
          f"· arrondi half-up 1 déc. = {m_half_up}")
    print(f"  valeurs triées (agrégat) : {sorted(s.tolist())}")

print("\n--- Q6.1 ---")
stats(df[col_q61], "Global (n=7 attendu)")
stats(df.loc[mask_interim, col_q61], "Intérim")
stats(df.loc[~mask_interim, col_q61], "Public")
