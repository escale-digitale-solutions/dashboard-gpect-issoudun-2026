# -*- coding: utf-8 -*-
"""
Contre-expertise ENT Q4.4 — « Services concentrant les départs en retraite »
Dashboard (block bars Q4.4, n=20) : Conduite / transport = 20 %.
Premier auditeur : 5/20 = 25 %.
Recalcul indépendant depuis data/01_entreprises.xlsx (export 30/06/2026).

Méthode :
- colonne source : index 52 « Q4.4 — Sur quels services ou métiers ces
  départs à la retraite vont-ils se concentrer ? »
- n = réponses non vides.
- Items « cases à cocher » : un répondant compte pour une option si le
  libellé exact de l'option apparaît dans sa cellule (les options Google
  Forms ne contiennent pas de virgule ici, le split n'est pas nécessaire ;
  on teste l'inclusion du libellé).
- Item « Conduite / transport » : catégorie recodée à partir du texte
  libre (« Autre ») — codée si la cellule mentionne la conduite ou les
  conducteurs/chauffeurs (mots-clés ci-dessous, insensible à la casse).
- % arrondi à l'entier, round half up, base = répondants à la question.
Aucune donnée en dur dans ce script ; sortie agrégée et anonymisée.
"""
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
COL_IDX = 52  # Q4.4

# Items « cases à cocher » du graphique dashboard : libellé affiché -> libellé Forms
CHECKBOX_ITEMS = {
    "Production / fabrication": "Production / Fabrication",
    "Logistique": "Logistique",
    "Commerce / ADV": "Commerce / ADV",
    "Qualité": "Qualité",
    "Maintenance": "Maintenance",
    "Bureau d'études": "Bureau d'études",
    "Management de proximité": "Management de proximité",
}

# Codage du thème « Conduite / transport » (réponses libres) :
# racines de mots, comparées sans accents et sans casse.
CONDUITE_KEYWORDS = ["conducteur", "chauffeur", "conduite"]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def pct(k: int, n: int) -> int:
    """% arrondi à l'entier, round half up (convention dashboard)."""
    return int((Decimal(k) * 100 / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def main():
    df = pd.read_excel(XLSX, engine="openpyxl")
    print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")
    col = df.columns[COL_IDX]
    print(f"Colonne [{COL_IDX}] : {col}")

    s = df[col].dropna().astype(str).str.strip()
    s = s[s != ""]
    n = len(s)
    print(f"n (réponses non vides) = {n}\n")

    print("Item du graphique                | effectif | %  | dashboard")
    print("-" * 62)
    dash = {  # valeurs affichées par le dashboard (v12) pour comparaison
        "Production / fabrication": 60, "Logistique": 25, "Commerce / ADV": 25,
        "Conduite / transport": 20, "Qualité": 15, "Maintenance": 15,
        "Bureau d'études": 15, "Management de proximité": 15,
    }
    for label, needle in CHECKBOX_ITEMS.items():
        k = int(s.str.contains(re.escape(needle), case=True, regex=True).sum())
        p = pct(k, n)
        flag = "OK" if p == dash[label] else f"ECART (dash={dash[label]})"
        print(f"{label:<32} | {k:>2}/{n}    | {p:>2} | {flag}")

    # Thème recodé « Conduite / transport »
    mask = s.map(lambda v: any(kw in norm(v) for kw in CONDUITE_KEYWORDS))
    k = int(mask.sum())
    p = pct(k, n)
    flag = "OK" if p == dash["Conduite / transport"] else f"ECART (dash={dash['Conduite / transport']})"
    print(f"{'Conduite / transport (recode)':<32} | {k:>2}/{n}    | {p:>2} | {flag}")

    # Traçabilité anonyme : identifiants ligne (E01 = 1re ligne de données)
    ids = [f"E{df.index.get_loc(i) + 1:02d}" for i in s[mask].index]
    print(f"\nRépondants codés Conduite / transport (identifiants anonymes) : {', '.join(ids)}")
    print("Mots-clés de codage :", ", ".join(CONDUITE_KEYWORDS))


if __name__ == "__main__":
    main()
