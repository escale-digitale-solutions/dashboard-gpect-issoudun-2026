# -*- coding: utf-8 -*-
"""
Contre-expertise CROISE / Écart 4 + Risque 1 :
« 136 départs retraite à 5 ans, départs concentrés à 60% sur la production »

Vérifie :
  1. Le total des départs à 5 ans (Q4.3, col 51) = 136 ?
  2. Le 60% : part des ENTREPRISES répondantes à Q4.4 (col 52, texte libre)
     citant la production/fabrication ?
  3. La part des DÉPARTS (Q4.3) portés par ces entreprises — pour trancher
     si « 60% des départs » serait défendable.
Aucune donnée en dur ; sorties agrégées uniquement.
"""
import re
import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col_q43 = df.columns[51]  # Q4.3 départs 5 ans
col_q44 = df.columns[52]  # Q4.4 services/métiers concernés
print(f"[51] {col_q43}")
print(f"[52] {col_q44}")

# ---- 1. Total départs à 5 ans (Q4.3) ----
def to_num(v):
    if pd.isna(v):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", ".")
    m = re.search(r"\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None

q43 = df[col_q43].map(to_num)
n43 = q43.notna().sum()
total43 = q43.dropna().sum()
print(f"\nQ4.3 — n réponses numériques = {n43} ; TOTAL départs 5 ans = {total43:.0f}")

# ---- 2. Q4.4 : entreprises citant production / fabrication ----
q44 = df[col_q44].astype("string")
mask_rep = q44.notna() & (q44.str.strip() != "")
n44 = int(mask_rep.sum())
print(f"\nQ4.4 — réponses non vides : n = {n44}")

pat_prod = re.compile(r"(produc|fabric|atelier|usinage|op[ée]rateur|r[ée]gleur|soud|mont(age|eur))", re.I)
cite_prod = q44.fillna("").map(lambda s: bool(pat_prod.search(s))) & mask_rep
n_prod = int(cite_prod.sum())

# variante stricte : uniquement production/fabrication
pat_strict = re.compile(r"(produc|fabric)", re.I)
cite_strict = q44.fillna("").map(lambda s: bool(pat_strict.search(s))) & mask_rep
n_strict = int(cite_strict.sum())

from decimal import Decimal, ROUND_HALF_UP
def pct(a, b):
    return int(Decimal(a * 100) / Decimal(b) if False else Decimal(str(a * 100 / b)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

print(f"Q4.4 — citent production/fabrication (strict 'produc|fabric') : {n_strict}/{n44} = {pct(n_strict, n44)}%")
print(f"Q4.4 — citent prod. élargie (atelier/usinage/soudure/etc.)    : {n_prod}/{n44} = {pct(n_prod, n44)}%")
print(f"Q4.4 — base collège n=21 (strict) : {n_strict}/21 = {pct(n_strict, 21)}%")

# ---- 3. Part des DÉPARTS portés par les entreprises citant la production ----
dep_strict = q43[cite_strict & q43.notna()].sum()
dep_elargi = q43[cite_prod & q43.notna()].sum()
print(f"\nDéparts Q4.3 portés par les entreprises citant la production (strict) : "
      f"{dep_strict:.0f}/{total43:.0f} = {pct(dep_strict, total43)}%")
print(f"Départs Q4.3 portés par la définition élargie : "
      f"{dep_elargi:.0f}/{total43:.0f} = {pct(dep_elargi, total43)}%")

# Sensibilité : sans le plus gros employeur (effectif max)
col_eff_cands = [c for c in df.columns if re.search(r"effectif|salari", str(c), re.I)]
if col_eff_cands:
    eff = df[col_eff_cands[0]].map(to_num)
    idx_max = eff.idxmax()
    m = df.index != idx_max
    tot_ss = q43[m].dropna().sum()
    dep_ss = q43[m & cite_strict].dropna().sum()
    if tot_ss > 0:
        print(f"\nSans le plus gros employeur : départs prod (strict) = "
              f"{dep_ss:.0f}/{tot_ss:.0f} = {pct(dep_ss, tot_ss)}%")

# ---- Contrôle du découpage : y a-t-il une lecture donnant 60% des départs ? ----
print("\n--- Recherche d'une lecture alternative donnant 60% des 136 départs ---")
print(f"60% de {total43:.0f} = {0.6 * total43:.0f} départs")
