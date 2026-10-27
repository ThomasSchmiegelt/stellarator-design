//
// SegmentErstwand - Kuehlsegment mit eigenem Erstwand-Spalt hinter der Plasmaseite (PicoGK, headless).
// Variante zu SegmentKuehlung: Wasser fliesst NICHT durch den Gyroid-Kern, sondern durch einen schmalen Spalt
// direkt hinter der Innenhaut; der Gyroid-Kern bleibt geschlossene Tragstruktur.
//
// Auftrag (auftrag.json, von stellarator/kuehlung_erstwand.py), Masse in mm, Abstaende d_* vom Plasmarand:
//   d_innen, d_aussen       Wand (Innen- und Aussenseite)
//   d_haut_i, d_haut_a      Wasserraum der Kammern (ohne Haeute)
//   d_spalt                 Ende des Erstwand-Spalts (d_haut_i .. d_spalt ist Wasser)
//   d_vor                   Tiefe der Vorkammer hinter dem Lochblech
//   d_kern, d_vor_kern      Beginn des Kernhohlraums (hinter Trennblech) bzw. hinter der Vorkammer
//   keil_*                  segment, kin (Verteilkammer), platte, vor (Vorkammer), spalt, kern, kaus (Sammelkammer)
//   zelle, halbdicke, loecher [[x0,y0,z0,x1,y1,z1,r]], rohre [[x0,y0,z0,x1,y1,z1,r_i,wand]], voxel, ausgabe
// Wasser = Raum.kin + Loecher + Schicht(haut_i..vor).vor + Schicht(haut_i..spalt).spalt + Raum.kaus + Bohrungen
// Stahl  = Wand + Rohre - Wasser - Kernhohlraum + Gyroid(Kernhohlraum)
//

using System.Diagnostics;
using System.Numerics;
using System.Text.Json;
using PicoGK;

if (args.Length != 1) { Console.Error.WriteLine("Aufruf: SegmentErstwand <auftrag.json>"); return 2; }
Auftrag a = JsonSerializer.Deserialize<Auftrag>(File.ReadAllText(args[0]), new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
    ?? throw new InvalidDataException("Leerer Auftrag.");
Directory.CreateDirectory(a.ausgabe);
var oUhr = Stopwatch.StartNew();
var oZeiten = new Dictionary<string, double>();
void Messe(string s) { oZeiten[s] = oUhr.Elapsed.TotalSeconds; oUhr.Restart(); Console.WriteLine($"  {s} {oZeiten[s]:F1} s"); }

using Library lib = new(a.voxel);
Voxels Lade(string p) => new(Mesh.mshFromStlFile(p, Mesh.EStlUnit.MM, libSet: lib));
Voxels Zylinder(float[] b, float r)
{
    Lattice lat = new(lib);
    lat.AddBeam(new Vector3(b[0], b[1], b[2]), new Vector3(b[3], b[4], b[5]), r, r, false);
    return new Voxels(lat);
}

Voxels voxP = Lade(a.plasma_stl);
var K = new Dictionary<string, Voxels>();
foreach (var k in new[] { "segment", "kin", "platte", "vor", "spalt", "kern", "kaus" }) K[k] = Lade(Path.Combine(Path.GetDirectoryName(a.plasma_stl)!, $"keil_{k}.stl"));
Messe("einlesen");

var O = new Dictionary<float, Voxels>();
Voxels Off(float d) { if (!O.ContainsKey(d)) O[d] = voxP.voxOffset(d); return O[d]; }
Voxels Schicht(float d0, float d1, string keil) { var v = Off(d1).voxBoolSubtract(Off(d0)); v.BoolIntersect(K[keil]); return v; }

Voxels voxWand = Schicht(a.d_innen, a.d_aussen, "segment");
Voxels voxWasser = Schicht(a.d_haut_i, a.d_haut_a, "kin");
voxWasser.BoolAdd(Schicht(a.d_haut_i, a.d_haut_a, "kaus"));
voxWasser.BoolAdd(Schicht(a.d_haut_i, a.d_vor, "vor"));
voxWasser.BoolAdd(Schicht(a.d_haut_i, a.d_spalt, "spalt"));
Messe("schichten");

Voxels voxLoecher = new(lib);
foreach (var l in a.loecher) voxLoecher.BoolAdd(Zylinder(l, l[6]));
voxLoecher.BoolIntersect(Schicht(a.d_haut_i, a.d_haut_a, "platte"));
voxWasser.BoolAdd(voxLoecher);
Voxels voxRohre = new(lib), voxBohrungen = new(lib);
foreach (var r in a.rohre) { voxRohre.BoolAdd(Zylinder(r, r[6] + r[7])); voxBohrungen.BoolAdd(Zylinder(r, r[6])); }
voxWasser.BoolAdd(voxBohrungen);

// Kernhohlraum hinter dem Trennblech, ausserhalb der Vorkammer; darin das Gyroid
Voxels voxHohl = Schicht(a.d_kern, a.d_haut_a, "kern");
voxHohl.BoolSubtract(Schicht(0f, a.d_vor_kern, "vor"));
Voxels voxGyroid = new(voxHohl);
voxGyroid.IntersectImplicit(new Gyroid(a.zelle, a.halbdicke));
Messe("loecher+kern");

Voxels voxStahl = voxWand.voxBoolAdd(voxRohre);
voxStahl.BoolSubtract(voxWasser);
voxStahl.BoolSubtract(voxHohl);
voxStahl.BoolAdd(voxGyroid);
Messe("bool");

voxStahl.CalculateProperties(out float fVolStahl, out BBox3 oBox);
voxWasser.CalculateProperties(out float fVolWasser, out BBox3 oBoxW);
Mesh mshS = voxStahl.mshAsMesh(); mshS.SaveToStlFile(Path.Combine(a.ausgabe, "stahl.stl"));
Mesh mshW = voxWasser.mshAsMesh(); mshW.SaveToStlFile(Path.Combine(a.ausgabe, "wasser.stl"));
Messe("export");
var oErg = new
{
    volumen_stahl_m3 = fVolStahl * 1e-9, volumen_wasser_m3 = fVolWasser * 1e-9,
    bbox_wasser_mm = new[] { oBoxW.vecMin.X, oBoxW.vecMin.Y, oBoxW.vecMin.Z, oBoxW.vecMax.X, oBoxW.vecMax.Y, oBoxW.vecMax.Z },
    dreiecke_stahl = mshS.nTriangleCount(), dreiecke_wasser = mshW.nTriangleCount(), zeiten_s = oZeiten,
};
File.WriteAllText(Path.Combine(a.ausgabe, "ergebnis.json"), JsonSerializer.Serialize(oErg, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine($"FERTIG Stahl {fVolStahl * 1e-9:F2} m3, Wasser {fVolWasser * 1e-9:F2} m3");
return 0;

class Gyroid(float fZelle, float fHalbDicke) : IImplicit
{
    readonly float fK = 2f * MathF.PI / fZelle;
    public float fSignedDistance(in Vector3 v)
    {
        float x = v.X * fK, y = v.Y * fK, z = v.Z * fK;
        float g = MathF.Sin(x) * MathF.Cos(y) + MathF.Sin(y) * MathF.Cos(z) + MathF.Sin(z) * MathF.Cos(x);
        return MathF.Abs(g) / (1.5f * fK) - fHalbDicke;
    }
}

record Auftrag(string plasma_stl, float d_innen, float d_aussen, float d_haut_i, float d_haut_a, float d_spalt, float d_vor,
               float d_kern, float d_vor_kern, float zelle, float halbdicke, float[][] loecher, float[][] rohre, float voxel, string ausgabe);
