//
// StlSchnitt - Bauteil (STL, mm) horizontal aufschneiden: nur der Teil z <= z_max bleibt, Schnittflaeche geschlossen.
// Grobes Voxel macht das Netz kleiner (fuer Blender).
// plasma.stl + abstand: alles naeher als abstand am Plasma weg (Innenhaut abnehmen, Blick in den Kuehlraum)
//   StlSchnitt <ein.stl> <voxel_mm> <z_max_mm> <aus.stl> [schnitt.stl] [plasma.stl abstand_mm]
// schnitt.stl (optional): nur die Schnittflaeche als duenne Scheibe (fuer eigene Farbe)
//

using System.Numerics;
using PicoGK;

if (args.Length < 4)
{
    Console.Error.WriteLine("Aufruf: StlSchnitt <ein.stl> <voxel_mm> <z_max_mm> <aus.stl> [schnitt.stl]");
    return 2;
}
float fVoxel = float.Parse(args[1], System.Globalization.CultureInfo.InvariantCulture);
float fZ = float.Parse(args[2], System.Globalization.CultureInfo.InvariantCulture);
using Library lib = new(fVoxel);
Voxels vox = new(Mesh.mshFromStlFile(args[0], Mesh.EStlUnit.MM, libSet: lib));
if (args.Length > 6)
{
    Voxels voxPlasma = new(Mesh.mshFromStlFile(args[5], Mesh.EStlUnit.MM, libSet: lib));
    vox.BoolSubtract(voxPlasma.voxOffset(float.Parse(args[6], System.Globalization.CultureInfo.InvariantCulture)));
}
Voxels voxUnten = new(vox);
voxUnten.IntersectImplicit(new HalbRaum(fZ));
voxUnten.mshAsMesh().SaveToStlFile(args[3]);
if (args.Length > 4 && args[4] != "-")
{
    Voxels voxScheibe = new(vox);
    voxScheibe.IntersectImplicit(new Schicht(fZ - 2f * fVoxel, fZ));
    voxScheibe.mshAsMesh().SaveToStlFile(args[4]);
}
Console.WriteLine("FERTIG");
return 0;

class HalbRaum(float fZ) : IImplicit
{
    public float fSignedDistance(in Vector3 v) => v.Z - fZ;
}

class Schicht(float fZ0, float fZ1) : IImplicit
{
    public float fSignedDistance(in Vector3 v) => MathF.Max(fZ0 - v.Z, v.Z - fZ1);
}
