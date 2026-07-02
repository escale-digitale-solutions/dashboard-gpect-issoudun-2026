#!/usr/bin/env python3
"""Contre-expertise OF-SUB-1 : le chapeau de section OF du dashboard liste
6 types d'organismes ("OF privé, CFA, lycée pro, GRETA, IUT, financeur régional").
Recalcul de la distribution réelle de Q0.7 (Type d'organisme) + colonne
"Autre type, précisez" dans l'export OF du 30/06/2026.
Sortie : uniquement des catégories agrégées (types d'organismes), aucune
donnée nominative.
"""
import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/02_organismes_formation.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Identification des colonnes Q0.7 par leur intitulé
cols_q07 = [c for c in df.columns if "Q0.7" in str(c)]
print("Colonnes Q0.7 trouvées :")
for c in cols_q07:
    print(f"  - {c}")

col_type = [c for c in cols_q07 if "récis" not in str(c) and "utre" not in str(c)][0]
col_autre = [c for c in cols_q07 if "utre" in str(c)][0]

s_type = df[col_type]
n_rep = s_type.notna().sum()
print(f"\nQ0.7 Type d'organisme — n={n_rep} réponses non vides / {len(df)} répondants")
print("Distribution des valeurs (catégories, non nominatives) :")
vc = s_type.value_counts(dropna=False)
for val, cnt in vc.items():
    print(f"  {cnt} x {val!r}")

print(f"\nNombre de types distincts en Q0.7 : {s_type.dropna().nunique()}")

# Colonne "Autre type, précisez"
s_autre = df[col_autre]
n_autre = s_autre.notna().sum()
print(f"\nQ0.7 'Autre type, précisez' — {n_autre} réponse(s) non vide(s)")
if n_autre:
    print("Valeurs (catégories de structure, non nominatives) :")
    for val in s_autre.dropna().unique():
        print(f"  - {val!r}")
