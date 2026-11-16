"""k8_tragwerk.py — Schritt K8: Tragwerk (Gehaeuse + Verbinder, Elmer-FEM) fuer den Spulensatz aus sim/kandidat/kandidat.json.
KI-generiert (Claude Sonnet 5.5, 2026-11-13). Erwartung: sim/kandidat/erwartung/K8.md (Opus, vor der Rechnung).

    .venv/bin/python -m stellarator.k8_tragwerk [--test] [--weiter]

Kette wie sim/kette_k3/lauf_vergleich_fem.sh (B-081 ff.): satz_nach_kopplung (.venv-opt) -> kopplung punkt --von qi_proxima_dpr/0012
--p strom_je_spule=1 (.venv). Wanddicken = Parameter dieses Punkts (Waende, huelle_min_m 1,5, wand_adapt), Regel des Autors:
Bewertung = p99 der heissesten Spule ohne 0,5-m-Randzone (stahl_heiss.p99_ohne_rand_MPa, submodell.p99_ohne_rand_je_spule).
500 MPa = ANNAHME (kopplung.ANNAHMEN, Nutzer 2026-11-04), 800 MPa = zweite Stufe (STUFEN_MPa).
Varianten: V0 Basis; ist p99 > 500 -> V1 x1,25; V2 x1,5; V3 x2 (Opus 2026-11-13). Bleibt p99 nach V2 > 800 -> HALT (Opus).
Lorentzkraefte: kopplung.hexmodell.lorentzdichte aus den Stroemen je Spule (Netto 0,17-4,0 GN laut K2 P3; hier nur nachgemeldet).
Fertige Varianten (ergebnis.json im Punktordner) werden uebersprungen. --test: stationen_faktor 0,15, MUMPS 20 GB, Studie k8_test, nie die echte ERGEBNIS.md.
Speicher: FEM braucht bei 40 Spulen ~18 GB (K3, 11 GB reichten nicht, F-283); Umgebungsvariable FEM_MEM (Standard 20G, direkte Loesung MUMPS).
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time
from pathlib import Path

from .kandidat_hilfe import PROJEKT, KAND, kandidat, pfad, jetzt, aus_wurzel

K8 = (aus_wurzel() or KAND) / "K8"        # FUSION_K_AUS: Variantenlauf schreibt nach <Ordner>/K8
PY, PYOPT = str(PROJEKT / ".venv" / "bin" / "python"), str(PROJEKT / ".venv-opt" / "bin" / "python")
VON = "qi_proxima_dpr/0012"
GRENZE_MPa, STUFE2_MPa = 500.0, 800.0          # 500: Annahme (kopplung.STUFEN_MPa), 800: zweite Stufe
VARIANTEN = [("v0", 1.0), ("v1", 1.25), ("v2", 1.5), ("v3", 2.0)]


def scope(cmd: list[str], mem: str, log: Path, env: dict | None = None) -> int:
    c = ["systemd-run", "--user", "--scope", "-q", f"--unit=hermes-fusion-k8-{os.getpid()}-{int(time.time())}", "-p", f"MemoryMax={mem}", "-p", "MemorySwapMax=0",
         "nice", "-n", "10", "env", "OMP_NUM_THREADS=4", "JAX_PLATFORMS=cpu"] + cmd
    with open(log, "a") as f:
        f.write(f"$ {' '.join(cmd)}\n"); f.flush()
        return subprocess.call(c, cwd=PROJEKT, stdout=f, stderr=subprocess.STDOUT, env={**os.environ, **(env or {})})


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--test", action="store_true")
    ap.add_argument("--studie", default=None, help="Studienname unter sim/kopplung (Standard k8_dgoz; Variantenlauf: neuer Name, alte Studie bleibt)")
    ap.add_argument("--regel", choices=["v1"], default=None, help="Regel V1 (Opus 2026-11-15): wand_seite_m 0,30 fest, wand_adapt (Faktor bis 3, 5 Runden) nur innen/aussen; statt der Staffel v0-v3")
    ap.add_argument("--mit-v0", action="store_true", help="mit --regel: zuerst v0 (Punkt 0) rechnen, Regelpunkt wird Punkt 1")
    a = ap.parse_args(argv)
    t0 = time.time(); start = jetzt(); k = kandidat()
    o = K8 / ("test" if a.test else "lauf"); o.mkdir(parents=True, exist_ok=True); log = o / "lauf.log"
    mem = os.environ.get("FEM_MEM", "20G")
    satz = pfad(k["spulensatz"]); bsf = pfad(k["biot_savart"]); wout = pfad(k["wout"])
    for p, von in ((satz / "pruefung_satz.json", "K2/Kette DGoz"), (bsf, "K2/Kette DGoz"), (wout, "GX-Lauf DGoz")):
        if not p.exists():
            print(f"ABBRUCH: Eingabe fehlt: {p} (kommt aus {von}).", file=sys.stderr); sys.exit(2)
    if not (pfad("sim/kopplung") / VON.split("/")[0] / "punkte" / VON.split("/")[1] / "param.json").exists():
        print(f"ABBRUCH: Referenzpunkt {VON} fehlt.", file=sys.stderr); sys.exit(2)
    P1 = json.loads(pfad(k["k2"] + "/P1.json").read_text())
    # Massstab L = faktor_k aus K2 (P1.json), NICHT a_gross/a: pruefung_satz.json["a"] ist eine andere Groesse als a_klein (L waere 36,33 statt 35,85)
    a_m = P1["faktor_k"] * json.loads((satz / "pruefung_satz.json").read_text())["a"]
    st = "k8_test2" if a.test else (a.studie or "k8_dgoz")
    po = PROJEKT / "sim" / "kopplung" / st / "punkte" / "0000"
    if not (po / "geometrie.json").exists():                       # 1. Umwandlung (3 s)
        if scope([PYOPT, "-m", "stellarator.satz_nach_kopplung", str(satz), st, "--a", str(a_m), "--wout", str(wout),
                  "--herkunft", f"Datensatzform {k['id']} (ConStellaration), unveraendert; eigene Spulen ohne Kreuzung"], "3G", log):
            sys.exit(f"ABBRUCH: Umwandlung fehlgeschlagen, siehe {log}")
    base = json.loads((PROJEKT / "sim" / "kopplung" / VON.split("/")[0] / "punkte" / VON.split("/")[1] / "param.json").read_text())
    res = []
    REGEL_P = ["strom_je_spule=1", "wand_seite_m=0.30", "wand_adapt=1", "wand_fak_max=3", "wand_runden=5", "wand_adapt_seiten=0"]
    if a.regel:
        VAR = ([("v0", 1.0)] if a.mit_v0 else []) + [("regel_v1", 1.0)]
    else:
        VAR = VARIANTEN
    for idx, (name, f) in enumerate(VAR):
        nr = idx if a.regel else int(name[1]); pn = PROJEKT / "sim" / "kopplung" / st / "punkte" / f"{nr:04d}"
        if not (pn / "ergebnis.json").exists():
            pz = ["strom_je_spule=1"] + [f"{q}={base[q] * f}" for q in ("wand_innen_m", "wand_seite_m", "t_min_m")] if f != 1.0 else ["strom_je_spule=1"]
            if name == "regel_v1":
                pz = REGEL_P
            if a.test:
                pz += ["stationen_faktor=0.15"] 
            rc = scope([PY, "-m", "stellarator.kopplung", "punkt", "--studie", st, "--nr", str(nr), "--von", VON if (nr == 0 or (a.regel and not a.mit_v0)) else f"{st}/0000", "--p"] + pz, mem, log)
            if rc or not (pn / "ergebnis.json").exists():
                print(f"ABBRUCH: FEM {name} fehlgeschlagen (rc {rc}), siehe {log}", file=sys.stderr); sys.exit(5)
        e = json.loads((pn / "ergebnis.json").read_text())["struktur"]
        r = {"variante": name, "faktor_wand": f, "p99_heisse_ohne_rand_MPa": e["stahl_heiss"]["p99_ohne_rand_MPa"], "heisse_spule": e["stahl_heiss"]["spule"],
             "u_max_mm": e["u_max_mm"], "kraft_MN_max_je_spule": e["kraft_MN_max_je_spule"], "quelle": str(pn.relative_to(PROJEKT) / "ergebnis.json")}
        res.append(r); print(r, flush=True)
        if a.test or (not a.regel and r["p99_heisse_ohne_rand_MPa"] <= GRENZE_MPa):
            break
    (o / "ergebnis.json").write_text(json.dumps({"varianten": res, "start": start, "ende": jetzt()}, indent=1))
    if a.test:
        (o / "TEST_OK.txt").write_text(f"{jetzt()} Umwandlung + FEM (stationen_faktor 0,15, MUMPS 20 GB) gelaufen, {(time.time() - t0) / 60:.1f} min\n"); return
    last = res[-1]; halt = ""
    if last["p99_heisse_ohne_rand_MPa"] > STUFE2_MPa:
        halt = f"HALT: p99 heisseste Spule {last['p99_heisse_ohne_rand_MPa']:.0f} MPa > {STUFE2_MPa:.0f} MPa nach {len(res) - 1} Verstaerkungsvarianten (bis x2); Lastpfad/Stuetzstellen pruefen (Opus)\n\n"
    zeilen = "\n".join(f"| {r['variante']} (Waende x{r['faktor_wand']}) | {r['p99_heisse_ohne_rand_MPa']:.0f} MPa (Spule {r['heisse_spule']}) | {r['u_max_mm']:.0f} mm | {r['kraft_MN_max_je_spule']:.0f} MN | {r['quelle']} |" for r in res)
    md = f"""{halt}# ERGEBNIS K8 · Tragwerk (Elmer-FEM)
KI-generiert (Claude Sonnet 5.5, Skript stellarator/k8_tragwerk.py). Status Entwurf, ungeprueft. Start {start}, Ende {jetzt()}, Dauer {(time.time() - t0) / 60:.0f} min.

Form {k['id']} (Datensatzform unveraendert), Spulensatz {k['spulensatz']}. Bewertung: p99 der heissesten Spule ohne 0,5-m-Randzone.
Richtwert 500 MPa = Annahme (nicht belegt); zweite Stufe 800 MPa.

| Variante | p99 heisseste Spule ohne Rand | u_max | Kraft max je Spule | Quelle |
|---|---|---|---|---|
{zeilen}

Vergleich mit Erwartung (400-1000 MPa, Auslenkung < 0,1 % der Spulenlaenge): durch PI/Opus. Spulenlaenge fuer den Auslenkungsvergleich: aus sim/kopplung/{st}/punkte/0000/spulen.json.

---
*KI-generiert. Status Entwurf.*
"""
    (K8 / "ERGEBNIS.md").write_text(md)


if __name__ == "__main__":
    main()
