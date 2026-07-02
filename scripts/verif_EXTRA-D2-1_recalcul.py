#!/usr/bin/env python3
"""Contre-expertise fiche D2 (zone EXTRA du dashboard).
Vérifie les chiffres de l'ancrage de la fiche D2 :
  - SYN Q24  : % transmission-reprise jugée (très) prioritaire (syndicats)
  - ENT Q1.8 : % de dirigeants de 55 ans et + (entreprises)
  - ENT Q2.2 : % de projets de transmission/cession déclarés (entreprises)
Aucune donnée en dur ; sortie agrégée uniquement.
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

DATA = "/home/user/dashboard-gpect-issoudun-2026/data"

def pct(k, n):
    return int((Decimal(k) * 100 / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

# --- SYN Q24 ---
syn = pd.read_excel(f"{DATA}/04_syndicats.xlsx", engine="openpyxl")
print(f"SYN : {syn.shape[0]} lignes x {syn.shape[1]} colonnes")
col_q24 = syn.columns[24]
print(f"Colonne [24] : {col_q24!r}")
s = syn[col_q24].dropna().astype(str).str.strip()
s = s[s != ""]
n = len(s)
print(f"n (réponses non vides) = {n}")
print("Distribution :")
for val, k in s.value_counts().items():
    print(f"  {val!r} : {k}")
prio = s.str.lower().str.contains("prioritaire") & ~s.str.lower().str.contains("secondaire")
k_prio = int(prio.sum())
print(f"(Très) prioritaire : {k_prio}/{n} = {pct(k_prio, n)}%")

# --- ENT Q1.8 et Q2.2 ---
ent = pd.read_excel(f"{DATA}/01_entreprises.xlsx", engine="openpyxl")
print(f"\nENT : {ent.shape[0]} lignes x {ent.shape[1]} colonnes")

c18 = ent.columns[18]
print(f"Colonne [18] : {c18!r}")
a = ent[c18].dropna().astype(str).str.strip()
a = a[a != ""]
na = len(a)
print("Distribution :")
for val, k in a.value_counts().items():
    print(f"  {val!r} : {k}")
k55 = int(a.str.contains("55|60", regex=True).sum())
print(f"Dirigeants 55 ans et + : {k55}/{na} = {pct(k55, na)}%")

c20 = ent.columns[20]
print(f"\nColonne [20] : {c20!r}")
t = ent[c20].dropna().astype(str).str.strip()
t = t[t != ""]
nt = len(t)
print("Distribution :")
for val, k in t.value_counts().items():
    print(f"  {val!r} : {k}")
koui = int(t.str.lower().str.startswith("oui").sum())
print(f"Projet transmission/cession (Oui...) : {koui}/{nt} = {pct(koui, nt)}%")
