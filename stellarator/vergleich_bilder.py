"""vergleich_bilder.py — Bilder zum Vergleich Kandidat 3 halb (eigene Form) gegen DATJ5FC (Datensatzform).
Aufruf: python -m stellarator.vergleich_bilder"""
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = Path(__file__).resolve().parents[1]
K = R / "sim/kette_k3"
OUT = R / "docs/recherche/spulen_suche/vergleich"
C_K3, C_DJ, C_DJ2, GRAU = "#2a78d6", "#eb6834", "#f2aa8a", "#52514e"
SK3 = K / "stage2/satz_d100_n10_lr_s56"
SN5 = K / "datj/satz_d100_n5_lr_s56"
SN6 = K / "datj/satz_d100_n6_lr_s56"
HERKUNFT = "Herkunft: Kandidat 3 halb = EIGENE Form (aus Do3Qy, halber Schritt) | DATJ5FC = DATENSATZ-Form (ConStellaration), unverändert"


def kraft(s):
    return [math.hypot(*z["F_netto_MN"]) for z in json.loads((s / "kraefte.json").read_text())["basisspulen"]]


def stil(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e6e5e0", lw=0.7)
    ax.set_axisbelow(True)


def fuss(fig):
    fig.text(0.01, 0.01, HERKUNFT, fontsize=8, color=GRAU)


# a) Nettokraft je Basisspule
fig, ax = plt.subplots(figsize=(10, 4.8), facecolor="#fcfcfb"); ax.set_facecolor("#fcfcfb")
b = 0.27
for i, (n, s, c) in enumerate([("Kandidat 3 halb (eigene Form), 10 Basisspulen", SK3, C_K3),
                               ("DATJ5FC n5 (Datensatzform, Hauptsatz), 5 Basisspulen", SN5, C_DJ),
                               ("DATJ5FC n6 (Datensatzform, Nebensatz), 6 Basisspulen", SN6, C_DJ2)]):
    v = kraft(s); x = np.arange(1, len(v) + 1)
    ax.bar(x + (i - 1) * b, v, b * 0.9, color=c, label=n)
    k = int(np.argmax(v)); ax.text(x[k] + (i - 1) * b, v[k] + 25, f"{v[k]:.0f}", ha="center", fontsize=9, color="#0b0b0b")
ax.axhline(792, color=GRAU, lw=1, ls="--")
ax.text(10.45, 810, "DPrcxq66: 792 MN (Vergleichswert, keine Grenze)", ha="right", fontsize=9, color=GRAU)
ax.set_xticks(range(1, 11)); ax.set_xlabel("Basisspule (die übrigen Spulen wiederholen sich durch Symmetrie)", color=GRAU)
ax.set_ylabel("Nettokraft je Spule in MN", color=GRAU)
ax.set_title("Nettokraft je Spule: DATJ5FC liegt um etwa ein Viertel niedriger", loc="left", fontsize=12)
stil(ax); ax.legend(frameon=False, fontsize=9, loc="upper right", bbox_to_anchor=(1, 0.92)); ax.set_ylim(0, 1600)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fuss(fig); fig.savefig(OUT / "nettokraft_vergleich.png", dpi=130); plt.close(fig)

# b) FEM heißeste Spule je Runde
k3 = json.loads((K / "vergleich/ergebnis_k3_halb.json").read_text())["struktur"]["wand_adapt"]["heiss_je_runde_MPa"]
txt = (K / "vergleich/fem_datj5fc_d100_n5.log").read_text()
n5 = [float(m) for m in re.findall(r"Runde \d: heisseste Spule \d+ (\d+) MPa", txt)]
assert len(k3) == 4 and len(n5) == 4, (k3, n5)
fig, ax = plt.subplots(figsize=(10, 4.8), facecolor="#fcfcfb"); ax.set_facecolor("#fcfcfb")
r = np.arange(4)
for v, c, n, d in [(k3, C_K3, "Kandidat 3 halb (eigene Form)", -0.2), (n5, C_DJ, "DATJ5FC n5 (Datensatzform)", 0.2)]:
    ax.bar(r + d, v, 0.38, color=c, label=n)
    for x, y in zip(r + d, v):
        ax.text(x, y + 20, f"{y:.0f}", ha="center", fontsize=9, color="#0b0b0b")
ax.axhline(500, color=GRAU, lw=1.2, ls="--"); ax.text(-0.45, 515, "500 MPa (nur Annahme)", ha="left", fontsize=9, color=GRAU, bbox=dict(fc="#fcfcfb", ec="none", pad=1))
ax.set_xticks(r); ax.set_xticklabels(["Runde 0\n(gleiche Wände)", "Runde 1", "Runde 2", "Runde 3"])
ax.set_ylabel("Vergleichsspannung heißeste Spule (p99) in MPa", color=GRAU); ax.set_ylim(0, 1700)
ax.set_title("Spannung der heißesten Spule: beide weit über 500 MPa, die Anpassung schwingt", loc="left", fontsize=12)
stil(ax); ax.legend(frameon=False, fontsize=9, loc="upper right")
fig.tight_layout(rect=(0, 0.03, 1, 1)); fuss(fig); fig.savefig(OUT / "fem_runden.png", dpi=130); plt.close(fig)

# c) Hauptkennzahlen relativ, K3 = 1
def j(p): return json.loads(Path(p).read_text())
fk3, fn5 = j(SK3 / "frei/faelle/k_n48000.json"), j(SN5 / "frei/faelle/k_n48000.json")
pk3, pn5 = j(SK3 / "pruefung_satz.json"), j(SN5 / "pruefung_satz.json")
rk3, rn5 = j(SK3 / "rohr/pruefung_rohr.json")["vereinigung"], j(SN5 / "rohr/pruefung_rohr.json")["vereinigung"]
ck3, cn5 = j(K / "vergleich/kuehlung_k3_halb.json"), j(K / "vergleich/kuehlung_datj5fc_d100_n5.json")
e3 = j(K / "vergleich/ergebnis_k3_halb.json")
huelle_k3 = e3["package"]["freiraum_huelle_m"]
huelle_n5 = float(re.search(r'"freiraum_huelle_m": ([\d.]+)', txt).group(1))
M = [("Feldfehler (kleiner ist besser)", pn5["Bn_mittel"] / pk3["Bn_mittel"]),
     ("QI mit Spulen, frei (kleiner ist besser)", fn5["qi"] / fk3["qi"]),
     ("Größte Nettokraft je Spule", max(kraft(SN5)) / max(kraft(SK3))),
     ("Spannung heißeste Spule, Runde 0", n5[0] / k3[0]),
     ("Wandlast Neutronen", cn5["wandlast_neutronen_mittel_MW_m2"] / ck3["wandlast_neutronen_mittel_MW_m2"]),
     ("Abstand Spule–Plasma (Platz)", pn5["abstand_plasma_a"] / pk3["abstand_plasma_a"]),
     ("Rohr–Plasma-Abstand (Platz)", rn5["abstand_plasma_m"] / rk3["abstand_plasma_m"]),
     ("Hülle Plasma–Gehäuse (Platz)", huelle_n5 / huelle_k3)]
fig, ax = plt.subplots(figsize=(10, 5.2), facecolor="#fcfcfb"); ax.set_facecolor("#fcfcfb")
y = np.arange(len(M))[::-1]
ax.barh(y, [m[1] for m in M], 0.6, color=C_DJ)
for yy, m in zip(y, M):
    ax.text(6.95, yy, f"{m[1]:.2f}", va="center", ha="right", fontsize=10, color="#0b0b0b")
ax.axvline(1, color=C_K3, lw=2); ax.text(1.05, -0.75, "Kandidat 3 halb = 1", color=C_K3, fontsize=10, va="center")
ax.set_ylim(-1.1, len(M) - 0.4)
ax.set_yticks(y); ax.set_yticklabels([m[0] for m in M]); ax.set_xlim(0, 7)
ax.set_xlabel("DATJ5FC n5 im Verhältnis zu Kandidat 3 halb", color=GRAU)
ax.set_title("Relativ zu K3: DATJ5FC hat kleinere Kräfte, aber weniger Platz und größere Fehler", loc="left", fontsize=12)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", color="#e6e5e0", lw=0.7); ax.set_axisbelow(True)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fuss(fig); fig.savefig(OUT / "kennzahlen_relativ.png", dpi=130); plt.close(fig)
for m in M:
    print(f"{m[0]}: {m[1]:.3f}")
