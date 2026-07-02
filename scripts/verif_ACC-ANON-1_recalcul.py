#!/usr/bin/env python3
"""Contre-expertise ACC-ANON-1 : poids du plus gros employeur dans Q1.4.

Recalcule, à partir de data/01_entreprises.xlsx (export 30/06/2026) :
- n (réponses non vides à Q1.4 — Effectif inscrit CDI+CDD),
- effectif max,
- effectif cumulé,
- part du max dans le cumul (%, round half up).

Aucune donnée nominative n'est lue ni écrite : seule la colonne
d'effectif (numérique) est exploitée. Résultats agrégés uniquement.
"""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "01_entreprises.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier lu : {SRC.name} — {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Identification de la colonne Q1.4 par son intitulé (pas par index en dur)
cands = [c for c in df.columns if "Effectif inscrit" in str(c)]
assert len(cands) == 1, f"Colonne Q1.4 ambigüe : {cands}"
col = cands[0]
print(f"Colonne source : {col!r}")

s = pd.to_numeric(df[col], errors="coerce").dropna()
n = len(s)
vmax = s.max()
total = s.sum()
part = Decimal(str(100 * vmax / total)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
total_sans_max = total - vmax

print(f"n (réponses non vides Q1.4) = {n}")
print(f"Effectif max déclaré        = {vmax:.0f}")
print(f"Effectif cumulé             = {total:.0f}")
print(f"Effectif cumulé SANS le max = {total_sans_max:.0f}")
print(f"Part du max dans le cumul   = {part} %")

out = REPO / "resultats" / "verif_ACC-ANON-1_recalcul.txt"
out.parent.mkdir(exist_ok=True)
out.write_text(
    "Contre-expertise ACC-ANON-1 — Q1.4 Effectif inscrit (CDI+CDD), "
    "college Entreprises\n"
    f"n = {n}\n"
    f"effectif_max = {vmax:.0f}\n"
    f"effectif_cumule = {total:.0f}\n"
    f"effectif_cumule_sans_max = {total_sans_max:.0f}\n"
    f"part_max_pct = {part} %\n",
    encoding="utf-8",
)
print(f"Résultats agrégés écrits dans {out}")
