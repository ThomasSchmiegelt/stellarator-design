"""QI aus den Spulen: Free-boundary VMEC++ mit Proximas Spulensatz DjLe3eL6 (Spulen -> Magnetfeld -> Plasmagrenze -> QI).

Aufruf (aus ~/hermes/fusion, je Rechnung ein eigener Scope, hoechstens 2 parallel):
  .venv-constellaration/bin/python -m stellarator.qi_spulen tabelle [<tabellenname> [<verschiebung>]]  # Feld je 1 A und Spulengruppe
  systemd-run --user --scope -q -p MemoryMax=6G -p MemorySwapMax=0 --description="hermes python qi_spulen basis" \
      env OMP_NUM_THREADS=2 .venv-constellaration/bin/python -m stellarator.qi_spulen eins basis
  .venv-constellaration/bin/python -m stellarator.qi_spulen liste      # alle Faelle (Teil B/C) ausgeben
  .venv-constellaration/bin/python -m stellarator.qi_spulen auswertung # Tabelle + Bilder aus fertigen Faellen

Verfahren (Weg i):
  1. Spulen: Proxima CoilStellaration DjLe3eL6KjahKZboHs6o7rc (5 Basisspulen, nfp 4, Stellarator-Symmetrie -> 40 Spulen),
     Kurven wie stellarator/proxima_spulen.py (CurveXYZFourier Ordnung 7, Sinus-Vorzeichen -1), Massstab des Datensatzes (R ~ 1).
  2. Tabelle: Magnetfeld je Spulengruppe (Basisspule + ihre 7 Symmetrie-Kopien) fuer 1 A auf einem Zylindergitter
     (R, phi, Z) ueber eine Feldperiode, phi-Punkte = nzeta von VMEC++ (24). Eigene Biot-Savart-Rechnung mit simsopt
     (nicht vmecpp-makegrid, weil simsopt bei gespiegelten Spulen das Stromvorzeichen umdreht und die Normierung je Ampere
     dann zweideutig waere). Speicherreihenfolge wie vmecpp mgrid_provider: index = (k*nZ + jz)*nR + ir.
  3. Kalibrierung: alle Stroeme gemeinsam mit k skaliert, so dass der Toroidalfluss der Spulen durch den Soll-Querschnitt
     (phi = 0) gleich phiedge der offiziellen Rechnung ist (pi a^2). Damit ist die Soll-Plasmagrenze die Flaeche mit genau
     dem offiziellen Fluss, wenn die Spulen sie exakt erzeugen.
  4. VMEC++ free-boundary: constellaration.forward_model unveraendert (ConstellarationSettings.default_high_fidelity(),
     alle Kennzahlen gleich gerechnet), nur vmec_utils.run_vmec wird durch eine Free-boundary-Variante ersetzt
     (lfreeb, extcur, Feldtabelle im Speicher, Soll-Rand nur als Startwert). Danach booz_xform + QI auf 14 Flaechen
     wie stellarator/qi_karte.py.
Faelle (Teil B/C): Name -> Faktoren je Spulengruppe (Strom) bzw. Verschiebung einer Basisspule (eigene Tabelle).
Ergebnis: sim/qi_spulen/faelle/<name>.json (+ wout); fertige Faelle werden uebersprungen.
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
QUELLE = ROOT / "sim" / "constellaration" / "qi" / "proxima_spulen_dje"
AUS = ROOT / "sim" / "qi_spulen"
# Eigener Spulensatz (2026-11-07, Kette K3): QI_SATZ=<Ordner mit boundary.json + spulen.json> (stellarator/spulen_satz.py);
# Ergebnisse dann in <Ordner>/frei/ statt sim/qi_spulen. Ohne QI_SATZ unveraendert Proxima DjLe3eL6.
if os.environ.get("QI_SATZ"):
    QUELLE = (ROOT / os.environ["QI_SATZ"]).resolve()
    AUS = QUELLE / "frei"
S = [0.02, 0.05, 0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0]
NR, NZ = 201, 201          # Gitter R, Z (Abstand ~1,7 mm bzw. ~2,9 mm im Datensatzmassstab)
RAND_A = 0.45              # Gitterrand: Plasmaausdehnung + 0,45 a
THREADS = 2


# ---------------------------------------------------------------- Geometrie
def rand():
    from constellaration.geometry import surface_rz_fourier as srf
    return srf.SurfaceRZFourier.model_validate(json.loads((QUELLE / "boundary.json").read_text()))


def rz(rc, zs, xm, xn, th, ze):
    """R, Z einer VMEC-Flaeche (rmnc, zmns mit xm, xn inkl. nfp) auf Gitter th x ze."""
    a = np.multiply.outer(th, xm)[:, None, :] - np.multiply.outer(ze, xn)[None, :, :]
    return (np.cos(a) * rc).sum(-1), (np.sin(a) * zs).sum(-1)


def rand_rz(b, th, ze):
    m = np.arange(b.r_cos.shape[0]); n = np.arange(-(b.r_cos.shape[1] // 2), b.r_cos.shape[1] // 2 + 1)
    M, N = np.meshgrid(m, n, indexing="ij")
    return rz(np.asarray(b.r_cos).ravel(), np.asarray(b.z_sin).ravel(), M.ravel(), N.ravel() * b.n_field_periods, th, ze)


def basis_kurven(nq=400, vorzeichen=-1):
    from simsopt.geo import CurveXYZFourier
    if (QUELLE / "spulen.json").exists():                        # eigener Satz (simsopt-Basiskurven, Datensatzmassstab)
        d = json.loads((QUELLE / "spulen.json").read_text()); out = []
        for x in d["basis_x"]:
            k = CurveXYZFourier(max(nq, d["nq"]), d["order"]); k.x = np.asarray(x, float); out.append(k)
        return out, np.asarray(d["currents"], float), int(d["nfp"])
    c = json.loads((QUELLE / "coilset.json").read_text()); N = 7
    out = []
    for i in range(len(c["currents"])):
        k = CurveXYZFourier(nq, N); dofs = []
        for xyz in ("coil_x_n", "coil_y_n", "coil_z_n"):
            a = np.asarray(c[xyz][i])
            dofs.append(a[N])
            for n in range(1, N + 1):
                dofs += [vorzeichen * a[N - n], a[N + n]]
        k.x = np.asarray(dofs, float); out.append(k)
    return out, np.asarray(c["currents"], float), int(c["n_field_periods"])


def verschoben(kurve, spec):
    """Basisspule starr verschieben/verdrehen. spec: dict mit d=[dx,dy,dz] (m) und/oder rot=[achse 'r'|'z'|'t', winkel rad]
    (Drehung um den Spulenschwerpunkt; 'r' radial, 't' toroidal, 'z' senkrecht, bezogen auf die Lage des Schwerpunkts)."""
    from simsopt.geo import CurveXYZFourier
    g = kurve.gamma(); c0 = g.mean(0)
    ph = np.arctan2(c0[1], c0[0]); er = np.array([np.cos(ph), np.sin(ph), 0]); et = np.array([-np.sin(ph), np.cos(ph), 0]); ez = np.array([0, 0, 1.])
    d = np.zeros(3)
    if "d_rtz" in spec:
        d = spec["d_rtz"][0] * er + spec["d_rtz"][1] * et + spec["d_rtz"][2] * ez
    R = np.eye(3)
    if "rot" in spec:
        ach = {"r": er, "t": et, "z": ez}[spec["rot"][0]]; w = spec["rot"][1]
        K = np.array([[0, -ach[2], ach[1]], [ach[2], 0, -ach[0]], [-ach[1], ach[0], 0]])
        R = np.eye(3) + np.sin(w) * K + (1 - np.cos(w)) * K @ K
    # Fourier-Koeffizienten sind linear in den Punkten: neue Kurve = R (x - c0) + c0 + d, c0 nur im Mittelwert
    N = kurve.order; x = kurve.x.reshape(3, 2 * N + 1)
    neu = R @ x
    neu[:, 0] += (np.eye(3) - R) @ c0 + d
    k = CurveXYZFourier(len(kurve.quadpoints), N); k.x = neu.ravel(); return k


def spulen(basis, I, nfp):
    from simsopt.field import Current, coils_via_symmetries
    return coils_via_symmetries(basis, [Current(float(x)) for x in I], nfp, True)


# ---------------------------------------------------------------- Feldtabelle
def gitter(b):
    from constellaration.geometry import surface_rz_fourier as srf
    th = np.linspace(0, 2 * np.pi, 200, endpoint=False); ze = np.linspace(0, 2 * np.pi / b.n_field_periods, 48, endpoint=False)
    R, Z = rand_rz(b, th, ze); a = srf.evaluate_minor_radius(b); m = RAND_A * a
    return dict(r_min=float(R.min() - m), r_max=float(R.max() + m), z_min=float(Z.min() - m), z_max=float(Z.max() + m), a=float(a))


def tabelle(name="basis", spec=None, nzeta=None):
    """Feld je Spulengruppe fuer 1 A. spec: {'spule': i, ...} verschiebt Basisspule i (alle 8 Symmetrie-Kopien)."""
    from simsopt.field import BiotSavart, Current, coils_via_symmetries
    from constellaration.mhd import vmec_settings as vs
    datei = AUS / "tabellen" / f"{name}.npz"
    if datei.exists():
        print("Tabelle vorhanden:", datei); return datei
    datei.parent.mkdir(parents=True, exist_ok=True)
    b = rand(); nzeta = nzeta or vs.vmec_settings_high_fidelity_fixed_boundary(b).n_toroidal_grid_points
    basis, I, nfp = basis_kurven()
    if spec:
        basis[spec["spule"]] = verschoben(basis[spec["spule"]], spec)
    gi = gitter(b)
    r = np.linspace(gi["r_min"], gi["r_max"], NR); z = np.linspace(gi["z_min"], gi["z_max"], NZ)
    ph = 2 * np.pi / nfp * np.arange(nzeta) / nzeta
    P, Zg, Rg = np.meshgrid(ph, z, r, indexing="ij")          # Reihenfolge (k, jz, ir) wie mgrid_provider
    xyz = np.ascontiguousarray(np.stack([Rg * np.cos(P), Rg * np.sin(P), Zg], -1).reshape(-1, 3))
    c, s = np.cos(P.ravel()), np.sin(P.ravel()); del Rg, Zg
    # vorbelegte Felder statt Listen (2026-11-07: 10 Gruppen x nzeta 100 sprengten mit Liste + np.array-Kopie den 6-GB-Scope)
    br, bp, bz = (np.empty((len(basis), len(xyz))) for _ in range(3))
    for g in range(len(basis)):
        sp = coils_via_symmetries([basis[g]], [Current(1.0)], nfp, True)
        bs = BiotSavart(sp); bs.set_points(xyz); B = bs.B()
        br[g] = B[:, 0] * c + B[:, 1] * s; bp[g] = -B[:, 0] * s + B[:, 1] * c; bz[g] = B[:, 2]
        del bs, B, sp
        print("Gruppe", g, "fertig", flush=True)
    del xyz, c, s
    np.savez(datei, b_r=br, b_p=bp, b_z=bz, r=r, z=z, phi=ph, nfp=nfp, nzeta=nzeta,
             gamma=np.array([k.gamma() for k in basis]), spec=json.dumps(spec or {}), **{k: v for k, v in gi.items()})
    return datei


def tabelle_laden(name):
    import vmecpp
    t = np.load(AUS / "tabellen" / f"{name}.npz")
    p = vmecpp.MakegridParameters(normalize_by_currents=True, assume_stellarator_symmetry=True, number_of_field_periods=int(t["nfp"]),
                                  r_grid_minimum=float(t["r"][0]), r_grid_maximum=float(t["r"][-1]), number_of_r_grid_points=len(t["r"]),
                                  z_grid_minimum=float(t["z"][0]), z_grid_maximum=float(t["z"][-1]), number_of_z_grid_points=len(t["z"]),
                                  number_of_phi_grid_points=int(t["nzeta"]))
    return vmecpp.MagneticFieldResponseTable(parameters=p, b_r=np.ascontiguousarray(t["b_r"]), b_p=np.ascontiguousarray(t["b_p"]),
                                             b_z=np.ascontiguousarray(t["b_z"])), t


def kalibrierung():
    """k: gemeinsamer Stromfaktor, damit der Spulenfluss durch den Soll-Querschnitt (phi=0) = phiedge (offiziell)."""
    datei = AUS / "kalibrierung.json"
    if datei.exists():
        return json.loads(datei.read_text())
    from matplotlib.path import Path as MPath
    from simsopt.field import BiotSavart
    from constellaration.mhd import ideal_mhd_parameters as imp
    b = rand(); basis, I, nfp = basis_kurven(); bs = BiotSavart(spulen(basis, I, nfp))
    th = np.linspace(0, 2 * np.pi, 2000, endpoint=False); R, Z = rand_rz(b, th, np.array([0.0])); R, Z = R[:, 0], Z[:, 0]
    n = 600; rr = np.linspace(R.min(), R.max(), n); zz = np.linspace(Z.min(), Z.max(), n); RR, ZZ = np.meshgrid(rr, zz)
    innen = MPath(np.c_[R, Z]).contains_points(np.c_[RR.ravel(), ZZ.ravel()])
    pts = np.c_[RR.ravel()[innen], np.zeros(innen.sum()), ZZ.ravel()[innen]]
    bs.set_points(np.ascontiguousarray(pts)); Bphi = bs.B()[:, 1]
    fluss = float(Bphi.sum() * (rr[1] - rr[0]) * (zz[1] - zz[0]))
    from simsopt.field import Current, coils_via_symmetries
    # Fluss je Gruppe fuer 1 A (fuer phiedge = 'fluss'), gemittelt ueber 12 Schnitte einer Periode: eine Gruppe allein hat
    # auf dem Soll-Rand keine Flussflaeche, ihr Fluss haengt vom Schnitt ab; das Mittel entspricht dem Volumenmittel von B_phi
    fg = np.zeros(len(basis)); fs = []
    for ph in 2 * np.pi / nfp * np.arange(12) / 12:
        R1, Z1 = rand_rz(b, th, np.array([ph])); R1, Z1 = R1[:, 0], Z1[:, 0]
        r1 = np.linspace(R1.min(), R1.max(), 400); z1 = np.linspace(Z1.min(), Z1.max(), 400); RR1, ZZ1 = np.meshgrid(r1, z1)
        inn = MPath(np.c_[R1, Z1]).contains_points(np.c_[RR1.ravel(), ZZ1.ravel()]); dA = (r1[1] - r1[0]) * (z1[1] - z1[0])
        pp = np.c_[RR1.ravel()[inn] * np.cos(ph), RR1.ravel()[inn] * np.sin(ph), ZZ1.ravel()[inn]]
        for g in range(len(basis)):
            bg = BiotSavart(coils_via_symmetries([basis[g]], [Current(1.0)], nfp, True)); bg.set_points(np.ascontiguousarray(pp)); B = bg.B()
            fg[g] += float((-B[:, 0] * np.sin(ph) + B[:, 1] * np.cos(ph)).sum() * dA) / 12
        bs.set_points(np.ascontiguousarray(pp)); B = bs.B(); fs.append(float((-B[:, 0] * np.sin(ph) + B[:, 1] * np.cos(ph)).sum() * dA))
    fg = fg.tolist()
    phiedge = float(imp.boundary_to_ideal_mhd_parameters(b).boundary_toroidal_flux)
    # Kontrolle Feldfehler auf dem Soll-Rand (wie proxima_spulen: |B.n|/|B|)
    from simsopt.geo import SurfaceRZFourier as SS
    s = SS(nfp=nfp, stellsym=True, mpol=b.r_cos.shape[0] - 1, ntor=b.r_cos.shape[1] // 2, quadpoints_phi=np.linspace(0, 1, 128, endpoint=False),
           quadpoints_theta=np.linspace(0, 1, 64, endpoint=False))
    for m in range(b.r_cos.shape[0]):
        for nn in range(-(b.r_cos.shape[1] // 2), b.r_cos.shape[1] // 2 + 1):
            if m == 0 and nn < 0:
                continue
            s.set_rc(m, nn, float(b.r_cos[m, nn + b.r_cos.shape[1] // 2])); s.set_zs(m, nn, float(b.z_sin[m, nn + b.r_cos.shape[1] // 2]))
    bs.set_points(s.gamma().reshape(-1, 3)); B = bs.B().reshape(s.gamma().shape)
    bn = np.abs((B * s.unitnormal()).sum(2)) / np.linalg.norm(B, axis=2)
    k = {"phiedge": phiedge, "fluss_spulen_Soll_A": fluss, "fluss_je_gruppe_1A": fg, "fluss_gesamt_je_schnitt": fs, "k": phiedge / fluss, "stroeme_proxima_A": I.tolist(),
         "stroeme_kalibriert_A": (I * phiedge / fluss).tolist(), "Bn_rel_mittel": float(bn.mean()), "Bn_rel_max": float(bn.max()),
         "B_mittel_Rand_T_kalibriert": float(np.linalg.norm(B, axis=2).mean() * phiedge / fluss)}
    AUS.mkdir(parents=True, exist_ok=True); datei.write_text(json.dumps(k, indent=1)); print(json.dumps(k, indent=1))
    return k


def pruefe_interpolation(name="basis"):
    """Bilineare Interpolation der Tabelle (wie VMEC++) gegen direktes Biot-Savart auf dem Soll-Rand."""
    from simsopt.field import BiotSavart
    _, t = tabelle_laden(name); b = rand(); basis, I, nfp = basis_kurven(); bs = BiotSavart(spulen(basis, I, nfp))
    th = np.linspace(0, 2 * np.pi, 120, endpoint=False); R, Z = rand_rz(b, th, t["phi"])
    r, z = t["r"], t["z"]; dr, dz = r[1] - r[0], z[1] - z[0]
    Bt = (t["b_r"] * I[:, None]).sum(0), (t["b_p"] * I[:, None]).sum(0), (t["b_z"] * I[:, None]).sum(0)
    fehler = []
    for k in range(len(t["phi"])):
        ir = np.floor((R[:, k] - r[0]) / dr).astype(int); jz = np.floor((Z[:, k] - z[0]) / dz).astype(int)
        p = (R[:, k] - r[ir]) / dr; q = (Z[:, k] - z[jz]) / dz
        idx = lambda j, i: (k * len(z) + j) * len(r) + i
        Bi = [(1 - p) * (1 - q) * c[idx(jz, ir)] + p * (1 - q) * c[idx(jz, ir + 1)] + (1 - p) * q * c[idx(jz + 1, ir)] + p * q * c[idx(jz + 1, ir + 1)] for c in Bt]
        ph = t["phi"][k]; pts = np.c_[R[:, k] * np.cos(ph), R[:, k] * np.sin(ph), Z[:, k]]
        bs.set_points(np.ascontiguousarray(pts)); B = bs.B()
        Bd = [B[:, 0] * np.cos(ph) + B[:, 1] * np.sin(ph), -B[:, 0] * np.sin(ph) + B[:, 1] * np.cos(ph), B[:, 2]]
        fehler.append(np.linalg.norm(np.array(Bi) - np.array(Bd), axis=0) / np.linalg.norm(np.array(Bd), axis=0))
    f = np.concatenate(fehler); print(f"Interpolationsfehler relativ: mittel {f.mean():.2e}, max {f.max():.2e}"); return float(f.mean()), float(f.max())


# ---------------------------------------------------------------- Faelle
def faelle():
    ng = len(basis_kurven(nq=8)[0]) if os.environ.get("QI_SATZ") else 5
    F = {"basis": {"strom": [1] * ng}, "fest": {"strom": [1] * ng, "fest": True}}  # fest = offizielle Rechnung ohne Spulen
    # (a) alle gemeinsam: mit phiedge mitskaliert (muss identisch sein) und bei festem phiedge (Plasmagrenze wandert)
    F["a_alle_1.05_fluss_mit"] = {"strom": [1.05] * 5, "phiedge": 1.05}
    for f in (0.95, 0.99, 1.01, 1.05):
        F[f"a_alle_{f}"] = {"strom": [f] * 5}
    # (b) je Spulengruppe (Basisspule + 7 Symmetrie-Kopien); Fluss folgt dem Spulenfluss (gleiche Plasmamenge je Feld)
    for g in range(ng):
        for f in (0.95, 0.99, 1.01, 1.05):
            v = [1.0] * ng; v[g] = f; F[f"b_S{g + 1}_{f}"] = {"strom": v, "phiedge": "fluss"}
    # (C) Verschiebung/Verdrehung je Basisspule (alle 8 Kopien), W7-X-Toleranz 3-5 mm in der Anlage
    return F


def fall_tabelle(spec):
    """Tabellenname; Tabelle wird bei Bedarf gerechnet (Verschiebung 'versatz' bzw. Toroidalpunkte 'nzeta')."""
    nz = spec.get("nzeta"); v = spec.get("versatz")
    name = spec.get("tabelle") or ("basis" if not v else "v_" + "_".join(f"{k}{v[k]}" for k in sorted(v)).replace(" ", "").replace("[", "").replace("]", "").replace(",", "x"))
    if nz:
        name += f"_nz{nz}"
    if not (AUS / "tabellen" / f"{name}.npz").exists():
        tabelle(name, v, nz)
    return name


def eins(name):
    F = faelle()
    if name not in F:
        F.update(json.loads((AUS / "faelle_zusatz.json").read_text()) if (AUS / "faelle_zusatz.json").exists() else {})
    spec = F[name]; ziel = AUS / "faelle" / f"{name}.json"
    if ziel.exists():
        print("fertig, uebersprungen:", name); return
    ziel.parent.mkdir(parents=True, exist_ok=True)
    import vmecpp
    from constellaration import forward_model
    from constellaration.boozer import boozer as bm
    from constellaration.mhd import geometry_utils, vmec_utils
    from constellaration.omnigeneity import qi
    from constellaration.geometry import surface_rz_fourier as srf
    sys.path.insert(0, str(ROOT))
    from stellarator.qi_karte import ausschnitt
    kal = kalibrierung(); tab, t = tabelle_laden(fall_tabelle(spec))
    extcur = np.asarray(kal["stroeme_kalibriert_A"]) * np.asarray(spec["strom"], float)
    info = {}

    def run_fb(boundary, mhd_parameters, vmec_settings):
        for k_, a_ in (("nzeta", "n_toroidal_grid_points"), ("ntor", "max_toroidal_mode"), ("mpol", "n_poloidal_modes"), ("ntheta", "n_poloidal_grid_points")):
            if k_ in spec:
                setattr(vmec_settings, a_, int(spec[k_]))
        ind = vmec_utils.build_vmecpp_indata(mhd_parameters=mhd_parameters, boundary=boundary, vmec_settings=vmec_settings)
        info["aufloesung"] = dict(mpol=int(ind.mpol), ntor=int(ind.ntor), ntheta=int(ind.ntheta), nzeta=int(ind.nzeta))
        if not spec.get("fest"):
            ind.lfreeb = True; ind.extcur = extcur; ind.nvacskip = int(spec.get("nvacskip", 6)); ind.mgrid_file = "NONE"
        pf = spec.get("phiedge", 1.0)
        if pf == "fluss":                                         # Fluss folgt dem Spulenfluss durch den Soll-Querschnitt
            fg = np.asarray(kal["fluss_je_gruppe_1A"]); I0 = np.asarray(kal["stroeme_kalibriert_A"])
            pf = float(fg @ extcur / (fg @ I0))
        info["phiedge_faktor"] = float(pf)
        ind.phiedge = ind.phiedge * float(pf)
        if "ftol" in spec:
            ind.ftol_array = np.array(spec["ftol"], float)
        t0 = time.time()
        if spec.get("trotzdem"):                                  # Ergebnis auch ohne erreichte Toleranz (Restkraft wird gespeichert)
            ind.return_outputs_even_if_not_converged = True
        if "niter" in spec:
            ind.niter_array = np.array(spec["niter"], int)
        out = vmecpp.run(ind, magnetic_field=None if spec.get("fest") else tab, max_threads=THREADS, verbose=bool(spec.get("verbose", False)))
        info.update(sek_vmec=time.time() - t0, phiedge=float(ind.phiedge), extcur=extcur.tolist(), fsqr=float(out.wout.fsqr),
                    fsqz=float(out.wout.fsqz), fsql=float(out.wout.fsql), ier=int(out.wout.ier_flag), itfsq=int(out.wout.itfsq))
        return vmec_utils.vmecppwout_from_wout(out.wout)

    vmec_utils.run_vmec = run_fb                      # forward_model ruft vmec_utils.run_vmec ueber das Modul auf (fest: nur Aufloesung)
    b = rand(); t0 = time.time()
    try:
        m, w = forward_model.forward_model(b, settings=forward_model.ConstellarationSettings.default_high_fidelity())
    except Exception as e:
        ziel.write_text(json.dumps({"name": name, "spec": spec, "fehler": f"{type(e).__name__}: {str(e)[:400]}", **info}, indent=1))
        print("FEHLER", name, e, flush=True); return
    (AUS / "wout").mkdir(exist_ok=True); w.save(AUS / "wout" / f"{name}.nc")
    # Plasmagrenze frei gegen Soll
    th = np.linspace(0, 2 * np.pi, 256, endpoint=False); ze = np.linspace(0, 2 * np.pi / b.n_field_periods, 24, endpoint=False)
    Rf, Zf = rz(w.rmnc[:, -1], w.zmns[:, -1], w.xm, w.xn, th, ze)
    th2 = np.linspace(0, 2 * np.pi, 4000, endpoint=False); Rs, Zs = rand_rz(b, th2, ze)
    from matplotlib.path import Path as MPath
    d = np.empty_like(Rf)
    for k in range(len(ze)):
        dd = np.hypot(Rf[:, k, None] - Rs[None, :, k], Zf[:, k, None] - Zs[None, :, k]).min(1)
        aussen = ~MPath(np.c_[Rs[:, k], Zs[:, k]]).contains_points(np.c_[Rf[:, k], Zf[:, k]])
        d[:, k] = np.where(aussen, dd, -dd)
    a = srf.evaluate_minor_radius(b)
    # Dreieckigkeit der freien Grenze (forward_model nimmt die Eingabe-Grenze)
    m_pol = int(w.xm.max()); nn = np.unique(np.abs(w.xn)) // b.n_field_periods; nt = int(nn.max())
    rc = np.zeros((m_pol + 1, 2 * nt + 1)); zsn = np.zeros_like(rc)
    for c, (mm, n) in enumerate(zip(w.xm.astype(int), (w.xn // b.n_field_periods).astype(int))):
        rc[mm, n + nt] = w.rmnc[c, -1]; zsn[mm, n + nt] = w.zmns[c, -1]
    bf = srf.SurfaceRZFourier(r_cos=rc, z_sin=zsn, n_field_periods=b.n_field_periods, is_stellarator_symmetric=True)
    tri_frei = float(geometry_utils.average_triangularity(surface=bf))
    # QI auf 14 Flaechen wie qi_karte
    qs = qi.QISettings()
    bz = bm.run_boozer(w, bm.create_boozer_settings_from_equilibrium_resolution(w, bm.BoozerPresetSettings(normalized_toroidal_flux=S)))
    qf, fehl = [], {}
    for js in range(bz.n_boozer_flux_surfaces):
        try:
            qf.append(float(np.sum(qi.quasi_isodynamicity_residual(ausschnitt(bz, js), qs).residuals ** 2)))
        except Exception as e:
            qf.append(None); fehl[js] = str(e)[:120]
    np.savez_compressed(AUS / "faelle" / f"{name}_rand.npz", R=Rf, Z=Zf, d=d, th=th, ze=ze)
    j = {"name": name, "spec": spec, **info, "qi": m.qi, "metriken": m.model_dump(), "dreieckigkeit_freie_grenze": tri_frei,
         "rand_abstand_mittel_a": float(np.abs(d).mean() / a), "rand_abstand_max_a": float(np.abs(d).max() / a),
         "rand_abstand_signiert_mittel_a": float(d.mean() / a), "a_soll": float(a), "volumen": float(w.volume_p),
         "iotaf": [float(x) for x in w.iotaf], "s_qi": [float(x) for x in bz.boozer_normalized_toroidal_flux], "qi_flaeche": qf,
         "qi_fehler": fehl, "sek_gesamt": time.time() - t0}
    ziel.write_text(json.dumps(j, indent=1))
    print(json.dumps({k: j[k] for k in ("name", "qi", "rand_abstand_mittel_a", "rand_abstand_max_a", "fsqr", "sek_vmec", "sek_gesamt")}), flush=True)


# ---------------------------------------------------------------- Weg (ii): feste Flaechen + |B| der Spulen (Stoerungsmodell)
class Modell2:
    """Boozer-Koordinaten des festen Gleichgewichts (offizielle Rechnung) behalten; auf jeder Flaeche |B| aus Biot-Savart der
    Spulen einsetzen, nach den Boozer-Moden (xm_b, xn_b) zurueck zerlegen (kleinste Quadrate) und qi.quasi_isodynamicity_residual
    rechnen. Vernachlaessigt: dass Feldlinien des Spulenfelds die Flaeche um Bn verlassen (Flaechenlage und Winkel bleiben die des
    festen Gleichgewichts). Feld je Spulengruppe fuer 1 A wird einmal gerechnet, danach ist QI(I) eine Sache von Sekunden."""

    def __init__(self, wout="fest", s=(0.5, 0.75, 1.0), nth=160, nph=64):   # Boozer-Moden bis m = 59, n = 19 je Periode
        import vmecpp
        from constellaration.boozer import boozer as bm
        from constellaration.mhd import vmec_utils
        from simsopt.field import BiotSavart, Current, coils_via_symmetries
        self.w = vmec_utils.vmecppwout_from_wout(vmecpp.VmecWOut.from_wout_file(AUS / "wout" / f"{wout}.nc"))
        self.bz = bm.run_boozer(self.w, bm.create_boozer_settings_from_equilibrium_resolution(self.w, bm.BoozerPresetSettings(normalized_toroidal_flux=list(s))))
        bz = self.bz; nfp = bz.n_field_periods; self.nfp = nfp
        th = np.linspace(0, 2 * np.pi, nth, endpoint=False); ph = np.linspace(0, 2 * np.pi / nfp, nph, endpoint=False)
        TH, PH = np.meshgrid(th, ph, indexing="ij"); self.TH, self.PH = TH.ravel(), PH.ravel()
        ang = bz.xm_b[:, None] * self.TH[None] - bz.xn_b[:, None] * self.PH[None]
        self.C = np.cos(ang).T                                    # Punkte x Moden
        self.pinv = np.linalg.pinv(self.C)
        # Vorzeichen von nu wie in residuen_ort: Punkt muss auf der VMEC-Flaeche liegen (Pruefung auf der Randflaeche)
        self.punkte = []
        for js in range(bz.n_boozer_flux_surfaces):
            R = self.C @ bz.rmnc_b[:, js]; Z = np.sin(ang).T @ bz.zmns_b[:, js]; nu = np.sin(ang).T @ bz.numns_b[:, js]
            self.punkte.append((R, Z, nu))
        self.vz = self._nu_vorzeichen()
        self.B0 = []                                              # Feld der VMEC-Rechnung in Boozer-Moden (Kontrolle)
        self.Bg = {}
        self.kurven, self.I0, _ = basis_kurven(); kal = kalibrierung(); self.I0 = np.asarray(kal["stroeme_kalibriert_A"])
        self.xyz = []
        for R, Z, nu in self.punkte:
            P = self.PH + self.vz * nu; self.xyz.append(np.c_[R * np.cos(P), R * np.sin(P), Z])
        self.feld_gruppen()

    def _nu_vorzeichen(self):
        w = self.w; R, Z, nu = self.punkte[-1]; th = np.linspace(0, 2 * np.pi, 3000, endpoint=False); f = {}
        for vz in (-1, 1):
            idx = np.arange(0, len(R), max(1, len(R) // 40))
            ph = self.PH[idx] + vz * nu[idx]; Rv, Zv = rz(w.rmnc[:, -1], w.zmns[:, -1], w.xm, w.xn, th, ph)
            f[vz] = float(np.max([np.hypot(Rv[:, i] - R[j], Zv[:, i] - Z[j]).min() for i, j in enumerate(idx)]))
        self.nu_fehler = f
        return min(f, key=f.get)

    def feld_gruppen(self, kurven=None):
        """B-Vektor je Gruppe fuer 1 A auf allen Flaechenpunkten (Liste je Flaeche: Gruppe x Punkte x 3)."""
        from simsopt.field import BiotSavart, Current, coils_via_symmetries
        kurven = kurven or self.kurven; out = []
        for X in self.xyz:
            Bg = []
            for k in kurven:
                bs = BiotSavart(coils_via_symmetries([k], [Current(1.0)], self.nfp, True)); bs.set_points(np.ascontiguousarray(X)); Bg.append(bs.B())
            out.append(np.array(Bg))
        self.Bg = out
        return out

    def qi(self, faktoren=None, Bg=None, vmec_feld=False):
        """QI je Flaeche fuer Stroeme I0*faktoren (vmec_feld=True: |B| der VMEC-Rechnung selbst, Kontrolle des Verfahrens)."""
        from constellaration.omnigeneity import qi
        from stellarator.qi_karte import ausschnitt
        I = self.I0 * (np.ones(len(self.I0)) if faktoren is None else np.asarray(faktoren, float)); Bg = self.Bg if Bg is None else Bg
        bm_neu = self.bz.bmnc_b.copy(); rest = []
        for js in range(self.bz.n_boozer_flux_surfaces):
            if vmec_feld:
                modb = self.C @ self.bz.bmnc_b[:, js]
            else:
                modb = np.linalg.norm(np.tensordot(I, Bg[js], 1), axis=1)
            c = self.pinv @ modb; bm_neu[:, js] = c; rest.append(float(np.abs(self.C @ c - modb).max() / modb.mean()))
        bz2 = self.bz.model_copy(update={"bmnc_b": bm_neu}); qs = qi.QISettings()
        return [float(np.sum(qi.quasi_isodynamicity_residual(ausschnitt(bz2, js), qs).residuals ** 2)) for js in range(self.bz.n_boozer_flux_surfaces)], rest


def modell2_basis():
    """Kontrollen und Grundwerte von Weg (ii)."""
    sys.path.insert(0, str(ROOT))
    M = Modell2(); s = [float(x) for x in M.bz.boozer_normalized_toroidal_flux]
    q_vmec, r_vmec = M.qi(vmec_feld=True); q_sp, r_sp = M.qi()
    # Feld der Spulen gegen Feld der VMEC-Rechnung auf dem Rand (relativ)
    modb_v = M.C @ M.bz.bmnc_b[:, -1]; modb_s = np.linalg.norm(np.tensordot(M.I0, M.Bg[-1], 1), axis=1)
    j = {"s": s, "nu_vorzeichen": M.vz, "nu_lagefehler": M.nu_fehler, "qi_vmec_feld_refit": q_vmec, "refit_rest_vmec": r_vmec,
         "qi_spulenfeld": q_sp, "refit_rest_spulen": r_sp, "B_spulen_zu_vmec_rand_mittel": float((modb_s / modb_v).mean()),
         "B_abw_rel_rand_rms_nach_mittelwert": float(np.std(modb_s / modb_v / (modb_s / modb_v).mean()))}
    (AUS / "modell2_basis.json").write_text(json.dumps(j, indent=1)); print(json.dumps(j, indent=1))
    return M


def spiegel(M, faktoren):
    """Spiegelverhaeltnis (Bmax - Bmin)/(Bmax + Bmin) je Flaeche fuer das Spulenfeld auf den festen Flaechen."""
    I = M.I0 * np.asarray(faktoren, float)
    out = []
    for Bg in M.Bg:
        b = np.linalg.norm(np.tensordot(I, Bg, 1), axis=1); out.append(float((b.max() - b.min()) / (b.max() + b.min())))
    return out


def modell2_strom():
    """Teil B mit Weg (ii): (a) alle Stroeme gemeinsam, (b) je Spulengruppe +-1 %, +-5 %, (c) Optimierung der Stromverhaeltnisse."""
    sys.path.insert(0, str(ROOT))
    datei = AUS / "modell2_strom.json"
    E = json.loads(datei.read_text()) if datei.exists() else {}
    t0 = time.time(); M = Modell2(); print("Modell bereit", f"{time.time() - t0:.0f} s", flush=True)
    s = [float(x) for x in M.bz.boozer_normalized_toroidal_flux]

    def bewerte(name, fk):
        if name in E:
            return E[name]
        t1 = time.time(); q, rest = M.qi(fk)
        E[name] = {"faktoren": list(map(float, fk)), "qi": q, "spiegel": spiegel(M, fk), "refit_rest": rest, "sek": time.time() - t1}
        datei.write_text(json.dumps(E, indent=1)); print(name, q, f"{time.time() - t1:.0f} s", flush=True)
        return E[name]
    bewerte("basis", [1.0] * 5)
    for f in (0.95, 1.05):
        bewerte(f"a_alle_{f}", [f] * 5)
    for g in range(5):
        for f in (0.95, 0.99, 1.01, 1.05):
            v = [1.0] * 5; v[g] = f; bewerte(f"b_S{g + 1}_{f}", v)
    # (c) Stromverhaeltnisse: S1 fest, S2..S5 frei (Gesamtskala aendert QI nicht), Ziel QI am Rand; innen mitgeschrieben
    if "c_optimum" not in E:
        from scipy.optimize import minimize
        verlauf = []

        def ziel(x):
            fk = np.r_[1.0, x]; q, _ = M.qi(fk); verlauf.append([*map(float, fk), *q]); print("opt", np.round(fk, 4), q, flush=True)
            return q[-1]
        # Schranken 0,95..1,05: Weg (ii) ist nur bis +-5 % gegen Weg (i) geprueft; ohne Schranken lief Nelder-Mead zu Faktoren
        # bis 2,2 und negativen Stroemen (c_frei_ohne_schranken, physikalisch unbrauchbar)
        r = minimize(ziel, np.ones(4), method="L-BFGS-B", bounds=[(0.95, 1.05)] * 4, options=dict(eps=2e-3, maxfun=80))
        fk = np.r_[1.0, r.x]
        E["c_verlauf"] = verlauf; bewerte("c_optimum", fk); E["c_optimum"]["nfev"] = int(r.nfev); E["c_optimum"]["meldung"] = str(r.message)
        datei.write_text(json.dumps(E, indent=1))
    E["s"] = s; datei.write_text(json.dumps(E, indent=1)); print("FERTIG modell2_strom", f"{time.time() - t0:.0f} s")


MASSSTAB_M = 1.6989171455997287 * 10.102932590386631   # 1 Laengeneinheit des Datensatzes = 17,16 m Anlage (proxima_spulen, kopplung.L)


def modell2_lage(mm=5.0):
    """Teil C mit Weg (ii): Basisspule g (mit ihren 7 Symmetrie-Kopien) um mm (Anlage) verschieben (radial r, toroidal t, senkrecht z)
    bzw. um die Achsen r, t, z durch ihren Schwerpunkt drehen (Winkel so, dass der entfernteste Spulenpunkt sich um mm bewegt)."""
    sys.path.insert(0, str(ROOT))
    datei = AUS / "modell2_lage.json"
    E = json.loads(datei.read_text()) if datei.exists() else {}
    M = Modell2(); B0 = M.Bg; d = mm / 1000 / MASSSTAB_M
    if "basis" not in E:
        q, _ = M.qi(); E["basis"] = {"qi": q, "spiegel": spiegel(M, np.ones(5))}
    for g in range(5):
        k = M.kurven[g]; gam = k.gamma(); rmax = float(np.linalg.norm(gam - gam.mean(0), axis=1).max())
        for art in ("d_r", "d_t", "d_z", "rot_r", "rot_t", "rot_z"):
            for vz in (1, -1):
                name = f"S{g + 1}_{art}_{'+' if vz > 0 else '-'}{mm:g}mm"
                if name in E:
                    continue
                if art.startswith("d_"):
                    v = [0.0, 0.0, 0.0]; v["rtz".index(art[-1])] = vz * d; spec = {"d_rtz": v}
                else:
                    spec = {"rot": [art[-1], vz * d / rmax]}
                kn = verschoben(k, spec); verschiebung = float(np.linalg.norm(kn.gamma() - gam, axis=1).max() * MASSSTAB_M * 1000)
                Bg = []
                for js, X in enumerate(M.xyz):
                    from simsopt.field import BiotSavart, Current, coils_via_symmetries
                    bs = BiotSavart(coils_via_symmetries([kn], [Current(1.0)], M.nfp, True)); bs.set_points(np.ascontiguousarray(X))
                    B = B0[js].copy(); B[g] = bs.B(); Bg.append(B)
                q, _ = M.qi(Bg=Bg); M.Bg = Bg; sp = spiegel(M, np.ones(5)); M.Bg = B0
                E[name] = {"spule": g + 1, "art": art, "vorzeichen": vz, "qi": q, "spiegel": sp, "max_punktverschiebung_mm": verschiebung}
                datei.write_text(json.dumps(E, indent=1)); print(name, q, f"{verschiebung:.2f} mm", flush=True)
    print("FERTIG modell2_lage")


# ---------------------------------------------------------------- Feldlinien des reinen Spulenfelds (Poincare)
def poincare(n_linien=18, umlaeufe=300, schritte=128):
    """Feldlinien des Spulenfelds (kalibrierte Stroeme) ab phi = 0 auf der Aussenseite (Z = 0); Durchstosspunkte bei phi = 0
    (mod Periode) und phi = halbe Periode. Eigenes Runge-Kutta 4 mit phi als Laufvariable (dR/dphi = R B_R/B_phi,
    dZ/dphi = R B_Z/B_phi), direktes Biot-Savart (keine Interpolation), alle Linien gleichzeitig. Zeigt unabhaengig von VMEC++,
    ob das Spulenfeld am Rand geschlossene Flaechen oder Inseln hat."""
    datei = AUS / "poincare.npz"
    if datei.exists():
        return dict(np.load(datei))
    from simsopt.field import BiotSavart
    kal = kalibrierung(); b = rand(); basis, _, nfp = basis_kurven(); bs = BiotSavart(spulen(basis, np.asarray(kal["stroeme_kalibriert_A"]), nfp))
    gi = gitter(b); a = gi["a"]
    R0, _ = rand_rz(b, np.array([0.0]), np.array([0.0])); R0 = float(R0[0, 0])
    Rs = np.linspace(R0 - 0.7 * a, R0 + 0.12 * a, n_linien)

    def f(ph, y):
        R, Z = y[:n_linien], y[n_linien:]
        bs.set_points(np.ascontiguousarray(np.c_[R * np.cos(ph), R * np.sin(ph), Z])); B = bs.B()
        BR = B[:, 0] * np.cos(ph) + B[:, 1] * np.sin(ph); BP = -B[:, 0] * np.sin(ph) + B[:, 1] * np.cos(ph)
        return np.r_[R * BR / BP, R * B[:, 2] / BP]
    h = 2 * np.pi / nfp / schritte; y = np.r_[Rs, np.zeros(n_linien)]; ph = 0.0
    n_halb = umlaeufe * nfp * 2; ebene0, ebene1 = [], []; t0 = time.time()
    for k in range(n_halb):
        for _ in range(schritte // 2):
            k1 = f(ph, y); k2 = f(ph + h / 2, y + h / 2 * k1); k3 = f(ph + h / 2, y + h / 2 * k2); k4 = f(ph + h, y + h * k3)
            y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4); ph += h
            raus = (y[:n_linien] < gi["r_min"]) | (y[:n_linien] > gi["r_max"]) | (np.abs(y[n_linien:]) > gi["z_max"])
            y[:n_linien][raus] = np.nan; y[n_linien:][raus] = np.nan
        (ebene0 if k % 2 == 1 else ebene1).append(y.copy())
        if k % 400 == 0:
            print("Halbperiode", k, "von", n_halb, f"{time.time() - t0:.0f} s", flush=True)
    np.savez(datei, starts=Rs, a=a, R0_rand_aussen=R0, ebene0=np.array(ebene0), ebene1=np.array(ebene1), n=n_linien)
    return dict(np.load(datei))


def poincare_bild(vergleich=("fest", "k_n3000", "k_n12000")):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import vmecpp
    from constellaration.mhd import vmec_utils
    P = poincare(); b = rand(); nfp = b.n_field_periods
    fig, ax = plt.subplots(1, 2, figsize=(12, 6.5), constrained_layout=True)
    th = np.linspace(0, 2 * np.pi, 400)
    farbe = {"fest": "k", "k_n3000": "#2a9d8f", "k_n12000": "#c0392b", "basis": "#c0392b"}
    for j, (A, ph) in enumerate(zip(ax, (0.0, np.pi / nfp))):
        E = P["ebene0"] if j == 0 else P["ebene1"]; n = int(P["n"])
        for i in range(n):
            A.plot(E[:, i], E[:, n + i], ".", ms=0.8, color=plt.cm.viridis(i / n))
        Rs, Zs = rand_rz(b, th, np.array([ph])); A.plot(Rs[:, 0], Zs[:, 0], "--", color="gray", lw=1.2, label="Soll-Grenze (Datensatz)")
        for n in vergleich:
            f = AUS / "wout" / f"{n}.nc"
            if f.exists() and n != "fest":
                w = vmec_utils.vmecppwout_from_wout(vmecpp.VmecWOut.from_wout_file(f))
                Rv, Zv = rz(w.rmnc[:, -1], w.zmns[:, -1], w.xm, w.xn, th, np.array([ph])); A.plot(Rv[:, 0], Zv[:, 0], "-", color=farbe.get(n, "C3"), lw=1, label=f"freie Grenze VMEC++ ({n})")
        A.set_aspect("equal"); A.set_xlabel("R (Datensatzmaßstab, 1 = 17,2 m)"); A.set_ylabel("Z")
        A.set_title(f"Schnitt φ = {np.degrees(ph):.0f}°", fontsize=10); A.legend(fontsize=7, loc="lower left")
    fig.suptitle("Feldlinien des Spulenfelds (Punkte = Durchstoßpunkte, je Farbe eine Feldlinie) und Plasmagrenzen", fontsize=11)
    fig.savefig(AUS / "karte" / "poincare.png", dpi=120); plt.close(fig)


# ---------------------------------------------------------------- Karte QI + Spulen (Teil A2)
def residuen_ort(quelle):
    """Residuen am Rand (75 Feldlinien x 2000 Winkel) mit Ort im Raum, naechster Spule, Abstand und Kruemmung.
    quelle 'fest': |B| des festen Gleichgewichts (offiziell); 'spulen': |B| der Spulen auf denselben Boozer-Punkten (Weg ii)."""
    datei = AUS / "karte" / f"orte_{quelle}.npz"
    if datei.exists():
        return dict(np.load(datei))
    sys.path.insert(0, str(ROOT))
    from constellaration.omnigeneity import qi
    from scipy import interpolate
    from scipy.spatial import cKDTree
    M = Modell2(s=(1.0,)); bz = M.bz
    if quelle == "spulen":
        modb = np.linalg.norm(np.tensordot(M.I0, M.Bg[0], 1), axis=1); bm_neu = bz.bmnc_b.copy(); bm_neu[:, 0] = M.pinv @ modb
        bz = bz.model_copy(update={"bmnc_b": bm_neu})
    qs = qi.QISettings(); Res = qi.quasi_isodynamicity_residual(bz, qs).residuals[0] * np.sqrt(qs.n_output_toroidal_points * qs.n_field_lines)
    nfp = bz.n_field_periods; p0 = np.pi / nfp if bz.bmnc[1, 1] < 0 else 0.0
    phB = np.linspace(p0, p0 + 2 * np.pi / nfp, qs.n_output_toroidal_points)
    io = float(interpolate.UnivariateSpline(bz.normalized_toroidal_flux, bz.iota, k=1, s=0)(bz.boozer_normalized_toroidal_flux)[0])
    thB = np.linspace(-io * p0, -io * p0 + 2 * np.pi, qs.n_field_lines)[:, None] + io * phB[None, :]
    R, Z, nu = (np.empty_like(thB) for _ in range(3))
    for j in range(thB.shape[0]):                                # feldlinienweise (sonst Moden x 75 x 2000 = 2,8 GB je Feld)
        ang = bz.xm_b[:, None] * thB[j][None] - bz.xn_b[:, None] * phB[None]; c, s_ = np.cos(ang), np.sin(ang)
        R[j] = bz.rmnc_b[:, 0] @ c; Z[j] = bz.zmns_b[:, 0] @ s_; nu[j] = bz.numns_b[:, 0] @ s_
    PH = phB[None, :] + M.vz * nu
    xyz = np.stack([R * np.cos(PH), R * np.sin(PH), Z], -1)
    sp = spulen(M.kurven, M.I0, nfp)
    G = np.concatenate([c.curve.gamma() for c in sp]); K = np.concatenate([c.curve.kappa() for c in sp])
    nr = np.repeat(np.arange(len(sp)), len(M.kurven[0].quadpoints))
    d, i = cKDTree(G).query(xyz.reshape(-1, 3))
    out = dict(res=Res, thB=thB, phB=phB, nu=nu, R=R, Z=Z, phi=PH, xyz=xyz, abstand=d.reshape(R.shape), kruemmung=K[i].reshape(R.shape),
               spule=(nr[i] % len(M.kurven)).reshape(R.shape), iota=io, nfp=nfp, p0=p0, nu_vorzeichen=M.vz, nu_pruef_m=M.nu_fehler[M.vz],
               qi=float((Res ** 2).sum() / Res.size))
    datei.parent.mkdir(parents=True, exist_ok=True); np.savez_compressed(datei, **out); print(quelle, "QI", out["qi"], "nu", M.vz, M.nu_fehler)
    return out


def karte():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.stats import spearmanr
    import vmecpp
    from constellaration.mhd import vmec_utils
    O = AUS / "karte"; O.mkdir(parents=True, exist_ok=True)
    fr, fe = residuen_ort("spulen"), residuen_ort("fest")
    nfp = int(fr["nfp"]); a = rand(); from constellaration.geometry import surface_rz_fourier as srf
    a_m = srf.evaluate_minor_radius(a)
    basis, I, _ = basis_kurven(); sp = spulen(basis, I, nfp)
    farben = plt.cm.tab10(np.arange(5))
    # Lage der Spulen auf der Abwicklung: Spulenpunkte naeher als 1,6 a an der Flaeche, abgebildet auf (phi, theta_B) des naechsten Flaechenpunkts
    from scipy.spatial import cKDTree
    baum = cKDTree(fr["xyz"].reshape(-1, 3))
    phi_deg = np.degrees(np.mod(fr["phi"], 2 * np.pi / nfp)); thg = np.degrees(np.mod(fr["thB"], 2 * np.pi))
    spur = []
    for n, c in enumerate(sp):
        g = c.curve.gamma(); d, i = baum.query(g); ok = d < 1.6 * a_m
        spur.append((n % 5, phi_deg.ravel()[i], thg.ravel()[i], ok, d / a_m))
    def spuren(ax):
        for g, p, t, ok, _ in spur:
            p = np.where(ok, p, np.nan); t = np.where(ok, t, np.nan)
            sprung = np.r_[False, (np.abs(np.diff(p)) > 20) | (np.abs(np.diff(t)) > 90)]
            p[sprung] = np.nan
            ax.plot(p, t, "-", color=farben[g], lw=1.2)
    res2 = fr["res"] ** 2; delta = fr["res"] ** 2 - fe["res"] ** 2
    q = lambda x: np.percentile(np.abs(x), 99)
    fig, ax = plt.subplots(2, 2, figsize=(13, 8.5), constrained_layout=True)
    for A, wert, titel, cm, nrm in ((ax[0, 0], fr["res"], "Restfehler im Spulenfeld (B_QI − B, 1 = Muldentiefe)", "RdBu_r", (-q(fr["res"]), q(fr["res"]))),
                                    (ax[0, 1], fe["res"], "Restfehler festes Gleichgewicht (ohne Spulen, offiziell)", "RdBu_r", (-q(fr["res"]), q(fr["res"]))),
                                    (ax[1, 0], delta, "Zusatzfehler durch die Spulen: Quadrat mit − ohne Spulen", "PuOr_r", (-q(delta), q(delta))),
                                    (ax[1, 1], fr["abstand"] / a_m, "Abstand zur nächsten Spule (in kleinen Radien a)", "viridis_r", (0.8, 2.0))):
        im = A.scatter(phi_deg.ravel(), thg.ravel(), c=wert.ravel(), s=0.6, cmap=cm, vmin=nrm[0], vmax=nrm[1], rasterized=True)
        spuren(A); A.set_xlim(0, 360 / nfp); A.set_ylim(0, 360); A.set_title(titel, fontsize=10)
        A.set_xlabel("Toroidalwinkel φ (Grad, eine Periode = 90°)"); A.set_ylabel("Poloidalwinkel (Boozer, Grad)")
        fig.colorbar(im, ax=A, shrink=0.85)
    for g in range(5):
        ax[1, 1].plot([], [], color=farben[g], label=f"Spule S{g + 1}")
    ax[1, 1].legend(fontsize=7, loc="upper right")
    fig.suptitle("DjLe3eL6: QI-Fehler auf der abgewickelten Plasmaoberfläche, Linien = Spulen (wo sie näher als 1,6 a vorbeilaufen)", fontsize=11)
    fig.savefig(O / "abwicklung.png", dpi=110); plt.close(fig)
    # Verlauf ueber phi (eine Periode, 2 Grad Klassen)
    kl = np.arange(0, 90.01, 2.0); mitte = 0.5 * (kl[1:] + kl[:-1]); ix = np.digitize(phi_deg.ravel(), kl) - 1
    summe = lambda v: np.array([v.ravel()[ix == k].sum() for k in range(len(mitte))])
    mini = lambda v: np.array([v.ravel()[ix == k].min() for k in range(len(mitte))])
    mittel = lambda v: np.array([v.ravel()[ix == k].mean() for k in range(len(mitte))])
    N = res2.size
    fig, ax = plt.subplots(3, 1, figsize=(9, 8), sharex=True, constrained_layout=True)
    ax[0].plot(mitte, summe(res2) / N, "-", color="#8e6c8a", label="mit Spulen")
    ax[0].plot(mitte, summe(fe["res"] ** 2) / N, "--", color="gray", label="feste Soll-Grenze")
    ax[0].set_ylabel("QI-Beitrag je 2°"); ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3)
    ax[1].plot(mitte, mini(fr["abstand"]) / a_m, color="#1b6ca8", label="kleinster Abstand")
    ax[1].plot(mitte, mittel(fr["abstand"]) / a_m, ":", color="#1b6ca8", label="mittlerer Abstand")
    ax[1].set_ylabel("Spule–Plasma (a)"); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3)
    ax[2].plot(mitte, mittel(fr["kruemmung"]) * a_m, color="#c0392b", label="mittlere Krümmung der nächsten Spulenstelle")
    ax[2].set_ylabel("Krümmung × a"); ax[2].set_xlabel("Toroidalwinkel φ (Grad, eine Periode)"); ax[2].grid(alpha=0.3); ax[2].legend(fontsize=8)
    for g, k in enumerate(basis):
        c = k.gamma().mean(0); p = np.degrees(np.arctan2(c[1], c[0])) % 90
        for A in ax:
            A.axvline(p, color=farben[g], lw=0.8, alpha=0.7); A.axvline(90 - p, color=farben[g], lw=0.8, alpha=0.4, ls="--")
        ax[0].text(p, ax[0].get_ylim()[1] * 0.95, f"S{g + 1}", color=farben[g], fontsize=7, ha="center", va="top")
    fig.suptitle("Verlauf über den Toroidalwinkel; senkrechte Linien = Spulenmitte (durchgezogen) und Spiegelbild (gestrichelt)", fontsize=10)
    fig.savefig(O / "verlauf_phi.png", dpi=110); plt.close(fig)
    # 3D-Bild
    w = vmec_utils.vmecppwout_from_wout(vmecpp.VmecWOut.from_wout_file(AUS / "wout" / "fest.nc"))
    th = np.linspace(0, 2 * np.pi, 90); ze = np.linspace(0, 2 * np.pi, 361)
    Rv, Zv = rz(w.rmnc[:, -1], w.zmns[:, -1], w.xm, w.xn, th, ze)
    X = np.stack([Rv * np.cos(ze)[None], Rv * np.sin(ze)[None], Zv], -1)
    # Fehler aus einer Periode auf den ganzen Torus (Symmetrie: Drehung um 2pi/nfp und Spiegelung)
    P = fr["xyz"].reshape(-1, 3); W = res2.ravel(); alle_p, alle_w = [], []
    for k in range(nfp):
        c, s_ = np.cos(2 * np.pi * k / nfp), np.sin(2 * np.pi * k / nfp); Rm = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
        alle_p += [P @ Rm.T, (P * [1, -1, -1]) @ Rm.T]; alle_w += [W, W]
    i = cKDTree(np.concatenate(alle_p)).query(X.reshape(-1, 3))[1]; F = np.concatenate(alle_w)[i].reshape(Rv.shape)
    from mpl_toolkits.mplot3d import Axes3D  # noqa
    fig = plt.figure(figsize=(11, 8)); A = fig.add_subplot(111, projection="3d")
    nrm = plt.Normalize(0, np.percentile(F, 99))
    A.plot_surface(X[..., 0], X[..., 1], X[..., 2], facecolors=plt.cm.magma(nrm(F)), rstride=1, cstride=2, linewidth=0, shade=False, alpha=0.95)
    for n, c in enumerate(sp):
        g = c.curve.gamma(); A.plot(g[:, 0], g[:, 1], g[:, 2], color=farben[n % 5], lw=1.0)
    A.set_box_aspect((1, 1, 0.35)); A.view_init(elev=35, azim=20); A.set_axis_off()
    m = plt.cm.ScalarMappable(norm=nrm, cmap="magma"); fig.colorbar(m, ax=A, shrink=0.5, label="lokaler QI-Beitrag (Quadrat des Restfehlers)")
    for g in range(5):
        A.plot([], [], color=farben[g], label=f"S{g + 1}")
    A.legend(loc="upper left", fontsize=8); A.set_title("DjLe3eL6, Spulenfeld auf dem Soll-Rand: hell = viel QI-Fehler", fontsize=11)
    fig.savefig(O / "plasma_3d.png", dpi=110, bbox_inches="tight"); plt.close(fig)
    # Zusammenhang (Hinweis, kein Beleg: Punkte sind raeumlich nicht unabhaengig, nur eine Form)
    kor = {}
    for nm, y in (("QI_lokal_Spulenfeld", res2), ("Zusatzfehler_durch_Spulen", delta), ("QI_lokal_fest", fe["res"] ** 2)):
        for xn_, x in (("abstand", fr["abstand"]), ("kruemmung", fr["kruemmung"])):
            kor[f"{nm}~{xn_}"] = float(spearmanr(x.ravel(), y.ravel())[0])
        # Klassen 2 Grad: Summe Fehler gegen kleinsten Abstand
        kor[f"{nm}~abstand_min_je_2grad"] = float(spearmanr(mini(fr["abstand"]), summe(y))[0])
    z = {"qi_mit_spulen_aus_karte": float(fr["qi"]), "qi_fest_aus_karte": float(fe["qi"]), "rang_korrelation_spearman": kor,
         "abstand_min_a": float(fr["abstand"].min() / a_m), "abstand_max_a": float(fr["abstand"].max() / a_m),
         "anteil_zusatzfehler_positiv": float((delta > 0).mean()), "nu_pruef_m": [float(fr["nu_pruef_m"]), float(fe["nu_pruef_m"])]}
    (O / "zusammenhang.json").write_text(json.dumps(z, indent=1)); print(json.dumps(z, indent=1))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "karte":
        karte()
    elif c == "modell2_lage":
        modell2_lage(float(sys.argv[2]) if len(sys.argv) > 2 else 5.0)
    elif c == "modell2_strom":
        modell2_strom()
    elif c == "modell2":
        modell2_basis()
    elif c == "poincare":
        poincare(); (AUS / "karte").mkdir(parents=True, exist_ok=True); poincare_bild()
    if c == "tabelle":
        tabelle(sys.argv[2] if len(sys.argv) > 2 else "basis", json.loads(sys.argv[3]) if len(sys.argv) > 3 else None)
    elif c == "kalibrierung":
        kalibrierung()
    elif c == "interpolation":
        pruefe_interpolation(sys.argv[2] if len(sys.argv) > 2 else "basis")
    elif c == "eins":
        eins(sys.argv[2])
    elif c == "liste":
        print("\n".join(faelle()))
