// WandStueck: ebenes Stueck der Gefaesswand mit doppeltem Filament (schematisch, Kruemmung vernachlaessigt).
// Von der Plasmaseite (z = 0) nach aussen: Innenhaut | Kuehlkanaele (toroidal, x-Richtung) mit Stegen | Rueckwand |
// Gyroid nur fuer die Steifigkeit (trocken) | Aussenhaut. Kuehlung und Tragstruktur sind getrennt.
//   WandStueck <voxel_mm> <ausgabeordner> [laenge breite tiefe haut kanal_b kanal_h steg rueck zelle halbdicke aussen] (mm)
// Ausgabe: stahl.stl (Innenhaut im Fenster x > L/2, y > B/2 weggelassen, damit die Kanaele sichtbar sind),
//          stahl_ganz.stl, wasser.stl (nur Kanaele).
using System.Numerics;
using PicoGK;

var inv = System.Globalization.CultureInfo.InvariantCulture;
float fVoxel = float.Parse(args[0], inv); string sAus = args[1];
float[] p = args.Skip(2).Select(s => float.Parse(s, inv)).ToArray();
float L = W(0, 450), B = W(1, 450), T = W(2, 900), fHaut = W(3, 5), fKb = W(4, 6), fKh = W(5, 6), fSteg = W(6, 3),
      fRueck = W(7, 5), fZelle = W(8, 300), fHalb = W(9, 43), fAussen = W(10, 40);
float W(int i, float d) => i < p.Length ? p[i] : d;
using Library lib = new(fVoxel);
var bb = new BBox3(new Vector3(-2, -2, -2), new Vector3(L + 2, B + 2, T + 2));
float z1 = fHaut, z2 = z1 + fKh, z3 = z2 + fRueck;           // Kanallage z1..z2, Rueckwand bis z3
float fTeil = fKb + fSteg;

// Stahl vorne: massive Platte 0..z3 minus Kanaele
Voxels voxVorn = new(lib); voxVorn.RenderImplicit(new Quader(0, L, 0, B, 0, z3), bb);
Voxels voxKanal = new(lib); voxKanal.RenderImplicit(new Kanaele(L, B, z1, z2, fKb, fTeil), bb);
voxVorn.BoolSubtract(voxKanal);
// Tragstruktur: Gyroid z3..T-aussen, Aussenhaut
Voxels voxGyr = new(lib); voxGyr.RenderImplicit(new Quader(0, L, 0, B, z3 - 1, T - fAussen + 1), bb);
voxGyr.IntersectImplicit(new Gyroid(fZelle, fHalb));
Voxels voxAussen = new(lib); voxAussen.RenderImplicit(new Quader(0, L, 0, B, T - fAussen, T), bb);
Voxels voxStahl = voxVorn.voxDuplicate(); voxStahl.BoolAdd(voxGyr); voxStahl.BoolAdd(voxAussen);
voxStahl.mshAsMesh().SaveToStlFile(Path.Combine(sAus, "stahl_ganz.stl"));
// Fenster in der Innenhaut
Voxels voxFenster = new(lib); voxFenster.RenderImplicit(new Quader(L / 2, L + 5, B / 2, B + 5, -5, z1 + 0.01f), bb);
voxStahl.BoolSubtract(voxFenster);
voxStahl.mshAsMesh().SaveToStlFile(Path.Combine(sAus, "stahl.stl"));
voxKanal.mshAsMesh().SaveToStlFile(Path.Combine(sAus, "wasser.stl"));
voxStahl.CalculateProperties(out float fVol, out _);
Console.WriteLine($"FERTIG Stahl {fVol / 1e9:F4} m3, Kanaele {(int)(B / fTeil)}, Teilung {fTeil} mm");
return 0;

class Quader(float x0, float x1, float y0, float y1, float z0, float z1) : IImplicit
{
    public float fSignedDistance(in Vector3 v) =>
        MathF.Max(MathF.Max(MathF.Max(x0 - v.X, v.X - x1), MathF.Max(y0 - v.Y, v.Y - y1)), MathF.Max(z0 - v.Z, v.Z - z1));
}

class Kanaele(float L, float B, float z0, float z1, float fB, float fTeil) : IImplicit
{
    // Rechteckkanaele b x h in x-Richtung, Mitte bei y = (i + 0.5) * Teilung
    public float fSignedDistance(in Vector3 v)
    {
        float yl = v.Y - fTeil * MathF.Floor(v.Y / fTeil) - fTeil / 2;          // lokale Lage in der Teilung
        if (v.Y < 0 || v.Y > B) yl = MathF.Max(MathF.Abs(yl), fTeil);
        float dy = MathF.Abs(yl) - fB / 2, dz = MathF.Max(z0 - v.Z, v.Z - z1), dx = MathF.Max(-1 - v.X, v.X - L - 1);
        return MathF.Max(MathF.Max(dy, dz), dx);
    }
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
