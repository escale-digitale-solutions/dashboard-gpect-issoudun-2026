#!/usr/bin/env python3
"""Contre-expertise Écart 4 (zone CROISE) : Q9.1 entreprises —
'Transmission/seniors = priorité GPECT la plus basse (2,5/5)'.
Recalcule la moyenne des 8 items Q9.1 (échelle 1-5) et identifie le minimum.
Aucune donnée en dur ; sortie agrégée anonyme uniquement.
"""
import re
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Identification des colonnes Q9.1 par leur intitulé (matrice de 8 items)
q91_cols = [c for c in df.columns if str(c).startswith("Q9.1")]
print(f"Colonnes Q9.1 trouvées : {len(q91_cols)}")

def label(col):
    m = re.search(r"\[(.+)\]\s*$", str(col))
    return m.group(1) if m else str(col)

def r1(x):
    return Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

rows = []
for c in q91_cols:
    s = pd.to_numeric(df[c], errors="coerce").dropna()
    rows.append({
        "item": label(c),
        "n": int(s.count()),
        "moyenne_brute": float(s.mean()),
        "moyenne_1dec": float(r1(s.mean())),
    })

res = pd.DataFrame(rows).sort_values("moyenne_brute").reset_index(drop=True)
print("\nMoyennes Q9.1 (tri croissant) :")
for _, r in res.iterrows():
    print(f"  {r['moyenne_brute']:.4f} -> {r['moyenne_1dec']:.1f} (n={r['n']}) {r['item']}")

mn = res["moyenne_brute"].min()
minis = res[abs(res["moyenne_brute"] - mn) < 1e-9]
print(f"\nMinimum brut = {mn:.4f}, atteint par {len(minis)} item(s) :")
for _, r in minis.iterrows():
    print(f"  - {r['item']} (affiché {r['moyenne_1dec']:.1f}/5, n={r['n']})")

# Items ex aequo une fois arrondis à 1 décimale (convention dashboard)
mn_arr = res["moyenne_1dec"].min()
minis_arr = res[res["moyenne_1dec"] == mn_arr]
print(f"\nMinimum arrondi (1 déc.) = {mn_arr:.1f}, atteint par {len(minis_arr)} item(s) :")
for _, r in minis_arr.iterrows():
    print(f"  - {r['item']} ({r['moyenne_brute']:.4f}, n={r['n']})")

res.to_csv("/home/user/dashboard-gpect-issoudun-2026/resultats/verif_CROISE-E4-1_q91_moyennes.csv", index=False)
print("\nRésultats agrégés écrits dans resultats/verif_CROISE-E4-1_q91_moyennes.csv")
