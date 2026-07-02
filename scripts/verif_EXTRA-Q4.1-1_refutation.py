# -*- coding: utf-8 -*-
"""
Contre-expertise EXTRA / Levier 5 / fiche D1 — « 47% de seniors (45 ans et +) »
Source : data/01_entreprises.xlsx, Q4.1 (pyramide des âges, 8 colonnes H/F x 4 tranches).
Objectif : tenter de REPRODUIRE le 47% du dashboard sous toutes les conventions
plausibles, sinon confirmer l'écart signalé (46%).
Aucune donnée nominative n'est affichée : agrégats uniquement.
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

F = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
df = pd.read_excel(F, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Colonnes Q4.1 (indices confirmés via colonnes_ENT.txt)
idx = {
    "H<30": 42, "F<30": 43,
    "H31-44": 44, "F31-44": 45,
    "H45-59": 46, "F45-59": 47,
    "H60+": 48, "F60+": 49,
}
cols = {k: df.columns[v] for k, v in idx.items()}
for k, c in cols.items():
    print(f"  {k} -> [{idx[k]}] {c}")

age = df[[c for c in cols.values()]].apply(pd.to_numeric, errors="coerce")
age.columns = list(idx.keys())

SENIORS = ["H45-59", "F45-59", "H60+", "F60+"]
JEUNES = ["H<30", "F<30", "H31-44", "F31-44"]

def half_up(x, nd=0):
    q = Decimal(1).scaleb(-nd)
    return float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))

def pct(num, den, label):
    if den == 0:
        print(f"  {label}: denominateur nul")
        return
    p = 100 * num / den
    print(f"  {label}: {num:.0f}/{den:.0f} = {p:.3f}% -> arrondi half-up {half_up(p):.0f}%")

print("\n--- H1. Ponderé, NaN traités comme 0 (toutes lignes) ---")
a0 = age.fillna(0)
pct(a0[SENIORS].sum().sum(), a0.sum().sum(), "seniors/total pyramide")

print("\n--- H2. Ponderé, lignes avec pyramide entièrement renseignée ---")
full = age.dropna(how="any")
print(f"  n lignes complètes = {len(full)}")
pct(full[SENIORS].sum().sum(), full.sum().sum(), "seniors/total pyramide (complet)")

print("\n--- H3. Ponderé, lignes avec au moins une cellule renseignée ---")
part = age.dropna(how="all")
print(f"  n lignes partiellement renseignées = {len(part)}")
p0 = part.fillna(0)
pct(p0[SENIORS].sum().sum(), p0.sum().sum(), "seniors/total pyramide (partiel)")

print("\n--- H4. Base 'effectif inscrit (CDI+CDD)' (col 14) ---")
eff_inscrit = pd.to_numeric(df[df.columns[14]], errors="coerce")
pct(a0[SENIORS].sum().sum(), eff_inscrit.fillna(0).sum(), "seniors/effectif inscrit")

print("\n--- H5. Base 'effectif total 31/12/2025' (col 13) ---")
eff_total = pd.to_numeric(df[df.columns[13]], errors="coerce")
if eff_total.notna().sum() == 0:
    print("  colonne non numérique (valeurs texte/tranches) -> hypothèse inapplicable")
else:
    pct(a0[SENIORS].sum().sum(), eff_total.fillna(0).sum(), "seniors/effectif total")

print("\n--- H6. Moyenne non pondérée des % seniors par entreprise ---")
row_tot = age.sum(axis=1, min_count=1)
row_sen = age[SENIORS].sum(axis=1, min_count=1)
share = (100 * row_sen / row_tot).dropna()
share = share[row_tot.reindex(share.index) > 0]
print(f"  n entreprises = {len(share)}")
print(f"  moyenne = {share.mean():.3f}% -> {half_up(share.mean()):.0f}%")
print(f"  mediane = {share.median():.3f}% -> {half_up(share.median()):.0f}%")

print("\n--- H7. Sans le plus gros employeur (pyramide max) ---")
imax = a0.sum(axis=1).idxmax()
print(f"  ligne exclue = index interne {imax} (pyramide ~{a0.sum(axis=1).max():.0f} salariés) — non nominatif")
sans = a0.drop(index=imax)
pct(sans[SENIORS].sum().sum(), sans.sum().sum(), "seniors/total sans plus gros employeur")

print("\n--- H8. Variantes de définition 'senior' ---")
# 8a. seniors = 60+ seulement (peu plausible mais on teste)
pct(a0[["H60+", "F60+"]].sum().sum(), a0.sum().sum(), "60+ seulement / total")
# 8b. seniors incluant 31-44 ? (non plausible, controle)
pct(a0[SENIORS + ["H31-44", "F31-44"]].sum().sum(), a0.sum().sum(), "31+ / total")
# 8c. hommes seniors / hommes, femmes seniors / femmes
pct(a0[["H45-59", "H60+"]].sum().sum(),
    a0[["H<30", "H31-44", "H45-59", "H60+"]].sum().sum(), "seniors hommes / hommes")
pct(a0[["F45-59", "F60+"]].sum().sum(),
    a0[["F<30", "F31-44", "F45-59", "F60+"]].sum().sum(), "seniors femmes / femmes")

print("\n--- H9. Recherche systématique : quel sous-ensemble de lignes donne 47% ? ---")
# Leave-one-out : retirer une seule entreprise à la fois
hits = []
for i in a0.index:
    sub = a0.drop(index=i)
    d = sub.sum().sum()
    if d > 0:
        p = 100 * sub[SENIORS].sum().sum() / d
        if half_up(p) == 47:
            hits.append((f"E{i+1:02d} exclue", p))
for h, p in hits:
    print(f"  leave-one-out {h}: {p:.3f}% -> 47%")
if not hits:
    print("  aucun retrait d'une seule entreprise ne donne 47%")

print("\n--- H10. Arrondi du numérateur/dénominateur, autres arrondis ---")
num = a0[SENIORS].sum().sum(); den = a0.sum().sum()
p = 100 * num / den
import math
print(f"  brut = {p:.4f}% | half-up={half_up(p):.0f} | ceil={math.ceil(p)} | floor={math.floor(p)} | round python={round(p)}")

print("\n--- Totaux de référence (pour traçabilité) ---")
print(f"  somme seniors (45+) = {num:.0f}")
print(f"  somme pyramide totale = {den:.0f}")
print(f"  n répondants Q4.1 (>=1 cellule) = {len(part)}")
