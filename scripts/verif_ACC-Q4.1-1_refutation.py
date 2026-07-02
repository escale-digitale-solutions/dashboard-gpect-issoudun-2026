#!/usr/bin/env python3
"""Contre-expertise (réfutation) — KPI accueil ENT Q4.1 : part de seniors 45+.

Dashboard : 47% (table : avec plus gros employeur 3 031 têtes / 47,0% seniors /
36,5% femmes / tranches 18,0-35,0-41,7-5,3 ; sans plus gros employeur 1 506 /
45,6% / 46,5%).
Premier auditeur : 46% (1 460,5 seniors / 3 154,95 têtes = 46,29%).

Objectif : tenter de RÉFUTER l'écart, c.-à-d. trouver une convention légitime
(bonnes colonnes, base, arrondi, exclusion/conversion de lignes atypiques)
qui redonne exactement les chiffres du dashboard.

Aucune donnée en dur ; sorties strictement agrégées/anonymisées (E01..E21).
"""
from decimal import Decimal, ROUND_HALF_UP
from itertools import combinations
import pandas as pd

PATH = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
df = pd.read_excel(PATH, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

cols = list(df.columns[42:50])  # Q4.1.1..Q4.1.8
assert all("Q4.1" in c for c in cols), "Mauvaises colonnes Q4.1"
num = df[cols].apply(pd.to_numeric, errors="coerce")
eff = pd.to_numeric(df[df.columns[13]], errors="coerce")  # Q1.3 (catégoriel -> NaN)
eff14 = pd.to_numeric(df[df.columns[14]], errors="coerce")  # Q1.4 effectif inscrit


def r1(x):
    return float(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def r0(x):
    return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def profil(d):
    tot = d.sum().sum()
    if tot == 0:
        return None
    sen = d[cols[4:8]].sum().sum()
    return {
        "tetes": tot,
        "m30": r1(d[cols[0:2]].sum().sum() / tot * 100),
        "t3144": r1(d[cols[2:4]].sum().sum() / tot * 100),
        "t4559": r1(d[cols[4:6]].sum().sum() / tot * 100),
        "t60": r1(d[cols[6:8]].sum().sum() / tot * 100),
        "sen": r1(sen / tot * 100),
        "sen_raw": sen / tot * 100,
        "fem": r1(d[[cols[1], cols[3], cols[5], cols[7]]].sum().sum() / tot * 100),
    }


# ---------------------------------------------------------------- 0. Contrôles
print("\n[0] Contrôle colonnes / n : ")
print(f"    n répondants Q4.1 (au moins une cellule) = {int(num.notna().any(axis=1).sum())} / 21")

# ------------------------------------------------- 1. Calcul brut + arrondis
tot_all = num.sum().sum()
sen_all = num[cols[4:8]].sum().sum()
raw = sen_all / tot_all * 100
print(f"\n[1] Somme brute (21 lignes) : {sen_all:g} seniors / {tot_all:g} têtes = {raw:.4f}%")
print(f"    round half up entier = {r0(raw)}% | round() python (half even) = {round(raw)}%"
      f" | plafond = {int(-(-raw // 1))}%")
print("    -> aucune convention d'arrondi ne transforme 46,29 en 47.")

# --------------------------------- 2. La table du dashboard comme point fixe
# Le dashboard n'affiche pas 47% depuis la somme brute : sa table repose sur
# 3 031 têtes (et 1 506 sans plus gros employeur). On cherche quel sous-
# ensemble de lignes (exclusions) reproduit EXACTEMENT cette table.
totals_row = num.sum(axis=1)
big_idx = int(totals_row.idxmax())
big_tot = totals_row.max()
print(f"\n[2] Plus gros employeur = E{big_idx+1:02d} ({big_tot:g} têtes déclarées Q4.1)")
print(f"    Base dashboard 3 031 vs somme brute {tot_all:g} : écart = {tot_all - 3031:g} têtes")
print(f"    Base sans gros employeur : dashboard 1 506 vs brut {tot_all - big_tot:g}")

TABLE_AVEC = {"m30": 18.0, "t3144": 35.0, "t4559": 41.7, "t60": 5.3, "sen": 47.0, "fem": 36.5}
TABLE_SANS = {"m30": 20.9, "t3144": 33.5, "t4559": 39.5, "t60": 6.1, "sen": 45.6, "fem": 46.5}

others = [i for i in range(len(num)) if i != big_idx]
matches = []
for k in range(0, 5):  # jusqu'à 4 lignes exclues
    for combo in combinations(others, k):
        keep = [i for i in range(len(num)) if i not in combo]
        d = num.iloc[keep]
        t = d.sum().sum()
        if not (3030.5 <= t < 3031.5):
            continue
        p_avec = profil(d)
        p_sans = profil(d.drop(index=big_idx))
        ok_avec = all(abs(p_avec[key] - v) < 0.051 for key, v in TABLE_AVEC.items())
        ok_sans = all(abs(p_sans[key] - v) < 0.051 for key, v in TABLE_SANS.items())
        matches.append((combo, p_avec, p_sans, ok_avec, ok_sans))

print(f"\n    Sous-ensembles dont le total tombe à 3 031 (±0,5) : {len(matches)}")
for combo, p_avec, p_sans, ok_avec, ok_sans in matches:
    excl = ", ".join(f"E{i+1:02d}" for i in combo) or "(aucune)"
    print(f"\n    Exclusion de : {excl}")
    print(f"      AVEC gros employeur : têtes={p_avec['tetes']:g} | <30 {p_avec['m30']}% | "
          f"31-44 {p_avec['t3144']}% | 45-59 {p_avec['t4559']}% | 60+ {p_avec['t60']}% | "
          f"seniors {p_avec['sen']}% (brut {p_avec['sen_raw']:.3f}%) | femmes {p_avec['fem']}%"
          f"  -> table dashboard {'REPRODUITE' if ok_avec else 'non reproduite'}")
    print(f"      SANS gros employeur : têtes={p_sans['tetes']:g} | <30 {p_sans['m30']}% | "
          f"31-44 {p_sans['t3144']}% | 45-59 {p_sans['t4559']}% | 60+ {p_sans['t60']}% | "
          f"seniors {p_sans['sen']}% | femmes {p_sans['fem']}%"
          f"  -> table dashboard {'REPRODUITE' if ok_sans else 'non reproduite'}")

full_match = [m for m in matches if m[3] and m[4]]

# ------------------------- 3. Hypothèses de conversion des lignes atypiques
print("\n[3] Hypothèses de conversion (lignes atypiques) :")
for i in range(len(num)):
    row = num.iloc[i]
    t = row.sum()
    frac = (row.dropna() % 1 != 0).any()
    if t == 0 or frac or (90 <= t <= 110 and t != eff.iloc[i]):
        print(f"    E{i+1:02d} : somme Q4.1 = {t:g} | effectif déclaré Q1.3 = {eff.iloc[i]:g}"
              f" | valeurs non entières = {bool(frac)}")

# Variante : convertir les lignes 'proportions/%' en effectifs via Q1.3
conv = num.copy()
changed = []
for i in range(len(num)):
    t = conv.iloc[i].sum()
    if t > 0 and (t <= 2.5 or (90 <= t <= 110 and abs(t - eff.iloc[i]) > 10)):
        if pd.notna(eff.iloc[i]) and eff.iloc[i] > 0:
            conv.iloc[i] = conv.iloc[i] / t * eff.iloc[i]
            changed.append(f"E{i+1:02d}")
p = profil(conv)
print(f"    Conversion via effectif Q1.3 des lignes {changed} :")
print(f"      têtes={p['tetes']:g} | seniors {p['sen_raw']:.2f}% -> {r0(p['sen_raw'])}%")

# --------------------- 3bis. Cohérence Q4.1 vs effectif inscrit Q1.4 par ligne
print("\n[3bis] Cohérence somme Q4.1 vs effectif inscrit Q1.4 (justification des exclusions) :")
print("    (écart relatif > 25% ou somme non entière = ligne invalide comme effectifs)")
for i in range(len(num)):
    t = num.iloc[i].sum()
    e = eff14.iloc[i]
    if pd.isna(e) or e == 0:
        flag = "effectif Q1.4 manquant"
    else:
        ecart = abs(t - e) / e
        frac = (num.iloc[i].dropna() % 1 != 0).any()
        flag = "OK" if ecart <= 0.25 and not frac else \
            f"INVALIDE (somme {t:g} vs effectif {e:g}" + (", valeurs non entières)" if frac else ")")
    if flag != "OK":
        print(f"    E{i+1:02d} : {flag}")

# ------------------------------------------------------------- 4. Conclusion
print("\n[4] CONCLUSION")
if full_match:
    combo = full_match[0][0]
    excl = ", ".join(f"E{i+1:02d}" for i in combo)
    sen_raw = full_match[0][1]["sen_raw"]
    print(f"    La table du dashboard (3 031 / 47,0% / 1 506 / 45,6% + tranches + femmes)")
    print(f"    est reproduite EXACTEMENT en excluant : {excl}")
    print(f"    Part seniors correspondante : {sen_raw:.3f}% -> {r0(sen_raw)}%")
else:
    print("    Aucun sous-ensemble ne reproduit exactement la table du dashboard.")
print(f"    Somme brute toutes lignes : {raw:.2f}% -> {r0(raw)}%")
