"""netzplan_din.py -- Vorgangsknoten-Netzplan nach DIN 69900 (REFA) aus plan_fusion.py.

KI-generiert (Claude Opus, 2026-11-12). Knoten: oben FAZ | D | FEZ, Mitte Nr. + Vorgang, unten SAZ | GP | FP | SEZ.
Zeiten in Arbeitstagen ab Projektbeginn Zukunft (0 = 13.11.2026); Dauern sind Annahmen. Kritischer Pfad (GP = 0) rot.
Die rekonstruierten Phasen der Vergangenheit haben keine belegte Abfolge und erscheinen nur als Vorlauf-Kasten.

    python3 pm/plan/netzplan_din.py [--en]   -> pm/plan/netzplan_din.svg (bzw. netzplan_din_en.svg)
"""
import json, sys
from pathlib import Path
from html import escape

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
from plan_fusion import A, cpm, START  # noqa: E402

EN = "--en" in sys.argv
T = dict(titel="Netzplan nach DIN 69900 (Vorgangsknotennetz) · Stellarator, Zukunft ab 13.11.2026 · KI-generiert" if not EN else
         "Network plan per DIN 69900 (activity-on-node) · Stellarator, future from 13 Nov 2026 · AI-generated",
         leg="Zeiten in Arbeitstagen ab 13.11.2026, Dauern = Annahmen · FAZ/FEZ frühester Anfang/Ende · SAZ/SEZ spätester Anfang/Ende · GP Gesamtpuffer · FP freier Puffer · rot = kritischer Pfad (GP = 0)" if not EN else
         "Times in working days from 13 Nov 2026, durations = assumptions · ES/EF earliest start/finish · LS/LF latest start/finish · TF total float · FF free float · red = critical path (TF = 0)",
         vor="Vorlauf: 13 Phasen 22.10.–12.11.2026 (rekonstruiert, Abfolge nicht belegt)" if not EN else
         "Preceding: 13 phases 22 Oct–12 Nov 2026 (reconstructed, sequence not recorded)",
         k=("FAZ", "FEZ", "SAZ", "SEZ", "GP", "FP", "D") if not EN else ("ES", "EF", "LS", "LF", "TF", "FF", "D"))

es, ef, ls, lf, nach, ende = cpm(A)
name = {t[0]: t[1] for t in A}; dur = {t[0]: t[2] for t in A}; vor = {t[0]: t[3] for t in A}
fp = {i: round((min(es[s] for s in nach[i]) if nach[i] else ende) - ef[i], 2) for i in name}
gp = {i: round(ls[i] - es[i], 2) for i in name}

# Ebenen: längste Vorgängerkette (Anzahl), Reihenfolge in der Ebene nach FAZ, dann Listenposition
ebene = {}
for i in name:
    ebene[i] = 1 + max((ebene[v] for v in vor[i]), default=-1)
spalten = {}
for i in name:
    spalten.setdefault(ebene[i], []).append(i)
W, H, GX, GY, X0, Y0 = 230, 104, 70, 34, 290, 96
pos = {}
for e, ids in spalten.items():
    ids.sort(key=lambda i: (es[i], [t[0] for t in A].index(i)))
    for r, i in enumerate(ids):
        pos[i] = (X0 + e * (W + GX), Y0 + r * (H + GY))
breite = X0 + (max(spalten) + 1) * (W + GX) + 20
hoehe = Y0 + max(len(v) for v in spalten.values()) * (H + GY) + 30


def zahl(x):
    return f"{x:g}".replace(".", ",") if not EN else f"{x:g}"


def umbruch(txt, n=30):
    w, z = txt.split(), [""]
    for x in w:
        if len(z[-1]) + len(x) + 1 > n:
            z.append(x)
        else:
            z[-1] = (z[-1] + " " + x).strip()
    return z[:2] if len(z) <= 2 else [z[0], z[1][: n - 1] + "…"]


s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {breite} {hoehe}" width="{breite}" height="{hoehe}" font-family="Helvetica, Arial, sans-serif">',
     '<defs><marker id="p" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z" fill="#555"/></marker>'
     '<marker id="pr" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z" fill="#c0392b"/></marker></defs>',
     f'<rect width="{breite}" height="{hoehe}" fill="#fff"/>',
     f'<text x="16" y="28" font-size="18" font-weight="bold">{escape(T["titel"])}</text>',
     f'<text x="16" y="52" font-size="12.5" fill="#333">{escape(T["leg"])}</text>']
# Vorlauf-Kasten
s.append(f'<rect x="16" y="{Y0}" width="{X0 - 60}" height="{H}" rx="6" fill="#e8f0fa" stroke="#3a78b8" stroke-dasharray="5 3"/>')
for k, z in enumerate(umbruch(T["vor"], 34) + [""]):
    s.append(f'<text x="26" y="{Y0 + 30 + 18 * k}" font-size="12.5" fill="#1f4e79">{escape(z)}</text>')
# Pfeile
for i in name:
    for v in vor[i]:
        x1, y1 = pos[v][0] + W, pos[v][1] + H / 2; x2, y2 = pos[i][0], pos[i][1] + H / 2
        krit = gp[i] == 0 and gp[v] == 0 and abs(ef[v] - es[i]) < 1e-9
        if ebene[i] - ebene[v] > 1:   # über mehrere Spalten: in der Lücke zwischen zwei Zeilen führen
            r = min(round((pos[v][1] - Y0) / (H + GY)), round((pos[i][1] - Y0) / (H + GY)))
            yc = Y0 + (r + 1) * (H + GY) - GY / 2; a1, a2 = x1 + GX / 2, x2 - GX / 2
            d = f"M{x1},{y1} C{a1},{y1} {x1},{yc} {a1},{yc} L{a2},{yc} C{x2},{yc} {a2},{y2} {x2},{y2}"
        else:
            mx = (x1 + x2) / 2; d = f"M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}"
        s.append(f'<path d="{d}" fill="none" stroke="{"#c0392b" if krit else "#888"}" '
                 f'stroke-width="{2.4 if krit else 1.2}" marker-end="url(#{"pr" if krit else "p"})"/>')
for i in name:
    if not vor[i]:
        x2, y2 = pos[i][0], pos[i][1] + H / 2
        s.append(f'<path d="M{X0 - 44},{Y0 + H / 2} C{X0 - 20},{Y0 + H / 2} {X0 - 20},{y2} {x2},{y2}" fill="none" stroke="#3a78b8" stroke-dasharray="4 3" marker-end="url(#p)"/>')
# Knoten
fk = T["k"]
for i in name:
    x, y = pos[i]; krit = gp[i] == 0; c = "#c0392b" if krit else "#444"
    h3 = H / 3.4
    s.append(f'<g><title>{escape(i)}: {escape(name[i])}</title>')
    s.append(f'<rect x="{x}" y="{y}" width="{W}" height="{H}" fill="{"#fdecea" if krit else "#fafafa"}" stroke="{c}" stroke-width="{2.2 if krit else 1.2}"/>')
    s.append(f'<line x1="{x}" y1="{y + h3}" x2="{x + W}" y2="{y + h3}" stroke="{c}"/><line x1="{x}" y1="{y + H - h3}" x2="{x + W}" y2="{y + H - h3}" stroke="{c}"/>')
    for fx in (W / 3, 2 * W / 3):
        s.append(f'<line x1="{x + fx}" y1="{y}" x2="{x + fx}" y2="{y + h3}" stroke="{c}"/>')
    for fx in (W / 4, W / 2, 3 * W / 4):
        s.append(f'<line x1="{x + fx}" y1="{y + H - h3}" x2="{x + fx}" y2="{y + H}" stroke="{c}"/>')
    oben = [(fk[0], es[i]), (fk[6], dur[i]), (fk[1], ef[i])]
    for k, (lab, val) in enumerate(oben):
        cx = x + W / 6 + k * W / 3
        s.append(f'<text x="{cx}" y="{y + 11}" font-size="8.5" fill="#777" text-anchor="middle">{lab}</text>'
                 f'<text x="{cx}" y="{y + h3 - 5}" font-size="13" font-weight="bold" text-anchor="middle">{zahl(val)}</text>')
    unten = [(fk[2], ls[i]), (fk[4], gp[i]), (fk[5], fp[i]), (fk[3], lf[i])]
    for k, (lab, val) in enumerate(unten):
        cx = x + W / 8 + k * W / 4
        s.append(f'<text x="{cx}" y="{y + H - h3 + 11}" font-size="8.5" fill="#777" text-anchor="middle">{lab}</text>'
                 f'<text x="{cx}" y="{y + H - 5}" font-size="13" font-weight="bold" text-anchor="middle" fill="{c if lab in (fk[4],) and krit else "#000"}">{zahl(val)}</text>')
    s.append(f'<text x="{x + 8}" y="{y + h3 + 15}" font-size="12.5" font-weight="bold" fill="{c}">{escape(i)}</text>')
    for k, z in enumerate(umbruch(name[i], 31)):
        s.append(f'<text x="{x + 42}" y="{y + h3 + 15 + 13 * k}" font-size="10.5">{escape(z)}</text>')
    s.append("</g>")
s.append(f'<text x="16" y="{hoehe - 10}" font-size="11" fill="#666">KI-generiert (Claude Opus, 2026-11-12) aus pm/plan/plan_fusion.py · Projektende Zukunft: {zahl(ende)} AT · Thomas Schmiegelt</text>')
s.append("</svg>")
datei = HIER / ("netzplan_din_en.svg" if EN else "netzplan_din.svg")
datei.write_text("\n".join(s)); print(datei, f"{len(name)} Vorgänge, Ende {ende} AT, kritisch: {[i for i in name if gp[i] == 0]}")
