// GyroidTest: Wasseranteil eines Gyroid-Wuerfels in PicoGK gegen die Formel |g|/(1.5k) < t (Kalibrierung Wanddicke).
//   GyroidTest <voxel_mm> <zelle_mm> <halbdicke_mm>
using System.Numerics;
using PicoGK;

var inv = System.Globalization.CultureInfo.InvariantCulture;
float fVoxel = float.Parse(args[0], inv), fZelle = float.Parse(args[1], inv), fT = float.Parse(args[2], inv);
using Library lib = new(fVoxel);
float L = 4 * fZelle;


Voxels voxBox = new(lib);
var oBox = new Box(L); voxBox.RenderImplicit(oBox, new BBox3(new Vector3(-10, -10, -10), new Vector3(L + 10, L + 10, L + 10)));
voxBox.CalculateProperties(out float fVolBox, out _);
Voxels voxWand = voxBox.voxDuplicate();
voxWand.IntersectImplicit(new Gyroid(fZelle, fT));
voxWand.CalculateProperties(out float fVolWand, out _);
// Formel auf feinem Raster
int n = 200, nWand = 0; float k = 2f * MathF.PI / fZelle;
for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) for (int l = 0; l < n; l++)
{
    float x = (i + 0.5f) * L / n * k, y = (j + 0.5f) * L / n * k, z = (l + 0.5f) * L / n * k;
    float g = MathF.Sin(x) * MathF.Cos(y) + MathF.Sin(y) * MathF.Cos(z) + MathF.Sin(z) * MathF.Cos(x);
    if (MathF.Abs(g) / (1.5f * k) < fT) nWand++;
}
Console.WriteLine($"ERGEBNIS voxel {fVoxel} zelle {fZelle} t {fT}: Wandanteil PicoGK {fVolWand / fVolBox:F3}  Formel {(float)nWand / (n * n * n):F3}");
voxWand.mshAsMesh().SaveToStlFile($"gyroid_{fZelle}_{fT}.stl");
return 0;

class Box(float L) : IImplicit
{
    public float fSignedDistance(in Vector3 v) =>
        MathF.Max(MathF.Max(MathF.Max(-v.X, v.X - L), MathF.Max(-v.Y, v.Y - L)), MathF.Max(-v.Z, v.Z - L));
}

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
