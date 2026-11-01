"""mhd_hartmann.py — Prüffall für die Lorentzkraft in FluidX3D (Variante B: Flüssigmetall im Magnetfeld).

  .venv/bin/python -m stellarator.mhd_hartmann

Kernänderung (eigene FluidX3D-Kopie mit den Diffs aus fluidx3d/, Pfad über FLUIDX3D_MHD): induktionsfreie MHD bei kleiner magnetischer
Reynoldszahl. Die Lorentzkraft f = j x B mit j = sigma (-grad phi + u x B). Im Kanal zwischen zwei unendlich
ausgedehnten Platten mit B senkrecht dazu verschwindet grad phi, also f = -sigma B^2 u_senkrecht = -K rho u_s.
Halbimplizit eingebaut (Guo-Kraft: u = u* + F/2rho  ->  u_s = (u*_s + F_s/2rho)/(1 + K/2)), damit auch grosse K stabil bleiben.

Exakte Lösung (Hartmann 1937), Wände bei y = +-a, Antrieb G = rho fx:
    u(y) = fx/K * (1 - cosh(Ha y/a)/cosh(Ha)),   Ha = B a sqrt(sigma/(rho nu)),   K = Ha^2 nu / a^2
Ha = 0 ergibt die Poiseuille-Parabel u = fx (a^2 - y^2)/(2 nu).
"""
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FX = Path(os.environ.get("FLUIDX3D_MHD", "fluidx3d_mhd"))   # Ordner der gepatchten FluidX3D-Kopie
AUS = ROOT / "sim" / "mhd" / "hartmann"
NU = 0.1
U_ZIEL = 0.03


def analytisch(eta, Ha, fx, a):
    if Ha == 0:
        return fx * a ** 2 * (1 - eta ** 2) / (2 * NU)
    K = Ha ** 2 * NU / a ** 2
    return fx / K * (1 - np.cosh(Ha * eta) / np.cosh(Ha))


def lauf(Ha, a):
    Ny = 2 * a + 2
    K = Ha ** 2 * NU / a ** 2
    fx = U_ZIEL * 2 * NU / a ** 2 if Ha == 0 else U_ZIEL * K / (1 - 1 / np.cosh(Ha))
    t_rel = a ** 2 / NU if Ha == 0 else min(a ** 2 / NU, 1 / K)
    schritte = int(12 * t_rel) + 2000
    ordner = AUS / f"ha{Ha}_a{a}"; ordner.mkdir(parents=True, exist_ok=True)
    (ordner / "fall.txt").write_text(f"{ordner} {Ny} {NU} {fx:.9e} {schritte} {max(schritte // 20, 100)}\n")
    env = dict(os.environ, MHD_FALL=str(ordner / "fall.txt"), FX_MHD_K=f"{K:.9e}", FX_MHD_B="0.0f, 1.0f, 0.0f")
    r = subprocess.run([str(FX / "bin" / "FluidX3D")], cwd=FX, env=env, capture_output=True, text=True, timeout=3600)
    (ordner / "fluidx3d.log").write_text(r.stdout + r.stderr)
    p = np.loadtxt(ordner / "profil.txt")
    yc = (Ny - 1) / 2; eta = (p[:, 0] - yc) / a
    ua = analytisch(eta, Ha, fx, a)
    fehler = float(np.sqrt(np.mean((p[:, 1] - ua) ** 2)) / ua.max())
    return dict(Ha=Ha, a=a, K=K, fx=fx, schritte=schritte, eta=eta, u=p[:, 1], ua=ua, fehler=fehler,
                schicht_zellen=a / Ha if Ha else np.inf)


def bild(erg, gitter, sprache):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    de = sprache == "de"
    fig, ax = plt.subplots(1, 2, figsize=(13, 5), dpi=130)
    farben = ["#52514e", "#2a78d6", "#1baf7a", "#eda100", "#eb6834"]
    for e, c in zip(erg, farben):
        ax[0].plot(e["eta"], e["ua"] / e["ua"].max(), color=c, lw=1.5)
        ax[0].plot(e["eta"][::2], e["u"][::2] / e["ua"].max(), "o", ms=3.5, color=c,
                   label=f"Ha = {e['Ha']}: {('Fehler' if de else 'error')} {100*e['fehler']:.2f} %")
    ax[0].set_xlabel("y / a"); ax[0].set_ylabel("u / u_max" if not de else "u / u_max (exakt)")
    ax[0].set_title(("Hartmann-Strömung: FluidX3D (Punkte) gegen exakte Lösung (Linien), a = 32 Zellen" if de else
                     "Hartmann flow: FluidX3D (dots) vs exact solution (lines), a = 32 cells"), fontsize=10.5)
    ax[0].legend(frameon=False, fontsize=8.5, loc="lower center")
    a_ = np.array([g["a"] for g in gitter]); f_ = np.array([g["fehler"] for g in gitter])
    ax[1].loglog(a_, f_, "o-", color="#eb6834", label="Ha = 30")
    ax[1].loglog(a_, f_[0] * (a_ / a_[0]) ** -2, ls="--", color="#52514e", label=("Ordnung 2" if de else "order 2"))
    for g in gitter:
        ax[1].annotate((f"Schicht {g['schicht_zellen']:.1f} Zellen" if de else f"layer {g['schicht_zellen']:.1f} cells"),
                       (g["a"], g["fehler"]), (6, 6), textcoords="offset points", fontsize=8)
    ax[1].set_xlabel(("Halbe Kanalweite a [Zellen]" if de else "half channel width a [cells]"))
    ax[1].set_ylabel(("RMS-Fehler / u_max" if de else "RMS error / u_max"))
    ax[1].set_title(("Gitterstudie bei Ha = 30 (Hartmann-Schicht a/Ha)" if de else "Grid study at Ha = 30 (Hartmann layer a/Ha)"),
                    fontsize=10.5)
    ax[1].legend(frameon=False, fontsize=8.5)
    for q in ax:
        q.grid(True, which="both", color="#e5e4e0", lw=0.6); q.spines[["top", "right"]].set_visible(False)
    fig.text(0.99, 0.01, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", fontsize=7, color="#52514e", ha="right")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    name = "mhd_hartmann.png" if de else "mhd_hartmann_en.png"
    fig.savefig(ROOT / "docs" / "bilder" / name); plt.close(fig)
    shutil.copy(ROOT / "docs" / "bilder" / name, ROOT / "bericht" / "projektbericht" / "bilder" / name)
    return ROOT / "docs" / "bilder" / name


def main():
    erg = [lauf(Ha, 32) for Ha in (0, 5, 10, 20, 30)]
    gitter = [lauf(30, a) for a in (8, 16, 32, 64)]
    for e in erg + gitter:
        print(f"Ha {e['Ha']:3d}  a {e['a']:3d}  K {e['K']:.4e}  Schritte {e['schritte']:7d}  Fehler {100*e['fehler']:.3f} %  "
              f"Schicht {e['schicht_zellen']:.2f} Zellen")
    import json
    (ROOT / "stellarator" / "daten" / "mhd_hartmann.json").write_text(json.dumps(
        [{k: (float(v) if np.isscalar(v) else None) for k, v in e.items() if np.isscalar(v)} for e in erg + gitter], indent=1))
    for s in ("de", "en"):
        print(bild(erg, gitter, s))


if __name__ == "__main__":
    main()
