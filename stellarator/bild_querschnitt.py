"""Korrigierte Schemazeichnung W7-X-Spulenquerschnitt (SVG)."""
import math, sys

W, H = 1400, 1180
o = []
a = o.append


def t(x, y, s, cls="label", anchor="start", fill=None):
    f = f' fill="{fill}"' if fill else ""
    a(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{f}>{s}</text>')


def leit(x1, y1, x2, y2):
    a(f'<path d="M{x2},{y2} L{x1},{y1}" class="leader"/>')


a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
  'aria-label="Schematischer Querschnitt einer nichtplanaren W7-X-Spule und ihres CICC-Leiters">')
a('<title>W7-X Spulenquerschnitt (korrigiert)</title>')
a('''<style>
text { font-family: "Segoe UI", "Noto Sans", Arial, sans-serif; fill: #111827; }
.title { font-size: 28px; font-weight: 700; } .sub { font-size: 14px; fill: #4b5563; }
.pt { font-size: 18px; font-weight: 700; fill: #0f172a; } .label { font-size: 13px; }
.small { font-size: 12px; fill: #374151; } .tiny { font-size: 11px; fill: #4b5563; }
.h { font-size: 14px; font-weight: 700; } .warn { font-size: 12px; fill: #991b1b; }
.leader { stroke: #374151; stroke-width: 1; fill: none; marker-end: url(#pf); }
.dim { stroke: #1d4ed8; stroke-width: 1.5; fill: none; marker-start: url(#pb); marker-end: url(#pb); }
</style>
<defs>
<marker id="pf" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#374151"/></marker>
<marker id="pb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1d4ed8"/></marker>
<linearGradient id="alu" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#e5e7eb"/><stop offset="50%" stop-color="#a3aab5"/><stop offset="100%" stop-color="#d1d5db"/></linearGradient>
<linearGradient id="stahl" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#9ca3af"/><stop offset="100%" stop-color="#6b7280"/></linearGradient>
<pattern id="sand" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="#efe2bd"/><circle cx="3" cy="3" r="1" fill="#b59a5a"/><circle cx="8" cy="7" r="0.8" fill="#b59a5a"/></pattern>
<clipPath id="bohrung"><circle cx="1020" cy="330" r="122"/></clipPath>
</defs>''')
a(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
t(40, 45, "W7-X Magnetspulen – schematischer Querschnitt", "title")
t(40, 70, "Nichtplanare Spule: CICC-Wicklung, Isolation, Quarzsand-Epoxid-Verguss, Gehäuse aus Edelstahlguss. "
          "Schematisch, nicht maßstäblich.", "sub")

# ------------------------------------------------------------------ Panel 1: Makro
a('<rect x="30" y="85" width="660" height="745" rx="18" fill="#fff" stroke="#e5e7eb"/>')
t(50, 115, "1) Spule: Wickelpaket, Verguss, Gehäuse", "pt")
# Gehaeuse (Stahl), Verguss, Grundisolierung, Wickelpaket
a('<rect x="160" y="160" width="420" height="440" rx="22" fill="#8b939e" stroke="#374151" stroke-width="2"/>')
a('<rect x="232" y="232" width="276" height="308" rx="8" fill="#efe2bd" stroke="#a16207" stroke-width="1.5"/>')
import random; random.seed(1)
for _ in range(260):                             # Quarzsand-Koerner nur im Ring zwischen Paket und Gehaeuse
    x, y = random.uniform(235, 505), random.uniform(235, 537)
    if not (252 < x < 488 and 252 < y < 520):
        a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.3" fill="#a8894a"/>')
a('<rect x="254" y="254" width="232" height="264" rx="4" fill="#fef9c3" stroke="#65a30d" stroke-width="2"/>')
cx0, cy0, d = 271, 262, 22                      # 9 Spalten x 12 Lagen = 108 Windungen
for r in range(12):
    for c in range(9):
        x, y = cx0 + c * d, cy0 + r * d
        a(f'<rect x="{x + 1.5}" y="{y + 1.5}" width="{d - 3}" height="{d - 3}" rx="2" fill="#9ca3af" stroke="#4b5563" stroke-width="0.6"/>')
        a(f'<circle cx="{x + d / 2}" cy="{y + d / 2}" r="6" fill="#c2813f"/>')
    if r % 2 == 1 and r < 11:                   # Trennung der Doppelschichten
        yy = cy0 + (r + 1) * d
        a(f'<line x1="{cx0 - 2}" y1="{yy}" x2="{cx0 + 9 * d + 2}" y2="{yy}" stroke="#16a34a" stroke-width="2"/>')
# Kuehlrohre auf der Gehaeuseoberflaeche
for x, y in ((205, 160), (370, 160), (535, 160), (205, 600), (370, 600), (535, 600)):
    a(f'<circle cx="{x}" cy="{y}" r="9" fill="#bfdbfe" stroke="#1d4ed8" stroke-width="2"/>')
# Abstuetzelemente zur Nachbarspule
a('<rect x="580" y="300" width="70" height="46" fill="#3a73a6" stroke="#1e3a5f"/>')
a('<rect x="90" y="420" width="70" height="46" fill="#3a73a6" stroke="#1e3a5f"/>')
# Beschriftungen
leit(271, 300, 120, 140); t(42, 135, "Wickelpaket: 6 Doppelschichten × 18 Windungen = 108", "small")
leit(395, 349, 630, 140); t(470, 135, "CICC-Leiter mit Windungsisolation", "small")
leit(486, 383, 655, 230); t(560, 225, "Doppelschicht-Trennung", "tiny")
leit(254, 515, 200, 560); t(42, 578, "Grundisolierung (Glasfaser/Epoxid)", "small")
leit(236, 540, 200, 625); t(42, 642, "Verguss: Quarzsand-gefülltes Epoxid", "small")
leit(165, 590, 200, 690); t(42, 707, "Gehäuse: Edelstahlguss, trägt die Lorentzkräfte", "small")
leit(370, 609, 370, 650); t(300, 668, "Kühlrohre (He) auf dem Gehäuse", "small")
leit(650, 323, 660, 400); t(560, 420, "Abstützelemente zur", "small"); t(560, 436, "Nachbarspule", "small")
t(42, 762, "Kryostat: Spulen bei ~4 K im Isoliervakuum. Die Wärmeschilde sitzen an Plasma- und Außengefäß,", "small")
t(42, 780, "nicht direkt an der einzelnen Spule. Spulen hängen am zentralen Tragring und sind über", "small")
t(42, 798, "Abstützelemente untereinander verbunden.", "small")

# ------------------------------------------------------------------ Panel 2: CICC
a('<rect x="710" y="85" width="660" height="745" rx="18" fill="#fff" stroke="#e5e7eb"/>')
t(730, 115, "2) CICC-Leiter (Cable-in-Conduit)", "pt")
a('<path d="M860,145 L1180,145" class="dim"/>'); t(1020, 138, "16 mm", "label", "middle", "#1d4ed8")
a('<rect x="860" y="170" width="320" height="320" rx="14" fill="#c7ccd4" stroke="#374151" stroke-width="2"/>')
a('<circle cx="1020" cy="330" r="124" fill="#bfdbfe" stroke="#374151" stroke-width="1.5"/>')
r_s = 5.6; dx = 2 * r_s + 3.2; dy = dx * math.sqrt(3) / 2
j = 0; y = 330 - 130
while y < 330 + 130:
    x = 1020 - 130 + (dx / 2 if j % 2 else 0)
    while x < 1020 + 130:
        if (x - 1020) ** 2 + (y - 330) ** 2 < 118 ** 2:
            a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_s}" fill="#c2813f" stroke="#7c4a1d" stroke-width="0.6"/>')
        x += dx
    y += dy; j += 1
leit(870, 200, 760, 175); t(730, 165, "Mantel: Aluminiumlegierung (koextrudiert)", "small")
leit(985, 300, 760, 260); t(730, 250, "Kabel: 243 NbTi/Cu-Stränge", "small"); t(730, 266, "(symbolisch)", "tiny")
leit(1012, 450, 760, 470); t(730, 490, "Hohlraum ~37 %: überkritisches", "small"); t(730, 506, "Helium im Zwangsdurchfluss", "small")
# Strang-Detail
a('<circle cx="1260" cy="560" r="55" fill="#e8b27a" stroke="#7c4a1d" stroke-width="1.5"/>')
for k in range(37):
    ring = 0 if k == 0 else (1 if k < 7 else (2 if k < 19 else 3))
    n_r = {0: 1, 1: 6, 2: 12, 3: 18}[ring]; i0 = {0: 0, 1: 1, 2: 7, 3: 19}[ring]
    w = 2 * math.pi * (k - i0) / n_r
    a(f'<circle cx="{1260 + 13 * ring * math.cos(w):.1f}" cy="{560 + 13 * ring * math.sin(w):.1f}" r="3.2" fill="#475569"/>')
leit(1060, 360, 1215, 525)
t(1150, 640, "Strang: NbTi-Filamente in Cu-Matrix", "small"); t(1150, 656, "Cu : NbTi ca. 2,6 (Filamente symbolisch)", "tiny")
t(730, 560, "Auslegung bis ~17,6 kA; Standardbetrieb ~13 kA", "small")
t(730, 578, "(unser Modell: 13,49 kA, kalibriert auf 2,5 T)", "tiny")
t(730, 600, "Max. Feld am Leiter ~6,7 T (Auslegung, 3 T auf der Achse)", "small")
t(730, 630, "108 Windungen je nichtplanarer Spule; 10 Spulen je Stromkreis", "small")
t(730, 648, "in Reihe, 7 Stromkreise (5 nichtplanar, 2 planar).", "small")
t(730, 690, "Planare Spulen (20 Stück, 2 Typen): verstellen die", "small")
t(730, 708, "Konfiguration (iota, Spiegelverhältnis, Plasmalage).", "small")

# ------------------------------------------------------------------ Panel 3: Korrekturen + Modellbezug
a('<rect x="30" y="850" width="1340" height="290" rx="18" fill="#f8fafc" stroke="#e5e7eb"/>')
t(50, 882, "Korrigiert gegenüber der Vorlage", "pt")
for i, s in enumerate([
        "Kein Stahlkern im Wickelpaket: Das Paket ist ein massiver Block aus gestapelten Leiterlagen,",
        "   keine ineinanderliegenden Ringe. „0,1 mm“ war eine Genauigkeitsangabe, keine Dicke.",
        "Wärmeschild nicht direkt an jeder Spule, sondern an den Gefäßwänden des Kryostaten;",
        "   die Gehäuse haben eigene Heliumkühlrohre.",
        "„Kryostat-Vakuum ca. 4 K“: die kalten Bauteile sind bei ~4 K, das Vakuum isoliert.",
        "„35 kA je Strang“: gilt (wenn überhaupt) für den ganzen Leiter, nicht für einen Strang.",
        "Prüfspannungen, VPI-Drücke, Faser- und Filamentzahlen der Vorlage weggelassen (nicht belegt)."]):
    t(56, 910 + 20 * i, ("• " if not s.startswith("   ") else "  ") + s.strip(), "small")
t(740, 882, "Bezug zu unserem FreeCAD/Elmer-Modell", "pt")
for i, s in enumerate([
        "Wickelpaket: Loft durch die Wickelpaket-Skizzen (homogenisiertes Material)",
        "Verguss: noch nicht modelliert (nächste Verbesserungsschleife, E ~10–20 GPa)",
        "Gehäuse: Variable Section Sweep, Wanddicke nach Kraft und Freiraum",
        "Abstützelemente: Verbinder (Ruled-Loft) zwischen den Gehäusen",
        "Hinweis: Spulenbahnen aus öffentlichen simsopt-Daten; Gehäuse/Verbinder sind",
        "eine eigene, vereinfachte Konstruktion, nicht die echte IPP-Struktur."]):
    t(746, 910 + 20 * i, ("• " if i < 4 else "") + s, "small")
t(56, 1120, "Zahlenwerte vor Veröffentlichung mit IPP-Quellen gegenprüfen. Schematische Darstellung, nicht maßstäblich.", "warn")
a('</svg>')
open(sys.argv[1], "w").write("\n".join(o))
