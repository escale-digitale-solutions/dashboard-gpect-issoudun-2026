#!/usr/bin/env python3
"""Contre-expertise SYN Q09 — thème verbatim « Désertification médicale ».

Dashboard : 29% (2/7). Premier auditeur : 14% (1/7).
Recalcul indépendant : on lit la colonne [9] du fichier syndicats
(« principaux freins ou fragilités pour le développement des entreprises
industrielles ») et on compte le nombre de RÉPONDANTS dont la réponse
contient au moins un terme relié à la désertification médicale.

Le script n'imprime que des indicateurs booléens par identifiant anonyme
(S01…S07) + les mots-clés touchés, jamais de verbatim complet dans un
fichier. Aucune donnée en dur dans le script.
"""
import re
import unicodedata

import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/04_syndicats.xlsx"

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()

# Termes larges pour ne rien rater (santé / médical / désert / démographie).
# Regex avec frontière de mot à gauche pour éviter les faux positifs du type
# « insuffiSANTE » qui contiendrait « sante ».
KEYWORDS = [
    r"\bdesert\w*", r"\bmedic\w*", r"\bmedec\w*", r"\bsante\b",
    r"\bhopita\w*", r"\bhospit\w*", r"\bdocteur\w*", r"\bsoins?\b",
    r"\bdemograph\w*", r"\bvieilli\w*",
]

def main() -> None:
    df = pd.read_excel(SRC, engine="openpyxl")
    print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")
    col = df.columns[9]
    print(f"Colonne [9] : {col!r}")
    serie = df[col]
    n_nonvide = serie.notna().sum()
    print(f"Réponses non vides (n=) : {n_nonvide}")

    hits = 0
    for i, val in enumerate(serie):
        rid = f"S{i+1:02d}"
        if pd.isna(val) or not str(val).strip():
            print(f"  {rid} : (vide)")
            continue
        t = norm(str(val))
        matched = sorted({kw for kw in KEYWORDS if re.search(kw, t)})
        if matched:
            hits += 1
            # contexte court (fenêtre de 40 caractères autour du 1er match)
            m = re.search("|".join(matched), t)
            ctx = t[max(0, m.start() - 25): m.end() + 25].replace("\n", " ")
            print(f"  {rid} : MATCH  mots-cles={matched}  contexte=…{ctx}…")
        else:
            print(f"  {rid} : aucun terme sante/medical/demographie")

    pct = round(100 * hits / n_nonvide) if n_nonvide else 0
    print(f"\nRépondants mentionnant le thème : {hits}/{n_nonvide} = {pct}%")

if __name__ == "__main__":
    main()
