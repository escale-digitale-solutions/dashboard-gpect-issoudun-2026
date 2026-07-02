#!/usr/bin/env python3
"""Contre-expertise SYN Q26 — vérification de la fidélité des citations du
bloc 'verbatims' Q26 du dashboard (une seule action prioritaire).

Lit data/04_syndicats.xlsx (colonne index 26 : « Si vous ne pouviez proposer
qu'une seule action prioritaire... ») et affiche sur stdout les réponses non
vides, avec pour chacune un test de présence des mots-clés litigieux
(« orientation » vs « programmes scolaires »).

Aucune donnée n'est écrite dans le repo : sortie stdout uniquement,
pour comparaison manuelle avec les citations déjà publiées du dashboard.
Anonymat : aucune colonne d'identification (0-5) n'est lue ni affichée.
"""
import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/04_syndicats.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col = df.columns[26]
print(f"\nColonne [26] : {col!r}")

serie = df[col]
non_vides = serie.dropna().astype(str).str.strip()
non_vides = non_vides[non_vides != ""]
print(f"n (réponses non vides) = {len(non_vides)}\n")

for i, (idx, val) in enumerate(non_vides.items(), start=1):
    has_orient = "orientation" in val.lower()
    has_prog = "programme" in val.lower()
    has_simpl = "simplification" in val.lower() or "simplifier" in val.lower()
    print(f"--- Réponse S{i:02d} (flags: orientation={has_orient}, "
          f"programme={has_prog}, simplification={has_simpl}) ---")
    print(val)
    print()

# Contrôle complémentaire : la question voisine Q28 (résultats attendus,
# colonne 28) est aussi couverte par le titre du bloc dashboard
# « ...& résultats attendus » — on vérifie si la formulation litigieuse
# pourrait en provenir.
for cidx in (27, 28):
    col2 = df.columns[cidx]
    s2 = df[col2].dropna().astype(str).str.strip()
    s2 = s2[s2 != ""]
    hits = [v for v in s2 if "refonte" in v.lower() or "orientation" in v.lower()]
    print(f"Colonne [{cidx}] {col2[:60]!r}... : n={len(s2)}, "
          f"réponses contenant 'refonte' ou 'orientation' : {len(hits)}")
    for v in hits:
        print("  >>", v)
