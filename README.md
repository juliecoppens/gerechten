# Wat eten we?

Een lijst met gerechten die je kunt filteren op telefoon of computer.
De pagina staat op: https://juliecoppens.github.io/gerechten/

## Een gerecht toevoegen of aanpassen

1. Open `gerechten.csv` in deze repository.
2. Klik op het potloodje rechtsboven ("Edit this file").
3. Voeg onderaan een nieuwe regel toe, of pas een bestaande regel aan.
4. Klik op **Commit changes** en bevestig.
5. Na ongeveer één à twee minuten staat de wijziging op de pagina.
   Bij problemen: kijk op het tabblad **Actions**. Een rood kruisje betekent dat de bouw mislukt is.

## Hoe een regel eruitziet

```
Dish,Carbs,Meat,Moeite,Tijd,Etentje,Notities,Description
Wraps,Wrap,"Kip, Gehakt",Makkelijk,Snel,Nee,,
```

- Eén gerecht per regel, de kolommen gescheiden door komma's.
- **Kan een gerecht meerdere dingen zijn?** Zet de waarden in één cel tussen dubbele aanhalingstekens, gescheiden door een komma: `"Kip, Gehakt"`. Vergeet de aanhalingstekens niet, anders schuiven de kolommen op.
- Laat een cel leeg als er niets past. Het gerecht blijft dan zichtbaar, maar verschijnt niet bij een filter op die kolom.
- **Notities** en **Description** zijn vrije tekst en verschijnen onder het gerecht.

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

## Niet doen

- **Bewerk de CSV niet in Excel.** Nederlandse en Belgische Excel slaat bestanden op met puntkomma's en
  kan aanhalingstekens en speciale tekens aanpassen. Bewerk het bestand op GitHub zelf.
- Pas `index.html` niet aan: die wordt bij elke wijziging automatisch opnieuw gemaakt.

## Technisch

`maak_pagina.py` leest `gerechten.csv` en maakt `index.html`. De workflow in
`.github/workflows/pagina.yml` draait dat script bij elke wijziging aan de CSV en publiceert de
pagina op GitHub Pages. Lokaal proberen: `python maak_pagina.py` en open `index.html`.
