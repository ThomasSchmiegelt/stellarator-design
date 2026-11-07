//
// SpulenRohr - headless PicoGK: Spulen-Mittellinien -> Rohr mit Kreisquerschnitt (Lattice-Balken) -> Voxel
// -> Glaettung (TripleOffset: innen, doppelt aussen, innen) -> STL je Spule und Vereinigung.
// Auftrag (auftrag.json, von stellarator/k3_rohr.py): voxel_mm, radius_mm, glaett_mm, ausgabe, spulen[{name, punkte_mm[[x,y,z]]}]
// Ohne Library.Go() (kein Viewer, kein X-Display). Zahlen nur per JsonSerializer (Locale-unabhaengig).
//
using System.Diagnostics;
using System.Numerics;
using System.Text.Json;
using PicoGK;

if (args.Length != 1) { Console.Error.WriteLine("Aufruf: SpulenRohr <auftrag.json>"); return 2; }
var oOpts = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
Auftrag oA = JsonSerializer.Deserialize<Auftrag>(File.ReadAllText(args[0]), oOpts) ?? throw new InvalidDataException("Leerer Auftrag.");
Directory.CreateDirectory(oA.ausgabe);
var oUhr = Stopwatch.StartNew();
var oErg = new Dictionary<string, object>();
using Library lib = new(oA.voxel_mm);
Voxels voxAlle = new(lib);
var aSpulen = new List<Dictionary<string, object>>();
foreach (Spule oS in oA.spulen)
{
    Lattice lat = new(lib);
    int n = oS.punkte_mm.Length;
    for (int i = 0; i < n; i++)
    {
        float[] a = oS.punkte_mm[i], b = oS.punkte_mm[(i + 1) % n];
        lat.AddBeam(new Vector3(a[0], a[1], a[2]), new Vector3(b[0], b[1], b[2]), oA.radius_mm, oA.radius_mm, true);
    }
    Voxels voxRoh = new(lat);
    double tRoh = oUhr.Elapsed.TotalSeconds;
    Voxels voxGlatt = oA.glaett_mm > 0 ? voxRoh.voxTripleOffset(oA.glaett_mm) : new Voxels(voxRoh);
    double tGlatt = oUhr.Elapsed.TotalSeconds;
    voxGlatt.mshAsMesh().SaveToStlFile(Path.Combine(oA.ausgabe, $"{oS.name}_glatt.stl"));
    if (oA.roh_export) voxRoh.mshAsMesh().SaveToStlFile(Path.Combine(oA.ausgabe, $"{oS.name}_roh.stl"));
    voxAlle.BoolAdd(voxGlatt);
    aSpulen.Add(new Dictionary<string, object> { ["name"] = oS.name, ["punkte"] = n, ["t_voxel_s"] = tRoh, ["t_glatt_s"] = tGlatt });
    Console.WriteLine($"{oS.name} fertig");
}
voxAlle.mshAsMesh().SaveToStlFile(Path.Combine(oA.ausgabe, "alle_glatt.stl"));
oErg["spulen"] = aSpulen; oErg["zeit_s"] = oUhr.Elapsed.TotalSeconds; oErg["voxel_mm"] = oA.voxel_mm;
oErg["radius_mm"] = oA.radius_mm; oErg["glaett_mm"] = oA.glaett_mm;
File.WriteAllText(Path.Combine(oA.ausgabe, "ergebnis_picogk.json"), JsonSerializer.Serialize(oErg, new JsonSerializerOptions { WriteIndented = true }));
return 0;

record Spule(string name, float[][] punkte_mm);
record Auftrag(float voxel_mm, float radius_mm, float glaett_mm, string ausgabe, bool roh_export, Spule[] spulen);
