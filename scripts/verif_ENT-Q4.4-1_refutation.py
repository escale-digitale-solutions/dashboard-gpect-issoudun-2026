# -*- coding: utf-8 -*-
"""
Contre-expertise ENT Q4.4 — « Services concentrant les départs en retraite »
Écart signalé : dashboard « Conduite / transport » = 20% (4/20) vs auditeur 1 = 25% (5/20).

Objectif : réfuter ou confirmer, en testant :
  - bonne colonne (Q4.4, index 52)
  - base de calcul (n de la question vs n=21 du collège ; base répondants vs base citations)
  - convention d'arrondi (round half up à l'entier)
  - découpage des choix multiples (options contenant des virgules) + texte libre « Autre »

Aucune donnée en dur dans ce script. Sorties console = inspection de travail ;
seuls des agrégats sont conservés dans resultats/.
"""
import sys
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"

def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()

def pct_half_up(k, n):
    return int(Decimal(k * 100) / Decimal(n).quantize(Decimal("1")) if False else
               (Decimal(k) * 100 / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

df = pd.read_excel(XLSX, engine="openpyxl")
print(f"[fichier] {XLSX} -> {df.shape[0]} lignes x {df.shape[1]} colonnes")

col = df.columns[52]
print(f"[colonne 52] {col}")
assert "Q4.4" in str(col) or "départs à la retraite vont-ils se concentrer" in str(col), "mauvaise colonne"

serie = df[col]
non_vides = serie.dropna().astype(str).str.strip()
non_vides = non_vides[non_vides != ""]
n_q = len(non_vides)
print(f"[n question] réponses non vides Q4.4 : {n_q} (collège n={len(df)})")

# --- Inspection brute des cellules (console uniquement, pour codage) ---
print("\n--- Valeurs brutes des cellules (inspection, 1 ligne = 1 répondant, anonyme) ---")
for i, v in enumerate(non_vides.tolist(), 1):
    print(f"R{i:02d} | {v!r}")

# --- Codage par mots-clés : catégorie « Conduite / transport » ---
# La question Google Forms mélange cases à cocher (options standard, séparées par ', ')
# et texte libre (« Autre »). On teste plusieurs périmètres de mots-clés.
kw_strict = ["conduite", "conducteur", "chauffeur", "transport"]  # cœur conduite/transport
kw_large = kw_strict + ["car", "poids lourd", "spl", "livraison", "livreur", "routier"]

def match_any(cell, kws):
    c = norm(cell)
    hits = []
    for k in kws:
        if k == "car":
            # éviter les faux positifs (« car » mot-outil, « carrossier », « cariste »...)
            import re
            if re.search(r"\bcars?\b", c):
                hits.append(k)
        elif k in c:
            hits.append(k)
    return hits

print("\n--- Codage « Conduite / transport » ---")
strict_ids, large_ids = [], []
for i, v in enumerate(non_vides.tolist(), 1):
    hs = match_any(v, kw_strict)
    hl = match_any(v, kw_large)
    if hs:
        strict_ids.append(i)
    if hl:
        large_ids.append(i)
    if hl:
        print(f"R{i:02d} -> mots-clés stricts={hs} larges={hl}")

k_strict, k_large = len(strict_ids), len(large_ids)
print(f"\n[strict]  {k_strict}/{n_q} répondants -> {pct_half_up(k_strict, n_q)}% (base n question)")
print(f"[large]   {k_large}/{n_q} répondants -> {pct_half_up(k_large, n_q)}% (base n question)")
print(f"[strict]  base collège n=21 -> {pct_half_up(k_strict, len(df))}%")
print(f"[large]   base collège n=21 -> {pct_half_up(k_large, len(df))}%")

# --- Contrôle des 7 autres items du graphique dashboard ---
cats = {
    "Production / fabrication": ["production", "fabrication", "usinage", "operateur", "regleur", "soudeur", "atelier"],
    "Logistique": ["logistique", "cariste", "magasinier", "prepara"],
    "Commerce / ADV": ["commerc", "adv", "vente", "vendeur"],
    "Qualité": ["qualite"],
    "Maintenance": ["maintenance"],
    "Bureau d'études": ["bureau d'etudes", "bureau d etudes", "be ", "etudes"],
    "Management de proximité": ["management", "manager", "chef d'equipe", "chef d equipe", "encadrement", "proximite"],
}
dash = {"Production / fabrication": 60, "Logistique": 25, "Commerce / ADV": 25,
        "Conduite / transport": 20, "Qualité": 15, "Maintenance": 15,
        "Bureau d'études": 15, "Management de proximité": 15}

print("\n--- Contrôle des autres items (codage mots-clés indicatif) ---")
resume = []
for cat, kws in cats.items():
    ids = [i for i, v in enumerate(non_vides.tolist(), 1) if match_any(v, kws)]
    p = pct_half_up(len(ids), n_q)
    ok = "OK" if p == dash[cat] else f"ECART (dash={dash[cat]}%)"
    print(f"{cat:28s} {len(ids)}/{n_q} -> {p:3d}%  {ok}")
    resume.append((cat, len(ids), p, dash[cat]))

# conduite dans le résumé
resume.insert(3, ("Conduite / transport (strict)", k_strict, pct_half_up(k_strict, n_q), dash["Conduite / transport"]))

# --- Base citations (contrôle de l'hypothèse « % de citations ») ---
total_citations = sum(len(ids) for _, ids, _, _ in
                      [(c, [i for i, v in enumerate(non_vides.tolist(), 1) if match_any(v, k)], 0, 0)
                       for c, k in list(cats.items())]) + k_strict
print(f"\n[base citations] total citations codées ~{total_citations} ; "
      f"conduite strict = {k_strict} -> {pct_half_up(k_strict, total_citations)}% en base citations")

# --- Résultat agrégé anonymisé ---
out = "/home/user/dashboard-gpect-issoudun-2026/resultats/verif_ENT-Q4.4-1_refutation.txt"
with open(out, "w", encoding="utf-8") as f:
    f.write("Contre-expertise ENT Q4.4 - Services concentrant les departs en retraite\n")
    f.write(f"Source : data/01_entreprises.xlsx ({df.shape[0]}x{df.shape[1]}), colonne index 52\n")
    f.write(f"n question (reponses non vides) = {n_q} / college n=21\n\n")
    f.write("Categorie ; effectif ; % (base n question, round half up) ; % dashboard\n")
    for cat, k, p, d in resume:
        f.write(f"{cat} ; {k} ; {p}% ; {d}%\n")
    f.write(f"\nConduite/transport perimetre large : {k_large}/{n_q} = {pct_half_up(k_large, n_q)}%\n")
print(f"\n[resultats] agrégats écrits dans {out}")
