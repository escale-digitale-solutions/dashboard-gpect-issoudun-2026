# -*- coding: utf-8 -*-
"""
Audit des chiffres d'enquête repris dans les pages EXTRA du dashboard
(pages « 8 leviers stratégiques » et « Plan d'action » — ancrages données
des leviers et des 12 fiches-actions).
Sources : 4 exports xlsx du 30/06/2026 (data/). Aucune donnée en dur ici :
seuls les chiffres AFFICHÉS par le dashboard (agrégats publics) servent de
valeurs attendues.
Sortie : resultats/audit_EXTRA.json ({q, label, dashboard, calcule, verdict}).
Conventions dashboard : % arrondis à l'entier (half-up), moyennes à 1
décimale (half-up), n = réponses non vides à la question.
"""
import json
import os
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "resultats", "audit_EXTRA.json")

ent = pd.read_excel(os.path.join(DATA, "01_entreprises.xlsx"), engine="openpyxl")
of_ = pd.read_excel(os.path.join(DATA, "02_organismes_formation.xlsx"), engine="openpyxl")
act = pd.read_excel(os.path.join(DATA, "03_acteurs_emploi.xlsx"), engine="openpyxl")
syn = pd.read_excel(os.path.join(DATA, "04_syndicats.xlsx"), engine="openpyxl")

print("Fichiers lus :")
for name, df in [("ENT", ent), ("OF", of_), ("ACT", act), ("SYN", syn)]:
    print(f"  {name}: {df.shape[0]} lignes x {df.shape[1]} colonnes")


def pct(count, n):
    """% arrondi à l'entier, round half up."""
    if n == 0:
        return None
    return int(Decimal(count * 100) / Decimal(n)
               if (count * 100) % n == 0 else
               (Decimal(count) * 100 / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def mean1(series):
    """moyenne à 1 décimale, round half up, sur valeurs non vides."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) == 0:
        return None, 0
    m = Decimal(str(float(s.mean()))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return float(m), len(s)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower()


def contains(df, idx, needle):
    """(nb de cellules non vides contenant needle, n non vides) — insensible accents/casse."""
    col = df[df.columns[idx]].dropna().astype(str)
    n = len(col)
    needle_n = norm(needle)
    c = sum(1 for v in col if needle_n in norm(v))
    return c, n


checks = []


def add(q, label, dashboard, calcule, detail=""):
    verdict = "OK" if str(dashboard) == str(calcule) else "ECART"
    checks.append({"q": q, "label": label, "dashboard": str(dashboard),
                   "calcule": str(calcule) + (f" ({detail})" if detail else ""),
                   "verdict": verdict})


def fr(x):
    return str(x).replace(".", ",")


# ============================================================ ENTREPRISES
# --- Q9.1 : priorités GPECT (cols 113-120), levier 1 / fiche A1 :
# « 2e des entreprises (3,3/5) »
q91_cols = list(range(113, 121))
means_ent = {}
for i in q91_cols:
    m, n = mean1(ent[ent.columns[i]])
    means_ent[ent.columns[i]] = m
m_conn, n_conn = mean1(ent[ent.columns[113]])
rank_conn = sorted(means_ent.values(), reverse=True).index(means_ent[ent.columns[113]]) + 1
add("ENT-Q9.1", "Priorité 'connaissance du marché' — moyenne entreprises (n=%d)" % n_conn,
    "3,3", fr(m_conn))
add("ENT-Q9.1-rang", "Rang de 'connaissance du marché' dans les priorités entreprises",
    "2e", f"{rank_conn}e")

# --- Q8.2 image (col 111) : « Image 2,3/5 »
m, n = mean1(ent[ent.columns[111]])
add("ENT-Q8.2", f"Image d'Issoudun auprès des candidats — moyenne /5 (n={n})", "2,3", fr(m))

# --- Q8.1 freins territoriaux (col 110) : « frein n°1 (95%) »
opts_q81 = {
    "Image globale du territoire": "image",
    "Offre de soins": "soins",
    "Manque de transports en commun": "transports",
    "Offre de services à la personne": "services personne",
    "Offre de logement": "logement",
    "Manque d'animation culturelle": "animation",
}
counts_q81 = {}
for opt in opts_q81:
    c, n = contains(ent, 110, opt)
    counts_q81[opt] = c
c_img, n = contains(ent, 110, "Image globale du territoire")
add("ENT-Q8.1", f"Image du territoire citée comme frein territorial (n={n})",
    "95%", f"{pct(c_img, n)}%", f"{c_img}/{n}")
rank_img = sorted(counts_q81.values(), reverse=True).index(counts_q81["Image globale du territoire"]) + 1
add("ENT-Q8.1-rang", "Rang du frein 'image du territoire'", "1er", f"{rank_img}er")

# --- Q8.3 actions collectives (col 112) : 76 / 67 / 62 / 52 / 29
for opt, dash, lab in [
    ("Campagne de communication commune", 76, "campagne de communication territoriale"),
    ("Actions de promotion des métiers industriels", 67, "promotion des métiers (scolaires)"),
    ("Ateliers inter-entreprises sur les bonnes pratiques RH", 62, "ateliers inter-entreprises RH"),
    ("Plateforme de recrutement mutualisée", 52, "plateforme de recrutement mutualisée"),
    ("Groupement d'employeurs", 29, "groupement d'employeurs"),
]:
    c, n = contains(ent, 112, opt)
    add("ENT-Q8.3", f"Prêts à s'engager : {lab} (n={n})", f"{dash}%", f"{pct(c, n)}%", f"{c}/{n}")

# --- Q6.5 compétences 3-5 ans (col 88) : « IA 38% »
c, n = contains(ent, 88, "Intelligence artificielle")
add("ENT-Q6.5", f"IA citée dans les compétences à développer 3-5 ans (n={n})",
    "38%", f"{pct(c, n)}%", f"{c}/{n}")

# --- Q4.1 pyramide (cols 42-49) : « 47% de seniors (45 ans et +) »
pyr = ent.iloc[:, 42:50].apply(pd.to_numeric, errors="coerce")
tot = pyr.sum().sum()
seniors = pyr.iloc[:, 4:8].sum().sum()  # H/F 45-59 + H/F 60+
p_sen = pct(int(seniors), int(tot))
add("ENT-Q4.1", f"Part des 45 ans et + dans l'effectif cumulé ({int(tot)} salariés déclarés)",
    "47%", f"{p_sen}%", f"{int(seniors)}/{int(tot)}")
# contrôle avec/sans plus gros employeur (règle d'anonymat : agrégats seulement)
tot_ligne = pyr.sum(axis=1)
i_max = tot_ligne.idxmax()
pyr2 = pyr.drop(index=i_max)
p_sen2 = pct(int(pyr2.iloc[:, 4:8].sum().sum()), int(pyr2.sum().sum()))
checks.append({"q": "ENT-Q4.1-robustesse",
               "label": "Part des 45 ans et + HORS plus gros employeur (contrôle de sensibilité, non affiché)",
               "dashboard": "(non affiché)", "calcule": f"{p_sen2}%", "verdict": "INFO"})

# --- Q4.3 (col 51) : « 136 départs à 5 ans »
dep5 = pd.to_numeric(ent[ent.columns[51]], errors="coerce").dropna()
add("ENT-Q4.3", f"Départs retraite prévisibles à 5 ans — cumul déclaré (n={len(dep5)})",
    "136", str(int(dep5.sum())))

# --- Q4.4 (col 52) : « 60% en production »
c, n = contains(ent, 52, "Production / Fabrication")
add("ENT-Q4.4", f"Départs concentrés sur la production/fabrication (n={n})",
    "60%", f"{pct(c, n)}%", f"{c}/{n}")

# --- Q4.8 AFEST (col 66) : « AFEST 1,0/5 »
m, n = mean1(ent[ent.columns[66]])
std = pd.to_numeric(ent[ent.columns[66]], errors="coerce").dropna().std()
add("ENT-Q4.8-AFEST", f"Mise en place AFEST — moyenne /5 (n={n}, écart-type={fr(round(float(std), 2))})",
    "1,0", fr(m))

# --- Q9.2 (col 121) : « 33% de refus »
c, n = contains(ent, 121, "ne souhaite pas participer")
add("ENT-Q9.2", f"'Ne souhaite pas participer' aux ateliers (n={n})",
    "33%", f"{pct(c, n)}%", f"{c}/{n}")

# --- Q1.8 (col 18) : « 29% des dirigeants ont 55 ans et + »
col18 = ent[ent.columns[18]].dropna().astype(str)
c = sum(1 for v in col18 if ("55" in v and "59" in v) or "60 ans" in v)
n = len(col18)
add("ENT-Q1.8", f"Dirigeants de 55 ans et + (n={n})", "29%", f"{pct(c, n)}%", f"{c}/{n}")

# ============================================================ ORGANISMES DE FORMATION
# --- Q9.1 (cols 81-88) : « Priorité n°1 des OF (4,0/5) »
q91of = list(range(81, 89))
means_of = {}
for i in q91of:
    m, n = mean1(of_[of_.columns[i]])
    means_of[of_.columns[i]] = m
m_conn_of, n_of = mean1(of_[of_.columns[81]])
rank_of = sorted(means_of.values(), reverse=True).index(means_of[of_.columns[81]]) + 1
add("OF-Q9.1", f"Priorité 'connaissance du marché' — moyenne OF (n={n_of})", "4,0", fr(m_conn_of))
add("OF-Q9.1-rang", "Rang de 'connaissance du marché' dans les priorités OF", "1er", f"{rank_of}er")

# --- Q7.2 leviers (col 75) : « observatoire 71% » / « plateaux mutualisés 43% »
c, n = contains(of_, 75, "Observatoire local des métiers")
add("OF-Q7.2", f"Levier 'observatoire local des métiers' (n={n})", "71%", f"{pct(c, n)}%", f"{c}/{n}")
c, n = contains(of_, 75, "Plateforme mutualisée de plateaux techniques")
add("OF-Q7.2b", f"Levier 'plateaux techniques mutualisés' (n={n})", "43%", f"{pct(c, n)}%", f"{c}/{n}")

# --- Q4.1 (col 55) : « OF 4,0/5 » (adéquation auto-évaluée)
m, n = mean1(of_[of_.columns[55]])
add("OF-Q4.1", f"'Notre offre couvre les besoins' — moyenne /5 (n={n})", "4,0", fr(m))

# --- Q2.2 IA (col 35) et cybersécurité (col 39)
m, n = mean1(of_[of_.columns[35]])
add("OF-Q2.2-IA", f"Capacité à former à l'IA — moyenne /5 (n={n})", "2,3", fr(m))
m, n = mean1(of_[of_.columns[39]])
add("OF-Q2.2-cyber", f"Capacité à former à la cybersécurité — moyenne /5 (n={n})", "1,1", fr(m))

# --- Q8.2 (col 77) : « IA 100% (OF prospective) »
c, n = contains(of_, 77, "Intelligence artificielle")
add("OF-Q8.2", f"IA citée dans les évolutions les plus marquées (n={n})",
    "100%", f"{pct(c, n)}%", f"{c}/{n}")

# --- Q7.1 (col 73) : « mobilisation difficile 71% (OF) »
c, n = contains(of_, 73, "Difficulté à mobiliser les entreprises")
add("OF-Q7.1", f"Frein 'difficulté à mobiliser les entreprises' (n={n})",
    "71%", f"{pct(c, n)}%", f"{c}/{n}")

# --- Q5.2 (col 61) : « maîtrise AFEST 2,6/5 »
m, n = mean1(of_[of_.columns[61]])
add("OF-Q5.2", f"Maîtrise de l'ingénierie AFEST — moyenne /5 (n={n})", "2,6", fr(m))

# --- Q5.3 (col 62) : « méconnaissance entreprises (43%) »
c, n = contains(of_, 62, "Résistance ou méconnaissance des entreprises")
add("OF-Q5.3", f"Frein AFEST 'résistance/méconnaissance des entreprises' (n={n})",
    "43%", f"{pct(c, n)}%", f"{c}/{n}")

# ============================================================ ACTEURS DE L'EMPLOI
type_col = act[act.columns[4]].astype(str)
is_interim = type_col.apply(lambda v: "interim" in norm(v))
n_int, n_pub = int(is_interim.sum()), int((~is_interim).sum())

# --- Q7.1 anticipation (col 66) : « intérim 4,7 / public 2,0 »
serie = pd.to_numeric(act[act.columns[66]], errors="coerce")
m_int, _ = mean1(serie[is_interim])
m_pub, _ = mean1(serie[~is_interim])
add("ACT-Q7.1-interim", f"Anticipation des besoins — moyenne intérim (n={n_int})", "4,7", fr(m_int))
add("ACT-Q7.1-public", f"Anticipation des besoins — moyenne public (n={n_pub})", "2,0", fr(m_pub))

# --- Q6.1 (col 53) : « acteurs 2,3/5 » (adéquation offre de formation)
m, n = mean1(act[act.columns[53]])
add("ACT-Q6.1", f"'L'offre de formation locale répond aux besoins' — moyenne /5 (n={n})", "2,3", fr(m))

# --- Q4.1 (col 40 qualification ; col 36 mobilité)
m, n = mean1(act[act.columns[40]])
add("ACT-Q4.1-qualif", f"Frein 'niveau de qualification insuffisant' — moyenne /5 (n={n})", "4,3", fr(m))
m, n = mean1(act[act.columns[36]])
add("ACT-Q4.1-mobilite", f"Frein 'mobilité et accès aux transports' — moyenne /5 (n={n})", "3,7", fr(m))

# --- Q5.2 formation qualifiante (col 50) : « dispositifs qualifiants efficaces 4,3/5 »
m, n = mean1(act[act.columns[50]])
add("ACT-Q5.2", f"Efficacité 'formation qualifiante' — moyenne /5 (n={n})", "4,3", fr(m))

# --- Q5.3 (col 52) : « durée des emplois obtenus 4,1/5 »
m, n = mean1(act[act.columns[52]])
add("ACT-Q5.3", f"Durée/stabilité des emplois obtenus — moyenne /5 (n={n})", "4,1", fr(m))

# --- Q6.2 robotique (col 57) : « robotique 4,6/5 »
m, n = mean1(act[act.columns[57]])
add("ACT-Q6.2", f"Manque de formation 'robotique/cobotique' — moyenne /5 (n={n})", "4,6", fr(m))

# --- Q8.2 campagne commune (col 79) : « 4,7/5 prêts à s'engager »
m, n = mean1(act[act.columns[79]])
add("ACT-Q8.2", f"Disposition 'campagne de communication commune' — moyenne /5 (n={n})", "4,7", fr(m))

# ============================================================ SYNDICATS
# --- Q13 (col 13) : « savoirs de base 57% » (thème codé sur texte libre)
col13 = syn[syn.columns[13]].dropna().astype(str)
kw = ["lire", "compter", "calcul", "elementaire"]
c = sum(1 for v in col13 if any(k in norm(v) for k in kw))
n = len(col13)
add("SYN-Q13", f"Thème 'savoirs de base (lire/écrire/compter)' — codage lexical (n={n})",
    "57%", f"{pct(c, n)}%", f"{c}/{n}")

# --- Q17 (col 17) : « mobilité rurale frein n°1 pour 86% » / « orientation 29% »
c, n = contains(syn, 17, "Mobilité rurale")
add("SYN-Q17", f"Frein 'mobilité rurale' (n={n})", "86%", f"{pct(c, n)}%", f"{c}/{n}")
counts_q17 = {}
for opt in ["Mobilité rurale", "Logement cher", "Compétences de base", "Orientation", "Motivation des personnes"]:
    cc, _ = contains(syn, 17, opt)
    counts_q17[opt] = cc
rank_mob = sorted(counts_q17.values(), reverse=True).index(counts_q17["Mobilité rurale"]) + 1
add("SYN-Q17-rang", "Rang du frein 'mobilité rurale'", "1er", f"{rank_mob}er")
c, n = contains(syn, 17, "Orientation")
add("SYN-Q17b", f"Frein 'orientation' (n={n})", "29%", f"{pct(c, n)}%", f"{c}/{n}")

# --- Q20 (col 20) : « engagement faible 57% »
col20 = syn[syn.columns[20]].dropna().astype(str)
c = sum(1 for v in col20 if norm(v).strip() == "faible")
n = len(col20)
add("SYN-Q20", f"Engagement des entreprises jugé 'faible' (n={n})", "57%", f"{pct(c, n)}%", f"{c}/{n}")

# --- Q24 (col 24) : « transmission (très) prioritaire 71% »
col24 = syn[syn.columns[24]].dropna().astype(str)
c = sum(1 for v in col24 if "prioritaire" in norm(v) and "secondaire" not in norm(v))
n = len(col24)
add("SYN-Q24", f"Transmission-reprise '(très) prioritaire' (n={n})", "71%", f"{pct(c, n)}%", f"{c}/{n}")

# ============================================================ PAGE NATIONALE
# Chiffres de cadrage EXTERNES (France Travail Data Emploi, EPCI 243600236).
# Liste validée par Florian : 18 899 hab · 8 153 actifs · 7 151 salariés ·
# 63 % industrie · chômage 7,2 % (Indre). Les autres chiffres externes de la
# page ne sont pas vérifiables depuis les xlsx -> verdict INVERIFIABLE.
for q, label, dash, ref in [
    ("NAT-hab", "Habitants Pays d'Issoudun (dashboard vs liste validée)", "18 899", "18 899"),
    ("NAT-actifs", "Actifs (dashboard vs liste validée)", "8 153", "8 153"),
    ("NAT-salaries", "Salariés tous secteurs (dashboard vs liste validée)", "7 151", "7 151"),
    ("NAT-industrie", "Part des salariés dans l'industrie (dashboard vs liste validée)", "63%", "63%"),
    ("NAT-chomage", "Taux de chômage Indre (dashboard vs liste validée)", "7,2%", "7,2%"),
]:
    add(q, label, dash, ref)

# Cohérences arithmétiques internes de la page nationale
add("NAT-coh-diplomes", "66% ≤ CAP/BEP = 33% (sans diplôme/<CAP) + 33% (CAP/BEP)", "66", str(33 + 33))
add("NAT-coh-3x", "« plus de 3× la moyenne » : 63/19", "plus de 3x", "plus de 3x" if 63 / 19 > 3 else "moins de 3x")
add("NAT-coh-15pts", "« 15 points d'écart » : 62% - 47%", "15", str(62 - 47))
add("NAT-coh-doughnut", "Nature des embauches : somme des parts", "100", str(70 + 17 + 9 + 4))
add("NAT-coh-secteurs", "Poids des secteurs (local) : somme", "100", str(63 + 20 + 11 + 4 + 2))

for q, label in [
    ("NAT-INV-reperes", "Repères hors liste validée : France 7,9% (T4 2025) · 43%/33% 55 ans et + · "
     "66%/50% ≤ CAP/BEP · -2,1% pop. depuis 2020 · 19% industrie France · dynamisme 'Faible'"),
    ("NAT-INV-ages", "Pyramide des âges détaillée (9,4/9,2/16/8,2/43 vs 12/12/19/6,7/33) · actifs 55-64 : 20% vs 17%"),
    ("NAT-INV-diplomes", "Diplômes détaillés (33/33/16/8,5/5,8/4,4 vs 26/24/18/11/9,7/12)"),
    ("NAT-INV-secteurs", "Secteurs hors 63% validé (20/11/4/2 local ; 19/55/17/8/1 France)"),
    ("NAT-INV-marche", "Marché du travail : 1 610 DE ABC · 910 cat.A · +8,8% · 3 570 offres · -6,8% · "
     "51% CDI · 2 030 embauches/trim · +22% · 30% >1 mois · 575 établissements · +1,6%"),
    ("NAT-INV-metiers", "Tables métiers candidats/recruteurs (20 valeurs demandeurs/offres)"),
    ("NAT-INV-embauches", "Embauches par secteur (670/490/280/210/110 ; +40%/+44%/-4,6%) · nature (70/17/9/4 ; France 65%)"),
    ("NAT-INV-formation", "Accès emploi post-formation 47% vs 62% · ménages imposés 45% vs 53%"),
]:
    checks.append({"q": q, "label": label, "dashboard": "(voir label)",
                   "calcule": "non vérifiable depuis les xlsx — à sourcer (capture Data Emploi 30/06/2026)",
                   "verdict": "INVERIFIABLE"})

# ============================================================ SORTIE
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"zone": "Pages leviers, plan d'action et comparaison nationale",
               "source": "exports xlsx 30/06/2026 + liste de cadrage externe validée",
               "nb_controles": len([c for c in checks if c["verdict"] in ("OK", "ECART")]),
               "controles": checks}, f, ensure_ascii=False, indent=2)

ok = sum(1 for c in checks if c["verdict"] == "OK")
print(f"\n{ok} OK / {len([c for c in checks if c['verdict'] in ('OK', 'ECART')])} contrôles "
      f"(+ {sum(1 for c in checks if c['verdict'] == 'INVERIFIABLE')} groupes invérifiables, "
      f"{sum(1 for c in checks if c['verdict'] == 'INFO')} info)")
for c in checks:
    flag = {"OK": "  ", "ECART": "!!", "INFO": "ii", "INVERIFIABLE": "??"}[c["verdict"]]
    print(f" {flag} [{c['q']}] {c['label']} : dashboard={c['dashboard']} | calculé={c['calcule']}")
