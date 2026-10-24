//
// StellaratorVoxel - headless PicoGK-Lauf fuer die Stellarator-Pipeline.
//
// Liest einen Auftrag (auftrag.json, von stellarator/picogk_bruecke.py geschrieben):
//   - Wickelpaket-STL (mm) -> Voxelkoerper
//   - optional Spulengehaeuse = Offset(Wickelpaket, t) minus Wickelpaket
//   - Abstand: fuer vorgegebene Kandidaten-Gitterpunkte SDF [mm] -> abstand.f32
// Schreibt STL/VDB der Voxelkoerper und ergebnis.json (Volumen, BBox, Zeiten).
//
// Bewusst ohne Library.Go(): der Konstruktor new Library(voxel) braucht kein
// Viewer-Fenster und kein X-Display, und die Voxelgroesse ist frei waehlbar
// (die Web-API ist fest auf 0.25 mm - fuer einen 16-m-Stellarator unbrauchbar).
//

using System.Diagnostics;
using System.Numerics;
using System.Text.Json;
using PicoGK;

if (args.Length != 1)
{
    Console.Error.WriteLine("Aufruf: StellaratorVoxel <auftrag.json>");
    return 2;
}

var oOpts = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
Auftrag oAuftrag = JsonSerializer.Deserialize<Auftrag>(File.ReadAllText(args[0]), oOpts)
    ?? throw new InvalidDataException("Leerer Auftrag.");
string strAus = oAuftrag.ausgabe;
Directory.CreateDirectory(strAus);

var oUhr = Stopwatch.StartNew();
var oZeiten = new Dictionary<string, double>();
void Messe(string strSchritt) { oZeiten[strSchritt] = oUhr.Elapsed.TotalSeconds; oUhr.Restart(); }

using Library lib = new(oAuftrag.voxel_mm);

Mesh mshEin = Mesh.mshFromStlFile(oAuftrag.stl_wickel, Mesh.EStlUnit.MM, libSet: lib);
Voxels voxWickel = new(mshEin);
Messe("voxelisieren");

voxWickel.CalculateProperties(out float fVolWickel, out BBox3 oBoxWickel);
voxWickel.mshAsMesh().SaveToStlFile(Path.Combine(strAus, "wickelpaket_voxel.stl"));
voxWickel.SaveToVdbFile(Path.Combine(strAus, "wickelpaket.vdb"));
Messe("wickel_export");

float fVolGehaeuse = 0f;
if (oAuftrag.gehaeuse_mm > 0f)
{
    Voxels voxGehaeuse = voxWickel.voxOffset(oAuftrag.gehaeuse_mm);
    voxGehaeuse.BoolSubtract(voxWickel);
    voxGehaeuse.CalculateProperties(out fVolGehaeuse, out _);
    voxGehaeuse.mshAsMesh().SaveToStlFile(Path.Combine(strAus, "gehaeuse_voxel.stl"));
    Messe("gehaeuse");
}

int nBelegt = 0;
if (oAuftrag.kandidaten is not null)
{
    // Kandidaten: int32-Rohdatei mit flachen Gitterindizes (C-Reihenfolge nx,ny,nz).
    // Nur diese Punkte werden geprueft - die Vorauswahl (Abstand zum Filament)
    // macht Python, sonst waeren es ~10^7 Aufrufe ueber P/Invoke.
    // Ausgabe: vorzeichenbehafteter Abstand [mm] je Kandidat (innen < 0) aus dem
    // ScalarField. NICHT Voxels.bIsInside: das liefert in PicoGK 26.2 (Linux-Build)
    // fuer Aussenpunkte nahe der Oberflaeche ~50 % falsch "innen" (gemessen
    // 2026-10-23 gegen ScalarField und analytischen Rechteckquerschnitt).
    byte[] abyRoh = File.ReadAllBytes(oAuftrag.kandidaten);
    int[] anIdx = new int[abyRoh.Length / 4];
    Buffer.BlockCopy(abyRoh, 0, anIdx, 0, abyRoh.Length);
    Gitter g = oAuftrag.gitter ?? throw new InvalidDataException("kandidaten ohne gitter.");
    ScalarField oSdf = new(voxWickel);
    float[] afAbstand = new float[anIdx.Length];
    int nYZ = g.n[1] * g.n[2];
    for (int k = 0; k < anIdx.Length; k++)
    {
        int n = anIdx[k];
        int i = n / nYZ, j = (n / g.n[2]) % g.n[1], l = n % g.n[2];
        Vector3 vec = new(g.ursprung_mm[0] + i * g.h_mm,
                          g.ursprung_mm[1] + j * g.h_mm,
                          g.ursprung_mm[2] + l * g.h_mm);
        oSdf.bGetValue(vec, out float fWert);   // inaktiv: Hintergrund +-Bandbreite, Vorzeichen stimmt
        afAbstand[k] = fWert;
        if (fWert <= 0f)
            nBelegt++;
    }
    byte[] abyAus = new byte[afAbstand.Length * 4];
    Buffer.BlockCopy(afAbstand, 0, abyAus, 0, abyAus.Length);
    File.WriteAllBytes(Path.Combine(strAus, "abstand.f32"), abyAus);
    Messe("abstand");
}

var oErgebnis = new
{
    voxel_mm = oAuftrag.voxel_mm,
    volumen_wickel_m3 = fVolWickel * 1e-9,
    volumen_gehaeuse_m3 = fVolGehaeuse * 1e-9,
    bbox_wickel_mm = new[] { oBoxWickel.vecMin.X, oBoxWickel.vecMin.Y, oBoxWickel.vecMin.Z,
                             oBoxWickel.vecMax.X, oBoxWickel.vecMax.Y, oBoxWickel.vecMax.Z },
    belegte_punkte = nBelegt,
    zeiten_s = oZeiten,
};
File.WriteAllText(Path.Combine(strAus, "ergebnis.json"),
    JsonSerializer.Serialize(oErgebnis, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine($"FERTIG Wickel {fVolWickel * 1e-9:F3} m3, Gehaeuse {fVolGehaeuse * 1e-9:F3} m3, belegt {nBelegt}");
return 0;

record Gitter(float[] ursprung_mm, float h_mm, int[] n);
record Auftrag(float voxel_mm, string stl_wickel, float gehaeuse_mm, string ausgabe,
               string? kandidaten, Gitter? gitter);
