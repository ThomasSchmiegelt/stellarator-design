"""K3: ERGEBNIS.md und Bilder (erst am Ende).  KI-generiert (Claude Sonnet 5.5, 2026-11-13)."""
from pathlib import Path


def schreibe(OUT, test, aus, t0, t1):
    OUT = Path(OUT); (OUT / "bilder").mkdir(exist_ok=True)
    bild(OUT, aus)
    z = ["| Dok.-Nr. | FUS-ERG-K3 | Version | 0.1 | Status | Entwurf |", "|---|---|---|---|---|---|",
         "| Titel | Ergebnis K3 · Alphateilchen im Spulenfeld (DGozX5fj, volle Größe) | Ersteller | Claude Sonnet 5.5 (KI) | Prüfer | – (Opus/Mensch offen) |", "",
         "> **KI-generiert (Claude Sonnet 5.5, 2026-11-13).** Erwartung `sim/kandidat/erwartung/K3.md` (unverändert), Eingabe `sim/kandidat/kandidat.json`. Entwurf, keine Deutung."
         + (" **RAUCHTEST: wenige Teilchen, kurze Zeit – keine echten Zahlen.**" if test else ""),
         f"> Lauf {t0} bis {t1} (date). Alle Zahlen aus `auswertung.json`. Form: Datensatzform DGozX5fj unverändert; Spulen: eigene.", "",
         f"Setup: R0 {aus['R0_m']} m, B0 {aus['B0_T']} T, ρ_L/a = {aus['rho_L_durch_a']:.4f}, n = {aus['n_je_flaeche']} je Fläche, t_max = {aus['tmax_s']} s; Führungszentrum, stoßfrei, Verlust bei s = 1 (Annahme wie `stellarator/alpha_bahnen.py`).", "",
         "## 1 Verlust bis t_max", "| Feld | s_Start | n | verloren | Anteil | 95 %-Intervall (Wilson) | Erwartung |", "|---|---|---|---|---|---|---|"]
    erw = {0.25: "1–8 %", 0.5: "3–15 %"}
    for nm, f in aus["felder"].items():
        for r in f["flaechen"]:
            z.append(f"| {'Spulenfeld' if nm == 'spulen' else 'VMEC-Feld (Boozer)'} | {r['s']} | {r['n']} | {r['verloren']} | {100 * r['anteil']:.1f} % | {100 * r['ci95'][0]:.1f}–{100 * r['ci95'][1]:.1f} % | {erw[r['s']] if nm == 'spulen' else '–'} |")
    if "vmec" in aus["felder"]:
        z += ["", "Spulenfeld gegen VMEC-Feld (Erwartung ± 50 %): " + "; ".join(
            f"s = {a['s']}: Verhältnis {a['anteil'] / b['anteil']:.2f}" if b["anteil"] > 0 else f"s = {a['s']}: VMEC-Verlust 0" for a, b in zip(aus["felder"]["spulen"]["flaechen"], aus["felder"]["vmec"]["flaechen"]))]
    if "wandtreffer" in aus:
        w = aus["wandtreffer"]; z += ["", f"Wandtreffer (Spulenfeld): {w['n']}; belegte φ-Bins je Periode {w['belegte_phi_bins']} von {w['phi_bins_je_periode']}; Anteil in den 3 stärksten φ-Bins {100 * w['anteil_in_staerksten_3_phi_bins']:.0f} % (Erwartung: 2–4 Streifen je Periode, Lastkarte `lastkarte_alpha.npz` für K6/K7)."]
    z += ["", "## 2 Bilder", "`bilder/k3_verlust_de.png` / `_en.png` (Zielband = Erwartung beschriftet).", "", "---", "*KI-generiert (Claude Sonnet 5.5), Entwurf, nicht geprüft.*"]
    (Path(OUT) / "ERGEBNIS_test.md" if test else Path(OUT).parent / "ERGEBNIS.md").write_text("\n".join(z) + "\n", encoding="utf-8")
    f = aus["felder"]["spulen"]["flaechen"]; a, b = f[0], f[1]
    baustein_md(Path(OUT) / "baustein" if test else Path(__file__).resolve().parents[1] / "video/bausteine/K3", "K3 Alphateilchen",
                f"Von {a['n']} Alphateilchen, die bei s = {a['s']} starten, gehen bis {aus['tmax_s']} s {a['verloren']} verloren ({100 * a['anteil']:.1f} %); bei s = {b['s']} sind es {b['verloren']} von {b['n']} ({100 * b['anteil']:.1f} %).",
                f"Of {a['n']} alpha particles starting at s = {a['s']}, {a['verloren']} are lost within {aus['tmax_s']} s ({100 * a['anteil']:.1f} %); at s = {b['s']} it is {b['verloren']} of {b['n']} ({100 * b['anteil']:.1f} %).",
                "sim/kandidat/K3/ERGEBNIS.md, auswertung.json (Bahnen als VTK: alpha_bahnen.vtk)", test)


def bild(OUT, aus):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    T = {"de": ("Alphaverlust bis t_max", "Anteil verloren (%)", "Erwartung (Zielband)", "Spulenfeld", "VMEC-Feld", "KI-generiert (Claude Sonnet 5.5), Entwurf"),
         "en": ("alpha loss up to t_max", "fraction lost (%)", "expectation (target band)", "coil field", "VMEC field", "AI-generated (Claude Sonnet 5.5), draft")}
    for sp, (t, yl, bl, c1, c2, fu) in T.items():
        fig, ax = plt.subplots(figsize=(6, 4.2))
        ax.fill_between([0.2, 0.3], 1, 8, color="#ccbb44", alpha=.4, label=bl); ax.fill_between([0.45, 0.55], 3, 15, color="#ccbb44", alpha=.4)
        for nm, lab, col, off in (("spulen", c1, "#4477aa", -0.01), ("vmec", c2, "#228833", 0.01)):
            if nm in aus["felder"]:
                fl = aus["felder"][nm]["flaechen"]; s = [r["s"] + off for r in fl]; y = [100 * r["anteil"] for r in fl]
                ax.errorbar(s, y, yerr=[[100 * r["anteil"] - 100 * r["ci95"][0] for r in fl], [100 * r["ci95"][1] - 100 * r["anteil"] for r in fl]], fmt="o", color=col, label=lab, capsize=3)
        ax.axhline(10, color="r", ls="--", lw=.8); ax.text(0.5, 10.3, "10 %" + (" (Deutung: > 10 % bei s = 0,25 prüfen)" if sp == "de" else " (interpretation: > 10 % at s = 0.25 check)"), fontsize=6, color="r", ha="center")
        ax.set_xlabel("s (Start)"); ax.set_ylabel(yl); ax.set_title(t); ax.legend(fontsize=7); ax.set_xlim(0.15, 0.6)
        fig.text(.5, .01, fu, ha="center", fontsize=7); fig.tight_layout(rect=(0, .04, 1, 1)); fig.savefig(OUT / "bilder" / f"k3_verlust_{sp}.png", dpi=110); plt.close(fig)

def baustein_md(ziel, titel, de, en, quelle, test):
    ziel = Path(ziel); ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "baustein.md").write_text(f"# Szenenbaustein {titel}\n\n> KI-generiert (Claude Sonnet 5.5, 2026-11-13)." + (" RAUCHTEST, keine echten Zahlen." if test else "") + f"\n\n**DE:** {de}\n\n**EN:** {en}\n\nQuelle: {quelle}\n\n---\n*KI-generiert, Entwurf.*\n", encoding="utf-8")
