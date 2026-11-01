// GEAENDERTE FASSUNG (altered source version) von src/setup.cpp aus FluidX3D v3.8
// (https://github.com/ProjectPhysX/FluidX3D, Commit 50150a7, Copyright (c) 2022-2026 Dr. Moritz Lehmann).
// Nicht das Original: die Beispiel-Setups wurden durch diesen einen Fall ersetzt. Es gilt die FluidX3D-Lizenz
// (LICENSE.md), NICHT die MIT-Lizenz des uebrigen Repositorys.
//
// Fall: Hartmann-Stroemung, Pruefung der Lorentzkraft (Kernaenderung MHD, kernel.cpp.diff).
// Kanal zwischen zwei Platten (y), B senkrecht zu den Platten (y), Stroemung in x durch Volumenkraft fx,
// x und z periodisch (unendlich ausgedehnt -> kein Potentialgefaelle, j = sigma u x B).
// Konfiguration ueber die Datei in MHD_FALL:  aus Ny nu fx schritte stat_alle
// K = sigma B^2/rho kommt ueber FX_MHD_K (Gittereinheiten), Richtung ueber FX_MHD_B.
// Ausgabe: stat.txt (t, mittleres ux), profil.txt (y, ux) am Ende.

#include "setup.hpp"
#include <fstream>

void main_setup() { // benoetigt in defines.hpp: VOLUME_FORCE, MHD
	const char* fall = getenv("MHD_FALL");
	if(fall==nullptr) print_error("Umgebungsvariable MHD_FALL fehlt.");
	std::ifstream c(fall);
	string aus; uint Ny; float nu, fx; ulong schritte, stat_alle;
	c >> aus >> Ny >> nu >> fx >> schritte >> stat_alle;
	if(c.fail()) print_error("Konfiguration unvollstaendig: "+string(fall));
	const uint Nx = 4u, Nz = 4u;
	LBM lbm(uint3(Nx, Ny, Nz), nu, fx, 0.0f, 0.0f);
	const ulong N = lbm.get_N();
	for(ulong n=0ull; n<N; n++) {
		uint x=0u, y=0u, z=0u; lbm.coordinates(n, x, y, z);
		if(y==0u||y==Ny-1u) lbm.flags[n] = TYPE_S;
	}
	std::ofstream st(aus+"/stat.txt");
	st << "# t  ux_mittel\n";
	lbm.run(0u);
	while(lbm.get_t()<schritte) {
		lbm.run(stat_alle, schritte);
		lbm.u.read_from_device();
		double su=0.0; ulong m=0ull;
		for(uint y=1u; y<Ny-1u; y++) { su += lbm.u.x[lbm.index(1u, y, 1u)]; m++; }
		st << lbm.get_t() << " " << su/(double)m << "\n"; st.flush();
		if(!(su==su)) { st << "# instabil\n"; st.close(); print_error("Simulation instabil."); }
	}
	st.close();
	std::ofstream pr(aus+"/profil.txt");
	pr << "# y  ux  (Waende bei y = 0,5 und Ny-1,5)\n";
	for(uint y=1u; y<Ny-1u; y++) pr << y << " " << lbm.u.x[lbm.index(1u, y, 1u)] << "\n";
	pr.close();
}
