"""Drehbare 3D-Ansicht (plotly-HTML): Plasma + alle Spulen mehrerer Sätze, Sätze per Legende ein-/ausschaltbar.
Aufruf: python spulen_3d_html.py <aus.html> <titel> <name=satz_ordner> ...   (Längen in m über a = 1,8 m)"""
import sys
from pathlib import Path
import numpy as np
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spulen_satz import flaeche, lade_satz  # noqa: E402
from simsopt.field import Current, coils_via_symmetries  # noqa: E402

aus, titel, saetze = sys.argv[1], sys.argv[2], [a.split("=", 1) for a in sys.argv[3:]]
s = flaeche(Path(saetze[0][1]) / "boundary.json", nphi=160, ntheta=48)
a = float(np.sqrt(abs(s.volume()) / (2 * np.pi ** 2 * float(s.get_rc(0, 0))))); k = 1.8 / a
g = s.gamma() * k; g = np.concatenate([g, g[:, :1]], 1); g = np.concatenate([g, g[:1]], 0)
fig = go.Figure(go.Surface(x=g[..., 0], y=g[..., 1], z=g[..., 2], colorscale=[[0, "#e8662f"], [1, "#f4a259"]],
                           showscale=False, opacity=0.9, name="Plasma", showlegend=True))
farben = ["#222222", "#1f77b4", "#2ca02c", "#9467bd"]
for j, (name, ordner) in enumerate(saetze):
    basis, I, nfp = lade_satz(ordner)
    sp = coils_via_symmetries(basis, [Current(float(x)) for x in I], nfp, True)
    for i, c in enumerate(sp):
        p = c.curve.gamma() * k; p = np.vstack([p, p[:1]])
        fig.add_trace(go.Scatter3d(x=p[:, 0], y=p[:, 1], z=p[:, 2], mode="lines", line=dict(color=farben[j % 4], width=5),
                                   name=name, legendgroup=name, showlegend=(i == 0), visible=True if j == 0 else "legendonly"))
fig.update_layout(title=titel, scene=dict(aspectmode="data", xaxis_title="x, m", yaxis_title="y, m", zaxis_title="z, m"),
                  legend=dict(itemclick="toggle"), margin=dict(l=0, r=0, t=60, b=0))
fig.write_html(aus, include_plotlyjs=True)
print("ok", aus)
