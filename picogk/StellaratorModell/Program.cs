//
// StellaratorModell - komplettes 3D-Modell eines Entwurfs der gekoppelten Studie in PicoGK (headless).
//
// Auftrag (auftrag.json, von stellarator/picogk_modell.py geschrieben):
//   voxel_mm, ausgabe
//   spulen_bin    float32 [spule][station][schicht 0..2][ecke 0..3][xyz] in mm; Schicht 0 = Gehaeuse aussen,
//                 1 = Verguss aussen (= Gehaeuse innen), 2 = Wickelpaket. Ecken = Rechteck je Station (FE-Querschnitt).
//   n_spulen, n_stationen
//   verbinder_stl geschlossene Oberflaechen aller Verbinder (aus dem FE-Netz)
//   plasma_stl    letzte geschlossene Flussflaeche (VMEC, Anlagengroesse)
//   package       Schichten [{name, bis_mm}] als Abstand zur Plasmaoberflaeche (aufsteigend)
//   lager         Stuetzen [{a, b, r_mm}] (Stab von Lagerflecken zum Stuetzring) + zylinder {r_innen_mm, r_aussen_mm, z0_mm, z1_mm}
//
// Aufbau in PicoGK:
//   Wickelpaket / Gehaeuse-Aussenkontur / Verguss-Aussenkontur: Netz aus den Stationsrechtecken (geschlossener Ring)
//     -> Voxel; Gehaeuse = Aussen - VergussAussen, Verguss = VergussAussen - Wickelpaket (Boolesche Differenz).
//   Package: Offsets der Plasma-Voxel (voxOffset), Schale = Offset(bis) - Offset(von).
//   Lager: Lattice-Staebe + Zylinderschale (Implicit).
// Pruefungen: Ueberschneidung Package-Huelle mit Gehaeusen/Verbindern/Lagern, Gehaeuse untereinander,
//   Verbinder mit Wickelpaketen. Ergebnis als STL; Volumina rechnet Python aus den Netzen (CalculateProperties
//   ist nach Booleschen Operationen unzuverlaessig, s. Skill picogk-voxel).
//
using System.Diagnostics;
using System.Numerics;
using System.Text.Json;
using PicoGK;

if (args.Length != 1) { Console.Error.WriteLine("Aufruf: StellaratorModell <auftrag.json>"); return 2; }
var oOpts = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
Auftrag a = JsonSerializer.Deserialize<Auftrag>(File.ReadAllText(args[0]), oOpts) ?? throw new InvalidDataException("Leerer Auftrag.");
Directory.CreateDirectory(a.ausgabe);
var oUhr = Stopwatch.StartNew(); var oZeiten = new Dictionary<string, double>();
void Messe(string s) { oZeiten[s] = oUhr.Elapsed.TotalSeconds; oUhr.Restart(); Console.WriteLine($"  {s} {oZeiten[s]:F1} s"); }
var oVolumen = new Dictionary<string, double>();
void Stl(Voxels v, string name)
{   // Volumen immer aus dem Netz (CalculateProperties ist nach Booleschen Operationen unzuverlaessig);
    // STL nur bei export = true oder fuer Pruefkoerper (klein)
    Mesh m = v.mshAsMesh();
    double fV = 0;
    for (int i = 0; i < m.nTriangleCount(); i++)
    {
        m.GetTriangle(i, out Vector3 p0, out Vector3 p1, out Vector3 p2);
        fV += Vector3.Dot(p0, Vector3.Cross(p1, p2)) / 6.0;
    }
    oVolumen[name] = Math.Abs(fV) * 1e-9;
    if (a.export || name.StartsWith("pruefung")) m.SaveToStlFile(Path.Combine(a.ausgabe, name + ".stl"));
}

using Library lib = new(a.voxel_mm);

// ---------------------------------------------------------------- Spulen
byte[] aby = File.ReadAllBytes(a.spulen_bin);
float[] af = new float[aby.Length / 4]; Buffer.BlockCopy(aby, 0, af, 0, aby.Length);
int nS = a.n_spulen, nN = a.n_stationen;
Vector3 Ecke(int s, int i, int l, int e) { int o = ((((s * nN) + i) * 3 + l) * 4 + e) * 3; return new(af[o], af[o + 1], af[o + 2]); }
Mesh Ring(int s, int l)
{   // geschlossenes Rohr: je Station 4 Ecken, Viereck je Seite und Stationsschritt -> 2 Dreiecke
    Mesh m = new(lib);
    int[,] id = new int[nN, 4];
    for (int i = 0; i < nN; i++) for (int e = 0; e < 4; e++) id[i, e] = m.nAddVertex(Ecke(s, i, l, e));
    for (int i = 0; i < nN; i++)
    {
        int j = (i + 1) % nN;
        for (int e = 0; e < 4; e++)
        {
            int f = (e + 1) % 4;
            m.nAddTriangle(id[i, e], id[j, e], id[j, f]); m.nAddTriangle(id[i, e], id[j, f], id[i, f]);
        }
    }
    return m;
}
var avoxWP = new List<Voxels>(); var avoxGeh = new List<Voxels>(); var avoxVerg = new List<Voxels>();
for (int s = 0; s < nS; s++)
{
    Voxels voxAussen = new(Ring(s, 0)), voxVergA = new(Ring(s, 1)), voxWP = new(Ring(s, 2));
    // Umlaufsinn unbekannt -> Voxelisierung arbeitet mit |Winding|, Vorzeichen egal
    avoxGeh.Add(voxAussen.voxBoolSubtract(voxVergA));
    avoxVerg.Add(voxVergA.voxBoolSubtract(voxWP));
    avoxWP.Add(voxWP);
}
Voxels voxWickel = new(lib); voxWickel.BoolAddAll(avoxWP);
Voxels voxVerguss = new(lib); voxVerguss.BoolAddAll(avoxVerg);
Voxels voxGehaeuse = new(lib); voxGehaeuse.BoolAddAll(avoxGeh);
Messe("spulen");
// Gehaeuse untereinander: Schnitt jeder Spule mit allen anderen
Voxels voxUeberGeh = new(lib);
for (int s = 0; s < nS; s++)
{
    Voxels voxAndere = new(lib);
    for (int t = 0; t < nS; t++) if (t != s) voxAndere.BoolAdd(avoxGeh[t]);
    voxUeberGeh.BoolAdd(avoxGeh[s].voxBoolIntersect(voxAndere));
}
Messe("pruefung_gehaeuse");

// ---------------------------------------------------------------- Verbinder
Voxels voxVerbinder = a.verbinder_stl is null ? new(lib) : new(Mesh.mshFromStlFile(a.verbinder_stl, Mesh.EStlUnit.MM, libSet: lib));
Voxels voxVerbInWP = voxVerbinder.voxBoolIntersect(voxWickel);
Messe("verbinder");

// ---------------------------------------------------------------- Lager / Stuetzstruktur
Voxels voxLager = new(lib);
if (a.lager is not null)
{
    Lattice lat = new(lib);
    foreach (var st in a.lager.staebe) lat.AddBeam(V(st.a), V(st.b), st.r_mm, st.r_mm, false);
    voxLager.BoolAdd(new Voxels(lat));
    foreach (var z in a.lager.zylinder)
    {
        Voxels vz = new(lib);
        float R = z.r_aussen_mm + 10;
        vz.RenderImplicit(new Zylinderschale(z.r_innen_mm, z.r_aussen_mm, z.z0_mm, z.z1_mm),
                          new BBox3(new Vector3(-R, -R, z.z0_mm - 10), new Vector3(R, R, z.z1_mm + 10)));
        voxLager.BoolAdd(vz);
    }
    voxLager.BoolSubtract(voxGehaeuse.voxBoolAdd(voxVerguss).voxBoolAdd(voxWickel));  // Stab endet an der Gehaeusewand
}
Messe("lager");

// ---------------------------------------------------------------- Plasma + Package
Voxels voxPlasma = new(Mesh.mshFromStlFile(a.plasma_stl, Mesh.EStlUnit.MM, libSet: lib));
Stl(voxPlasma, "plasma");
var oPackage = new List<object>();
Voxels voxInnen = voxPlasma; float fVon = 0;
Voxels? voxHuelle = null;
foreach (var sch in a.package)
{
    Voxels voxBis = voxPlasma.voxOffset(sch.bis_mm);
    Voxels voxSchale = voxBis.voxBoolSubtract(voxInnen);
    Stl(voxSchale, "package_" + sch.name);
    oPackage.Add(new { sch.name, von_mm = fVon, sch.bis_mm });
    voxInnen = voxBis; fVon = sch.bis_mm; voxHuelle = voxBis;
    Messe("package_" + sch.name);
}
// Package-Huelle gegen Spulen, Verbinder und Lager
Voxels voxSpulenAlles = voxGehaeuse.voxBoolAdd(voxVerguss).voxBoolAdd(voxWickel).voxBoolAdd(voxVerbinder).voxBoolAdd(voxLager);
Voxels voxUeberPack = voxHuelle is null ? new(lib) : voxHuelle.voxBoolIntersect(voxSpulenAlles);
Messe("pruefung_package");

// ---------------------------------------------------------------- Ausgabe
Stl(voxWickel, "wickelpaket"); Stl(voxVerguss, "verguss"); Stl(voxGehaeuse, "gehaeuse");
Stl(voxVerbinder, "verbinder"); Stl(voxLager, "lager");
Stl(voxUeberGeh, "pruefung_gehaeuse_ueberschneidung"); Stl(voxUeberPack, "pruefung_package_ueberschneidung");
Stl(voxVerbInWP, "pruefung_verbinder_im_wickelpaket");
Messe("export");
File.WriteAllText(Path.Combine(a.ausgabe, "ergebnis.json"), JsonSerializer.Serialize(new
{
    voxel_mm = a.voxel_mm, volumen_m3 = oVolumen, n_spulen = nS, n_stationen = nN, package = oPackage, zeiten_s = oZeiten,
}, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine("FERTIG");
return 0;

static Vector3 V(float[] x) => new(x[0], x[1], x[2]);

class Zylinderschale(float r0, float r1, float z0, float z1) : IImplicit
{
    public float fSignedDistance(in Vector3 v)
    {
        float r = MathF.Sqrt(v.X * v.X + v.Y * v.Y);
        return MathF.Max(MathF.Max(r0 - r, r - r1), MathF.Max(z0 - v.Z, v.Z - z1));
    }
}
record Schicht(string name, float bis_mm);
record Stab(float[] a, float[] b, float r_mm);
record Zyl(float r_innen_mm, float r_aussen_mm, float z0_mm, float z1_mm);
record Lager(List<Stab> staebe, List<Zyl> zylinder);
record Auftrag(float voxel_mm, string ausgabe, string spulen_bin, int n_spulen, int n_stationen, string? verbinder_stl,
               string plasma_stl, List<Schicht> package, Lager? lager, bool export = true);
