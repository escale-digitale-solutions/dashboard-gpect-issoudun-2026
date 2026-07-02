# -*- coding: utf-8 -*-
"""
Contre-expertise ACC-KPI-1 : KPI accueil « 2,3/5 Image du bassin »
sous-titré « note la plus basse du diagnostic (Ent. Q8.2) ».
Vérifie :
  1. la moyenne Q8.2 entreprises (col 111) ;
  2. la moyenne AFEST entreprises (col 66) et cybersécurité OF (col 39) ;
  3. le minimum de toutes les moyennes sur échelles 1-5 des 4 fichiers.
Aucune donnée en dur ; sortie agrégée uniquement.
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

DATA = "/home/user/dashboard-gpect-issoudun-2026/data/"
FILES = {
    "ENT": DATA + "01_entreprises.xlsx",
    "OF":  DATA + "02_organismes_formation.xlsx",
    "ACT": DATA + "03_acteurs_emploi.xlsx",
    "SYN": DATA + "04_syndicats.xlsx",
}

def r1(x):  # arrondi half-up a 1 decimale (convention dashboard)
    return float(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

dfs = {k: pd.read_excel(v, engine="openpyxl") for k, v in FILES.items()}
for k, df in dfs.items():
    print(f"{k}: {df.shape[0]} lignes x {df.shape[1]} colonnes")

def scale_mean(df, idx):
    s = pd.to_numeric(df.iloc[:, idx], errors="coerce").dropna()
    return s.mean(), len(s), s.min(), s.max()

# --- 1. Les 3 KPI cites ---
targets = [
    ("ENT", 111, "Q8.2 image bassin"),
    ("ENT", 66,  "Q4.8 AFEST"),
    ("OF",  39,  "Q2.2 cybersecurite"),
]
print("\n--- KPI cites ---")
for col, idx, label in targets:
    m, n, lo, hi = scale_mean(dfs[col], idx)
    print(f"{col} col[{idx}] {label} : moyenne brute={m:.4f} -> {r1(m)}/5 (n={n}, min={lo}, max={hi})")

# --- 2. Balayage : toutes colonnes numeriques bornees dans [1,5] ---
print("\n--- Balayage echelles 1-5 : moyennes <= 2.3 ---")
results = []
for cname, df in dfs.items():
    for i in range(df.shape[1]):
        s = pd.to_numeric(df.iloc[:, i], errors="coerce").dropna()
        if len(s) < 3:
            continue
        # echelle 1-5 plausible : valeurs entieres entre 1 et 5, au moins une <=5 et >=1
        if s.min() >= 1 and s.max() <= 5 and (s == s.round()).all() and s.max() > 1:
            results.append((cname, i, str(df.columns[i])[:90], s.mean(), len(s)))

results.sort(key=lambda t: t[3])
for cname, i, head, m, n in results:
    if m <= 2.3:
        print(f"{cname} col[{i}] moy={r1(m)}/5 (brut {m:.3f}, n={n}) | {head}")

low = results[0]
print(f"\nMinimum absolu du balayage : {low[0]} col[{low[1]}] = {r1(low[3])}/5 (n={low[4]})")
