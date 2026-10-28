// GradientWand: ebenes Wandstueck mit abgestufter Gyroid-Struktur (Idee des Nutzers 2026-10-28).
// An der Haut flaechige Auflage: kleine Zellen, dicke Straenge (Waermeleitung, Stuetzabstand <= 20 mm bei 16 MPa);
// nach aussen verdoppelt sich die Zelle je Lage, die Straenge werden duenn und veraesteln sich (Stahlanteil >= ~15 %).
// Zwischen zwei Lagen werden die Abstandsfelder der Gyroide mit Zelle a und 2a weich ineinander ueberblendet.
//   GradientWand <voxel_mm> <ausgabeordner> [laenge breite tiefe haut aussen rundung] (mm)
// Lagen (Zelle a, Wanddicke t, Ende z der Lage): fest im Code unten. Wasser stroemt durch den ganzen Gyroid.
// Ausgabe: stahl.stl (Haut mit Fenster x > L/2, y > B/2 und Viertel ausgeschnitten, nur zum Ansehen),
//          stahl_ganz.stl, wasser.stl (Quader minus Stahl, fuer Durchstroemung), lagen.txt.
using System.Numerics;
using PicoGK;

var inv = System.Globalization.CultureInfo.InvariantCulture;
float fVoxel = float.Parse(args[0], inv); string sAus = args[1];
float[] p = args.Skip(2).Select(s => float.Parse(s, inv)).ToArray();
float L = W(0, 240), B = W(1, 240), T = W(2, 600), fHaut = W(3, 5), fAussen = W(4, 30), fRund = W(5, 1.5f);
float W(int i, float d) => i < p.Length ? p[i] : d;
// Lagen von der Haut nach aussen: Zelle a [mm], Wanddicke t [mm], Lagenende z [mm]
float[] aZelle = { 20, 40, 80, 160 }, aDicke = { 2.5f, 3f, 4.5f, 8f }, aEnde = { 30, 80, 180, T };
using Library lib = new(fVoxel);
var bb = new BBox3(new Vector3(-2, -2, -2), new Vector3(L + 2, B + 2, T + 2));

Voxels voxGyr = new(lib); voxGyr.RenderImplicit(new Quader(0, L, 0, B, fHaut - 1, T - fAussen + 1), bb);
voxGyr.IntersectImplicit(new GyroidGestuft(aZelle, aDicke, aEnde, fHaut));
Voxels voxStahl = new(lib); voxStahl.RenderImplicit(new Quader(0, L, 0, B, 0, fHaut), bb);
Voxels voxAussen = new(lib); voxAussen.RenderImplicit(new Quader(0, L, 0, B, T - fAussen, T), bb);
voxStahl.BoolAdd(voxGyr); voxStahl.BoolAdd(voxAussen);
// Ausrundung der Anschluesse (Schliessen: erst aufdicken, dann wieder abtragen), dann auf den Quader begrenzen
if (fRund > 0) { voxStahl.DoubleOffset(fRund, -fRund); voxStahl.IntersectImplicit(new Quader(0, L, 0, B, 0, T)); }
voxStahl.mshAsMesh().SaveToStlFile(Path.Combine(sAus, "stahl_ganz.stl"));
Voxels voxWasser = new(lib); voxWasser.RenderImplicit(new Quader(0, L, 0, B, fHaut, T - fAussen), bb);
voxWasser.BoolSubtract(voxStahl);
voxWasser.mshAsMesh().SaveToStlFile(Path.Combine(sAus, "wasser.stl"));
voxStahl.CalculateProperties(out float fVolStahl, out _); voxWasser.CalculateProperties(out float fVolWasser, out _);
// Ansicht: Fenster in der Haut und ein Viertel (x > L/2, y < B/2) ueber die ganze Tiefe weg
Voxels voxAnsicht = voxStahl.voxDuplicate();
Voxels voxWeg = new(lib); voxWeg.RenderImplicit(new Quader(L / 2, L + 5, B / 2, B + 5, -5, fHaut + 0.01f), bb);
voxAnsicht.BoolSubtract(voxWeg);
Voxels voxViertel = new(lib); voxViertel.RenderImplicit(new Quader(L / 2, L + 5, -5, B / 2, -5, T + 5), bb);
voxAnsicht.BoolSubtract(voxViertel);
voxAnsicht.mshAsMesh().SaveToStlFile(Path.Combine(sAus, "stahl.stl"));
using (var f = new StreamWriter(Path.Combine(sAus, "lagen.txt")))
{
    f.WriteLine("Lage Zelle_mm Dicke_mm Ende_mm Stahlanteil_Gyroid(~3,09 t/a)");
    for (int i = 0; i < aZelle.Length; i++)
        f.WriteLine($"{i} {aZelle[i]} {aDicke[i]} {aEnde[i]} {3.09f * aDicke[i] / aZelle[i]:F2}");
}
Console.WriteLine($"FERTIG Stahl {fVolStahl / 1e9:F5} m3, Wasser {fVolWasser / 1e9:F5} m3, Porositaet {fVolWasser / (L * B * (T - fAussen - fHaut)):F2}");
return 0;

class Quader(float x0, float x1, float y0, float y1, float z0, float z1) : IImplicit
{
    public float fSignedDistance(in Vector3 v) =>
        MathF.Max(MathF.Max(MathF.Max(x0 - v.X, v.X - x1), MathF.Max(y0 - v.Y, v.Y - y1)), MathF.Max(z0 - v.Z, v.Z - z1));
}

class GyroidGestuft(float[] aZelle, float[] aDicke, float[] aEnde, float fStart) : IImplicit
{
    // Abstand zur Gyroid-Wand der Lage i; zwischen Lage i und i+1 weich ueberblendet (Breite 0,75 Zelle i)
    static float Lage(in Vector3 v, float fZelle, float fDicke)
    {
        float k = 2f * MathF.PI / fZelle, x = v.X * k, y = v.Y * k, z = v.Z * k;
        float g = MathF.Sin(x) * MathF.Cos(y) + MathF.Sin(y) * MathF.Cos(z) + MathF.Sin(z) * MathF.Cos(x);
        return MathF.Abs(g) / (1.5f * k) - fDicke / 2;
    }
    public float fSignedDistance(in Vector3 v)
    {
        int i = 0;
        while (i < aEnde.Length - 1 && v.Z > aEnde[i]) i++;
        float d = Lage(v, aZelle[i], aDicke[i]);
        // Uebergang zur naechsten (weiter aussen) bzw. vorigen Lage
        if (i < aEnde.Length - 1)
        {
            float h = 0.75f * aZelle[i], s = Glatt((v.Z - (aEnde[i] - h / 2)) / h);
            if (s > 0) d = (1 - s) * d + s * Lage(v, aZelle[i + 1], aDicke[i + 1]);
        }
        if (i > 0)
        {
            float h = 0.75f * aZelle[i - 1], s = Glatt((v.Z - (aEnde[i - 1] - h / 2)) / h);
            if (s < 1) d = (1 - s) * Lage(v, aZelle[i - 1], aDicke[i - 1]) + s * d;
        }
        return d;
    }
    static float Glatt(float u) { u = Math.Clamp(u, 0, 1); return u * u * (3 - 2 * u); }
}
