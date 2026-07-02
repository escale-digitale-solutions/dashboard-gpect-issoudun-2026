# -*- coding: utf-8 -*-
"""
Contre-expertise CROISE-E4-3 — « 136 départs retraite à 5 ans,
départs concentrés à 60% sur la production ».

Vérifie, depuis les données brutes (data/01_entreprises.xlsx) :
1. le total de départs à la retraite à 5 ans (Q4.3, col 51) ;
2. la part d'entreprises répondantes à Q4.4 (col 52, texte libre)
   qui citent la production/fabrication ;
3. la part des départs (Q4.3) portés par ces entreprises.

Aucune donnée brute n'est imprimée nominativement : uniquement des
agrégats et, pour Q4.4, des indicateurs booléens anonymisés (E01...).
"""
import re
import pandas as pd

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"

df = pd.read_excel(XLSX, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col_q43 = df.columns[51]
col_q44 = df.columns[52]
print(f"Col 51 : {col_q43}")
print(f"Col 52 : {col_q44}")

# --- 1. Total départs à 5 ans (Q4.3) ---
q43 = pd.to_numeric(df[col_q43], errors="coerce")
n43 = q43.notna().sum()
total_departs = q43.sum()
print(f"\nQ4.3 — n réponses numériques = {n43} ; total départs 5 ans = {total_departs:.0f}")

# --- 2. Q4.4 texte libre : citations de la production/fabrication ---
q44 = df[col_q44].astype("string").str.strip()
mask_rep = q44.notna() & (q44 != "")
n44 = int(mask_rep.sum())
print(f"Q4.4 — n réponses non vides = {n44}")

PAT = re.compile(r"production|fabrication|atelier|usinage|opérateur|operateur", re.IGNORECASE)
cite_prod = mask_rep & q44.str.contains(PAT, na=False)
n_prod = int(cite_prod.sum())
pct_ent = 100.0 * n_prod / n44 if n44 else float("nan")
print(f"Q4.4 — entreprises citant production/fabrication/atelier/usinage/opérateur : "
      f"{n_prod}/{n44} = {pct_ent:.1f}%")

# Variante stricte (uniquement 'production' ou 'fabrication')
PAT2 = re.compile(r"production|fabrication", re.IGNORECASE)
cite_prod2 = mask_rep & q44.str.contains(PAT2, na=False)
n_prod2 = int(cite_prod2.sum())
print(f"Q4.4 — variante stricte (production/fabrication seulement) : "
      f"{n_prod2}/{n44} = {100.0*n_prod2/n44:.1f}%")

# --- 3. Part des DÉPARTS portés par les entreprises citant la production ---
departs_prod = q43[cite_prod].sum()
departs_prod2 = q43[cite_prod2].sum()
print(f"\nDéparts Q4.3 portés par les entreprises citant la production (élargi) : "
      f"{departs_prod:.0f}/{total_departs:.0f} = {100.0*departs_prod/total_departs:.1f}%")
print(f"Départs Q4.3 portés par les entreprises citant la production (strict) : "
      f"{departs_prod2:.0f}/{total_departs:.0f} = {100.0*departs_prod2/total_departs:.1f}%")

# --- Détail anonymisé : pour chaque répondant, départs 5 ans + cite prod (bool) ---
print("\nDétail anonymisé (id, départs 5 ans, Q4.4 renseignée, cite production élargi/strict) :")
for i in range(len(df)):
    eid = f"E{i+1:02d}"
    d = q43.iloc[i]
    d_txt = "NA" if pd.isna(d) else f"{d:.0f}"
    print(f"  {eid}: departs5ans={d_txt}, q44_renseignee={bool(mask_rep.iloc[i])}, "
          f"cite_prod={bool(cite_prod.iloc[i])}, cite_prod_strict={bool(cite_prod2.iloc[i])}")
