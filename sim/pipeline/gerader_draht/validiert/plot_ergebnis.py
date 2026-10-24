import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MU0   = 4*math.pi*1e-7
I     = 1.0          # A
R     = 1e-3         # m  (Draht-Radius)
RMAX  = 5e-3         # m

pts = []
for l in open('f.dat'):
    p = l.split()
    if len(p) < 12:
        continue
    try:
        x = float(p[3]); Hy = float(p[11])
    except Exception:
        continue
    r = (x*x + 0.0) ** 0.5
    if r > 1e-12:
        pts.append((r, abs(Hy)))

# exakte Biot-Savart
def H_exact(r):
    return (I*r/(2*math.pi*R**2)) if r <= R else (I/(2*math.pi*r))

rs    = sorted(t[0] for t in pts)
Hen   = [dict(pts)[r] for r in rs]
rfin  = numpy_rfin = [r for r in rs if 0.85*R <= r <= 1.15*R]

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
fig.suptitle("Gerader Draht, I = 1 A, R = 1 mm — Elmer (MgDynamics2D) vs. Biot-Savart",
             fontsize=12)

ax = axes[0]
ax.plot(rs, [MU0*H_exact(r) for r in rs], 'k-', lw=2, label='Biot-Savart (exakt)')
ax.plot(rs, [MU0*h for h in Hen], 'ro', ms=3.5, lw=0, label='Elmer FEM')
ax.axvline(R, color='gray', ls='--', lw=1, label='Draht-Oberflaeche r=R')
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlabel('r [m]'); ax.set_ylabel('B_theta [T]')
ax.set_title('Magnetische Flussdichte')
ax.legend(loc='lower left', fontsize=8); ax.grid(alpha=0.3, which='both')

ax = axes[1]
inn  = [r for r in rs if r <= R]
aus  = [r for r in rs if r > R and r < RMAX - 0.5e-6]
dev_i = [100.0*(dict(pts)[r] - H_exact(r))/H_exact(r) for r in inn]
dev_a = [100.0*(dict(pts)[r] - H_exact(r))/H_exact(r) for r in aus]
ax.plot(inn,  dev_i, 'ob', ms=4, label='innerhalb Draht (H ~ r)')
ax.plot(aus,  dev_a, 'r^', ms=4, label='auusserhalb (H ~ 1/r)')
ax.axhline(0, color='k', lw=1)
ax.axhline(-5, color='gray', ls=':'); ax.axhline(5, color='gray', ls=':')
ax.set_xscale('log')
ax.set_xlabel('r [m]'); ax.set_ylabel('Abweichung von exakt [%]')
ax.set_title('Fehler gegen Biot-Savart')
ax.legend(fontsize=8); ax.grid(alpha=0.3, which='both')

plt.tight_layout()
plt.savefig('ergebnis.png', dpi=130)
print("speichert ->", "ergebnis.png")

# Zahlen-Tabelle
print()
print(" r [mm]      H_FEM [A/m]   H_exakt [A/m]   B_exakt [mT]   Abw. [%]")
print("-"*74)
for tgt in [0.3e-3, 0.6e-3, 1.0e-3, 1.3e-3, 2.0e-3, 3.0e-3, 4.0e-3, 5.0e-3]:
    best = min(pts, key=lambda t: abs(t[0]-tgt))
    r, hf = best
    he = H_exact(r); b = MU0*he
    dw = 100.0*(hf-he)/he
    tag = " *" if abs(r-5.0e-3) < 1e-9 else ""
    print(f" {r*1e3:6.2f}   {hf:12.3f}  {he:12.3f}   {b*1e3:10.4f}  {dw:+8.2f}{tag}")
print()
print("  * Randknoten: Az dort per Dirichlet-BC fixiert (B-Komponente ist")
print("    dort ein BC-Artefakt, bewusst aus der Auswertung ausgeschlossen)")
mean_i = sum(dev_i)/len(dev_i); mean_a = sum(dev_a)/len(dev_a)
print(f"  Mittelwert innerer Feld: {mean_i:+.2f} %")
print(f"  Mittelwert Ausserfeld:  {mean_a:+.2f} %")
