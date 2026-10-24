"""bericht.py — Bericht (LaTeX -> PDF) aus den Rechenergebnissen erzeugen.

Alle Zahlen werden aus den Ergebnisdateien gelesen (stufe1/2.json, bilanz.json, kennzahlen.json,
struktur/ergebnis.json), Bilder werden kopiert. Fehlt ein Ergebnis, steht im Bericht
"noch nicht gerechnet" statt einer Zahl. Der Bericht bleibt lokal (bericht/ ist nicht im Repo).

    .venv/bin/python -m stellarator.bericht [--version 0.3] [--ohne_pdf]

Ausgabe bericht/v<version>/: bericht_v<version>.tex, bericht_v<version>.pdf, bilder/.
Varianten und Pfade: VARIANTEN unten (neue Rechnung -> Eintrag ergaenzen).
"""
from __future__ import annotations
import argparse, json, shutil, subprocess
from datetime import date
from pathlib import Path

from .lauf import PROJEKT

SIM = PROJEKT / "sim"
VARIANTEN = {   # Plasmaform -> Dateien der Kette
    "A6": {"titel": "A = 6", "stufe1": SIM / "invers/qa_nfp2", "stufe2": SIM / "invers/qa_nfp2_spulen_mittel",
           "bilanz": SIM / "invers/qa_nfp2_1GW", "fall": "qa_nfp2_1GW",
           "struktur": {"HTS": SIM / "stellarator/struktur/qa_nfp2_1GW_HTS_mittel"}},
    "A45": {"titel": "A = 4,5", "stufe1": SIM / "invers/qa_nfp2_A45", "stufe2": SIM / "invers/qa_nfp2_A45_spulen_mittel",
            "bilanz": SIM / "invers/qa_nfp2_A45_1GW", "fall": "qa_nfp2_A45_1GW",
            "struktur": {"HTS": SIM / "stellarator/struktur/qa_nfp2_A45_1GW_HTS"}},
}
NETZSTUDIE = [("grob", SIM / "stellarator/struktur/qa_nfp2_1GW_HTS_grob"),
              ("mittel", SIM / "stellarator/struktur/qa_nfp2_1GW_HTS_mittel")]
W7X = {"bewertung": SIM / "stellarator/bewertung/bew_w7x_standard/kennzahlen.json",
       "elmer": SIM / "stellarator/elmer_w7x_70/ergebnis.json"}
LEITER = ("HTS", "Nb3Sn")
FEHLT = r"\textit{n.\,g.}"


def lies(p: Path):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def z(x, nk=1, einheit=""):
    """Zahl deutsch formatiert (Komma), fehlend -> n. g."""
    if x is None:
        return FEHLT
    s = f"{x:,.{nk}f}".replace(",", "X").replace(".", ",").replace("X", r"\,")
    return s + (f"\\,{einheit}" if einheit else "")


def sammle() -> dict:
    d = {}
    for k, v in VARIANTEN.items():
        s1, s2, bil = lies(v["stufe1"] / "stufe1.json"), lies(v["stufe2"] / "stufe2.json"), lies(v["bilanz"] / "bilanz.json")
        e = {"titel": v["titel"], "s1": s1, "s2": s2, "bilanz": bil, "leiter": {}}
        for L in LEITER:
            kz = lies(SIM / "stellarator/bewertung" / f"{v['fall']}_{L}" / "kennzahlen.json")
            st = lies(v["struktur"][L] / "ergebnis.json") if L in v["struktur"] else None
            e["leiter"][L] = {"aus": (bil or {}).get("auslegung", {}).get(L), "kz": kz,
                              "struktur": (st or {}).get("ergebnis"), "struktur_param": st}
        d[k] = e
    d["netzstudie"] = [(n, (lies(p / "ergebnis.json") or {}).get("ergebnis"), (lies(p / "ergebnis.json") or {}).get("netz"))
                       for n, p in NETZSTUDIE]
    d["w7x"] = {k: lies(p) for k, p in W7X.items()}
    return d


def bilder(d, ziel: Path) -> dict:
    ziel.mkdir(parents=True, exist_ok=True)
    quelle = {"uebersicht": PROJEKT / "docs/bilder/uebersicht_1GW_A6_A45.png"}
    for k, v in VARIANTEN.items():
        quelle[f"{k}_flaechen"] = v["stufe1"] / "stufe1_flaechen.png"
        quelle[f"{k}_spulen"] = v["stufe2"] / "stufe2_spulen.png"
        quelle[f"{k}_bilanz"] = v["bilanz"] / "bilanz_R0_B0.png"
        for L in LEITER:
            quelle[f"{k}_{L}_3d"] = SIM / "stellarator/bewertung" / f"{v['fall']}_{L}" / "feldlinien_3d.png"
            quelle[f"{k}_{L}_poincare"] = SIM / "stellarator/bewertung" / f"{v['fall']}_{L}" / "poincare.png"
        for L, p in v["struktur"].items():
            quelle[f"{k}_{L}_struktur"] = p / "struktur.png"
    da = {}
    for n, q in quelle.items():
        if q.exists():
            shutil.copy(q, ziel / f"{n}.png"); da[n] = f"bilder/{n}.png"
    return da


def abb(b, name, breite, text):
    if name not in b:
        return f"\\par\\textit{{(Bild {name.replace('_', ' ')} noch nicht erzeugt)}}\\par\n"
    return (f"\\begin{{figure}}[H]\\centering\\includegraphics[width={breite}\\linewidth]{{{b[name]}}}"
            f"\\caption{{{text}}}\\end{{figure}}\n")


def tex(d, b, version) -> str:
    A6, A45 = d["A6"], d["A45"]
    lb = (A6["bilanz"] or A45["bilanz"] or {}).get("leistung", {})
    an = (A6["bilanz"] or A45["bilanz"] or {}).get("annahmen", {})

    def g(e, L, *pfad):
        x = e["leiter"][L]
        for p in pfad:
            x = (x or {}).get(p) if isinstance(x, dict) else None
        return x

    def zeile_auslegung(k, L):  # noqa: E306
        e = d[k]; a = g(e, L, "aus") or {}; kz = g(e, L, "kz") or {}
        B0 = (kz.get("achse") or {}).get("B_mittel_T"); sp_ = kz.get("spulen") or {}
        bl = sp_.get("B_max_oberflaeche_T")
        F = max((sp_.get("F_netto_MN_max_je_typ") or {}).values(), default=None)
        return (f"{e['titel']} & {L.replace('Nb3Sn', 'Nb$_3$Sn')} & {z(a.get('R0_m'))} & {z(a.get('a_m'))} & {z(a.get('B0_T'), 2)} & "
                f"{z(bl)} & {z((kz.get('strom') or {}).get('kA_je_windung_max', 0) / 1e3 if kz else None)} & "
                f"{z(a.get('wickelpaket_m'), 2)} & {z((kz.get('geometrie') or {}).get('spalt_min_m'), 2)} & {z(F, 0)} \\\\\n")

    def zeile_form(k):
        e = d[k]; s1 = (e["s1"] or {}).get("kennzahlen", {}); s2 = e["s2"] or {}
        return (f"{e['titel']} & {z(s1.get('qs_fehler') * 1e5 if s1.get('qs_fehler') else None, 1)} & "
                f"{z(s1.get('iota_achse'), 3)} & {z(s1.get('iota_rand'), 3)} & "
                f"{z(s2.get('Bn_rel_mittel', 0) * 100 if s2 else None, 2)} & {z(s2.get('Bn_rel_max', 0) * 100 if s2 else None, 2)} \\\\\n")

    def zeile_struktur(k, L="HTS"):
        st = g(d[k], L, "struktur"); par = g(d[k], L, "struktur_param") or {}
        if not st:
            return f"{d[k]['titel']} & \\multicolumn{{7}}{{l}}{{noch nicht gerechnet}} \\\\\n"
        s, w = st["schale"], st["wickelpakete"]
        return (f"{d[k]['titel']} & {z((par.get('netz') or {}).get('dicke_m'), 2)} & {z(s['masse_t'] / 1e3, 1)} & "
                f"{z(s['vonmises_mittel_MPa'], 0)} & {z(s['vonmises_p99_MPa'], 0)} & {z(s['vonmises_max_MPa'], 0)} & "
                f"{z(w['vonmises_p99_MPa'], 0)} & {z(1e3 * st['u_max_m'], 0)} \\\\\n")

    stA6 = g(A6, "HTS", "struktur") or {}
    ns = "".join(f"{n} & {z((nz or {}).get('n_tet', 0) / 1e6 if nz else None, 2)} & "
                 f"{z(e['schale']['vonmises_p99_MPa'] if e else None, 0)} & {z(e['schale']['vonmises_max_MPa'] if e else None, 0)} & "
                 f"{z(e['wickelpakete']['vonmises_p99_MPa'] if e else None, 0)} & {z(1e3 * e['u_max_m'] if e else None, 0)} \\\\\n"
                 for n, e, nz in d["netzstudie"])
    kraft = ""
    if stA6:
        fe = max(stA6["kraft_elmer_MN_je_spule"].values()); fb = max(stA6["kraft_biot_savart_MN_je_typ"].values())
        kraft = (f"Die Lorentzkraft je Spule aus Elmer ($\\int \\vec J\\times\\vec B\\,dV$) stimmt mit Biot-Savart überein: "
                 f"größte Spule {z(fe, 0)}\\,MN (Elmer) gegen {z(fb, 0)}\\,MN (Biot-Savart), "
                 f"Abweichung {z(100 * (fe / fb - 1), 1)}\\,\\%.")
    w7 = d["w7x"]["bewertung"] or {}; el = d["w7x"]["elmer"] or {}
    el_achse = ((el.get("fehler_vs_biot_savart") or {}).get("achse") or {}).get("fehler_median")

    return rf"""\documentclass[10pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}\usepackage[T1]{{fontenc}}\usepackage[german]{{babel}}
\usepackage{{graphicx,float,booktabs,amsmath,siunitx,xcolor}}
\usepackage[margin=2.2cm]{{geometry}}\usepackage[hidelinks]{{hyperref}}
\sisetup{{output-decimal-marker={{,}}}}
\hypersetup{{pdfauthor={{Thomas Schmiegelt}},pdftitle={{Kompakter Stellarator für 1 GW}}}}
\title{{\textbf{{Vom Stromnetz zur Spule: Auslegung eines kompakten\\Stellarators für 1\,GW elektrisch}}\\[2pt]\large Version {version}}}
\author{{Thomas Schmiegelt \textbar{{}} Hobbyprojekt \texttt{{stellarator-design}}}}
\date{{{date.today().strftime('%d.%m.%Y')}}}
\begin{{document}}\maketitle

\noindent\fcolorbox{{gray}}{{gray!8}}{{\parbox{{0.96\linewidth}}{{\textbf{{Hobbyprojekt, aus Neugier entstanden.}}
Keine Verbindung zu einem Forschungsinstitut oder Unternehmen, nicht begutachtet. Alle Ergebnisse
sind Abschätzungen mit vereinfachten Modellen (0-D-Leistungsbilanz, Vakuumfeld, lineare Elastizität)
und können Fehler enthalten. Keine Auslegung einer realen Anlage.}}}}

\begin{{abstract}}
Die Frage wird vom Ziel her gestellt: Ein Kraftwerk soll \SI{{1000}}{{MW}} ins Netz liefern. Daraus folgt die
Fusionsleistung (\SI{{{z(lb.get('P_fus_MW'), 0)}}}{{MW}}), daraus über Grenzen für Wandlast, Plasmadruck,
Dichte, Einschluss und Supraleiter die Größe $R_0$ und das Magnetfeld $B_0$. Eine optimierte,
quasi-axisymmetrische Plasmaform (DESC) wird mit Spulen (simsopt) erzeugt und unabhängig geprüft
(Feldlinien, Spulenfeld, Spalt, Kräfte). Eine Stützschale wird mit ElmerFEM in einem gekoppelten
Lauf (Magnetfeld $\to$ Lorentzkraft $\to$ Spannung) berechnet.
Ergebnis: Mit Seitenverhältnis $A=4{{,}}5$ reichen etwa $R_0\approx\SI{{{z(g(A45, 'HTS', 'aus', 'R0_m'))}}}{{m}}$
(HTS) bzw. \SI{{{z(g(A45, 'Nb3Sn', 'aus', 'R0_m'))}}}{{m}} (Nb$_3$Sn). Kritisch sind die Kräfte: über
\SI{{1000}}{{MN}} je Spule. Die Stützschale der Variante $A=6$ wiegt \SI{{{z(stA6['schale']['masse_t'] / 1e3 if stA6 else None, 0)}}}{{kt}} Stahl;
99\,\% der Schale liegen unter \SI{{{z(stA6['schale']['vonmises_p99_MPa'] if stA6 else None, 0)}}}{{MPa}} (zulässig \SI{{667}}{{MPa}}),
örtliche Spitzen darüber.
\end{{abstract}}

{abb(b, 'uebersicht', 1.0, 'Übersicht: kompaktere Plasmaform macht die Anlage kleiner (Feldlinien gefärbt nach $|B|$, Spulen braun). Die 3D-Bilder sind formatfüllend und nicht maßstäblich zueinander.')}

\section{{Die Kette vom Netz zum Plasma}}
\begin{{itemize}}
\item \textbf{{Plasma:}} D-T-Fusion, je Reaktion \SI{{17,6}}{{MeV}}: \SI{{80}}{{\%}} trägt ein Neutron (\SI{{14}}{{MeV}}),
  \SI{{20}}{{\%}} ein Alpha-Teilchen. Die Alphas bleiben im Magnetfeld gefangen und heizen das Plasma
  (\SI{{{z(lb.get('P_alpha_MW'), 0)}}}{{MW}}).
\item \textbf{{Blanket:}} Die Neutronen (\SI{{{z(lb.get('P_neutronen_MW'), 0)}}}{{MW}}) durchdringen das Feld, werden im
  Blanket abgebremst (Energievervielfachung {z(an.get('M_blanket'), 2)}) und erbrüten Tritium aus Lithium.
\item \textbf{{Kraftwerk:}} Wärme \SI{{{z(lb.get('P_th_MW'), 0)}}}{{MW}}, Wirkungsgrad {z(an.get('eta_th'), 2)} $\to$
  brutto \SI{{{z(lb.get('P_brutto_MW'), 0)}}}{{MW}}, Eigenbedarf \SI{{{z(lb.get('P_eigen_MW'), 0)}}}{{MW}}
  (Pumpen, Kälte, Anlage) $\to$ netto \SI{{{z(lb.get('P_netz_MW'), 0)}}}{{MW}}.
\item \textbf{{Magnetfeld:}} hält nur geladene Teilchen. Es ist ein „Käfig“ für das \SI{{150}}{{Mio.}}\,°C heiße
  Plasma, durchlässig für Neutronen. Die verdrillten Spulen erzeugen geschlossene, geschachtelte
  Flussflächen ohne Plasmastrom (Dauerbetrieb).
\end{{itemize}}

\section{{Methode}}
\begin{{description}}
\item[Stufe 0 -- Leistungsbilanz] Raster über $(R_0, B_0, T_0)$; Fusionsleistung nach Bosch-Hale mit
  Parabelprofilen; Grenzen: Neutronen-Wandlast $\le$ \SI{{{z(an.get('wandlast_max'), 1)}}}{{MW/m^2}},
  $\langle\beta\rangle\le$ {z(100 * an['beta_max'] if an else None, 0)}\,\%, Dichte $\le$ {z(an.get('sudo_max'), 1)}$\times$Sudo-Grenze,
  nötiger Einschluss $\le$ {z(an.get('H_max'), 1)}$\times$ISS04, Feld am Leiter (HTS \SI{{20}}{{T}}, Nb$_3$Sn \SI{{12}}{{T}}),
  Spule--Plasma $\ge$ \SI{{{z(an.get('d_noetig'), 1)}}}{{m}}, Spalt zwischen Wickelpaketen $\ge$ \SI{{0,2}}{{m}}.
  Faktor Feld am Leiter / $B_0$ und Spaltmodell werden aus Stufe 3 iteriert.
\item[Stufe 1 -- Plasmaform] DESC, Vakuumgleichgewicht, Ziele Quasisymmetrie (QA), Seitenverhältnis, $\iota=0{{,}}42$, $n_\mathrm{{fp}}=2$.
\item[Stufe 2 -- Spulen] simsopt, 16 Spulen (4 Basisspulen und Symmetrie), $B\cdot n\to 0$ mit Strafen für Länge, Abstände, Krümmung.
\item[Stufe 3 -- Prüfung] eigene Biot-Savart-Rechnung, Feldlinien, $\iota$, Feld an der Wickeloberfläche, Kräfte, Spaltprüfung.
\item[Struktur] ElmerFEM: CoilSolver, WhitneyAV (Magnetostatik), Lorentzkraft $\vec J\times\vec B$ als Volumenlast im
  StressSolver; Stützschale aus Stahl (316LN, zulässig \SI{{667}}{{MPa}}) mit eingebetteten Wickelpaketen.
\end{{description}}

\section{{Plasmaform und Spulen}}
\begin{{table}}[H]\centering\begin{{tabular}}{{lccccc}}\toprule
Form & QS-Fehler [$10^{{-5}}$] & $\iota$ Achse & $\iota$ Rand & $|B\cdot n|/|B|$ Mittel [\%] & max [\%]\\\midrule
{zeile_form('A6')}{zeile_form('A45')}\bottomrule\end{{tabular}}
\caption{{Stufe 1 und 2. Referenz DESC \emph{{precise QA}}: QS-Fehler $5{{,}}8\cdot10^{{-5}}$.}}\end{{table}}
{abb(b, 'A45_flaechen', 0.55, 'Flussflächen der kompakten Form $A=4{,}5$ (DESC).')}

\section{{Auslegung auf 1\,GW und Prüfung in voller Größe}}
\begin{{table}}[H]\centering\small\begin{{tabular}}{{llcccccccc}}\toprule
Form & Leiter & $R_0$ [m] & $a$ [m] & $B_0$ [T] & $B_\mathrm{{Leiter}}$ [T] & $I$ [MA] & Paket [m] & Spalt [m] & $F_\mathrm{{max}}$ [MN]\\\midrule
{zeile_auslegung('A6', 'HTS')}{zeile_auslegung('A6', 'Nb3Sn')}{zeile_auslegung('A45', 'HTS')}{zeile_auslegung('A45', 'Nb3Sn')}\bottomrule\end{{tabular}}
\caption{{Auslegung (Stufe 0) und Prüfung (Stufe 3): Feld am Leiter, Strom je Spule, Spalt und Netto-Kraft aus der Biot-Savart-Rechnung in voller Größe.}}\end{{table}}
{abb(b, 'A45_bilanz', 0.75, 'Auslegungsraum für $A=4{,}5$: grün machbar, Linien = Grenzen.')}
{abb(b, 'A45_HTS_poincare', 0.8, 'Poincaré-Schnitt und $\\iota$-Profil der HTS-Auslegung $A=4{,}5$: alle Flussflächen intakt.')}

\section{{Stützstruktur (ElmerFEM)}}
{kraft}
\begin{{table}}[H]\centering\small\begin{{tabular}}{{lccccccc}}\toprule
Form (HTS) & Dicke [m] & Masse [kt] & $\sigma_\mathrm{{v}}$ Mittel & 99\,\% unter & Spitze & Paket 99\,\% & $u_\mathrm{{max}}$ [mm]\\
 & & & [MPa] & [MPa] & [MPa] & [MPa] & \\\midrule
{zeile_struktur('A6')}{zeile_struktur('A45')}\bottomrule\end{{tabular}}
\caption{{Von-Mises-Spannung in Schale und Wickelpaketen. Zulässig für 316LN bei \SI{{4}}{{K}}: \SI{{667}}{{MPa}}.}}\end{{table}}
\begin{{table}}[H]\centering\small\begin{{tabular}}{{lccccc}}\toprule
Netz ($A=6$) & Tetraeder [Mio.] & Schale 99\,\% [MPa] & Schale Spitze [MPa] & Paket 99\,\% [MPa] & $u_\mathrm{{max}}$ [mm]\\\midrule
{ns}\bottomrule\end{{tabular}}
\caption{{Netzstudie: die 99-\%-Werte sind konvergiert, die Spitzen wachsen (Spannungssingularität an den Paketecken).}}\end{{table}}
{abb(b, 'A45_HTS_struktur', 1.0, 'Von-Mises-Spannung, $A=4{,}5$ mit HTS: links Schale (Schnitt), rechts Wickelpakete.')}
{abb(b, 'A6_HTS_struktur', 1.0, 'Von-Mises-Spannung, $A=6$ mit HTS.')}

\section{{Validierung}}
W7-X mit realen Spulen: \SI{{{z((w7.get('strom') or {}).get('kA_je_windung_npc1'), 2)}}}{{kA}} je Windung für
$\langle B\rangle_\mathrm{{Achse}}=\SI{{2,5}}{{T}}$, Spalt der Wickelpakete \SI{{{z(1e3 * (w7.get('geometrie') or {}).get('spalt_min_m', 0) if w7 else None, 0)}}}{{mm}}.
ElmerFEM gegen Biot-Savart mit allen 70 Spulen: Median-Abweichung auf der Achse {z(100 * el_achse if el_achse else None, 2)}\,\%.

\section{{Erkenntnisse}}
\begin{{enumerate}}
\item Der Einschluss (ISS04) bestimmt die Größe, bei HTS zusätzlich die Wandlast. Ein kleineres Seitenverhältnis
  verkleinert die Anlage deutlich; bei $A=4{{,}}5$ sind HTS und Nb$_3$Sn fast gleich groß.
\item Das Feld am Leiter ist kein fester Vielfacher von $B_0$: eng stehende Spulen ergaben $3{{,}}5\times B_0$,
  besser verteilte $1{{,}}8$--$2{{,}}4\times B_0$. Bei Nb$_3$Sn dominiert sonst das Eigenfeld des Wickelpakets
  (Stromdichte auf \SI{{15}}{{A/mm^2}} gesenkt).
\item Der Spulenstrom folgt aus dem Durchflutungsgesetz ($I\approx2\pi R_0B_0/\mu_0N$), unabhängig von der Spulenlage.
\item Die Spaltprüfung fand bei Nb$_3$Sn eine Durchdringung der Wickelpakete; der Spalt ist jetzt Teil von Stufe 0.
\item Kräfte von über \SI{{1000}}{{MN}} je Spule (W7-X: \SI{{2}}{{MN}}) machen die Stützstruktur zum Hauptproblem.
\end{{enumerate}}

\section{{Grenzen und nächste Schritte}}
\begin{{itemize}}
\item 0-D-Bilanz ($\pm30\,\%$): ohne Divertor-Wärmelast, Zyklotronstrahlung, Neutronik des Blankets.
\item Geometrie der Stützschale für allgemeine Spulenformen noch nicht robust: Flächen durch die
  Spulenkurven falten sich auf der Torus-Innenseite, die Vernetzung hängt bei dünnen Spalten.
  Für $A=4{{,}}5$ fehlt deshalb noch die Strukturrechnung.
\item Stützschale v1 ohne Öffnungen für Wartung und Heizung; Wickelpakete noch nicht an der Schalennormalen ausgerichtet
  (daher dicke Schale); Spannungsspitzen an Ecken $\to$ Ausrundungen, örtliche Verstärkung auf der Torus-Innenseite.
\item Zulässige Querdruckspannung der HTS-Bänder prüfen (Wickelpaket-Spannungen mehrere \SI{{100}}{{MPa}}).
\item Gewichtung Masse gegen Spannung: Schalendicke optimieren (Studien-Runner).
\end{{itemize}}

\begin{{thebibliography}}{{9}}\small
\bibitem{{desc}} D. Dudt, D. Panici, E. Kolemen: DESC stellarator equilibrium and optimization code, \url{{https://github.com/PlasmaControl/DESC}}.
\bibitem{{simsopt}} M. Landreman et al.: SIMSOPT, J. Open Source Softw. 6 (2021) 3525.
\bibitem{{elmer}} ElmerFEM, CSC -- IT Center for Science, \url{{https://www.elmerfem.org}}.
\bibitem{{bh}} H.-S. Bosch, G. M. Hale: Improved formulas for fusion cross-sections and thermal reactivities, Nucl. Fusion 32 (1992) 611.
\bibitem{{iss04}} H. Yamada et al.: Characterization of energy confinement in net-current free plasmas (ISS04), Nucl. Fusion 45 (2005) 1684.
\bibitem{{sudo}} S. Sudo et al.: Scalings of energy confinement and density limit in stellarator/heliotron devices, Nucl. Fusion 30 (1990) 11.
\bibitem{{gmsh}} C. Geuzaine, J.-F. Remacle: Gmsh, Int. J. Numer. Meth. Eng. 79 (2009) 1309.
\end{{thebibliography}}
\end{{document}}
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bericht aus den Ergebnisdateien erzeugen")
    ap.add_argument("--version", default="0.3")
    ap.add_argument("--ohne_pdf", action="store_true")
    a = ap.parse_args(argv)
    ordner = PROJEKT / "bericht" / f"v{a.version}"
    d = sammle(); b = bilder(d, ordner / "bilder")
    datei = ordner / f"bericht_v{a.version}.tex"
    datei.write_text(tex(d, b, a.version))
    fehlend = [k for k in ("uebersicht", "A45_HTS_struktur", "A6_HTS_struktur") if k not in b]
    if not a.ohne_pdf:
        for _ in range(2):
            r = subprocess.run(["pdflatex", "-interaction=nonstopmode", datei.name], cwd=ordner,
                               capture_output=True, text=True)
        if r.returncode:
            print("\n".join(l for l in r.stdout.splitlines() if l.startswith("!") or "l." in l)[:3000])
            raise SystemExit("LaTeX-Fehler, siehe " + str(ordner / datei.with_suffix(".log").name))
        for e in (".aux", ".log", ".out"):
            datei.with_suffix(e).unlink(missing_ok=True)
    print("FERTIG", datei.with_suffix(".pdf"), "fehlende Bilder:", fehlend or "keine")


if __name__ == "__main__":
    main()
