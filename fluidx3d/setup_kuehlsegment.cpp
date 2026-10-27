// GEAENDERTE FASSUNG (altered source version) von src/setup.cpp aus FluidX3D v3.8
// (https://github.com/ProjectPhysX/FluidX3D, Commit 50150a7, Copyright (c) 2022-2026 Dr. Moritz Lehmann).
// Nicht das Original: die Beispiel-Setups wurden durch diesen einen Fall ersetzt. Es gilt die FluidX3D-Lizenz
// (LICENSE.md in diesem Ordner), NICHT die MIT-Lizenz des uebrigen Repositorys.
//
// Fall: Kuehlsegment der Gefaesswand (stellarator/kuehlung_segment.py, stellarator/kuehlung_cfd.py).
// Wasserraum als STL in Gitterkoordinaten (Zelle x <-> Koordinate x) oder als Belegung .bin (1 Byte je Zelle, aus PicoGK);
// alles ausserhalb ist fest (TYPE_S).
// Eintritt: TYPE_E-Zellen am Ende des Eintrittsrohrs mit fester Geschwindigkeit; Austritt: TYPE_E mit rho = 1.
// Konfiguration ueber die Datei in der Umgebungsvariable KUEHL_FALL (Leerzeichen-getrennte Zahlen, siehe unten).
// Ausgabe: <aus>/stat.txt (Verlauf), <aus>/feld_<t>.bin (nur Wasserzellen: Index, Flag, u, rho in Gittereinheiten).

#include "setup.hpp"
#include <fstream>

struct Rohr { float3 ende, achse; float r; };

static void schreibe_feld(LBM& lbm, const vector<ulong>& zellen, const string& pfad) {
	lbm.u.read_from_device(); lbm.rho.read_from_device();
	const ulong M = zellen.size(), N = lbm.get_N();
	std::ofstream f(pfad, std::ios::binary);
	f.write((const char*)&M, sizeof(ulong));
	for(ulong i=0ull; i<M; i++) { const uint n = (uint)zellen[i]; f.write((const char*)&n, 4); }
	for(ulong i=0ull; i<M; i++) { const uchar fl = lbm.flags[zellen[i]]; f.write((const char*)&fl, 1); }
	for(ulong i=0ull; i<M; i++) { const ulong n = zellen[i]; const float v[4] = { lbm.u.x[n], lbm.u.y[n], lbm.u.z[n], lbm.rho[n] }; f.write((const char*)v, 16); }
	f.close();
	(void)N;
}

void main_setup() { // Kuehlsegment; benoetigt in defines.hpp: EQUILIBRIUM_BOUNDARIES, SUBGRID
	const char* fall = getenv("KUEHL_FALL");
	if(fall==nullptr) print_error("Umgebungsvariable KUEHL_FALL fehlt.");
	std::ifstream c(fall);
	string stl, aus;
	uint Nx, Ny, Nz; float nu, u_ein, u_aus, rho_ein; ulong schritte, stat_alle, feld_alle;
	Rohr ein, aus_r;
	c >> stl >> aus >> Nx >> Ny >> Nz >> nu >> u_ein >> u_aus >> rho_ein >> schritte >> stat_alle >> feld_alle;
	c >> ein.ende.x >> ein.ende.y >> ein.ende.z >> ein.achse.x >> ein.achse.y >> ein.achse.z >> ein.r;
	c >> aus_r.ende.x >> aus_r.ende.y >> aus_r.ende.z >> aus_r.achse.x >> aus_r.achse.y >> aus_r.achse.z >> aus_r.r;
	if(c.fail()) print_error("Konfiguration unvollstaendig: "+string(fall));

	LBM lbm(uint3(Nx, Ny, Nz), nu);
	if(stl.size()>4&&stl.substr(stl.size()-4)==".bin") { // Belegung (1 Byte je Zelle, x schnellste, 1 = Wasser) aus PicoGK
		std::ifstream b(stl, std::ios::binary);
		vector<uchar> w((size_t)Nx*Ny*Nz);
		b.read((char*)w.data(), (std::streamsize)w.size());
		if(!b) print_error("Belegung unvollstaendig: "+stl);
		for(ulong n=0ull; n<lbm.get_N(); n++) lbm.flags[n] = w[n] ? TYPE_S : 0u; // TYPE_S = Wasser wie nach dem Voxelisieren, s. unten
	} else {
		Mesh* mesh = read_stl(stl, 1.0f); // keine Skalierung/Verschiebung: STL liegt schon in Gitterkoordinaten
		lbm.flags.write_to_device();
		lbm.voxelize_mesh_on_device(mesh, TYPE_S);
		lbm.flags.read_from_device();
		delete mesh;
	}

	const ulong N = lbm.get_N();
	vector<ulong> zellen; // Wasserzellen (fuer Ausgabe)
	vector<ulong> q_ein, q_aus; // Querschnitte 15 Zellen vor den Rohrenden (Mittelwerte fuer stat.txt)
	for(ulong n=0ull; n<N; n++) {
		uint x=0u, y=0u, z=0u; lbm.coordinates(n, x, y, z);
		const bool wasser = lbm.flags[n]==TYPE_S; // voxelisiert = innerhalb des Wasserraums
		lbm.flags[n] = wasser ? 0u : TYPE_S;
		if(!wasser) continue;
		zellen.push_back(n);
		const float3 p((float)x, (float)y, (float)z);
		for(int k=0; k<2; k++) {
			const Rohr& r = k==0 ? ein : aus_r;
			const float t = dot(p-r.ende, r.achse); // < 0: innen
			const float d = length(p-r.ende-t*r.achse);
			if(d>r.r+1.5f) continue;
			if(t>-2.0f) { // letzte Zellen am Rohrende: Randbedingung
				lbm.flags[n] = TYPE_E;
				lbm.u.x[n] = (k==0 ? -u_ein : u_aus)*r.achse.x;
				lbm.u.y[n] = (k==0 ? -u_ein : u_aus)*r.achse.y;
				lbm.u.z[n] = (k==0 ? -u_ein : u_aus)*r.achse.z;
				lbm.rho[n] = k==0 ? rho_ein : 1.0f;
			} else if(t>-16.0f&&t<=-15.0f) {
				(k==0 ? q_ein : q_aus).push_back(n);
			}
		}
	}
	print_info("Wasserzellen: "+to_string(zellen.size())+", Messquerschnitte "+to_string(q_ein.size())+"/"+to_string(q_aus.size()));

	std::ofstream st(aus+"/stat.txt");
	st << "# t  u_ein_mittel  rho_ein_mittel  u_aus_mittel  rho_aus_mittel  (Gittereinheiten, Messquerschnitte)\n";
	lbm.run(0u);
	while(lbm.get_t()<schritte) {
		lbm.run(stat_alle, schritte);
		lbm.u.read_from_device(); lbm.rho.read_from_device();
		double w[4] = { 0.0, 0.0, 0.0, 0.0 };
		for(const ulong n : q_ein) { w[0] += -dot(float3(lbm.u.x[n], lbm.u.y[n], lbm.u.z[n]), ein.achse); w[1] += lbm.rho[n]; }
		for(const ulong n : q_aus) { w[2] += dot(float3(lbm.u.x[n], lbm.u.y[n], lbm.u.z[n]), aus_r.achse); w[3] += lbm.rho[n]; }
		const double a = (double)max(q_ein.size(), (size_t)1u), b = (double)max(q_aus.size(), (size_t)1u);
		st << lbm.get_t() << " " << w[0]/a << " " << w[1]/a << " " << w[2]/b << " " << w[3]/b << "\n"; st.flush();
		if(!(w[1]==w[1])||w[1]/a>2.0) { st << "# instabil, Abbruch\n"; st.close(); print_error("Simulation instabil."); }
		if(lbm.get_t()%feld_alle==0ull||lbm.get_t()>=schritte) schreibe_feld(lbm, zellen, aus+"/feld_"+to_string(lbm.get_t())+".bin");
	}
	st.close();
}
