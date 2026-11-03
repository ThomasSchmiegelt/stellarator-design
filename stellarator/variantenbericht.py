"""variantenbericht.py — Tabellen, Steckbriefe und Bilder fuer den Variantenbericht (DE/EN) aus den Rechendaten.

  .venv/bin/python -m stellarator.variantenbericht            # erzeugt bericht/variantenbericht/gen/*.tex + bilder/
  dann: cd bericht/variantenbericht && latexmk -pdf variantenbericht.tex variant_report_en.tex

Quellen: daten/doe1_auswertung.json, doe1_kategorien.json, doe1_ersatz.json (stellarator.doe_auswertung),
sim/kopplung/test (Tragwerksversuche A-E), sim/kopplung/schwaechen, sim/kopplung/ersatz1, sim/kopplung/modell3d.
Jede Zahl im Bericht stammt aus diesen Dateien (keine Handabschrift).
"""
from __future__ import annotations
import json, os, shutil
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KOP = ROOT / "sim" / "kopplung"
DATEN = ROOT / "daten"
BER = ROOT / "bericht" / "variantenbericht"
GEN = BER / "gen"
BILD = BER / "bilder"
NAME = "Thomas Schmiegelt"

TRAGWERK = [("0000", "A", "Lager außen (bisher), 6 Verbinder je Paar", "bearing outside (previous), 6 connectors per pair"),
            ("0001", "B", "Lager innen", "bearing inside"),
            ("0002", "C", "Lager innen und außen", "bearing inside and outside"),
            ("0003", "D", "+ 12 Verbinder je Paar, Stahl (200 GPa)", "+ 12 connectors per pair, steel (200 GPa)"),
            ("0004", "E", "+ dickste Wände des Bereichs", "+ thickest walls of the range")]


def f(x, n=0):
    """Zahl mit deutschem/englischem Dezimalzeichen ueber siunitx (\\num)."""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "--"
    return f"\\num{{{x:.{n}f}}}"


def lade_e(st, nr):
    p = KOP / st / "punkte" / nr / "ergebnis.json"
    return json.loads(p.read_text()) if p.exists() else None


def tr(en, de, eng):
    return eng if en else de


# ---------------------------------------------------------------- Tabellen
def tab_grenzen(en):
    from .doe_auswertung import GRENZEN
    erkl = {"stahl": ("2/3 der Streckgrenze bei 4 K (316LN, ITER-Güte C3)", "2/3 of the 4 K yield strength (316LN, ITER grade C3)"),
            "dehn": ("REBCO-Band, Barth 2015: irreversibel ab 0,45 %", "REBCO tape, Barth 2015: irreversible above 0.45 %"),
            "pack": ("Erstwand + Blanket + Abschirmung + Vakuumgefäß (ARIES-CS-Größenordnung)", "first wall + blanket + shield + vessel (ARIES-CS order)"),
            "kern": ("ARIES-CS 2 mW/cm³; EU-DEMO streng 50 W/m³", "ARIES-CS 2 mW/cm³; EU-DEMO strict 50 W/m³"),
            "fluenz": ("REBCO-Schädigung (ARC, Sorbom 2015), 20 Volllastjahre", "REBCO damage (ARC, Sorbom 2015), 20 full-power years"),
            "ausl": ("Betriebsstrom / kritischer Strom bei 20 K", "operating / critical current at 20 K"),
            "marge": ("Abstand zur Stromteilungstemperatur", "distance to current-sharing temperature"),
            "Bn": ("mittlerer Feldfehler auf dem Plasmarand", "mean field error on the plasma boundary")}
    z = ["\\begin{tabular}{@{}lcp{0.55\\linewidth}@{}}\\toprule",
         tr(en, "Grenze & Wert & Herkunft", "Limit & value & origin") + " \\\\\\midrule"]
    for k, g in GRENZEN.items():
        art = "$\\le$" if g[2] == "max" else "$\\ge$"
        wert = "3e18" if k == "fluenz" else (f"{g[1]:g}".replace(".", "," if not en else "."))
        zeile = f"{g[5] if en else g[4]} & {art} {wert} {g[3]} & {erkl[k][1 if en else 0]}"
        z.append(zeile.replace("%", "\\%").replace("3e18", "$3\\cdot 10^{18}$") + " \\\\")
    z.append("\\bottomrule\\end{tabular}")
    return "\n".join(z)


def tab_tragwerk(en):
    z = ["\\begin{tabular}{@{}llrrrrr@{}}\\toprule",
         tr(en, " & Variante & $\\sigma_{99}$ & max. & Verformung & Dehnung WP & Stahl \\\\\n & & MPa & MPa & mm & \\% & kt",
            " & variant & $\\sigma_{99}$ & max. & deformation & WP strain & steel \\\\\n & & MPa & MPa & mm & \\% & kt") + " \\\\\\midrule"]
    for nr, b, de, eng in TRAGWERK:
        e = lade_e("test", nr); s = e["struktur"]
        m = (s["stahl"]["masse_t"] + s.get("verbinder", {}).get("masse_t", 0)) / 1e3
        z.append(f"{b} & {eng if en else de} & {f(s['stahl']['vm_p99_MPa'])} & {f(s['stahl']['vm_max_MPa'])} & {f(s['u_max_mm'])}"
                 f" & {f(100*e['bewertung']['dehnung_wp'], 2)} & {f(m, 1)} \\\\")
    z.append("\\bottomrule\\end{tabular}")
    return "\n".join(z)


def tab_rang(en, erg, n_nah=12):
    """Zulaessige (bereinigt) + die naechsten nicht zulaessigen (kleinste Verletzung)."""
    Z = erg["zeilen"]
    nah = sorted([nr for nr, z in Z.items() if not z["alle_ok"]], key=lambda nr: -Z[nr]["robust"])[:n_nah]
    from .doe_auswertung import GRENZEN
    kurz = {k: (GRENZEN[k][5] if en else GRENZEN[k][4]) for k in GRENZEN}
    z = ["\\begin{tabular}{@{}lrrrrrrrl@{}}\\toprule",
         tr(en, "Nr. & Spulen & $\\sigma_{99}$ & max. & Dehnung & $B\\cdot n$ & Freiraum & Stahl & kleinste Reserve (Engpass) \\\\\n & & MPa & MPa & \\% & ‰ & m & kt & ",
            "No. & coils & $\\sigma_{99}$ & max. & strain & $B\\cdot n$ & clearance & steel & smallest reserve (bottleneck) \\\\\n & & MPa & MPa & \\% & ‰ & m & kt & ") + " \\\\\\midrule"]
    for gruppe, liste in ((tr(en, "zulässig", "admissible"), erg["zulaessig"]), (tr(en, "knapp verfehlt", "narrowly missed"), nah)):
        z.append(f"\\multicolumn{{9}}{{@{{}}l}}{{\\textit{{{gruppe}}}}} \\\\")
        for nr in liste:
            r = Z[nr]
            q = "$^\\ast$" if r.get("quelle") == "netz_normal" else ""
            z.append(f"{nr}{q} & {r['spulen']} & {f(r['wert_stahl'])} & {f(r['stahl_max_MPa'])} & {f(r['wert_dehn'], 2)} & {f(r['wert_Bn'], 2)}"
                     f" & {f(r['freiraum_min_m'], 2)} & {f(r['masse_kt'])} & {f(100*r['robust'])}\\,\\% ({kurz[r['engpass']]}) \\\\")
    z.append("\\bottomrule\\end{tabular}")
    return "\n".join(z)


def tab_netz(en, erg):
    N = erg["netzstudie"]
    sp = [("doe1", tr(en, "doe1", "doe1")), ("netz_normal", tr(en, "Standard", "standard")),
          ("netz_s15", tr(en, "1,5× Stationen", "1.5× stations")), ("netz_q3", tr(en, "Wand 3 Zellen", "wall 3 cells"))]
    z = ["\\begin{tabular}{@{}l" + "rr" * len(sp) + "@{}}\\toprule",
         tr(en, "Entwurf", "Design") + "".join(f" & \\multicolumn{{2}}{{c}}{{{t}}}" for _, t in sp) + " \\\\",
         " " + "".join(" & $\\sigma_{99}$ & max." for _ in sp) + " \\\\\\midrule"]
    for nr in sorted(N):
        d = N[nr]; zeile = nr
        for k, _ in sp:
            if k in d:
                zeile += f" & {f(d[k]['wert_stahl'])} & {f(d[k]['stahl_max_MPa'])}"
            else:
                zeile += " & -- & --"
        z.append(zeile + " \\\\")
    z.append("\\bottomrule\\end{tabular}")
    return "\n".join(z)


def tab_kategorien(en):
    K = json.loads((DATEN / "doe1_kategorien.json").read_text())
    z = ["\\begin{tabular}{@{}lrrrrrrl@{}}\\toprule",
         tr(en, "Modell & $\\sigma_{99}$ & $P_m$ max. & $P_m$ 99\\,\\% & $P_m{+}P_b$ max. & Spitze & Verbinder $P_m$ & Ort $P_m$ max. \\\\",
            "Model & $\\sigma_{99}$ & $P_m$ max. & $P_m$ 99\\,\\% & $P_m{+}P_b$ max. & peak & connector $P_m$ & location $P_m$ max. \\\\") + "\\midrule"]
    wand = {"innen": ("Innenwand", "inner wall"), "aussen": ("Außenwand", "outer wall"), "links": ("Seitenwand", "side wall"), "rechts": ("Seitenwand", "side wall")}
    for n, k in K.items():
        o = k["Pm_ort"]
        z.append(f"{n.replace('_', '\\_')} & {f(k['sigma99_MPa'])} & {f(k['Pm_max_MPa'])} & {f(k['Pm_p99_MPa'])} & {f(k['PmPb_max_MPa'])}"
                 f" & {f(k['spitze_max_MPa'])} & {f(k['verbinder_Pm_max_MPa'])} & {tr(en, 'Spule', 'coil')} {o['spule']}, {wand[o['wand']][1 if en else 0]} \\\\")
    z.append("\\bottomrule\\end{tabular}")
    return "\n".join(z)


def tab_ersatz(en):
    E = json.loads((DATEN / "doe1_ersatz.json").read_text())
    from .doe_auswertung import PARAM_NAMEN
    z = ["\\begin{tabular}{@{}lrrp{0.5\\linewidth}@{}}\\toprule",
         tr(en, "Kenngröße & $R^2$ (KV) & 95-\\%-Band & wichtigste Stellgrößen (Anteil) \\\\",
            "Quantity & $R^2$ (CV) & 95-\\% band & most important variables (share) \\\\") + "\\midrule"]
    for n, d in E.items():
        h = d["haupteffekt"]; s = sum(h.values())
        top = sorted(h, key=h.get, reverse=True)[:3]
        z.append(f"{d['en' if en else 'de']} & {f(d['R2_kv'], 2)} & {f(100*d['abdeckung95'])}\\,\\% & "
                 + ", ".join(f"{PARAM_NAMEN[k][1 if en else 0]} ({f(100*h[k]/s)}\\,\\%)" for k in top) + " \\\\")
    z.append("\\bottomrule\\end{tabular}")
    return "\n".join(z)


def tab_studie(en, st, titel_spalte):
    """Tabelle fuer eine kleine Studie (schwaechen, ersatz1)."""
    pk = sorted((KOP / st / "punkte").glob("*/ergebnis.json"))
    if not pk:
        return tr(en, "\\textit{(noch keine Ergebnisse)}", "\\textit{(no results yet)}")
    from .doe_auswertung import kurz
    z = ["\\begin{tabular}{@{}lrrrrrrrl@{}}\\toprule",
         tr(en, f"Nr. & {titel_spalte[0]} & Stationen & $\\sigma_{{99}}$ & max. & Verformung & Dehnung & $B\\cdot n$ & alle Grenzen \\\\\n & & & MPa & MPa & mm & \\% & ‰ &",
            f"No. & {titel_spalte[1]} & stations & $\\sigma_{{99}}$ & max. & deformation & strain & $B\\cdot n$ & all limits \\\\\n & & & MPa & MPa & mm & \\% & ‰ &") + " \\\\\\midrule"]
    for p in pk:
        e = json.loads(p.read_text()); r = kurz(e)
        wert = {"schwaechen": f"{e['param']['E_verbinder_GPa']:.0f} GPa", "ersatz1": f"{4*int(e['param']['n_basis'])} " + tr(en, "Sp.", "coils")}[st]
        z.append(f"{p.parent.name} & {wert} & {r['stationen']} & {f(r['wert_stahl'])} & {f(r['stahl_max_MPa'])} & {f(r['u_max_mm'])}"
                 f" & {f(r['wert_dehn'], 2)} & {f(r['wert_Bn'], 2)} & {tr(en, 'ja', 'yes') if r['alle_ok'] else tr(en, 'nein', 'no') + ' (' + r['engpass'] + ')'} \\\\")
    z.append("\\bottomrule\\end{tabular}")
    return "\n".join(z)


def tab_ersatz1(en):
    """Vorschlaege des Ersatzmodells: Stellgroessen, Vorhersage, Rechnung, Netzpruefung (ersatz1_s15)."""
    from .doe_auswertung import kurz, GRENZEN
    pk = sorted((KOP / "ersatz1" / "punkte").glob("*/ergebnis.json"))
    if not pk:
        return tr(en, "\\textit{(noch keine Ergebnisse)}", "\\textit{(no results yet)}")
    D = json.loads((KOP / "ersatz1" / "doe.json").read_text())["punkte"]
    z = ["\\begin{tabular}{@{}lrrrrrrrrl@{}}\\toprule",
         tr(en, "Vorschlag & $E_\\text{V}$ & V./Paar & Masse & $\\sigma_{99}$ & $\\sigma_{99}$ fein & Dehnung & $B\\cdot n$ & \\multicolumn{2}{c}{Robustheit} \\\\\n"
                " & GPa & & kt & MPa & MPa & \\% & ‰ & vorherges. & gerechnet (Engpass)",
            "Proposal & $E_\\text{c}$ & c./pair & mass & $\\sigma_{99}$ & $\\sigma_{99}$ fine & strain & $B\\cdot n$ & \\multicolumn{2}{c}{robustness} \\\\\n"
            " & GPa & & kt & MPa & MPa & \\% & ‰ & predicted & computed (bottleneck)") + " \\\\\\midrule"]
    for p in pk:
        e = json.loads(p.read_text()); r = kurz(e); i = int(p.parent.name)
        fein = KOP / "ersatz1_s15" / "punkte" / p.parent.name / "ergebnis.json"
        sf = f(json.loads(fein.read_text())["struktur"]["stahl"]["vm_p99_MPa"]) if fein.exists() else "--"
        eng = GRENZEN[r["engpass"]][5 if en else 4]
        rob = f"{r['robust']:.2f}".replace(".", "." if en else ",")
        vor = f"{D[i]['_robust_ersatz']:.2f}".replace(".", "." if en else ",")
        z.append(f"V{i} & {f(r['E_verbinder_GPa'])} & {r['verbinder_je_paar']} & {f(r['masse_kt'], 1)} & {f(r['wert_stahl'])} & {sf}"
                 f" & {f(r['wert_dehn'], 2)} & {f(r['wert_Bn'], 2)} & {vor} & {rob} ({eng})" + ("" if r["alle_ok"] else tr(en, ", unzulässig", ", inadmissible")) + " \\\\")
    z.append("\\bottomrule\\end{tabular}")
    return "\n".join(z)


def tab_modell3d(en):
    z = ["\\begin{tabular}{@{}lrrrrrrrr@{}}\\toprule",
         tr(en, "Modell & Voxel & Zeit & WP & Gehäuse & Verbinder & Lager & Package & Überschneidung \\\\\n & mm & s & \\multicolumn{3}{c}{Abweichung zum FE-Modell} & m³ & m³ & Package/Gehäuse m³",
            "Model & voxel & time & WP & case & connectors & bearings & package & overlap \\\\\n & mm & s & \\multicolumn{3}{c}{deviation from FE model} & m³ & m³ & package/case m³") + " \\\\\\midrule"]
    for p in sorted((KOP / "modell3d").glob("*/pruefung.json")):
        d = json.loads(p.read_text()); a = d["abweichung_zu_fe"]; v = d["volumen_m3"]
        pack = sum(v[k] for k in v if k.startswith("package_"))
        ue = v["pruefung_package_ueberschneidung"] + v["pruefung_gehaeuse_ueberschneidung"]
        pc = lambda x: f"{'+' if x >= 0 else '−'}{f(abs(100*x), 1)}\\,\\%"
        z.append(f"{p.parent.name.replace('_', '\\_')} & {f(d['voxel_mm'])} & {f(d['picogk_s'])} & {pc(a['wickelpaket'])} & {pc(a['gehaeuse'])}"
                 f" & {pc(a.get('verbinder', 0))} & {f(v['lager'])} & {f(pack)} & {f(ue, 2)} \\\\")
    z.append("\\bottomrule\\end{tabular}")
    return "\n".join(z)


def tab_alle(en, erg):
    """Anhang: alle Entwuerfe (bereinigt), longtable."""
    Z = erg["zeilen"]
    kopf = tr(en, "Nr. & Sp. & Abst. & Länge & Kraft & W.i. & W.s. & t & n\\textsubscript{V} & E\\textsubscript{V} & R\\textsubscript{L} & $\\sigma_{99}$ & max. & Dehn. & $B\\cdot n$ & frei & Kern & Stahl & ok \\\\\n & & – & – & – & m & m & m & & GPa & m & MPa & MPa & \\% & ‰ & m & W/m³ & kt &",
              "No. & coils & dist. & length & force & w.i. & w.s. & t & n\\textsubscript{c} & E\\textsubscript{c} & R\\textsubscript{b} & $\\sigma_{99}$ & max. & strain & $B\\cdot n$ & clear. & heat & steel & ok \\\\\n & & – & – & – & m & m & m & & GPa & m & MPa & MPa & \\% & ‰ & m & W/m³ & kt &")
    z = ["{\\scriptsize\\setlength{\\tabcolsep}{2.2pt}\\begin{longtable}{@{}lrrrrrrrrrrrrrrrrrl@{}}\\toprule", kopf + " \\\\\\midrule\\endhead"]
    for nr, r in Z.items():
        ok = "\\checkmark" if r["alle_ok"] else r["engpass"]
        z.append(f"{nr}{'$^\\ast$' if r.get('quelle') == 'netz_normal' else ''} & {r['spulen']} & {f(r['abstand_sp'], 2)} & {f(r['laenge_je'], 1)} & {f(r['kraft_gewicht'], 3)}"
                 f" & {f(r['wand_innen_m'], 2)} & {f(r['wand_seite_m'], 2)} & {f(r['t_min_m'], 2)} & {int(r['verbinder_je_paar'])} & {f(r['E_verbinder_GPa'])}"
                 f" & {f(r['r_lager_m'], 1)} & {f(r['wert_stahl'])} & {f(r['stahl_max_MPa'])} & {f(r['wert_dehn'], 2)} & {f(r['wert_Bn'], 2)}"
                 f" & {f(r['freiraum_min_m'], 2)} & {f(r['wert_kern'])} & {f(r['masse_kt'])} & {ok} \\\\")
    z.append("\\bottomrule\\end{longtable}}")
    return "\n".join(z)


# ---------------------------------------------------------------- Steckbriefe
STECKBRIEFE = [("0061", "doe1/0061"), ("0169", "netz_normal/0169"), ("0093", "doe1/0093"), ("0008", "doe1/0008"),
               ("0014", "doe1/0014"), ("0017", "doe1/0017"), ("0157", "doe1/0157"), ("0063", "netz_normal/0063"),
               ("0136", "netz_normal/0136"), ("V3", "ersatz1/0003"), ("V1", "ersatz1/0001"),
               ("E_test", "test/0004"), ("A_test", "test/0000")]


def steckbrief(en, name, quelle, erg, K):
    from .doe_auswertung import kurz, GRENZEN, PARAM_NAMEN
    st, nr = quelle.split("/")
    e = lade_e(st, nr)
    if e is None:
        return ""
    r = kurz(e); p = {k: r[k] for k in PARAM_NAMEN if k in r} | {k: v for k, v in e["param"].items() if k in PARAM_NAMEN}; p.setdefault("n_basis", r["spulen"] // 4)
    titel = {"E_test": tr(en, "Tragwerksversuch E (dickste Wände)", "Support test E (thickest walls)"),
             "A_test": tr(en, "Tragwerksversuch A (Ausgangsentwurf)", "Support test A (starting design)"),
             "V3": tr(en, "Vorschlag V3 des Ersatzmodells", "Surrogate proposal V3"),
             "V1": tr(en, "Vorschlag V1 des Ersatzmodells", "Surrogate proposal V1")}.get(name, tr(en, f"Entwurf {name}", f"Design {name}"))
    z = [f"\\subsection{{{titel}}}\\label{{sb:{name}}}"]
    # Kurzurteil
    if name in erg["zulaessig"]:
        urteil = tr(en, f"Zulässig (bereinigt), Rang {erg['zulaessig'].index(name)+1} von {len(erg['zulaessig'])}; kleinste Reserve {r['robust']*100:.0f} \\% ({GRENZEN[r['engpass']][4]}).",
                    f"Admissible (cleaned), rank {erg['zulaessig'].index(name)+1} of {len(erg['zulaessig'])}; smallest reserve {r['robust']*100:.0f} \\% ({GRENZEN[r['engpass']][5]}).")
    elif name.startswith("V"):
        urteil = (tr(en, f"Vorschlag des Ersatzmodells (Abschnitt~\\ref{{sec:ersatz1}}), zulässig; kleinste Reserve {r['robust']*100:.0f} % ({GRENZEN[r['engpass']][4]}).",
                     f"Surrogate proposal (section~\\ref{{sec:ersatz1}}), admissible; smallest reserve {r['robust']*100:.0f} % ({GRENZEN[r['engpass']][5]}).")
                  if r["alle_ok"] else tr(en, f"Vorschlag des Ersatzmodells, unzulässig ({GRENZEN[r['engpass']][4]}).", f"Surrogate proposal, inadmissible ({GRENZEN[r['engpass']][5]})."))
    elif name in ("E_test", "A_test"):
        urteil = tr(en, "Gleiche 16 Spulen wie der Ausgangsentwurf; nur das Tragwerk ist verändert.", "Same 16 coils as the starting design; only the support structure differs.")
    else:
        urteil = tr(en, f"In doe1 zulässig, mit Standardnetz nicht mehr: Engpass {GRENZEN[r['engpass']][4]} (Reserve {r['robust']*100:.0f} \\%).",
                    f"Admissible in doe1, no longer with the standard mesh: bottleneck {GRENZEN[r['engpass']][5]} (reserve {r['robust']*100:.0f} \\%).")
    z.append("\\noindent\\textbf{" + tr(en, "Urteil: ", "Verdict: ") + "}" + urteil.replace("%", "\\%").replace("\\\\%", "\\%") + "\\par\\smallskip")
    # Parameter + Ergebnisse nebeneinander
    links = [f"{PARAM_NAMEN[k][1 if en else 0]} & {f(p[k], 3 if k in ('abstand_sp', 'kraft_gewicht') else (0 if k in ('verbinder_je_paar', 'E_verbinder_GPa', 'n_basis') else 2))} \\\\" for k in PARAM_NAMEN]
    links.insert(1, f"{tr(en, 'Spulen gesamt', 'coils in total')} & {r['spulen']} \\\\")
    kat = K.get(quelle, {})
    rechts = [f"$\\sigma_{{99}}$ {tr(en, 'Stahl', 'steel')} & {f(r['wert_stahl'])} MPa \\\\",
              f"{tr(en, 'größtes Element', 'largest element')} & {f(r['stahl_max_MPa'])} MPa \\\\",
              f"$P_m$ {tr(en, 'max. / 99 %', 'max. / 99 %').replace('%', '\\%')} & {f(kat.get('Pm_max_MPa'))} / {f(kat.get('Pm_p99_MPa'))} MPa \\\\" if kat else "",
              f"$P_m+P_b$ max. & {f(kat.get('PmPb_max_MPa'))} MPa \\\\" if kat else "",
              f"{tr(en, 'Verbinder σ99', 'connectors σ99')} & {f(r['verb_p99_MPa'])} MPa \\\\",
              f"{tr(en, 'Verformung max.', 'max. deformation')} & {f(r['u_max_mm'])} mm \\\\",
              f"{tr(en, 'Dehnung Wickelpaket', 'winding-pack strain')} & {f(r['wert_dehn'], 2)} \\% \\\\",
              f"{tr(en, 'Strom je Spule', 'current per coil')} & {f(r['I_MA'], 1)} MA \\\\",
              f"{tr(en, 'Feld am Leiter', 'field at conductor')} & {f(r['B_leiter_T'], 1)} T \\\\",
              f"{tr(en, 'Auslastung / Marge', 'utilisation / margin')} & {f(100*r['wert_ausl'])} \\% / {f(r['wert_marge'])} K \\\\",
              f"{tr(en, 'Feldfehler', 'field error')} $B\\cdot n$ & {f(r['wert_Bn'], 2)} ‰ \\\\",
              f"{tr(en, 'Freiraum Plasma–Gehäuse', 'clearance plasma–case')} & {f(r['freiraum_min_m'], 2)} m \\\\",
              f"{tr(en, 'Kernheizung / Fluenz', 'nuclear heating / fluence')} & {f(r['wert_kern'])} W/m³ / {r['wert_fluenz']:.1e} \\\\".replace("e+", "e"),
              f"{tr(en, 'Stahl Gehäuse + Verbinder', 'steel case + connectors')} & {f(r['masse_gehaeuse_kt'], 1)} + {f(r['masse_verbinder_kt'], 1)} kt \\\\",
              f"{tr(en, 'Verbinder gebaut', 'connectors built')} & {r['verbinder_ok']} \\\\"]
    z.append("\\begin{minipage}[t]{0.46\\linewidth}\\small\\begin{tabular}[t]{@{}lr@{}}\\toprule\\multicolumn{2}{@{}l}{\\textbf{"
             + tr(en, "Stellgrößen", "Design variables") + "}}\\\\\\midrule\n" + "\n".join(links) + "\n\\bottomrule\\end{tabular}\\end{minipage}\\hfill")
    z.append("\\begin{minipage}[t]{0.5\\linewidth}\\small\\begin{tabular}[t]{@{}lr@{}}\\toprule\\multicolumn{2}{@{}l}{\\textbf{"
             + tr(en, "Ergebnisse", "Results") + "}}\\\\\\midrule\n" + "\n".join(x for x in rechts if x) + "\n\\bottomrule\\end{tabular}\\end{minipage}\\par\\medskip")
    # Netzstudie dieses Entwurfs
    N = erg["netzstudie"].get(nr) if st in ("doe1", "netz_normal") else None
    if st == "ersatz1":
        N = {"netz_normal": {"wert_stahl": r["wert_stahl"], "stahl_max_MPa": r["stahl_max_MPa"]}}
        fein = KOP / "ersatz1_s15" / "punkte" / nr / "ergebnis.json"
        if fein.exists():
            sf = json.loads(fein.read_text())["struktur"]["stahl"]
            N["netz_s15"] = {"wert_stahl": sf["vm_p99_MPa"], "stahl_max_MPa": sf["vm_max_MPa"]}
    if N and st != "test":
        teile = []
        for k, t in (("doe1", "doe1"), ("netz_normal", tr(en, "Standard", "standard")), ("netz_s15", tr(en, "1,5× Stationen", "1.5× stations")), ("netz_q3", tr(en, "Wand 3 Zellen", "wall 3 cells"))):
            if k in N:
                teile.append(f"{t}: {N[k]['wert_stahl']:.0f}/{N[k]['stahl_max_MPa']:.0f}")
        z.append("\\noindent\\textit{" + tr(en, "Netzstudie ($\\sigma_{99}$/max. in MPa): ", "Mesh study ($\\sigma_{99}$/max. in MPa): ") + "}" + "; ".join(teile) + ".\\par\\smallskip")
    # Bilder: Spannung + 3D
    bilder = []
    if (BILD / f"spannung_{name}.png").exists():
        bilder.append((f"spannung_{name}.png", tr(en, "Vergleichsspannung im Stahl (Draufsicht, 0–800 MPa)", "von Mises stress in the steel (top view, 0–800 MPa)")))
    if (BILD / f"modell3d_{name}_schnitt{'_en' if en else ''}.png").exists():
        bilder.append((f"modell3d_{name}_schnitt{'_en' if en else ''}.png", tr(en, "PicoGK-Modell, Treppenschnitt", "PicoGK model, stepped cut")))
    if bilder:
        z.append("\\begin{figure}[H]\\centering")
        for b, cap in bilder:
            z.append(f"\\begin{{minipage}}[t]{{0.49\\linewidth}}\\centering\\includegraphics[width=\\linewidth]{{bilder/{b}}}\\\\\\footnotesize {cap}\\end{{minipage}}\\hfill")
        z.append(f"\\caption{{{titel}}}\\end{{figure}}")
    return "\n".join(z)


# ---------------------------------------------------------------- Bilder
def spannungsbild(quelle, name):
    import pyvista as pv
    pv.OFF_SCREEN = True
    st, nr = quelle.split("/")
    g = pv.read(KOP / st / "punkte" / nr / "struktur.vtu")
    s = g.extract_surface(algorithm="dataset_surface")
    pl = pv.Plotter(window_size=(1000, 950)); pl.set_background("white")
    pl.add_mesh(s, scalars="vonmises_MPa", clim=[0, 800], cmap="turbo", show_scalar_bar=True,
                scalar_bar_args={"title": "MPa", "vertical": True, "position_x": 0.86, "position_y": 0.2, "height": 0.6,
                                 "color": "black", "title_font_size": 16, "label_font_size": 14})
    pl.view_xy(); pl.reset_camera(); pl.camera.zoom(1.3)
    pl.add_text(NAME, position="lower_right", font_size=8, color="#52514e")
    pl.screenshot(str(BILD / f"spannung_{name}.png")); pl.close()


def montage(en):
    """Alle 3D-Modelle (Gesamtansicht) in einem Raster."""
    from PIL import Image, ImageDraw, ImageFont
    alle = [p.parent.name for p in sorted((KOP / "modell3d").glob(f"*/gesamt{'_en' if en else ''}.png"))]
    vorne = [n for n, _ in STECKBRIEFE if n in alle and not n.endswith("_test")]
    namen = vorne + [n for n in alle if n not in vorne and not n.endswith("_test")] + [n for n in ("E_test", "A_test") if n in alle]
    if not namen:
        return
    w, h = 800, 560; sp = 3; zl = (len(namen) + sp - 1) // sp     # Modell liegt im Bild bei x 300-1280, y 270-890
    M = Image.new("RGB", (w * sp, h * zl), "white"); d = ImageDraw.Draw(M)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except OSError:
        font = None
    for i, n in enumerate(namen):
        im = Image.open(KOP / "modell3d" / n / f"gesamt{'_en' if en else ''}.png").convert("RGB")
        im = im.crop((300, 290, 1280, 890)).resize((w, int(w * 600 / 980)))
        x, y = (i % sp) * w, (i // sp) * h
        M.paste(im, (x, y + 45)); d.text((x + 15, y + 10), n.replace("_test", " (test)"), fill="black", font=font)
    M.save(BILD / f"modell3d_montage{'_en' if en else ''}.png")


KATALOG = Path(os.environ.get("FUSION_KATALOG", ROOT / "sim" / "kopplung" / "katalog3d"))


def katalog(en, erg):
    """Katalog: alle geometrisch darstellbaren Entwuerfe, je Karte Bild (PicoGK, Gesamtansicht) + Kennzahlen, 4 je Seite."""
    from PIL import Image
    from .doe_auswertung import GRENZEN
    Z = erg["zeilen"]; (BILD / "katalog").mkdir(exist_ok=True)
    karten = []
    for nr, r in Z.items():
        if r["durchdringung"] != 0:
            continue
        q = KATALOG / nr / f"gesamt{'_en' if en else ''}.png"
        bild = ""
        if q.exists():
            ziel = BILD / "katalog" / f"{nr}{'_en' if en else ''}.jpg"
            if not ziel.exists():
                Image.open(q).convert("RGB").crop((300, 290, 1280, 890)).resize((640, 392)).save(ziel, quality=82)
            bild = f"\\includegraphics[width=\\linewidth]{{bilder/katalog/{ziel.name}}}"
        pr = KATALOG / nr / "pruefung.json"
        geo = json.loads(pr.read_text()).get("geometrisch_ok") if pr.exists() else None
        status = ("\\textbf{" + tr(en, "zulässig", "admissible") + "}") if r["alle_ok"] else tr(en, "verletzt: ", "violated: ") + \
            ", ".join(GRENZEN[k][5 if en else 4] for k in GRENZEN if r[f"res_{k}"] < 0)
        tab = (f"\\begin{{tabular}}{{@{{}}l@{{\\,}}r@{{\\quad}}l@{{\\,}}r@{{}}}}"
               f"{tr(en, 'Spulen', 'coils')} & {r['spulen']} & $\\sigma_{{99}}$ & {f(r['wert_stahl'])} MPa \\\\"
               f"{tr(en, 'Verb./Paar', 'conn./pair')} & {int(r['verbinder_je_paar'])} & max. & {f(r['stahl_max_MPa'])} MPa \\\\"
               f"$E_V$ & {f(r['E_verbinder_GPa'])} GPa & {tr(en, 'Dehnung', 'strain')} & {f(r['wert_dehn'], 2)} \\% \\\\"
               f"{tr(en, 'Abstand', 'distance')} & {f(r['abstand_sp'], 2)} & $B\\cdot n$ & {f(r['wert_Bn'], 2)} ‰ \\\\"
               f"{tr(en, 'Stahl', 'steel')} & {f(r['masse_kt'])} kt & {tr(en, 'frei', 'clear.')} & {f(r['freiraum_min_m'], 2)} m \\\\"
               f"\\end{{tabular}}")
        geo_t = "" if geo is None else (tr(en, " PicoGK: keine Überschneidung.", " PicoGK: no overlap.") if geo else tr(en, " PicoGK: Überschneidung!", " PicoGK: overlap!"))
        karten.append(f"\\begin{{minipage}}[t]{{0.47\\linewidth}}\\textbf{{{nr}}}{'$^\\ast$' if r.get('quelle') == 'netz_normal' else ''}"
                      f" \\hfill {f(100*r['robust'])}\\,\\%\\par {bild}\\par\\scriptsize {tab}\\par {status}.{geo_t}\\end{{minipage}}")
    z = []
    for i, k in enumerate(karten):
        z.append(k + ("\\hfill" if i % 2 == 0 else "\\par\\vspace{6pt}"))
        if i % 4 == 3:
            z.append("\\clearpage")
    return "\n".join(z), len(karten)


def main():
    from .doe_auswertung import tabelle
    GEN.mkdir(parents=True, exist_ok=True); BILD.mkdir(parents=True, exist_ok=True)
    erg = json.loads((DATEN / "doe1_auswertung.json").read_text())
    K = json.loads((DATEN / "doe1_kategorien.json").read_text()) if (DATEN / "doe1_kategorien.json").exists() else {}
    # Bilder kopieren / erzeugen
    for b in ("doe1_uebersicht", "doe1_reserven", "doe1_ersatz", "doe1_kategorien", "doe1_netz", "doe1_schwaechen",
              "festigkeit_tragwerk", "stahl_kennwerte", "modell3d_ablauf"):
        for s in ("", "_en"):
            q = ROOT / "docs" / "bilder" / f"{b}{s}.png"
            if q.exists():
                shutil.copy(q, BILD / q.name)
    for name, quelle in STECKBRIEFE:
        st, nr = quelle.split("/")
        if (KOP / st / "punkte" / nr / "struktur.vtu").exists() and not (BILD / f"spannung_{name}.png").exists():
            spannungsbild(quelle, name)
        for art in ("gesamt", "schnitt"):
            for s in ("", "_en"):
                q = KOP / "modell3d" / name / f"{art}{s}.png"
                if q.exists():
                    shutil.copy(q, BILD / f"modell3d_{name}_{art}{s}.png")
    for en in (False, True):
        montage(en)
        s = "_en" if en else "_de"
        teile = {"grenzen": tab_grenzen(en), "tragwerk": tab_tragwerk(en), "rang": tab_rang(en, erg),
                 "netz": tab_netz(en, erg), "ersatz": tab_ersatz(en) if (DATEN / "doe1_ersatz.json").exists() else "",
                 "kategorien": tab_kategorien(en) if K else "", "modell3d": tab_modell3d(en), "alle": tab_alle(en, erg),
                 "schwaechen": tab_studie(en, "schwaechen", ("E Verbinder", "E connectors")),
                 "ersatz1": tab_ersatz1(en),
                 "katalog": katalog(en, erg)[0],
                 "steckbriefe": "".join("\n\\clearpage\n" + x for x in (steckbrief(en, n, q, erg, K) for n, q in STECKBRIEFE) if x)}
        for k, v in teile.items():
            (GEN / f"{k}{s}.tex").write_text(v + "\n")
    print("geschrieben:", sorted(p.name for p in GEN.iterdir()))


if __name__ == "__main__":
    main()
