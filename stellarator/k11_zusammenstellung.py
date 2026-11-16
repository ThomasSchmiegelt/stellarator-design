"""k11_zusammenstellung.py -- K11: Tabelle aller Grenzen aus K2e-K10 und Anforderungsverfolgung neu erzeugen. Nur Zusammenstellung, keine Deutung.
KI-generiert (Claude Sonnet 5.5, 2026-11-13).  Erwartung: sim/kandidat/erwartung/K11.md (nicht aendern).
Aufruf (Projektordner):  python3 stellarator/k11_zusammenstellung.py [--test]
Echt: liest sim/kandidat/<Schritt>/ERGEBNIS.md + auswertung.json (K2e/lauf, K3/lauf, K4/lauf, K5/lauf, K6/lauf), schreibt sim/kandidat/K11/ERGEBNIS.md und fuehrt pm/plan/wissensnetz.py aus
(Vorgang als fertig markiert, wenn sim/kandidat/<K>/ERGEBNIS.md existiert; ohne die Datei zu aendern: AUS wird im Aufruf ergaenzt).
--test: liest die test/-Ordner, schreibt nur nach sim/kandidat/K11/test/, fuehrt wissensnetz.py NICHT aus.
Spalten: Anforderung | Wert | Grenze | Art der Grenze (belegt/Annahme) | erfuellt (nur reiner Zahlenvergleich) | Quelle. K7-K10: keine feste Auswertungsstruktur -> Zeilen aus deren ERGEBNIS.md unveraendert (Zeilen mit 'Grenze' oder 'Erwartung')."""
import json, re, subprocess, sys, time
from pathlib import Path

P = Path(__file__).resolve().parents[1]
TEST = "--test" in sys.argv
UN = "test" if TEST else "lauf"
OUT = P / "sim/kandidat/K11" / ("test" if TEST else "lauf"); OUT.mkdir(parents=True, exist_ok=True)
J = lambda p: json.loads((P / p).read_text()) if (P / p).exists() else None
K = J("sim/kandidat/kandidat.json")


def zeile(anf, wert, grenze, art, ok, quelle):
    return {"anforderung": anf, "wert": wert, "grenze": grenze, "art": art, "erfuellt": ok, "quelle": quelle}


def zeilen():
    z = []
    k2 = K["k2"]; P1, P2, P3, P4 = (J(f"{k2}/{x}.json") for x in ("P1", "P2", "P3", "P4"))
    ep = Path.home() / "cae_projekte/gx/laeufe" / K["id"] / "ergebnis_vmec.json"; e = json.loads(ep.read_text()) if ep.exists() else {}
    qi = J("sim/spulenfreundlich/ergebnis/" + K["id"] + ".json")
    # K2 / K2e (Stand der kandidat.json)
    if P1:
        bn = P1["feldfehler"]; bn = bn if isinstance(bn, (int, float)) else bn.get("Bn_mittel", bn.get("mittel"))
        z.append(zeile("Feldfehler Spulen gegen Plasmarand (REQ-F04)", f"{bn:.3g}" if isinstance(bn, float) else str(bn), "≤ 2,5e-3", "Annahme (Bezug DATJ5FC, Lastenheft)", (bn <= 2.5e-3) if isinstance(bn, float) else None, f"{k2}/P1.json"))
    if P2:
        from itertools import chain
        s_ok = 1e9
        for eb in P2["ebenen"].values():
            for l in eb["linien"]:
                if l["verloren"] or l["rms_rel"] > 0.02: s_ok = min(s_ok, l["s_start"] - 1e-9)
        ss = [l["s_start"] for eb in P2["ebenen"].values() for l in eb["linien"] if l["s_start"] <= s_ok]
        z.append(zeile("Magnetische Flächen geschlossen bis s", f"{max(ss):.2f}", "≥ 0,8", "Annahme (Arbeitskriterium K2: rms ≤ 2 %)", max(ss) >= 0.8, f"{k2}/P2.json"))
    if P4:
        z.append(zeile("Spulen ohne Rücklauf / ohne Kreuzung (REQ-F05)", f"{P4['spulen_mit_ruecklauf']} / {P4['nachbarpaare_kreuzend']}", "0 / 0", "Vorgabe Autor", P4["spulen_mit_ruecklauf"] == 0 and P4["nachbarpaare_kreuzend"] == 0, f"{k2}/P4.json"))
        z.append(zeile("Biegeradius / Wickelpaket R_min/d (REQ-F05)", f"{P4['R_min_durch_d']:.2f}", "≥ 2,0", "Vorgabe Autor", P4["R_min_durch_d"] >= 2.0, f"{k2}/P4.json"))
    if P3:
        lf = P3["leiterfeld"]["B_leiter_bei_B0_bilanz_T"]
        z.append(zeile("Feld am Leiter (HTS)", f"{lf:.2f} T", "≤ 20 T", "Annahme (Werkzeug invers/stufe0_bilanz.py)", lf <= 20.0, f"{k2}/P3.json"))
    if qi:
        pass
    if e:
        z.append(zeile("QI-Güte der Plasmaform (REQ-F02)", f"{e['qi']:.3g}", "≤ 5e-4", "Pool-Kriterium (B-028)", e["qi"] <= 5e-4, "~/cae_projekte/gx/laeufe/<ID>/ergebnis_vmec.json (ausserhalb Repo)"))
    # K2e
    a = J(f"sim/kandidat/K2e/{UN}/auswertung.json")
    if a:
        z.append(zeile("K2e: übernommene Variante", str(a.get("gewaehlt")), "Regel aus Erwartung K2e", "Setzung Opus", None, f"sim/kandidat/K2e/{UN}/auswertung.json"))
    # K3
    k3 = J(f"sim/kandidat/K3/{UN}/auswertung.json")
    if k3:
        r = {x["s"]: x for x in k3["felder"]["spulen"]["flaechen"]}
        z.append(zeile("Alphaverlust s = 0,25 bis t_max (REQ-F09)", f"{100 * r[0.25]['anteil']:.1f} %", "≤ 10 % (Deutungsgrenze Erwartung K3)", "Setzung Opus", r[0.25]["anteil"] <= 0.10, f"sim/kandidat/K3/{UN}/auswertung.json"))
        z.append(zeile("Alphaverlust s = 0,5 bis t_max", f"{100 * r[0.5]['anteil']:.1f} %", "Erwartungsband 3–15 %", "Erwartung (kein Grenzwert)", None, f"sim/kandidat/K3/{UN}/auswertung.json"))
    k4 = J(f"sim/kandidat/K4/{UN}/auswertung.json")
    if k4:
        z.append(zeile("Turbulenz: GX-Fluss / nötiger Fluss (REQ-F11)", f"{k4['verhaeltnis']:.2f}", "≤ 3 (Deutungsgrenze Erwartung K4; > 3 = H 1,3 fraglich)", "Setzung Opus", k4["verhaeltnis"] <= 3, f"sim/kandidat/K4/{UN}/auswertung.json"))
    k5 = J(f"sim/kandidat/K5/{UN}/auswertung.json")
    if k5:
        z.append(zeile("Freier Platz Plasma–Wickelpaket min (REQ-F08)", f"{k5['frei_min_m']:.2f} m", "≥ 2,1 m (Summe Aufbau 1,73–2,13 m)", "Annahme (Aufbau aus Kraftwerksstudien, nicht belegt)", k5["frei_min_m"] >= 2.1, f"sim/kandidat/K5/{UN}/auswertung.json"))
    k6 = J(f"sim/kandidat/K6/{UN}/auswertung.json")
    if k6:
        z.append(zeile("Neutronen-Wandlast Spitze (REQ-F10)", f"{k6['neutronen']['spitze_MW_m2']:.2f} MW/m²", "≤ 2 MW/m²", "Annahme (Werkzeug)", k6["neutronen"]["spitze_MW_m2"] <= 2.0, f"sim/kandidat/K6/{UN}/auswertung.json"))
        z.append(zeile("Wärmebilanz geschlossen", f"{k6['bilanz_schliessung_prozent']:+.2f} %", "± 2 %", "Setzung Opus", abs(k6["bilanz_schliessung_prozent"]) <= 2, f"sim/kandidat/K6/{UN}/auswertung.json"))
    return z


def auszuege(schritt):
    p = P / f"sim/kandidat/{schritt}" / ("ERGEBNIS_test.md" if TEST and (P / f"sim/kandidat/{schritt}/ERGEBNIS_test.md").exists() else "ERGEBNIS.md")
    if not p.exists():
        return None, []
    t = p.read_text(encoding="utf-8").splitlines()
    return p.relative_to(P).as_posix(), [x for x in t if x.startswith("|") and re.search(r"Grenze|Erwartung|erfüllt|≤|≥", x)][:12] + [x for x in t[:3] if x.startswith("HALT")]


def main():
    t0 = time.strftime("%F %T"); z = zeilen(); rest = {s: auszuege(s) for s in ("K7", "K8", "K9", "K10")}
    L = ["| Dok.-Nr. | FUS-ERG-K11 | Version | 0.1 | Status | Entwurf |", "|---|---|---|---|---|---|",
         "| Titel | Ergebnis K11 · Absprungbasis prüfen: Tabelle der Grenzen (Zusammenstellung) | Ersteller | Claude Sonnet 5.5 (KI) | Prüfer | – (Opus/Mensch offen) |", "",
         "> **KI-generiert (Claude Sonnet 5.5, 2026-11-13).** Erwartung `sim/kandidat/erwartung/K11.md` (unverändert). Reine Zusammenstellung der Zahlen aus den Ergebnisdateien, **keine Deutung, keine Freigabe** (die setzt nur der Autor)."
         + (" **RAUCHTEST: Testordner der Schritte, grobe Zahlen.**" if TEST else ""), f"> Stand kandidat.json: {K['stand']}; R0 {K['R0_m']} m, B0 {K['B0_T']} T. Erstellt {t0} (date).", "",
         "## 1 Grenzen K2–K6 (Spalte „erfüllt“ = reiner Zahlenvergleich Wert gegen Grenze)", "| Anforderung | Wert | Grenze | Art der Grenze | erfüllt | Quelle |", "|---|---|---|---|---|---|"]
    for r in z:
        L.append(f"| {r['anforderung']} | {r['wert']} | {r['grenze']} | {r['art']} | {'–' if r['erfuellt'] is None else ('ja' if r['erfuellt'] else 'nein')} | `{r['quelle']}` |")
    L += ["", "## 2 K7–K10 (unveränderte Zeilen aus deren ERGEBNIS.md, soweit vorhanden)"]
    for s, (p, rows) in rest.items():
        L.append(f"**{s}**: " + (f"`{p}`" if p else "ERGEBNIS.md liegt noch nicht vor."))
        L += rows
    L += ["", "## 3 Anforderungsverfolgung", ("Im Test nicht erneut erzeugt." if TEST else "`docs/projekt/03_anforderungsverfolgung.md` und `pm/plan/wissensnetz.json/.html` mit `pm/plan/wissensnetz.py` neu erzeugt (Vorgang K<n> fertig, wenn `sim/kandidat/K<n>/ERGEBNIS.md` existiert)."), "",
          "Die Wertung „Absprungbasis erreicht / nicht erreicht“ steht nicht hier (Deutung bei Opus, Freigabe beim Autor).", "", "---", "*KI-generiert (Claude Sonnet 5.5), Entwurf, nicht geprüft.*"]
    ziel = OUT / "ERGEBNIS_test.md" if TEST else P / "sim/kandidat/K11/ERGEBNIS.md"
    ziel.write_text("\n".join(L) + "\n", encoding="utf-8"); (OUT / "tabelle.json").write_text(json.dumps(z, indent=1, ensure_ascii=False))
    if not TEST:
        sys.path.insert(0, str(P / "pm/plan")); import wissensnetz as W
        for n in ("K2", "K2e", "K3", "K4", "K5", "K6", "K7", "K8", "K9", "K10", "K11"):
            f = f"sim/kandidat/{n}/ERGEBNIS.md"
            if (P / f).exists(): W.AUS.setdefault(n, []).append(f)
        W.main()
    print("K11 Ende", time.strftime("%F %T"), len(z), "Zeilen")


if __name__ == "__main__":
    main()
