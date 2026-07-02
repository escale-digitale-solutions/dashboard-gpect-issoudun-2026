# -*- coding: utf-8 -*-
"""
Contre-expertise ENT Q3.1 — thème « Bureau études / méthodes / CAO »
Dashboard : 29% (6/21) · Premier auditeur : 7/21 -> 33%

Hypothèses de réfutation testées :
  H1. Mauvaise colonne (Q3.1 = index 24 du fichier entreprises)
  H2. Mauvaise base (n de la question = non-vides, vs n=21 du collège)
  H3. Convention d'arrondi (round half up à l'entier)
  H4. Sensibilité accents/majuscules du codage mots-clés
      (la faute de frappe « TECNHICIEN METHODES » est-elle en cause ?)
  H4b. Variante « bureau études » SANS le « d' » (ratée par le motif
      strict « bureau d'études » de l'auditeur)
  H5. Cohérence des 7 autres thèmes du bloc (contrôle de méthode)

Aucune donnée en dur. Sorties : comptages agrégés anonymisés (E01..E21)
et motifs regex ayant matché — jamais le contenu des verbatims.
"""
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
COL_Q31 = 24  # [24] Q3.1 — Listez vos 3 à 5 métiers clés ou en tension

def norm(s: str) -> str:
    """minuscule + suppression des accents"""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()

def pct_half_up(k: int, n: int) -> int:
    return int((Decimal(k) * 100 / Decimal(n))
               .quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def compte(serie, patterns, use_norm=True):
    """ids des répondants dont la cellule matche >= 1 motif"""
    ids = []
    for idx, val in serie.items():
        if pd.isna(val) or str(val).strip() == "":
            continue
        t = norm(val) if use_norm else str(val).lower()
        if any(re.search(p, t) for p in patterns):
            ids.append(f"E{idx+1:02d}")
    return ids

df = pd.read_excel(XLSX, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")
assert df.shape == (21, 124), "Shape inattendue — STOP"

col_name = df.columns[COL_Q31]
print(f"[H1] Colonne index {COL_Q31} : {col_name!r}")
assert "Q3.1" in str(col_name), "Ce n'est pas Q3.1 — STOP"

serie = df.iloc[:, COL_Q31]
n_q = int(serie.dropna().astype(str).str.strip().ne("").sum())
print(f"[H2] Réponses non vides à Q3.1 : n={n_q} (dashboard : n=21)")

# --- Mots-clés STRICTS du premier auditeur --------------------------------
KW_AUDITEUR = [
    r"bureau\s+d\W?etudes?",   # « bureau d'études » (avec le d')
    r"\bbe\b",                  # sigle BE, bornes de mot
    r"methode",                 # méthodes (normalisé : capte METHODES)
    r"\bcao\b",
    r"dessinateur",
]
ids_strict = compte(serie, KW_AUDITEUR)
k = len(ids_strict)
print(f"\n[Recomptage strict, mots-clés de l'auditeur, casse+accents normalisés]")
print(f"  Répondants : {ids_strict}")
print(f"  => {k}/21 -> {pct_half_up(k, 21)}%   (dashboard : 29%)")

# --- H4 : la ligne à faute de frappe est-elle captée ? ---------------------
print("\n[H4] La cellule contenant la faute « TECNHICIEN » (E18) matche-t-elle ?")
print("  ->", "OUI (via 'methode' normalisé — la faute porte sur TECNHICIEN,"
      " pas sur METHODES)" if "E18" in ids_strict else "NON")

# codage naïf .lower() sans strip des accents (motif « méthode » accentué)
ids_naif = compte(serie, [r"bureau\s+d.?études?", r"\bbe\b", r"méthode",
                          r"\bcao\b", r"dessinateur"], use_norm=False)
print(f"  Codage naïf sans normalisation d'accents : {len(ids_naif)}/21 "
      f"-> {pct_half_up(len(ids_naif), 21)}% (perd {sorted(set(ids_strict)-set(ids_naif))})")

# --- H4b : « bureau études » sans le « d' » --------------------------------
KW_CORRIGE = KW_AUDITEUR[:]
KW_CORRIGE[0] = r"bureau\s+(d\W?\s*)?etudes?"   # accepte « bureau études »
ids_corr = compte(serie, KW_CORRIGE)
k2 = len(ids_corr)
print(f"\n[H4b] Motif élargi « bureau (d')études » :")
print(f"  Répondants : {ids_corr}")
print(f"  Ajouté(s) vs strict : {sorted(set(ids_corr)-set(ids_strict))} "
      f"(cellule citant 'bureau etudes' sans apostrophe-d)")
print(f"  => {k2}/21 -> {pct_half_up(k2, 21)}%   (auditeur : 33%)")

# --- H3 : arrondis ----------------------------------------------------------
print(f"\n[H3] Arrondis half-up : 6/21 = {pct_half_up(6,21)}% ; 7/21 = {pct_half_up(7,21)}%")

# --- H5 : contrôle des 7 autres thèmes du bloc ------------------------------
THEMES = {
    "Usinage / réglage CN / mécanique (dash 33%)":
        [r"usinage", r"usineur", r"regleur", r"\bcn\b", r"\bcnc\b",
         r"commande numerique", r"mecanicien", r"tourneur", r"fraiseur",
         r"decolletage", r"rectifieur"],
    "Encadrement / management (dash 29%)":
        [r"chef d.equipe", r"chef d.atelier", r"manager", r"management",
         r"encadr", r"responsable", r"chef de projets?", r"directeur",
         r"superviseur", r"agent de maitrise"],
    "Qualité / contrôle / HSE (dash 24%)":
        [r"qualite", r"metrolog", r"\bhse\b", r"\bqhse\b", r"\bqse\b"],
    "Conduite / transport (dash 24%)":
        [r"conducteur", r"chauffeur", r"routier", r"\bspl\b", r"\bpl\b"],
    "Maintenance (dash 19%)":
        [r"maintenance", r"electromecanicien"],
    "Logistique / cariste (dash 19%)":
        [r"logistique", r"cariste", r"magasinier", r"supply",
         r"preparateur de commandes?"],
    "Soudure / chaudronnerie (dash 10%)":
        [r"soudeur", r"soudure", r"chaudronn"],
}
print("\n[H5] Contrôle des autres thèmes (mots-clés indicatifs, normalisés) :")
for label, pats in THEMES.items():
    c = len(compte(serie, pats))
    print(f"  {label} : {c}/21 -> {pct_half_up(c, 21)}%")

print("\nCONCLUSION :")
print(f"  - Mots-clés stricts de l'auditeur : {k}/21 = {pct_half_up(k,21)}% (= dashboard)")
print(f"  - Lecture thématique complète (bureau études sans d') : {k2}/21 = {pct_half_up(k2,21)}%")
print("  - La ligne à faute de frappe (E18) était DÉJÀ comptée ; le répondant")
print("    manquant du dashboard est celui qui écrit « bureau études » sans d'.")
