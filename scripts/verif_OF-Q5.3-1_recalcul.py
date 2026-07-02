#!/usr/bin/env python3
"""Contre-expertise Q5.3 OF — Freins au déploiement de l'AFEST (choix multiple).

Recalcule de zéro les % affichés par le dashboard (n=7, 43/29/29/14/14)
et vérifie l'allégation du 1er auditeur (2 répondants sans option officielle).
Sortie : agrégats anonymisés uniquement (comptages, %, n=).
"""
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/02_organismes_formation.xlsx"

df = pd.read_excel(XLSX, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col = df.columns[62]
print(f"Colonne [62] : {col!r}")
assert "AFEST" in col and "freins" in col.lower(), "Mauvaise colonne ?"

s = df[col]
nonvide = s.dropna().astype(str).str.strip()
nonvide = nonvide[nonvide != ""]
n_nonvide = len(nonvide)
print(f"Cellules non vides : {n_nonvide} / {len(s)}")

def norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).strip().lower()

# Inspection anonymisée des valeurs : longueur + empreinte structurelle
print("\n--- Structure des cellules (anonymisé : longueur, nb de virgules) ---")
for i, v in enumerate(nonvide, 1):
    print(f"  R{i:02d}: len={len(v)}, virgules={v.count(',')}")

# Options officielles (libellés Google Forms, reconstitués depuis les
# fragments observés ; on matche en normalisé, par sous-chaîne)
OPTIONS = {
    "Résistance / méconnaissance des entreprises": [
        "resistance", "meconnaissance des entreprises", "cote entreprises",
        "des entreprises"],
    "Complexité du référentiel & traçabilité": [
        "complexite", "referentiel", "tracabilite"],
    "Absence de modèle économique viable": [
        "modele economique"],
    "Difficulté à identifier les situations apprenantes": [
        "situations apprenantes", "situations de travail apprenantes"],
    "Méconnaissance par les OPCO locaux": [
        "opco"],
}

counts = {k: 0 for k in OPTIONS}
sans_option = 0
for v in nonvide:
    nv = norm(v)
    hit = False
    for label, keys in OPTIONS.items():
        if any(k in nv for k in keys):
            counts[label] += 1
            hit = True
    if not hit:
        sans_option += 1
        # signalement structurel uniquement (pas de contenu si verbatim long)
        extrait = nv if len(nv) <= 12 else f"<texte libre, {len(v)} car.>"
        print(f"  -> réponse SANS option officielle détectée : {extrait}")

def pct(a, b):
    return int(Decimal(a * 100) / Decimal(b) if b else 0) if a * 100 % b == 0 \
        else int((Decimal(a) * 100 / Decimal(b)).quantize(0, ROUND_HALF_UP))

def pct_hu(a, b):
    return int((Decimal(a) * 100 / Decimal(b)).quantize(Decimal("1"), ROUND_HALF_UP))

n_avec_option = n_nonvide - sans_option
print(f"\nRépondants ayant coché >=1 option officielle : {n_avec_option}")
print(f"Répondants non vides SANS option officielle : {sans_option}")

print(f"\n--- % base n={n_nonvide} (convention dashboard : cellules non vides) ---")
for label, c in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"  {label}: {c}/{n_nonvide} = {pct_hu(c, n_nonvide)}%")

if n_avec_option and n_avec_option != n_nonvide:
    print(f"\n--- % base n={n_avec_option} (répondants avec >=1 option cochée) ---")
    for label, c in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {label}: {c}/{n_avec_option} = {pct_hu(c, n_avec_option)}%")

print("\nDashboard affiche : n=7, 43/29/29/14/14")
