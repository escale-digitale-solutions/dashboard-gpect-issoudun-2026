# -*- coding: utf-8 -*-
"""
Contre-expertise ACC-Q4.4-1 — message clé accueil « choc démographique » :
« 136 départs en retraite déclarés à 5 ans (concentrés à 60% sur la production) »

Vérifie :
  1. la somme des départs à 5 ans (Q4.3, col index 51) ;
  2. la part des entreprises répondantes à Q4.4 (col index 52) citant la
     production (ou un métier de production) parmi les services/métiers
     concernés par ces départs ;
  3. la part des DÉPARTS (Q4.3) portés par les entreprises citant la
     production dans Q4.4.
Sortie : agrégats anonymisés uniquement (aucun verbatim imprimé, seulement
des catégories thématiques détectées par mots-clés).
"""
import re
import unicodedata
import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col_q43 = df.columns[51]
col_q44 = df.columns[52]
print(f"Q4.3 (index 51) : {col_q43[:80]}")
print(f"Q4.4 (index 52) : {col_q44[:80]}")

# --- 1. Somme des départs à 5 ans (Q4.3) ---
q43 = pd.to_numeric(df[col_q43], errors="coerce")
n_q43 = int(q43.notna().sum())
total_departs = q43.sum()
print(f"\nQ4.3 — n={n_q43} réponses numériques, somme = {total_departs:.0f}")

# --- 2. Q4.4 : entreprises citant la production ---
def norm(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    return s.lower()

# Mots-clés « production » au sens large (cœur technique/atelier),
# alignés sur la lecture dashboard : production, usinage, fabrication,
# atelier, opérateur, régleur, soudure/soudeur, maintenance exclue par défaut
KW_PROD_STRICT = ["production"]
KW_PROD_LARGE = ["production", "usinage", "fabrication", "atelier",
                 "operateur", "regleur", "soudeur", "soudure", "montage",
                 "conducteur de ligne", "mecanicien", "mecanique"]

q44_raw = df[col_q44]
mask_answered = q44_raw.notna() & (q44_raw.astype(str).str.strip() != "")
n_q44 = int(mask_answered.sum())
print(f"\nQ4.4 — n={n_q44} réponses non vides sur {len(df)}")

q44_norm = q44_raw.where(mask_answered).map(lambda v: norm(v) if pd.notna(v) else "")

def cites(kws):
    return q44_norm.map(lambda t: any(k in t for k in kws)) & mask_answered

mask_strict = cites(KW_PROD_STRICT)
mask_large = cites(KW_PROD_LARGE)

for label, m in [("mot 'production' strict", mask_strict),
                 ("production au sens large", mask_large)]:
    n_cit = int(m.sum())
    pct_ent = 100 * n_cit / n_q44
    departs_cit = q43[m].sum()
    pct_dep = 100 * departs_cit / total_departs if total_departs else float("nan")
    print(f"\n[{label}]")
    print(f"  Entreprises citant : {n_cit}/{n_q44} = {pct_ent:.1f}% des répondants Q4.4")
    print(f"  Départs Q4.3 portés par ces entreprises : {departs_cit:.0f}/{total_departs:.0f} "
          f"= {pct_dep:.1f}% des départs déclarés")

# --- 3. Contrôle sensibilité : agrégat sans le plus gros employeur ---
# (règle CLAUDE.md §5.4) — identifié par le max de l'effectif si colonne trouvée
eff_best = None
for c in df.columns:
    if "effectif" in norm(c):
        s = pd.to_numeric(df[c], errors="coerce")
        if s.notna().sum() and (eff_best is None or s.max() > eff_best.max()):
            eff_best = s
if eff_best is not None and eff_best.max() > 1000:
    eff = eff_best
    idx_max = eff.idxmax()
    m2 = mask_large.copy()
    q43_sans = q43.drop(idx_max)
    tot_sans = q43_sans.sum()
    dep_cit_sans = q43[m2].drop(idx_max, errors="ignore").sum()
    print(f"\n[Sensibilité] hors plus gros employeur : total départs = {tot_sans:.0f} ; "
          f"départs portés par entreprises citant production (large) = {dep_cit_sans:.0f} "
          f"({100*dep_cit_sans/tot_sans:.1f}%)" if tot_sans else "")

# --- 4. Distribution des départs Q4.3 (contrôle de concentration, anonyme) ---
top = q43.dropna().sort_values(ascending=False).head(5).tolist()
print(f"\nTop 5 valeurs Q4.3 (anonyme) : {[int(v) for v in top]}")
