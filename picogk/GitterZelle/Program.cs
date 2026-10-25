//
// GitterZelle - headless PicoGK-Lauf: Gitter-Einheitszellen fuer die Homogenisierung (Stuetzgitter 1-GW-Variante).
//
// Auftrag (auftrag.json, von stellarator/gitterzelle.py geschrieben):
//   art        "bcc" (Staebe Ecke->Mitte, rund) oder "gyroid" (TPMS-Schale)
//   zelle_mm   Kantenlaenge einer Zelle, n_zellen Zellen je Richtung (Stapel)
//   dicke_mm   Stabradius (bcc) bzw. halbe Wandstaerke (gyroid)
//   voxel_mm   PicoGK-Voxelgroesse, n_raster Abtastpunkte je Richtung (Zellmitten des FEM-Voxelnetzes)
// Ausgabe: zelle.stl (Anschauung), abstand.f32 (vorzeichenbehafteter Abstand [mm] je Rasterpunkt,
// C-Reihenfolge x,y,z, innen < 0), ergebnis.json (Volumen, Volumenanteil).
// Wie StellaratorVoxel ohne Library.Go() (kein Viewer, kein X-Display).
//

using System.Diagnostics;
using System.Numerics;
using System.Text.Json;
using PicoGK;

if (args.Length != 1)
{
    Console.Error.WriteLine("Aufruf: GitterZelle <auftrag.json>");
    return 2;
}

var oOpts = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
Auftrag a = JsonSerializer.Deserialize<Auftrag>(File.ReadAllText(args[0]), oOpts)
    ?? throw new InvalidDataException("Leerer Auftrag.");
Directory.CreateDirectory(a.ausgabe);
var oUhr = Stopwatch.StartNew();

using Library lib = new(a.voxel_mm);
float L = a.zelle_mm, H = a.zelle_mm * a.n_zellen;
BBox3 oBox = new(Vector3.Zero, new Vector3(H, H, H));

Voxels vox;
if (a.art == "bcc")
{
    // Raumdiagonalen jeder Zelle (Ecke -> Mitte); Nachbarzellen teilen die Eckpunkte
    Lattice lat = new(lib);
    for (int i = 0; i < a.n_zellen; i++)
    for (int j = 0; j < a.n_zellen; j++)
    for (int k = 0; k < a.n_zellen; k++)
    {
        Vector3 vecM = new((i + 0.5f) * L, (j + 0.5f) * L, (k + 0.5f) * L);
        for (int c = 0; c < 8; c++)
        {
            Vector3 vecE = new((i + (c & 1)) * L, (j + ((c >> 1) & 1)) * L, (k + ((c >> 2) & 1)) * L);
            lat.AddBeam(vecE, vecM, a.dicke_mm, a.dicke_mm, true);
        }
    }
    vox = new Voxels(lat);
}
else if (a.art == "gyroid")
{
    vox = new Voxels(lib, new Gyroid(L, a.dicke_mm), oBox);
}
else
    throw new InvalidDataException($"unbekannte art {a.art}");

// auf den Zellstapel zuschneiden (Staebe mit runden Kappen ragen sonst ueber den Rand)
Voxels voxKasten = new(Utils.mshCreateCube(lib, oBox));
vox.BoolIntersect(voxKasten);
vox.CalculateProperties(out float fVol, out BBox3 _);
vox.mshAsMesh().SaveToStlFile(Path.Combine(a.ausgabe, "zelle.stl"));

ScalarField oSdf = new(vox);
int n = a.n_raster;
float h = H / n;
float[] afAbstand = new float[n * n * n];
for (int i = 0; i < n; i++)
for (int j = 0; j < n; j++)
for (int k = 0; k < n; k++)
{
    oSdf.bGetValue(new Vector3((i + 0.5f) * h, (j + 0.5f) * h, (k + 0.5f) * h), out float f);
    afAbstand[(i * n + j) * n + k] = f;
}
byte[] aby = new byte[afAbstand.Length * 4];
Buffer.BlockCopy(afAbstand, 0, aby, 0, aby.Length);
File.WriteAllBytes(Path.Combine(a.ausgabe, "abstand.f32"), aby);

var oErg = new
{
    art = a.art, zelle_mm = L, n_zellen = a.n_zellen, dicke_mm = a.dicke_mm, voxel_mm = a.voxel_mm,
    n_raster = n, volumen_mm3 = fVol, volumenanteil = fVol / (H * H * H), zeit_s = oUhr.Elapsed.TotalSeconds,
};
File.WriteAllText(Path.Combine(a.ausgabe, "ergebnis.json"),
    JsonSerializer.Serialize(oErg, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine($"FERTIG {a.art} dicke {a.dicke_mm} mm: Volumenanteil {fVol / (H * H * H):F3}");
return 0;

// Gyroid-Schale: |g| < t, g = sin x cos y + sin y cos z + sin z cos x; Abstand genaehert ueber |grad g| ~ 1,5 k
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

record Auftrag(string art, float zelle_mm, int n_zellen, float dicke_mm, float voxel_mm, int n_raster, string ausgabe);
