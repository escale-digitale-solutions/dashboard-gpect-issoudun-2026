#!/usr/bin/env python3
"""Contre-expertise OF-SUB-1 : le chapeau de section OF du dashboard liste
6 types d'organismes ("OF privé, CFA, lycée pro, GRETA, IUT, financeur régional").
Le premier auditeur affirme que Q0.7 contient 7 types distincts pour 7 répondants.
On vérifie : bonne colonne, valeurs réelles, comptage par type (agrégé, anonyme).
"""
import pandas as pd
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "02_organismes_formation.xlsx"

df = pd.read_excel(DATA, engine="openpyxl")
print(f"Fichier : {DATA.name} — {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Colonnes Q0.7 (type d'organisme + champ "Autre, précisez")
cols = [c for c in df.columns if "Q0.7" in str(c)]
print("\nColonnes Q0.7 trouvées :")
for c in cols:
    print(f"  - {c}")

col_type = [c for c in cols if "Autre" not in str(c)][0]
col_autre = [c for c in cols if "Autre" in str(c)]

s = df[col_type].dropna().astype(str).str.strip()
print(f"\nQ0.7 Type d'organisme : n={len(s)} réponses non vides (sur {len(df)} répondants)")

# Distribution agrégée (catégories, pas de donnée nominative)
vc = s.value_counts()
print(f"Nombre de modalités (types) distinctes : {vc.size}")
print("Distribution (effectifs) :")
for val, cnt in vc.items():
    print(f"  {cnt} x {val}")

# Champ "Autre, précisez" : nombre de réponses non vides uniquement
for c in col_autre:
    n_autre = df[c].dropna().astype(str).str.strip().replace("", pd.NA).dropna().size
    print(f"\nChamp '{c}' : {n_autre} réponse(s) non vide(s)")

# Confrontation avec la liste du dashboard (chapeau "sub")
DASH_TYPES = ["privé", "CFA", "lycée", "GRETA", "IUT", "financeur"]
print("\n--- Confrontation avec le chapeau du dashboard ---")
print("Dashboard liste 6 types : OF privé, CFA, lycée pro, GRETA, IUT, financeur régional")
non_couverts = []
for val in vc.index:
    low = val.lower()
    couvert = any(k.lower() in low for k in DASH_TYPES)
    print(f"  {'COUVERT ' if couvert else 'ABSENT  '}: {val}")
    if not couvert:
        non_couverts.append(val)
print(f"\nTypes présents dans les données mais absents du chapeau : {len(non_couverts)}")
for v in non_couverts:
    print(f"  -> {v}")
