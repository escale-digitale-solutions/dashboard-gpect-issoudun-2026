#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit exhaustif de la section « Acteurs de l'emploi » (objet ACT) du dashboard
contre data/03_acteurs_emploi.xlsx (7 répondants x 88 colonnes).

Sorties :
  - resultats/distributions_ACT.json : distributions complètes anonymes par colonne
  - resultats/audit_ACT.json         : liste {q, label, dashboard, calcule, verdict}

Aucune donnée brute en dur : seules les valeurs AFFICHEES par le dashboard public
(v, n=) sont référencées ici pour comparaison.
Conventions dashboard : % arrondis à l'entier (half up), moyennes 1 décimale,
n = réponses non vides. Sous-groupes : Intérim = Q0.1 « Agence d'intérim »,
Public = les autres structures.
"""
import json
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

ROOT = Path("/home/user/dashboard-gpect-issoudun-2026")
XLSX = ROOT / "data" / "03_acteurs_emploi.xlsx"
OUT_DIST = ROOT / "resultats" / "distributions_ACT.json"
OUT_AUDIT = ROOT / "resultats" / "audit_ACT.json"

df = pd.read_excel(XLSX, engine="openpyxl")
assert df.shape == (7, 88), f"shape inattendue {df.shape}"

def norm(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()

def r_pct(num, den):
    """% arrondi entier, half up."""
    return int(Decimal(num * 100) / Decimal(den).quantize(Decimal("1")) if False else
               (Decimal(num) * 100 / Decimal(den)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def r_mean(series):
    """moyenne à 1 décimale, half up ; None si vide."""
    s = series.dropna()
    if len(s) == 0:
        return None
    m = Decimal(str(float(s.mean())))
    return float(m.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

# ---- sous-groupes ----
q01 = df.iloc[:, 4].astype(str)
mask_interim = q01.map(lambda v: "interim" in norm(v))
mask_public = ~mask_interim
N_INT, N_PUB = int(mask_interim.sum()), int(mask_public.sum())

# =====================================================================
# 1) DISTRIBUTIONS COMPLETES (colonnes 4..87 ; 0-3 = méta/identifiant exclues)
# =====================================================================
distributions = {"_meta": {"fichier": "data/03_acteurs_emploi.xlsx",
                           "n_repondants": int(df.shape[0]),
                           "n_colonnes": int(df.shape[1]),
                           "colonnes_exclues": "0-3 (horodateur, consentements, nom de structure)"}}
MULTI = {7}  # Q1.1 choix multiple
Q11_OPTS = ["Jeunes de moins de 26 ans", "Seniors de 50 ans et plus",
            "Publics issus des QPV", "Travailleurs handicapés",
            "Personnes en reconversion professionnelle",
            "Demandeurs d’emploi longue durée", "Réfugiés / primo-arrivants"]

for i in range(4, df.shape[1]):
    col = df.columns[i]
    s = df.iloc[:, i]
    nn = int(s.notna().sum())
    key = f"[{i}] {col}"
    if i in MULTI:
        counts = {opt: int(s.dropna().astype(str).str.contains(opt, regex=False).sum())
                  for opt in Q11_OPTS}
        distributions[key] = {"type": "choix_multiple", "n": nn, "options": counts}
    elif pd.api.types.is_numeric_dtype(s):
        sd = s.dropna()
        distributions[key] = {
            "type": "echelle", "n": nn,
            "moyenne": round(float(sd.mean()), 3) if nn else None,
            "ecart_type": round(float(sd.std(ddof=1)), 3) if nn > 1 else None,
            "distribution": {str(int(k)): int(v) for k, v in sd.value_counts().sort_index().items()},
        }
    else:
        vc = s.dropna().astype(str).value_counts()
        distributions[key] = {"type": "categorielle", "n": nn,
                              "distribution": {k: int(v) for k, v in vc.items()}}

# =====================================================================
# 2) AUDIT DES CHIFFRES DU DASHBOARD
# =====================================================================
audit = []

def check(q, label, dash, calc):
    audit.append({"q": q, "label": label, "dashboard": dash, "calcule": calc,
                  "verdict": "OK" if str(dash) == str(calc) else "ECART"})

def fmt_mean(v):
    return "n/a" if v is None else f"{v:.1f}".replace(".", ",")

def check_mean(q, label, dash, colidx, mask=None):
    s = df.iloc[:, colidx]
    if mask is not None:
        s = s[mask]
    check(q, label, f"{dash:.1f}".replace(".", ","), fmt_mean(r_mean(s)))

def check_pct(q, label, dash, colidx, value, contains=False):
    s = df.iloc[:, colidx].dropna().astype(str)
    n = len(s)
    cnt = int(s.str.contains(value, regex=False).sum()) if contains else int((s == value).sum())
    pct = int((Decimal(cnt) * 100 / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    check(q, label, f"{dash}%", f"{pct}% ({cnt}/{n})" if pct != dash else f"{dash}%")

def check_n(q, label, dash, colidxs):
    ns = sorted({int(df.iloc[:, i].notna().sum()) for i in colidxs})
    calc = ns[0] if len(ns) == 1 else f"variable {ns}"
    check(q, label, f"n={dash}", f"n={calc}")

# ---- Effectif global & composition (headline/sub) ----
check("ACT", "n collège", "n=7", f"n={df.shape[0]}")
check("Q0.1", "sub : nb agences d'intérim", "3", str(N_INT))
check("Q0.1", "sub : nb opérateurs publics", "4", str(N_PUB))

# ---- KPIs d'en-tête ----
check_mean("Q3.1", "KPI difficulté maintenance industrielle", 4.9, 25)
check_mean("Q3.1", "KPI difficulté programmation CNC/robots", 4.9, 26)
check_mean("Q2.2", "KPI manque de compétences techniques", 4.3, 17)
check_mean("Q6.1", "KPI offre de formation locale adaptée", 2.3, 53)
check_mean("Q5.3", "KPI durée/stabilité des emplois obtenus", 4.1, 52)

# ---- Doughnuts profil ----
check_n("Q0.1", "n bloc type de structure", 7, [4])
check_pct("Q0.1", "Agence d'intérim", 43, 4, "intérim", contains=True)
check_pct("Q0.1", "France Travail", 14, 4, "France Travail")
check_pct("Q0.1", "Mission Locale", 14, 4, "Mission Locale")
check_pct("Q0.1", "Cap Emploi", 14, 4, "Cap Emploi")
check_pct("Q0.1", "APEC", 14, 4, "APEC")
check_n("Q0.3", "n bloc personnes accompagnées/an", 7, [6])
check_pct("Q0.3", "500 à 1000", 43, 6, "500 à 1000 personnes")
check_pct("Q0.3", "100 à 500", 29, 6, "100 à 500 personnes")
check_pct("Q0.3", "1000 à 3000", 14, 6, "1000 à 3000 personnes")
check_pct("Q0.3", "< 100", 14, 6, "Moins de 100 personnes")
check_n("Q1.3", "n bloc niveau de qualification dominant", 7, [15])
check_pct("Q1.3", "CAP / BEP", 57, 15, "CAP / BEP")
check_pct("Q1.3", "Bac", 14, 15, "Bac")
check_pct("Q1.3", "Sans diplôme", 14, 15, "Sans diplôme")
check_pct("Q1.3", "Bac +3 et plus", 14, 15, "Bac +3 et plus")

# ---- Q1.2 échelle par sous-groupe (Intérim v / Public v2) ----
q12 = [("Seniors de 50 ans et +", 9, 4.3, 3.5),
       ("Jeunes de moins de 26 ans", 8, 4.7, 2.8),
       ("Personnes en reconversion", 12, 3.7, 2.8),
       ("Travailleurs handicapés", 11, 2.7, 3.0),
       ("Demandeurs d'emploi longue durée", 13, 2.3, 3.0),
       ("Réfugiés / primo-arrivants", 14, 2.3, 2.2)]
check_n("Q1.2", "n bloc importance des publics", 7, [c for _, c, _, _ in q12])
for lab, c, vi, vp in q12:
    check_mean("Q1.2", f"{lab} — intérim", vi, c, mask_interim)
    check_mean("Q1.2", f"{lab} — public", vp, c, mask_public)

# ---- KPIs adéquation ----
check_mean("Q2.1", "KPI adéquation profils/besoins", 2.9, 16)
check_mean("Q4.1", "KPI niveau de qualification insuffisant", 4.3, 40)

# ---- Q3.1 échelle (11 items affichés / 12 colonnes) ----
q31 = [("Maintenance industrielle", 25, 4.9), ("Programmation CNC/robots", 26, 4.9),
       ("Usinage & mécanique", 24, 4.4), ("CAO/DAO & lecture de plans", 30, 4.3),
       ("Numérique industriel", 29, 4.0), ("Transition énergétique", 31, 4.0),
       ("Qualité & métrologie", 27, 3.9), ("Sécurité & prévention", 32, 3.3),
       ("Management d'équipe", 35, 3.1), ("Logistique & supply chain", 28, 3.0),
       ("Conduite véhicules/engins", 33, 2.4)]
check_n("Q3.1", "n bloc difficulté à trouver", 7, [c for _, c, _ in q31])
for lab, c, v in q31:
    check_mean("Q3.1", lab, v, c)
# écart-type 0,4 cité dans l'analyse (maintenance et CNC)
for lab, c in [("Maintenance industrielle", 25), ("Programmation CNC/robots", 26)]:
    sd = df.iloc[:, c].dropna().std(ddof=1)
    check("Q3.1", f"écart-type cité 0,4 — {lab}", "0,4",
          f"{Decimal(str(float(sd))).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}".replace(".", ","))

# ---- Q4.1 échelle ----
q41 = [("Niveau de qualification insuffisant", 40, 4.3), ("Mobilité & transports", 36, 3.7),
       ("Difficulté d'intégration", 43, 3.3), ("Image des métiers industriels", 42, 3.0),
       ("Compétences de base", 41, 2.9), ("Accès aux soins/santé", 39, 2.7),
       ("Accès au logement", 37, 2.3), ("Garde d'enfants", 38, 1.7)]
check_n("Q4.1", "n bloc freins accès emploi", 7, [c for _, c, _ in q41])
for lab, c, v in q41:
    check_mean("Q4.1", lab, v, c)

# ---- Q5.2 échelle ----
q52 = [("Formation qualifiante", 50, 4.3), ("Parcours individualisés", 51, 4.3),
       ("PMSMP (immersion)", 49, 3.6), ("POEI", 48, 3.3)]
check_n("Q5.2", "n bloc efficacité dispositifs", 7, [c for _, c, _ in q52])
for lab, c, v in q52:
    check_mean("Q5.2", lab, v, c)

# ---- Q6.1 : global + sous-groupes ----
check_n("Q6.1", "n bloc offre de formation locale", 7, [53])
check_mean("Q6.1", "offre formation locale — intérim", 2.3, 53, mask_interim)
check_mean("Q6.1", "offre formation locale — public", 2.2, 53, mask_public)

# ---- Q6.2 échelle (8 items affichés / 11 colonnes) ----
q62 = [("Robotique / cobotique", 57, 4.6), ("Maintenance industrielle", 54, 4.4),
       ("Usinage / mécanique", 55, 4.1), ("Industrie 4.0 / IA", 58, 4.1),
       ("Exploitation transport", 63, 4.0), ("Management industriel", 59, 3.4),
       ("Savoir-être", 60, 2.9), ("Sécurité industrielle", 61, 2.9)]
check_n("Q6.2", "n bloc manque de formation", 7, [c for _, c, _ in q62])
for lab, c, v in q62:
    check_mean("Q6.2", lab, v, c)

# ---- Q7.1 échelle par sous-groupe ----
q71 = [("Suivi des candidats après intégration", 69, 4.0, 4.0),
       ("Qualité des relations avec les entreprises", 65, 5.0, 2.8),
       ("Partage d'infos compétences attendues", 68, 4.7, 3.0),
       ("Anticipation des besoins de recrutement", 66, 4.7, 2.0),
       ("Construction de parcours sur mesure", 67, 3.0, 2.0)]
check_n("Q7.1", "n bloc coopération entreprises", 7, [c for _, c, _, _ in q71])
for lab, c, vi, vp in q71:
    check_mean("Q7.1", f"{lab} — intérim", vi, c, mask_interim)
    check_mean("Q7.1", f"{lab} — public", vp, c, mask_public)

# ---- Q8.1 échelle ----
q81 = [("Formations courtes métiers en tension", 72, 4.4), ("Solutions de mobilité", 73, 4.4),
       ("Pré-qualification industrielle", 71, 4.3), ("Mutualisation entre entreprises", 75, 4.1),
       ("Campagnes de communication métiers", 74, 4.0), ("Plateforme de recrutement", 70, 2.1)]
check_n("Q8.1", "n bloc actions territoriales", 7, [c for _, c, _ in q81])
for lab, c, v in q81:
    check_mean("Q8.1", lab, v, c)

# ---- Q8.2 échelle ----
q82 = [("Campagne de communication commune", 79, 4.7), ("Ateliers inter-entreprises RH", 81, 4.3),
       ("Visites d'entreprises coordonnées", 78, 3.9), ("Promotion métiers lycéens/collégiens", 77, 3.3),
       ("Groupement d'employeurs", 80, 3.1), ("Aucune participation envisagée", 82, 1.4)]
check_n("Q8.2", "n bloc participation actions collectives", 7, [c for _, c, _ in q82])
for lab, c, v in q82:
    check_mean("Q8.2", lab, v, c)

# ---- Q8.3 échelle ----
q83 = [("Atelier métiers sensibles", 83, 4.3), ("Atelier attractivité & recrutement", 84, 4.3),
       ("Atelier transmission savoir-faire", 86, 4.0), ("Atelier ingénierie pédagogique", 85, 3.4),
       ("Atelier Industrie 4.0", 87, 3.4)]
check_n("Q8.3", "n bloc ateliers GPECT", 7, [c for _, c, _ in q83])
for lab, c, v in q83:
    check_mean("Q8.3", lab, v, c)

# ---- Contrôle croisé : « auto-évaluation des OF 4,0/5 » citée dans l'insight Q6.1 ----
try:
    df_of = pd.read_excel(ROOT / "data" / "02_organismes_formation.xlsx", engine="openpyxl")
    cands = [c for c in df_of.columns
             if ("couvre" in norm(c) or "repond" in norm(c)) and "besoin" in norm(c)
             and pd.api.types.is_numeric_dtype(df_of[c])]
    if cands:
        check("insight Q6.1", f"auto-éval OF (fichier OF, col: {cands[0][:60]}...)",
              "4,0", fmt_mean(r_mean(df_of[cands[0]])))
    else:
        audit.append({"q": "insight Q6.1", "label": "auto-éval OF 4,0/5",
                      "dashboard": "4,0", "calcule": "colonne non identifiée dans le fichier OF",
                      "verdict": "INVERIFIABLE"})
except Exception as e:
    audit.append({"q": "insight Q6.1", "label": "auto-éval OF 4,0/5",
                  "dashboard": "4,0", "calcule": f"fichier OF illisible: {e}",
                  "verdict": "INVERIFIABLE"})

# =====================================================================
# 3) SORTIES
# =====================================================================
OUT_DIST.parent.mkdir(exist_ok=True)
OUT_DIST.write_text(json.dumps(distributions, ensure_ascii=False, indent=1), encoding="utf-8")
OUT_AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")

ok = sum(1 for a in audit if a["verdict"] == "OK")
print(f"Contrôles : {len(audit)} | OK : {ok} | écarts : {len(audit) - ok}")
for a in audit:
    if a["verdict"] != "OK":
        print(f"  [{a['verdict']}] {a['q']} — {a['label']} : dash={a['dashboard']} vs calc={a['calcule']}")
