// GEAENDERTE FASSUNG (altered source version) von src/setup.cpp aus FluidX3D v3.8
// (https://github.com/ProjectPhysX/FluidX3D, Commit 50150a7, Copyright (c) 2022-2026 Dr. Moritz Lehmann).
// Nicht das Original: die Beispiel-Setups wurden durch diesen einen Fall ersetzt. Es gilt die FluidX3D-Lizenz
// (LICENSE.md in diesem Ordner), NICHT die MIT-Lizenz des uebrigen Repositorys.
//
// Fall: eine Fluidseite eines Waermetauschers (Gyroid, Diamond, Platten), ausgebildete Stroemung (stellarator/tauscher_cfd.py).
// Gebiet in allen Richtungen periodisch, Antrieb durch Volumenkraft fz (kein Dichtegefaelle wie bei Ein-/Austritt).
// Belegung .bin (1 Byte je Zelle, x schnellste): 0 = fest, 1 = Fluid, 2 = Fluid an der Tauscherwand (wie 1).
// Festzellen: TYPE_S|TYPE_T mit T = 0 -> Wandtemperatur halbwegs zwischen Fluid- und Festzelle (Anti-Bounce-Back,
// Kernaenderung in kernel.cpp.diff); TYPE_S allein waere adiabat.
// Waerme: gleichmaessige Quelle q je Schritt in allen freien Fluidzellen (Kernaenderung, Umgebungsvariable FX_Q_T,
// siehe kernel.cpp.diff, lbm.cpp.diff); im eingeschwungenen Zustand h = q V_f / (A (T_misch - T_wand)).
// Konfiguration ueber die Datei in der Umgebungsvariable TAUSCHER_FALL:
//   bin aus Nx Ny Nz nu alpha fz u0 schritte stat_alle   (u0: Anfangsgeschwindigkeit in z, verkuerzt das Anlaufen)
// Ausgabe: stat.txt (t, mittleres uz aller Fluidzellen, Mischtemperatur Summe(uz T)/Summe(uz), mittleres T, mittleres rho),
//          am Ende feld.bin (alle Fluidzellen: Index uint, dann ux uy uz rho T als float) fuer Bilder und Videos.

#include "setup.hpp"
#include <fstream>

void main_setup() { // benoetigt in defines.hpp: TEMPERATURE (schaltet VOLUME_FORCE ein), SUBGRID, UPDATE_FIELDS
	const char* fall = getenv("TAUSCHER_FALL");
	if(fall==nullptr) print_error("Umgebungsvariable TAUSCHER_FALL fehlt.");
	std::ifstream c(fall);
	string bin, aus; uint Nx, Ny, Nz; float nu, alpha, fz, u0; ulong schritte, stat_alle;
	c >> bin >> aus >> Nx >> Ny >> Nz >> nu >> alpha >> fz >> u0 >> schritte >> stat_alle;
	if(c.fail()) print_error("Konfiguration unvollstaendig: "+string(fall));

	LBM lbm(uint3(Nx, Ny, Nz), nu, 0.0f, 0.0f, fz, 0.0f, alpha, 0.0f);
	std::ifstream b(bin, std::ios::binary);
	vector<uchar> w((size_t)Nx*Ny*Nz);
	b.read((char*)w.data(), (std::streamsize)w.size());
	if(!b) print_error("Belegung unvollstaendig: "+bin);

	const ulong N = lbm.get_N();
	vector<ulong> fl;
	for(ulong n=0ull; n<N; n++) {
		const uchar k = w[n];
		lbm.T[n] = 0.0f;
		if(k==0u) { lbm.flags[n] = TYPE_S|TYPE_T; continue; }
		fl.push_back(n);
		lbm.u.z[n] = u0;
	}
	print_info("Fluidzellen "+to_string(fl.size()));

	std::ofstream st(aus+"/stat.txt");
	st << "# t  uz_mittel  T_misch  T_mittel  rho_mittel\n";
	lbm.run(0u);
	while(lbm.get_t()<schritte) {
		lbm.run(stat_alle, schritte);
		lbm.u.read_from_device(); lbm.rho.read_from_device(); lbm.T.read_from_device();
		double su=0.0, sut=0.0, sT=0.0, sr=0.0;
		for(const ulong n : fl) { su += lbm.u.z[n]; sut += lbm.u.z[n]*lbm.T[n]; sT += lbm.T[n]; sr += lbm.rho[n]; }
		const double m = (double)max(fl.size(), (size_t)1u);
		st << lbm.get_t() << " " << su/m << " " << sut/su << " " << sT/m << " " << sr/m << "\n"; st.flush();
		if(!(su==su)||sr/m>2.0) { st << "# instabil, Abbruch\n"; st.close(); print_error("Simulation instabil."); }
	}
	st.close();
	std::ofstream f(aus+"/feld.bin", std::ios::binary); const ulong M = fl.size();
	f.write((const char*)&M, sizeof(ulong));
	for(const ulong n : fl) { const uint i = (uint)n; f.write((const char*)&i, 4); }
	for(const ulong n : fl) { const float v[5] = { lbm.u.x[n], lbm.u.y[n], lbm.u.z[n], lbm.rho[n], lbm.T[n] }; f.write((const char*)v, 20); }
	f.close();
}
