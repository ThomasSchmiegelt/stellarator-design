"""3D-Galerie der Plasmaformen (reine Flaeche aus den Fourier-Koeffizienten, KEINE VMEC++-Rechnung).

Aufruf (aus ~/hermes/fusion, im Scope, 1 Thread):
  systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 --description="hermes python galerie" \
      env OMP_NUM_THREADS=1 nice .venv-constellaration/bin/python -m stellarator.plasma_galerie

Formen: 10 beste nach QI (rangliste.json, top_gesamt), Kompromiss-Kandidat DATJ5FC..., Basisformen Do3Qy, Kandidat 3 halb, DjLe3eL6.
Flaeche: R(th,ph) = sum r_cos[m,n] cos(m th - nfp n ph), Z = sum z_sin[m,n] sin(m th - nfp n ph); x = R cos ph, y = R sin ph.
Farbe = Hoehe Z. Ausgabe: docs/recherche/spulen_suche/galerie/{*.png, galerie.md, galerie_3d.html, plotly.min.js}.
"""
import csv
import glob
import json
import shutil
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUS = ROOT / "docs" / "recherche" / "spulen_suche" / "galerie"
RL = ROOT / "docs" / "recherche" / "spulen_suche" / "rangliste.json"
CSV = ROOT / "sim" / "qi_flaeche" / "experiment" / "alle_proben.csv"
FORMDIR = ROOT / "sim" / "qi_flaeche" / "experiment" / "form"
NTH, NPH = 96, 160   # Gitter pro Querschnitt / ueber den ganzen Torus


def flaeche(rc, zs, nfp, nph=NPH, nth=NTH):
    rc, zs = np.asarray(rc, float), np.asarray(zs, float)
    M, K = rc.shape
    ns = np.arange(K) - K // 2
    th = np.linspace(0, 2 * np.pi, nth + 1)       # inkl. Endpunkt: Flaeche geschlossen
    ph = np.linspace(0, 2 * np.pi, nph + 1)
    a = np.multiply.outer(th, np.arange(M))[:, None, :, None] - nfp * np.multiply.outer(ph, ns)[None, :, None, :]
    R = (np.cos(a) * rc).sum((2, 3))
    Z = (np.sin(a) * zs).sum((2, 3))
    return R * np.cos(ph)[None, :], R * np.sin(ph)[None, :], Z, R


def parquet_rand(ids):
    import pyarrow.parquet as pq
    out = {}
    for fn in sorted(glob.glob(str(ROOT / "sim/rohdaten/constellaration/train-*.parquet"))):
        for i in [i for i in ids if i not in out]:
            t = pq.read_table(fn, columns=["plasma_config_id", "boundary.json"], filters=[("plasma_config_id", "=", i)])
            if t.num_rows:
                out[i] = json.loads(t.column(1)[0].as_py())
    return out


def auswahl():
    rl = json.load(open(RL))
    alle = {e["name"]: e for k in ("top_gesamt", "top_datensatz", "kompromiss") for e in rl[k]}
    top = [e["name"] for e in rl["top_gesamt"][:10]]
    komp = next(e["name"] for e in rl["kompromiss"] if e["name"].startswith("DATJ5FC"))
    do3 = next(e["name"] for e in rl["top_datensatz"] if e["name"].startswith("Do3Qy"))
    rows = []
    for i, n in enumerate(top, 1):
        rows.append((n, f"QI-Platz {i}", alle[n], "probe"))
    rows.append((komp, "Kompromiss-Kandidat", alle[komp], "parquet"))
    rows.append((do3, "Basisform Do3Qy (bester Datensatz)", alle[do3], "parquet"))
    rows.append(("k3_halb", "Basisform Kandidat 3 halb", alle.get("k3_vernunft_00_basis_s20261205"), "k3"))
    rows.append(("DjLe3eL6", "Basisform DjLe3eL6 (Proxima-Spulen)", None, "dje"))
    return rows


def lade(rows):
    cs = {r["name"]: r for r in csv.DictReader(open(CSV))}
    pq = parquet_rand([n for n, _, _, q in rows if q == "parquet"])
    out, pruef = {}, []
    for n, _, _, q in rows:
        if q == "probe":
            b = json.load(open(FORMDIR / f"{n}.json"))["rand"]
            c = cs[n]
            nz_csv = sum(1 for k, v in c.items() if (k.startswith("r_cos_") or k.startswith("z_sin_")) and float(v) != 0.0)
            nz_q = int(np.count_nonzero(b["r_cos"]) + np.count_nonzero(b["z_sin"]))
            # Wert-Vergleich Gitter CSV (5x9 aufgefuellt) gegen Quelle
            rc = np.array([[float(c[f"r_cos_{m}_{k - 4}"]) for k in range(9)] for m in range(5)])
            zs = np.array([[float(c[f"z_sin_{m}_{k - 4}"]) for k in range(9)] for m in range(5)])
            rq = np.asarray(b["r_cos"]); zq = np.asarray(b["z_sin"])
            pad = np.zeros((5, 9)); pad[:rq.shape[0], 4 - rq.shape[1] // 2:4 - rq.shape[1] // 2 + rq.shape[1]] = rq
            padz = np.zeros((5, 9)); padz[:zq.shape[0], 4 - zq.shape[1] // 2:4 - zq.shape[1] // 2 + zq.shape[1]] = zq
            pruef.append((n, nz_q, nz_csv, float(np.abs(pad - rc).max()), float(np.abs(padz - zs).max()), b["n_field_periods"] == int(float(c.get("nfp", b["n_field_periods"])) if "nfp" in c else b["n_field_periods"])))
        elif q == "parquet":
            b = pq[n]
        elif q == "k3":
            b = json.load(open(ROOT / "sim/qi_flaeche/gegenrechnung_klein/form_k3_f0.5.json"))
        else:
            b = json.load(open(ROOT / "sim/constellaration/qi/proxima_spulen_dje/boundary.json"))
        out[n] = b
    return out, pruef


def bilder(name, b, titel):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import cm
    rc, zs, nfp = np.asarray(b["r_cos"]), np.asarray(b["z_sin"]), int(b["n_field_periods"])
    X, Y, Z, R = flaeche(rc, zs, nfp)
    norm = plt.Normalize(Z.min(), Z.max())
    fc = cm.viridis(norm((Z[:-1, :-1] + Z[1:, 1:]) / 2))
    L = max(np.abs(X).max(), np.abs(Y).max())
    for ansicht, (el, az) in {"schraeg": (35, -60), "oben": (90, -90)}.items():
        fig = plt.figure(figsize=(7.5, 6.2))
        ax = fig.add_subplot(111, projection="3d")
        ax.plot_surface(X, Y, Z, facecolors=fc, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)
        ax.set_xlim(-L, L); ax.set_ylim(-L, L)
        zh = float(np.abs(Z).max()) * 1.05
        ax.set_zlim(-zh, zh)
        ax.set_box_aspect((2 * L, 2 * L, 2 * zh))   # massstabsgetreu: gleiche Einheit auf allen Achsen
        ax.view_init(elev=el, azim=az)
        ax.set_xlabel("x (Einheit: Hauptradius ≈ 1)"); ax.set_ylabel("y")
        if ansicht == "schraeg":
            ax.set_zlabel("Höhe z")
        else:
            ax.set_zticks([])
        ax.set_title(f"{titel}\nnfp = {nfp} Perioden, {ansicht.replace('schraeg', 'schräg')}", fontsize=10)
        sm = cm.ScalarMappable(norm=norm, cmap="viridis")
        cb = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.16)
        cb.set_label("Höhe z der Fläche (gleiche Einheit wie x, y)")
        fig.savefig(AUS / f"{name}_{ansicht}.png", dpi=110, bbox_inches="tight")
        plt.close(fig)
    # geometrische Kennzahlen aus der Fläche selbst (nur zur Plausibilitaet)
    return dict(nfp=nfp, zmin=float(Z.min()), zmax=float(Z.max()), rmin=float(R.min()), rmax=float(R.max()),
                schluss=float(max(np.abs(X[:, 0] - X[:, -1]).max(), np.abs(Z[0] - Z[-1]).max(), np.abs(Z[:, 0] - Z[:, -1]).max())),
                koef=int(np.count_nonzero(rc) + np.count_nonzero(zs)))


def html(daten, titel):
    import plotly.graph_objects as go
    fig = go.Figure()
    namen = list(daten)
    for i, n in enumerate(namen):
        b = daten[n]
        X, Y, Z, _ = flaeche(b["r_cos"], b["z_sin"], int(b["n_field_periods"]), nph=120, nth=64)
        fig.add_trace(go.Surface(x=X.round(4), y=Y.round(4), z=Z.round(4), surfacecolor=Z.round(4), colorscale="Viridis", visible=(i == 0),
                                 colorbar=dict(title="Höhe z"), name=titel[n], showscale=True))
    fig.update_layout(
        title=titel[namen[0]], scene=dict(aspectmode="data", xaxis_title="x", yaxis_title="y", zaxis_title="Höhe z"),
        updatemenus=[dict(buttons=[dict(label=titel[n][:48], method="update", args=[{"visible": [j == i for j in range(len(namen))]}, {"title": titel[n]}])
                                   for i, n in enumerate(namen)], direction="down", x=0.0, y=1.12)],
        margin=dict(l=0, r=0, t=80, b=0))
    p = AUS / "galerie_3d.html"
    fig.write_html(p, include_plotlyjs="directory", full_html=True)   # schreibt plotly.min.js neben die Datei
    return p


def fmt(v, f):
    return "–" if v is None else format(v, f).replace(".", ",")


LESE_ALLG = ("**Lesehilfe (gilt für alle Bilder):** Man sieht die Oberfläche des Plasmaschlauchs, der zum Ring (Torus) geschlossen ist, "
             "gezeichnet nur aus der Formel (Fourier-Koeffizienten), ohne Feldrechnung. Die Farbe ist die Höhe z über der Ringebene "
             "(dunkelblau/violett = tief, gelb = hoch); sie ist keine physikalische Größe des Plasmas (kein Druck, keine Temperatur, kein QI-Wert). "
             "Die Achsen x, y liegen in der Ringebene, Einheit ist der Hauptradius (≈ 1); z ist in derselben Einheit, alle drei Achsen sind maßstabsgetreu "
             "(kein Stauchen). **Worauf achten:** (1) Zahl der Perioden = nfp. Der Ring besteht aus nfp gleichen Abschnitten wie die Zähne eines "
             "Zahnrads; zählt man die Wiederholungen der Form um den Ring, muss nfp herauskommen. (2) Verdrehung des Querschnitts: Der Querschnitt ist "
             "keine feste Ellipse, er dreht sich beim Umlauf um den Ring, wie ein Bandschlüssel, den man entlang des Rings verdrillt. Je größer die "
             "Elongation (Verhältnis lange zu kurze Achse des Querschnitts), desto flacher/bandförmiger der Schlauch. (3) Im Bild von oben sieht man "
             "die Ringform und die Wellen von innen nach außen; die Höhe sieht man dort nur an der Farbe.")


def md(rows, info, pruef):
    Z = ["# Galerie der Plasmaformen (reine 3D-Fläche)", "",
         "Alle Formen sind direkt aus den Randkoeffizienten (`r_cos`, `z_sin`) gezeichnet, **ohne** neue VMEC++-Rechnung. "
         "Erzeugt mit `stellarator/plasma_galerie.py`. Kennzahlen stammen aus `docs/recherche/spulen_suche/rangliste.json`; "
         "„–“ heißt: dort nicht vorhanden (nichts ergänzt).", "",
         "Interaktiv und offline: [galerie_3d.html](galerie_3d.html) (Auswahlfeld oben links, mit der Maus drehbar; braucht `plotly.min.js` im selben Ordner).", "",
         LESE_ALLG, "",
         "## Kennzahlen", "",
         "| Bild-Nr | Name | Rolle | QI | nfp | Aspektverhältnis | max. Elongation | iota/nfp | Spiegelverhältnis |", "|---|---|---|---|---|---|---|---|---|"]
    for i, (n, rolle, e, _) in enumerate(rows, 1):
        g = (lambda k, f: fmt(e.get(k), f)) if e else (lambda k, f: "–")
        nfp = e["nfp"] if e else info[n]["nfp"]
        Z.append(f"| {i} | `{n}` | {rolle} | {g('qi', '.2e')} | {nfp} | {g('A', '.2f')} | {g('elong', '.2f')} | {g('iota', '.3f')} | {g('spiegel', '.3f')} |")
    Z += ["", "QI = quasi-isodynamischer Restwert (kleiner = besser). Spiegelverhältnis = Stärke der Feldmodulation entlang der Feldlinie (Rand). "
          "Für `DjLe3eL6` und `k3_halb` liefert die Rangliste keine eigene Zeile (K3 halb: Zahlen der Basisprobe `k3_vernunft_00_basis`, "
          "gleiche Randkoeffizienten, siehe Prüfung).", ""]
    Z += ["## Bilder", ""]
    for i, (n, rolle, e, _) in enumerate(rows, 1):
        k = info[n]
        Z += [f"### {i}. {n} ({rolle})", "", f"![{n} schräg]({n}_schraeg.png) ![{n} von oben]({n}_oben.png)", "",
              f"**Lesehilfe:** links schräg von vorn, rechts senkrecht von oben. Gezählt: **{k['nfp']} Perioden** (nfp = {k['nfp']}), "
              f"also {k['nfp']} gleiche Abschnitte um den Ring. Höhenbereich der Fläche z = {fmt(k['zmin'], '.2f')} bis {fmt(k['zmax'], '.2f')}, "
              f"Radius R = {fmt(k['rmin'], '.2f')} bis {fmt(k['rmax'], '.2f')} (Einheit Hauptradius ≈ 1). Die Farbe zeigt nur die Höhe z. "
              f"Achten Sie auf die Wellen von Abschnitt zu Abschnitt (Zahnrad) und darauf, wie sich der Querschnitt beim Umlauf dreht.", ""]
    Z += ["## Prüfung (Plausibilität, Datenabgleich)", "",
          "| Form | nicht-null Koeffizienten (Quelle) | in CSV | größte Abweichung r_cos / z_sin |", "|---|---|---|---|"]
    for n, a, b, dr, dz, _ in pruef:
        Z.append(f"| `{n}` | {a} | {b} | {dr:.1e} / {dz:.1e} |")
    Z += ["", "Flächenschluss (größte Lücke zwischen Anfang und Ende in θ und φ) je Form: "
          + ", ".join(f"`{n}` {info[n]['schluss']:.0e}" for n in info) + ".", ""]
    (AUS / "galerie.md").write_text("\n".join(Z))


def main():
    AUS.mkdir(parents=True, exist_ok=True)
    rows = auswahl()
    daten, pruef = lade(rows)
    # k3_halb gegen Basisprobe vergleichen
    bp = json.load(open(FORMDIR / "k3_vernunft_00_basis_s20261205.json"))["rand"]
    k3 = daten["k3_halb"]
    gleich = np.abs(np.asarray(bp["r_cos"]) - np.asarray(k3["r_cos"])).max() if np.shape(bp["r_cos"]) == np.shape(k3["r_cos"]) else None
    print("k3_halb gegen Basisprobe max Abweichung r_cos:", gleich)
    titel = {n: f"{n} ({rolle})" for n, rolle, _, _ in rows}
    info = {n: bilder(n, daten[n], titel[n]) for n in daten}
    for n, k in info.items():
        print(n, k)
    for p in pruef:
        print("pruef", p)
    html(daten, titel)
    md(rows, info, pruef)
    print("HTML MB:", (AUS / "galerie_3d.html").stat().st_size / 1e6)


if __name__ == "__main__":
    main()
