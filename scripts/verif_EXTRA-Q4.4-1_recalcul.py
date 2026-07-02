# -*- coding: utf-8 -*-
"""
Contre-expertise EXTRA — Levier 5 + fiche D1 : « 136 départs à 5 ans (60% en production) »
Source : data/01_entreprises.xlsx
 - Q4.3 (col 51) : Nombre de départs à la retraite prévisibles d'ici 5 ans  -> cumul (le "136")
 - Q4.4 (col 52) : Sur quels services ou métiers ces départs vont-ils se concentrer ? (choix multiple)

Deux lectures possibles du "(60% en production)" :
 A) % d'ENTREPRISES répondantes à Q4.4 citant la production (base répondants, choix multiple)
 B) % des 136 DÉPARTS qui seraient en production (départs Q4.3 des entreprises citant la
    production / 136) — lecture induite par la formulation, vérifiée à titre de contrôle.

Aucune donnée nominative ni verbatim n'est écrit en sortie : uniquement comptages agrégés.
"""
import re
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col_q43 = df.columns[51]
col_q44 = df.columns[52]
print(f"Col 51 (Q4.3) : {col_q43}")
print(f"Col 52 (Q4.4) : {col_q44}")

# ---- Q4.3 : cumul des départs à 5 ans ----
q43 = pd.to_numeric(df[col_q43], errors="coerce")
n_q43 = int(q43.notna().sum())
total_departs = q43.sum()
print(f"\nQ4.3 — n réponses numériques = {n_q43} ; cumul départs 5 ans = {total_departs:g}")

# ---- Q4.4 : inspection anonyme des valeurs (choix multiple, séparateur ', ') ----
q44_raw = df[col_q44]
mask_rep = q44_raw.notna() & (q44_raw.astype(str).str.strip() != "")
n_q44 = int(mask_rep.sum())
print(f"\nQ4.4 — n répondants (cellules non vides) = {n_q44}")

vals = q44_raw[mask_rep].astype(str)

# Détection "production" : toute cellule contenant production/fabrication (insensible casse)
pat_prod = re.compile(r"production|fabrication", re.IGNORECASE)
cite_prod = vals.apply(lambda s: bool(pat_prod.search(s)))
n_prod = int(cite_prod.sum())


def pct(num, den):
    return int(Decimal(num) / Decimal(den) * 100 if den else 0) if False else int(
        (Decimal(num) * 100 / Decimal(den)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )


print(f"\nLECTURE A — part des entreprises répondantes à Q4.4 citant la production :")
print(f"  {n_prod}/{n_q44} = {pct(n_prod, n_q44)}%")

# ---- Lecture B : part des 136 départs portés par les entreprises citant la production ----
idx_rep = vals.index
departs_repondants_q44 = q43.loc[idx_rep]
departs_citant_prod = departs_repondants_q44[cite_prod].sum()
print(f"\nLECTURE B — départs (Q4.3) déclarés par les entreprises citant la production :")
print(f"  {departs_citant_prod:g} départs / {total_departs:g} total = "
      f"{pct(int(departs_citant_prod), int(total_departs))}% des départs")
print("  (NB : lecture indicative — une entreprise citant plusieurs services ne permet pas")
print("   d'attribuer ses départs au seul service production.)")

# ---- Contrôle complet du graphe Q4.4 du dashboard (% de répondants) ----
options = {
    "Production / fabrication": r"production|fabrication",
    "Logistique": r"logistique",
    "Commerce / ADV": r"commerc|adv|administration des ventes|vente",
    "Conduite / transport": r"conduite|transport|chauffeur|conducteur",
    "Qualité": r"qualit",
    "Maintenance": r"maintenance",
    "Bureau d'études": r"bureau d.études|études|etudes",
    "Management de proximité": r"management|encadrement",
}
print(f"\nContrôle du graphe Q4.4 (base n={n_q44}, % de répondants, choix multiple) :")
for label, pattern in options.items():
    rx = re.compile(pattern, re.IGNORECASE)
    n_opt = int(vals.apply(lambda s: bool(rx.search(s))).sum())
    print(f"  {label:32s} n={n_opt:2d}  -> {pct(n_opt, n_q44)}%")
