"""picogk_bruecke.py — Wickelpakete -> PicoGK-Voxelkoerper + Belegungsgitter fuer den Solver.

Ablauf: Python schreibt Wickelpaket-STL (mm) und die Kandidaten-Gitterpunkte (nahe am
Filament), die headless PicoGK-App (picogk/StellaratorVoxel) voxelisiert, bildet das
Gehaeuse per Offset und prueft die Kandidaten mit bIsInside. Ohne gebaute App (oder mit
modus="python") wird die Belegung direkt aus dem lokalen Rechteckquerschnitt bestimmt —
beide Wege sind als Gegenprobe vergleichbar.
"""
from __future__ import annotations
import json, os, subprocess, time
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .spulen import Spule, rahmen, rohr_dreiecke, schreibe_stl

PICOGK_APP = Path(__file__).resolve().parents[1] / "picogk" / "StellaratorVoxel"
PICOGK_BIN = PICOGK_APP / "bin" / "Release" / "net9.0" / "StellaratorVoxel"


@dataclass
class Gitter:
    ursprung: np.ndarray   # (3,) m, Mittelpunkt der Zelle (0,0,0)
    h: float               # m
    n: tuple[int, int, int]

    @classmethod
    def um(cls, spulen: list[Spule], h: float, rand: float) -> "Gitter":
        P = np.vstack([s.punkte for s in spulen])
        lo, hi = P.min(0) - rand, P.max(0) + rand
        n = tuple(int(v) for v in np.ceil((hi - lo) / h) + 1)
        return cls(lo, h, n)

    def punkte(self, idx: np.ndarray) -> np.ndarray:
        i, j, k = np.unravel_index(idx, self.n)
        return self.ursprung + self.h * np.column_stack([i, j, k])


def zuordnung(spulen: list[Spule], x: np.ndarray):
    """Naechster Filamentpunkt je Punkt x: (spulen-index, punkt-index, abstand)."""
    P = np.vstack([s.punkte for s in spulen])
    sid = np.concatenate([np.full(len(s.punkte), i) for i, s in enumerate(spulen)])
    pid = np.concatenate([np.arange(len(s.punkte)) for s in spulen])
    d, k = cKDTree(P).query(x)
    return sid[k], pid[k], d


def kandidaten(spulen, gitter: Gitter, breite, hoehe) -> np.ndarray:
    """Flache Gitterindizes mit Abstand zum Filament < halbe Diagonale + Zelldiagonale."""
    r = 0.5 * np.hypot(breite, hoehe) + gitter.h * np.sqrt(3)
    baum = cKDTree(np.vstack([s.punkte for s in spulen]))
    out = []
    nx, ny, nz = gitter.n
    for i in range(nx):                       # schichtweise, spart Speicher
        J, K = np.meshgrid(np.arange(ny), np.arange(nz), indexing="ij")
        x = gitter.ursprung + gitter.h * np.column_stack([np.full(J.size, i), J.ravel(), K.ravel()])
        d, _ = baum.query(x, distance_upper_bound=r)
        out.append(np.ravel_multi_index((np.full(J.size, i), J.ravel(), K.ravel()), gitter.n)[d < r])
    return np.concatenate(out).astype(np.int32)


def abstand_python(spulen, gitter: Gitter, idx, breite, hoehe) -> np.ndarray:
    """Vorzeichenbehafteter Abstand [m] zum Rechteckquerschnitt im lokalen Rahmen des
    naechsten Filamentpunkts (innen < 0)."""
    x = gitter.punkte(idx)
    sid, pid, _ = zuordnung(spulen, x)
    fr = [rahmen(s) for s in spulen]
    N = np.array([fr[s][1][p] for s, p in zip(sid, pid)])
    B = np.array([fr[s][2][p] for s, p in zip(sid, pid)])
    d = x - np.array([spulen[s].punkte[p] for s, p in zip(sid, pid)])
    q = np.column_stack([np.abs(np.sum(d * N, 1)) - breite / 2, np.abs(np.sum(d * B, 1)) - hoehe / 2])
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0)


def anteil(abstand: np.ndarray, h: float) -> np.ndarray:
    """Volumenanteil einer Wuerfelzelle aus dem Mittelpunktsabstand (ebene Naeherung)."""
    return np.clip(0.5 - abstand / h, 0.0, 1.0)


def baue_app() -> None:
    env = os.environ | {"DOTNET_ROOT": str(Path.home() / ".dotnet"),
                        "PATH": f"{Path.home() / '.dotnet'}:{os.environ['PATH']}"}
    subprocess.run(["dotnet", "build", "-c", "Release", "-v", "q"], cwd=PICOGK_APP, env=env,
                   check=True, capture_output=True)


def voxelisiere(spulen, gitter: Gitter, ordner: Path, breite, hoehe,
                voxel_mm=20.0, gehaeuse_mm=60.0, modus="picogk", log=print) -> dict:
    """Schreibt STL, laeuft PicoGK (oder Python), liefert dict mit idx/anteil und Kennzahlen."""
    ordner.mkdir(parents=True, exist_ok=True)
    tri = np.concatenate([rohr_dreiecke(s, breite, hoehe) for s in spulen])
    stl = ordner / "wickelpaket_eingabe.stl"
    schreibe_stl(stl, tri)
    t0 = time.time()
    idx = kandidaten(spulen, gitter, breite, hoehe)
    log(f"  Gitter {gitter.n} h={gitter.h} m, Kandidaten {idx.size}  ({time.time()-t0:.1f} s)")
    info = {"modus": modus, "kandidaten": int(idx.size)}
    if modus == "picogk":
        if not PICOGK_BIN.exists():
            log("  PicoGK-App nicht gebaut -> dotnet build")
            baue_app()
        (ordner / "kandidaten.i32").write_bytes(idx.tobytes())
        auftrag = {"voxel_mm": voxel_mm, "stl_wickel": str(stl), "gehaeuse_mm": gehaeuse_mm,
                   "ausgabe": str(ordner), "kandidaten": str(ordner / "kandidaten.i32"),
                   "gitter": {"ursprung_mm": (gitter.ursprung * 1000).tolist(),
                              "h_mm": gitter.h * 1000, "n": list(gitter.n)}}
        (ordner / "auftrag.json").write_text(json.dumps(auftrag, indent=2))
        env = os.environ | {"DOTNET_ROOT": str(Path.home() / ".dotnet")}
        t0 = time.time()
        r = subprocess.run([str(PICOGK_BIN), str(ordner / "auftrag.json")], env=env,
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"PicoGK fehlgeschlagen:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
        log("  " + r.stdout.strip().splitlines()[-1] + f"  ({time.time()-t0:.1f} s)")
        abstand = np.frombuffer((ordner / "abstand.f32").read_bytes(), np.float32) / 1000.0
        info |= json.loads((ordner / "ergebnis.json").read_text())
    else:
        abstand = abstand_python(spulen, gitter, idx, breite, hoehe)
    a = anteil(abstand, gitter.h)
    m = a > 0
    info["zellen_mit_strom"] = int(m.sum())
    info["volumen_gitter_m3"] = float(a.sum() * gitter.h ** 3)
    np.savez_compressed(ordner / "belegung.npz", idx=idx[m], anteil=a[m], ursprung=gitter.ursprung,
                        h=gitter.h, n=np.array(gitter.n))
    return info | {"idx": idx[m], "anteil": a[m]}
