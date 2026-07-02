#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit de la section « Syndicats & organisations professionnelles » du dashboard
GPECT Issoudun 2026, contre data/04_syndicats.xlsx (7 répondants x 30 colonnes).

- Recalcule chaque chiffre affiché dans l'objet SYN du dashboard (KPIs, échelles,
  doughnuts, barres, thèmes de verbatims, chiffres cités dans les textes).
- Les valeurs « dashboard » codées ci-dessous sont les agrégats PUBLICS affichés
  sur le dashboard (aucune donnée brute individuelle dans ce script).
- Les thèmes de verbatims sont recomptés par mots-clés génériques : le codage
  qualitatif original est humain, le recomptage sert de contrôle de cohérence.
- Vérifie aussi les chiffres inter-collèges cités dans les textes de la section
  (fichiers 01_entreprises, 02_organismes_formation, 03_acteurs_emploi).

Sorties :
  resultats/distributions_SYN.json  (distributions complètes, agrégats anonymes)
  resultats/audit_SYN.json          (liste des contrôles {q,label,dashboard,calcule,verdict})
"""

import json
import math
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "resultats"
OUT.mkdir(exist_ok=True)

N = 7  # taille du collège


def pct(k, n=N):
    """Pourcentage arrondi à l'entier, round half up."""
    return int(math.floor(k * 100.0 / n + 0.5))


def moy1(s):
    """Moyenne arrondie à 1 décimale, round half up."""
    return math.floor(s.mean() * 10 + 0.5) / 10


def nonvide(s):
    return (s.fillna("").astype(str).str.strip() != "").sum()


syn = pd.read_excel(DATA / "04_syndicats.xlsx", engine="openpyxl")
assert syn.shape == (7, 30), f"format inattendu: {syn.shape}"

checks = []  # {q, label, dashboard, calcule, verdict}


def check(q, label, dash, calc, ok=None):
    if ok is None:
        ok = str(dash) == str(calc)
    checks.append({"q": q, "label": label, "dashboard": str(dash),
                   "calcule": str(calc), "verdict": "OK" if ok else "ECART"})


def col(i):
    return syn.iloc[:, i]


def txt(i):
    return col(i).fillna("").astype(str)


# ---------------------------------------------------------------- n par bloc
nn = {i: int(nonvide(col(i))) for i in range(30)}
for q, i in [("Q08", 8), ("Q09", 9), ("Q10", 10), ("Q11", 11), ("Q13", 13),
             ("Q14", 14), ("Q15", 15), ("Q17", 17), ("Q19", 19), ("Q20", 20),
             ("Q21", 21), ("Q22", 22), ("Q24", 24), ("Q25", 25), ("Q26", 26)]:
    check(q, "n= du bloc (réponses non vides)", 7, nn[i])
check("header", "n global du collège", 7, len(syn))

# ------------------------------------------------- composition (sous-titre)
# Le sous-titre du dashboard publie déjà les 7 structures par acronyme :
# on vérifie uniquement le comptage par famille (3 patronales / 2 salariés /
# 2 consulaires), sans sortir aucune correspondance individuelle.
comb = txt(2) + " " + txt(3)
fam_patronales = sum(comb.str.contains(a, case=False).any()
                     for a in ["CPME", "UIMM", "MEDEF"])
fam_salaries = sum(comb.str.contains(a, case=False).any()
                   for a in ["CGT", "CGC"])
fam_consulaires = sum(comb.str.contains(a, case=False).any()
                      for a in ["CCI", "CMA|artisan"])
check("header", "composition annoncée 3 patronales / 2 syndicats salariés / 2 consulaires",
      "3/2/2", f"{fam_patronales}/{fam_salaries}/{fam_consulaires}")

# ------------------------------------------------------------ échelles 1-5
q06 = pd.to_numeric(col(6), errors="coerce").dropna()
q07 = pd.to_numeric(col(7), errors="coerce").dropna()
q18 = pd.to_numeric(col(18), errors="coerce").dropna()
check("Q06", "dynamique économique — moyenne /5", "2,9", str(moy1(q06)).replace(".", ","))
check("Q06", "dynamique économique — médiane", 3, int(q06.median()))
check("Q06", "dynamique économique — plage « resserré [2-3] »",
      "[2-3]", f"[{int(q06.min())}-{int(q06.max())}]")
check("Q07", "coordination acteurs — moyenne /5", "2,9", str(moy1(q07)).replace(".", ","))
check("Q18", "mobilité frein — moyenne /5", "3,3", str(moy1(q18)).replace(".", ","))
check("Q18", "mobilité frein — « jusqu'à 5/5 »", 5, int(q18.max()))

# --------------------------------------------------------- questions fermées
def closed(qcode, i, expected):
    vc = col(i).value_counts()
    for label, dashv in expected.items():
        k = int(vc.get(label, 0))
        check(qcode, f"« {label} » (%)", dashv, pct(k))
    return vc

vc11 = closed("Q11", 11, {"Partiellement identifiés": 57,
                          "Bien identifiés et formalisés": 29,
                          "Peu formalisés": 14})
k = int(vc11.get("Partiellement identifiés", 0)) + int(vc11.get("Peu formalisés", 0))
check("Q11", "analysis : 71% « partiellement » ou « peu » formalisés", 71, pct(k))

vc14 = closed("Q14", 14, {"Peu adaptée": 43, "Partiellement adaptée": 29,
                          "Globalement adaptée": 29})
k = int(vc14.get("Peu adaptée", 0)) + int(vc14.get("Partiellement adaptée", 0))
check("Q14", "analysis : 71% « peu » ou « partiellement » adaptée", 71, pct(k))

vc20 = closed("Q20", 20, {"Faible": 57, "Plutôt satisfaisant": 29, "Moyen": 14})
check("Q20", "KPI : 57% engagement « faible »", 57, pct(int(vc20.get("Faible", 0))))

vc24 = closed("Q24", 24, {"Prioritaire": 43, "Très prioritaire": 29, "Secondaire": 29})
k = int(vc24.get("Prioritaire", 0)) + int(vc24.get("Très prioritaire", 0))
check("Q24", "KPI/analysis : 71% (très) prioritaire", 71, pct(k))

# ------------------------------------------------- Q17 choix multiple (bars)
OPT17 = ["Mobilité rurale", "Logement cher ou en mauvais état",
         "Compétences de base", "Orientation", "Motivation des personnes",
         "Freins sociaux"]
s17 = txt(17)
cnt17 = {o: int(s17.str.contains(re.escape(o), case=False).sum()) for o in OPT17}
# réponse libre affichée par le dashboard sous « Niveau scolaire faible (jeunes) »
cnt17_niveau = int(s17.str.contains("niveau scolaire", case=False).sum())
# réponses libres (hors options standard) : comptage sans contenu
libres = 0
for cell in s17:
    for part in cell.split(", "):
        p = part.strip()
        if p and p not in OPT17 and "niveau scolaire" not in p.lower():
            libres += 1
key_map = {"Mobilité rurale": 86, "Logement cher ou en mauvais état": 43,
           "Compétences de base": 43, "Orientation": 29,
           "Motivation des personnes": 14}
for opt, dashv in key_map.items():
    check("Q17", f"bars « {opt} » (%)", dashv, pct(cnt17[opt]))
check("Q17", "bars « Niveau scolaire faible (jeunes) » (%)", 14, pct(cnt17_niveau))
check("Q17", "KPI : 86% mobilité rurale frein n°1", 86, pct(cnt17["Mobilité rurale"]))
check("Q17", "exhaustivité : réponses non affichées dans les bars",
      "0 (implicite)",
      f"{pct(cnt17['Freins sociaux'])}% « Freins sociaux » + {libres} réponse(s) libre(s) non affichée(s)",
      ok=(cnt17["Freins sociaux"] == 0 and libres == 0))

# --------------------------------------- thèmes de verbatims (recomptage par
# mots-clés génériques ; contrôle de cohérence du codage qualitatif)
THEMES = {
    "Q08": (8, [
        ("Foncier disponible / prix", 43, r"fonci"),
        ("Axes routiers / logistique", 43, r"routi|logistiq|autorout|axe routier"),
        ("Tissu industriel implanté", 29, r"tissu"),
        ("Proximité pouvoirs publics", 29, r"pouvoirs publics|coordination des acteurs"),
        ("Data center / numérique", 14, r"data ?cent"),
    ]),
    "Q09": (9, [
        ("Qualification / main d'œuvre absente", 57,
         r"qualificat|niveau global de formation|compétences non|main d.œuvre|ressources humaines"),
        ("Transport / accessibilité", 43, r"transport|accessibilité"),
        ("Logement", 29, r"logement"),
        ("Désertification médicale", 29, r"médical"),
        ("Orientation / image des métiers", 29, r"orientation scolaire|dévalorisation des métiers"),
        ("Énergie (puissance électrique)", 14, r"électrique"),
    ]),
    "Q10": (10, [
        ("Usinage / fraiseur / tourneur / ajusteur", 43, r"usinage|fraiseu|tourneur|ajusteu"),
        ("Qualité / méthodes / contrôle", 43, r"qualit|méthod|contrôl"),
        ("Maintenance", 29, r"maintenance"),
        ("Encadrement / management", 29, r"encadrement|manager|management"),
        ("Restauration / services", 29, r"restauration"),
    ]),
    "Q13": (13, [
        ("Savoirs de base (lire / écrire / compter)", 57,
         r"lire|compter|élémentaires|niveau scolaire de base"),
        ("Savoir-être", 29, r"savoir[- ]?être"),
        ("Motivation / valeur travail", 14, r"motivation|valeur travail"),
        ("Anglais", 14, r"anglais"),
        ("Mobilité (permis, véhicule)", 14, r"permis|véhicule"),
    ]),
    "Q15": (15, [
        ("Intégration / maintien en formation", 29, r"intégration|maintenir les effectifs"),
        ("Débouchés / concurrence CFA", 29, r"débouch|concurrence"),
        ("Orientation (Éducation nationale)", 14, r"ducation nationale"),
        ("Disparition AFPA → AFPI", 14, r"afpa"),
    ]),
    "Q19": (19, [
        ("Transport adapté / navette gare-zones", 43, r"transport en commun|navette|bus"),
        ("Hébergement / colocation", 29, r"hébergement|colocation|habitat"),
        ("Aides financières mobilité", 29, r"aides|financement"),
    ]),
    "Q21": (21, [
        ("Manque de temps / sursollicitation", 43, r"temps|sollicitation|saturation"),
        ("Réunions sans résultat", 14, r"réunion"),
        ("Concurrence inter-entreprises", 14, r"concurrence"),
        ("Autarcie / méfiance historique", 14, r"autarcie|mainmise"),
    ]),
    "Q22": (22, [
        ("Ateliers courts / par thème", 57, r"ateliers courts"),
        ("Avec représentants institutionnels / élus", 29, r"institutionnels|élus"),
        ("Conditionné à un résultat concret", 14, r"résultat concret"),
    ]),
    "Q25": (25, [
        ("Accompagnement", 71, r"accompagnement"),
        ("Viviers de repreneurs / détection", 29, r"vivier"),
        ("Formation gestion / RH", 29, r"gestion|montée en compétences"),
    ]),
}
themes_out = {}
for qcode, (i, defs) in THEMES.items():
    s = txt(i)
    themes_out[qcode] = {}
    for label, dashv, rex in defs:
        k = int(s.str.contains(rex, case=False, regex=True).sum())
        themes_out[qcode][label] = {"n_repondants": k, "pct": pct(k)}
        check(qcode, f"thème « {label} » (%)", dashv, pct(k))

# KPI reprenant des thèmes déjà contrôlés
check("Q09", "KPI : 57% « qualification / main d'œuvre absente »", 57,
      themes_out["Q09"]["Qualification / main d'œuvre absente"]["pct"])

# ------------------------------------- chiffres inter-collèges cités (textes)
ent = pd.read_excel(DATA / "01_entreprises.xlsx", engine="openpyxl")
of = pd.read_excel(DATA / "02_organismes_formation.xlsx", engine="openpyxl")
act = pd.read_excel(DATA / "03_acteurs_emploi.xlsx", engine="openpyxl")

m = pd.to_numeric(act.iloc[:, 53], errors="coerce").dropna()   # ACT Q6.1
check("Q14-txt", "acteurs emploi : offre formation 2,3/5", "2,3",
      str(moy1(m)).replace(".", ","))
m = pd.to_numeric(ent.iloc[:, 94], errors="coerce").dropna()   # ENT Q7.6
check("Q14-txt", "entreprises : offre formation 3,1/5", "3,1",
      str(moy1(m)).replace(".", ","))
m = pd.to_numeric(of.iloc[:, 55], errors="coerce").dropna()    # OF Q4.1
check("Q14-txt", "OF : auto-évaluation 4,0/5", "4,0",
      f"{moy1(m):.1f}".replace(".", ","))
m = pd.to_numeric(ent.iloc[:, 31], errors="coerce").dropna()   # ENT Q3.3 transport
check("Q17-txt", "entreprises : transport 2,5/5 (cause de tensions, n=20)", "2,5",
      str(moy1(m)).replace(".", ","))
s = of.iloc[:, 73].fillna("").astype(str)                      # OF Q7.1
k = int(s.str.contains("Difficulté à mobiliser les entreprises", case=False).sum())
check("Q20-txt", "OF : 71% difficulté à mobiliser les entreprises", 71, pct(k, len(of)))
vc = ent.iloc[:, 20].value_counts()                            # ENT Q2.2
k = int(sum(v for lab, v in vc.items() if str(lab).startswith("Oui")))
check("Q24-txt", "entreprises : 19% projet de transmission d'ici 5 ans", 19, pct(k, len(ent)))
s = ent.iloc[:, 19].fillna("").astype(str)                     # ENT Q2.1
k = int(s.str.contains("transmission|cession", case=False).sum())
check("Q24-txt", "entreprises : 5% transmission en préoccupation principale", 5, pct(k, len(ent)))

# ------------------------------------------------------- distributions JSON
dist = {"fichier": "data/04_syndicats.xlsx", "n_repondants": int(len(syn)),
        "n_colonnes": int(syn.shape[1]),
        "note": ("Agrégats anonymes uniquement. Colonnes 0-4 exclues des "
                 "distributions (horodateur + identifiantes : nom, structure, "
                 "fonction, type d'acteur à modalités identifiantes). "
                 "Texte libre : uniquement le nombre de réponses non vides."),
        "colonnes": {}}

SCALES = {6, 7, 18}
CLOSED = {5, 11, 14, 20, 24}
MULTI = {17}
for i in range(30):
    cname = str(syn.columns[i])
    entry = {"index": i, "n_non_vides": nn[i]}
    if i <= 4:
        entry["type"] = "exclue (horodateur / identifiante)"
    elif i in SCALES:
        s = pd.to_numeric(col(i), errors="coerce").dropna()
        entry.update(type="echelle_1_5", n=int(len(s)),
                     moyenne=round(float(s.mean()), 3),
                     moyenne_affichee=moy1(s),
                     ecart_type=round(float(s.std(ddof=1)), 3),
                     mediane=float(s.median()), min=int(s.min()), max=int(s.max()),
                     distribution={str(int(k)): int(v)
                                   for k, v in s.value_counts().sort_index().items()})
    elif i in CLOSED:
        vc = col(i).value_counts()
        entry.update(type="fermee", n=int(vc.sum()),
                     distribution={str(k): int(v) for k, v in vc.items()},
                     pourcentages={str(k): pct(int(v), int(vc.sum()))
                                   for k, v in vc.items()})
    elif i in MULTI:
        entry.update(type="choix_multiple", n=nn[i],
                     comptage_options={o: cnt17[o] for o in OPT17},
                     reponses_libres={"niveau scolaire (affichee dashboard)": cnt17_niveau,
                                      "autres libres non affichees": libres},
                     pourcentages={o: pct(cnt17[o]) for o in OPT17})
    else:
        entry["type"] = "texte_libre"
        if i in {i2 for i2, _ in THEMES.values()}:
            qcode = [q for q, (i2, _) in THEMES.items() if i2 == i][0]
            entry["themes_recomptes_mots_cles"] = themes_out[qcode]
    dist["colonnes"][cname[:90]] = entry

with open(OUT / "distributions_SYN.json", "w", encoding="utf-8") as f:
    json.dump(dist, f, ensure_ascii=False, indent=2)

n_ok = sum(1 for c in checks if c["verdict"] == "OK")
audit = {"section": "SYN — Syndicats & organisations professionnelles",
         "source": "data/04_syndicats.xlsx (7x30) + croisements 01/02/03",
         "nb_controles": len(checks), "nb_ok": n_ok,
         "nb_ecarts": len(checks) - n_ok, "controles": checks}
with open(OUT / "audit_SYN.json", "w", encoding="utf-8") as f:
    json.dump(audit, f, ensure_ascii=False, indent=2)

print(f"Contrôles : {len(checks)} | OK : {n_ok} | Écarts : {len(checks) - n_ok}")
for c in checks:
    if c["verdict"] != "OK":
        print(f"  ECART {c['q']} — {c['label']} : dashboard={c['dashboard']} calculé={c['calcule']}")
