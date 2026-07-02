#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit exhaustif de la section « Entreprises » (objet ENT) du dashboard
contre data/01_entreprises.xlsx (export du 30/06/2026, 21 répondants).

- Recalcule chaque chiffre affiché (KPIs, doughnuts, bars, échelles, n=,
  chiffres cités dans les textes, tableau pyramide des âges, thèmes verbatims).
- Écrit resultats/audit_ENT.json  : {q, label, dashboard, calcule, verdict}
- Écrit resultats/distributions_ENT.json : agrégats anonymes par colonne
  (jamais de contenu de texte libre, colonnes Q0.x exclues).

Aucune donnée brute en dur : seules les valeurs PUBLIÉES du dashboard
(agrégats anonymes) figurent ici comme références de comparaison.
"""
import json, re, unicodedata
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
OUT_AUDIT = "/home/user/dashboard-gpect-issoudun-2026/resultats/audit_ENT.json"
OUT_DIST = "/home/user/dashboard-gpect-issoudun-2026/resultats/distributions_ENT.json"

df = pd.read_excel(SRC, engine="openpyxl")
N = len(df)
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

def rhu(x, nd=0):
    """round half up"""
    q = Decimal(1).scaleb(-nd)
    return float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))

def pct(k, n):
    return rhu(100.0 * k / n)

def col(i):
    return df.iloc[:, i]

def nn(i):
    """n réponses non vides (chaînes vides/espaces = vides)"""
    s = col(i)
    if s.dtype == object:
        return int(s.fillna("").astype(str).str.strip().ne("").sum())
    return int(s.notna().sum())

checks = []
def check(q, label, dash, calc, tol_type="exact"):
    if tol_type == "exact":
        ok = (str(dash) == str(calc))
    else:
        ok = abs(float(dash) - float(calc)) < 1e-9
    checks.append({"q": q, "label": label, "dashboard": dash,
                   "calcule": calc, "verdict": "OK" if ok else "ECART"})
    return ok

def _py(x):
    if hasattr(x, "item"):
        return x.item()
    return x

def check_num(q, label, dash, calc):
    ok = abs(float(dash) - float(calc)) < 1e-9
    checks.append({"q": q, "label": label, "dashboard": _py(dash),
                   "calcule": _py(calc), "verdict": "OK" if ok else "ECART"})
    return ok

# ---------- helpers questions ----------
def single_choice(qcode, idx, mapping, n_dash):
    """mapping: {label_dashboard: (motif_option, %_dashboard)}"""
    s = col(idx).dropna().astype(str)
    n = len(s)
    check_num(qcode, f"{qcode} n=", n_dash, n)
    vc = s.value_counts()
    for lab, (motif, vd) in mapping.items():
        k = int(sum(c for v, c in vc.items() if motif in v))
        check_num(qcode, f"{lab} (%)", vd, pct(k, n))

def multi_choice(qcode, idx, mapping, n_dash, regex=False):
    """compte 1 répondant par option si la cellule contient le motif"""
    s = col(idx).fillna("").astype(str)
    n = int(s.str.strip().ne("").sum())
    check_num(qcode, f"{qcode} n=", n_dash, n)
    for lab, (motif, vd) in mapping.items():
        if regex:
            k = int(s.str.contains(motif, case=False, regex=True).sum())
        else:
            k = int(s.str.contains(re.escape(motif), case=False).sum())
        check_num(qcode, f"{lab} (%)", vd, pct(k, n))

def scale(qcode, items, n_dash=None):
    """items: [(idx_colonne, label, moyenne_dashboard)]"""
    ns = set()
    for idx, lab, vd in items:
        s = pd.to_numeric(col(idx), errors="coerce").dropna()
        ns.add(len(s))
        check_num(qcode, f"{lab} (moyenne)", vd, rhu(s.mean(), 1))
    if n_dash is not None:
        # le dashboard affiche un n unique pour le bloc
        calc = sorted(ns)
        ok = (len(ns) == 1 and n_dash in ns)
        checks.append({"q": qcode, "label": f"{qcode} n= (bloc)", "dashboard": n_dash,
                       "calcule": str(calc if len(ns) > 1 else calc[0]),
                       "verdict": "OK" if ok else "ECART"})

def strip_acc(t):
    return unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().lower()

def theme_count(idx, patterns):
    """nb de répondants dont la réponse (sans accents, minuscule) matche un des motifs regex"""
    s = col(idx).fillna("").astype(str).map(strip_acc)
    return int(s.apply(lambda t: any(re.search(p, t) for p in patterns)).sum())

# ================= KPIs de tête =================
vc11 = col(11).dropna().astype(str)
k_met = int((vc11 == "Métallurgie, usinage et travail des métaux").sum())
check_num("KPI", "48% métallurgie", 48, pct(k_met, N))
check_num("KPI", "métallurgie 10/21 (effectif)", 10, k_met)

s24 = col(22).dropna().astype(str)
k_inv = int(s24.str.startswith("Oui").sum())
check_num("KPI", "71% investissent à 3 ans (Q2.4 Oui budgétés + à l'étude)", 71, pct(k_inv, N))

s32 = col(25).dropna().astype(str)
k_ten = int(s32.str.startswith("Oui").sum())
check_num("KPI", "95% en tension (Q3.2)", 95, pct(k_ten, N))

s18 = col(18).dropna().astype(str)
k_55 = int(s18.isin(["55 à 59 ans", "60 ans et plus"]).sum())
check_num("KPI", "29% dirigeants 55+ (Q1.8)", 29, pct(k_55, N))

# ================= Section 1 =================
single_choice("Q1.1", 11, {
    "Métallurgie / usinage / métaux": ("Métallurgie", 48),
    "Transport routier & logistique": ("Transport routier", 19),
    "Autre": ("Autre", 14),
    "Agroalimentaire": ("agroalimentaire", 5),
    "Imprimerie": ("Imprimerie", 5),
    "Maroquinerie / luxe": ("Maroquinerie", 5),
    "Aéronautique": ("Aéronautique", 5),
}, 21)

single_choice("Q1.3", 13, {
    "10 à 49 salariés": ("10 à 49", 38),
    "50 à 249 salariés": ("50 à 249", 38),
    "Moins de 10": ("Moins de 10", 14),
    "250 et plus": ("250 salariés", 10),
}, 21)
s13 = col(13).dropna().astype(str)
k_pme = int(s13.isin(["10 à 49 salariés", "50 à 249 salariés"]).sum())
check_num("Q1.3", "76% entre 10 et 249 salariés (analysis)", 76, pct(k_pme, N))

eff = pd.to_numeric(col(14), errors="coerce").dropna()
big = eff.max()
check_num("Q1.3", "plus gros employeur ~1 550 salariés (Q1.4)", 1550, big)
med_sans = eff[eff < big].median()
check_num("Q1.3", "effectif médian hors plus gros employeur = 28,5 (Q1.4)", 28.5, med_sans)

multi_choice("Q1.5", 15, {
    "Intérim": ("Intérim", 71),
    "Prestation industrielle / logistique": ("Prestation de services", 48),
    "Aucun recours externe": ("Aucun recours", 24),
}, 21)

single_choice("Q1.8", 18, {
    "45 à 54 ans": ("45 à 54", 52),
    "55 à 59 ans": ("55 à 59", 19),
    "Moins de 45 ans": ("Moins de 45", 19),
    "60 ans et +": ("60 ans", 10),
}, 21)
s22 = col(20).dropna().astype(str)
k_tr = int(s22.str.startswith("Oui").sum())
check_num("Q1.8", "19% projets de transmission (analysis, Q2.2)", 19, pct(k_tr, N))

# ================= Section 2 =================
multi_choice("Q2.1", 19, {
    "Maintenir activité / compétitivité (coûts)": ("Maintenir l'activité et la compétitivité", 67),
    "Recruter des collaborateurs qualifiés": ("Recruter des collaborateurs qualifiés", 62),
    "Fidéliser les collaborateurs": ("Fidéliser les collaborateurs", 48),
    "Développer de nouveaux marchés": ("Développer de nouveaux marchés", 38),
    "Transition écologique & énergétique": ("transition écologique et énergétique", 29),
    "Investir / moderniser l'outil": ("Investir pour moderniser", 24),
    "Diversifier / nouveaux produits": ("Diversifier l'activité", 14),
    "Évolutions technos (Industrie 4.0, IA)": ("évolutions technologiques", 10),
    "Préparer la transmission": ("Préparer la transmission", 5),
}, 21)

single_choice("Q2.3", 21, {
    "À la hausse": ("hausse", 62),
    "Stable": ("Stable", 33),
    "À la baisse": ("baisse", 5),
}, 21)
single_choice("Q2.4", 22, {
    "Oui, budgétés": ("planifiés et budgétés", 62),
    "Non": ("Non", 29),
    "Oui, à l'étude": ("à l'étude", 10),
}, 21)
single_choice("Q2.2", 20, {
    "Non": ("Non", 81),
    "Oui, défini / en cours": ("défini ou en cours", 10),
    "Oui, en réflexion": ("réflexion", 10),
}, 21)
single_choice("Q2.5", 23, {
    "Non, compétences suffisantes": ("suffisantes", 56),
    "Oui, besoins de formation": ("besoins de formation", 44),
}, 16)

# ================= Section 3 =================
# Q3.1 — thèmes verbatims (codage thématique recompté par mots-clés)
themes31 = [
    ("Usinage / réglage CN / mécanique", 33,
     [r"usinage", r"regleur", r"\bcn\b", r"commande numerique", r"mecanicien", r"mecanique", r"forge"]),
    ("Bureau études / méthodes / CAO", 29,
     [r"bureau", r"\bbe\b", r"methodes", r"\bcao\b", r"dessinateur"]),
    ("Encadrement / management", 29,
     [r"chef", r"responsable", r"\bresp\b", r"encadr", r"manag", r"dirigeant"]),
    ("Qualité / contrôle / HSE", 24,
     [r"qualite", r"controle qualite", r"controleur", r"certificateur", r"qhse", r"\bhse\b"]),
    ("Conduite / transport", 24,
     [r"conducteur", r"chauffeur", r"routier", r"\bcar\b", r"\bspl\b"]),
    ("Maintenance", 19, [r"maintenance", r"electromecanicien"]),
    ("Logistique / cariste", 19, [r"logistique", r"cariste", r"magasinier", r"supply"]),
    ("Soudure / chaudronnerie", 10, [r"soudeur", r"soudure", r"chaudron"]),
]
check_num("Q3.1", "Q3.1 n=", 21, nn(24))
for lab, vd, pats in themes31:
    k = theme_count(24, pats)
    check_num("Q3.1", f"thème « {lab} » (%) [codage mots-clés]", vd, pct(k, N))
# citation présente dans les données ? (normalisée, sous-chaîne approx.)
def quote_exists(idx, fragments):
    s = col(idx).fillna("").astype(str).map(strip_acc)
    return bool(s.apply(lambda t: all(f in t for f in fragments)).any())
q31_quotes = [
    ("Règleur, contrôle qualité, technicien méthodes", [["regleur", "qualite", "technicien methodes"]]),
    ("Chef de projet BE, technicien BE, technicien méthodes industrialisation",
     [["chef de projet", "technicien methodes industrialisation"]]),
    ("Tech méthodes & ingénieurs, tech qualité, responsable QHSE, tech maintenance, responsable supply",
     [["tech methodes", "qhse", "tech maintenance", "supply"]]),
    ("Électromécanicien, opérateur logistique/cariste, opérateur de production",
     [["electromecanicien", "cariste", "operateur de production"]]),
]
for label_q, frag_sets in q31_quotes:
    found = any(quote_exists(24, fr) for fr in frag_sets)
    checks.append({"q": "Q3.1", "label": f"citation « {label_q[:50]}… » présente",
                   "dashboard": "citée", "calcule": "retrouvée" if found else "INTROUVABLE",
                   "verdict": "OK" if found else "ECART"})

single_choice("Q3.2", 25, {
    "Oui, difficultés majeures": ("majeures", 62),
    "Oui, difficultés ponctuelles": ("ponctuelles", 33),
    "Non, pas de tension": ("pas de tension", 5),
}, 21)
single_choice("Q3.4", 36, {
    "Non, stabilité prévue": ("stabilité", 48),
    "Oui, risque partiel": ("risque partiel", 33),
    "Oui, transformation profonde": ("transformation profonde", 19),
}, 21)
s34 = col(36).dropna().astype(str)
check_num("Q3.4", "52% anticipent une transformation (analysis)", 52,
          pct(int(s34.str.startswith("Oui").sum()), N))

scale("Q3.3", [
    (26, "Pénurie de candidats sur le marché local", 4.5),
    (29, "Concurrence salariale autres entreprises/secteurs", 3.7),
    (27, "Inadéquation des compétences / diplômes", 3.1),
    (28, "Déficit d'image du métier / secteur", 3.1),
    (34, "Localisation de l'entreprise", 2.8),
    (31, "Transport", 2.5),
    (35, "Délais de formation initiale trop longs", 2.4),
    (30, "Logement", 1.7),
    (32, "Emploi du conjoint", 1.6),
    (33, "Garde d'enfant", 1.5),
], n_dash=20)

scale("Q3.5", [
    (40, "Changement attentes clients / marchés", 3.5),
    (41, "Transition énergétique & décarbonation", 3.5),
    (38, "Intégration de l'IA dans les process", 3.1),
    (39, "Évolution normes & réglementations", 3.1),
    (37, "Automatisation & robotisation", 2.8),
], n_dash=13)

# ================= Section 4 =================
# Pyramide des âges Q4.1 (cols 42..49) avec / sans plus gros employeur
pyr = df.iloc[:, 42:50].apply(pd.to_numeric, errors="coerce")
row_tot = pyr.sum(axis=1)
i_big = pd.to_numeric(col(14), errors="coerce").idxmax()  # identifié par Q1.4 max
def pyr_stats(mask):
    p = pyr[mask]
    tot = float(p.sum().sum())
    a30 = float(p.iloc[:, 0].sum() + p.iloc[:, 1].sum())
    a3144 = float(p.iloc[:, 2].sum() + p.iloc[:, 3].sum())
    a4559 = float(p.iloc[:, 4].sum() + p.iloc[:, 5].sum())
    a60 = float(p.iloc[:, 6].sum() + p.iloc[:, 7].sum())
    fem = float(p.iloc[:, [1, 3, 5, 7]].sum().sum())
    return dict(tot=tot, p30=rhu(100*a30/tot, 1), p3144=rhu(100*a3144/tot, 1),
                p4559=rhu(100*a4559/tot, 1), p60=rhu(100*a60/tot, 1),
                sen=rhu(100*(a4559+a60)/tot, 1), fem=rhu(100*fem/tot, 1))
# Lignes incohérentes (somme pyramide très éloignée de l'effectif déclaré Q1.4
# ou valeurs fractionnaires) : détection automatique — hypothèse : le dashboard
# les a exclues (sans le documenter).
q14 = pd.to_numeric(col(14), errors="coerce")
aberr = []
for ix in pyr.index:
    tot_i = pyr.loc[ix].sum()
    eff_i = q14.loc[ix]
    frac = ((pyr.loc[ix] % 1) != 0).any()
    if pd.notna(eff_i) and eff_i > 0 and (frac or tot_i > 3 * eff_i or tot_i < eff_i / 3):
        aberr.append(ix)
print(f"Pyramide Q4.1 — lignes incohérentes détectées (pyramide vs Q1.4) : {len(aberr)}")
mask_clean = ~pyr.index.isin(aberr)
avec = pyr_stats(mask_clean)                       # base nettoyée (hypothèse dashboard)
sans = pyr_stats(mask_clean & (pyr.index != i_big))
avec_brut = pyr_stats(pyr.index == pyr.index)      # base brute 21 répondants
checks.append({"q": "Q4.1", "label": "têtes base BRUTE 21 répondants (non affiché)",
               "dashboard": "3031 affiché", "calcule": avec_brut["tot"],
               "verdict": "OK" if abs(avec_brut["tot"] - 3031) < 0.5 else "ECART"})
for name, st, dash in [
    ("Avec plus gros employeur", avec,
     dict(tot=3031, p30=18.0, p3144=35.0, p4559=41.7, p60=5.3, sen=47.0, fem=36.5)),
    ("Sans plus gros employeur", sans,
     dict(tot=1506, p30=20.9, p3144=33.5, p4559=39.5, p60=6.1, sen=45.6, fem=46.5)),
]:
    check_num("Q4.1", f"{name} — têtes", dash["tot"], rhu(st["tot"]))
    check_num("Q4.1", f"{name} — <30 ans %", dash["p30"], st["p30"])
    check_num("Q4.1", f"{name} — 31-44 %", dash["p3144"], st["p3144"])
    check_num("Q4.1", f"{name} — 45-59 %", dash["p4559"], st["p4559"])
    check_num("Q4.1", f"{name} — 60+ %", dash["p60"], st["p60"])
    check_num("Q4.1", f"{name} — seniors 45+ %", dash["sen"], st["sen"])
    check_num("Q4.1", f"{name} — % femmes", dash["fem"], st["fem"])
check_num("KPI4", "47% de seniors (45+) — KPI", 47, rhu(avec["sen"]))

dep5 = pd.to_numeric(col(51), errors="coerce")
check_num("KPI4", "136 départs retraite à 5 ans (cumul Q4.3)", 136, float(dep5.sum()))
check_num("KPI4", "Q4.3 n=", 21, int(dep5.notna().sum()))

s45 = col(53).dropna().astype(str)
check_num("KPI4", "81% turnover faible & maîtrisé (Q4.5)", 81,
          pct(int(s45.str.startswith("Faible").sum()), len(s45)))

afest = pd.to_numeric(col(66), errors="coerce").dropna()
check_num("KPI4", "AFEST moyenne 1,0/5 (Q4.8)", 1.0, rhu(afest.mean(), 1))
check_num("KPI4", "AFEST écart-type nul (Q4.8)", 0.0, rhu(afest.std(ddof=0), 3))
check_num("KPI4", "AFEST n=", 21, len(afest))

single_choice("Q4.5", 53, {
    "Faible & maîtrisé": ("Faible et maîtrisé", 81),
    "En augmentation sur certains postes": ("augmentation", 19),
}, 21)
single_choice("Q4.8b", 70, {
    "Non, dispositifs suffisants": ("suffisants", 67),
    "Oui, besoin non traité": ("non traité", 29),
    "Aucun dispositif ni besoin": ("Aucun dispositif", 5),
}, 21)

multi_choice("Q4.4", 52, {
    "Production / fabrication": (r"production\s*/\s*fabrication", 60),
    "Logistique": (r"logistique", 25),
    "Commerce / ADV": (r"commerce\s*/\s*adv", 25),
    "Conduite / transport": (r"conduite|conducteur|chauffeur", 20),
    "Qualité": (r"qualité", 15),
    "Maintenance": (r"maintenance", 15),
    "Bureau d'études": (r"bureau d'études", 15),
    "Management de proximité": (r"management de proximité", 15),
}, 20, regex=True)

scale("Q4.8", [
    (68, "Documentation des procédures", 3.5),
    (69, "Formation interne structurée", 3.3),
    (65, "Tutorat / binôme junior-senior", 3.2),
    (67, "Dispositifs France Travail (POEI, PMSMP)", 2.1),
    (66, "AFEST", 1.0),
], n_dash=21)

scale("Q4.7", [
    (63, "Départ vers la concurrence", 2.8),
    (55, "Rémunération & avantages", 2.7),
    (56, "Conditions de travail", 2.4),
    (62, "Qualité de vie / équilibre", 2.2),
    (64, "Autre secteur", 2.1),
    (57, "Horaires", 2.0),
    (58, "Pénibilité", 2.0),
    (59, "Manque de perspectives", 1.9),
], n_dash=21)

# ================= Section 5 =================
single_choice("Q5.1", 71, {"Oui": ("Oui", 95), "Non": ("Non", 5)}, 21)

dif = pd.to_numeric(col(72), errors="coerce").dropna()
check_num("Q5.2", "difficulté de recrutement 3,8/5", 3.8, rhu(dif.mean(), 1))
check_num("Q5.2", "Q5.2 n=", 20, len(dif))

rec = pd.to_numeric(col(81), errors="coerce").dropna()
check_num("Q5.4", "131 recrutements prévus (cumul)", 131, float(rec.sum()))
check_num("Q5.4", "médiane 5", 5, float(rec.median()))
check_num("Q5.4", "Q5.4 n=", 21, len(rec))

multi_choice("Q5.5", 82, {
    "Remplacement départs retraite": ("départs à la retraite", 76),
    "Accroissement de l'activité": ("Accroissement", 62),
    "Remplacement départs volontaires": ("départs volontaires", 43),
    "Lancement nouvelle activité": ("Lancement", 5),
}, 21)

scale("Q5.3", [
    (73, "Manque de candidats sur le marché local", 4.3),
    (80, "Concurrence d'autres employeurs locaux", 3.2),
    (74, "Inadéquation compétences / diplômes", 2.8),
    (75, "Prétentions salariales trop élevées", 2.8),
    (79, "Déficit d'image de l'entreprise/secteur", 2.7),
    (77, "Mobilité (transports, véhicule)", 2.1),
    (76, "Logement", 1.4),
    (78, "Emploi du conjoint", 1.4),
], n_dash=21)

multi_choice("Q5.6", 83, {
    "Relations écoles / CFA / lycées": ("Relations avec les écoles", 81),
    "Communication réseaux sociaux": ("réseaux sociaux", 76),
    "Partenariat France Travail / ML / Cap Emploi": ("Partenariat avec France Travail", 71),
    "Portes ouvertes / visites": ("Portes ouvertes", 48),
    "Ambassadeurs métiers": ("ambassadeurs", 24),
    "Aucune action": ("Aucune action", 5),
}, 21)

# ================= Section 6 =================
single_choice("Q6.1", 84, {
    "Plutôt, avec quelques lacunes": ("quelques lacunes", 62),
    "Tout à fait adaptées": ("Tout à fait", 33),
    "Plutôt inadaptées": ("inadaptées", 5),
}, 21)
single_choice("Q6.3", 86, {
    "Plutôt adaptées": ("Plutôt adaptées", 67),
    "Tout à fait": ("Tout à fait", 24),
    "Plutôt inadaptées": ("inadaptées", 10),
}, 21)

multi_choice("Q6.2", 85, {
    "Qualité, contrôle & métrologie": ("Qualité, contrôle et métrologie", 43),
    "Management & gestion d'équipe": ("Management et gestion d'équipe", 33),
    "Maintenance industrielle & automatismes": ("Maintenance industrielle", 29),
    "CAO / DAO / lecture de plans": ("CAO / DAO", 29),
    "Aucun manque identifié": ("Aucun manque", 24),
    "Logistique / supply chain": ("Logistique, supply chain", 19),
    "Compétences commerciales": ("commerciales", 19),
    "Usinage / mécanique": ("Usinage, mécanique", 14),
    "Programmation machines (CNC, automates)": ("Programmation de machines", 14),
    "Numérique industriel (ERP/GPAO)": ("Numérique industriel", 14),
}, 21)

multi_choice("Q6.4", 87, {
    "Rigueur & respect des procédures": ("Rigueur", 91),
    "Culture sécurité & vigilance": ("Culture sécurité", 45),
    "Autonomie & initiative": ("Autonomie", 36),
    "Travail en équipe": ("Travail en équipe", 36),
    "Engagement & responsabilité": ("Engagement", 36),
}, 11)

multi_choice("Q6.5", 88, {
    "Intelligence artificielle": ("Intelligence artificielle", 38),
    "Transition énergétique & décarbonation": ("Transition énergétique", 33),
    "Transmission des savoir-faire & tutorat": ("Transmission des savoir-faire", 33),
    "Animation d'équipes (agile/projet)": ("Animation d'équipes", 29),
    "Automatisation, cobotique": ("Automatisation, cobotique", 24),
    "Cybersécurité industrielle": ("Cybersécurité", 24),
    "Conduite du changement": ("Conduite du changement", 24),
    "Outils numériques collaboratifs": ("outils numériques collaboratifs", 24),
}, 21)

# ================= Section 7 =================
single_choice("Q7.2", 90, {
    "Oui, mobilisés régulièrement": ("mobilisons régulièrement", 90),
    "Non, dispositifs mal connus": ("Non", 10),
}, 21)
single_choice("Q7.4", 92, {
    "Oui, régulièrement": ("Oui, régulièrement", 76),
    "Non, pas envisagé": ("pas envisagé", 14),
    "Non, mais ouverts": ("ouverts", 10),
}, 21)
multi_choice("Q7.1", 89, {
    "Développement des compétences métiers": ("compétences métiers", 90),
    "Obligatoires (sécurité, habilitations)": ("obligatoires", 71),
    "Management & développement personnel": ("management et développement personnel", 29),
}, 21)
single_choice("Q7.5", 93, {
    "Oui, majoritairement": ("majoritairement", 50),
    "Partiellement": ("Partiellement", 28),
    "Non, autres territoires": ("autres territoires", 22),
}, 18)
multi_choice("Q7.3", 91, {
    "Difficulté à libérer les salariés": ("libérer les salariés", 38),
    "Coût pédagogique trop élevé": ("Coût pédagogique", 29),
    "Aucun frein particulier": ("Aucun frein", 29),
    "Faible appétence des salariés": ("appétence", 24),
    "Absence de formation adaptée localement": ("Absence de formation adaptée", 14),
    "Manque de temps pour organiser": ("Manque de temps", 14),
}, 21)
single_choice("Q7.8", 101, {
    "Faible & ponctuelle": ("faible et ponctuelle", 43),
    "Régulière & structurée": ("régulière et structurée", 38),
    "Aucune coopération": ("Aucune", 19),
}, 21)
s78 = col(101).dropna().astype(str)
k_fn = int((~s78.str.contains("régulière et structurée")).sum())
check_num("Q7.8", "62% coopération faible ou nulle (analysis)", 62, pct(k_fn, len(s78)))

off = pd.to_numeric(col(94), errors="coerce").dropna()
check_num("Q7.6", "offre formation locale 3,1/5", 3.1, rhu(off.mean(), 1))
check_num("Q7.6", "médiane 3", 3, float(off.median()))
check_num("Q7.6", "Q7.6 n=", 21, len(off))

scale("Q7.9", [
    (103, "Job datings & forums de recrutement", 3.3),
    (108, "Découverte des métiers auprès des scolaires", 3.2),
    (102, "Diffusion & présélection des offres", 3.1),
    (104, "Parcours de pré-qualification", 2.8),
    (109, "Suivi post-recrutement / intégration", 2.7),
    (107, "Partage de viviers entre entreprises", 2.6),
    (106, "Parcours de formation sur mesure (CQP, titres pro)", 2.5),
], n_dash=21)

# ================= Section 8 =================
multi_choice("Q8.1", 110, {
    "Image du territoire peu attractive": ("Image globale du territoire", 95),
    "Offre de soins / santé insuffisante": ("soins", 67),
    "Transports en commun / mobilité": ("transports en commun", 38),
    "Services à la personne (crèches, gardes)": ("services à la personne", 24),
    "Offre de logement insuffisante/chère": ("logement", 14),
    "Animation culturelle / loisirs": ("animation culturelle", 14),
}, 21)

img = pd.to_numeric(col(111), errors="coerce").dropna()
check_num("Q8.2", "image d'Issoudun 2,3/5", 2.3, rhu(img.mean(), 1))
check_num("Q8.2", "max observé : 3", 3, float(img.max()))
check_num("Q8.2", "Q8.2 n=", 21, len(img))

multi_choice("Q8.3", 112, {
    "Campagne de communication territoriale": ("Campagne de communication commune", 76),
    "Promotion des métiers (scolaires)": ("promotion des métiers industriels", 67),
    "Ateliers inter-entreprises RH": ("Ateliers inter-entreprises", 62),
    "Visites / portes ouvertes coordonnées": ("portes ouvertes coordonnées", 57),
    "Plateforme de recrutement mutualisée": ("Plateforme de recrutement", 52),
    "Groupement d'employeurs (temps partagé)": ("Groupement d'employeurs", 29),
    "Pas d'intérêt actuellement": ("pas d'intérêt", 5),
}, 21)

# ================= Section 9 =================
scale("Q9.1", [
    (117, "Attractivité du territoire & communication", 3.9),
    (113, "Connaissance du marché du travail & métiers en tension", 3.3),
    (114, "Aide au recrutement & sourcing", 2.8),
    (119, "Développement de l'alternance & liens écoles", 2.8),
    (120, "Transition numérique & Industrie 4.0", 2.7),
    (115, "Développement de l'offre de formation locale", 2.6),
    (116, "Mutualisation inter-entreprises", 2.5),
    (118, "Gestion des seniors & transmission", 2.5),
], n_dash=21)

multi_choice("Q9.2", 121, {
    "Attractivité & recrutement territorial": ("Attractivité et recrutement territorial", 48),
    "Métiers sensibles & compétences clés": ("Métiers sensibles", 38),
    "Ne souhaite pas participer": ("ne souhaite pas participer", 33),
    "Transmission savoir-faire & seniors": ("Transmission des savoir-faire", 14),
    "Industrie 4.0 & compétences de demain": ("Industrie 4.0", 14),
}, 21)

# Q9.3 — thèmes verbatims
themes93 = [
    ("Attractivité / image / com", 38,
     [r"attractivite", r"image", r"visibilite", r"communication", r"video", r"atouts"]),
    ("Observatoire métiers en tension", 24,
     [r"observatoire", r"metiers? sous tension", r"metiers? en tension", r"identification de metiers"]),
    ("Formation locale", 19, [r"formation"]),
    ("Santé / sécurité / transport", 14, [r"sante", r"securite", r"medecin", r"transport"]),
]
check_num("Q9.3", "Q9.3 n=", 21, nn(122))
for lab, vd, pats in themes93:
    k = theme_count(122, pats)
    check_num("Q9.3", f"thème « {lab} » (%) [codage mots-clés]", vd, pct(k, N))
q93_quotes = [
    ("Faire connaître nos métiers, améliorer l'image du territoire",
     [["faire connaitre", "image du territoire"], ["nos metiers", "image du territoire"]]),
    ("Identifier précisément les métiers en tension du bassin",
     [["identifi", "tension"]]),
    ("Ouvrir des formations locales (génie méca) pour les jeunes",
     [["formation", "genie mecanique", "jeunes"], ["ouverture", "genie mecanique"]]),
]
for label_q, frag_sets in q93_quotes:
    found = any(quote_exists(122, fr) for fr in frag_sets)
    checks.append({"q": "Q9.3", "label": f"citation « {label_q[:50]}… » présente",
                   "dashboard": "citée", "calcule": "retrouvée" if found else "INTROUVABLE (reformulation)",
                   "verdict": "OK" if found else "ECART"})

# ================= Distributions complètes (agrégats anonymes) =================
FREE_TEXT = {12, 16, 17, 24, 52, 54, 122, 123}   # texte libre -> n non vides seulement
NUMERIC_FREE = {14, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 72, 81, 94, 111}
MULTI = {15, 19, 82, 83, 85, 87, 88, 89, 91, 110, 112, 121}
SCALES = set(range(26, 36)) | set(range(37, 42)) | set(range(55, 70)) \
    | set(range(73, 81)) | set(range(95, 101)) | set(range(102, 110)) | set(range(113, 121))
EXCLUDE = set(range(0, 11))  # horodateur, consentements, Q0.x identifiantes

dist = {}
for i in range(df.shape[1]):
    if i in EXCLUDE:
        continue
    name = str(df.columns[i])[:110]
    key = f"[{i}] {name}"
    s = col(i)
    n = nn(i)
    if i in FREE_TEXT:
        dist[key] = {"type": "texte_libre", "n_non_vides": n}
    elif i in SCALES or (i in NUMERIC_FREE and i in (72, 94, 111)):
        v = pd.to_numeric(s, errors="coerce").dropna()
        dist[key] = {"type": "echelle", "n": int(len(v)),
                     "moyenne": rhu(v.mean(), 2) if len(v) else None,
                     "ecart_type": rhu(v.std(ddof=0), 2) if len(v) else None,
                     "distribution": {str(int(k)): int(c) for k, c in v.value_counts().sort_index().items()}}
    elif i in NUMERIC_FREE:
        v = pd.to_numeric(s, errors="coerce").dropna()
        dist[key] = {"type": "numerique", "n": int(len(v)),
                     "somme": rhu(v.sum(), 2), "moyenne": rhu(v.mean(), 2),
                     "mediane": rhu(v.median(), 2)}
    elif i in MULTI:
        raw = s.fillna("").astype(str)
        opts = {}
        # options standard = fragments présents chez >=2 répondants après split naïf
        frags = {}
        for cell in raw:
            for p in [x.strip() for x in cell.split(",") if x.strip()]:
                frags[p] = frags.get(p, 0) + 1
        for p, c in sorted(frags.items(), key=lambda x: -x[1]):
            if c >= 2:  # agrégat anonyme : options citées par au moins 2 répondants
                opts[p[:90]] = c
        dist[key] = {"type": "choix_multiple", "n": int(raw.str.strip().ne("").sum()),
                     "options_frequentes_split_virgule": opts,
                     "note": "options écrites libres uniques non listées (anonymat)"}
    else:
        vc = s.dropna().astype(str).value_counts()
        dist[key] = {"type": "choix_unique", "n": n,
                     "distribution": {k[:110]: int(v) for k, v in vc.items()}}

with open(OUT_DIST, "w", encoding="utf-8") as f:
    json.dump({"source": "01_entreprises.xlsx (30/06/2026)", "n_repondants": N,
               "colonnes": dist}, f, ensure_ascii=False, indent=1)

n_ok = sum(1 for c in checks if c["verdict"] == "OK")
with open(OUT_AUDIT, "w", encoding="utf-8") as f:
    json.dump({"section": "Entreprises (ENT)", "n_controles": len(checks),
               "n_ok": n_ok, "controles": checks}, f, ensure_ascii=False, indent=1)

print(f"\nContrôles : {len(checks)} | OK : {n_ok} | Écarts : {len(checks) - n_ok}\n")
for c in checks:
    if c["verdict"] != "OK":
        print(f"ECART  {c['q']:6} {c['label']}  dashboard={c['dashboard']}  calculé={c['calcule']}")
