//
// ModellAnsicht - zeigt ein Stellarator-Modell (Plasma, Gefaess, Spulenrohre) im PicoGK-Viewer (mit Fenster).
//   dotnet run -c Release -- <modell_ordner> [<titel>]
// Erwartet <modell_ordner>/plasma.stl, gefaess.stl, spulen.stl in Metern (stellarator/modell_bauen.py).
// Gruppen: 0 Plasma (orange-rot), 1 Gefaess (grau, halbtransparent), 2 Spulen (kupfer).
// Bedienung im Viewer: Maus ziehen = drehen, Rad = zoomen. Nur Ansicht, keine Voxel-Operationen.
//
using PicoGK;

if (args.Length < 1) { Console.Error.WriteLine("Aufruf: ModellAnsicht <modell_ordner> [<titel>]"); return 2; }
string strOrdner = args[0];
string strTitel = args.Length > 1 ? args[1] : Path.GetFileName(strOrdner.TrimEnd('/'));

void Zeige()
{
    var oV = Library.oViewer();
    (string datei, int gruppe)[] aTeile = { ("plasma.stl", 0), ("gefaess.stl", 1), ("spulen.stl", 2) };
    foreach (var (datei, gruppe) in aTeile)
    {
        string p = Path.Combine(strOrdner, datei);
        if (!File.Exists(p)) { Library.Log($"fehlt: {p}"); continue; }
        Mesh m = Mesh.mshFromStlFile(p, Mesh.EStlUnit.M);
        Library.Log($"{datei}: {m.nTriangleCount()} Dreiecke");
        oV.Add(m, gruppe);
    }
    oV.SetGroupMaterial(0, new ColorFloat(0.92f, 0.40f, 0.20f, 1.0f), 0.0f, 0.6f);
    oV.SetGroupMaterial(1, new ColorFloat(0.65f, 0.65f, 0.68f, 0.35f), 0.2f, 0.5f);
    oV.SetGroupMaterial(2, new ColorFloat(0.78f, 0.47f, 0.25f, 1.0f), 0.8f, 0.35f);
}

Library.Go(5.0f, Zeige, strWindowTitle: $"PicoGK - {strTitel}");
return 0;
