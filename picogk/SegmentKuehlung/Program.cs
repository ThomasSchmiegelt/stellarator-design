//
// SegmentKuehlung - ein Segment der Gefaesswand mit Gyroid-Kern als durchstroemtes Kuehlsegment (PicoGK, headless).
//
// Auftrag (auftrag.json, von stellarator/kuehlung_segment.py), Masse in mm:
//   plasma_stl            geschlossener Plasma-Sektor (laenger als das Segment)
//   keil_segment          Segment phi0..phi1; keil_kern Gyroid-Bereich; keil_ende0/1 Stirnplatten; keil_platte Lochblech
//   spalt, wand           Wand = Offset(Plasma, spalt+wand) - Offset(Plasma, spalt)
//   haut_innen, haut_aussen   Wasserraum = Wand ohne die Haeute
//   zelle, halbdicke      Gyroid-Schale |g| < t
//   loecher               [[x0,y0,z0, x1,y1,z1, r], ...]  Bohrungen im Lochblech
//   schicht, zelle_vorn, halbdicke_vorn   optional: abgestufter Kern, vorn (Plasmaseite) feinere Zelle
//   flaechen_stl                          optional: {spalt, haut_innen, haut_aussen, wand} als exakte Netze
//   vorn_stl                              optional: Grenze der feinen Schicht als geschlossenes Netz
//   halbdicke_vorn_R                      optional: [[R_mm, halbdicke_mm], ...] Wanddicke vorn ueber dem Radius (linear)
//   mit_platte            false: kein Lochblech, Ringkammern flaechig offen zum Gyroid-Kern
//   rohre                 [[x0,y0,z0, x1,y1,z1, r_innen, wand], ...]  Ein- und Austrittsrohr (Achse von innen nach aussen)
//   voxel, ausgabe
// Wasser = Wasserraum - Stirnplatten - Lochblech(ohne Loecher) - Gyroid + Rohrbohrungen
// Stahl  = (Wand + Rohre) - Wasser
// Ausgabe: stahl.stl, wasser.stl, ergebnis.json
//

using System.Diagnostics;
using System.Numerics;
using System.Text.Json;
using PicoGK;

if (args.Length != 1)
{
    Console.Error.WriteLine("Aufruf: SegmentKuehlung <auftrag.json>");
    return 2;
}
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

Voxels voxPlasma = Lade(a.plasma_stl);
Voxels voxSeg = Lade(a.keil_segment), voxKernKeil = Lade(a.keil_kern), voxPlatteKeil = Lade(a.keil_platte);
Voxels voxEnden = Lade(a.keil_ende0).voxBoolAdd(Lade(a.keil_ende1));
Messe("einlesen");

// Versatzflaechen bevorzugt als exakte Netze aus Python (flaechen_stl); voxOffset ist an starker Kruemmung ungenau
Voxels Versatz(string k, float d) => a.flaechen_stl is not null && a.flaechen_stl.TryGetValue(k, out var p) ? Lade(p) : voxPlasma.voxOffset(d);
Voxels voxWand = Versatz("wand", a.spalt + a.wand).voxBoolSubtract(Versatz("spalt", a.spalt));
voxWand.BoolIntersect(voxSeg);
Voxels voxRaum = Versatz("haut_aussen", a.spalt + a.wand - a.haut_aussen).voxBoolSubtract(Versatz("haut_innen", a.spalt + a.haut_innen));
voxRaum.BoolIntersect(voxSeg);
Messe("offsets");

// Lochblech: Platte im Wasserraum, Bohrungen frei
Voxels voxLoecher = new(lib);
foreach (var l in a.loecher) voxLoecher.BoolAdd(Zylinder(l, l[6]));
// ohne Lochblech (mit_platte = false): Ringkammer flaechig offen zum Gyroid-Kern
Voxels voxPlatte = a.mit_platte ? voxRaum.voxBoolIntersect(voxPlatteKeil) : new Voxels(lib);
if (a.mit_platte) voxPlatte.BoolSubtract(voxLoecher);
// Gyroid-Kern
Voxels voxKern = voxRaum.voxBoolIntersect(voxKernKeil);
if (a.schicht > 0)
{
    // abgestuft: vorn (Plasmaseite, Tiefe schicht) feine Zelle, dahinter grobe/dichte Zelle
    // Grenze bevorzugt als exakte Versatzflaeche aus Python (vorn_stl); voxOffset ueber ~0,3 m ist an starker Kruemmung zu kurz
    Voxels voxGrenze = a.vorn_stl is not null ? Lade(a.vorn_stl) : voxPlasma.voxOffset(a.spalt + a.haut_innen + a.schicht);
    Voxels voxVorn = voxKern.voxBoolIntersect(voxGrenze);
    voxKern.BoolSubtract(voxVorn);
    voxVorn.IntersectImplicit(new Gyroid(a.zelle_vorn, a.halbdicke_vorn, a.halbdicke_vorn_R));
    voxKern.IntersectImplicit(new Gyroid(a.zelle, a.halbdicke));
    voxKern.BoolAdd(voxVorn);
}
else voxKern.IntersectImplicit(new Gyroid(a.zelle, a.halbdicke));
Messe("platte+gyroid");

Voxels voxRohre = new(lib), voxBohrungen = new(lib);
foreach (var r in a.rohre)
{
    voxRohre.BoolAdd(Zylinder(r, r[6] + r[7]));
    voxBohrungen.BoolAdd(Zylinder(r, r[6]));
}
Voxels voxWasser = voxRaum.voxBoolSubtract(voxEnden);
voxWasser.BoolSubtract(voxPlatte);
voxWasser.BoolSubtract(voxKern);
voxWasser.BoolAdd(voxBohrungen);
Voxels voxStahl = voxWand.voxBoolAdd(voxRohre);
voxStahl.BoolSubtract(voxWasser);
Messe("bool");

voxStahl.CalculateProperties(out float fVolStahl, out BBox3 oBox);
voxWasser.CalculateProperties(out float fVolWasser, out BBox3 oBoxW);
voxKern.CalculateProperties(out float fVolKern, out _);
Mesh mshS = voxStahl.mshAsMesh(); mshS.SaveToStlFile(Path.Combine(a.ausgabe, "stahl.stl"));
Mesh mshW = voxWasser.mshAsMesh(); mshW.SaveToStlFile(Path.Combine(a.ausgabe, "wasser.stl"));
// Belegung je Voxel fuer FluidX3D (statt dort das Netz zu voxelisieren: dessen Strahlverfahren kippt einzelne
// Lagen an waagerecht gestreiften Flaechen, f6-f9 Sperrschicht bei z = +-1,9 m). Kopf: Ursprung/Groesse [Voxel],
// Ursprung [mm], Voxel [mm]; dann je z-Schicht x-schnellste Bytes (1 = Wasser).
{
    voxWasser.GetVoxelDimensions(out int nX0, out int nY0, out int nZ0, out int nXs, out int nYs, out int nZs);
    Vector3 vecO = lib.vecVoxelsToMm(nX0, nY0, nZ0);
    using var oBin = new BinaryWriter(File.Create(Path.Combine(a.ausgabe, "wasser_belegung.bin")));
    foreach (int n in new[] { nX0, nY0, nZ0, nXs, nYs, nZs }) oBin.Write(n);
    oBin.Write(vecO.X); oBin.Write(vecO.Y); oBin.Write(vecO.Z); oBin.Write(a.voxel);
    ImageGrayScale img = new(nXs, nYs);
    byte[] abZeile = new byte[nXs * nYs];
    for (int z = 0; z < nZs; z++)
    {
        voxWasser.GetVoxelSlice(z, ref img);
        for (int y = 0; y < nYs; y++) for (int x = 0; x < nXs; x++) abZeile[x + y * nXs] = img.fValue(x, nYs - 1 - y) <= 0f ? (byte)1 : (byte)0; // Bildzeile 0 = groesstes y
        oBin.Write(abZeile);
    }
}
Messe("export");

var oErg = new
{
    volumen_stahl_m3 = fVolStahl * 1e-9, volumen_wasser_m3 = fVolWasser * 1e-9, volumen_kern_stahl_m3 = fVolKern * 1e-9,
    bbox_stahl_mm = new[] { oBox.vecMin.X, oBox.vecMin.Y, oBox.vecMin.Z, oBox.vecMax.X, oBox.vecMax.Y, oBox.vecMax.Z },
    bbox_wasser_mm = new[] { oBoxW.vecMin.X, oBoxW.vecMin.Y, oBoxW.vecMin.Z, oBoxW.vecMax.X, oBoxW.vecMax.Y, oBoxW.vecMax.Z },
    dreiecke_stahl = mshS.nTriangleCount(), dreiecke_wasser = mshW.nTriangleCount(), zeiten_s = oZeiten,
};
File.WriteAllText(Path.Combine(a.ausgabe, "ergebnis.json"), JsonSerializer.Serialize(oErg, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine($"FERTIG Stahl {fVolStahl * 1e-9:F2} m3, Wasser {fVolWasser * 1e-9:F2} m3");
return 0;

class Gyroid(float fZelle, float fHalbDicke, float[][]? aDickeR = null) : IImplicit
{
    readonly float fK = 2f * MathF.PI / fZelle;
    public float fSignedDistance(in Vector3 v)
    {
        float x = v.X * fK, y = v.Y * fK, z = v.Z * fK;
        float g = MathF.Sin(x) * MathF.Cos(y) + MathF.Sin(y) * MathF.Cos(z) + MathF.Sin(z) * MathF.Cos(x);
        return MathF.Abs(g) / (1.5f * fK) - fDicke(MathF.Sqrt(v.X * v.X + v.Y * v.Y));
    }

    // Halbdicke ueber dem Radius: linear zwischen den Stuetzstellen, ausserhalb konstant
    float fDicke(float fR)
    {
        if (aDickeR is null || aDickeR.Length == 0) return fHalbDicke;
        if (fR <= aDickeR[0][0]) return aDickeR[0][1];
        for (int i = 1; i < aDickeR.Length; i++)
            if (fR <= aDickeR[i][0])
            {
                float t = (fR - aDickeR[i - 1][0]) / (aDickeR[i][0] - aDickeR[i - 1][0]);
                return aDickeR[i - 1][1] + t * (aDickeR[i][1] - aDickeR[i - 1][1]);
            }
        return aDickeR[^1][1];
    }
}

record Auftrag(string plasma_stl, string keil_segment, string keil_kern, string keil_ende0, string keil_ende1, string keil_platte,
               float spalt, float wand, float haut_innen, float haut_aussen, float zelle, float halbdicke,
               float[][] loecher, float[][] rohre, float voxel, string ausgabe, bool mit_platte = true,
               float schicht = 0, float zelle_vorn = 0, float halbdicke_vorn = 0, float[][]? halbdicke_vorn_R = null, string? vorn_stl = null, Dictionary<string, string>? flaechen_stl = null);
