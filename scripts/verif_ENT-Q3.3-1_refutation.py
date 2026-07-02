# -*- coding: utf-8 -*-
"""
Contre-expertise ECART ENT-Q3.3-1
Dashboard : Q3.3 (n=20) — « Déficit d'image du métier / secteur » affiché 3,1.
Premier auditeur : moyenne = 3,15 (n=20) -> 3,2 en round half up.
Objectif : réfuter ou confirmer, en testant :
  - la bonne colonne (Q3.3 item image, index 28) vs colonne piège Q5.3 (index 79)
  - la base de calcul (n non-vides de l'item vs n=21 du collège)
  - la convention d'arrondi (Decimal ROUND_HALF_UP exact vs round() flottant)
Aucune donnée individuelle n'est imprimée : uniquement n, somme, moyennes.
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Valeurs affichées par le dashboard (block_3.js, bloc scale Q3.3, n=20)
DASH_Q33 = {
    "Pénurie de candidats sur le marché local": 4.5,
    "Inadéquation des compétences ou des diplômes des candidats": 3.1,
    "Déficit d'image du métier ou du secteur": 3.1,
    "Concurrence salariale d'autres entreprises ou secteurs": 3.7,
    "Contraintes liées au Logement": 1.7,
    "Contraintes liées au Transport": 2.5,
    "Contraintes liées à l'Emploi du conjoint": 1.6,
    "Contraintes liées à la Garde d'enfant": 1.5,
    "Contraintes liées à la Localisation de l'entreprise": 2.8,
    "Délais de formation initiale trop longs par rapport aux besoins": 2.4,
}

def arrondis(serie):
    """Retourne (n, somme, moyenne exacte, RHU décimal exact, round() flottant)."""
    s = pd.to_numeric(serie, errors="coerce").dropna()
    n = int(s.count())
    somme = s.sum()
    if n == 0:
        return n, somme, None, None, None
    # Arrondi half-up sur la valeur EXACTE (fraction somme/n en Decimal)
    exact = Decimal(str(somme)) / Decimal(n)
    rhu = exact.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    # Arrondi Python natif sur le flottant (banker's + représentation binaire)
    rfloat = round(float(somme) / n, 1)
    return n, somme, exact, rhu, rfloat

q33_cols = [c for c in df.columns if str(c).startswith("Q3.3")]
print(f"\nColonnes Q3.3 trouvées : {len(q33_cols)}")

print("\n=== Q3.3 — toutes les sous-échelles (base : répondants non vides à l'item) ===")
for c in q33_cols:
    item = c.split("[")[-1].rstrip("]")
    n, somme, exact, rhu, rfloat = arrondis(df[c])
    dash = DASH_Q33.get(item, "?")
    ok = "OK" if dash != "?" and float(rhu) == dash else "ECART"
    print(f"  {item[:62]:<62} n={n:>2} somme={somme:>5.0f} "
          f"moy_exacte={float(exact):.6f} RHU={rhu} round()={rfloat} dash={dash} -> {ok}")

# Focus item litigieux
col_img = [c for c in q33_cols if "image" in str(c).lower()]
assert len(col_img) == 1, "colonne image Q3.3 non unique"
col_img = col_img[0]
n, somme, exact, rhu, rfloat = arrondis(df[col_img])
print("\n=== FOCUS : Q3.3 [Déficit d'image du métier ou du secteur] ===")
print(f"  n (non vides) = {n} ; somme = {somme:.0f} ; moyenne exacte = {float(exact):.10f}")
print(f"  Arrondi ROUND_HALF_UP (Decimal, valeur exacte) : {rhu}")
print(f"  Arrondi round() Python sur flottant            : {rfloat}")
print(f"  Dashboard : 3,1 ; premier auditeur : 3,15 -> 3,2")

# Hypothèse 'mauvaise base' : moyenne sur n=21 (blancs = 0 ou exclus)
s_all = pd.to_numeric(df[col_img], errors="coerce")
if df.shape[0] != n:
    moy_blancs_zero = Decimal(str(s_all.fillna(0).sum())) / Decimal(df.shape[0])
    print(f"  Hypothèse base n=21 avec blancs comptés 0 : "
          f"{float(moy_blancs_zero):.4f} -> RHU "
          f"{moy_blancs_zero.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}")

# Hypothèse 'mauvaise colonne' : Q5.3 déficit d'image de l'ENTREPRISE ou du secteur
col_q53 = [c for c in df.columns if str(c).startswith("Q5.3") and "image" in str(c).lower()]
print("\n=== Colonne piège : Q5.3 [Déficit d'image de l'entreprise ou du secteur] ===")
for c in col_q53:
    n5, somme5, exact5, rhu5, rf5 = arrondis(df[c])
    print(f"  n={n5} somme={somme5:.0f} moy_exacte={float(exact5):.6f} RHU={rhu5} round()={rf5}")

# Distribution agrégée (contrôle 1..5, pas de valeur hors échelle) — comptages seulement
s = pd.to_numeric(df[col_img], errors="coerce").dropna()
print("\n=== Contrôle d'échelle (item image Q3.3) : distribution des notes ===")
print(s.value_counts().sort_index().to_string())
print(f"  min={s.min():.0f} max={s.max():.0f}")
