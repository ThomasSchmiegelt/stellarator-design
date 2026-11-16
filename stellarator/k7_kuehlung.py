"""k7_kuehlung.py — Schritt K7: Kuehlung Erste Wand / Gefaess an der Form aus sim/kandidat/kandidat.json.
KI-generiert (Claude Sonnet 5.5, 2026-11-13). Erwartung: sim/kandidat/erwartung/K7.md (Opus, vor der Rechnung).

    .venv/bin/python -m stellarator.k7_kuehlung [--test] [--voxel 8] [--weiter]

Ablauf (jeder Teil pausierbar/neustartbar: fertige Teile werden uebersprungen):
  1. Eingaben: sim/kandidat/K6/ergebnis.json (Wandlast; Abbruch 2 wenn fehlt), K5/ERGEBNIS.md (muss da sein, nicht HALT).
  2. Segment-Geometrie: stellarator.kuehlung_segment (PicoGK) mit f12-Parametern (sim/kuehlung_segment/f12), Randflaeche aus der
     Form des Kandidaten (Umgebungsvariablen FUSION_RAND_WOUT/FAKTOR, siehe gyroid_gefaess.randflaeche), Regel Rohr 300/400 mm.
  3. FluidX3D (GPU): stellarator.kuehlung_cfd (nur wenn GPU frei, nvidia-smi); Lizenz FluidX3D: nicht MIT, eigene Kopie
     ~/fluidx3d_stellarator, nur setup.cpp/defines geaendert (siehe kuehlung_cfd.py).
  4. Waermeuebergang: stellarator.kuehlung_waerme; Wandtemperatur = T_Wasser (319 C Austritt, WWER-1000, docs/recherche/pi/ergebnis.md)
     + dT Wasser-Uebergang + dT Leitung Innenhaut. 550 C = Annahme (EUROFER, Erwartung K7).
  5. ERGEBNIS.md erst am Ende. --test: kleinste Aufloesung, Platzhalter, Ausgabe nach sim/kandidat/K7/test/, nie die echte ERGEBNIS.md.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time
from pathlib import Path

from .kandidat_hilfe import PROJEKT, KAND, kandidat, pfad, eingabe_oder_abbruch, ergebnis_halt_pruefen, gpu_warten, jetzt

K7 = KAND / "K7"
PY = str(PROJEKT / ".venv" / "bin" / "python")
T_WASSER_AUS_C = 319.0       # Druckwasser 289 -> 319 C (WWER-1000), Beleg docs/recherche/pi/ergebnis.md
T_GRENZE_C = 550.0           # Annahme (EUROFER), Erwartung K7
SEG = PROJEKT / "sim" / "kuehlung_segment"


def sh(cmd: list[str], log: Path, env: dict | None = None) -> int:
    with open(log, "a") as f:
        f.write(f"$ {' '.join(cmd)}\n"); f.flush()
        return subprocess.call(cmd, cwd=PROJEKT, stdout=f, stderr=subprocess.STDOUT, env={**os.environ, **(env or {})})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true"); ap.add_argument("--voxel", type=float, default=None, help="mm; Standard 16 (echt; 8 mm wie f12 waere ~1,4 Mrd Zellen, Segment radial 21 m statt 9 m), 60 (Test)")
    ap.add_argument("--span", type=float, default=None, help="Winkelbreite des Segments [Grad]; Standard: Bogenlaenge wie f12 (10 Grad bei R0 10,4 m) -> 10*10,4/R0 aus kandidat.json (27,6 m: 3,77 Grad)")
    ap.add_argument("--t_phys", type=float, default=40.0)
    a = ap.parse_args(argv)
    t0 = time.time(); start = jetzt()
    k = kandidat(); o = K7 / ("test" if a.test else "lauf"); o.mkdir(parents=True, exist_ok=True)
    log = o / "lauf.log"; name = "k7_test" if a.test else "k7_mittel"
    if a.span is None: a.span = round(10.0 * 10.4 / float(k["R0_m"]), 2)   # Opus 2026-11-15: nicht mehr fest 3,0 (galt fuer 34,7 m)
    vox = a.voxel or (60.0 if a.test else 16.0)
    ergebnis_halt_pruefen("K5/ERGEBNIS.md", "K5") if not a.test else None
    w = eingabe_oder_abbruch("K6/ergebnis.json", ["erstwand_waermestrom_spitze_MW_m2", "erstwand_waermestrom_mittel_MW_m2"], "K6", a.test,
                             {"erstwand_waermestrom_spitze_MW_m2": 0.5, "erstwand_waermestrom_mittel_MW_m2": 0.25})
    q = float(w["erstwand_waermestrom_spitze_MW_m2"]); q_m = float(w["erstwand_waermestrom_mittel_MW_m2"])
    # Opus 2026-11-15 (Erwartung K7 Nachtrag 3, Entscheidung Autor a): Durchfluss nach Mittel, Spitze oertlich (Lauf 1 k7: Spitze flaechig, HALT)
    P1 = json.loads(pfad(kandidat()["k2"] + "/P1.json").read_text())
    env = {"FUSION_RAND_WOUT": str(pfad(k["wout"])), "FUSION_RAND_FAKTOR": str(P1["faktor_k"])}
    out = SEG / name
    # 2. Geometrie
    if not (out / "ergebnis.json").exists():
        f12 = json.loads((SEG / "f12" / "auslegung.json").read_text())["parameter"]
        c = 90.0; ph0, ph1 = c - a.span / 2, c + a.span / 2
        cmd = [PY, "-m", "stellarator.kuehlung_segment", "--name", name, "--phi0", str(ph0), "--phi1", str(ph1), "--q_MW", str(q_m), "--dT", "10",
               "--haut_innen", str(f12["haut_innen"]), "--zelle", str(f12["zelle"]), "--halbdicke", str(f12["halbdicke"]),
               "--kammer_ein", str(f12["kammer_ein"]), "--kammer_aus", str(f12["kammer_aus"]), "--ohne_platte", "--ruhe", "0",
               "--d_loch", str(f12["d_loch"]), "--n_loch", str(f12["n_loch"]), "--d_ein", "300", "--d_aus", "400",   # Regel Austritt > Eintritt (300/400)
               "--schraeg", "--ein_innen", "--schicht", str(f12["schicht"]), "--zelle_vorn", str(f12["zelle_vorn"]),
               "--halbdicke_vorn", str(f12["halbdicke_vorn"]), "--voxel", str(vox), "--max_gb", "11"]
        if sh(cmd, log, env):
            sys.exit(f"ABBRUCH: kuehlung_segment fehlgeschlagen, siehe {log}")
    # 3. CFD
    if not (out / "cfd" / "auswertung.json").exists() and (a.test or not list((out / "cfd").glob("feld_*.bin"))):   # fertiges Feld nicht neu rechnen
        gpu_warten()
        cmd = [PY, "-m", "stellarator.kuehlung_cfd", "--name", name, "--dx", str(vox), "--max_gb", "8"]
        cmd += ["--probe", "--stat", "10"] if a.test else ["--t_phys", str(a.t_phys), "--stat", "4000"]
        if sh(cmd, log, env):
            sys.exit(f"ABBRUCH: kuehlung_cfd fehlgeschlagen, siehe {log}")
    # 3b. Auswertung (kuehlung_cfd.main rechnet nur; auswerten() schreibt auswertung.json). Fehlte bis 2026-11-15 (K7-Abbruch 14:38).
    if not a.test and not (out / "cfd" / "auswertung.json").exists() and list((out / "cfd").glob("feld_*.bin")):
        if sh([PY, "-c", f"from pathlib import Path; from stellarator.kuehlung_cfd import auswerten; auswerten(Path({str(out)!r}))"], log, env):   # env: Randflaeche des Kandidaten (sonst alte Form, leere Plasmaseite)
            sys.exit(f"ABBRUCH: kuehlung_cfd.auswerten fehlgeschlagen, siehe {log}")
    if a.test and not (out / "cfd" / "auswertung.json").exists():
        print("Probelauf ohne Auswertung (Probe schreibt nur stat.txt): Rest nur mit echtem Lauf pruefbar."); (o / "TEST_OK.txt").write_text(f"{jetzt()} Geometrie + CFD-Probe gelaufen\n"); return
    # 4. Waerme
    if sh([PY, "-m", "stellarator.kuehlung_waerme", "--name", name, "--q", str(q)], log, env):
        sys.exit(f"ABBRUCH: kuehlung_waerme fehlgeschlagen, siehe {log}")
    wj = json.loads((out / "waerme.json").read_text()); cj = json.loads((out / "cfd" / "auswertung.json").read_text())
    aj = json.loads((out / "auslegung.json").read_text())
    haut = wj["dT_haut_K"].get(f"{aj['parameter']['haut_innen'] * 1000:.0f} mm", 0.0)
    u = {z["fall"]: z for z in wj["uebergang"]}["Plasmaseite Mittel"]
    t_ohne = T_WASSER_AUS_C + u["dT_wasser_ohne_rippe_K"] + haut        # Spitze (waerme.json mit --q Spitze)
    t_mit = T_WASSER_AUS_C + u["dT_wasser_mit_rippe_K"] + haut
    f_m = q_m / q                                                          # dT linear in q (Leitung und Uebergang)
    tm_ohne = T_WASSER_AUS_C + f_m * (u["dT_wasser_ohne_rippe_K"] + haut); tm_mit = T_WASSER_AUS_C + f_m * (u["dT_wasser_mit_rippe_K"] + haut)
    erg = {"q_spitze_MW_m2": q, "q_mittel_MW_m2": q_m, "T_wand_mittel_ohne_rippe_C": tm_ohne, "T_wand_mittel_mit_rippe_C": tm_mit, "druckverlust_kPa": cj["druckverlust_kPa"], "v_plasmaseite_mittel_m_s": cj["plasmaseite"]["v_mittel_m_s"],
           "T_wand_max_ohne_rippe_C": t_ohne, "T_wand_max_mit_rippe_C": t_mit, "dT_haut_K": haut, "T_wasser_aus_C": T_WASSER_AUS_C,
           "grenze_C": T_GRENZE_C, "voxel_mm": vox, "start": start, "ende": jetzt(), "dauer_min": (time.time() - t0) / 60}
    (o / "ergebnis.json").write_text(json.dumps(erg, indent=1))
    if a.test:
        (o / "TEST_OK.txt").write_text(f"{jetzt()} komplett (Test, Platzhalter)\n"); return
    halt = "" if tm_ohne <= T_GRENZE_C else f"BEFUND (kein HALT, Autor 2026-11-15: Kette weiter): Wandtemperatur bei Mittellast {tm_ohne:.0f} C > {T_GRENZE_C:.0f} C (Annahme); Verteilung vorn pruefen (Deutung K7 Nachtrag 3)\n\n"
    if not halt and t_ohne > T_GRENZE_C:
        halt = f"BEFUND (kein HALT): Spitze oertlich {t_ohne:.0f} C > {T_GRENZE_C:.0f} C -> oertliche Massnahme noetig\n\n"
    md = f"""{halt}# ERGEBNIS K7 · Kuehlung Erste Wand / Gefaess
KI-generiert (Claude Sonnet 5.5, Skript stellarator/k7_kuehlung.py). Status Entwurf, ungeprueft. Start {start}, Ende {erg['ende']}, Dauer {erg['dauer_min']:.0f} min.

| Groesse | Wert | Quelle |
|---|---|---|
| Waermestrom Spitze / Mittel (aus K6) | {q:.4f} / {q_m:.4f} MW/m2 (Durchfluss nach Mittel) | sim/kandidat/K6/ergebnis.json |
| Wandtemperatur bei Mittellast (ohne / mit Rippen) | {tm_ohne:.0f} / {tm_mit:.0f} C | waerme.json, linear auf q_mittel |
| Druckverlust Segment | {cj['druckverlust_kPa']:.1f} kPa | sim/kuehlung_segment/{name}/cfd/auswertung.json |
| v Plasmaseite Mittel | {cj['plasmaseite']['v_mittel_m_s']:.3f} m/s | dito |
| Wandtemperatur Spitze oertlich (ohne / mit Rippen) | {t_ohne:.0f} / {t_mit:.0f} C | sim/kuehlung_segment/{name}/waerme.json + T_Wasser 319 C (WWER-1000, docs/recherche/pi/ergebnis.md) |
| Grenze Wand | {T_GRENZE_C:.0f} C (Annahme, EUROFER) | Erwartung K7 |

Segment: Rand der Form {k['id']} (unveraendert), Rohre 300/400 mm (Austritt > Eintritt). Aufloesung {vox} mm; Segmentbreite {a.span} Grad.
Vergleich mit Erwartung (350-500 C, dp +-30 % gegen frueher 19,4 kPa f12): durch PI/Opus.

---
*KI-generiert. Status Entwurf.*
"""
    (K7 / "ERGEBNIS.md").write_text(md)


if __name__ == "__main__":
    main()
