#!/usr/bin/env python3
"""Contre-expertise ACT Q6.1 — moyenne 'Offre de formation locale' :
globale (n=7) et sous-groupes Intérim (n=3) / Public (n=4).
Vérifie la valeur dashboard 'intérim 2,3 / public 2,2' vs auditeur 'public 2,3'.
Aucune donnée en dur ; sortie agrégée anonyme uniquement.
"""
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

PATH = "/home/user/dashboard-gpect-issoudun-2026/data/03_acteurs_emploi.xlsx"

df = pd.read_excel(PATH, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col_type = df.columns[4]   # Q0.1 type de structure
col_q61 = df.columns[53]   # Q6.1 offre de formation locale
print(f"Colonne type   [4] : {col_type[:80]}")
print(f"Colonne Q6.1  [53] : {col_q61[:80]}")

# Valeurs distinctes du type de structure (agrégat, non nominatif)
print("\nRépartition Q0.1 (type de structure) :")
print(df[col_type].value_counts(dropna=False).to_string())

q61 = pd.to_numeric(df[col_q61], errors="coerce")
print(f"\nQ6.1 valeurs non vides : n={q61.notna().sum()}")
print("Distribution des notes Q6.1 :")
print(q61.value_counts(dropna=False).sort_index().to_string())

def half_up(x, nd=1):
    return Decimal(str(x)).quantize(Decimal("0.1") if nd == 1 else Decimal("1"),
                                    rounding=ROUND_HALF_UP)

# Sous-groupes : intérim = type contenant 'intérim'/'interim', public = le reste
t = df[col_type].astype(str).str.lower()
mask_interim = t.str.contains("intérim") | t.str.contains("interim")
mask_public = ~mask_interim

for name, mask in [("GLOBAL", pd.Series(True, index=df.index)),
                   ("INTERIM", mask_interim),
                   ("PUBLIC", mask_public)]:
    vals = q61[mask].dropna()
    if len(vals) == 0:
        print(f"\n{name}: aucune valeur")
        continue
    m = vals.mean()
    s = vals.sum()
    print(f"\n{name}: n={len(vals)}  somme={s}  moyenne exacte={m!r} "
          f"({int(s)}/{len(vals)})  arrondi half-up 1 déc. = {half_up(m)}")
    # notes individuelles triées (agrégat anonyme, effectif minuscule mais
    # nécessaire pour trancher le tie 2,25 ; pas de lien nominatif)
    print(f"  multiset des notes : {sorted(vals.tolist())}")
