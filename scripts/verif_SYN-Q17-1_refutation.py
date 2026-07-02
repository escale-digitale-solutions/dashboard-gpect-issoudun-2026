#!/usr/bin/env python3
"""Contre-expertise SYN Q17 — 'Freins les plus structurants pour l'accès à l'emploi'.

Objectif : vérifier si le dashboard (6 items : 86/43/43/29/14/14) omet des
réponses (option 'Freins sociaux' + réponse libre), comme l'affirme le
premier auditeur. Choix multiple Google Forms : options séparées par ', ',
mais certaines options peuvent contenir des virgules -> on inspecte les
valeurs brutes, puis on compte par 'la cellule contient le texte de
l'option' pour les options standard, et on isole le reliquat (réponses
libres 'Autre').

Aucune donnée nominative n'est lue ni écrite : seule la colonne Q17 est
exploitée, et la sortie est agrégée (comptages, %, n=).
"""
import re
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data" / "04_syndicats.xlsx"
COL_IDX = 17  # [17] Parmi les freins suivants, lesquels vous semblent les plus structurants...

def pct(k, n):
    """Round half up, entier."""
    from decimal import Decimal, ROUND_HALF_UP
    return int(Decimal(k * 100 / n).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

df = pd.read_excel(DATA, engine="openpyxl")
print(f"Fichier : {DATA.name} — {df.shape[0]} lignes x {df.shape[1]} colonnes")
col = df.columns[COL_IDX]
print(f"Colonne [{COL_IDX}] : {col!r}\n")

s = df[col]
non_vides = s.dropna().astype(str).str.strip()
non_vides = non_vides[non_vides != ""]
n = len(non_vides)
print(f"n (réponses non vides) = {n}\n")

# 1) Inspection brute des cellules (anonyme : la question ne contient aucune
#    donnée nominative ; affichage limité aux valeurs de cette colonne)
print("=== Valeurs brutes des cellules (colonne Q17 uniquement) ===")
for i, v in enumerate(non_vides, 1):
    print(f"R{i:02d}: {v!r}")

# 2) Comptage par 'contains' sur des options candidates (issues du formulaire
#    et des libellés du dashboard). On vérifie ensuite que chaque fragment de
#    chaque cellule est couvert.
options_candidates = [
    "Mobilité",            # mobilité rurale / manque de mobilité
    "Logement",
    "Compétences de base",
    "Orientation",
    "Freins sociaux",
    "Motivation",
]
print("\n=== Comptage par option (cellule contient le texte, insensible casse) ===")
counts = {}
for opt in options_candidates:
    mask = non_vides.str.contains(re.escape(opt), case=False, regex=True)
    counts[opt] = int(mask.sum())
for opt, k in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"  {opt:<25} n={k}  ({pct(k, n)}%)")

# 3) Découpage naïf par ', ' pour lister TOUTES les modalités distinctes et
#    repérer les réponses libres ('Autre') non couvertes par les options.
print("\n=== Modalités distinctes après split ', ' (contrôle exhaustivité) ===")
from collections import Counter
frags = Counter()
for v in non_vides:
    for f in v.split(", "):
        frags[f.strip()] += 1
for f, k in frags.most_common():
    print(f"  n={k}  ({pct(k, n)}%)  {f!r}")

# 4) Comparaison au dashboard
print("\n=== Dashboard v12 (bloc bars Q17, n=7) ===")
dash = [("Mobilité rurale", 86), ("Logement cher / mauvais état", 43),
        ("Compétences de base", 43), ("Orientation", 29),
        ("Motivation des personnes", 14), ("Niveau scolaire faible (jeunes)", 14)]
for lab, v in dash:
    print(f"  {lab:<32} {v}%")
