"""schnitt_werkzeug.py — Schnitte durch ein FluidX3D-Stroemungsfeld im Browser festlegen und als Bild rechnen lassen.

    .venv/bin/python -m stellarator.schnitt_werkzeug [--port 8766]      dann http://127.0.0.1:8766 im Browser

Modelle: alle Ordner unter sim/kuehlung_segment mit cfd/feld_*.bin. Im Browser liegt der Wasserraum als grobes Netz;
der Schnitt wird als Ebene festgelegt (Winkel phi, Hoehe z oder Linie ueber das Bauteil gezogen, Ebene = Linie +
Blickrichtung) und erscheint als Vorschau. "Senden und naechster Schnitt" / "Senden und beenden" rechnet das Bild aus
dem Feld (Gitter regelmaessig abgetastet, halbe Zellweite) und legt sim/schnitte/<zeit>/ an:
  schnitt.png   Groesse farbig (|v|, v senkrecht zur Ebene oder Druck), Stahl grau (aus dem Abstand zum Wasser
                genaehert), optional Stromlinien der Geschwindigkeit in der Ebene
  schnitt.json  Ebene (Punkt, Normale, Achsen), Bereich, Text, Kennwerte
sim/schnitte/neu.txt nennt den letzten Schnitt (ein KI-Agent kann darauf warten); bei "beenden" steht dort zusaetzlich
ENDE. Ein Rechteck im Ergebnisbild setzt den Ausschnitt fuer den naechsten Schnitt. Nur lokal (127.0.0.1).
"""
import argparse, json, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import numpy as np

from .kuehlung_segment import WURZEL

PROJEKT = WURZEL.parents[1]
SCHNITTE = PROJEKT / "sim" / "schnitte"
HTML = Path(__file__).with_name("schnitt_werkzeug.html")
STAHL_ABSTAND = 0.12          # Nicht-Wasser naeher als das am Wasser gilt als Stahl [m] (Naeherung)
_feld, _sperre = {}, threading.Lock()


def modelle():
    return sorted({p.parents[1].name for p in WURZEL.glob("*/cfd/feld_*.bin") if (p.parents[1] / "cfd/fall.json").exists()})


def feld(name: str) -> dict:
    """Feld eines Modells dicht auf dem Gitter (einmal je Modell geladen)."""
    with _sperre:
        if _feld.get("name") != name:
            from .kuehlung_cfd import lese_feld
            _feld.clear()
            F = lese_feld(WURZEL / name); f = F["fall"]; N = tuple(f["N"]); i, j, k = F["ijk"].T
            W = np.zeros(N, bool); W[i, j, k] = True
            U = np.zeros(N + (3,), np.float16); U[i, j, k] = F["u"]
            P = np.zeros(N, np.float16); P[i, j, k] = F["p"] / 1000
            _feld.update(name=name, W=W, U=U, P=P, x0=np.array(f["ursprung_m"]), dx=f["dx_m"], N=np.array(N),
                         t=F["t_s"], datei=F["datei"])
        return _feld


def vorschau(name: str) -> Path:
    """Grobes Netz des Wasserraums (24 mm) fuer den Browser, einmalig aus den Gitterzellen."""
    ziel = WURZEL / name / "cfd" / "vorschau_wasser.stl"
    if not ziel.exists():
        import pyvista as pv
        F = feld(name); s = 3
        W = F["W"][::s, ::s, ::s].astype(np.float32)
        g = pv.ImageData(dimensions=W.shape, spacing=(F["dx"] * s * 1000,) * 3, origin=tuple(F["x0"] * 1000))
        g.point_data["w"] = W.ravel(order="F")
        m = g.contour([0.5], scalars="w").decimate(0.7).extract_surface().triangulate()
        m.save(str(ziel))
    return ziel


def ebene(e: dict) -> tuple:
    """Punkt p0, Achsen e1, e2, Normale n, Bereich in e1 (oder None) und Achsennamen aus der Browser-Angabe."""
    if e["typ"] == "phi":
        ph = np.radians(e["wert"]); e1 = np.array([np.cos(ph), np.sin(ph), 0.0]); e2 = np.array([0, 0, 1.0])
        return np.zeros(3), e1, e2, np.cross(e1, e2), None, ("R [m]", "z [m]"), f"φ = {e['wert']:.2f}°"
    if e["typ"] == "z":
        return np.array([0, 0, e["wert"]]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0]), None, \
            ("x [m]", "y [m]"), f"z = {e['wert']:.3f} m"
    p1, p2, d = (np.array(e[k], float) for k in ("p1", "p2", "blick"))
    e1 = (p2 - p1) / np.linalg.norm(p2 - p1); n = np.cross(e1, d); n /= np.linalg.norm(n); e2 = np.cross(n, e1)
    if e2[2] < 0:
        e2, n = -e2, -n
    L = float(np.linalg.norm(p2 - p1))
    return p1, e1, e2, n, (0.0, L), ("entlang der Linie [m]", "quer dazu [m]"), \
        f"Linie ({p1[0]:.2f}, {p1[1]:.2f}, {p1[2]:.2f}) → ({p2[0]:.2f}, {p2[1]:.2f}, {p2[2]:.2f}) m"


def schnitt(d: dict, o: Path) -> dict:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm, Normalize, TwoSlopeNorm
    from scipy.ndimage import distance_transform_edt
    F = feld(d["modell"]); dx = F["dx"]; h = dx / 2
    p0, e1, e2, n, ub, achsen, beschr = ebene(d["ebene"])
    # Bereich: Ecken des Rechengebiets in die Ebene projiziert, dann auf Wasser zuschneiden
    lo, hi = F["x0"], F["x0"] + (F["N"] - 1) * dx
    ecken = np.array([[a, b, c] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for c in (lo[2], hi[2])]) - p0
    u0, u1 = (ecken @ e1).min(), (ecken @ e1).max(); v0, v1 = (ecken @ e2).min(), (ecken @ e2).max()
    if ub:
        u0, u1 = ub
    if d.get("ausschnitt"):
        u0, u1, v0, v1 = d["ausschnitt"]
    uu = np.arange(u0, u1, h); vv = np.arange(v0, v1, h)
    if uu.size * vv.size > 2.5e7:                       # Schutz vor riesigen Bildern
        f = np.sqrt(uu.size * vv.size / 2.5e7); uu = np.arange(u0, u1, h * f); vv = np.arange(v0, v1, h * f)
    G = p0 + uu[None, :, None] * e1 + vv[:, None, None] * e2          # (nv, nu, 3)
    I = np.rint((G - F["x0"]) / dx).astype(np.int64)
    gut = np.all((I >= 0) & (I < F["N"]), axis=2)
    I = np.where(gut[..., None], I, 0)
    nass = gut & F["W"][I[..., 0], I[..., 1], I[..., 2]]
    if not nass.any():
        raise ValueError("Die Ebene schneidet kein Wasser.")
    if not d.get("ausschnitt"):                          # auf Wasser zuschneiden (+ Rand)
        r = 0.15; jj, ii = np.where(nass)
        su = slice(max(ii.min() - int(r / h), 0), ii.max() + int(r / h) + 1)
        sv = slice(max(jj.min() - int(r / h), 0), jj.max() + int(r / h) + 1)
        uu, vv, I, nass = uu[su], vv[sv], I[sv, su], nass[sv, su]
    Uv = F["U"][I[..., 0], I[..., 1], I[..., 2]].astype(np.float32)
    gr = d.get("groesse", "v")
    if gr == "v":
        wert = np.linalg.norm(Uv, axis=2); einheit = "Geschwindigkeit |v| [m/s]"; cmap = "turbo"
    elif gr == "vn":
        wert = Uv @ n.astype(np.float32); einheit = "Geschwindigkeit senkrecht zur Ebene [m/s]"; cmap = "RdBu_r"
    else:
        wert = F["P"][I[..., 0], I[..., 1], I[..., 2]].astype(np.float32); einheit = "Druck relativ zum Austritt [kPa]"; cmap = "viridis"
    werte = wert[nass]
    if gr == "vn":
        g_ = float(np.percentile(np.abs(werte), 99)) or 1e-3; norm = TwoSlopeNorm(0, -g_, g_)
    elif gr == "v" and d.get("skala", "log") == "log":
        norm = LogNorm(max(1e-3, float(np.percentile(werte, 1))), max(float(werte.max()), 2e-3))
    else:
        norm = Normalize(float(np.percentile(werte, 0.5)), float(np.percentile(werte, 99.5)))
    stahl = (~nass) & (distance_transform_edt(~nass) * h < STAHL_ABSTAND)
    B = np.ones(nass.shape + (4,)); B[stahl] = (0.55, 0.57, 0.6, 1); B[~stahl & ~nass] = (1, 1, 1, 0)
    ext = (uu[0] - h / 2, uu[-1] + h / 2, vv[0] - h / 2, vv[-1] + h / 2)
    breite = 13.0; hoehe = min(max(breite * (ext[3] - ext[2]) / (ext[1] - ext[0]) * 0.82, 4.0), 11.0)
    fig, ax = plt.subplots(figsize=(breite, hoehe + 1.2))
    ax.set_facecolor("white")
    ax.imshow(B, origin="lower", extent=ext, interpolation="nearest")
    im = ax.imshow(np.ma.masked_where(~nass, wert), origin="lower", extent=ext, cmap=cmap, norm=norm,
                   interpolation="nearest")
    if d.get("stromlinien", True):
        s = max(1, int(round(max(nass.shape) / 300)))
        a1 = np.ma.masked_where(~nass[::s, ::s], Uv[::s, ::s] @ e1.astype(np.float32))
        a2 = np.ma.masked_where(~nass[::s, ::s], Uv[::s, ::s] @ e2.astype(np.float32))
        try:
            ax.streamplot(uu[::s], vv[::s], a1, a2, color="white", linewidth=0.6, density=2.2, arrowsize=0.7,
                          broken_streamlines=True)
        except Exception as ex:                          # Stromlinien sind Beiwerk
            print("Stromlinien:", ex)
    ax.set_xlim(ext[:2]); ax.set_ylim(ext[2:]); ax.set_aspect("equal")
    ax.set_xlabel(achsen[0]); ax.set_ylabel(achsen[1])
    fig.colorbar(im, ax=ax, label=einheit, shrink=0.85, pad=0.02)
    ax.set_title(f"{d['modell']}: Schnitt {beschr} · Stahl grau (genähert) · "
                 f"{'Stromlinien in der Ebene · ' if d.get('stromlinien', True) else ''}FluidX3D t = {F['t']:.0f} s", fontsize=11)
    fig.tight_layout(); fig.savefig(o / "schnitt.png", dpi=110);
    pos = ax.get_position()
    plt.close(fig)
    return {"bereich": [float(e) for e in ext], "achsen_bild": [pos.x0, pos.y0, pos.x1, pos.y1],
            "p0_m": p0.tolist(), "e1": e1.tolist(), "e2": e2.tolist(), "normale": n.tolist(), "beschreibung": beschr,
            "wasserzellen_im_schnitt": int(nass.sum()),
            "wert_min": float(werte.min()), "wert_median": float(np.median(werte)), "wert_max": float(werte.max()),
            "einheit": einheit}


class Antwort(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def senden(self, code, daten: bytes, typ: str):
        self.send_response(code); self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(daten))); self.end_headers(); self.wfile.write(daten)

    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        if u.path == "/":
            return self.senden(200, HTML.read_bytes(), "text/html; charset=utf-8")
        if u.path == "/modelle":
            return self.senden(200, json.dumps(modelle()).encode(), "application/json")
        if u.path == "/netz":
            name = q["modell"][0]
            if name not in modelle():
                return self.senden(404, b"unbekannt", "text/plain")
            return self.senden(200, vorschau(name).read_bytes(), "application/octet-stream")
        if u.path == "/fall":
            name = q["modell"][0]
            f = json.loads((WURZEL / name / "cfd" / "fall.json").read_text())
            p = WURZEL / name / "auslegung.json"
            lage = json.loads(p.read_text()).get("lage", {}) if p.exists() else {}
            return self.senden(200, json.dumps({"fall": f, "lage": lage}, default=float).encode(), "application/json")
        if u.path == "/bild":
            p = (SCHNITTE / q["ordner"][0] / "schnitt.png").resolve()
            if SCHNITTE.resolve() in p.parents and p.exists():
                return self.senden(200, p.read_bytes(), "image/png")
        self.senden(404, b"", "text/plain")

    def do_POST(self):
        if self.path != "/schnitt":
            return self.senden(404, b"", "text/plain")
        d = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        o = SCHNITTE / time.strftime("%Y-%m-%d_%H-%M-%S"); o.mkdir(parents=True, exist_ok=True)
        try:
            erg = schnitt(d, o)
        except Exception as ex:
            return self.senden(400, json.dumps({"fehler": str(ex)}).encode(), "application/json")
        d["ergebnis"] = erg
        (o / "schnitt.json").write_text(json.dumps(d, indent=1, ensure_ascii=False))
        ende = d.get("aktion") == "ende"
        (SCHNITTE / "neu.txt").write_text(str(o) + ("\nENDE\n" if ende else "\n"))
        print("SCHNITT", o, "ENDE" if ende else "", flush=True)
        self.senden(200, json.dumps({"ordner": o.name, **erg}).encode(), "application/json")


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8766)
    a = ap.parse_args(argv)
    SCHNITTE.mkdir(parents=True, exist_ok=True)
    print(f"Schnitt-Werkzeug: http://127.0.0.1:{a.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), Antwort).serve_forever()


if __name__ == "__main__":
    main()
