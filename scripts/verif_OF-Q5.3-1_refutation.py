# -*- coding: utf-8 -*-
"""
Contre-expertise OF Q5.3 — Freins au déploiement de l'AFEST (choix multiple).
Écart signalé : dashboard affiche n=7 et % sur base 7 (43/29/29/14/14) ;
le premier auditeur soutient que 2 des 7 cellules non vides ne contiennent
aucune option officielle (une réponse 'na', une réponse texte libre seule),
soit 5 répondants "exploitables".

Le script :
1. identifie la colonne Q5.3 (et la colonne 'Autres freins' voisine) ;
2. affiche la STRUCTURE anonymisée des cellules (longueur, découpage par
   options officielles, résidu oui/non — jamais le contenu brut) ;
3. recompte chaque option sur base n=7 (cellules non vides) et sur base
   n=5 (répondants ayant coché >=1 option officielle) ;
4. compare aux valeurs du dashboard avec arrondi round-half-up.
Aucune donnée nominative ni verbatim n'est imprimé.
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

F = "/home/user/dashboard-gpect-issoudun-2026/data/02_organismes_formation.xlsx"
df = pd.read_excel(F, engine="openpyxl")
print(f"Fichier OF lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col = df.columns[62]
col_autre = df.columns[63]
print(f"\nColonne [62] : {col}")
print(f"Colonne [63] : {col_autre}")
assert "AFEST" in col and "freins" in col, "Mauvaise colonne ?"

# Options officielles telles qu'affichées par le dashboard (libellés courts)
# -> on cherche les libellés Google Forms réels par sous-chaînes robustes
DASH = {
    "Résistance / méconnaissance des entreprises": 43,
    "Complexité du référentiel & traçabilité": 29,
    "Absence de modèle économique viable": 29,
    "Difficulté à identifier les situations apprenantes": 14,
    "Méconnaissance par les OPCO locaux": 14,
}
# Sous-chaînes discriminantes (insensibles aux libellés longs du Forms)
KEYS = {
    "Résistance / méconnaissance des entreprises": ["ntreprise"],
    "Complexité du référentiel & traçabilité": ["éférentiel", "raçabilit"],
    "Absence de modèle économique viable": ["conomique"],
    "Difficulté à identifier les situations apprenantes": ["apprenant"],
    "Méconnaissance par les OPCO locaux": ["OPCO"],
}

s = df[col]
nonvide = s.dropna().astype(str)
nonvide = nonvide[nonvide.str.strip() != ""]
print(f"\nCellules non vides : {len(nonvide)} / {len(s)}")

def rhu(x):
    return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

# Structure anonymisée de chaque cellule
print("\n--- Structure des cellules (anonymisée) ---")
compte = {lab: 0 for lab in DASH}
n_avec_option = 0
n_sans_option = 0
for i, (idx, val) in enumerate(nonvide.items(), 1):
    hits = []
    for lab, keys in KEYS.items():
        if any(k.lower() in val.lower() for k in keys):
            hits.append(lab)
            compte[lab] += 1
    est_na = val.strip().lower() in ("na", "n/a", "aucun", "aucune", "-", ".")
    if hits:
        n_avec_option += 1
    else:
        n_sans_option += 1
    print(f"OF{i:02d} : longueur={len(val)} car., options officielles matchées="
          f"{len(hits)}, cellule=='na'-like : {est_na}, "
          f"texte hors options : {'oui' if (not hits and not est_na) else ('na seul' if est_na else 'non')}")

print(f"\nRépondants ayant coché >=1 option officielle : {n_avec_option}")
print(f"Répondants non vides SANS option officielle    : {n_sans_option}")

# Colonne 'Autres freins, précisez'
autre_nonvide = df[col_autre].dropna().astype(str)
autre_nonvide = autre_nonvide[autre_nonvide.str.strip() != ""]
print(f"Colonne [63] 'Autres freins, précisez' : {len(autre_nonvide)} réponses non vides (contenu non affiché)")

print("\n--- Comparaison des bases ---")
print(f"{'Option':55s} {'brut':>4s} {'%/7':>5s} {'dash':>5s} {'ok?':>4s} {'%/5':>5s}")
tout_ok = True
for lab, vdash in DASH.items():
    c = compte[lab]
    p7 = rhu(c / 7 * 100)
    p5 = rhu(c / n_avec_option * 100) if n_avec_option else None
    ok = (p7 == vdash)
    tout_ok &= ok
    print(f"{lab:55s} {c:4d} {p7:4d}% {vdash:4d}% {'OUI' if ok else 'NON':>4s} {p5:4d}%")

print(f"\nDashboard exact sur base n=7 (cellules non vides) : {tout_ok}")
