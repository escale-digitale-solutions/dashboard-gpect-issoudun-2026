#!/usr/bin/env python3
"""Contre-expertise OF Q2.1 — Niveau de l'offre de formation par domaine.

Recalcule de zéro les moyennes de TOUTES les sous-questions Q2.1 du
questionnaire Organismes de formation (échelle 1-5), pour vérifier :
- les 10 moyennes affichées par le dashboard,
- l'existence éventuelle de domaines omis et leur classement.

Aucune donnée en dur ; les colonnes sont identifiées par leur préfixe
« Q2.1 » dans les intitulés du xlsx. Sortie : agrégats anonymisés
(moyennes à 1 décimale, n=), affichés en console.
"""
import re
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/02_organismes_formation.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

q21_cols = [c for c in df.columns if str(c).startswith("Q2.1")]
print(f"Nombre de sous-questions Q2.1 trouvées : {len(q21_cols)}")

def label(col):
    m = re.search(r"\[(.+)\]\s*$", str(col))
    return m.group(1) if m else str(col)

rows = []
for col in q21_cols:
    s = pd.to_numeric(df[col], errors="coerce")
    n = int(s.notna().sum())
    # contrôle : valeurs hors échelle 1-5 ?
    bad = s.dropna()[(s.dropna() < 1) | (s.dropna() > 5)]
    if len(bad):
        print(f"  ATTENTION valeurs hors échelle dans « {label(col)} »")
    mean = s.mean()
    mean_r = float(Decimal(str(mean)).quantize(Decimal("0.1"), ROUND_HALF_UP)) if n else None
    rows.append({"domaine": label(col), "n": n, "moyenne": mean_r, "moyenne_brute": round(float(mean), 4) if n else None})

out = pd.DataFrame(rows).sort_values(["moyenne", "domaine"], ascending=[False, True])
print("\nClassement complet Q2.1 (moyenne 1-5, arrondi 1 décimale, round half up) :")
for _, r in out.iterrows():
    print(f"  {r['moyenne']:.1f} (n={r['n']}, brute={r['moyenne_brute']})  {r['domaine']}")
