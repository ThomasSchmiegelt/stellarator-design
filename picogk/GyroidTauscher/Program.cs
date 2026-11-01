// GyroidTauscher: Kernmodul eines Zwei-Fluid-Vorwaermers aus abgestuftem Gyroid (Divertorwasser gegen Kondensat).
// Auslegung aus stellarator/vorwaermer.py (Gyroid abgestuft, 99 % der Obergrenze): d_h ~ 2-3 mm auf beiden Seiten
// (Gyroid Zelle 4,33-5,8 mm, Diamond 5,37-7,2 mm bei 0,5 mm Wand; numerisch geprueft in stellarator/tauscher_cfd.py),
// Wand 0,5 mm Edelstahl. Die Gyroid-Wand trennt zwei verschlungene Kanalnetze: g > 0 Divertorwasser (warm),
// g < 0 Kondensat (kalt). Gegenstrom entlang z.
// Abstufung: Zelle a(z) waechst linear von a0 (warmes Ende z = 0, kleinste Annaeherung -> meiste Flaeche) bis a1.
// Die z-Phase wird integriert (phi = 2 pi * int dz/a), damit die Flaeche stetig bleibt.
// Anschluesse (Prinzip der TPMS-Sammler): Stirnflaechen offen fuer warm, kalte Kanaele dort mit Kappe verschlossen;
// das Kondensat tritt durch Seitenfenster in der Huelle ein und aus, dort sind die warmen Kanaele verschlossen.
//   GyroidTauscher <voxel_mm> <ausgabeordner> [breite laenge a0 a1 wand huelle typ] (mm; typ 0 Gyroid, 1 Diamond)
using System.Numerics;
using PicoGK;

var inv = System.Globalization.CultureInfo.InvariantCulture;
float fVoxel = float.Parse(args[0], inv); string sAus = args[1];
float[] p = args.Skip(2).Select(s => float.Parse(s, inv)).ToArray();
float W(int i, float d) => i < p.Length ? p[i] : d;
float B = W(0, 48), L = W(1, 96), a0 = W(2, 4.33f), a1 = W(3, 5.8f), t = W(4, 0.5f), h = W(5, 1.5f);
int iTyp = (int)W(6, 0);                            // 0 Gyroid, 1 Diamond
float kappe = 2.5f, fz0 = 5, fz1 = 22;                 // Kappenlaenge, Seitenfenster z = fz0..fz1 bzw. L-fz1..L-fz0
var gyr = new Gyroid(a0, a1, L, iTyp);
using Library lib = new(fVoxel);
var bb = new BBox3(new Vector3(-1, -1, -1), new Vector3(B + 1, B + 1, L + 1));
Voxels V(IImplicit i) { var v = new Voxels(lib); v.RenderImplicit(i, bb); return v; }

Voxels voxBox = V(new Quader(0, B, 0, B, 0, L));
// Huelle: Quader minus Innenraum, Stirnseiten offen, zwei Fenster auf der Seite x = 0
Voxels voxHuelle = V(new Quader(0, B, 0, B, 0, L)); voxHuelle.BoolSubtract(V(new Quader(h, B - h, h, B - h, -1, L + 1)));
Voxels voxFenster = V(new Quader(-1, h + 0.01f, 6, B - 6, fz0, fz1)); voxFenster.BoolAdd(V(new Quader(-1, h + 0.01f, 6, B - 6, L - fz1, L - fz0)));
voxHuelle.BoolSubtract(voxFenster);
Voxels voxWand = V(new Seite(gyr, t, 0)); voxWand.BoolIntersect(V(new Quader(0, B, 0, B, 0, L)));
Voxels voxWarm = V(new Seite(gyr, t, +1)); voxWarm.BoolIntersect(V(new Quader(0, B, 0, B, 0, L)));
Voxels voxKalt = V(new Seite(gyr, t, -1)); voxKalt.BoolIntersect(V(new Quader(0, B, 0, B, 0, L)));
// Kappen: kalte Kanaele an beiden Stirnseiten zu; warme Kanaele hinter den Seitenfenstern zu (bis x = 3 h)
Voxels voxKappeK = voxKalt.voxDuplicate(); var vk = V(new Quader(-1, B + 1, -1, B + 1, -1, kappe)); vk.BoolAdd(V(new Quader(-1, B + 1, -1, B + 1, L - kappe, L + 1)));
voxKappeK.BoolIntersect(vk);
Voxels voxKappeW = voxWarm.voxDuplicate(); var vw = V(new Quader(-1, 3 * h, 4, B - 4, fz0 - 1, fz1 + 1)); vw.BoolAdd(V(new Quader(-1, 3 * h, 4, B - 4, L - fz1 - 1, L - fz0 + 1)));
voxKappeW.BoolIntersect(vw);
Voxels voxStahl = voxWand.voxDuplicate(); voxStahl.BoolAdd(voxHuelle); voxStahl.BoolAdd(voxKappeK); voxStahl.BoolAdd(voxKappeW);
voxWarm.BoolSubtract(voxStahl); voxKalt.BoolSubtract(voxStahl);
// Huelle unterhalb der Fenster weg fuer die Ansicht nicht noetig; Schnittansicht: Viertel (x > B/2, y < B/2) weg
voxStahl.mshAsMesh().SaveToStlFile(Path.Combine(sAus, "stahl_ganz.stl"));
voxWarm.mshAsMesh().SaveToStlFile(Path.Combine(sAus, "warm.stl"));
voxKalt.mshAsMesh().SaveToStlFile(Path.Combine(sAus, "kalt.stl"));
Voxels voxViertel = V(new Quader(B / 2, B + 2, -2, B / 2, L * 0.35f, L + 2));
foreach (var (v, n) in new[] { (voxStahl, "stahl"), (voxWarm, "warm"), (voxKalt, "kalt") })
{ var c = v.voxDuplicate(); c.BoolSubtract(voxViertel); c.mshAsMesh().SaveToStlFile(Path.Combine(sAus, n + "_schnitt.stl")); }
voxStahl.CalculateProperties(out float vS, out _); voxWarm.CalculateProperties(out float vW, out _); voxKalt.CalculateProperties(out float vK, out _);
float vGes = B * B * L;
Console.WriteLine($"FERTIG {(iTyp == 0 ? "Gyroid" : "Diamond")} Stahl {vS / vGes:P1}, warm {vW / vGes:P1}, kalt {vK / vGes:P1} des Moduls ({B}x{B}x{L} mm, Zelle {a0}->{a1} mm, Wand {t} mm)");
return 0;

class Quader(float x0, float x1, float y0, float y1, float z0, float z1) : IImplicit
{
    public float fSignedDistance(in Vector3 v) =>
        MathF.Max(MathF.Max(MathF.Max(x0 - v.X, v.X - x1), MathF.Max(y0 - v.Y, v.Y - y1)), MathF.Max(z0 - v.Z, v.Z - z1));
}

class Gyroid(float a0, float a1, float L, int iTyp)
{
    // Abstand zur Mittelflaeche mit Vorzeichen (positiv = warme Seite), s = g / |grad g| (erste Ordnung)
    // iTyp 0: Gyroid, 1: Diamond (Schwarz D)
    public float s(in Vector3 v)
    {
        float a = a0 + (a1 - a0) * Math.Clamp(v.Z / L, 0, 1), k = 2f * MathF.PI / a;
        float Z = MathF.Abs(a1 - a0) < 1e-4f ? v.Z * k : 2f * MathF.PI * L / (a1 - a0) * MathF.Log(a / a0);
        float X = v.X * k, Y = v.Y * k;
        float sx = MathF.Sin(X), cx = MathF.Cos(X), sy = MathF.Sin(Y), cy = MathF.Cos(Y), sz = MathF.Sin(Z), cz = MathF.Cos(Z);
        float g, gx, gy, gz;
        if (iTyp == 0)
        {
            g = sx * cy + sy * cz + sz * cx;
            gx = cx * cy - sz * sx; gy = -sx * sy + cy * cz; gz = -sy * sz + cz * cx;
        }
        else
        {
            g = sx * sy * sz + sx * cy * cz + cx * sy * cz + cx * cy * sz;
            gx = cx * sy * sz + cx * cy * cz - sx * sy * cz - sx * cy * sz;
            gy = sx * cy * sz - sx * sy * cz + cx * cy * cz - cx * sy * sz;
            gz = sx * sy * cz - sx * cy * sz - cx * sy * sz + cx * cy * cz;
        }
        return g / (k * MathF.Max(MathF.Sqrt(gx * gx + gy * gy + gz * gz), 0.3f));
    }
}

class Seite(Gyroid gyr, float t, int iSeite) : IImplicit
{
    // 0: Wand |s| < t/2; +1: warm s > t/2; -1: kalt s < -t/2
    public float fSignedDistance(in Vector3 v)
    {
        float s = gyr.s(v);
        return iSeite == 0 ? MathF.Abs(s) - t / 2 : t / 2 - iSeite * s;
    }
}
