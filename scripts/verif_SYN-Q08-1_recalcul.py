#!/usr/bin/env python3
"""
Contre-expertise SYN Q08 — thème verbatim « Foncier disponible / prix »
(atouts du territoire, collège Syndicats).

Dashboard : 43% (3/7). Premier auditeur : 57% (4/7).

Colonne source : index 8 du fichier data/04_syndicats.xlsx
« Selon vous, quels sont les principaux atouts du territoire pour
l'industrie et les TPE/PME ? »

Le script :
- compte les réponses non vides (n),
- détecte par regex les occurrences de la racine « fonci » (foncier,
  foncière...) dans chaque réponse (insensible à la casse/accents),
- affiche par répondant (S01..S07) un booléen + une fenêtre de contexte
  courte autour du mot détecté (contrôle du sens : atout foncier vs autre),
- calcule le % correspondant (round half up, base répondants).
Aucune donnée nominative ni verbatim complet n'est écrit dans un fichier.
"""
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

PATH = "/home/user/dashboard-gpect-issoudun-2026/data/04_syndicats.xlsx"

df = pd.read_excel(PATH, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col = df.columns[8]
print(f"Colonne [8] : {col!r}\n")

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()

serie = df[col]
n_nonvide = serie.apply(lambda v: isinstance(v, str) and v.strip() != "" or (pd.notna(v) and not isinstance(v, str))).sum()
print(f"n (réponses non vides) = {n_nonvide} / {len(serie)}\n")

pattern = re.compile(r"fonci")
hits = 0
for i, v in enumerate(serie, start=1):
    rid = f"S{i:02d}"
    if not isinstance(v, str) or not v.strip():
        print(f"{rid}: (vide)")
        continue
    t = norm(v)
    matches = list(pattern.finditer(t))
    if matches:
        hits += 1
        for m in matches:
            a, b = max(0, m.start() - 30), min(len(t), m.end() + 35)
            print(f"{rid}: FONCIER  …{t[a:b]}…")
    else:
        print(f"{rid}: —")

pct = Decimal(hits * 100) / Decimal(int(n_nonvide))
pct = int(pct.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
print(f"\nThème « foncier » : {hits}/{int(n_nonvide)} = {pct}%")
print(f"Dashboard : 43% (3/7) | Auditeur 1 : 57% (4/7)")
