"""freecad_vereinigen.py — Stahl (Gehaeuse + Verbinder + Keile) zu einem Koerper vereinigen (laeuft in freecadcmd).

  VSS_STAHL=<ordner mit stahl.step> <FreeCAD.AppImage> freecadcmd stellarator/freecad_vereinigen.py

Grund: Keil- und Gehaeuseschnitt am selben Wickelpaket erzeugen fast deckungsgleiche Flaechen; gmsh
meldet dann "overlapping facets", auch nach occ.fuse. OCC-Fuse in FreeCAD + removeSplitter (Refine)
fuehrt koplanare Teilflaechen zusammen. Ausgabe stahl_vereint.step.
"""
import os, time
import Part

ordner = os.environ["VSS_STAHL"]
t0 = time.time()
sh = Part.Shape(); sh.read(os.path.join(ordner, "stahl.step"))
sol = sh.Solids
print(f"VEREINIGEN {len(sol)} Solids", flush=True)
v = sol[0].multiFuse(sol[1:], 1e-4) if len(sol) > 1 else sol[0]
v = v.removeSplitter()
print(f"VEREINIGEN gueltig={v.isValid()} solids={len(v.Solids)} faces={len(v.Faces)} "
      f"volumen_m3={v.Volume * 1e-9:.2f} t={time.time() - t0:.0f}s", flush=True)
Part.Compound(v.Solids).exportStep(os.path.join(ordner, "stahl_vereint.step"))
print("VEREINIGEN_FERTIG")
