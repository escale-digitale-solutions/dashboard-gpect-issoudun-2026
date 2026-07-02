#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contre-expertise SYN Q17 — « Parmi les freins suivants, lesquels vous semblent
les plus structurants pour l'accès à l'emploi sur le territoire ? »
Fichier source : data/04_syndicats.xlsx (colonne index 17).
Question à choix multiples (cases à cocher Google Forms, avec champ "Autre").
Étape 1 (inspection des cellules brutes, non conservée en sortie de résultats)
a permis d'identifier les libellés exacts des options cochées. Ce script
produit uniquement des comptages agrégés anonymisés.
"""
import re
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/04_syndicats.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col = df.columns[17]
print(f"Colonne [17] : {col!r}\n")

serie = df[col].dropna().astype(str).str.strip()
serie = serie[serie != ""]
n = len(serie)
print(f"n (réponses non vides) = {n}\n")

# Libellés exacts observés dans les cellules (options standard du formulaire)
OPTIONS_STANDARD = [
    "Mobilité rurale",
    "Logement cher ou en mauvais état",
    "Compétences de base",
    "Freins sociaux",
    "Orientation",
    "Motivation des personnes",
]

def pct(k):
    return int(Decimal(k * 100 / n).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

counts = {opt: 0 for opt in OPTIONS_STANDARD}
libres = 0
themes_libres = []
for val in serie:
    reste = val
    for opt in OPTIONS_STANDARD:
        if opt in reste:
            counts[opt] += 1
            reste = reste.replace(opt, "")
    reste = re.sub(r"(^|,)\s*(?=,|$)", r"\1", reste)      # segments vidés
    reste = re.sub(r"^[,\s]+|[,\s]+$", "", reste)
    if reste:
        libres += 1
        # catégorisation générique, pas de verbatim intégral en résultat
        low = reste.lower()
        if "blablacar" in low or "covoitur" in low:
            themes_libres.append("covoiturage à initier (1 mention)")
        elif "niveau scolaire" in low:
            themes_libres.append("niveau scolaire de base faible chez certains jeunes (1 mention)")
        else:
            themes_libres.append(f"autre mention libre non catégorisée (1) : {reste[:40]}…")

print("=== Comptage recalculé (base : n répondants à la question) ===")
for opt, k in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"  {opt:<35} {k}/{n} = {pct(k)}%")
print(f"\nRéponses libres (champ « Autre ») : {libres} répondant(s)")
for t in themes_libres:
    print(f"  - {t}  -> 1/{n} = {pct(1)}%")

print("\n=== Comparaison avec le dashboard (bloc bars SYN Q17) ===")
dash = [("Mobilité rurale", 86), ("Logement cher / mauvais état", 43),
        ("Compétences de base", 43), ("Orientation", 29),
        ("Motivation des personnes", 14), ("Niveau scolaire faible (jeunes)", 14)]
for lbl, v in dash:
    print(f"  affiché : {lbl} = {v}%")
