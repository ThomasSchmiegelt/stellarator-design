"""K6: ERGEBNIS.md, Bilder, Baustein.  KI-generiert (Claude Sonnet 5.5, 2026-11-13)."""
from pathlib import Path
import numpy as np


def schreibe(OUT, test, e, qn, qe, th, ph, X, baust):
    OUT = Path(OUT); (OUT / "bilder").mkdir(exist_ok=True); baust = Path(baust); baust.mkdir(parents=True, exist_ok=True)
    bilder(OUT, qn, qe, e); vtk(baust / "wand_last.vtk", X, qn, qe)
    b, n, ew, fl = e["bilanz"], e["neutronen"], e["erste_wand_waerme"], e["flaeche_m2"]
    z = ["| Dok.-Nr. | FUS-ERG-K6 | Version | 0.1 | Status | Entwurf |", "|---|---|---|---|---|---|",
         "| Titel | Ergebnis K6 · Wärmebilanz und Wandlast (DGozX5fj) | Ersteller | Claude Sonnet 5.5 (KI) | Prüfer | – (Opus/Mensch offen) |", "",
         "> **KI-generiert (Claude Sonnet 5.5, 2026-11-13).** Erwartung `sim/kandidat/erwartung/K6.md` (unverändert), Eingabe `sim/kandidat/kandidat.json`, Alpha-Treffer aus K3. Entwurf, keine Deutung. Zahlen aus `auswertung.json`."
         + (" **RAUCHTEST (grobe Gitter, K3-Testdaten).**" if test else ""), f"> Form: Datensatzform ConStellaration DGozX5fj unverändert. Rechnung {e['start']} bis {e['ende']} (date).", "",
         "## 1 Wärmebilanz (`stellarator/waermebilanz.py`, Vorgaben des Werkzeugs: η 0,35, M 1,15, f_p 0,04, P_eigen 60 MW, Divertorwärme genutzt)",
         "| Größe | Wert (MW) | Erwartung |", "|---|---|---|",
         f"| P_fus | {b['P_fus_MW']:.0f} | kandidat.json {e['P_fus_Stufe0_kandidat_MW']} |", f"| P_th | {b['P_th_MW']:.0f} | ≈ 3400 |",
         f"| P_Neutronen / P_Alpha | {b['P_neutronen_MW']:.0f} / {b['P_alpha_MW']:.0f} | 2442 (Überschlag) |",
         f"| P_brutto / Eigenbedarf+Pumpen | {b['P_brutto_MW']:.0f} / {b['P_eigen_MW']:.0f} | |", f"| netto ins Netz (aus Komponenten) | {e['netto_aus_komponenten_MW']:.0f} | 1000 (± 2 %) |",
         f"| Schließung Σ(Blanket, Erste Wand, Divertor) gegen P_th | {e['bilanz_schliessung_prozent']:+.2f} % | ± 2 % |", "",
         "## 2 Wandlast", "| Größe | Wert | Erwartung |", "|---|---|---|",
         f"| Fläche (wout s = 1, Quadratur) | {fl['wout_s1_quadratur']:.0f} m² | Überschlag {fl['ueberschlag_7_9_R0_2']:.0f} m²; Stufe 0 (S_R2·R0²) {fl['stufe0_S_R2']:.0f} m² |",
         f"| Neutronen mittel | {n['mittel_MW_m2']:.3f} MW/m² | 0,2–0,35 |", f"| Neutronen Spitze (max / p99) | {n['spitze_MW_m2']:.3f} / {n['p99_MW_m2']:.3f} MW/m² | 0,4–0,8 (Grenze {n['grenze_MW_m2']} MW/m², {n['grenze_art']}) |",
         f"| Strahlung (Bremsstrahlung, gleichmäßig) | {ew['q_strahlung_MW_m2']:.3f} MW/m² ({ew['P_brems_MW']:.0f} MW) | |",
         f"| Alpha-Verlust K3 (Mittel beider Startflächen) / Leistung auf Wand | {100 * ew['verlustanteil_alpha_K3']:.1f} % / {ew['P_alpha_wand_MW']:.1f} MW | Quelle `{ew['K3_quelle']}` |",
         f"| Wärmestrom Erste Wand (Strahlung + Alpha) Spitze / Mittel | {ew['q_gesamt_spitze_MW_m2']:.3f} / {ew['q_gesamt_mittel_MW_m2']:.3f} MW/m² | 0,1–0,5 (Spitze, ohne Divertor) |", "",
         f"Verfahren: {n['gitter']}; Sichtfaktorsumme {n['sichtfaktor_summe']:.3f} (Anteil der Quelle, der ohne Abschattung die Wand trifft; danach auf P_Neutronen normiert). Wand = Plasmarand s = 1 (Annahme). Divertor nicht Teil von K6 (Liste K9).", "",
         "Bilder: `bilder/k6_wandlast_de.png` / `_en.png` (Zielband und Grenze beschriftet). Szenenbaustein `video/bausteine/K6/wand_last.vtk` (Skalare q_neutron, q_erstewand).", "", "---", "*KI-generiert (Claude Sonnet 5.5), Entwurf, nicht geprüft.*"]
    baustein_md(baust, "K6 Wandlast",
                f"Bei {b['P_neutronen_MW']:.0f} MW Neutronenleistung auf {fl['wout_s1_quadratur']:.0f} m² Wand liegt die mittlere Neutronenlast bei {n['mittel_MW_m2']:.2f} MW/m², die Spitze bei {n['spitze_MW_m2']:.2f} MW/m² (Grenze 2 MW/m², Annahme); netto {e['netto_aus_komponenten_MW']:.0f} MW ins Netz.",
                f"With {b['P_neutronen_MW']:.0f} MW of neutron power on {fl['wout_s1_quadratur']:.0f} m² of wall, the mean neutron load is {n['mittel_MW_m2']:.2f} MW/m² and the peak {n['spitze_MW_m2']:.2f} MW/m² (limit 2 MW/m², assumption); net {e['netto_aus_komponenten_MW']:.0f} MW to the grid.",
                "sim/kandidat/K6/ERGEBNIS.md, auswertung.json; Geometrie wand_last.vtk", test)
    (Path(OUT) / "ERGEBNIS_test.md" if test else Path(OUT).parent / "ERGEBNIS.md").write_text("\n".join(z) + "\n", encoding="utf-8")


def bilder(OUT, qn, qe, e):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    T = {"de": ("Neutronen-Wandlast", "Wärmestrom Erste Wand (Strahlung + Alpha)", "θ-Index", "φ-Index", "MW/m²", "Zielband Spitze 0,4–0,8 (Erwartung)", "Grenze 2 MW/m² (Annahme)", "KI-generiert (Claude Sonnet 5.5), Entwurf"),
         "en": ("Neutron wall load", "Heat flux first wall (radiation + alpha)", "θ index", "φ index", "MW/m²", "target band peak 0.4–0.8 (expectation)", "limit 2 MW/m² (assumption)", "AI-generated (Claude Sonnet 5.5), draft")}
    for sp, (t1, t2, xl, yl, u, band, gr, fu) in T.items():
        fig, ax = plt.subplots(1, 3, figsize=(14, 4.2), gridspec_kw={"width_ratios": [1, 1, .7]})
        for a_, f_, t_ in ((ax[0], qn, t1), (ax[1], qe, t2)):
            im = a_.imshow(f_, origin="lower", aspect="auto", cmap="inferno", vmin=0); fig.colorbar(im, ax=a_, label=u); a_.set_title(t_, fontsize=9); a_.set_xlabel(yl); a_.set_ylabel(xl)
        v = [e["neutronen"]["mittel_MW_m2"], e["neutronen"]["spitze_MW_m2"]]; ax[2].bar(["mean" if sp == "en" else "Mittel", "peak" if sp == "en" else "Spitze"], v, color=["#4477aa", "#cc3311"])
        ax[2].axhspan(0.2, 0.35, xmin=0, xmax=.5, color="#ccbb44", alpha=.4); ax[2].axhspan(0.4, 0.8, xmin=.5, xmax=1, color="#ccbb44", alpha=.4, label=band); ax[2].axhline(2, color="r", ls="--", label=gr)
        ax[2].set_ylabel(u); ax[2].legend(fontsize=6); fig.text(.5, .005, fu, ha="center", fontsize=7); fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(OUT / "bilder" / f"k6_wandlast_{sp}.png", dpi=105); plt.close(fig)


def vtk(datei, X, qn, qe):
    nth, nph = qn.shape; pts = X.reshape(-1, 3); polys = []
    for i in range(nth):
        for j in range(nph):
            polys.append((i * nph + j, i * nph + (j + 1) % nph, ((i + 1) % nth) * nph + (j + 1) % nph, ((i + 1) % nth) * nph + j))
    with open(datei, "w") as f:
        f.write("# vtk DataFile Version 3.0\nKI-generiert K6, Wandlast (MW/m2), Anlage m\nASCII\nDATASET POLYDATA\n"); f.write(f"POINTS {len(pts)} float\n"); np.savetxt(f, pts, fmt="%.3f")
        f.write(f"POLYGONS {len(polys)} {5 * len(polys)}\n"); [f.write("4 " + " ".join(map(str, q)) + "\n") for q in polys]
        f.write(f"POINT_DATA {len(pts)}\nSCALARS q_neutron float 1\nLOOKUP_TABLE default\n"); np.savetxt(f, qn.ravel(), fmt="%.5f")
        f.write("SCALARS q_erstewand float 1\nLOOKUP_TABLE default\n"); np.savetxt(f, qe.ravel(), fmt="%.5f")

def baustein_md(ziel, titel, de, en, quelle, test):
    ziel = Path(ziel); ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "baustein.md").write_text(f"# Szenenbaustein {titel}\n\n> KI-generiert (Claude Sonnet 5.5, 2026-11-13)." + (" RAUCHTEST, keine echten Zahlen." if test else "") + f"\n\n**DE:** {de}\n\n**EN:** {en}\n\nQuelle: {quelle}\n\n---\n*KI-generiert, Entwurf.*\n", encoding="utf-8")
