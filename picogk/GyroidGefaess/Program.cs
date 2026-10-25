//
// GyroidGefaess - Plasmagefaess-Sektor mit Gyroid-Kuehlkern (PicoGK, headless).
//
// Auftrag (auftrag.json, von stellarator/gyroid_gefaess.py):
//   plasma_stl   geschlossener Plasma-Sektor (mm, etwas laenger als der Keil)
//   keil_stl     Keil, der den Sektor in phi zuschneidet (mm)
//   spalt_mm     Abstand Plasma -> Innenhaut, wand_mm Wanddicke gesamt
//   haut_innen_mm / haut_aussen_mm  geschlossene Haeute (erste Wand / Aussenwand)
//   zelle_mm, halbdicke_mm          Gyroid-Kern (Schale |g| < t)
//   voxel_mm, ausgabe
// Wand = Offset(Plasma, spalt+wand) - Offset(Plasma, spalt); Kern = Wand ohne Haeute, geschnitten mit Gyroid.
// Ausgabe: gefaess.stl (Haeute + Kern), kern.stl, ergebnis.json (Volumina, Oberflaeche).
//

using System.Diagnostics;
using System.Numerics;
using System.Text.Json;
using PicoGK;

if (args.Length != 1)
{
    Console.Error.WriteLine("Aufruf: GyroidGefaess <auftrag.json>");
    return 2;
}

var oOpts = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
Auftrag a = JsonSerializer.Deserialize<Auftrag>(File.ReadAllText(args[0]), oOpts)
    ?? throw new InvalidDataException("Leerer Auftrag.");
Directory.CreateDirectory(a.ausgabe);
var oUhr = Stopwatch.StartNew();
var oZeiten = new Dictionary<string, double>();
void Messe(string s) { oZeiten[s] = oUhr.Elapsed.TotalSeconds; oUhr.Restart(); Console.WriteLine($"  {s} {oZeiten[s]:F1} s"); }

using Library lib = new(a.voxel_mm);
Voxels voxPlasma = new(Mesh.mshFromStlFile(a.plasma_stl, Mesh.EStlUnit.MM, libSet: lib));
Voxels voxKeil = new(Mesh.mshFromStlFile(a.keil_stl, Mesh.EStlUnit.MM, libSet: lib));
Messe("einlesen");

float s = a.spalt_mm, w = a.wand_mm;
Voxels voxInnen = voxPlasma.voxOffset(s);                       // Innenseite der Wand
Voxels voxAussen = voxPlasma.voxOffset(s + w);                  // Aussenseite der Wand
Voxels voxWand = voxAussen.voxBoolSubtract(voxInnen);
Voxels voxKernRaum = voxPlasma.voxOffset(s + w - a.haut_aussen_mm);
voxKernRaum.BoolSubtract(voxPlasma.voxOffset(s + a.haut_innen_mm));
Voxels voxHaeute = voxWand.voxBoolSubtract(voxKernRaum);
Messe("offsets");

Voxels voxKern = new(voxKernRaum);
voxKern.IntersectImplicit(new Gyroid(a.zelle_mm, a.halbdicke_mm));
Messe("gyroid");

Voxels voxGefaess = voxHaeute.voxBoolAdd(voxKern);
voxGefaess.BoolIntersect(voxKeil);
voxKern.BoolIntersect(voxKeil);
voxWand.BoolIntersect(voxKeil);
Messe("zuschnitt");

voxGefaess.CalculateProperties(out float fVolGef, out BBox3 oBox);
voxKern.CalculateProperties(out float fVolKern, out _);
voxWand.CalculateProperties(out float fVolWand, out _);
Mesh mshGef = voxGefaess.mshAsMesh();
mshGef.SaveToStlFile(Path.Combine(a.ausgabe, "gefaess.stl"));
voxKern.mshAsMesh().SaveToStlFile(Path.Combine(a.ausgabe, "kern.stl"));
Messe("export");

var oErg = new
{
    volumen_wand_m3 = fVolWand * 1e-9, volumen_stahl_m3 = fVolGef * 1e-9, volumen_kern_stahl_m3 = fVolKern * 1e-9,
    stahlanteil_wand = fVolGef / fVolWand, dreiecke = mshGef.nTriangleCount(),
    bbox_mm = new[] { oBox.vecMin.X, oBox.vecMin.Y, oBox.vecMin.Z, oBox.vecMax.X, oBox.vecMax.Y, oBox.vecMax.Z },
    zeiten_s = oZeiten,
};
File.WriteAllText(Path.Combine(a.ausgabe, "ergebnis.json"),
    JsonSerializer.Serialize(oErg, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine($"FERTIG Wand {fVolWand * 1e-9:F2} m3, Stahl {fVolGef * 1e-9:F2} m3 ({fVolGef / fVolWand:P0}), {mshGef.nTriangleCount()} Dreiecke");
return 0;

// Gyroid-Schale |g| < t (wie GitterZelle)
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

record Auftrag(string plasma_stl, string keil_stl, float spalt_mm, float wand_mm, float haut_innen_mm,
               float haut_aussen_mm, float zelle_mm, float halbdicke_mm, float voxel_mm, string ausgabe);
