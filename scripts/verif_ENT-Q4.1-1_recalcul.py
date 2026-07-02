# -*- coding: utf-8 -*-
"""
Contre-expertise ENT Q4.1 — Pyramide des âges (tableau + KPI "47% seniors").

Vérifie de zéro les 14 cellules du tableau du dashboard :
  Avec plus gros employeur : 3 031 têtes | <30 18,0% | 31-44 35,0% | 45-59 41,7% | 60+ 5,3% | Seniors 47,0% | Femmes 36,5%
  Sans plus gros employeur : 1 506 têtes | <30 20,9% | 31-44 33,5% | 45-59 39,5% | 60+ 6,1% | Seniors 45,6% | Femmes 46,5%

Méthode :
  1. Base BRUTE : les 21 répondants, somme directe des 8 colonnes Q4.1.1..Q4.1.8.
  2. Base NETTOYÉE : exclusion programmatique des réponses incohérentes
     (contrôle pyramide vs effectif inscrit Q1.4) :
       - valeurs fractionnaires (proportions déclarées au lieu de têtes) ;
       - somme pyramide hors de l'intervalle [0,5 ; 2] x effectif Q1.4 (somme > 0) ;
       - pyramide entièrement à zéro pour un effectif > 0 (flag séparé : sans effet
         sur les totaux, mais hors base de fait).
  3. Chaque base est calculée AVEC et SANS le plus gros employeur
     (identifié programmatiquement par l'effectif Q1.4 maximal).
Aucune donnée nominative : identifiants E01..E21 (ordre du fichier).
Arrondi : % à 1 décimale, half-up (convention dashboard).
"""
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

SRC = '/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx'

# Valeurs affichées par le dashboard (index.html, table Q4.1) — références publiques
DASH = {
    'avec': {'tetes': 3031, 'm30': 18.0, 'a3144': 35.0, 'a4559': 41.7, 'a60': 5.3, 'seniors': 47.0, 'femmes': 36.5},
    'sans': {'tetes': 1506, 'm30': 20.9, 'a3144': 33.5, 'a4559': 39.5, 'a60': 6.1, 'seniors': 45.6, 'femmes': 46.5},
}


def r1(x):
    """Arrondi half-up à 1 décimale."""
    return float(Decimal(str(x)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


def agg(pyr):
    """Agrégats pyramide sur un sous-ensemble de lignes (DataFrame 8 colonnes)."""
    tot = pyr.values.sum()
    m30 = pyr.iloc[:, 0].sum() + pyr.iloc[:, 1].sum()          # H + F < 30
    a3144 = pyr.iloc[:, 2].sum() + pyr.iloc[:, 3].sum()        # 31-44
    a4559 = pyr.iloc[:, 4].sum() + pyr.iloc[:, 5].sum()        # 45-59
    a60 = pyr.iloc[:, 6].sum() + pyr.iloc[:, 7].sum()          # 60+
    fem = pyr.iloc[:, [1, 3, 5, 7]].values.sum()               # colonnes Femmes
    return {
        'tetes_exact': tot,
        'tetes': int(Decimal(str(tot)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)),
        'm30': r1(100 * m30 / tot), 'a3144': r1(100 * a3144 / tot),
        'a4559': r1(100 * a4559 / tot), 'a60': r1(100 * a60 / tot),
        'seniors': r1(100 * (a4559 + a60) / tot), 'femmes': r1(100 * fem / tot),
    }


def show(tag, a, ref=None):
    line = (f"{tag:<42} {a['tetes']:>5} têtes | <30 {a['m30']:>4}% | 31-44 {a['a3144']:>4}% | "
            f"45-59 {a['a4559']:>4}% | 60+ {a['a60']:>3}% | seniors {a['seniors']:>4}% | femmes {a['femmes']:>4}%")
    print(line)
    if ref is not None:
        diffs = [k for k in ('tetes', 'm30', 'a3144', 'a4559', 'a60', 'seniors', 'femmes') if a[k] != ref[k]]
        print(f"{'':<42} -> vs dashboard : " + ("IDENTIQUE (7/7 cellules)" if not diffs else f"ÉCARTS sur {diffs}"))


df = pd.read_excel(SRC, engine='openpyxl')
print(f"Fichier lu : {df.shape[0]} lignes (répondants) x {df.shape[1]} colonnes\n")

pyr_cols = sorted([c for c in df.columns if str(c).startswith('Q4.1')])
assert len(pyr_cols) == 8, pyr_cols
eff_col = [c for c in df.columns if str(c).startswith('Q1.4')][0]

pyr = df[pyr_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
eff = pd.to_numeric(df[eff_col], errors='coerce')
sums = pyr.sum(axis=1)

# Plus gros employeur = effectif Q1.4 maximal (jamais nommé)
i_big = int(eff.idxmax())
print(f"Plus gros employeur : ligne E{i_big+1:02d} (effectif Q1.4 = {int(eff[i_big])}, somme pyramide = {sums[i_big]:.0f})\n")

# --- Contrôle de cohérence ligne à ligne ---
frac = pyr.apply(lambda r: any(v != int(v) for v in r), axis=1)
ratio_ko = (sums > 0) & ((sums > 2 * eff) | (sums < 0.5 * eff))
zero_ko = (sums == 0) & (eff > 0)
excl = frac | ratio_ko

print("Lignes exclues par le contrôle pyramide vs effectif Q1.4 :")
for i in df.index[excl]:
    why = 'valeurs fractionnaires (proportions)' if frac[i] else 'somme pyramide incohérente avec Q1.4'
    print(f"  E{i+1:02d} : somme pyramide = {sums[i]:g} pour effectif Q1.4 = {int(eff[i])} -> {why}")
for i in df.index[zero_ko]:
    print(f"  E{i+1:02d} : pyramide entièrement à zéro pour effectif Q1.4 = {int(eff[i])} -> hors base de fait (0 tête, aucun effet sur les totaux)")
n_clean = int((~excl).sum())
n_util = int((~excl & ~zero_ko).sum())
print(f"\nBase nettoyée : {n_clean} entreprises hors exclusions ({n_util} avec des têtes > 0)\n")

# --- 1. Base brute (21 répondants) ---
print("=== BASE BRUTE (21 répondants) ===")
show(f"Avec plus gros employeur (n=21)", agg(pyr), DASH['avec'])
show(f"Sans plus gros employeur (n=20)", agg(pyr.drop(index=i_big)), DASH['sans'])

# --- 2. Base nettoyée ---
print(f"\n=== BASE NETTOYÉE (exclusion des {int(excl.sum())} lignes incohérentes) ===")
clean = pyr[~excl]
show(f"Avec plus gros employeur (n={n_clean})", agg(clean), DASH['avec'])
show(f"Sans plus gros employeur (n={n_clean-1})", agg(clean.drop(index=i_big)), DASH['sans'])
