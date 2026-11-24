# Wat eten we?

Een lijst met gerechten die je kunt filteren op telefoon of computer.
De pagina staat op: https://juliecoppens.github.io/gerechten/

## Een gerecht toevoegen of aanpassen

1. Open `gerechten.csv` in deze repository.
2. Klik op het potloodje rechtsboven ("Edit this file").
3. Voeg onderaan een nieuwe regel toe, of pas een bestaande regel aan.
4. Klik op **Commit changes** en bevestig.
5. Na ongeveer één à twee minuten staat de wijziging op de pagina.
   Bij problemen: kijk op het tabblad **Actions**. Een rood kruisje betekent dat de bouw mislukt is;
   open die run en lees wat er staat. De pagina blijft dan op de vorige versie staan.

## Hoe een regel eruitziet

```
Dish,Carbs,Meat,Moeite,Tijd,Etentje,Notities,Description,Personen
Wraps,Wrap,"Kip, Gehakt",Makkelijk,Snel,Nee,,,4
```

- Eén gerecht per regel, de kolommen gescheiden door komma's.
- **Kan een gerecht meerdere dingen zijn?** Zet de waarden in één cel tussen dubbele aanhalingstekens,
  gescheiden door een komma: `"Kip, Gehakt"`. Vergeet de aanhalingstekens niet, anders schuiven de kolommen op
  (de bouw geeft dan een foutmelding).
- Laat een cel leeg als er niets past. Het gerecht blijft dan zichtbaar, maar verschijnt niet bij een filter op die kolom.
- **Notities** en **Description** zijn vrije tekst en verschijnen onder het gerecht.
- **Personen** is het aantal personen waarvoor de ingrediënten van dat gerecht zijn opgeschreven.
  Het is geen filter. Alleen nodig bij gerechten met ingrediënten; leeg betekent 2.
  Staat Personen als laatste kolom, dan telt het aantal komma's: een regel met lege Notities en Description
  eindigt dus op `,,,4`.

## Vaste waarden

| Kolom | Gebruik precies deze waarden |
|---|---|
| Moeite | Makkelijk, Gemiddeld, Moeilijk |
| Tijd | Snel, Gemiddeld, Lang |
| Etentje | Ja, Misschien, Nee |
| Carbs | Rijst, Aardappel, Pasta, Noedels, Wrap (of een nieuwe, maar schrijf hem altijd hetzelfde) |
| Meat | Veggie, Gehakt, Kip, Vis, Spek, Hesp, Lam, Rund, Eend, Worst (idem) |

Let op de spelling: "Rijt" naast "Rijst" geeft twee aparte knoppen, en het gerecht met de typfout
vind je dan niet meer onder Rijst. Hoofdletters tellen mee.

## Ingrediënten toevoegen

Ingrediënten staan in een apart bestand: `ingredienten.csv`. Eén regel per ingrediënt:

```
Dish,Ingredient,Amount,Unit
Spaghetti,Gehakt,200,g
Spaghetti,Ui,1,
Spaghetti,Tomatenpuree,1,el
Spaghetti,Zout,,snuf
```

(Dit is een voorbeeld, geen echt recept.)

- **Dish** moet exact hetzelfde geschreven zijn als in `gerechten.csv` (hoofdletters maken niet uit).
  Een typfout geeft een foutmelding in de bouw.
- Voor een tweede ingrediënt van hetzelfde gerecht maak je gewoon een nieuwe regel met dezelfde naam.
  In het sjabloon staat per gerecht één lege regel; vul die in en kopieer de naam voor de rest.
- **Amount** is de hoeveelheid voor het aantal personen dat bij het gerecht in `gerechten.csv` staat.
  Schrijf `400`, `1.5`, `1/2` of `1 1/2`. Wil je `1,5` met een komma, zet het dan tussen aanhalingstekens: `"1,5"`.
- **Unit** is de eenheid: `g`, `ml`, `el`, `tl`, een woord als `pak` of `blik`, of leeg voor stuks (1 ui).
- **Geen schaalbare hoeveelheid** (zout naar smaak)? Laat Amount leeg en zet er een woord bij in Unit, bv. `snuf`.
  Die regel blijft altijd hetzelfde, ook als je het aantal personen aanpast.
- Op de pagina tik je op "ingrediënten" onder een gerecht. Met + en − kies je het aantal personen.
  Dat aantal geldt dan voor alle gerechten, ook voor gerechten waarvan het recept voor een ander aantal is.
  Hoeveelheden worden afgerond: gram en milliliter op hele, handige getallen en de rest op kwarten.
  Bij 3 personen uit een recept voor 2 krijg je dus "1½ ui".

## Niet doen

- **Bewerk de CSV-bestanden niet in Excel.** Nederlandse en Belgische Excel slaat bestanden op met puntkomma's en
  kan aanhalingstekens en speciale tekens aanpassen. Bewerk de bestanden op GitHub zelf.
- Pas `index.html` niet aan: die wordt bij elke wijziging automatisch opnieuw gemaakt.

## Technisch

`maak_pagina.py` leest `gerechten.csv` (en `ingredienten.csv` als die er is) en maakt `index.html`.
De workflow in `.github/workflows/pagina.yml` draait dat script bij elke wijziging aan een van die bestanden
en publiceert de pagina op GitHub Pages. Lokaal proberen: `python maak_pagina.py` en open `index.html`.
