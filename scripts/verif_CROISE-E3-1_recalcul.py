#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contre-expertise CROISE / Écart 3 (gapBars mobilité).
Recalcule de zéro, depuis les xlsx du 30/06/2026 :
  - SYN col 18 : échelle 1-5 « mobilité frein majeur » -> moyenne, n
  - SYN col 17 : choix multiple « freins structurants » -> % citant la mobilité rurale
  - ACT col 36 : Q4.1 [Mobilité et accès aux transports] (1-5) -> moyenne, n
  - ENT col 31 : Q3.3 [Contraintes liées au Transport] (1-5) -> moyenne, n
Aucune donnée en dur. Sortie : agrégats anonymisés uniquement.
"""
import decimal
import pandas as pd

DATA = "/home/user/dashboard-gpect-issoudun-2026/data"
OUT = "/home/user/dashboard-gpect-issoudun-2026/resultats/verif_CROISE-E3-1_recalcul.txt"


def r1(x):  # moyenne à 1 décimale, round half up
    return decimal.Decimal(str(x)).quantize(decimal.Decimal("0.1"),
                                            rounding=decimal.ROUND_HALF_UP)


def pct(k, n):  # % entier, round half up
    return decimal.Decimal(str(100 * k / n)).quantize(decimal.Decimal("1"),
                                                      rounding=decimal.ROUND_HALF_UP)


lines = []


def log(s=""):
    print(s)
    lines.append(str(s))


syn = pd.read_excel(f"{DATA}/04_syndicats.xlsx", engine="openpyxl")
act = pd.read_excel(f"{DATA}/03_acteurs_emploi.xlsx", engine="openpyxl")
ent = pd.read_excel(f"{DATA}/01_entreprises.xlsx", engine="openpyxl")

log(f"Dimensions lues : SYN {syn.shape}, ACT {act.shape}, ENT {ent.shape}")
log()

# --- SYN col 18 : échelle 1-5 mobilité ---
c = syn.columns[18]
s = pd.to_numeric(syn[c], errors="coerce").dropna()
assert len(s) + syn[c].isna().sum() == len(syn)
log(f"[SYN col18] {c}")
log(f"  n={len(s)}, valeurs min={s.min():.0f} max={s.max():.0f}, "
    f"moyenne brute={s.mean():.6f}, moyenne affichable={r1(s.mean())}/5")
log(f"  distribution (note: effectif) = "
    f"{ {int(k): int(v) for k, v in s.value_counts().sort_index().items()} }")
log()

# --- SYN col 17 : choix multiple freins structurants ---
c17 = syn.columns[17]
cells = syn[c17].dropna().astype(str)
n17 = len(cells)
# Détection insensible à la casse du motif « mobilité » (l'option Google Forms
# contient « rural » : on vérifie les deux motifs séparément).
k_mobilite = cells.str.contains("mobilit", case=False).sum()
k_rural = cells.str.contains("rural", case=False).sum()
log(f"[SYN col17] {c17}")
log(f"  n répondants à la question = {n17}")
log(f"  cellules contenant 'mobilit' = {k_mobilite} -> {pct(k_mobilite, n17)}%")
log(f"  cellules contenant 'rural'   = {k_rural} -> {pct(k_rural, n17)}%")
log(f"  conversion dashboard : {pct(k_mobilite, n17)}% x 5 = "
    f"{r1(float(pct(k_mobilite, n17)) / 100 * 5)}/5 (procédé du gapBars)")
log()

# --- ACT col 36 : Q4.1 mobilité (1-5) ---
ca = act.columns[36]
a = pd.to_numeric(act[ca], errors="coerce").dropna()
log(f"[ACT col36] {ca}")
log(f"  n={len(a)}, moyenne brute={a.mean():.6f}, affichable={r1(a.mean())}/5")
log()

# --- ENT col 31 : Q3.3 transport (1-5) ---
ce = ent.columns[31]
e = pd.to_numeric(ent[ce], errors="coerce").dropna()
log(f"[ENT col31] {ce}")
log(f"  n={len(e)}, moyenne brute={e.mean():.6f}, affichable={r1(e.mean())}/5")
log()

log("Comparaison sur échelles 1-5 réellement posées :")
log(f"  SYN {r1(s.mean())} (n={len(s)}) | ACT {r1(a.mean())} (n={len(a)}) | "
    f"ENT {r1(e.mean())} (n={len(e)})")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(f"\nRésultats écrits dans {OUT}")
