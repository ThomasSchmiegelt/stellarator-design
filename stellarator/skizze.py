"""skizze.py — Skizzen-Werkzeug: Bauteil im Browser drehen, Linien darauf zeichnen, Text dazu, an Claude senden.

    .venv/bin/python -m stellarator.skizze [--port 8765]      dann http://127.0.0.1:8765 im Browser

Modelle: alle Ordner unter sim/kuehlung_segment mit stahl.stl. Fuer den Browser wird einmalig ein leichteres Netz
erzeugt (PicoGK StlSchnitt, grobes Voxel): vorschau_stahl.stl / vorschau_wasser.stl.
Senden legt sim/skizzen/<zeit>/ an: skizze.png (Ansicht mit Linien), skizze.json (Text, Kamera, Linien als
Bildpunkte und als 3D-Punkte auf dem Bauteil in m, dazu R und phi). sim/skizzen/neu.txt nennt die letzte Skizze.
Nur lokal erreichbar (127.0.0.1).
"""
import argparse, base64, json, os, subprocess, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from .kuehlung_segment import WURZEL

PROJEKT = WURZEL.parents[1]
SKIZZEN = PROJEKT / "sim" / "skizzen"
SCHNITT = PROJEKT / "picogk" / "StlSchnitt" / "bin" / "Release" / "net9.0" / "StlSchnitt"
HTML = Path(__file__).with_name("skizze.html")


def modelle():
    return sorted(p.parent.name for p in WURZEL.glob("*/stahl.stl"))


def vorschau(name: str, teil: str, voxel: float = 16.0) -> Path:
    """Leichtes Netz fuer den Browser (einmalig erzeugt)."""
    o = WURZEL / name; ziel = o / f"vorschau_{teil}.stl"
    if not ziel.exists():
        env = {**os.environ, "DOTNET_ROOT": str(Path.home() / ".dotnet")}
        subprocess.run([str(SCHNITT), str(o / f"{teil}.stl"), str(voxel), "1e7", str(ziel)], env=env, check=True,
                       stdout=subprocess.DEVNULL)
    return ziel


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
            name, teil = q["modell"][0], q.get("teil", ["stahl"])[0]
            if name not in modelle() or teil not in ("stahl", "wasser"):
                return self.senden(404, b"unbekannt", "text/plain")
            return self.senden(200, vorschau(name, teil).read_bytes(), "application/octet-stream")
        if u.path == "/lage":
            name = q["modell"][0]
            p = WURZEL / name / "auslegung.json"
            lage = json.loads(p.read_text())["lage"] if p.exists() else {}
            return self.senden(200, json.dumps(lage, default=float).encode(), "application/json")
        self.senden(404, b"", "text/plain")

    def do_POST(self):
        if self.path != "/skizze":
            return self.senden(404, b"", "text/plain")
        d = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        o = SKIZZEN / time.strftime("%Y-%m-%d_%H-%M-%S"); o.mkdir(parents=True, exist_ok=True)
        bild = d.pop("bild", "")
        if bild.startswith("data:image/png;base64,"):
            (o / "skizze.png").write_bytes(base64.b64decode(bild.split(",", 1)[1]))
        (o / "skizze.json").write_text(json.dumps(d, indent=1, ensure_ascii=False))
        (SKIZZEN / "neu.txt").write_text(str(o) + "\n")
        print("SKIZZE", o, flush=True)
        self.senden(200, json.dumps({"ordner": str(o.relative_to(PROJEKT))}).encode(), "application/json")


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args(argv)
    SKIZZEN.mkdir(parents=True, exist_ok=True)
    print(f"Skizzen-Werkzeug: http://127.0.0.1:{a.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), Antwort).serve_forever()


if __name__ == "__main__":
    main()
