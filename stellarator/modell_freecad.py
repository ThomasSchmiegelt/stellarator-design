# Aufruf: FreeCAD_1.1.4.AppImage freecadcmd modell_freecad.py -- <ordner> <titel>   (Umgebungsvariablen MODELL_DIR, MODELL_TITEL)
import os, FreeCAD, Mesh
d = os.environ["MODELL_DIR"]; titel = os.environ["MODELL_TITEL"]
doc = FreeCAD.newDocument(titel)
for nm, farbe, transp in (("plasma", (1.0, 0.35, 0.15), 50), ("gefaess", (0.6, 0.6, 0.6), 60), ("spulen", (0.72, 0.45, 0.2), 0)):
    o = doc.addObject("Mesh::Feature", nm.capitalize())
    m = Mesh.Mesh(os.path.join(d, nm + ".stl")); mat = FreeCAD.Matrix(); mat.scale(1000.0, 1000.0, 1000.0); m.transform(mat)   # m -> mm (FreeCAD-Einheit)
    o.Mesh = m
    o.Label = {"plasma": "Plasma (LCFS)", "gefaess": "Gefaess (ANNAHME 0,15-0,25 m)", "spulen": "Spulenrohre"}[nm]
    if FreeCAD.GuiUp is False:
        pass
    # Darstellungsfarben werden in der Datei nur mit GUI gespeichert; Fallback: Eigenschaften in Label/Doku
    try:
        o.ViewObject.ShapeColor = farbe; o.ViewObject.Transparency = transp
    except Exception:
        pass
doc.Comment = "Netze von m nach mm skaliert (FreeCAD-Standard). Gefaess 0,15-0,25 m ueber Plasma ist ANNAHME."
doc.recompute(); doc.saveAs(os.path.join(d, titel + ".FCStd")); print("gespeichert", os.path.join(d, titel + ".FCStd"))

# Farben: im Konsolenmodus gibt es keine ViewObjects -> GuiDocument.xml von Hand ergaenzen (Format wie FreeCAD-GUI,
# ShapeColor als RGBA-Ganzzahl, Transparency in Prozent). Ohne GUI nicht pruefbar.
import zipfile, shutil
pfad = os.path.join(d, titel + ".FCStd"); tmp = pfad + ".tmp"
def rgba(r, g, b): return (int(r * 255) << 24) | (int(g * 255) << 16) | (int(b * 255) << 8) | 255
vp = ""
for nm, farbe, tr in (("Plasma", (1.0, 0.35, 0.15), 50), ("Gefaess", (0.6, 0.6, 0.6), 60), ("Spulen", (0.72, 0.45, 0.2), 0)):
    vp += ('<ViewProvider name="%s" expanded="0"><Properties Count="3" TransientCount="0">'
           '<Property name="ShapeColor" type="App::PropertyColor" status="1"><PropertyColor value="%d"/></Property>'
           '<Property name="Transparency" type="App::PropertyPercent" status="1"><Integer value="%d"/></Property>'
           '<Property name="Visibility" type="App::PropertyBool" status="1"><Bool value="true"/></Property>'
           '</Properties></ViewProvider>') % (nm, rgba(*farbe), tr)
gui = '<?xml version="1.0" encoding="utf-8"?><Document SchemaVersion="1" HasExpansion="1"><Expand/><ViewProviderData Count="3">%s</ViewProviderData></Document>' % vp
with zipfile.ZipFile(pfad) as zi, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
    for it in zi.infolist(): zo.writestr(it, zi.read(it.filename))
    zo.writestr("GuiDocument.xml", gui)
shutil.move(tmp, pfad)
