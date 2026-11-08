"""Verlaufsbild autoresearch-Pilot: ziel und QI je results.tsv-Zeile.
Aufruf: python pilot_bild.py <results.tsv> <bild.png>"""
import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

zeilen = [l.rstrip("\n").split("\t") for l in open(sys.argv[1])][1:]
z = [float(r[1]) for r in zeilen]; q = [float(r[3]) for r in zeilen]
beh = ["[behalten]" in r[6] or "[basis]" in r[6] for r in zeilen]
best, b = [], float("inf")
for zi, k in zip(z, beh):
    if k: b = min(b, zi)
    best.append(b)
x = range(1, len(z) + 1)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 6.5), sharex=True)
a1.plot(x, z, "o", ms=4, color="0.6", label="jeder Versuch")
a1.step(x, best, where="post", color="C0", lw=2, label="bester behaltener Stand")
a1.axhline(0.400, color="C2", ls="--", label="DATJ5FC (DATENSATZ-Form, unverändert): 0,400")
a1.set_ylabel("ziel = f + 10·QI\n(kleiner ist besser)"); a1.legend(fontsize=8)
a1.set_title("autoresearch-Pilot 08.11.2026, Start: Kandidat 3 halb\n(EIGENE Form, aus Datensatzform Do3Qy, halber Schritt)", fontsize=10)
a2.semilogy(x, q, "o-", ms=3, color="C3")
a2.set_ylabel("QI-Restfehler (log)\n(kleiner ist besser)"); a2.set_xlabel("Versuch Nr. (Zeile in results.tsv)")
fig.tight_layout(); fig.savefig(sys.argv[2], dpi=130)
