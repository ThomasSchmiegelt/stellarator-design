//
// KuehlSegment - geschlossenes Kuehlsegment der Gefaesswand mit Gyroid-Kern, Wasser-Ein- und -Austritt (PicoGK, headless).
//
// Auftrag (auftrag.json, von stellarator/kuehlsegment.py), alle Masse in mm:
//   laenge (x, Stroemungsrichtung), breite (y), kern (z, Dicke des Gyroid-Kerns)
//   haut_plasma (z unten, plasmaseitig), haut_hinten (z oben), haut_seite (Seiten- und Stirnwaende)
//   zelle, halbdicke   Gyroid-Schale |g| < t
//   kammer             gyroidfreie Verteilkammer an beiden Enden (speist beide Gyroid-Labyrinthe)
//   rohr_d, rohr_wand, rohr_l   Ein-/Austrittsrohr auf den Stirnseiten (x)
//   voxel, ausgabe
// Ausgabe: segment.stl (Stahl), wasser.stl (Fluidraum fuer FluidX3D), ergebnis.json.
//

using System.Numerics;
using System.Text.Json;
using PicoGK;

if (args.Length != 1)
{
    Console.Error.WriteLine("Aufruf: KuehlSegment <auftrag.json>");
    return 2;
}
var a = JsonSerializer.Deserialize<Auftrag>(File.ReadAllText(args[0]), new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
    ?? throw new InvalidDataException("Leerer Auftrag.");
Directory.CreateDirectory(a.ausgabe);

using Library lib = new(a.voxel);
float L = a.laenge, B = a.breite, K = a.kern, hs = a.haut_seite;

Voxels Quader(float x0, float y0, float z0, float x1, float y1, float z1)
    => new(Utils.mshCreateCube(lib, new BBox3(new Vector3(x0, y0, z0), new Vector3(x1, y1, z1))));

Voxels Zylinder(Vector3 p0, Vector3 p1, float r)
{
    Lattice lat = new(lib); lat.AddBeam(p0, p1, r, r, false); return new Voxels(lat);
}

// Innenraum (Wasser ohne Gyroid) und Aussenkontur
Voxels voxInnen = Quader(0, 0, 0, L, B, K);
Voxels voxAussen = Quader(-hs, -hs, -a.haut_plasma, L + hs, B + hs, K + a.haut_hinten);
float zm = K / 2, ym = B / 2, ri = a.rohr_d / 2, ra = ri + a.rohr_wand;
Vector3 vEin0 = new(-hs - a.rohr_l, ym, zm), vEin1 = new(0.5f, ym, zm);
Vector3 vAus0 = new(L - 0.5f, ym, zm), vAus1 = new(L + hs + a.rohr_l, ym, zm);
Voxels voxRohrAussen = Zylinder(vEin0, new Vector3(-hs / 2, ym, zm), ra).voxBoolAdd(Zylinder(new Vector3(L + hs / 2, ym, zm), vAus1, ra));
Voxels voxBohrung = Zylinder(vEin0 - new Vector3(1, 0, 0), vEin1, ri).voxBoolAdd(Zylinder(vAus0, vAus1 + new Vector3(1, 0, 0), ri));

// Gyroid nur im Kernbereich (ohne Verteilkammern)
Voxels voxKern = Quader(a.kammer, 0, 0, L - a.kammer, B, K);
voxKern.IntersectImplicit(new Gyroid(a.zelle, a.halbdicke));

Voxels voxSegment = voxAussen.voxBoolAdd(voxRohrAussen);
voxSegment.BoolSubtract(voxInnen);
voxSegment.BoolSubtract(voxBohrung);
voxSegment.BoolAdd(voxKern);

Voxels voxWasser = voxInnen.voxBoolAdd(voxBohrung);
voxWasser.BoolSubtract(voxKern);
// Rohrenden exakt abschneiden (Ein-/Austrittsflaeche eben)
voxWasser.BoolIntersect(Quader(vEin0.X, -hs, -a.haut_plasma, vAus1.X, B + hs, K + a.haut_hinten));

voxSegment.CalculateProperties(out float fVolStahl, out BBox3 oBox);
voxWasser.CalculateProperties(out float fVolWasser, out _);
voxKern.CalculateProperties(out float fVolKern, out _);
Mesh mshS = voxSegment.mshAsMesh(); mshS.SaveToStlFile(Path.Combine(a.ausgabe, "segment.stl"));
Mesh mshW = voxWasser.mshAsMesh(); mshW.SaveToStlFile(Path.Combine(a.ausgabe, "wasser.stl"));

var erg = new
{
    volumen_stahl_l = fVolStahl * 1e-6, volumen_wasser_l = fVolWasser * 1e-6,
    kerndichte = fVolKern / ((L - 2 * a.kammer) * B * K),
    bbox_mm = new[] { oBox.vecMin.X, oBox.vecMin.Y, oBox.vecMin.Z, oBox.vecMax.X, oBox.vecMax.Y, oBox.vecMax.Z },
    ein_mm = new[] { vEin0.X, vEin0.Y, vEin0.Z }, aus_mm = new[] { vAus1.X, vAus1.Y, vAus1.Z }, rohr_d_mm = a.rohr_d,
    dreiecke_segment = mshS.nTriangleCount(), dreiecke_wasser = mshW.nTriangleCount(),
};
File.WriteAllText(Path.Combine(a.ausgabe, "ergebnis.json"), JsonSerializer.Serialize(erg, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine($"FERTIG Stahl {fVolStahl * 1e-6:F1} l, Wasser {fVolWasser * 1e-6:F1} l, Kerndichte {erg.kerndichte:P0}");
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

record Auftrag(float laenge, float breite, float kern, float haut_plasma, float haut_hinten, float haut_seite,
               float zelle, float halbdicke, float kammer, float rohr_d, float rohr_wand, float rohr_l, float voxel, string ausgabe);
