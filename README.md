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

This is a demonstration of method and a from-scratch network design. It is not an audit
of any operator's real network. The analysis is independent, uses no Budbee data, and is
not affiliated with or endorsed by Budbee or Instabee.

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
  resident walking time (walks capped at 30 minutes), and stop when the share of residents
  within a 10-minute walk reaches 90% of what these site types can achieve at most.

## Results

328,618 residents in 2,169 populated cells; 80 candidate sites.

- **A ceiling of 60%.** Even with all 80 candidate sites open, only 60.2% of residents
  are within a 10-minute walk (average walk 9.7 minutes). Stores of these types cluster in
  the large centres, so lower-density neighbourhoods between them stay beyond 10 minutes
  whatever is built.
- **47 sites reach 90% of that ceiling:** 54.4% of residents within 10 minutes, 81.0%
  within 15 minutes, average walk 10.5 minutes.
- **The first ten do the most work.** 10 sites put 18.6% within 10 minutes (average walk
  19.4 minutes). The first site, Iso Omena, saves 610,000 resident-minutes of walking; the
  47th saves 22,000.
- **Priority tiers.** Sites fall into four build tiers, each needing more sites for less
  progress:

  | Tier | Sites | Within 10 min after | Share of the ceiling |
  |---|---|---|---|
  | 1 | 1-10 (10 sites) | 18.6% | 31% |
  | 2 | 11-19 (9 sites) | 31.1% | 52% |
  | 3 | 20-34 (15 sites) | 45.1% | 75% |
  | 4 | 35-47 (13 sites) | 54.4% | 90% |

- **Shopping centres lead.** The chosen 47 are 16 shopping centres (of 23 candidates),
  15 K Group, 10 S Group, 5 Lidl and 1 R-kioski store. The first four are Iso Omena,
  Sello, Suvelan Ostari and Lippulaiva.
- **Where coverage stays expensive.** At 47 sites, Suur-Leppavaara has 68% of residents
  within 10 minutes, but Suur-Kauklahti has 16%, Pohjois-Espoo 18% and Kauniainen 38%.

## Method and data notes

- **Population.** HSY grid 2025 (`asukkaita`, total residents), cells kept where the
  centroid falls in Espoo or Kauniainen. The total is 0.8% below Statistics Finland's
  official population at 31 December 2024. HSY suppresses the age breakdown in cells with
  fewer than 100 residents; only the total is used, so no residents are lost.
- **Candidate sites.** OpenStreetMap supermarkets, convenience stores, kiosks and
  shopping centres matched to the chains by name, brand and operator. A store inside a
  shopping centre's outline, or within 50 m of it, counts as that centre, and other stores
  within 50 m of each other are merged, giving 80 sites from 128 matched stores and
  centres. Three R-kioskis no longer on R-kioski's own store list and one mis-tagged car
  dealership were removed. OSM data as of 25 September 2026.
- **Walking network.** OSMnx's standard walking filter, with one change: shared foot and
  cycle paths (`highway=cycleway`) are included. Finland maps most footpaths that way, and
  without them large areas such as Otaniemi appear disconnected. Cell centres and sites are
  joined to their nearest network node, and that snap distance is added to the walk at
  both ends (median 25 m, maximum 256 m).
- **Selection.** One shortest-path run per candidate gives walking time to every cell,
  capped at 30 minutes. Sites are then added greedily. Because this is a greedy build
  order, site 1 is where an operator would start; it is close to, but not guaranteed to
  be, the best possible set for each number of sites.
- **Limitations.** Residents stand in for demand, so pickups near work or on commutes are
  missed. Stores come from OpenStreetMap and may be incomplete or out of date. One locker
  per site, with no capacity limit. Lockers across the Helsinki and Vantaa boundaries are
  ignored, so edge areas look slightly worse served than they are. The 250 m grid is
  about a 3-minute walk across, and each cell is measured from its centre.

Every decision taken during the build, with the options considered, is logged in
`CLAUDE.md` (section 8).

## Data sources

All open data, no API keys. See `DATA_SOURCES.md` for provenance and licensing.

- Helsinki Region Environmental Services HSY: population grid, municipal and district
  boundaries, rail and metro lines, stations, sea area (CC BY 4.0)
- OpenStreetMap contributors via the Overpass API: candidate stores and shopping centres
  (ODbL)
- OpenStreetMap contributors via OSMnx: walking network (ODbL)
- Statistics Finland, table 11ra: official population, used only to check the grid total

## Running the scripts

Install dependencies:

```
pip install -r requirements.txt
```

Run the scripts in order from the project root. Each writes its output to
`data/processed/` or `outputs/` and prints a short summary. Downloads are cached in
`data/raw/`, so later runs work offline.

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

- `outputs/parcel_locker_analysis.xlsx`: formatted workbook with the chosen sites, the
  coverage curve, district results, all candidates, headline figures, and sources and
  assumptions
- `outputs/gis/parcelnetwork.gpkg`: GeoPackage layers (EPSG:3067) for manual cartography
  in QGIS: cells with walk times, candidates, chosen sites with rank and tier, study
  area, districts, rail and metro, stations, sea

The final poster is produced manually in QGIS and is not part of the scripted pipeline.
