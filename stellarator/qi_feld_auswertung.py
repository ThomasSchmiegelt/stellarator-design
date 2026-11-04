"""qi_feld_auswertung.py — Tabelle der QI-Tragwerksvarianten aus den Rechendaten (keine Handabschrift).

  .venv/bin/python -m stellarator.qi_feld_auswertung              # -> sim/qi_feld/tabelle.md
  .venv/bin/python -m stellarator.qi_feld_auswertung beste 11 12  # gibt die Zusatzparameter der besten Nummer aus

Varianten stehen in sim/qi_feld/varianten.txt (studie|nr|stufe|name|zusatzparameter). Spannung je Spule aus struktur.vtu.
Bewertung (F-225): massgebend ist der Stahl-p99 der heißesten Spule ohne 0,5-m-Randzone um Verbinder und Lager
(submodell.p99_ohne_rand_je_spule). Alte ergebnis.json ohne diesen Wert: aus sim/qi_feld/heisse_spule.json
(stellarator.heisse_spule, aus struktur.vtu nachgerechnet), sonst "–" und die Grenzenspalte zeigt "alt:".
500 MPa und 0,3 % sind Richtwerte (Annahmen); Stufe unter 500 / 500 bis 800 / über 800.
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


def heiss(st, nr, e):
    """(Spule, MPa) der heißesten Spule ohne Randzone oder None."""
    if "stahl_heiss" in e["struktur"]:
        h = e["struktur"]["stahl_heiss"]; return h["spule"], h["p99_ohne_rand_MPa"]
    c = ORD / "heisse_spule.json"
    d = json.loads(c.read_text()).get(f"{st}/{int(nr):04d}") if c.exists() else None
    return (d["heiss_spule"], d["heiss_p99_ohne_rand_MPa"]) if d else None


def zeile(st, nr, stufe, name, extra):
    from .kopplung import stahl_stufe, A
    po = punkt(st, nr); f = po / "ergebnis.json"
    if not f.exists():
        return f"| {st} | {nr} | {name} | kein Ergebnis | | | | | | | | | | | | | |"
    e = json.loads(f.read_text()); s = e["struktur"]; b = e["bewertung"]
    h = heiss(st, nr, e)
    rest = all(v for k_, v in b["grenzen"].items() if k_ != "stahl_p99")
    if h:
        hs = f"{h[1]:.0f} (Spule {h[0]})"; stu = stahl_stufe(h[1])
        ok = "ja" if rest and h[1] <= A["sigma_zul_MPa"] else "nein"
    else:
        hs, stu, ok = "–", "–", "alt: " + ("ja" if b["alle_ok"] else "nein")
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
            f"{s['stahl']['vm_p99_MPa']:.0f} | {je} | {hs} | {stu} | {s['stahl']['vm_max_MPa']:.0f} | {100 * b['dehnung_wp']:.2f} | "
            f"{s['stahl']['masse_t']:.0f} | {rep} | {e['package'].get('freiraum_alt_m', e['package']['freiraum_min_m']):.2f} | "
            f"{e['package'].get('freiraum_huelle_m', float('nan')):.2f} | {ok} |")


def tabelle():
    k = ("| Studie | Nr | Variante | Verbinder ok/Plätze | u max mm | Stahl p90 MPa | Stahl p99 MPa | p99 je Spule MPa | "
         "heißeste Spule MPa | Stufe | Stahl max MPa | Dehnung WP % | Stahl t | Reparaturrunden | Freiraum alt m | Freiraum Hülle m | "
         "alle Richtwerte (heißeste Spule) |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    t = ("# QI-Tragwerk: Varianten (automatisch aus den Rechendaten)\n\nRichtwerte (Annahmen, keine harten Grenzen): "
         "Stahl 500 MPa, Dehnung Wickelpaket 0,3 %. Maßgebend für Stahl ist seit F-225 der p99 der heißesten Spule ohne "
         "0,5-m-Randzone um Verbinder und Lager („heißeste Spule MPa“); „Stahl p99 MPa“ ist der alte Wert über alle Spulen. "
         "„alt:“ = heißeste Spule noch nicht bestimmt, Bewertung nach altem Maßstab.\n\n" + k)
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
