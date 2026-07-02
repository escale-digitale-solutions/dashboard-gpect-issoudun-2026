# -*- coding: utf-8 -*-
"""
Contre-expertise SYN Q09 — thème verbatim « Désertification médicale ».
Dashboard : 29% (2/7). Premier auditeur : 14% (1/7).
Objectif : recompter par script le nombre de RÉPONDANTS dont le verbatim
Q09 (col [9] « freins ou fragilités pour le développement ») évoque la
désertification médicale / l'accès aux soins / la santé / la démographie
médicale, au sens large puis au sens strict.
Sortie console uniquement (inspection) + résumé agrégé anonymisé.
Aucun verbatim n'est écrit dans un fichier.
"""
import re
import unicodedata
import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/04_syndicats.xlsx"

df = pd.read_excel(SRC, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

col = df.columns[9]
print(f"Colonne [9] : {col!r}\n")

serie = df[col]
n_nonvide = serie.notna().sum()
print(f"Réponses non vides à Q09 : n={n_nonvide} / {len(df)}\n")


def norm(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    return s.lower()


# Motifs : du plus strict au plus large
PATTERNS = {
    "strict 'desertification medicale'": r"desertification\s+medicale|desert\s+medical",
    "medical/medecin": r"medic|medecin",
    "sante/soins/hopital": r"\bsante\b|soins|hopital|hospitali",
    "demographie": r"demograph",
    "vieilliss": r"vieilliss",
}

hits = {k: set() for k in PATTERNS}
for idx, val in serie.items():
    if pd.isna(val):
        continue
    t = norm(val)
    for k, pat in PATTERNS.items():
        if re.search(pat, t):
            hits[k].add(idx)

print("=== Comptage par motif (nombre de REPONDANTS distincts) ===")
for k, s in hits.items():
    ids = sorted(f"S{ i+1:02d}".replace(" ", "") for i in s)
    print(f"  {k:42s} : {len(s)} repondant(s) {ids}")

union_medical = hits["strict 'desertification medicale'"] | hits["medical/medecin"] | hits["sante/soins/hopital"]
union_large = union_medical | hits["demographie"] | hits["vieilliss"]
print(f"\nUnion 'sante/medical' (sans demographie)   : {len(union_medical)} repondant(s)")
print(f"Union large (+ demographie + vieillissement): {len(union_large)} repondant(s)")


def pct_half_up(k, n):
    from decimal import Decimal, ROUND_HALF_UP
    return int(Decimal(k * 100) / Decimal(n) if False else (Decimal(k) * 100 / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


for k in sorted({len(union_medical), len(union_large), 1, 2}):
    print(f"  {k}/7 -> {pct_half_up(k, 7)}% (round half up)")

# Inspection console des verbatims concernés (anonymisés : index seulement)
print("\n=== Inspection console (extraits limites aux passages pertinents) ===")
for idx, val in serie.items():
    if pd.isna(val):
        continue
    t = norm(val)
    if re.search(r"medic|medecin|sante|soins|hopital|demograph|vieilliss|desert", t):
        # n'afficher que les segments de phrase contenant le motif
        segs = re.split(r"[;\n\.]", str(val))
        keep = [s.strip() for s in segs if re.search(r"medic|medecin|sante|soins|hopital|demograph|vieilliss|desert", norm(s))]
        print(f"  Repondant S{idx+1:02d} -> {len(keep)} segment(s) pertinent(s) : {keep}")

# Contre-hypothese : l'auditeur aurait-il pu se tromper de colonne ?
# Balayage de TOUTES les colonnes ouvertes pour voir ou apparaissent ces motifs.
print("\n=== Balayage toutes colonnes : ou parle-t-on de desertification medicale ? ===")
for j, c in enumerate(df.columns):
    ids = set()
    for idx, val in df[c].items():
        if pd.isna(val):
            continue
        if re.search(r"desertification|desert medical|medecin|\bmedical", norm(val)):
            ids.add(idx)
    if ids:
        print(f"  col[{j}] {str(c)[:70]!r} : {len(ids)} repondant(s) {sorted('S%02d' % (i+1) for i in ids)}")
