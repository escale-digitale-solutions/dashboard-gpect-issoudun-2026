#!/usr/bin/env python3
"""Contre-expertise EXTRA fiche D2 : « transmission (très) prioritaire 71% ».

Vérifie :
1. SYN Q24 (col 24) : % Prioritaire + Très prioritaire parmi les 7 syndicats.
2. ENT Q1.8 (col 18) : % de dirigeants de 55 ans et + (l'autre chiffre de la fiche D2).
3. ENT Q2.2 (col 20) : % d'entreprises avec projet de transmission/cession (Oui, toutes formes).
Objectif : établir si le 71% de la fiche D2 peut provenir des entreprises (auquel cas
l'absence d'attribution serait sans conséquence) ou uniquement des syndicats.
Aucune donnée nominative : uniquement des comptages agrégés.
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

DATA = "/home/user/dashboard-gpect-issoudun-2026/data/"

def pct(k, n):
    return int(Decimal(k * 100) / Decimal(n) if n else Decimal(0)) if False else int(
        (Decimal(k) * 100 / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

syn = pd.read_excel(DATA + "04_syndicats.xlsx", engine="openpyxl")
ent = pd.read_excel(DATA + "01_entreprises.xlsx", engine="openpyxl")
print(f"SYN : {syn.shape[0]} lignes x {syn.shape[1]} colonnes")
print(f"ENT : {ent.shape[0]} lignes x {ent.shape[1]} colonnes")

# --- 1. SYN Q24 ---
col_q24 = syn.columns[24]
s = syn[col_q24].dropna().astype(str).str.strip()
s = s[s != ""]
n = len(s)
vc = s.value_counts()
print(f"\n[SYN Q24] {col_q24!r}\n n reponses non vides = {n}")
for val, k in vc.items():
    print(f"  {val!r}: {k} ({pct(k, n)}%)")
k_prio = int(s.str.lower().str.startswith(("prioritaire", "très prioritaire", "tres prioritaire")).sum())
# comptage explicite : très prioritaire + prioritaire
k_tres = int((s.str.lower().str.contains("très prioritaire") | s.str.lower().str.contains("tres prioritaire")).sum())
k_prio_seul = int((s.str.lower() == "prioritaire").sum())
k_cum = k_tres + k_prio_seul
print(f" (Très) prioritaire = {k_cum}/{n} = {pct(k_cum, n)}%")

# --- 2. ENT Q1.8 : dirigeants 55+ ---
col_q18 = ent.columns[18]
a = ent[col_q18].dropna().astype(str).str.strip()
a = a[a != ""]
na = len(a)
k55 = int(a.str.contains("55").sum() + a.str.contains("60").sum())
print(f"\n[ENT Q1.8] {col_q18!r}\n n = {na}")
for val, k in a.value_counts().items():
    print(f"  {val!r}: {k} ({pct(k, na)}%)")
print(f" 55 ans et + = {k55}/{na} = {pct(k55, na)}%")

# --- 3. ENT Q2.2 : projet de transmission ---
col_q22 = ent.columns[20]
t = ent[col_q22].dropna().astype(str).str.strip()
t = t[t != ""]
nt = len(t)
k_oui = int(t.str.lower().str.startswith("oui").sum())
print(f"\n[ENT Q2.2] {col_q22!r}\n n = {nt}")
for val, k in t.value_counts().items():
    print(f"  {val!r}: {k} ({pct(k, nt)}%)")
print(f" Oui (toutes formes) = {k_oui}/{nt} = {pct(k_oui, nt)}%")

# --- Conclusion machine ---
print("\n--- SYNTHESE ---")
print(f"SYN Q24 (tres) prioritaire : {pct(k_cum, n)}% (n={n})")
print(f"ENT Q2.2 projet transmission Oui : {pct(k_oui, nt)}% (n={nt})")
print(f"ENT Q1.8 dirigeants 55+ : {pct(k55, na)}% (n={na})")
