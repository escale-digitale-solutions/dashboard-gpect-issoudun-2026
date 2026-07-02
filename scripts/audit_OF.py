# -*- coding: utf-8 -*-
"""
Audit de la section « Organismes de formation » du dashboard GPECT Issoudun.
Recalcule chaque chiffre affiché (KPIs, doughnuts, bars, échelles, moyennes
« hors financeur ») depuis data/02_organismes_formation.xlsx et produit :
  - resultats/distributions_OF.json : distributions complètes anonymisées
  - resultats/audit_OF.json         : comparaison dashboard vs calculé
Aucune donnée en dur : uniquement les valeurs attendues du dashboard (agrégats
publics) et les libellés d'options des questionnaires.
Conventions : % arrondis à l'entier (round half up), moyennes à 1 décimale,
n = réponses non vides.
"""
import json
import math
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "02_organismes_formation.xlsx"
OUT_DIST = ROOT / "resultats" / "distributions_OF.json"
OUT_AUDIT = ROOT / "resultats" / "audit_OF.json"

df = pd.read_excel(SRC, engine="openpyxl")
N = len(df)
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

# ---------------------------------------------------------------- utilitaires
def round_half_up(x, nd=0):
    m = 10 ** nd
    return math.floor(x * m + 0.5) / m

def pct(count, base):
    return int(round_half_up(100.0 * count / base))

def mean1(series):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) == 0:
        return None, 0
    return round_half_up(float(s.mean()), 1), int(len(s))

def col(i):
    return df.columns[i]

def nonempty(series):
    return series.dropna().astype(str).str.strip()

def count_option(series, option):
    """Compte les répondants dont la cellule contient le libellé de l'option."""
    s = nonempty(series)
    return int(s.str.contains(re.escape(option), regex=True).sum())

# Identification du financeur régional par son type (Q0.7), sans nom.
TYPE_COL = col(9)
FIN_MASK = df[TYPE_COL].astype(str).str.contains("financeur", case=False, na=False)
print(f"Répondants identifiés comme financeur (Q0.7) : {int(FIN_MASK.sum())}")
df_hf = df[~FIN_MASK]  # hors financeur, n attendu = 6

# ------------------------------------------------------- index des colonnes
IDENT_COLS = set(range(3, 9))  # Q0.1..Q0.6 : nominatif, exclu de tout export
FREE_TEXT_COLS = {0, 10, 22, 54, 58, 59, 63, 66, 69, 72, 74, 79, 94, 95, 97}

SCALE_GRIDS = {
    "Q2.1": list(range(23, 35)),
    "Q2.2": list(range(35, 43)),
    "Q3.3": list(range(46, 54)),
    "Q9.1": list(range(81, 89)),
}
SCALE_SINGLE = {"Q3.1": 44, "Q4.1": 55, "Q4.2": 56, "Q5.2": 61,
                "Q6.1": 67, "Q8.1": 76, "Q10.1": 91}
SCALE_COLS = set(sum(SCALE_GRIDS.values(), [])) | set(SCALE_SINGLE.values())

MULTI_COLS = {13, 15, 16, 17, 45, 57, 62, 64, 68, 70, 73, 75, 77, 80, 89, 90, 92, 93}

# ------------------------------------------------ distributions anonymisées
def short_label(name):
    return re.sub(r"\s+", " ", str(name)).strip()

distributions = {}
for i, c in enumerate(df.columns):
    if i in IDENT_COLS:
        continue
    key = f"[{i}] {short_label(c)[:120]}"
    s = df[c]
    n_ne = int(nonempty(s).shape[0])
    if i in FREE_TEXT_COLS:
        distributions[key] = {"type": "texte_libre", "n_reponses_non_vides": n_ne}
    elif i in SCALE_COLS:
        m, n = mean1(s)
        vc = pd.to_numeric(s, errors="coerce").dropna().astype(int).value_counts().sort_index()
        distributions[key] = {"type": "echelle", "n": n, "moyenne": m,
                              "ecart_type": (round_half_up(float(pd.to_numeric(s, errors='coerce').dropna().std()), 2) if n > 1 else None),
                              "distribution": {str(k): int(v) for k, v in vc.items()}}
    elif i in MULTI_COLS:
        # comptage par segment (découpage ', ') — GARDE-FOU anonymat :
        # un segment n'est publié que s'il est partagé par >= 2 répondants
        # (un texte libre « Autre » est unique à son auteur) ; les segments
        # uniques sont agrégés sans contenu.
        opts = {}
        for cell in nonempty(s):
            for part in set(re.split(r",\s+", cell)):
                p = part.strip().rstrip(",")
                if p:
                    opts[p] = opts.get(p, 0) + 1
        pub = {k2: v2 for k2, v2 in opts.items() if v2 >= 2}
        n_uniq = sum(1 for v2 in opts.values() if v2 < 2)
        distributions[key] = {"type": "choix_multiple", "n": n_ne,
                              "comptage_par_segment_partage": dict(sorted(pub.items(), key=lambda kv: -kv[1])),
                              "segments_uniques_non_publies (options rares ou texte libre)": n_uniq}
    else:
        vc = nonempty(s).value_counts()
        distributions[key] = {"type": "fermee", "n": n_ne,
                              "distribution": {str(k)[:120]: int(v) for k, v in vc.items()}}

OUT_DIST.parent.mkdir(exist_ok=True)
OUT_DIST.write_text(json.dumps(distributions, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Distributions écrites : {OUT_DIST}")

# ---------------------------------------------------------------- contrôles
checks = []

def check(q, label, dash, calc, ok=None):
    if ok is None:
        ok = str(dash) == str(calc)
    checks.append({"q": q, "label": label, "dashboard": dash,
                   "calcule": calc, "verdict": "OK" if ok else "ECART"})

def fmt1(x):
    return f"{x:.1f}".replace(".", ",") if x is not None else "NA"

# --- KPIs / doughnuts (questions fermées simples)
def check_closed(q, i, expected):  # expected: {libelle_dashboard: (option_data, pct)}
    s = nonempty(df[col(i)])
    n = len(s)
    check(q, "n", 7, n)
    for lab, (opt, p) in expected.items():
        c = int((s == opt).sum())
        check(q, lab, f"{p}%", f"{pct(c, n)}% ({c}/{n})" if pct(c, n) != p else f"{p}%")

check_closed("Q0.8", 11, {
    "Oui, certifié": ("Oui, certifié", 71),
    "Non": ("Non", 29)})
check_closed("Q1.4", 18, {
    "> 500 stagiaires/an": ("> 500 stagiaires/an", 71),
    "50 à 200": ("50 à 200 stagiaires/an", 14),
    "200 à 500": ("200 à 500 stagiaires/an", 14)})
check_closed("Q0.11", 14, {
    "Antenne permanente": ("Oui, antenne permanente", 43),
    "Sessions régulières": ("Oui, sessions régulières", 29),
    "Sessions ponctuelles": ("Oui, sessions ponctuelles", 14),
    "Aucune": ("Non, aucune implantation locale", 14)})
check_closed("Q1.7", 21, {
    "Oui, totalement équipés (KPI 86%)": ("Oui, totalement équipés", 86),
    "Aucun": ("Non, aucun plateau technique", 14)})
check_closed("Q5.1", 60, {
    "Jamais": ("Jamais", 43),
    "Régulièrement": ("Régulièrement", 29),
    "1 à 2 cas ponctuels": ("1 à 2 cas ponctuels", 29)})
check_closed("Q5.5", 65, {
    "Oui, sans condition": ("Oui, sans condition particulière", 57),
    "Non": ("Non, pas d'évolution envisagée", 29),
    "Oui, sous conditions": ("Oui, sous certaines conditions", 14)})
check_closed("Q8.3", 78, {
    "Probablement": ("Probablement", 57),
    "Non": ("Non", 29),
    "Je ne sais pas": ("Je ne sais pas", 14)})

# --- échelles simples + hors financeur
def check_scale(q, i, dash_mean, dash_hf=None, label=""):
    m, n = mean1(df[col(i)])
    check(q, f"{label} moyenne (n={n})", fmt1(dash_mean), fmt1(m))
    if dash_hf is not None:
        mh, nh = mean1(df_hf[col(i)])
        check(q, f"{label} moyenne hors financeur (n={nh})", fmt1(dash_hf), fmt1(mh))

check_scale("Q3.1", 44, 3.0, 3.0, "connaissance besoins")
check_scale("Q4.1", 55, 4.0, 4.3, "offre couvre besoins")
check_scale("Q4.2", 56, 4.0, None, "retours clients")
check_scale("Q5.2", 61, 2.6, 2.8, "maîtrise AFEST")

# --- grille Q2.1 (niveau de l'offre par domaine)
Q21_DASH = {
    "Maintenance industrielle": (24, 3.9),
    "Management & gestion d'équipe": (34, 3.9),
    "Usinage, mécanique & métaux": (23, 3.7),
    "Logistique & supply chain": (27, 3.7),
    "Programmation machines (CNC, robots)": (25, 3.4),
    "CAO / DAO / lecture de plans": (29, 3.3),
    "Compétences commerciales": (33, 3.3),
    "Sécurité & prévention": (31, 3.1),
    "Qualité, contrôle & métrologie": (26, 2.7),
    "Numérique industriel (ERP/GPAO)": (28, 2.7),
}
for lab, (i, v) in Q21_DASH.items():
    m, n = mean1(df[col(i)])
    check("Q2.1", f"{lab} (n={n})", fmt1(v), fmt1(m))
# domaines non affichés (pour information dans le json de distributions)
for i in (30, 32):
    m, n = mean1(df[col(i)])
    checks.append({"q": "Q2.1", "label": f"NON AFFICHÉ dashboard — {short_label(col(i))[-60:]}",
                   "dashboard": "absent", "calcule": f"{fmt1(m)} (n={n})", "verdict": "INFO"})

# --- grille Q2.2 (capacité compétences émergentes) avec v (n=7) et v2 (hors financeur)
Q22_DASH = {
    "Management de la performance": (40, 3.4, 3.8),
    "Conduite du changement & projet": (41, 3.3, 3.7),
    "Transmission des savoir-faire & tutorat": (42, 3.3, 3.7),
    "Maintenance avancée & prédictive": (37, 2.9, 3.2),
    "Automatisation, cobotique": (36, 2.7, 3.0),
    "Transition énergétique & décarbonation": (38, 2.4, 2.7),
    "Intelligence artificielle": (35, 2.3, 2.5),
    "Cybersécurité industrielle": (39, 1.1, 1.2),
}
for lab, (i, v, v2) in Q22_DASH.items():
    m, n = mean1(df[col(i)])
    mh, nh = mean1(df_hf[col(i)])
    check("Q2.2", f"{lab} ensemble (n={n})", fmt1(v), fmt1(m))
    check("Q2.2", f"{lab} hors financeur (n={nh})", fmt1(v2), fmt1(mh))

# --- grille Q9.1 (priorités GPECT)
Q91_DASH = {
    "Connaissance du marché & métiers en tension": (81, 4.0),
    "Développement de l'alternance & liens écoles": (87, 3.9),
    "Attractivité du territoire & communication": (85, 3.3),
    "Transition numérique & Industrie 4.0": (88, 3.3),
    "Mutualisation inter-entreprises": (84, 3.0),
    "Gestion des seniors & transmission": (86, 2.9),
    "Développement de l'offre de formation locale": (83, 2.6),
    "Aide au recrutement & sourcing": (82, 2.3),
}
for lab, (i, v) in Q91_DASH.items():
    m, n = mean1(df[col(i)])
    check("Q9.1", f"{lab} (n={n})", fmt1(v), fmt1(m))

# --- choix multiples : {question: (col, {label_dash: (texte_option, pct_dash)})}
MULTI_DASH = {
    "Q1.1": (15, {
        "Demandeurs d'emploi": ("Demandeurs d'emploi", 100),
        "Jeunes en alternance": ("Jeunes en alternance", 86),
        "Reconversion professionnelle": ("reconversion professionnelle", 71),
        "Situation de handicap": ("situation de handicap", 71),
        "Salariés en poste (continue)": ("Salariés en poste", 57),
        "Allophones / sous main de justice": ("allophones", 43),
        "Scolaires / lycéens": ("Scolaires / lycéens", 29)}),
    "Q1.2": (16, {
        "En alternance": ("En alternance", 86),
        "Certifiantes / diplômantes": ("Certifiantes / diplômantes", 86),
        "Continues (adultes)": ("Continues (salariés / adultes)", 71),
        "Sur mesure / intra": ("Sur mesure / intra-entreprise", 71),
        "Courtes / modulaires": ("Courtes / modulaires", 57),
        "VAE": ("VAE (Validation", 57),
        "Blocs de compétences": ("Blocs de compétences", 43)}),
    "Q3.2": (45, {
        "Contacts directs entreprises": ("Contacts directs avec les entreprises", 86),
        "Données France Travail / observatoires": ("Données France Travail / observatoires", 86),
        "Veille sectorielle (OPCO, branches)": ("Veille sectorielle", 71),
        "Instances locales (clubs, syndicats)": ("instances locales", 57),
        "Retours d'alternants": ("Retours d'alternants", 57),
        "Études CCI": ("rapports CCI", 29)}),
    "Q4.3": (57, {
        "Éloignement géographique": ("Éloignement géographique", 29),
        "Coût pédagogique trop élevé (PME)": ("Coût pédagogique trop élevé", 29),
        "Niveaux de qualification non adaptés": ("Niveaux de qualification non adaptés", 29),
        "Durée des parcours trop rigide": ("Durée des parcours trop rigide", 14),
        "Volume de sessions insuffisant": ("Volume de sessions insuffisant", 14),
        "Aucune lacune identifiée": ("Aucune lacune identifiée", 14)}),
    "Q5.3": (62, {
        "Résistance / méconnaissance des entreprises": ("Résistance ou méconnaissance des entreprises", 43),
        "Complexité du référentiel & traçabilité": ("Complexité du référentiel", 29),
        "Absence de modèle économique viable": ("Absence de modèle économique viable", 29),
        "Difficulté à identifier les situations apprenantes": ("situations apprenantes", 14),
        "Méconnaissance par les OPCO locaux": ("OPCO locaux", 14)}),
    "Q7.1": (73, {
        "Difficulté à mobiliser les entreprises": ("Difficulté à mobiliser les entreprises", 71),
        "Manque de financements ingénierie": ("Manque de financements pour l'ingénierie", 57),
        "Faible attractivité de certains métiers": ("Faible attractivité de certains métiers", 57),
        "Plateaux techniques absents / vétustes": ("Absence ou vétusté des plateaux techniques", 43),
        "Concurrence entre OF": ("Concurrence entre organismes de formation", 29),
        "Faible volume de demande": ("Faible volume de demande sur le territoire", 29)}),
    "Q7.2": (75, {
        "Observatoire local des métiers": ("Observatoire local des métiers", 71),
        "Financement dédié à l'adaptation pédago": ("Financement dédié à l'adaptation pédagogique", 57),
        "Plateforme mutualisée de plateaux techniques": ("Plateforme mutualisée de plateaux techniques", 43),
        "Parcours communs entre OF": ("parcours communs entre OF", 43),
        "Réseau structuré d'acteurs locaux": ("Réseau structuré d'acteurs locaux", 43),
        "Cartographie partagée de l'offre": ("Cartographie partagée de l'offre", 43)}),
    "Q8.2": (77, {
        "Intelligence artificielle": ("Intelligence artificielle", 100),
        "Automatisation / cobotique / robotique": ("Automatisation / cobotique", 71),
        "Cybersécurité industrielle": ("Cybersécurité industrielle", 71),
        "Transition énergétique & décarbonation": ("Transition énergétique", 57),
        "Maintenance avancée & prédictive": ("Maintenance avancée et prédictive", 43),
        "Transmission des savoir-faire": ("Transmission des savoir-faire", 29)}),
    "Q8.5": (80, {
        "Nouvelles filières / certifications": ("nouvelles filières / certifications", 71),
        "Renforcement partenariats entreprises": ("Renforcement des partenariats entreprises", 71),
        "Embauche de formateurs": ("Embauche de nouveaux formateurs", 57),
        "Offre digitale / e-learning": ("offre digitale / e-learning", 43),
        "Investissement plateaux techniques": ("Investissement plateaux techniques", 43)}),
    "Q9.2": (89, {
        "Informer sur l'offre existante": ("Informer sur l'offre de formation existante", 71),
        "Contribuer à l'attractivité (lycées)": ("Contribuer à l'attractivité des métiers", 71),
        "Co-construire des parcours": ("Co-construire des parcours avec les entreprises", 57),
        "Adapter l'offre aux besoins": ("Adapter l'offre aux besoins identifiés", 43),
        "Accueillir alternance / VAE": ("Accueillir des publics en alternance ou en VAE", 43),
        "Participer aux groupes de travail": ("Participer à des groupes de travail thématiques", 43)}),
    "Q10.2": (92, {
        "Image du territoire peu attractive": ("Image globale du territoire peu attractive", 71),
        "Transports / mobilité": ("Manque de transports en commun", 57),
        "Soins et santé insuffisants": ("Offre de soins et de santé insuffisante", 43),
        "Logement insuffisant / cher": ("Offre de logement insuffisante ou trop chère", 29),
        "Emploi du conjoint": ("emploi pour le conjoint", 14)}),
}
for q, (i, items) in MULTI_DASH.items():
    s = df[col(i)]
    n = int(nonempty(s).shape[0])
    check(q, "n (non vides)", 7, n)
    for lab, (opt, p) in items.items():
        c = count_option(s, opt)
        pc = pct(c, n)
        check(q, lab, f"{p}%", f"{p}%" if pc == p else f"{pc}% ({c}/{n})")

# --- verbatims Q11.1 : présence de mots-clés (aucun contenu imprimé)
Q111 = nonempty(df[col(94)]).str.lower().tolist()
def kw_found(*kws):
    return any(all(k in t for k in kws) for t in Q111)
verbatim_checks = {
    "quote 1 (communication/atouts)": kw_found("atout"),
    "quote 2 (lister les besoins)": kw_found("lister"),
    "quote 4 (embarquer les entreprises)": kw_found("embarque"),
    "quote 5 (bâton de pèlerin / pyramide des âges)": kw_found("pèlerin") and kw_found("pyramide des âges"),
}
for lab, found in verbatim_checks.items():
    check("Q11.1", lab, "cité au dashboard",
          "retrouvé dans les données" if found else "NON RETROUVÉ tel quel", ok=found)
# quote 3 : « Établir des partenariats pérennes… » — « partenariat » présent
# mais « pérennes » absent des réponses : reformulation, pas verbatim exact
check("Q11.1", "quote 3 (partenariats pérennes)", "cité au dashboard comme verbatim",
      "retrouvé en substance mais reformulé (« pérennes » absent des données)",
      ok=False)
check("Q11.1", "n (non vides)", 7, len(Q111))

# --- chiffres croisés cités dans les textes de la section OF
ent = pd.read_excel(ROOT / "data" / "01_entreprises.xlsx", engine="openpyxl")
act = pd.read_excel(ROOT / "data" / "03_acteurs_emploi.xlsx", engine="openpyxl")
syn = pd.read_excel(ROOT / "data" / "04_syndicats.xlsx", engine="openpyxl")
print(f"Croisements — ENT {ent.shape}, ACT {act.shape}, SYN {syn.shape}")

m, n = mean1(act[act.columns[53]])   # ACT Q6.1 offre de formation locale
check("croisé ACT Q6.1", f"acteurs emploi notent l'offre locale (n={n})", "2,3", fmt1(m))
m, n = mean1(ent[ent.columns[94]])   # ENT Q7.6
check("croisé ENT Q7.6", f"entreprises notent l'offre (n={n})", "3,1", fmt1(m))
m, n = mean1(ent[ent.columns[66]])   # ENT Q4.8 AFEST
check("croisé ENT Q4.8", f"AFEST chez entreprises (n={n})", "1,0", fmt1(m))
s = nonempty(syn[syn.columns[14]])
c = int(s.str.lower().str.contains("peu|partiellement").sum())
check("croisé SYN col14", f"partenaires sociaux « peu/partiellement » (n={len(s)})",
      "71%", f"{pct(c, len(s))}% ({c}/{len(s)})", ok=(pct(c, len(s)) == 71))
s = nonempty(syn[syn.columns[20]])
c = int(s.str.lower().str.contains("faible").sum())
check("croisé SYN col20", f"engagement entreprises « faible » (n={len(s)})",
      "57%", f"{pct(c, len(s))}% ({c}/{len(s)})", ok=(pct(c, len(s)) == 57))
s = nonempty(ent[ent.columns[85]])   # ENT Q6.2 compétences techniques manquantes
c = int(s.str.contains("étrologie|Qualité", regex=True).sum())
check("croisé ENT Q6.2", f"qualité/métrologie manque n°1 entreprises (n={len(s)})",
      "43%", f"{pct(c, len(s))}% ({c}/{len(s)})", ok=(pct(c, len(s)) == 43))

# ------------------------------------------------------------------- sortie
ok = sum(1 for c in checks if c["verdict"] == "OK")
ko = [c for c in checks if c["verdict"] == "ECART"]
OUT_AUDIT.write_text(json.dumps(
    {"section": "Organismes de formation", "n_college": N,
     "nb_controles": sum(1 for c in checks if c["verdict"] != "INFO"),
     "nb_ok": ok, "nb_ecarts": len(ko), "controles": checks},
    ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Audit écrit : {OUT_AUDIT}")
print(f"Contrôles : {sum(1 for c in checks if c['verdict'] != 'INFO')} — OK : {ok} — Écarts : {len(ko)}")
for c in ko:
    print(" ECART:", c["q"], "|", c["label"], "| dash =", c["dashboard"], "| calc =", c["calcule"])
for c in checks:
    if c["verdict"] == "INFO":
        print(" INFO :", c["q"], "|", c["label"], "| calc =", c["calcule"])
