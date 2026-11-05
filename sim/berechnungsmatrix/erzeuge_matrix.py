"""Erzeugt den Experiment-Teil der Berechnungsmatrix (matrix.tsv) reproduzierbar aus stellarator/qi_experiment.py (F-252).

Aufruf (aus dem Projektordner): .venv-constellaration/bin/python sim/berechnungsmatrix/erzeuge_matrix.py [matrix.tsv]
Handgeschriebene Zeilen (alles vor der Markierungszeile) bleiben erhalten; Auswertungszeilen (id beginnt mit AUSW) wandern auf
die letzte Stufe. Alles ab der Markierung wird bei jedem Aufruf neu geschrieben (gleiche Eingabe -> gleiche Datei).
Stufen: 4 Vorbereitung (Datensatz lesen, Sekunden), 5 Strom-Proben (vernunft zuerst, dann wild), 6 vernuenftige Formproben
(je Rang alle vier Basisformen nacheinander, Basisrechnungen zuerst), 7 wilde Formproben abwechselnd mit der
Datensatz-Stichprobe, danach Linearitaetsproben, 8 alle Auswertungen. Reihenfolge = Wert der Daten bei Abbruch.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from stellarator.qi_experiment import BASEN, N_DS, ds_name, formplan, stromplan  # noqa: E402

MARKE = "# ---- ab hier erzeugt von sim/berechnungsmatrix/erzeuge_matrix.py (nicht von Hand aendern; neu erzeugen) ----"
E = "sim/qi_flaeche/experiment"
PY = "@PY@ -m stellarator.qi_experiment"
ST_VOR, ST_STROM, ST_VERN, ST_WILD, ST_AUSW = 4, 5, 6, 7, 8
GB = 6


def main(datei):
    alt = datei.read_text().splitlines() if datei.exists() else []
    kopf = []
    for z in alt:
        if z.strip() == MARKE:
            break
        kopf.append(z)
    hand, ausw = [], []
    for z in kopf:
        if z.startswith("#") or not z.strip():
            hand.append(z); continue
        f = z.split("|")
        if f[0].startswith("AUSW"):
            f[1] = str(ST_AUSW); ausw.append("|".join(f))
        else:
            hand.append(z)
    neu = [MARKE]
    neu.append(f"EXP_VORBEREITEN|{ST_VOR}|{GB}|{E}/vorbereitung.json|{PY} vorbereiten")
    sp = stromplan()
    for p in [p for p in sp if p["modus"] == "vernunft"] + [p for p in sp if p["modus"] == "wild"]:
        neu.append(f"XS_{p['name']}|{ST_STROM}|{GB}|{E}/strom/{p['name']}.json|{PY} strom {p['name']}")
    fp = formplan()

    def je_basis(prio):
        L = {b: [p for p in fp if p["basis"] == b and p["prio"] == prio] for b in BASEN}
        out = []
        for i in range(max(len(v) for v in L.values())):
            out += [L[b][i] for b in BASEN if i < len(L[b])]
        return out

    def fz(p, st):
        return f"XF_{p['name']}|{st}|{GB}|{E}/form/{p['name']}.json|{PY} form {p['name']}"
    for p in je_basis(1):
        neu.append(fz(p, ST_VERN))
    wild = je_basis(2); ds = list(range(N_DS)); i = j = 0
    while i < len(wild) or j < len(ds):                       # abwechselnd: wild, Datensatz
        if i < len(wild):
            neu.append(fz(wild[i], ST_WILD)); i += 1
        if j < len(ds):
            neu.append(f"XD_{ds_name(ds[j])}|{ST_WILD}|{GB}|{E}/datensatz/{ds_name(ds[j])}.json|{PY} datensatz {ds[j]}"); j += 1
    for p in je_basis(3):
        neu.append(fz(p, ST_WILD))
    ausw = [z for z in ausw if not z.startswith("AUSW_EXPERIMENT|")] + [f"AUSW_EXPERIMENT|{ST_AUSW}|4||{PY} auswertung"]
    datei.write_text("\n".join(hand + ausw + neu) + "\n")
    n = {}
    for z in hand + ausw + neu:
        if z.startswith("#") or not z.strip():
            continue
        n[z.split("|")[1]] = n.get(z.split("|")[1], 0) + 1
    print("Zeilen je Stufe:", dict(sorted(n.items(), key=lambda t: int(t[0]))))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "sim" / "berechnungsmatrix" / "matrix.tsv")
