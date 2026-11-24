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
- Kolom 'Personen' = voor hoeveel personen de ingrediënten van dat gerecht zijn
  opgeschreven (leeg = 2). Het is geen filter.
- Optioneel: ingredienten.csv naast gerechten.csv, met de kolommen
  Dish, Ingredient, Amount, Unit (één regel per ingrediënt).
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


def lees_rijen(pad):
    with open(pad, newline="", encoding="utf-8-sig") as f:
        eerste = f.readline()
        f.seek(0)
        # Nederlandse/Belgische Excel slaat CSV op met puntkomma's: herken dat automatisch.
        scheiding = max(",;\t", key=eerste.count)
        return list(csv.reader(f, delimiter=scheiding))


def lees_getal(tekst):
    """'400', '1.5', '1,5', '1/2' en '1 1/2' -> float. Leeg -> None. Anders ValueError."""
    t = tekst.strip().replace(",", ".")
    if not t:
        return None
    totaal = 0.0
    for deel in t.split():
        if "/" in deel:
            boven, onder = deel.split("/")
            totaal += float(boven) / float(onder)
        else:
            totaal += float(deel)
    if totaal <= 0:
        raise ValueError("moet groter zijn dan 0")
    return totaal


def lees_csv(pad, fouten):
    rijen = lees_rijen(pad)
    if len(rijen) < 2:
        sys.exit("Het CSV-bestand heeft geen gerechten.")
    kop = [k.strip() for k in rijen[0]]
    titel_i = 0
    notitie_i = [i for i, k in enumerate(kop) if k.lower() in NOTITIE_KOLOMMEN]
    personen_i = next((i for i, k in enumerate(kop) if k.lower() == "personen"), None)
    groep_i = [i for i in range(len(kop))
               if i != titel_i and i not in notitie_i and i != personen_i and kop[i]]

    gerechten = []
    for nr, rij in enumerate(rijen[1:], start=2):
        if len(rij) > len(kop) and any(c.strip() for c in rij[len(kop):]):
            fouten.append(f"gerechten.csv regel {nr} ('{rij[0].strip()}') heeft meer cellen dan de kopregel. "
                          f"Staat er een komma in een cel zonder aanhalingstekens, bv. \"Kip, Gehakt\"?")
            continue
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
        notitie = " \u2013 ".join(t for t in (rij[i].strip() for i in notitie_i) if t)

        base, expliciet = 2, False
        if personen_i is not None and rij[personen_i].strip():
            try:
                getal = lees_getal(rij[personen_i])
                if getal != int(getal):
                    raise ValueError("geen heel getal")
                base, expliciet = int(getal), True
            except (ValueError, ZeroDivisionError):
                fouten.append(f"gerechten.csv regel {nr}: Personen '{rij[personen_i]}' bij "
                              f"'{naam}' is geen heel getal groter dan 0.")
        gerechten.append({"name": naam, "notes": notitie, "tags": tags,
                          "base": base, "ingr": [], "_expliciet": expliciet})

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


def lees_ingredienten(pad, data, fouten):
    rijen = lees_rijen(pad)
    if not rijen:
        return
    kop = [k.strip().lower() for k in rijen[0]]

    def kolom(*namen):
        return next((kop.index(n) for n in namen if n in kop), None)

    d_i = kolom("dish", "gerecht")
    i_i = kolom("ingredient", "ingrediënt")
    a_i = kolom("amount", "hoeveelheid")
    u_i = kolom("unit", "eenheid")
    if d_i is None or i_i is None:
        fouten.append("ingredienten.csv mist de kolom 'Dish' of 'Ingredient'.")
        return
    per_naam = {g["name"].strip().lower(): g for g in data["dishes"]}
    for nr, rij in enumerate(rijen[1:], start=2):
        rij = rij + [""] * (len(kop) - len(rij))
        naam, ingr = rij[d_i].strip(), rij[i_i].strip()
        if not ingr:          # lege sjabloonregel of lege regel: overslaan
            continue
        g = per_naam.get(naam.lower())
        if g is None:
            fouten.append(f"ingredienten.csv regel {nr}: gerecht '{naam}' staat niet in gerechten.csv "
                          f"(typfout?). Ingredient: '{ingr}'.")
            continue
        hoeveelheid = None
        if a_i is not None:
            try:
                hoeveelheid = lees_getal(rij[a_i])
            except (ValueError, ZeroDivisionError):
                fouten.append(f"ingredienten.csv regel {nr}: hoeveelheid '{rij[a_i]}' bij '{ingr}' "
                              f"is geen getal. Gebruik bv. 400, 1.5, 1,5 (tussen aanhalingstekens) of 1/2.")
                continue
        eenheid = rij[u_i].strip() if u_i is not None else ""
        g["ingr"].append({"n": ingr, "a": hoeveelheid, "u": eenheid})


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
summary { list-style: none; cursor: pointer; }
summary::-webkit-details-marker { display: none; }
summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
.tags .ingr { color: var(--accent); text-decoration: underline; }
.ingr-box { margin-top: 10px; padding: 10px 14px 8px; background: var(--chip); border-radius: 10px; }
.stepper { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }
.stepper .stap {
  width: 40px; height: 40px; border-radius: 50%; border: 1px solid var(--line);
  background: var(--bg); color: var(--ink); font: inherit; font-size: 1.3rem; line-height: 1; cursor: pointer;
}
.stepper .stap:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.aantal { font-weight: 600; min-width: 7.5rem; text-align: center; }
.ingr-box ul li { padding: 3px 0; border: 0; font-size: .95rem; }
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
let personen = null;           // null = elk gerecht toont zijn eigen receptaantal
const geopend = new Set();     // gerechten waarvan de ingrediënten openstaan
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

const BRUIKEN = { 1: "\u00bc", 2: "\u00bd", 3: "\u00be" };

function rond(x, eenheid) {
  const u = (eenheid || "").toLowerCase();
  if (u === "g" || u === "ml") {
    if (x < 20) return Math.max(0.5, Math.round(x * 2) / 2);
    if (x < 100) return Math.round(x / 5) * 5;
    return Math.round(x / 10) * 10;
  }
  return Math.max(0.25, Math.round(x * 4) / 4);
}

function toon(x) {
  const hele = Math.floor(x + 1e-9);
  const kwart = Math.round((x - hele) * 4);
  if (kwart === 0 || kwart === 4) return String(hele + (kwart === 4 ? 1 : 0));
  if (BRUIKEN[kwart] && Math.abs(x * 4 - Math.round(x * 4)) < 1e-9) return (hele ? hele : "") + BRUIKEN[kwart];
  return String(x).replace(".", ",");
}

function regel(i, factor) {
  if (i.a === null) return [i.u, i.n].filter(Boolean).join(" ");
  return [toon(rond(i.a * factor, i.u)), i.u, i.n].filter(Boolean).join(" ");
}

function knop(tekst, label, actie) {
  const b = el("button", { type: "button", className: "stap", textContent: tekst });
  b.setAttribute("aria-label", label);
  b.addEventListener("click", actie);
  return b;
}

function ingredientenBox(d) {
  const n = personen === null ? d.base : personen;
  const stepper = el("div", { className: "stepper" }, [
    knop("\u2212", "Minder personen", () => { personen = Math.max(1, n - 1); render(); }),
    el("span", { className: "aantal", textContent: "Voor " + n + (n === 1 ? " persoon" : " personen") }),
    knop("+", "Meer personen", () => { personen = Math.min(24, n + 1); render(); }),
  ]);
  if (n !== d.base) {
    const terug = el("button", { type: "button", className: "reset", textContent: "Zoals in recept (" + d.base + ")" });
    terug.addEventListener("click", () => { personen = null; render(); });
    stepper.append(terug);
  }
  const ul = el("ul");
  d.ingr.forEach(i => ul.append(el("li", { textContent: regel(i, n / d.base) })));
  return el("div", { className: "ingr-box" }, [stepper, ul]);
}

function matches(d) {
  if (q) {
    const hay = (d.name + " " + d.notes + " " + d.ingr.map(i => i.n).join(" ")).toLowerCase();
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
    if (d.ingr.length) tags.append(el("span", { className: "ingr", textContent: "ingredi\u00ebnten" }));
    const kop = [el("div", { className: "naam", textContent: d.name }), tags];
    if (d.notes) kop.push(el("div", { className: "notes", textContent: d.notes }));
    const li = el("li");
    if (!d.ingr.length) {
      kop.forEach(k => li.append(k));
    } else {
      const det = el("details");
      det.open = geopend.has(d.name);
      det.addEventListener("toggle", () => { det.open ? geopend.add(d.name) : geopend.delete(d.name); });
      det.append(el("summary", {}, kop), ingredientenBox(d));
      li.append(det);
    }
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
    fouten = []
    data = lees_csv(csv_pad, fouten)
    ingr_pad = csv_pad.parent / "ingredienten.csv"
    if ingr_pad.exists():
        lees_ingredienten(ingr_pad, data, fouten)
    if fouten:
        print("De pagina is NIET gemaakt. Dit moet eerst opgelost worden:")
        for f in fouten:
            print("  -", f)
        sys.exit(1)
    zonder = [g["name"] for g in data["dishes"] if g["ingr"] and not g["_expliciet"]]
    for g in data["dishes"]:
        g.pop("_expliciet")
    json_tekst = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    uit = csv_pad.parent / "index.html"
    uit.write_text(HTML.replace("__DATA__", json_tekst), encoding="utf-8")
    print(f"Klaar: {uit}")
    print(f"  {len(data['dishes'])} gerechten, filtergroepen: {', '.join(g['name'] for g in data['groups'])}")
    print(f"  {sum(1 for g in data['dishes'] if g['ingr'])} gerechten met ingredi\u00ebnten")
    if zonder:
        print(f"  Let op: geen Personen ingevuld bij {', '.join(zonder)}; er wordt 2 aangenomen.")
    waarschuw_bij_bijna_dubbele_tags(data)


if __name__ == "__main__":
    main()
