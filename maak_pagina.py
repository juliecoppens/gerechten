#!/usr/bin/env python3
"""Maakt van een CSV-export uit Notion één index.html met filterknoppen.

Gebruik:
    python maak_pagina.py                 (leest gerechten.csv naast dit script)
    python maak_pagina.py mijnbestand.csv

Regels voor de CSV:
- Eerste kolom = naam van het gerecht.
- Kolommen 'Notities', 'Notes', 'Description' of 'Beschrijving' = vrije tekst, wordt onder het gerecht getoond.
- Alle andere kolommen worden een filtergroep (bv. Carbs, Meat, Moeite).
- Meerdere waarden in één cel staan gescheiden door een komma: "Kip, Gehakt".
"""
import csv
import difflib
import json
import sys
from pathlib import Path

NOTITIE_KOLOMMEN = {"notities", "notes", "notitie", "description", "beschrijving"}
VASTE_VOLGORDE = {
    "moeite": ["Makkelijk", "Gemiddeld", "Moeilijk"],
    "tijd": ["Snel", "Gemiddeld", "Lang"],
    "etentje": ["Ja", "Misschien", "Nee"],
}


def lees_csv(pad):
    with open(pad, newline="", encoding="utf-8-sig") as f:
        rijen = list(csv.reader(f))
    if len(rijen) < 2:
        sys.exit("Het CSV-bestand heeft geen gerechten.")
    kop = [k.strip() for k in rijen[0]]
    titel_i = 0
    notitie_i = [i for i, k in enumerate(kop) if k.lower() in NOTITIE_KOLOMMEN]
    groep_i = [i for i in range(len(kop)) if i != titel_i and i not in notitie_i and kop[i]]

    gerechten = []
    for rij in rijen[1:]:
        rij = rij + [""] * (len(kop) - len(rij))
        naam = rij[titel_i].strip()
        if not naam:
            continue
        tags = {}
        for i in groep_i:
            waarden = []
            for w in rij[i].split(","):
                w = w.strip()
                if w and w not in waarden:
                    waarden.append(w)
            tags[kop[i]] = waarden
        notitie = " – ".join(t for t in (rij[i].strip() for i in notitie_i) if t)
        gerechten.append({"name": naam, "notes": notitie, "tags": tags})

    groepen = []
    for i in groep_i:
        naam = kop[i]
        tel = {}
        for g in gerechten:
            for w in g["tags"][naam]:
                tel[w] = tel.get(w, 0) + 1
        vast = VASTE_VOLGORDE.get(naam.lower())
        if vast:
            waarden = [w for w in vast if w in tel] + sorted(w for w in tel if w not in vast)
        else:
            waarden = sorted(tel, key=lambda w: (-tel[w], w.lower()))
        groepen.append({"name": naam, "values": waarden})
    return {"groups": groepen, "dishes": gerechten}


def waarschuw_bij_bijna_dubbele_tags(data):
    for groep in data["groups"]:
        gezien = set()
        for w in groep["values"]:
            for ander in difflib.get_close_matches(w, groep["values"], n=5, cutoff=0.8):
                paar = tuple(sorted((w, ander)))
                if ander != w and paar not in gezien:
                    gezien.add(paar)
                    print(f"  Let op ({groep['name']}): '{paar[0]}' en '{paar[1]}' lijken op elkaar. Typfout?")


HTML = r"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Wat eten we?</title>
<style>
:root {
  color-scheme: light dark;
  --bg: #f3f6f4; --ink: #17231f; --muted: #5d6b65; --line: #d5ddd8;
  --accent: #1f6b4f; --on-accent: #ffffff; --chip: #e4ebe7;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #121a17; --ink: #e8efeb; --muted: #9aaaa2; --line: #2b3832;
          --accent: #6fcf9f; --on-accent: #0c1a13; --chip: #1e2a25; }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: 16px/1.45 "Avenir Next", "Segoe UI", system-ui, sans-serif;
  padding: env(safe-area-inset-top, 0) env(safe-area-inset-right, 0) env(safe-area-inset-bottom, 0) env(safe-area-inset-left, 0);
}
.top { padding: 14px 16px 2px; }
.bar {
  position: sticky; top: 0; z-index: 5; background: var(--bg);
  border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 6px 16px;
}
.bar .wrap { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.wrap { max-width: 640px; margin: 0 auto; }
h1 { font: 700 1.5rem/1.2 Georgia, "Iowan Old Style", serif; margin: 0 0 10px; }
input[type=search] {
  width: 100%; font: inherit; color: inherit; background: var(--chip);
  border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; margin-bottom: 10px;
}
.row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.glabel { flex: 0 0 4.2rem; font-size: .85rem; color: var(--muted); }
.chips { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 2px; scrollbar-width: none; }
.chips::-webkit-scrollbar { display: none; }
.chip {
  flex: 0 0 auto; font: inherit; font-size: .9rem; color: var(--ink); background: var(--chip);
  border: 1px solid var(--line); border-radius: 999px; padding: 6px 12px; cursor: pointer;
}
.chip[aria-pressed=true] { background: var(--accent); border-color: var(--accent); color: var(--on-accent); font-weight: 600; }
.chip:focus-visible, input:focus-visible, .reset:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.count { font-size: .9rem; color: var(--muted); }
.acties { display: flex; gap: 14px; flex: 0 0 auto; }
.reset { font: inherit; font-size: .9rem; color: var(--accent); background: none; border: 0; padding: 4px 0; cursor: pointer; text-decoration: underline; }
main { padding: 6px 16px 40px; }
ul { list-style: none; margin: 0; padding: 0; }
li { padding: 12px 0; border-bottom: 1px solid var(--line); }
.naam { font: 600 1.15rem/1.3 Georgia, "Iowan Old Style", serif; }
.tags { margin-top: 4px; display: flex; flex-wrap: wrap; gap: 4px 12px; font-size: .88rem; color: var(--muted); }
.tags .on { color: var(--accent); font-weight: 700; }
.notes { margin-top: 4px; font-size: .9rem; color: var(--muted); font-style: italic; }
.leeg { padding: 28px 0; color: var(--muted); }
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Wat eten we?</h1>
  <div id="panel">
    <input id="q" type="search" placeholder="Zoek een gerecht" aria-label="Zoek een gerecht">
    <div id="filters"></div>
  </div>
</div></header>
<div class="bar"><div class="wrap">
  <span id="count" class="count"></span>
  <span class="acties">
    <button id="reset" class="reset" type="button" hidden>Wis filters</button>
    <button id="toggle" class="reset" type="button" aria-controls="panel" aria-expanded="true">Verberg filters</button>
  </span>
</div></div>
<main><div class="wrap"><ul id="list"></ul><p id="leeg" class="leeg" hidden>Geen gerecht gevonden. Haal een filter weg of wis je zoekopdracht.</p></div></main>
<script>
const DATA = __DATA__;
const sel = {};
DATA.groups.forEach(g => sel[g.name] = new Set());
let q = "";
const $ = id => document.getElementById(id);

function el(tag, props, kids) {
  const e = Object.assign(document.createElement(tag), props || {});
  (kids || []).forEach(k => e.append(k));
  return e;
}

function buildFilters() {
  DATA.groups.forEach(g => {
    if (!g.values.length) return;
    const chips = el("div", { className: "chips" });
    g.values.forEach(v => {
      const b = el("button", { className: "chip", type: "button", textContent: v });
      b.setAttribute("aria-pressed", "false");
      b.addEventListener("click", () => {
        const s = sel[g.name];
        s.has(v) ? s.delete(v) : s.add(v);
        b.setAttribute("aria-pressed", String(s.has(v)));
        render();
      });
      chips.append(b);
    });
    $("filters").append(el("div", { className: "row" }, [el("span", { className: "glabel", textContent: g.name }), chips]));
  });
}

function matches(d) {
  if (q) {
    const hay = (d.name + " " + d.notes).toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return DATA.groups.every(g => {
    const s = sel[g.name];
    return s.size === 0 || d.tags[g.name].some(v => s.has(v));
  });
}

function actieve() {
  const lijst = [];
  DATA.groups.forEach(g => sel[g.name].forEach(v => lijst.push(v)));
  if (q) lijst.push("\u201c" + q + "\u201d");
  return lijst;
}
function active() { return actieve().length > 0; }
let open = true;

function render() {
  const hits = DATA.dishes.filter(matches).sort((a, b) => a.name.localeCompare(b.name, "nl"));
  const list = $("list");
  list.replaceChildren();
  hits.forEach(d => {
    const tags = el("div", { className: "tags" });
    DATA.groups.forEach(g => d.tags[g.name].forEach(v =>
      tags.append(el("span", { className: sel[g.name].has(v) ? "on" : "", textContent: v }))));
    const li = el("li", {}, [el("div", { className: "naam", textContent: d.name }), tags]);
    if (d.notes) li.append(el("div", { className: "notes", textContent: d.notes }));
    list.append(li);
  });
  $("leeg").hidden = hits.length > 0;
  const act = actieve();
  let tekst = hits.length + " van " + DATA.dishes.length + " gerechten";
  if (!open && act.length) tekst += " (" + act.join(", ") + ")";
  $("count").textContent = tekst;
  $("reset").hidden = act.length === 0;
  $("panel").hidden = !open;
  $("toggle").setAttribute("aria-expanded", String(open));
  $("toggle").textContent = (open ? "Verberg filters" : "Toon filters") + (!open && act.length ? " (" + act.length + ")" : "");
}

$("q").addEventListener("input", e => { q = e.target.value.trim().toLowerCase(); render(); });
$("toggle").addEventListener("click", () => {
  open = !open;
  if (open) window.scrollTo({ top: 0 });
  render();
});
$("reset").addEventListener("click", () => {
  q = ""; $("q").value = "";
  DATA.groups.forEach(g => sel[g.name].clear());
  document.querySelectorAll(".chip").forEach(b => b.setAttribute("aria-pressed", "false"));
  render();
});

buildFilters();
render();
</script>
</body>
</html>
"""


def main():
    hier = Path(__file__).resolve().parent
    csv_pad = Path(sys.argv[1]) if len(sys.argv) > 1 else hier / "gerechten.csv"
    if not csv_pad.exists():
        sys.exit(f"Bestand niet gevonden: {csv_pad}")
    data = lees_csv(csv_pad)
    json_tekst = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    uit = csv_pad.parent / "index.html"
    uit.write_text(HTML.replace("__DATA__", json_tekst), encoding="utf-8")
    print(f"Klaar: {uit}")
    print(f"  {len(data['dishes'])} gerechten, filtergroepen: {', '.join(g['name'] for g in data['groups'])}")
    waarschuw_bij_bijna_dubbele_tags(data)


if __name__ == "__main__":
    main()
