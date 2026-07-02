# -*- coding: utf-8 -*-
"""
Contre-expertise Écart 4 (zone CROISE du dashboard) :
« Transmission/seniors = priorité GPECT la plus basse (2,5/5) »
Le premier auditeur affirme un ex æquo avec « Mutualisation inter-entreprises »
(2,48 chacun). On recalcule les moyennes des 8 sous-items de Q9.1 (entreprises)
avec la convention dashboard : moyenne à 1 décimale, n = réponses non vides.
Aucune donnée nominative n'est lue ni affichée : seules les colonnes Q9.1
(échelles 1-5) sont exploitées.
"""
import re
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier entreprises : {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Colonnes Q9.1 (matrice de priorités GPECT, échelle 1-5)
cols = [c for c in df.columns if str(c).startswith("Q9.1")]
print(f"Colonnes Q9.1 trouvées : {len(cols)}")

def label(col):
    m = re.search(r"\[(.+)\]\s*$", str(col))
    return m.group(1) if m else str(col)

def r1(x):
    return Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

rows = []
for c in cols:
    s = pd.to_numeric(df[c], errors="coerce").dropna()
    rows.append({
        "thematique": label(c),
        "n": int(s.shape[0]),
        "moyenne_brute": round(float(s.mean()), 4),
        "moyenne_1dec": float(r1(s.mean())),
        "somme": float(s.sum()),
        "hors_echelle_1_5": int(((s < 1) | (s > 5)).sum()),
    })

res = pd.DataFrame(rows).sort_values("moyenne_brute").reset_index(drop=True)
print("\nClassement Q9.1 (entreprises), du plus bas au plus haut :")
print(res.to_string(index=False))

mini = res["moyenne_brute"].min()
exaequo = res[res["moyenne_brute"] == mini]
print(f"\nMinimum brut = {mini} atteint par {len(exaequo)} thématique(s) :")
for _, r in exaequo.iterrows():
    print(f"  - {r['thematique']} : brute {r['moyenne_brute']}, "
          f"affichée {r['moyenne_1dec']}, n={r['n']}")

mini_aff = res["moyenne_1dec"].min()
exaequo_aff = res[res["moyenne_1dec"] == mini_aff]
print(f"\nMinimum affiché (1 déc.) = {mini_aff} atteint par "
      f"{len(exaequo_aff)} thématique(s) : "
      + " | ".join(exaequo_aff["thematique"].tolist()))
