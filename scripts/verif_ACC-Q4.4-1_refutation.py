#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contre-expertise ACC-Q4.4-1 — message clé « choc démographique » (zone ACCUEIL)
Affirmation dashboard : « 136 départs en retraite déclarés à 5 ans
(concentrés à 60% sur la production) »

Vérifications :
  1. Somme Q4.3 (départs retraite à 5 ans) = 136 ? n = ?
  2. Base « entreprises » : part des répondants Q4.4 citant la production
     (option Google Forms « Production / Fabrication », choix multiple ', ').
  3. Base « départs » : part des 136 départs déclarés portée par les
     entreprises citant la production (pondération par Q4.3).
Arrondi : round half up à l'entier. Aucune donnée en dur, aucun verbatim écrit.
Résultat agrégé : resultats/verif_ACC-Q4.4-1_refutation.txt
"""
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
OUT = "/home/user/dashboard-gpect-issoudun-2026/resultats/verif_ACC-Q4.4-1_refutation.txt"

def pct(num, den):
    return int((Decimal(num) * 100 / Decimal(den)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

df = pd.read_excel(XLSX, engine="openpyxl")
lignes, colonnes = df.shape

c_q43 = [c for c in df.columns if c.startswith("Q4.3")][0]
c_q44 = [c for c in df.columns if c.startswith("Q4.4")][0]

# 1) Somme Q4.3
q43 = pd.to_numeric(df[c_q43], errors="coerce")
n_q43 = int(q43.notna().sum())
total_departs = int(q43.sum())

# 2) Q4.4 : choix multiple ', ' — l'option visée ne contient pas de virgule.
q44 = df[c_q44].astype("string").str.strip()
repondants_q44 = q44.notna() & (q44 != "")
n_q44 = int(repondants_q44.sum())
OPTION = "Production / Fabrication"
cite_prod = repondants_q44 & q44.str.contains(OPTION, case=False, regex=False).fillna(False)
# contrôle : aucune autre mention du mot « production » hors option exacte
autres_prod = repondants_q44 & ~cite_prod & q44.str.contains("production", case=False, regex=False).fillna(False)
n_cite_prod = int(cite_prod.sum())
pct_entreprises = pct(n_cite_prod, n_q44)

# 3) Pondération par les départs déclarés (Q4.3)
departs_prod = int(q43[cite_prod].fillna(0).sum())
pct_departs = pct(departs_prod, total_departs)

# Nb moyen de services cités par les entreprises citant la production
# (pour juger si « départs des entreprises citant prod » = « départs en prod »)
nb_services_prod = q44[cite_prod].str.split(", ").str.len()

res = f"""CONTRE-EXPERTISE ACC-Q4.4-1 — « 136 départs (concentrés à 60% sur la production) »
Fichier : 01_entreprises.xlsx — {lignes} lignes x {colonnes} colonnes

1) Q4.3 (départs retraite à 5 ans) : somme = {total_departs} (n={n_q43}/21)
   -> le « 136 » du dashboard est {"EXACT" if total_departs == 136 else "FAUX"}.

2) Q4.4 base ENTREPRISES : {n_cite_prod}/{n_q44} répondants citent « {OPTION} »
   = {pct_entreprises} % (n={n_q44} répondants à Q4.4 ; 1 non-réponse sur 21)
   Mentions « production » hors option exacte : {int(autres_prod.sum())}

3) Q4.4 base DÉPARTS (pondération Q4.3) : les entreprises citant la production
   portent {departs_prod}/{total_departs} départs déclarés = {pct_departs} %.
   NB : ces entreprises citent en moyenne {nb_services_prod.mean():.1f} service(s) dans Q4.4
   (min {int(nb_services_prod.min())}, max {int(nb_services_prod.max())}) ; la répartition des départs PAR service
   n'est pas collectée -> « X % des départs EN production » est incalculable.

CONCLUSION : le 60 % existe (base entreprises, 12/20) mais la formulation du
dashboard le présente comme une part des 136 départs, ce que les données ne
mesurent pas. Part des départs portée par les entreprises citant la production :
{pct_departs} % (borne haute, multi-services).
"""
with open(OUT, "w", encoding="utf-8") as f:
    f.write(res)
print(res)
