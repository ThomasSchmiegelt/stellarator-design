"""paraview_feldlinien.py — ParaView-Ansicht: Gehaeusespannung (Elmer) + Magnetfeldlinien (Biot-Savart).

  STRUKTUR=<elmer .vtu> FELD=<feldlinien.vtm> [N_SPULEN=70] [PNG=<bild>] paraview --script=stellarator/paraview_feldlinien.py
  (mit pvbatch statt paraview nur Bild, ohne Fenster)

Elmer-Ergebnis: Gehaeuse (GeometryIds = n+1) nach von Mises [MPa], halbiert (Schnitt y = 0), damit die
Feldlinien sichtbar sind; Wickelpakete kupferfarben. Feldlinien aus stellarator.ansicht (Flussflaechen,
Farbe |B|) als Rohre. Zusaetzlich, ausgeblendet: Feldlinien direkt aus dem Elmer-Feld (StreamTracer),
zum Vergleich im Pipeline-Browser einschalten.
"""
import os
from paraview.simple import *

n = int(os.environ.get("N_SPULEN", "70"))
erg = XMLUnstructuredGridReader(registrationName="Elmer", FileName=[os.environ["STRUKTUR"]])
mpa = Calculator(registrationName="vonMises_MPa", Input=erg); mpa.ResultArrayName = "vonMises_MPa"; mpa.Function = "vonmises/1e6"

def teil(name, lo, hi):
    t = Threshold(registrationName=name, Input=mpa)
    t.Scalars = ["CELLS", "GeometryIds"]; t.LowerThreshold = lo; t.UpperThreshold = hi
    c = Clip(registrationName=name + " (Schnitt)", Input=t)
    c.ClipType = "Plane"; c.ClipType.Origin = [0, 0, 0]; c.ClipType.Normal = [0, 1, 0]
    return c

gehaeuse = teil("Gehaeuse", n + 1, n + 1)
wp = teil("Wickelpakete", 1, n)
feld = XMLMultiBlockDataReader(registrationName="Feldlinien", FileName=[os.environ["FELD"]])
linien = ExtractBlock(registrationName="Linien", Input=feld); linien.Selectors = ["/Root/feldlinien"]
rohr = Tube(registrationName="Feldlinien (Rohre)", Input=linien); rohr.Scalars = ["POINTS", "B_T"]; rohr.Radius = 0.012

# Vergleich: Feldlinien direkt aus dem Elmer-Feld, Startpunkte auf einer Linie durch das Plasma bei phi = 0
st = StreamTracer(registrationName="Feldlinien Elmer (Vergleich)", Input=erg, SeedType="Line")
st.Vectors = ["POINTS", "magnetic flux density"]; st.SeedType.Point1 = [5.45, 0, 0]; st.SeedType.Point2 = [6.2, 0, 0]
st.SeedType.Resolution = 6; st.MaximumStreamlineLength = 400.0; st.IntegrationDirection = "FORWARD"

v = GetActiveViewOrCreate("RenderView")
v.Background = [1, 1, 1]
try:
    v.UseColorPaletteForBackground = 0
except AttributeError:
    pass
v.OrientationAxesVisibility = 0
d = Show(gehaeuse, v); ColorBy(d, ("POINTS", "vonMises_MPa"))
lut = GetColorTransferFunction("vonMises_MPa"); lut.ApplyPreset("Turbo", True); lut.RescaleTransferFunction(0.0, 50.0)
bar = GetScalarBar(lut, v); bar.Title = "von Mises Gehaeuse [MPa]"; bar.ComponentTitle = ""; bar.TitleColor = [0, 0, 0]; bar.LabelColor = [0, 0, 0]
d.SetScalarBarVisibility(v, True)
d = Show(wp, v); ColorBy(d, None); d.AmbientColor = d.DiffuseColor = [0.78, 0.46, 0.20]
d = Show(rohr, v); ColorBy(d, ("POINTS", "B_T"))
lb = GetColorTransferFunction("B_T"); lb.ApplyPreset("Cool to Warm", True)
bar = GetScalarBar(lb, v); bar.Title = "|B| Feldlinien [T]"; bar.ComponentTitle = ""; bar.TitleColor = [0, 0, 0]; bar.LabelColor = [0, 0, 0]
bar.WindowLocation = "Upper Right Corner"
d.SetScalarBarVisibility(v, True)
Hide(st, v)
v.CameraPosition = [9.0, -16.0, 10.0]; v.CameraFocalPoint = [0, 0, 0]; v.CameraViewUp = [0, 0, 1]
v.ResetCamera(); v.CameraParallelProjection = 0
Render(v)
if os.environ.get("PNG"):
    SaveScreenshot(os.environ["PNG"], v, ImageResolution=[1800, 1100])
