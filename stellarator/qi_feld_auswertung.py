"""qi_feld_auswertung.py — Tabelle der QI-Tragwerksvarianten aus den Rechendaten (keine Handabschrift).

  .venv/bin/python -m stellarator.qi_feld_auswertung              # -> sim/qi_feld/tabelle.md
  .venv/bin/python -m stellarator.qi_feld_auswertung beste 11 12  # gibt die Zusatzparameter der besten Nummer aus

Varianten stehen in sim/qi_feld/varianten.txt (studie|nr|stufe|name|zusatzparameter). Spannung je Spule aus struktur.vtu.
Bewertung wie in der Studie: Stahl-p99 <= 500 MPa, Dehnung Wickelpaket <= 0,3 %.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ORD = ROOT / "sim" / "qi_feld"


def varianten():
    return [z.strip().split("|") for z in (ORD / "varianten.txt").read_text().splitlines() if z.strip() and z[0] != "#"]


def punkt(st, nr):
    return ROOT / "sim" / "kopplung" / st / "punkte" / f"{int(nr):04d}"


def zeile(st, nr, stufe, name, extra):
    po = punkt(st, nr); f = po / "ergebnis.json"
    if not f.exists():
        return f"| {st} | {nr} | {name} | kein Ergebnis | | | | | | | | |"
    e = json.loads(f.read_text()); s = e["struktur"]; b = e["bewertung"]
    je = "–"; p90 = float("nan")
    v = po / "struktur.vtu"
    if v.exists():
        import pyvista as pv
        g = pv.read(v); m = g.cell_data["material"]; q = g.cell_data["vonmises_MPa"]; sp = g.cell_data["spule"]
        st_ = m == 3; p90 = float(np.percentile(q[st_], 90))
        w = [float(np.percentile(q[st_ & (sp == c)], 99)) for c in np.unique(sp[st_])]
        je = f"{min(w):.0f}–{max(w):.0f}"
    r = po / "reparatur.json"
    rep = json.loads(r.read_text())["runden"] if r.exists() else 0
    return (f"| {st} | {nr} | {name} | {s['verbinder_ok']}/{s['verbinder_kandidaten']} | {s['u_max_mm']:.0f} | {p90:.0f} | "
            f"{s['stahl']['vm_p99_MPa']:.0f} | {je} | {s['stahl']['vm_max_MPa']:.0f} | {100 * b['dehnung_wp']:.2f} | "
            f"{s['stahl']['masse_t']:.0f} | {rep} | {e['package'].get('freiraum_alt_m', e['package']['freiraum_min_m']):.2f} | "
            f"{e['package'].get('freiraum_huelle_m', float('nan')):.2f} | {'ja' if b['alle_ok'] else 'nein'} |")


def tabelle():
    k = ("| Studie | Nr | Variante | Verbinder ok/Plätze | u max mm | Stahl p90 MPa | Stahl p99 MPa | p99 je Spule MPa | "
         "Stahl max MPa | Dehnung WP % | Stahl t | Reparaturrunden | Freiraum alt m | Freiraum Hülle m | alle Grenzen |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    t = "# QI-Tragwerk: Varianten (automatisch aus den Rechendaten)\n\nGrenzen: Stahl p99 500 MPa, Dehnung Wickelpaket 0,3 %.\n\n" + k
    t += "\n".join(zeile(*v[:5]) for v in varianten()) + "\n"
    (ORD / "tabelle.md").write_text(t)


def beste(nummern):
    w = []
    for st, nr, stufe, name, extra in varianten():
        f = punkt(st, nr) / "ergebnis.json"
        if nr in nummern and f.exists():
            w.append((json.loads(f.read_text())["struktur"]["stahl"]["vm_p99_MPa"], nr, extra))
    print(min(w)[2] if w else "")


if __name__ == "__main__":
    beste(sys.argv[2:]) if len(sys.argv) > 1 and sys.argv[1] == "beste" else tabelle()
