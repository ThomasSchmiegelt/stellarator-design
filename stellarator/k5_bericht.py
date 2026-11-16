"""K5: ERGEBNIS.md.  KI-generiert (Claude Sonnet 5.5, 2026-11-13)."""
from pathlib import Path


def schreibe(OUT, test, e):
    a = e["anteil_flaeche_unter_m"]; h = e["anteil_flaeche_unter_m_halbdiagonale"]; st = e["stelle_min"]
    z = ["| Dok.-Nr. | FUS-ERG-K5 | Version | 0.1 | Status | Entwurf |", "|---|---|---|---|---|---|",
         "| Titel | Ergebnis K5 · Platz zwischen Plasma und Spulen (DGozX5fj) | Ersteller | Claude Sonnet 5.5 (KI) | Prüfer | – (Opus/Mensch offen) |", ""]
    z += ["> **KI-generiert (Claude Sonnet 5.5, 2026-11-13).** Erwartung `sim/kandidat/erwartung/K5.md` (unverändert), Eingabe `sim/kandidat/kandidat.json`. Entwurf, keine Deutung. Zahlen aus `auswertung.json`."
          + (" **RAUCHTEST (grobe Abtastung).**" if test else ""), f"> Form: Datensatzform ConStellaration DGozX5fj unverändert; Spulen: eigene. Rechnung {e['start']} bis {e['ende']} (date).", "",
          "## 1 Zahlen", "| Größe | Wert | Anmerkung |", "|---|---|---|",
          f"| kleinster Abstand Spulenmitte–Plasmarand | {e['abstand_mitte_min_m']:.2f} m | Vergleich K2 P4 `{e['quelle_K2']}` (5,14 m im Ergebnis K2d) |",
          f"| Wickelpaket (Kante) | {e['wickelpaket_m']:.2f} m | kandidat.json |",
          f"| **freier Platz min** (Mitte − Wickelpaket/2) | **{e['frei_min_m']:.2f} m** | Erwartung ≥ 4,4 m frei im Minimum; Stelle φ = {st['phi_grad']:.0f}° |",
          f"| freier Platz Mittel (flächengewichtet) / max | {e['frei_mittel_m']:.2f} m / {e['frei_max_m']:.2f} m | |",
          f"| freier Platz min, konservativ (Halbdiagonale) | {e['frei_min_halbdiagonale_m']:.2f} m | Annahme: Paket um 45° gedreht |",
          f"| Reserve gegen 2,1 m | {e['reserve_min_m']:.2f} m | Erwartung ≥ 2 m Reserve |",
          f"| Flächenanteil frei < 3 m | {100 * a[3.0]:.1f} % (konservativ {100 * h[3.0]:.1f} %) | Erwartung < 5 % |",
          f"| Flächenanteil frei < 2,1 m / < 1,7 m | {100 * a[2.1]:.1f} % / {100 * a[1.7]:.1f} % | |", "",
          "## 2 Nötiger Aufbau (Annahmen aus der Erwartung K5, hier nicht belegt)", "| Teil | von (m) | bis (m) |", "|---|---|---|"]
    z += [f"| {x['teil']} | {x['min_m']} | {x['max_m']} |" for x in e["aufbau"]]
    z += [f"| Summe | {e['aufbau_summe_m'][0]:.2f} | {e['aufbau_summe_m'][1]:.2f} |", "",
          "Hinweis: Die Erwartung nennt die Summe 1,7–2,1 m, die Teilwerte ergeben 1,73–2,13 m; die Deutung nutzt 1,7 und 2,1 m wie dort festgelegt (offen für Opus).", "",
          f"Abtastung: {e['abtastung']}. Bilder `bilder/k5_platz_de.png` / `_en.png` (Linien 1,7 / 2,1 / 3 m beschriftet), Szenenbaustein `video/bausteine/K5/plasma_platz.vtk` (Skalar frei_m).", "", "---", "*KI-generiert (Claude Sonnet 5.5), Entwurf, nicht geprüft.*"]
    import os
    baustein_md(Path(OUT) if (test or os.environ.get("FUSION_K_AUS")) else Path(__file__).resolve().parents[1] / "video/bausteine/K5", "K5 Platz",
                f"Zwischen Plasmarand und Innenkante des Wickelpakets bleiben mindestens {e['frei_min_m']:.2f} m frei (Mittel {e['frei_mittel_m']:.1f} m); der nötige Aufbau beträgt {e['aufbau_summe_m'][0]:.2f}–{e['aufbau_summe_m'][1]:.2f} m (Annahme).",
                f"At least {e['frei_min_m']:.2f} m remain free between the plasma edge and the inner edge of the winding pack (mean {e['frei_mittel_m']:.1f} m); the required build-up is {e['aufbau_summe_m'][0]:.2f}–{e['aufbau_summe_m'][1]:.2f} m (assumption).",
                "sim/kandidat/K5/ERGEBNIS.md, auswertung.json; Geometrie plasma_platz.vtk", test)
    (Path(OUT) / "ERGEBNIS_test.md" if test else Path(OUT).parent / "ERGEBNIS.md").write_text("\n".join(z) + "\n", encoding="utf-8")

def baustein_md(ziel, titel, de, en, quelle, test):
    ziel = Path(ziel); ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "baustein.md").write_text(f"# Szenenbaustein {titel}\n\n> KI-generiert (Claude Sonnet 5.5, 2026-11-13)." + (" RAUCHTEST, keine echten Zahlen." if test else "") + f"\n\n**DE:** {de}\n\n**EN:** {en}\n\nQuelle: {quelle}\n\n---\n*KI-generiert, Entwurf.*\n", encoding="utf-8")
