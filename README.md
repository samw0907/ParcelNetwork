# Parcel Locker Network: Espoo

A small, self-contained geospatial analysis that answers one question:

> If a parcel-locker network were built in Espoo from scratch, how many lockers would it
> need, and where, to put most residents within a short walk of one? And how quickly do
> the returns fall off?

Parcel lockers let a delivery network serve a whole area from a handful of sites, usually
hosted inside supermarkets, kiosks and shopping centres. The planning questions are how
many sites are needed and where they should go. Espoo, with Kauniainen, suits the question
well: it is polycentric, with separate centres strung along the metro, the coastal
corridor and the rail line, so walking access varies a lot from place to place.

The analysis measures walking time along real streets and paths from every populated
250 m grid cell to the nearest candidate site, then adds sites one at a time, each time
choosing the site that cuts total resident walking time the most. The result is a build
order and a coverage curve showing how quickly the returns diminish.

## Scope

- Study area: Espoo plus Kauniainen, which Espoo encloses. Lockers are placed only inside
  this area.
- Demand: residents in the HSY 250 m population grid (2025).
- Candidate sites: stores of S Group, K Group, Lidl and R-kioski, plus shopping centres,
  taken from OpenStreetMap. These are the location types Budbee currently uses to host its
  lockers, as named in its press releases, so the candidate list reflects the kind of
  host agreement a locker operator actually makes. Stations and other chains are
  excluded.
- Walking: along the OpenStreetMap walking network at 4.8 km/h (80 m per minute).
- Selection: greedy. Start with no lockers, add the candidate that most reduces total
  resident walking time (walks capped at 30 minutes). Even with every candidate site open,
  only part of the population is within a 10-minute walk, so selection stops when the
  share within 10 minutes reaches 90% of that achievable maximum.

This is a demonstration of method and a from-scratch network design. It is not an audit
of any operator's real network. The analysis is independent, uses no Budbee data, and is
not affiliated with or endorsed by Budbee or Instabee.

## Data sources

All open data, no API keys. See `DATA_SOURCES.md` for provenance and licensing.

- Helsinki Region Environmental Services HSY: population grid, municipal and district
  boundaries, rail and metro lines, stations, sea area (CC BY 4.0)
- OpenStreetMap contributors via the Overpass API: candidate stores and shopping centres
  (ODbL)
- OpenStreetMap contributors via OSMnx: walking network (ODbL)

## Running the scripts

Install dependencies:

```
pip install -r requirements.txt
```

Run the scripts in order from the project root. Each writes its output to
`data/processed/` or `outputs/` and prints a short summary.

```
python scripts/01_population_grid.py
python scripts/02_candidate_sites.py
python scripts/03_walk_network.py
python scripts/04_site_selection.py
python scripts/05_export_excel.py
python scripts/06_export_gis.py
```

Shared settings and thresholds are in `scripts/config.py`.

## Outputs

- `outputs/parcel_locker_analysis.xlsx`: formatted workbook of chosen sites, the coverage
  curve, district results and all candidates
- `outputs/gis/parcelnetwork.gpkg`: GeoPackage layers for manual cartography in QGIS

The final poster is produced manually in QGIS and is not part of the scripted pipeline.
