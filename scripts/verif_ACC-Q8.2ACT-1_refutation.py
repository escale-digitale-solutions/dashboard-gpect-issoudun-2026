# -*- coding: utf-8 -*-
"""
Contre-expertise ACC-Q8.2ACT-1 : le message clé 5 de l'ACCUEIL affirme
« les acteurs de l'emploi se disent disposés à 4,7/5 ».
Vérifie si 4,7 correspond à un seul item de Q8.2 (Campagne de communication
commune) ou à une disposition générale (moyenne des actions collectives).
Aucune donnée en dur ; sortie agrégée anonymisée uniquement.
"""
import re
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/03_acteurs_emploi.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier ACT lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Colonnes Q8.2 (repérées par l'intitulé, pas par index en dur)
q82_cols = [c for c in df.columns if str(c).startswith("Q8.2")]
print(f"Nb de colonnes Q8.2 trouvées : {len(q82_cols)}")


def r1(x):
    return float(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def item_label(col):
    m = re.search(r"\[(.+)\]\s*$", str(col))
    return m.group(1) if m else str(col)


results = {}
for c in q82_cols:
    s = pd.to_numeric(df[c], errors="coerce").dropna()
    lab = item_label(c)
    results[lab] = (s.mean(), len(s), s)
    print(f"  {lab} : moyenne brute={s.mean():.4f} -> {r1(s.mean())} (n={len(s)})")

# Hypothèses de "disposition générale"
actions = {k: v for k, v in results.items()
           if "Aucune participation" not in k}
print(f"\nNb d'actions collectives (hors 'Aucune participation') : {len(actions)}")

# H1 : moyenne des moyennes des 6 actions
mm = sum(v[0] for v in actions.values()) / len(actions)
print(f"H1 moyenne des moyennes des {len(actions)} actions : {mm:.4f} -> {r1(mm)}")

# H2 : moyenne de toutes les notes individuelles des 6 actions (pool)
pool = pd.concat([v[2] for v in actions.values()])
print(f"H2 moyenne poolée ({len(pool)} notes) : {pool.mean():.4f} -> {r1(pool.mean())}")

# H3 : moyenne des 7 items y compris 'Aucune participation'
mm7 = sum(v[0] for v in results.values()) / len(results)
print(f"H3 moyenne des moyennes des {len(results)} items : {mm7:.4f} -> {r1(mm7)}")

# H4 : item max
best = max(results.items(), key=lambda kv: kv[1][0])
print(f"H4 item maximum : '{best[0]}' = {best[1][0]:.4f} -> {r1(best[1][0])} (n={best[1][1]})")

# Contrôle : valeurs distinctes rencontrées (échelle attendue 1-5)
vals = sorted(pd.concat([v[2] for v in results.values()]).unique())
print(f"Valeurs distinctes observées sur Q8.2 : {vals}")
