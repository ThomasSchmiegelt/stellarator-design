"""freecad_ansicht.py — Ansicht fuer ein headless gebautes FreeCAD-Modell nachtragen (laeuft in der FreeCAD-GUI).

  VSS_FCSTD=<gehaeuse.FCStd> <FreeCAD.AppImage> stellarator/freecad_ansicht.py      (braucht DISPLAY)

freecadcmd speichert keine GuiDocument.xml -> in der GUI ist dann alles ausgeblendet, nur der
Baum sichtbar. Dieses Skript schaltet Gehaeuse und Wickelpakete sichtbar (Farbe, Transparenz),
setzt die Ansicht, speichert das Modell und legt gehaeuse_freecad.png daneben; danach beendet es FreeCAD.
"""
import os
import FreeCAD as App
import FreeCADGui as Gui

pfad = os.environ["VSS_FCSTD"]
d = App.openDocument(pfad)
Gui.updateGui()
for o in d.Objects:
    vo = o.ViewObject
    if vo is None:
        continue
    gehaeuse, wp = o.Label.startswith("Gehaeuse_"), o.Label.startswith("Wickelpaket_")
    vo.Visibility = gehaeuse or wp
    if gehaeuse:
        vo.ShapeColor = (0.54, 0.61, 0.69); vo.Transparency = 0
    elif wp:
        vo.ShapeColor = (0.78, 0.46, 0.20); vo.Transparency = 0
v = Gui.ActiveDocument.ActiveView
v.setCameraType("Orthographic"); v.viewIsometric()
for _ in range(3):                         # erst nach dem Zeichnen stimmt die Huelle (sonst halb abgeschnitten)
    Gui.updateGui(); v.fitAll()
Gui.updateGui()
v.saveImage(os.path.join(os.path.dirname(pfad), "gehaeuse_freecad.png"), 1600, 1000, "White")
d.save()
App.closeDocument(d.Name)
Gui.getMainWindow().close()
