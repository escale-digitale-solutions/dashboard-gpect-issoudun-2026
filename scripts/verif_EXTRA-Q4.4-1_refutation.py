# -*- coding: utf-8 -*-
"""
Contre-expertise EXTRA — Levier 5 + fiche D1 : « 136 départs à 5 ans (60% en production) »
Vérifie :
  1. Q4.3 (départs retraite à 5 ans) : le cumul déclaré vaut-il 136 ?
  2. Q4.4 (services concentrant les départs, choix multiple) :
     - n = répondants non vides
     - part des ENTREPRISES citant Production / fabrication (base répondants)
     - part des CITATIONS "production" (base citations) pour tester l'hypothèse alternative
  3. La donnée permet-elle de calculer une part des 136 DÉPARTS en production ? (non : Q4.4
     ne ventile pas les effectifs de départs par service)
Sortie agrégée uniquement (aucun verbatim, aucune donnée nominative).
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"

def pct(num, den):
    return int(Decimal(num) / Decimal(den) * 100).__str__() if False else int(
        (Decimal(num) * 100 / Decimal(den)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

df = pd.read_excel(XLSX, engine="openpyxl")
print(f"Fichier : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col_q43 = df.columns[51]
col_q44 = df.columns[52]
print(f"\nColonne [51] : {col_q43}")
print(f"Colonne [52] : {col_q44}")

# --- 1. Cumul Q4.3 ---
q43 = pd.to_numeric(df[col_q43], errors="coerce")
print(f"\nQ4.3 — n non vides = {q43.notna().sum()} ; cumul = {q43.sum():.0f} ; "
      f"valeurs numeriques distinctes = {sorted(q43.dropna().unique().tolist())}")

# --- 2. Q4.4 choix multiple ---
s = df[col_q44].dropna().astype(str).str.strip()
s = s[s != ""]
n = len(s)
print(f"\nQ4.4 — n répondants non vides = {n} / {len(df)}")

# Inspection des valeurs : longueur et nb de segments (pas de contenu libre imprimé,
# la question est à options fermées Google Forms ; on n'imprime que les options agrégées)
from collections import Counter
tokens = Counter()
for v in s:
    for t in v.split(", "):
        tokens[t.strip()] += 1
print("\nOptions détectées (split ', ') et fréquences :")
for t, c in tokens.most_common():
    print(f"  {c:2d}  {t}")

# Comptage robuste par 'contains' pour la production
mask_prod = s.str.contains("roduction") | s.str.contains("abrication")
n_prod = int(mask_prod.sum())
total_citations = sum(tokens.values())
print(f"\nEntreprises citant Production/fabrication : {n_prod}")
print(f"  base répondants : {n_prod}/{n} = {pct(n_prod, n)}%")
print(f"  base collège    : {n_prod}/{len(df)} = {pct(n_prod, len(df))}%")
cit_prod = sum(c for t, c in tokens.items() if "roduction" in t or "abrication" in t)
print(f"  base citations  : {cit_prod}/{total_citations} = {pct(cit_prod, total_citations)}%")

# --- 3. Part des 136 départs situés en production : calculable ? ---
# Q4.4 est un choix multiple de services, sans ventilation numérique des départs.
# On teste néanmoins : somme des départs Q4.3 des répondants citant la production.
q43_prod = pd.to_numeric(df.loc[mask_prod.index[mask_prod], col_q43], errors="coerce")
tot = q43.sum()
print(f"\nDéparts Q4.3 déclarés par les entreprises citant la production : "
      f"{q43_prod.sum():.0f}/{tot:.0f} = {pct(int(q43_prod.sum()), int(tot))}% "
      "(≠ ventilation réelle par service : donnée non collectée)")

# Vérif dashboard : items affichés page ENT (Q4.4, n=20)
DASH = {"Production / fabrication": 60, "Logistique": 25, "Commerce / ADV": 25,
        "Conduite / transport": 20, "Qualité": 15, "Maintenance": 15,
        "Bureau d'études": 15, "Management de proximité": 15}
print("\nContrôle des autres barres (contains, base répondants n=%d) :" % n)
probes = {"Logistique": ["ogistique"], "Commerce / ADV": ["ommerc", "ADV"],
          "Conduite / transport": ["onduite", "ransport"], "Qualité": ["ualit"],
          "Maintenance": ["aintenance"], "Bureau d'études": ["tude"],
          "Management de proximité": ["anagement", "ncadrement", "roximit"]}
for lab, pats in probes.items():
    m = pd.Series(False, index=s.index)
    for p in pats:
        m |= s.str.contains(p)
    print(f"  {lab:28s} {int(m.sum()):2d}/{n} = {pct(int(m.sum()), n):3d}%  (dashboard {DASH[lab]}%)")
