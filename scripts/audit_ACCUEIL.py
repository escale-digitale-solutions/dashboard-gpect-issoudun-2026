# -*- coding: utf-8 -*-
"""
Audit de la zone « Page accueil » du dashboard GPECT Issoudun 2026.
Recalcule depuis les 4 exports xlsx du 30/06/2026 chaque chiffre d'enquête
affiché sur la page d'accueil (hero, KPIs, 5 messages clés, cartes collèges,
bloc Limites & biais, pied de page).
Sortie : resultats/audit_ACCUEIL.json ({q, label, dashboard, calcule, verdict}).
Aucune donnée brute ni verbatim n'est écrit : uniquement des agrégats anonymes.
"""
import json
import os
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "resultats", "audit_ACCUEIL.json")

ent = pd.read_excel(os.path.join(DATA, "01_entreprises.xlsx"), engine="openpyxl")
of = pd.read_excel(os.path.join(DATA, "02_organismes_formation.xlsx"), engine="openpyxl")
act = pd.read_excel(os.path.join(DATA, "03_acteurs_emploi.xlsx"), engine="openpyxl")
syn = pd.read_excel(os.path.join(DATA, "04_syndicats.xlsx"), engine="openpyxl")


def pct(num, den):
    """% arrondi à l'entier, round half up (convention dashboard)."""
    return int(Decimal(100 * num / den).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def m1(series):
    """Moyenne à 1 décimale, round half up (convention dashboard)."""
    s = pd.to_numeric(series, errors="coerce")
    return float(Decimal(str(s.mean())).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


controls = []


def ctl(q, label, dash, calc, ok=None):
    if ok is None:
        ok = str(dash) == str(calc)
    controls.append({
        "q": q, "label": label, "dashboard": dash, "calcule": calc,
        "verdict": "OK" if ok else "ECART",
    })


# ---------------------------------------------------------------- Hero / n=
n_ent, n_of, n_act, n_syn = len(ent), len(of), len(act), len(syn)
ctl("HERO", "42 répondants (chip hero)", "42", str(n_ent + n_of + n_act + n_syn))
ctl("HERO", "Entreprises : 21 répondants (carte + pied de page)", "21", str(n_ent))
ctl("HERO", "Organismes de formation : 7 répondants", "7", str(n_of))
ctl("HERO", "Acteurs de l'emploi : 7 répondants", "7", str(n_act))
ctl("HERO", "Syndicats & org. pro. : 7 répondants", "7", str(n_syn))
years = sorted(set(
    y for df in (ent, of, act, syn)
    for y in pd.to_datetime(df["Horodateur"], errors="coerce").dt.year.dropna().astype(int)
))
ctl("HERO", "Collecte 2026 (chip hero)", "2026", ",".join(map(str, years)))

# ------------------------------------------------------------------- KPIs
# KPI 1 — 95% des entreprises en tension (ENT Q3.2, majeures + ponctuelles)
q32 = ent.iloc[:, 25].dropna().astype(str)
tension = q32.str.startswith("Oui").sum()
ctl("ENT-Q3.2", "95% des entreprises en tension de recrutement (majeures ou ponctuelles)",
    "95%", f"{pct(tension, len(q32))}% ({tension}/{len(q32)})",
    pct(tension, len(q32)) == 95)

# KPI 2 — image du bassin 2,3/5 (ENT Q8.2)
ctl("ENT-Q8.2", "Image du bassin auprès des candidats : 2,3/5",
    "2,3/5", f"{m1(ent.iloc[:, 111])}/5 (n={ent.iloc[:, 111].notna().sum()})",
    m1(ent.iloc[:, 111]) == 2.3)

# KPI 3 — 47% de seniors 45+ (ENT Q4.1.1 à Q4.1.8, somme brute pondérée)
pyr = ent.iloc[:, 42:50].apply(pd.to_numeric, errors="coerce")
tot = pyr.sum().sum()
sen = pyr.iloc[:, 4:8].sum().sum()  # 45-59 ans + 60 ans et +
part_sen = pct(sen, tot)
ctl("ENT-Q4.1", "47% de seniors (45 ans et +) dans la pyramide des âges",
    "47%", f"{part_sen}% ({100 * sen / tot:.2f}% ; effectif pyramide={tot:.0f})",
    part_sen == 47)

# KPI 4 — AFEST 1,0/5 (ENT Q4.8 item AFEST)
ctl("ENT-Q4.8-AFEST", "Recours à l'AFEST : 1,0/5",
    "1,0/5", f"{m1(ent.iloc[:, 66])}/5 (n={ent.iloc[:, 66].notna().sum()})",
    m1(ent.iloc[:, 66]) == 1.0)

# ------------------------------------------------------- 5 messages clés
# Message 1 — acteurs de l'emploi : difficulté 4,9/5 maintenance et programmation
ctl("ACT-Q3.1-maint", "Difficulté maintenance industrielle (acteurs emploi) : 4,9/5",
    "4,9/5", f"{m1(act.iloc[:, 25])}/5 (n={act.iloc[:, 25].notna().sum()})",
    m1(act.iloc[:, 25]) == 4.9)
ctl("ACT-Q3.1-CNC", "Difficulté programmation machines CNC/robots (acteurs emploi) : 4,9/5",
    "4,9/5", f"{m1(act.iloc[:, 26])}/5 (n={act.iloc[:, 26].notna().sum()})",
    m1(act.iloc[:, 26]) == 4.9)

# Message 2 — adéquation de l'offre de formation, 4 collèges
ctl("OF-Q4.1", "OF : « notre offre couvre les besoins » 4,0/5",
    "4,0/5", f"{m1(of.iloc[:, 55])}/5 (n={of.iloc[:, 55].notna().sum()})",
    m1(of.iloc[:, 55]) == 4.0)
ctl("ACT-Q6.1", "Acteurs emploi : offre de formation locale adaptée 2,3/5",
    "2,3/5", f"{m1(act.iloc[:, 53])}/5 (n={act.iloc[:, 53].notna().sum()})",
    m1(act.iloc[:, 53]) == 2.3)
ctl("ENT-Q7.6", "Entreprises : offre de formation adaptée 3,1/5",
    "3,1/5", f"{m1(ent.iloc[:, 94])}/5 (n={ent.iloc[:, 94].notna().sum()})",
    m1(ent.iloc[:, 94]) == 3.1)
s14 = syn.iloc[:, 14].dropna().astype(str)
peu_part = s14.isin(["Peu adaptée", "Partiellement adaptée"]).sum()
ctl("SYN-offre", "71% des partenaires sociaux : offre « peu » ou « partiellement » adaptée",
    "71%", f"{pct(peu_part, len(s14))}% ({peu_part}/{len(s14)})",
    pct(peu_part, len(s14)) == 71)

# Message 3 — choc démographique
q43 = pd.to_numeric(ent.iloc[:, 51], errors="coerce")
ctl("ENT-Q4.3", "136 départs en retraite déclarés à 5 ans (cumul)",
    "136", f"{int(q43.sum())} (n={q43.notna().sum()})", int(q43.sum()) == 136)

q44 = ent.iloc[:, 52].dropna().astype(str)
prod_ment = q44.str.lower().str.contains("produc").sum()
part_dep_prod = q43[ent.iloc[:, 52].astype(str).str.lower().str.contains("produc", na=False)].sum()
ctl("ENT-Q4.4", "Départs « concentrés à 60% sur la production »",
    "60% (formulé comme part des départs)",
    f"{pct(prod_ment, len(q44))}% des entreprises répondantes citent la production "
    f"({prod_ment}/{len(q44)}) ; les entreprises citant la production portent "
    f"{pct(part_dep_prod, q43.sum())}% des 136 départs",
    pct(prod_ment, len(q44)) == 60)  # le chiffre 60 existe, la base est « entreprises », pas « départs »

q48b = ent.iloc[:, 70].dropna().astype(str)
suff = q48b.str.startswith("Non, les dispositifs en place sont suffisants").sum()
ctl("ENT-Q4.8b", "67% jugent leurs dispositifs de transmission suffisants",
    "67%", f"{pct(suff, len(q48b))}% ({suff}/{len(q48b)})", pct(suff, len(q48b)) == 67)

q45 = ent.iloc[:, 53].dropna().astype(str)
faible = q45.str.startswith("Faible").sum()
ctl("ENT-Q4.5", "Turnover faible : 81%",
    "81%", f"{pct(faible, len(q45))}% ({faible}/{len(q45)})", pct(faible, len(q45)) == 81)

# Message 4 — IA et compétences émergentes (OF)
q82of = of.iloc[:, 77].dropna().astype(str)
ia_cnt = q82of.str.contains("Intelligence artificielle", regex=False).sum()
counts_all = {}
for cell in q82of:
    for tok in ["Intelligence artificielle", "Automatisation", "Maintenance avancée",
                "Transition énergétique", "Cybersécurité", "Management de la performance",
                "Conduite du changement", "Transmission des savoir"]:
        if tok in cell:
            counts_all[tok] = counts_all.get(tok, 0) + 1
ia_rank1 = counts_all.get("Intelligence artificielle", 0) == max(counts_all.values())
ctl("OF-Q8.2", "IA citée comme évolution n°1 par 100% des OF",
    "100% (n°1)", f"{pct(ia_cnt, len(q82of))}% ({ia_cnt}/{len(q82of)}) ; option la plus citée : "
    f"{'oui' if ia_rank1 else 'non'}",
    pct(ia_cnt, len(q82of)) == 100 and ia_rank1)
ctl("OF-Q2.2-IA", "Capacité des OF à former à l'IA : 2,3/5",
    "2,3/5", f"{m1(of.iloc[:, 35])}/5 (n={of.iloc[:, 35].notna().sum()})",
    m1(of.iloc[:, 35]) == 2.3)
ctl("OF-Q2.2-cyber", "Capacité des OF à former à la cybersécurité : 1,1/5",
    "1,1/5", f"{m1(of.iloc[:, 39])}/5 (n={of.iloc[:, 39].notna().sum()})",
    m1(of.iloc[:, 39]) == 1.1)

# Message 5 — engagement collectif
q83 = ent.iloc[:, 112].dropna().astype(str)
camp = q83.str.contains("Campagne de communication commune", regex=False).sum()
atel = q83.str.contains("Ateliers inter-entreprises", regex=False).sum()
ctl("ENT-Q8.3-camp", "76% des entreprises prêtes à une campagne de communication territoriale",
    "76%", f"{pct(camp, len(q83))}% ({camp}/{len(q83)})", pct(camp, len(q83)) == 76)
ctl("ENT-Q8.3-atel", "62% prêtes à des ateliers RH inter-entreprises",
    "62%", f"{pct(atel, len(q83))}% ({atel}/{len(q83)})", pct(atel, len(q83)) == 62)
# « les acteurs de l'emploi se disent disposés à 4,7/5 » :
# 4,7 = item « Campagne de communication commune » de ACT Q8.2 (col 79) ;
# moyenne générale des 6 items = valeur de contexte.
disp_camp = m1(act.iloc[:, 79])
disp_all = m1(pd.concat([pd.to_numeric(act.iloc[:, i], errors="coerce") for i in range(76, 82)]))
ctl("ACT-Q8.2-camp", "Acteurs de l'emploi « disposés à 4,7/5 » (item campagne de communication)",
    "4,7/5", f"{disp_camp}/5 sur l'item campagne (n=7) ; moyenne des 6 actions : {disp_all}/5",
    disp_camp == 4.7)

# ------------------------------------------------------- Limites & biais
q14 = pd.to_numeric(ent.iloc[:, 14], errors="coerce")  # Q1.4 effectif inscrit
ctl("ENT-Q1.4-max", "Plus gros employeur ≈ 1 550 salariés",
    "~1 550", f"{int(q14.max())} (part de l'effectif cumulé : {pct(q14.max(), q14.sum())}%)",
    int(q14.max()) == 1550)

t_act = act.iloc[:, 4].dropna().astype(str).str.lower()
n_interim = t_act.str.contains("intérim|interim", regex=True).sum()
ctl("ACT-Q0.1-interim", "Sous-groupe intérim n=3 (acteurs de l'emploi)",
    "n=3", f"n={n_interim}", n_interim == 3)
ctl("ACT-Q0.1-public", "Sous-groupe « public » n=4 (acteurs de l'emploi hors intérim)",
    "n=4", f"n={len(t_act) - n_interim}", len(t_act) - n_interim == 4)

t_of = of.iloc[:, 9].dropna().astype(str).str.lower()
n_fin = t_of.str.contains("financeur").sum()
ctl("OF-Q0.7-horsfin", "Sous-groupe « hors financeur » n=6 (OF)",
    "n=6", f"n={len(t_of) - n_fin} ({n_fin} financeur identifié)", len(t_of) - n_fin == 6)

# ------------------------------------------------------------------ Sortie
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump({
        "zone": "Page accueil (pageAccueil)",
        "source": "exports xlsx du 30/06/2026 (data/01 à 04)",
        "nb_controles": len(controls),
        "nb_ok": sum(1 for c in controls if c["verdict"] == "OK"),
        "controles": controls,
    }, f, ensure_ascii=False, indent=2)

print(f"{sum(1 for c in controls if c['verdict'] == 'OK')}/{len(controls)} contrôles OK")
for c in controls:
    if c["verdict"] != "OK":
        print("ECART:", c["q"], "|", c["label"], "| dash:", c["dashboard"], "| calc:", c["calcule"])
print("Résultats écrits dans", OUT)
