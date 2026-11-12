"""gx_3d.py -- GX-Turbulenz (elektrostatisches Potential Phi) in 3D: Flussröhre an ihrem echten Ort im Plasma, animiert.

KI-generiert (Claude Opus, 2026-11-11). Nutzer: „kannst du auch eine simulation in 3D darstellen?“

  ~/cae_projekte/gx/deps/venv/bin/python -m stellarator.gx_3d <laufordner> <ausgabe.html> [--rho-mm 3.2] [--a 1.8]

Abbildung (wie GX-Geometriemodul pyvmec, gx_geo_vmec.py):
- Mittellinie: Feldlinie alpha = theta_B - iota*phi_B = 0 auf der Fläche s0 (Boozer, booz_xform), phi_zyl = phi_B - nu_B.
  Prüfung: R entlang der Linie gegen Rplot aus der GX-Geometriedatei (*.eik.nc).
- Querschnitt: Richtungen aus grad_x (radial), grad_y (binormal) der *.eik.nc als Einheitsvektoren; Verschiebung = rho_i * (x e_x + y e_y),
  x, y in rho (GX-Doku Inputs.rst: L_x = 2 pi x0 rho_ref). Rohe grad-Beträge enthalten Normierungsfaktoren (shat) und werden nicht verwendet.
- Maßstab: Plasma auf kleinen Radius a [m] skaliert. rho_i ANNAHME (Vorgabe 3,2 mm: T_i = 10 keV, D-T-Mittel 2,5 u, B = 5 T).
Daten: *.big.nc (PhiXY je nwrite_big Schritte). Ausgabe: eine HTML-Datei (Plotly von cdnjs).
"""
import json, sys
from pathlib import Path
import numpy as np
import netCDF4

PLOTLY = "https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.2/plotly.min.js"


def boozer_linie(wout, s0, theta_b, nfp_dummy=None):
    import booz_xform as bx
    b = bx.Booz_xform(); b.verbose = 0; b.read_wout(str(wout))
    s_half = np.asarray(b.s_in)
    j = int(np.argmin(np.abs(s_half - s0)))
    b.compute_surfs = [j]; b.mboz = 32; b.nboz = 32; b.run()
    iota = float(np.asarray(b.iota)[j])
    xm, xn = np.asarray(b.xm_b), np.asarray(b.xn_b)
    rmn, zmn, numn = (np.asarray(v)[:, 0] for v in (b.rmnc_b, b.zmns_b, b.numns_b))
    return b, j, iota, xm, xn, rmn, zmn, numn


def flaeche_xyz(xm, xn, rmn, zmn, numn, th, ph):
    """R, Z, phi_zyl auf Boozer-Gitter th, ph (beliebige gleich geformte Felder)."""
    ang = th[..., None] * xm - ph[..., None] * xn
    R = (np.cos(ang) * rmn).sum(-1); Z = (np.sin(ang) * zmn).sum(-1); nu = (np.sin(ang) * numn).sum(-1)
    phc = ph - nu
    return R * np.cos(phc), R * np.sin(phc), Z, R


def main(a):
    ordner, html = Path(a[0]), Path(a[1])
    rho_mm = float(a[a.index("--rho-mm") + 1]) if "--rho-mm" in a else 3.2
    a_m = float(a[a.index("--a") + 1]) if "--a" in a else 1.8
    big = next(ordner.glob("*.big.nc")); eik = next(ordner.glob("*.eik.nc")); wout = next(ordner.glob("wout_*.nc"))
    inp = next(ordner.glob("*.in")).read_text()
    s0 = float(inp.split("desired_normalized_toroidal_flux")[1].split("=")[1].split()[0])
    e = netCDF4.Dataset(eik)
    th_b = np.array(e["theta_PEST"][:]); Rplot = np.array(e["Rplot"][:])
    gx_ = np.array(e["grad_x"][:]); gy_ = np.array(e["grad_y"][:])          # (3, nz), kartesisch
    _, j, iota, xm, xn, rmn, zmn, numn = boozer_linie(wout, s0, th_b)
    w = netCDF4.Dataset(wout); a_vmec = float(w["Aminor_p"][:]); nfp = int(w["nfp"][:])
    k = a_m / a_vmec                                                         # Maßstab -> Meter
    ph_b = (th_b - 0.0) / iota
    X0, Y0, Z0, R0 = flaeche_xyz(xm, xn, rmn, zmn, numn, th_b, ph_b)
    pruef = float(np.max(np.abs(R0 - Rplot)) / np.mean(Rplot))
    print(f"s0={s0} (Boozer-Fläche Index {j}), iota={iota:.4f}, a_vmec={a_vmec:.4f}, "
          f"Abweichung R Mittellinie gegen GX-Rplot: {pruef:.2e}", flush=True)
    # Querschnitt: nur RICHTUNGEN aus grad_x, grad_y (enthalten Normierungsfaktoren wie shat); Längen nach GX-Doku
    # (Inputs.rst: x radial, y binormal, L_x = 2 pi x0 in rho_ref): ex senkrecht zur Fläche, ey quer zum Feld in der Fläche.
    ex = gx_.T / np.linalg.norm(gx_.T, axis=1)[:, None]
    ey = gy_.T - (gy_.T * ex).sum(1)[:, None] * ex; ey /= np.linalg.norm(ey, axis=1)[:, None]
    d = netCDF4.Dataset(big)
    t = np.array(d["Grids/time"][:]); xg = np.array(d["Grids/x"][:]); yg = np.array(d["Grids/y"][:])
    phi = np.array(d["Diagnostics/PhiXY"][:])                                # (t, y, x, theta)
    nz = phi.shape[3]
    xg = xg - xg.mean(); yg = yg - yg.mean()
    rho_star = rho_mm * 1e-3 / a_m
    s = rho_star * a_vmec                                                    # Verschiebung in VMEC-Einheiten je rho
    # Anzeige-Verfeinerung entlang der Feldlinie (GX: nz Punkte über ~5 Toroidalumläufe -> Sehnen von ~10 m):
    # Mittellinie exakt aus dem Gleichgewicht, e_x/e_y und Phi linear in theta interpoliert (Phi ändert sich entlang B langsam).
    NF = 6; st = 3; fs = 2                                                   # Verfeinerung, Querschnitt-Ausdünnung, jedes fs-te Bild
    thz = th_b[:nz]
    thf = np.linspace(thz[0], thz[-1], (nz - 1) * NF + 1)
    Xf, Yf, Zf, _ = flaeche_xyz(xm, xn, rmn, zmn, numn, thf, thf / iota)
    C = np.stack([Xf, Yf, Zf], 1)
    ex = np.stack([np.interp(thf, th_b, ex[:, c]) for c in range(3)], 1)
    ey = np.stack([np.interp(thf, th_b, ey[:, c]) for c in range(3)], 1)
    lin = lambda f: np.apply_along_axis(lambda v: np.interp(thf, thz, v), -1, f)
    xi, yi = xg[::st], yg[::st]
    bilder = list(range(0, len(t), fs)) + ([len(t) - 1] if (len(t) - 1) % fs else [])

    def seite(achse, wert):
        if achse == "x":
            P = C[:, None, :] + s * (wert * ex[:, None, :] + yi[None, :, None] * ey[:, None, :])
        else:
            P = C[:, None, :] + s * (xi[None, :, None] * ex[:, None, :] + wert * ey[:, None, :])
        return P * k

    seiten = [("x", xi[0]), ("x", xi[-1]), ("y", yi[0]), ("y", yi[-1])]
    geo = [seite(*q) for q in seiten]

    def werte(it):
        f = phi[it]                                                          # (y, x, z)
        return [lin(f[::st, 0, :]).T, lin(f[::st, -1, :]).T, lin(f[0, ::st, :]).T, lin(f[-1, ::st, :]).T]

    iz0 = int(np.argmin(np.abs(thz)))                                        # Querschnitt bei theta = 0 (Außenseite)

    def schnitt(it):
        return phi[it][:, :, iz0]

    vmax = float(np.percentile(np.abs(phi[len(t) // 2:]), 99))
    # Plasmaoberfläche (Rand) aus VMEC (s = 1), ganzer Torus
    rmnc = np.array(w["rmnc"][-1]); zmns = np.array(w["zmns"][-1]); xmv = np.array(w["xm"][:]); xnv = np.array(w["xn"][:])
    TH, PH = np.meshgrid(np.linspace(0, 2 * np.pi, 49), np.linspace(0, 2 * np.pi, 161), indexing="ij")
    ang = TH[..., None] * xmv - PH[..., None] * xnv
    Rr = (np.cos(ang) * rmnc).sum(-1); Zr = (np.sin(ang) * zmns).sum(-1)
    rand = {"type": "surface", "x": (Rr * np.cos(PH) * k).round(3).tolist(), "y": (Rr * np.sin(PH) * k).round(3).tolist(),
            "z": (Zr * k).round(3).tolist(), "surfacecolor": np.zeros_like(Rr).tolist(), "colorscale": [[0, "#9aa5b1"], [1, "#9aa5b1"]],
            "showscale": False, "opacity": 0.18, "name": "Plasmarand", "hoverinfo": "skip", "lighting": {"ambient": 0.9}}
    # Feldlinie über mehrere Umläufe (Orientierung)
    thl = np.linspace(-3 * np.pi, 3 * np.pi, 600)
    Xl, Yl, Zl, _ = flaeche_xyz(xm, xn, rmn, zmn, numn, thl, thl / iota)
    linie = {"type": "scatter3d", "mode": "lines", "x": (Xl * k).round(3).tolist(), "y": (Yl * k).round(3).tolist(), "z": (Zl * k).round(3).tolist(),
             "line": {"color": "#333", "width": 2}, "name": f"Feldlinie auf s = {s0}", "hoverinfo": "skip"}
    spuren = [rand, linie]
    for i, P in enumerate(geo):
        spuren.append({"type": "surface", "x": P[..., 0].round(3).tolist(), "y": P[..., 1].round(3).tolist(), "z": P[..., 2].round(3).tolist(),
                       "surfacecolor": werte(-1)[i].round(3).tolist(), "cmin": -vmax, "cmax": vmax, "colorscale": "RdBu", "reversescale": True,
                       "showscale": i == 0, "colorbar": {"title": {"text": "Potential Φ<br>(GX-Einheiten)"}, "len": 0.6},
                       "name": "Flussröhre", "hovertemplate": "Φ = %{surfacecolor:.2f}<extra></extra>"})
    frames = [{"name": f"{t[it]:.0f}", "data": [{"surfacecolor": v.round(1).tolist()} for v in werte(it)], "traces": [2, 3, 4, 5]}
              for it in bilder]
    schnitte = [schnitt(it).round(1).tolist() for it in bilder]
    q = netCDF4.Dataset(next(ordner.glob("*.out.nc")))
    tq = np.array(q["Grids/time"][:]); qq = np.array(q["Diagnostics/HeatFlux_st"][:, 0])
    laenge = float(np.sum(np.linalg.norm(np.diff(C, axis=0), axis=1)) * k)
    meta = {"form": ordner.name.replace("anim_", ""), "s0": s0, "iota": iota, "nfp": nfp, "a_m": a_m, "rho_mm": rho_mm,
            "box_m": [float(np.ptp(xg) * rho_mm / 1e3), float(np.ptp(yg) * rho_mm / 1e3)], "laenge_m": laenge,
            "pruef_R": pruef, "t": t[bilder].round(1).tolist(), "vmax": vmax,
            "sx": (xg * rho_mm / 10).round(2).tolist(), "sy": (yg * rho_mm / 10).round(2).tolist(), "tq": tq.round(1).tolist(), "qq": qq.round(3).tolist()}
    html.write_text(SEITE.replace("__PLOTLY__", PLOTLY).replace("__SPUREN__", json.dumps(spuren)).replace("__FRAMES__", json.dumps(frames)).replace("__SCHNITTE__", json.dumps(schnitte))
                    .replace("__META__", json.dumps(meta)))
    print(json.dumps({k_: v for k_, v in meta.items() if k_ not in ("t", "tq", "qq")}), "->", html, f"{html.stat().st_size/1e6:.1f} MB")


SEITE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Turbulenz in 3D</title>
<script src="__PLOTLY__"></script>
<script>if(!window.Plotly)document.write('<script src="plotly.min.js"><\/script>')</script>
<style>
:root{--bg:#fafaf8;--fg:#1d2329;--mut:#5b6670;--rand:#d9dde1;--karte:#fff}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#15181b;--fg:#e6e9ec;--mut:#9aa5b1;--rand:#30363c;--karte:#1d2125}}
:root[data-theme="dark"]{--bg:#15181b;--fg:#e6e9ec;--mut:#9aa5b1;--rand:#30363c;--karte:#1d2125}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
main{max-width:1200px;margin:0 auto;padding:16px}
h1{font-size:1.35rem;margin:.2rem 0}
.kasten{border:1px solid var(--rand);background:var(--karte);border-radius:8px;padding:10px 14px;margin:10px 0;font-size:.9rem}
.raster{display:grid;grid-template-columns:2fr 1fr;gap:12px}
@media (max-width:820px){.raster{grid-template-columns:1fr}}
#bild{height:640px}#fluss{height:240px}#schnitt{height:300px}
.mut{color:var(--mut)}
.steuer{display:flex;gap:10px;align-items:center;flex-wrap:wrap}#regler{flex:1;min-width:140px}
button{font:inherit;padding:4px 12px;border-radius:6px;border:1px solid var(--rand);background:var(--karte);color:var(--fg);cursor:pointer}
footer{font-size:.8rem;color:var(--mut);margin:16px 0}
</style></head><body><main>
<div class="kasten"><b>KI-generiert</b> (Claude Opus, 2026-11-11). Hobbyprojekt, nicht begutachtet. Rechnung: GX (Mandell et al., J. Plasma Phys. 2024, MIT-Lizenz).</div>
<h1>Turbulenz in einer Flussröhre, 3D</h1>
<p class="mut" id="unter"></p>
<div class="raster">
 <div><div id="bild"></div><div class="steuer"><button id="spiel">▶ Abspielen</button> <input id="regler" type="range" min="0" value="0" aria-label="Bild"> <span class="mut" id="zeit"></span></div></div>
 <div>
  <div id="fluss"></div>
  <div id="schnitt"></div>
  <div class="kasten" id="lesen"></div>
 </div>
</div>
<footer>KI-generiert. Annahmen: Gyroradius ρ<sub>i</sub> (Größe der Röhre in Metern), kleiner Radius a. Eine Feldlinie, adiabatische Elektronen.</footer>
</main>
<script>
const S=__SPUREN__, F=__FRAMES__, M=__META__, Q=__SCHNITTE__;
const dunkel=matchMedia('(prefers-color-scheme: dark)').matches&&document.documentElement.dataset.theme!=='light'||document.documentElement.dataset.theme==='dark';
const fg=dunkel?'#e6e9ec':'#1d2329', bg=dunkel?'#15181b':'#fafaf8';
document.getElementById('unter').textContent=`Form ${M.form} (Datensatzform unverändert, ${M.nfp} Feldperioden), Fläche s = ${M.s0}, Plasma skaliert auf a = ${M.a_m} m.`;
document.getElementById('lesen').innerHTML=`<b>Lesehilfe.</b> Grau durchscheinend: Plasmarand. Dunkle Linie: eine Magnetfeldlinie auf der Fläche s = ${M.s0}.
Die farbige Röhre (${M.laenge_m.toFixed(1)} m lang, Querschnitt ${M.box_m[0].toFixed(2)} × ${M.box_m[1].toFixed(2)} m) ist das Rechengebiet von GX: es folgt der Feldlinie einmal poloidal um das Plasma.
Farbe = elektrisches Potential Φ der Turbulenz auf der Röhrenwand: rot und blau sind Wirbel mit entgegengesetztem Drehsinn. Die Wirbel sind entlang des Feldes lang gestreckt und quer dazu schmal.
Sie tragen Wärme nach außen; rechts oben der Wärmefluss über die Zeit (roter Punkt = angezeigtes Bild), darunter ein Schnitt quer durch die Röhre: dort sieht man die Wirbel (einige cm groß) und senkrechte Streifen, die zonalen Strömungen, die die Wirbel zerscheren und so die Turbulenz bremsen.
Die Röhre läuft etwa ${(1/M.iota/M.nfp*M.nfp).toFixed(1)}-mal toroidal um, bis sie einmal poloidal herum ist (Rotationstransformation ι = ${M.iota.toFixed(3)}).<br><span class="mut">Größe der Röhre: Annahme ρ<sub>i</sub> = ${M.rho_mm} mm (T<sub>i</sub> 10 keV, B 5 T). Prüfung Mittellinie gegen GX: Abweichung ${(M.pruef_R*100).toFixed(1)} % im Radius. Anzeige entlang der Feldlinie verfeinert (GX rechnet 48 Punkte).</span>`;
const L={paper_bgcolor:bg,font:{color:fg},margin:{l:0,r:0,t:0,b:0},showlegend:false,
 scene:{aspectmode:'data',xaxis:{title:'x [m]',color:fg},yaxis:{title:'y [m]',color:fg},zaxis:{title:'z [m]',color:fg},camera:{eye:{x:1.2,y:1.2,z:0.7}}}};
const fertig=Plotly.newPlot('bild',S,L,{responsive:true,displaylogo:false});
const tr={x:M.tq,y:M.qq,type:'scatter',mode:'lines',line:{color:'#c0392b'},name:'Q_i'};
const pt={x:[M.t[M.t.length-1]],y:[0],type:'scatter',mode:'markers',marker:{size:9,color:'#c0392b'}};
function qBei(t){let i=M.tq.findIndex(v=>v>=t);return M.qq[i<0?M.qq.length-1:i];}
pt.y=[qBei(pt.x[0])];
const cfg={responsive:true,displayModeBar:false};
Plotly.newPlot('schnitt',[{type:'heatmap',x:M.sx,y:M.sy,z:Q[Q.length-1],zmin:-M.vmax,zmax:M.vmax,colorscale:'RdBu',reversescale:true,showscale:false,zsmooth:'best',
 hovertemplate:'Φ = %{z}<extra></extra>'}],{paper_bgcolor:bg,plot_bgcolor:bg,font:{color:fg,size:11},margin:{l:50,r:10,t:30,b:40},
 title:{text:'Querschnitt der Röhre (Außenseite, θ = 0)',font:{size:12}},xaxis:{title:'radial [cm]'},yaxis:{title:'quer zum Feld [cm]',scaleanchor:'x'}},cfg);
Plotly.newPlot('fluss',[tr,pt],{paper_bgcolor:bg,plot_bgcolor:bg,font:{color:fg,size:11},margin:{l:50,r:10,t:30,b:40},showlegend:false,
 title:{text:'Ionen-Wärmefluss Q_i/Q_GB',font:{size:12}},xaxis:{title:'Zeit t'},yaxis:{rangemode:'tozero'}},cfg);
const zeit=document.getElementById('zeit');
// eigener Abspieler: tauscht nur die Farben (surfacecolor) der vier Röhrenseiten
const regler=document.getElementById('regler'), knopf=document.getElementById('spiel');
regler.max=F.length-1;
let lauf=null, beschaeftigt=false;
function bildNr(i){
 const f=F[i], n=f.name; regler.value=i; zeit.textContent='t = '+n;
 if(beschaeftigt)return; beschaeftigt=true;
 Promise.all([Plotly.restyle('bild',{surfacecolor:f.data.map(d=>d.surfacecolor)},[2,3,4,5]),
  Plotly.restyle('fluss',{x:[[+n]],y:[[qBei(+n)]]},[1]),Plotly.restyle('schnitt',{z:[Q[i]]},[0])]).finally(()=>beschaeftigt=false);}
regler.oninput=()=>{stop();bildNr(+regler.value);};
function stop(){if(lauf){clearInterval(lauf);lauf=null;knopf.textContent='▶ Abspielen';}}
knopf.onclick=()=>{if(lauf){stop();return;}let i=+regler.value; if(i>=F.length-1)i=0;
 knopf.textContent='❚❚ Pause'; lauf=setInterval(()=>{if(beschaeftigt)return; bildNr(i); i++; if(i>=F.length)stop();},220);};
const start=+(new URLSearchParams(location.search).get('bild')??(F.length-1));
fertig.then(()=>bildNr(Math.min(Math.max(start,0),F.length-1)));
</script></body></html>"""

if __name__ == "__main__":
    main(sys.argv[1:])
