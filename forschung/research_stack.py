#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""forschung / research_stack.py — Abfrage-Kit für den wasserstoff-Vorgang.

Quellen (Zustand 2026-10-08, keylos, real gemessen):

  arXiv            ✅ keyless, liefert                       (arxiv.org)
  PubMed (NCBI)    ✅ keyless, liefert                       (ncbi.nlm.nih.gov)
  Semantic Scholar ⚠️ hart 429 ohne Key  → export S2_API_KEY="…" (kostenloses Formular)
  Google Patents   ⚠️ 1 Request/s → OK (GP_RATE_S); dicht = 503 (B-RS-006)
  EPO OPS          ⏸ fertig (OAuth2 3.2) — nur Key nötig: developers.epo.org
                   export OPS_USER='epo…'  OPS_KEY='…'  (Fair-use, ~4 Mio/Monat)
  SerpApi          ⏸ optional (Freemium), export SERPAPI_KEY="…"

Aufruf:
  .venv/bin/python forschung/research_stack.py [arxiv pubmed s2 ops serapi gp ...]
    ohne Argument      → nur die keyless Quellen
    arxiv pubmed s2     → beliebige Teilmenge
    ops                 → benötigt OPS_TOKEN
    serapi              → benötigt SERPAPI_KEY
    gp                  → nur als Warnung (hier blockiert)
Sonderbefehle:
  -q "Text"            → eigene Suchanfrage statt des Standard-Themas
  -n 10               → Anzahl (Default 5)
  -j                  → JSON-Ausgabe (für nachbearbeitete Kuratierung)

Standard-Themen (falls -q fehlt) — validierte Phrasen-Queries, nicht verpackt:
  arxiv     "hydrogen fuel cell" AND (aircraft OR aviation OR propulsion)
  pubmed    "hydrogen fuel cell" AND (aircraft OR aviation OR propulsion OR airplane)
  s2        "hydrogen fuel cell" (aircraft OR aviation OR propulsion)
  ops       hydrogen fuel cell aircraft OR aviation OR propulsion
  serapi    hydrogen fuel cell aircraft propulsion
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64; wasserstoff-research/1.0"

def _load_dotenv():
    """.env laden (CWD, dann Projekt-Root) — Datei enthält KEINE Keys, nur
    export-Vorlagen .env.example. Reale Keys: .env (nicht committen!) oder export."""
    import pathlib
    here = pathlib.Path(__file__).resolve().parent
    for base in (pathlib.Path.cwd(), here, here.parent):
        f = base / ".env"
        if f.is_file():
            for ln in f.read_text().splitlines():
                ln = ln.strip()
                if not ln or ln.startswith("#") or "=" not in ln:
                    continue
                k, v = [x.strip() for x in ln.split("=", 1)]
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
            return

_load_dotenv()

def _get(url: str, timeout: int = 30, headers: dict | None = None) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)

# ---------------------------------------------------------------- arXiv
def q_arxiv(query: str, n: int = 5) -> list[dict]:
    # Q bereits vollständig (Phrasen + OR-Klauseln); NICHT mit all:(...) umwickeln!
    params = urllib.parse.urlencode({"search_query": query,
                                     "start": 0, "max_results": n,
                                     "sortBy": "relevance", "sortOrder": "descending"})
    url = f"http://export.arxiv.org/api/query?{params}"
    status, body = _get(url)
    if status != 200:
        raise RuntimeError(f"arXiv HTTP {status}")
    import xml.etree.ElementTree as ET
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(body)
    out = []
    for e in root.findall("a:entry", ns):
        g = lambda k: (e.find(f"a:{k}", ns).text or "").strip()
        out.append({"id": g("id"), "year": g("published")[:4],
                    "title": re.sub(r"\s+", " ", g("title")).strip(),
                    "authors": [a.find("a:name", ns).text for a in e.findall("a:author", ns)[:5]],
                    "abstract": re.sub(r"\s+", " ", g("summary"))[:400],
                    "pdf": ""})
        for link in e.findall("a:link", ns):
            if link.get("title") == "pdf":
                out[-1]["pdf"] = link.get("href", "")
    return out

# ---------------------------------------------------------------- PubMed
def q_pubmed(query: str, n: int = 5) -> list[dict]:
    enc = urllib.parse.quote(query)
    st1, body1 = _get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={enc}&retmax={n}&retmode=json")
    if st1 != 200:
        raise RuntimeError(f"PubMed ESearch HTTP {st1}")
    ids = json.loads(body1).get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    time.sleep(0.4)
    # Esummary liefert sauberes JSON (Titel, DOI, Journal, Datum) — stabiler als EFetch-Text
    st2, body2 = _get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(ids)}&retmode=json")
    if st2 != 200:
        raise RuntimeError(f"PubMed ESummary HTTP {st2}")
    data = json.loads(body2).get("result", {})
    out = []
    for pid in ids:
        r = data.get(pid, {})
        doi = next((v.get("value", "") for v in r.get("articleids", []) if v.get("idtype") == "doi"), "")
        out.append({"pmid": pid, "doi": doi,
                    "title": r.get("title", "")[:160],
                    "journal": r.get("fulljournalname", r.get("source", "")),
                    "date": r.get("pubdate", ""),
                    "abstract": (r.get("softwarning") or "")})
    return out

# ---------------------------------------------------------------- Semantic Scholar
def q_s2(query: str, n: int = 5) -> list[dict]:
    enc = urllib.parse.quote(query)
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={enc}&limit={n}&fields=title,year,externalIds,citationCount,authors,abstract"
    key = os.environ.get("S2_API_KEY", "")
    headers = {"x-api-key": key} if key else {}
    last = None
    for attempt in range(3):
        status, body = _get(url, headers=headers)
        last = body
        if status == 200:
            data = json.loads(body)
            pubs = data.get("data", [])
            return [{"id": p.get("paperId"), "year": p.get("year"),
                     "title": p.get("title"),
                     "doi": (p.get("externalIds") or {}).get("DOI"),
                     "cites": p.get("citationCount"),
                     "authors": [a.get("name") for a in (p.get("authors") or [])[:5]],
                     "abstract": (p.get("abstract") or "")[:400]}
                    for p in pubs]
        if status in (429, 503):
            time.sleep(2 + attempt * 3)
            continue
        break
    msg = (last or "")[:200]
    if "429" in str(last) or not key:
        raise RuntimeError("S2: hart 429 (Key erforderlich) — kostenloses Formular: "
                           "https://www.semanticscholar.org/product/api#api-key-form, dann: export S2_API_KEY=…")
    raise RuntimeError(f"S2 HTTP {status}: {msg}")

# ---------------------------------------------------------------- EPO OPS 3.2
# Auth: OAuth2 client_credentials — Basic(User:Key) → Bearer-JWT (cache ~2 h).
#   Token:  developers.epo.org  →  Account  →  "My Apps" / API keys (free).
#   Env:    export OPS_USER='epo123456'  export OPS_KEY='<api-key>'
#   (oder zusammen: OPS_TOKEN='epo123456 <api-key>')
# Query:    OPS-Synopsis (keine Free-Text-Sprache!), z. B.
#             ti=(fuel cell) AND ti=hydrogen
#             ab=(bipolar plate) AND pd>=2020
#             pa=(Bosch) AND ti=(fuel cell)
#           Freies Eingabetext ohne Feld-Operator wird automatisch nach ti=(...) gemappt.
OPS_BASE = "https://ops.epo.org"
_ops_jwt = {"value": "", "exp": 0.0}

def _ops_userkey():
    raw = (os.environ.get("OPS_TOKEN", "") or "").strip()
    user = (os.environ.get("OPS_USER", "") or "").strip()
    if raw and " " in raw:
        user, key = raw.split(None, 1)
    else:
        key = raw
    if not user or not key:
        raise RuntimeError("OPS-Zugang fehlt: Token kostenlos anfordern "
                           "https://developers.epo.org (Account → API keys), dann "
                           "export OPS_USER='epo…'  OPS_KEY='…' "
                           "(oder OPS_TOKEN='epo… <key>'). Fair-use Charter beachten.")
    return user, key

def _ops_auth() -> str:
    if _ops_jwt["value"] and time.time() < _ops_jwt["exp"] - 60:
        return _ops_jwt["value"]
    user, key = _ops_userkey()
    creds = base64.b64encode(f"{user}:{key}".encode()).decode()
    url = f"{OPS_BASE}/3.2/auth/accesstoken?grant_type=client_credentials"
    req = urllib.request.Request(url, method="POST", headers={
        "User-Agent": UA, "Authorization": f"Basic {creds}",
        "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            token = r.read().decode().strip()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:220]
        hint = ("— Zugangsdaten prüfen (OPS_USER muss mit dem Account stimmen, Key kopiert)"
                if e.code in (401, 403) else "— Token-Endpoint nicht erreichbar")
        raise RuntimeError(f"OPS-Auth HTTP {e.code}: {detail} {hint}")
    except Exception as e:
        raise RuntimeError(f"OPS-Auth: {e}")
    _ops_jwt.update(value=token, exp=time.time() + 7200)
    return token

def _ops_get(path: str, params: dict) -> tuple[int, str]:
    url = f"{OPS_BASE}/3.2/rest-services/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Authorization": f"Bearer {_ops_auth()}",
        "Accept": "application/xml"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)

def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]

def q_ops(query: str, n: int = 10) -> list[dict]:
    """OPS-Bibliothekssuche → Titel/Nr/Datum/Applicant/URL. (OPS-Synopsis, s. Docstring oben.)"""
    if not re.search(r"^\s*[a-z]+\s*=", query, re.I):
        query = f"ti=({query})"
    status, body = _ops_get("published-data/search", {"q": query, "Range": f"1-{n}"})
    if status != 200:
        raise RuntimeError(f"EPO OPS HTTP {status}: {body[:260]} — "
                           f"401/403 = Key, 400 = Query-Syntax (OPS-Operator: ti=, ab=, pa=, pd>=).")
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        raise RuntimeError(f"OPS-Antwort ist kein XML: {body[:200]}")
    out = []
    for rec in (el for el in root.iter() if _local(el.tag) == "biblio"):
        desc = lambda local: next((e for e in rec.iter() if _local(e.tag) == local), None)
        e = desc("publication-number")
        pubnr = re.sub(r"\s+", "", (e.text or "").strip()) if e is not None else ""
        e = desc("publication-date") or desc("application-date")
        year = ((e.text or "").strip()[:4]) if e is not None else ""
        e = desc("title")
        title = re.sub(r"\s+", " ", (e.text or "").strip())[:160] if e is not None else ""
        ap = next((a.get("name", "").strip() for a in rec.iter()
                   if _local(a.tag) == "applicant" and a.get("name")), "")
        out.append({"pubnr": pubnr, "year": year, "title": title,
                    "applicant": ap,
                    "url": f"https://worldwide.espacenet.com/patent/search?q=pjn:{pubnr}"})
        if len(out) >= n:
            break
    return out

def q_ops_pub(pubnr: str, part: str = "biblio") -> list[dict]:
    """Volldaten einer einzelnen Publikation nach Nummer, z. B. q_ops_pub('EP2364703A1').
    part: biblio | abstract | fulltext | claims | full-cycle"""
    pubnr = re.sub(r"\s+", "", pubnr)
    m = re.match(r"([A-Z]{2}\d+[A-Z0-9]*)", pubnr)
    if not m:
        raise RuntimeError(f"'{pubnr}' sieht keine gültige OPS-Nummer an (expected: EPOfffffx).")
    num = m.group(1)
    country = num[:2]
    status, body = _ops_get(f"published-data/publication/{country}/{num}/{part}", {})
    if status != 200:
        raise RuntimeError(f"EPO OPS HTTP {status}: {body[:260]}")
    import xml.etree.ElementTree as ET
    root = ET.fromstring(body)
    txt = re.sub(r"\n{3,}", "\n\n", "".join(
        (t or "").strip() for t in root.iter() if _local(t.tag) in ("text", "title")))
    return [{"pubnr": num, "part": part, "text": txt[:1200],
             "url": f"https://worldwide.espacenet.com/patent/search?q=pjn:{num}"}]

# ---------------------------------------------------------------- SerpApi (Google Patents / Google)
def q_serpapi(query: str, n: int = 5) -> list[dict]:
    key = os.environ.get("SERPAPI_KEY", "")
    if not key:
        raise RuntimeError("SERPAPI_KEY fehlt. Kostenlos: https://serpapi.com (Freemium). "
                           "Dann: export SERPAPI_KEY=…")
    url = (f"https://serpapi.com/search.json?engine=google_patents&num={n}&q={urllib.parse.quote(query)}"
           f"&api_key={urllib.parse.quote(key)}")
    status, body = _get(url)
    if status != 200:
        raise RuntimeError(f"SerpApi HTTP {status}: {body[:300]}")
    data = json.loads(body)
    out = []
    for r in data.get("results", data.get("patents", []))[:n]:
        out.append({"pubnr": r.get("patent_number", r.get("patentNumber", "")),
                    "title": r.get("title", r.get("patent_title", ""))[:120],
                    "year": str(r.get("grant_date", r.get("filing_date", "")))[:4],
                    "assignee": r.get("assignee", r.get("applicant", "")),
                    "url": r.get("patent_url", r.get("url", ""))})
    return out

# ---------------------------------------------------------------- Google Patents
# Hinweis: Abfragen mit Abstand (>=1 s zwischen Requests) liefern HTTP 200;
# dichte Folgeabfragen triggern den Bot-Schutz (503/400). GP_RATE_S steuert den
# Mindestabstand — bei Blockade einfach erhöhen (2 s, 3 s ...).
GP_RATE_S = float(os.environ.get("GP_RATE_S", "1.0"))
_gp_last = [0.0]

def _gp_wait():
    delta = time.monotonic() - _gp_last[0]
    if delta < GP_RATE_S:
        time.sleep(GP_RATE_S - delta)
    _gp_last[0] = time.monotonic()

def q_gp(query: str, n: int = 5, retries: int = 3) -> list[dict]:
    """Google Patents XHR-Query (1 s/Request, UA + Referer, Backoff bei 503)."""
    base = ("https://patents.google.com/xhr/query?url="
            + urllib.parse.urlencode({"q": query, "num": n}))
    headers = {
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0 Safari/537.36"),
        "Accept": "application/json",
        "Referer": "https://patents.google.com/",
    }
    last_err = None
    # Bewusst großzügiger Backoff (15 s, 30 s): bei 503 (Cooldown/Block)
    # schnell wieder anzupacken verlängert den Block. 2 Retries genügen.
    for attempt in range(2):
        _gp_wait()
        try:
            req = urllib.request.Request(base, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read())
            cluster = data.get("results", {}).get("cluster", [])
            out = []
            for grp in cluster[:1]:
                for res in (grp.get("result") or [])[:n]:
                    pt = res.get("patent", {})
                    assignees = pt.get("assigneeCurrent", []) or pt.get("assigneeOriginal", [])
                    out.append({
                        "pubnr": (res.get("id") or "").replace("patent/", "").split("/")[0],
                        "title": (pt.get("title") or "").strip()[:160],
                        "year": (pt.get("priority") or pt.get("publicationDate") or "")[:4],
                        "assignee": (assignees[0] if assignees else ""),
                        "url": f"https://patents.google.com/{res.get('id', '')}",
                        "abstract": (pt.get("abstract") or "")[:200],
                    })
            return out
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (400, 403, 429, 503):
                # 503 = IP-Cooling: lang genug warten, dass der Block abklingt.
                time.sleep(15 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Google Patents blockiert/Cooldown (letzter Fehler: {last_err}). "
                       f"Nach 503: ~5 min pausieren, dann erneut mit <=1 RF/s. "
                       f"Oder EPO-OPS / SerpApi (s. B-RS-003/B-RS-006).")

# ---------------------------------------------------------------- Output
def _print(label: str, rows: list[dict], as_json: bool):
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    print(f"[{label}] {len(rows)} Treffer")
    for i, r in enumerate(rows, 1):
        title = r.get("title") or r.get("pubnr") or r.get("pmid") or "?"
        sub = ""
        if r.get("year"):
            sub += f"  {r['year']}"
        if r.get("doi"):
            sub += f"  doi:{r['doi']}"
        if r.get("pmid"):
            sub += f"  PMID {r['pmid']}"
        if r.get("pubnr"):
            sub += f"  {r['pubnr']}"
        if r.get("assignee") or r.get("applicant"):
            sub += f"  → {(r.get('assignee') or r.get('applicant'))[:40]}"
        print(f"  {i:>2} {title[:85]}{sub}")
        url = r.get("url") or r.get("pdf") or r.get("id") or ""
        if url:
            print(f"      {url}")
        if r.get("abstract"):
            print(f"      {r['abstract'][:160]}")
        print()

# ---------------------------------------------------------------- Main
DEFAULTS = {
    "arxiv":  ("arxiv",  '"hydrogen fuel cell" AND (aircraft OR aviation OR propulsion) OR ("hydrogen" AND "fuel cell" AND "electric propulsion")'),
    "pubmed": ("pubmed", '"hydrogen fuel cell" AND (aircraft OR aviation OR propulsion OR airplane)'),
    "s2":     ("s2",     "\"hydrogen fuel cell\" (aircraft OR aviation OR propulsion OR airplane)"),
    "ops":    ("ops",    "hydrogen fuel cell aircraft OR aviation OR propulsion"),
    "serapi": ("serapi", "hydrogen fuel cell aircraft propulsion"),
    "gp":     ("gp",     "hydrogen fuel cell aircraft"),
}
QUERIES = {
    "arxiv":  q_arxiv,
    "pubmed": q_pubmed,
    "s2":     q_s2,
    "ops":    q_ops,
    "serapi": q_serpapi,
    "gp":     q_gp,
}

def main():
    global DEFAULTS
    ap = argparse.ArgumentParser(description="Wasserstoff-Forschungs- und Patent-Quellen")
    ap.add_argument("sources", nargs="*", help=" ".join(list(DEFAULTS) + ["all"]))
    ap.add_argument("-q", "--query", help="Eigene Suchanfrage (überschreibt die Standards)")
    ap.add_argument("-n", "--num", type=int, default=5)
    ap.add_argument("-j", "--json", action="store_true", help="JSON-Ausgabe")
    a = ap.parse_args()

    sources = a.sources or ["arxiv", "pubmed"]
    if "all" in sources:
        sources = [s for s in DEFAULTS]
    if a.query:
        DEFAULTS = {k: (k, a.query) for k in DEFAULTS}

    failed = []
    for src in sources:
        if src not in DEFAULTS:
            print(f"[warn] unbekannte Quelle '{src}' — übersprungen", file=sys.stderr)
            continue
        label, dflt = DEFAULTS[src]
        query = dflt  # -q überschreibt alle
        try:
            rows = QUERIES[src](query, a.num)
            _print(src, rows or [], a.json)
            if not rows:
                print(f"[{src}] (keine Treffer)\n")
        except RuntimeError as e:
            msg = str(e)
            code = "NEEDS_KEY" if any(k in msg for k in ("fehlt", "429", "Token", "KEY")) else "ERR"
            status = "⏸" if code == "NEEDS_KEY" else "❌"
            print(f"[{src}] {status} {msg}")
            failed.append(src)
    if failed:
        print(f"\nSummary: {len(sources) - len(failed)}/{len(sources)} OK — "
              f"Nicht erreichbar: {', '.join(failed)}", file=sys.stderr)

if __name__ == "__main__":
    main()
