"""K4: ERGEBNIS.md und Bild.  KI-generiert (Claude Sonnet 5.5, 2026-11-13)."""
from pathlib import Path


def schreibe(OUT, test, e):
    OUT = Path(OUT); (OUT / "bilder").mkdir(exist_ok=True); bild(OUT, e)
    g, geo, pl, bi = e["gx"], e["geometrie"], e["plasma_bei_s"], e["bilanz"]
    z = ["| Dok.-Nr. | FUS-ERG-K4 | Version | 0.1 | Status | Entwurf |", "|---|---|---|---|---|---|",
         "| Titel | Ergebnis K4 · Turbulenz (GX) in voller Größe einordnen (DGozX5fj) | Ersteller | Claude Sonnet 5.5 (KI) | Prüfer | – (Opus/Mensch offen) |", "",
         "> **KI-generiert (Claude Sonnet 5.5, 2026-11-13).** Erwartung `sim/kandidat/erwartung/K4.md` (unverändert), Eingabe `sim/kandidat/kandidat.json`. Entwurf, keine Deutung. Zahlen aus `auswertung.json`.",
         f"> Form: Datensatzform ConStellaration DGozX5fj unverändert. GX-Lauf vorhanden (keine neue GPU-Rechnung): `{e['gx_datei']}`. Rechnung {e['start']} bis {e['ende']} (date).", "",
         "## 1 Zahlen", "| Größe | Wert | Quelle/Annahme |", "|---|---|---|",
         f"| Q_i/Q_GB (GX, Mittel t ≥ {g['ab']:.0f}) | {g['Q_i']:.3f} ± {g['fehler']:.3f} | GX-Lauf, eine Flussröhre s = 0,64, a/L_T = 3, a/L_n = 1 |",
         f"| a, B_ref (physikalisch) | {geo['a_m']:.2f} m, {geo['B_ref_phys_T']:.3f} T | wout, k = {geo['k']:.2f}; B_ref über Achsfeld auf B0 skaliert |",
         f"| T_i, n bei s = 0,64 | {pl['T_keV']:.2f} keV, {pl['n_1e20']:.3f}·10²⁰ m⁻³ | Stufe-0-Profile (Annahme T_i = T_e, n_i = n_e) |",
         f"| ρ_i/a | {pl['rho_i_durch_a']:.4f} | m_i = 2,5 u (Annahme) |",
         f"| Q_GB | {e['QGB_MW_m2']:.4f} MW/m² | n T v_t (ρ/a)² (Annahme Konvention) |",
         f"| GX-Ionenwärmefluss | {e['Q_GX_ionen_MW_m2']:.3f} MW/m² | Q_i/Q_GB · Q_GB |",
         f"| nötiger Fluss durch s = 0,64 | {bi['Q_noetig_MW_m2']:.3f} MW/m² | ({bi['F_alpha_bis_s']:.3f}·{bi['P_alpha_MW']:.0f} − {bi['F_brems_bis_s']:.3f}·{bi['P_brems_MW']:.0f}) MW = {bi['P_durch_s_MW']:.0f} MW durch {geo['S_s_m2']:.0f} m² |",
         f"| **Verhältnis GX / nötig** | **{e['verhaeltnis']:.2f}** (Erwartung 0,5–5) | bei 50 % Ionenanteil am Transport (Annahme): {e['verhaeltnis_bei_50_prozent_ionenanteil']:.2f} |", "",
         f"Zur Einordnung: Stufe 0 nimmt H = {e['H_ISS04']:.2f} auf ISS04 an. Grenzen: eine Flussröhre, ein Gradient, adiabatische Elektronen (nur Ionenfluss), keine Profilrückwirkung. Bild `bilder/k4_fluss_de.png` / `_en.png` (Zielband 0,5–5 beschriftet).", "",
         "---", "*KI-generiert (Claude Sonnet 5.5), Entwurf, nicht geprüft.*"]
    baustein_md(Path(OUT) / "baustein" if test else Path(__file__).resolve().parents[1] / "video/bausteine/K4", "K4 Turbulenz",
                f"Der Ionen-Wärmefluss aus GX beträgt {e['Q_GX_ionen_MW_m2']:.3f} MW/m², der nötige Fluss durch die Fläche s = 0,64 {bi['Q_noetig_MW_m2']:.3f} MW/m²: Verhältnis {e['verhaeltnis']:.2f} (Annahmen siehe ERGEBNIS).",
                f"The GX ion heat flux is {e['Q_GX_ionen_MW_m2']:.3f} MW/m², the required flux through the surface s = 0.64 is {bi['Q_noetig_MW_m2']:.3f} MW/m²: ratio {e['verhaeltnis']:.2f} (assumptions see result file).",
                "sim/kandidat/K4/ERGEBNIS.md, auswertung.json", test)
    (Path(OUT) / "ERGEBNIS_test.md" if test else Path(OUT).parent / "ERGEBNIS.md").write_text("\n".join(z) + "\n", encoding="utf-8")


def bild(OUT, e):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    T = {"de": ("Turbulenter Wärmefluss gegen nötigen Fluss", "Wärmefluss (MW/m²)", ["GX Ionen", "nötig (Bilanz)"], "Erwartung Verhältnis 0,5–5 (Zielband)", "Deutungsgrenze (Erwartung K4): > 3 × nötig → H 1,3 fraglich", "KI-generiert (Claude Sonnet 5.5), Entwurf"),
         "en": ("Turbulent heat flux versus required flux", "heat flux (MW/m²)", ["GX ions", "required (balance)"], "expected ratio 0.5–5 (target band)", "interpretation limit (expectation K4): > 3 × required → H 1.3 doubtful", "AI-generated (Claude Sonnet 5.5), draft")}
    q = [e["Q_GX_ionen_MW_m2"], e["bilanz"]["Q_noetig_MW_m2"]]
    for sp, (t, yl, lab, bl, gr, fu) in T.items():
        fig, ax = plt.subplots(figsize=(6, 4.2)); ax.bar(lab, q, color=["#4477aa", "#228833"])
        ax.axhspan(0.5 * q[1], 5 * q[1], color="#ccbb44", alpha=.3, label=bl + " (× nötig)" if sp == "de" else bl + " (× required)"); ax.axhline(3 * q[1], color="r", ls="--", label=gr)
        ax.set_ylabel(yl); ax.set_title(t); ax.legend(fontsize=7); fig.text(.5, .01, fu, ha="center", fontsize=7); fig.tight_layout(rect=(0, .04, 1, 1)); fig.savefig(OUT / "bilder" / f"k4_fluss_{sp}.png", dpi=110); plt.close(fig)

def baustein_md(ziel, titel, de, en, quelle, test):
    ziel = Path(ziel); ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "baustein.md").write_text(f"# Szenenbaustein {titel}\n\n> KI-generiert (Claude Sonnet 5.5, 2026-11-13)." + (" RAUCHTEST, keine echten Zahlen." if test else "") + f"\n\n**DE:** {de}\n\n**EN:** {en}\n\nQuelle: {quelle}\n\n---\n*KI-generiert, Entwurf.*\n", encoding="utf-8")
