# -*- coding: utf-8 -*-
"""
Contre-expertise ACT Q1.2 — Importance des publics, Réfugiés / primo-arrivants,
sous-groupe Public (n=4). Dashboard affiche 2,2 ; premier auditeur calcule 2,25 -> 2,3 (half-up).
Objectif : réfuter ou confirmer l'écart. Aucune donnée en dur, sortie agrégée uniquement.
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

PATH = "/home/user/dashboard-gpect-issoudun-2026/data/03_acteurs_emploi.xlsx"
df = pd.read_excel(PATH, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Colonne de type de structure (Q0.1) et colonnes Q1.2
col_type = [c for c in df.columns if "Type de structure" in c or "type de structure" in c]
if not col_type:
    # fallback : colonne d'index 3 d'après colonnes_ACT.txt
    col_type = [df.columns[3]]
col_type = col_type[0]
print(f"Colonne type de structure : index {list(df.columns).index(col_type)}")

cols_q12 = [c for c in df.columns if "importance de chacun de ces publics" in c]
print(f"Nb colonnes Q1.2 trouvées : {len(cols_q12)}")

# Sous-groupes : intérim vs public (tout le reste)
type_norm = df[col_type].astype(str).str.lower()
mask_interim = type_norm.str.contains("intérim") | type_norm.str.contains("interim")
mask_public = ~mask_interim
print(f"Sous-groupe intérim : n={mask_interim.sum()} · sous-groupe public : n={mask_public.sum()}")

def round1_half_up(x):
    return Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

def round1_half_even(x):
    return round(float(x), 1)  # banker's rounding de Python

print("\n--- Moyennes Q1.2 par sous-groupe (exacte | half-up 1déc | half-even 1déc | n non-vides) ---")
for c in cols_q12:
    label = c.split("[")[-1].rstrip("]")
    s = pd.to_numeric(df[c], errors="coerce")
    for name, mask in (("Intérim", mask_interim), ("Public ", mask_public)):
        sub = s[mask].dropna()
        if len(sub) == 0:
            print(f"{label:45s} {name}: aucune réponse")
            continue
        m = sub.mean()
        print(f"{label:45s} {name}: exact={m:.6f} | half-up={round1_half_up(m)} | "
              f"half-even={round1_half_even(m)} | n={len(sub)} | somme={sub.sum():.0f}")

# Focus Réfugiés : détail des valeurs (agrégat : distribution des notes, pas nominatif)
col_ref = [c for c in cols_q12 if "Réfugiés" in c][0]
s = pd.to_numeric(df[col_ref], errors="coerce")
sub = s[mask_public].dropna()
print("\n--- Focus Réfugiés / primo-arrivants, sous-groupe Public ---")
print(f"n non-vides = {len(sub)} sur {mask_public.sum()} répondants du sous-groupe")
print("Distribution des notes :", sub.value_counts().sort_index().to_dict())
print(f"Moyenne exacte = {sub.mean()!r}")
print(f"Arrondi half-up (convention dashboard) = {round1_half_up(sub.mean())}")
print(f"Arrondi half-even / troncature = {round1_half_even(sub.mean())} / {int(sub.mean()*10)/10}")
