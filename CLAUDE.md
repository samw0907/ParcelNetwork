# CLAUDE.md

Working rules and project plan for the Parcel Locker Network analysis (Espoo).

Read `BACKGROUND.md` for domain context and `DATA_SOURCES.md` for data provenance before
starting Step 1.

`private/` holds the original planning brief. It is git-ignored and **superseded** by this
file: its national "where next" analysis, served-city list, OpenRouteService work and
existing-locker walk times were all dropped during planning (see the decisions log). Do not
build anything from it. Read it only if asked to.

---

## 1. What this project is

A small, self-contained geospatial analysis that answers one question:

> If a parcel-locker network were built in Espoo from scratch, using only the kinds of
> location Budbee currently uses to host its lockers, how many lockers would it need, and
> where, to put most residents within a short walk of one? And how quickly do the returns
> fall off?

The project produces a candidate site list, walking-time access for every populated 250 m
grid cell, a ranked sequence of chosen sites with a coverage curve, a formatted Excel
workbook, and map layers ready for manual cartography in QGIS. The final output is a
one-page PDF poster built in QGIS using the RoutePlan layout (see Section 9).

It is a demonstration of method, built on open data. It is a from-scratch network design,
not an audit of any operator's real network.

---

## 2. Guiding principles

These matter more than any individual technical choice. When in doubt, follow these.

**Keep it simple and explainable.** Every method used must be something the project owner
can describe out loud in two or three sentences without notes. If a technique cannot be
explained simply, it is the wrong technique for this project, even if it is more accurate.

**Demonstrative, not comprehensive.** The aim is a clean, credible, quick piece of work.
Do not add analyses, variables, cities or outputs beyond this plan. Scope must not grow.

**Correct data over convenient data.** Every figure on the page must come from a source
that can be named and re-fetched by script. If the data for a step turns out to be
incomplete or wrong, stop and escalate; never paper over it with a fallback.

**Do not over-engineer.** No config frameworks, no plugin architectures, no abstract base
classes. Plain scripts that run top to bottom, plus one plain `scripts/config.py` module of
shared constants.

**Budbee framing.** Budbee is named openly where it is relevant, and kept to a minimum
elsewhere. It is relevant in three places: (1) why the candidate site types were chosen
(they are the location types Budbee currently hosts its lockers in), (2) the context of
lockers-first expansion, (3) the README and page text explaining the analysis. The
analysis itself is general and would apply to any locker operator. Never imply the
analysis uses Budbee's own locker data or describes Budbee's actual network or plans.

**Stand-alone framing.** Project documentation, code and outputs must read as an
independent piece of analysis. Do not reference job applications, employers, cover
letters or recruitment anywhere in code, comments, output files or committed material.

---

## 3. Hard rules

**Never run git commands that change the repo.** No `git init`, `add`, `commit` or `push`.
At the end of every completed step, print a copy-pasteable block for the project owner to
run manually:

```
git add .
git commit -m "<one short line>"
git push
```

The commit message is a single short line. No body, no `Co-Authored-By` trailer, no
emojis. Do not execute the block. Just print it.

**Never read, open, display or create `.env` files.** This project needs no API keys. If
that ever changes, stop, give written instructions on where to obtain the key and the
variable name to set, then wait. The project owner manages `.env` files.

**Escalate significant decisions.** If anything needs to change materially from this plan
(scope, data source, method, output format, or anything that would invalidate work already
done), stop and present it in this structure every time:

1. **The issue in detail:** what it is and why it matters, grounded in concrete numbers
   from the actual data, not general statements. Do the diagnostic work first.
2. **Options:** each with its own pros and cons.
3. **A clear recommendation** with reasoning.

Then wait for a decision. Do not decide unilaterally.

**Never delete or overwrite raw downloaded data.** Raw files in `data/raw/` are read-only
once fetched. All processing writes to `data/processed/` or `outputs/`.

**Code style.** Clean, light, readable, matching the RoutePlanner project (sibling folder
`../RoutePlanner`, for reference only). A file path comment and a docstring at the top of
each script. Comments used sparingly. Each script prints a short `--- Summary ---` block
of key counts. No emojis anywhere in code, comments, commit messages or output.

**One step at a time.** Complete a step, report what was done with the key numbers, update
the progress log (Section 8), print the git block, then stop and wait. Do not run ahead
into the next step.

**Run scripts from the project root** (`python scripts/0N_name.py`). Paths are relative to
the root.

---

## 4. Locked scope decisions

Decided during planning (2026-09-25). Do not revisit without escalating.

| Decision | Value |
|---|---|
| Study area | Espoo plus Kauniainen (Kauniainen is enclosed by Espoo). Lockers placed only inside this area. |
| Population | HSY 250 m population grid, latest year (2025), `asukkaita` (total residents) only |
| Candidate site types | Only the location types Budbee currently uses: stores of S Group, K Group, Lidl and R-kioski, plus shopping centres. No stations, no other chains. |
| Walking distance | Along the OpenStreetMap walking network (OSMnx, `network_type="walk"`), not straight line |
| Walking speed | 4.8 km/h (80 m per minute) |
| Site selection | Greedy: add one site at a time, each the candidate that most reduces total resident walking time |
| Walk cap in objective | 30 minutes. Longer walks count as 30. |
| Stopping rule | Stop when the share of residents within a 10-minute walk reaches 90% of the share achievable with every candidate open (the ceiling), or at `MAX_SITES` (config). Revised in Step 3; see decisions log. |
| Map snapshots | Walk times reported at 10 sites (Map 2) and at the final N (Map 3) |
| Working CRS | ETRS-TM35FIN, EPSG:3067. HSY publishes in EPSG:3879; reproject on load. |
| Excel | Plain formatted tables. No pivot tables, no openpyxl Table objects (LibreOffice). |
| Mapping | QGIS, manual. Python exports layers only and performs no cartography. |
| API keys | None |

Out of scope: any national or multi-city analysis, drive times, existing-locker data from any
operator, competitor analysis, parcel volume or demand modelling beyond residents, locker
capacity, delivery routing, interactive web maps.

---

## 5. Project structure

```
ParcelNetwork/
  CLAUDE.md              This file
  BACKGROUND.md          Domain context
  DATA_SOURCES.md        Data provenance and licensing
  README.md              Project description (written in Step 0, finalised after Step 6)
  requirements.txt
  .gitignore
  private/               Original brief, git-ignored, superseded
  data/
    raw/                 Downloaded source data, read-only, git-ignored
    processed/           Intermediate outputs
  scripts/
    config.py            Shared constants: paths, CRS, thresholds, chain patterns
    01_population_grid.py
    02_candidate_sites.py
    03_walk_network.py
    04_site_selection.py
    05_export_excel.py
    06_export_gis.py
  outputs/
    parcel_locker_analysis.xlsx
    gis/parcelnetwork.gpkg
  qgis/                  QGIS project, poster guide (manual work)
```

`scripts/config.py` holds every threshold and shared setting as plain named constants:
paths, `TARGET_CRS`, `HSY_CRS`, grid year, municipality names, chain name patterns,
`SITE_MERGE_M` (50), `SNAP_FLAG_M` (200), `SNAP_EXCLUDE_M` (to be set in Step 3),
`WALK_SPEED_M_PER_MIN` (80), `WALK_CAP_MIN` (30), `TARGET_MIN` (10), `TARGET_SHARE`
(0.90), `SNAPSHOT_SITES` (10), `MAX_SITES` (60), `BAND_EDGES_MIN`. Values used by only
one script may stay at the top of that script, as in RoutePlanner.

---

## 6. Step-by-step plan

Each step ends with a report, a progress-log update and a git block. Then stop.

### Step 0 - Setup

- Create the directory structure above (with `.gitkeep` in empty folders).
- Write `requirements.txt`: `geopandas`, `pandas`, `numpy`, `requests`, `shapely`,
  `openpyxl`, `osmnx`, `networkx`, `scipy`. Add others only if genuinely needed.
- The project uses the owner's global Python 3.14 (as RoutePlanner did). `osmnx` and
  `networkx` are not installed yet. Print the install command for the owner to run; do not
  install anything yourself.
- Write `scripts/config.py` with the constants in Section 5.
- Write a `.gitignore` excluding `.env`, `private/`, `data/raw/`, `__pycache__/`, `*.pyc`,
  `data/processed/*.gpkg` and any cached graph files.
- Write a short `README.md`: what the project asks, scope, that candidate sites are
  limited to the location types Budbee currently uses (and why), data sources, how to run.
  Neutral tone, stand-alone framing. Include one line stating the analysis is independent,
  uses no Budbee data, and is not affiliated with or endorsed by Budbee or Instabee.
- The git block for this step starts with `git init`, `git branch -M main` and
  `git remote add origin https://github.com/samw0907/ParcelNetwork.git`, then the usual
  add / commit / push (`git push -u origin main`).

Do not fetch any data yet.

### Step 1 - Population grid and boundaries (`01_population_grid.py`)

All from the HSY open WFS (see `DATA_SOURCES.md`). Cache every raw response in `data/raw/`.

- Fetch the population grid, latest year (`Vaestotietoruudukko_2025`; check whether a newer
  year exists and use it if so). Reproject EPSG:3879 to EPSG:3067.
- Fetch municipal boundaries (`seutukartta_kunta_2021`) and build the study area as the
  union of Espoo and Kauniainen.
- Keep grid cells whose centroid falls in the study area.
- Fetch major districts (`seutukartta_suur_2021`). Attach a district to each cell by
  centroid. Espoo has seven major districts (Suur-Leppavaara, Suur-Tapiola, Suur-Matinkyla,
  Suur-Espoonlahti, Suur-Kauklahti, Vanha-Espoo, Pohjois-Espoo); Kauniainen is its own unit.
  Confirm names and fields against the data.
- Fetch context layers for the maps: rail and metro lines (`seutukartta_juna_metro_radat`),
  stations (`seutukartta_asemat`, map labels and context only, never candidates) and sea
  area (`maanpeite_merialue_2024` or newer). Clip to a sensible extent around the study area.
- Privacy check: HSY codes suppressed age bands as `99` in small cells. Only `asukkaita`
  is used, but report how many cells have suppressed age bands and whether any cells
  appear to be dropped entirely. Compare total residents with Espoo plus Kauniainen's
  official population (roughly 330,000; confirm the figure) and report the gap.
- Output: `data/processed/grid.gpkg` with layers `cells` (polygons: `cell_id`, `residents`,
  `district`), `study_area`, `districts`, `rail_metro`, `stations`, `sea`.
- Summary: cells, residents, residents by district, suppression counts.

If the resident total differs from the official figure by more than about 5%, stop and
report before continuing.

### Step 2 - Candidate sites (`02_candidate_sites.py`) - CHECKPOINT

- Query Overpass for shops inside the study area bounding box: `shop` in supermarket,
  convenience, kiosk (and department_store if chain stores use it), plus `shop=mall`.
  Cache the raw JSON.
- Classify each shop by chain using case-insensitive patterns on `brand`, `name` and
  `operator`, kept in config:
  - S Group: Prisma, S-market, Sale, Alepa (and Food Market Herkku if present)
  - K Group: K-Citymarket, K-Supermarket, K-Market (K-Extra if present)
  - Lidl
  - R-kioski
  - Shopping centre: `shop=mall`
  Drop everything else. Keep only points inside the study area polygon.
- Merge candidates within `SITE_MERGE_M` (50 m) of each other into one site (for example a
  mall and the supermarket inside it). Keep one representative per cluster with priority
  shopping centre > supermarket chain > R-kioski, and record the merged names.
- Output: `data/processed/sites.gpkg` layer `candidates` (`site_id`, `name`, `chain`,
  `merged_names`, `district`).
- Summary: raw counts per chain, merges, final candidate count, counts by district, and a
  near-miss list (shops with chain-like names that did not match a pattern, and chain
  stores with no name).

**Stop and report to the owner.** They will spot-check the counts (R-kioski in particular
may be under-mapped in OSM). Do not proceed to Step 3 until the candidate list is approved.

### Step 3 - Walking network and snapping (`03_walk_network.py`)

- Download the OSMnx walking network for the study area buffered by 500 m (so paths near
  the boundary connect). Cache the graph in `data/raw/`. Project to EPSG:3067.
- Snap every populated cell centroid and every candidate site to its nearest network node.
  Record the snap distance.
- Flag cells with snap distance above `SNAP_FLAG_M` (200 m). Report how many and how many
  residents. Snap distance is added to the network walking distance at both ends.
  Propose a value for `SNAP_EXCLUDE_M` (cells so far from any path they are excluded from
  the metrics) based on the actual distribution, and state it in the report.
- Output: the projected graph (cached for Step 4) and `data/processed/snaps.gpkg`
  (cells and sites with `node_id` and `snap_m`).
- Summary: nodes, edges, snap-distance percentiles, flagged cells and residents.

### Step 4 - Site selection (`04_site_selection.py`)

- For each candidate site, compute walking distance to every cell node along the network,
  limited to the walk cap (30 min = 2,400 m). One shortest-path run per candidate
  (`scipy.sparse.csgraph.dijkstra` with a limit, or networkx) is fast at this size. Add the
  snap distances and convert to minutes. Unreachable within the cap = 30 minutes.
- Greedy selection. Start with no lockers (every cell at 30). At each step add the
  candidate that gives the largest reduction in total resident walking time (sum of
  residents times capped minutes). Update each cell's time to the minimum over chosen sites.
- For each chosen site record: rank, name, chain, district, residents for whom it became
  the nearest locker when added, total resident-minutes saved, and after adding it: average
  walk (population-weighted, capped) and share of residents within 5, 10 and 15 minutes.
- Ceiling: the share of residents within `TARGET_MIN` with every candidate open. Stop when
  the share within `TARGET_MIN` reaches `TARGET_SHARE` of that ceiling, or at `MAX_SITES`.
  If `MAX_SITES` is hit first, stop and escalate. Report the ceiling as a headline figure.
- Band edges: before writing outputs, print the distribution of walk minutes at 10 sites
  and at N. Default bands are under 5, 5-10, 10-15, 15-20, over 20 minutes. If the data
  suggests different round edges, propose them and wait. Maps 2 and 3 must use identical
  bands.
- Output: `data/processed/selection.gpkg` with layers `cells_access` (cell polygons with
  `residents`, `district`, `min_10`, `band_10`, `site_10`, `min_final`, `band_final`,
  `site_final`), `sites_selected` (points with the attributes above plus residents
  nearest at the final N and a priority `tier`), and a non-spatial `coverage_curve`
  table (one row per N), and a non-spatial `run_summary` table (ceiling, target, N) read by
  Step 5. Walk minutes are stored unrounded so shares computed later match the curve.
- Priority tiers (added after the first run): tier 1 is the first `SNAPSHOT_SITES`; tiers 2
  and 3 end where the share within `TARGET_MIN` first reaches each `TIER_MILESTONES`
  fraction (0.50, 0.75) of the ceiling; tier 4 ends at the stopping point.
- Summary: N reached, the coverage curve at 10, 20, 30 ... N, and headline figures.

### Step 5 - Excel workbook (`05_export_excel.py`)

`outputs/parcel_locker_analysis.xlsx`, plain formatted tables, sheets:

1. **Sites** - chosen sites in rank order: rank, tier, name, chain, district, residents newly
   served, resident-minutes saved, average walk after, share within 10 min after.
2. **Coverage Curve** - one row per N: average walk, share within 5, 10, 15 minutes.
3. **Districts** - residents, average walk and share within 10 minutes at 10 sites and at
   the final N, per district.
4. **Candidates** - every candidate site with chain, district and chosen rank (blank if
   not chosen).
5. **Headline** - the figures the page quotes.
6. **Sources & Assumptions** - sources with access dates, every threshold used, caveats,
   and the note that sites are limited to Budbee's current host location types.

Formatting follows RoutePlanner's `05_export_excel.py`: accent `1F4E79` bold header row,
frozen panes, autofilter, explicit widths, correct number formats (thousands separators,
one decimal on minutes, percentages as percentages), a colour scale on one key column per
sheet at most, A4 landscape fit to width with repeating header. No Table objects.

### Step 6 - Export GIS layers (`06_export_gis.py`)

Single GeoPackage `outputs/gis/parcelnetwork.gpkg`, all EPSG:3067, no styling:

- `cells` - populated cells with residents and all access attributes (Maps 1-3)
- `candidates` - all candidate sites with chain (Map 1)
- `sites_selected` - chosen sites with rank (Maps 2-3)
- `study_area`, `districts` - boundaries
- `rail_metro`, `stations`, `sea` - context

Then finalise `README.md` with results, the method and data notes, and the explicit note
on site types.

### Step 7 - QGIS poster (manual)

Handled by the owner in QGIS. If asked, write `qgis/poster_guide.md` with styling and
layout guidance only (as in RoutePlanner). Do not generate map images programmatically.

---

## 7. API keys required

None. HSY WFS and OpenStreetMap (Overpass, OSMnx) are keyless.

---

## 8. Progress log

Update at the end of every step. Keep entries to one or two lines.

| Step | Status | Notes |
|---|---|---|
| 0 - Setup | Done (2026-09-25) | Structure, requirements, config.py, .gitignore, README. osmnx and networkx to install. |
| 1 - Population grid | Done (2026-09-25) | 2,169 cells, 328,618 residents (-0.8% vs official 31.12.2024). 1,117 cells age-suppressed (<100 residents), none dropped. |
| 2 - Candidate sites | Checkpoint (2026-09-25) | 128 matched stores/malls -> 80 sites (mall-outline merge, 4 OSM objects excluded). Awaiting owner approval of the list. |
| 3 - Walk network | Done (2026-09-26) | Walk filter + cycleways: 126,525 nodes kept (98%). Cell snap p99 126 m, max 256 m; 1 cell >200 m. SNAP_EXCLUDE_M = 500 (excludes none). |
| 4 - Site selection | Done (2026-09-26) | Ceiling 60.2% within 10 min (all 80 open); target 54.2%; N = 47. At 10 sites 18.6% within 10 min, avg 19.4 min; at 47 sites 54.4%, avg 10.5 min. Default bands kept. Priority tiers 1-10, 11-19, 20-34, 35-47. |
| 5 - Excel workbook | Done (2026-09-26) | Six sheets as planned; Sites and Candidates carry tier; Districts adds candidate / chosen counts and a total row. |
| 6 - Export GIS | Done (2026-09-26) | 8 layers in outputs/gis/parcelnetwork.gpkg (EPSG:3067); candidates carry rank and tier. README finalised with results and method notes. |
| 7 - QGIS poster | Not started (manual) | |

### Decisions made during the project

Record every escalated decision here: option chosen and a one-line reason.

- **Planning, reframe (2026-09-25).** The original brief had two parts: a national screen of
  towns Budbee does not yet serve, and Espoo walking times to existing Budbee Boxes. Both
  were dropped because the data cannot be obtained correctly by script. Budbee's locker and
  served-postcode endpoints (`/boxes/all/FI`, `/postalcodes/FI`) require merchant
  credentials (HTTP 401); budbee.com has no public locker map; OpenStreetMap holds only
  about 8 Budbee Boxes in Espoo. The brief's served-city list (8 cities) is also out of
  date: Budbee expanded lockers-first to many smaller towns in 2024-2026, so most Finnish
  towns of 15,000+ are likely already served and no official list is public. Chosen
  instead: a from-scratch locker network design for Espoo on open data only. Rejected:
  a hand-built served list from press releases (unverifiable), all-carrier OSM lockers
  (also incomplete), repeating the method in towns outside the capital region (only a
  1 km open grid exists there, too coarse for walking).

- **Planning, candidate site types (2026-09-25).** Candidates limited to the location types
  Budbee currently uses: S Group, K Group, Lidl and R-kioski stores (named as hosts in
  Budbee press releases) plus shopping centres (Budbee Boxes exist in Sello and A Bloc).
  Stations dropped: no evidence Budbee uses them, a different kind of host agreement, and
  nearly every Espoo station has a qualifying store beside it. This restriction must be
  stated in the README and on the page.

- **Planning, simplifications (2026-09-25).** No OpenRouteService, no Statistics Finland
  data, no age or income columns, no 1.5 km locker search buffer, no separate objective
  area (the 30-minute cap stops sparse rural cells dominating). Lockers are placed only
  inside Espoo and Kauniainen; lockers across the Helsinki boundary are a stated
  limitation.

- **Step 2, merging stores into shopping centres (2026-09-25).** The 50 m point merge
  measured from each mall's centre point, so large malls split into several sites (Sello
  into 6, two of them unnamed OSM parts). Chosen: a store inside a shopping centre's OSM
  outline, or within 50 m of it, counts as that centre; touching centre parts merge;
  other candidates still merge at 50 m. Gives one correctly named site per centre.
  Rejected: keeping the point merge (95 sites, duplicates), a 150 m radius (74 sites,
  chains up to 351 m and merges unrelated neighbouring stores).

- **Step 2, stale OSM objects (2026-09-25).** OSM had 10 R-kioskis; the official list
  (r-kioski.fi/kioskit) has 7 in Espoo, none in Kauniainen, all 7 present in OSM. The 3
  extra (Suvela, Mankkaanportti, Keilaniemi metro) have closed. Chosen: exclude them by
  OSM id in a documented list in `02_candidate_sites.py`, plus MotorCenter Espoonlahti
  (tagged shop=mall, a car dealership). Rejected: keeping them, or scraping r-kioski.fi
  on every run (still needs a hand-made name match).

- **Step 2, Overpass mirror (2026-09-25).** The kumi.systems mirror served OSM data from
  2026-06-01 (four months stale). Mirrors removed; the script uses the main endpoint
  with retries and prints the data timestamp.

- **Step 3, walking network filter (2026-09-26).** OSMnx's standard `walk` filter excludes
  all `highway=cycleway`, but 98% of Espoo's cycleways are shared foot/cycle paths
  (`foot=designated`). With it, Otaniemi was a detached piece, 20 cells (5,518 residents)
  snapped over 200 m, and all 80 sites put only 40% within 10 min. Chosen: the standard
  filter with cycleways kept (`foot=no` still excluded): 1 cell over 200 m, 60% within
  10 min with all sites. Rejected: the standard filter (wrong for Finnish OSM),
  `network_type="all"` (includes private ways). `SNAP_EXCLUDE_M` set to 500 m (max cell
  snap is 256 m, so it is a guard only).

- **Stopping rule (2026-09-26, found in Step 3).** With every one of the 80 candidates
  open, only 60.2% of residents are within a 10-minute walk (79.8% within 800 m straight
  line), so "90% within 10 minutes" can never be met. The polycentric layout, with stores
  concentrated in large hubs, makes this expected. Chosen: stop when the share within 10
  minutes reaches 90% of that achievable ceiling (about 54%, roughly 47 sites in a trial
  run). Keeps the 10-minute walk, which is the more reasonable walk for a locker, and
  makes the ceiling itself a headline finding. Considered: 80% within 15 minutes (about the
  same N, simpler wording, but a longer walk); a plain lower target such as 50% within 10
  minutes (arbitrary); no target and a full 80-site curve (arbitrary cut-off).

- **Step 4, site names (2026-09-26, minor, not escalated).** 30 of the 47 chosen sites
  were named only by chain ("K-Market", "Alepa"), useless on the Map 2 list and in Excel.
  `02_candidate_sites.py` now appends the OSM `branch` tag ("K-Market Kilo"), or the street
  when there is no branch ("Lidl Kurjenkellontie"). Selection results are unchanged.
  One OSM typo carries through: "K-Market Iiivisniemi" (Iivisniemi); fix by hand on the
  poster if it appears.

- **Step 4, band edges (2026-09-26).** Defaults kept (under 5, 5-10, 10-15, 15-20, over
  20). At 47 sites residents spread 16 / 38 / 27 / 12 / 7%. At 10 sites 49% fall in
  "over 20", which is the Map 2 message (ten lockers leave half of Espoo over 20 minutes
  away), so no extra band was added.

- **Step 4, priority tiers (2026-09-26).** Greedy rank is a true build order (resident-
  minutes saved falls at every step, 610k at rank 1 to 22k at rank 47), but 47 numbers
  would clutter Map 3. Chosen: four colour-coded tiers at milestones toward the
  achievable maximum: 1-10 (first ten, 31%), 11-19 (half, 52%), 20-34 (three quarters,
  75%), 35-47 (stopping point, 90%). Each tier needs more sites for less progress, which
  shows the diminishing returns. Rejected: blocks of ten (arbitrary boundaries, uneven
  last block of 17); numbering all 47 (cluttered).

- **Step 5, rounding mismatch (2026-09-26, minor, fixed).** Step 4 stored cell walk
  minutes rounded to 0.1, so cells at 10.01-10.04 min counted as "within 10" when Step 5
  recomputed district shares (study-area total 54.6% vs 54.4% on the curve). Step 4 now
  stores unrounded minutes; all sheets agree. Step 4 also writes a `run_summary` table so
  the ceiling and target are not recomputed downstream.

---

## 9. Page and map plan (for the QGIS stage)

The page reuses the RoutePlan.pdf layout exactly (the RoutePlanner project's poster): black
background, yellow title and headings, intro paragraph, three text columns (Method &
Scoring, Key findings, Limitations, 5 to 6 bullets each), three map panels each with a
portrait map frame, a legend column and a four-line caption, footer with data sources left
and GitHub link right. Beige land, light grey sea, yellow panel borders. Fit the content to
the template.

**Title:** Placing Parcel Lockers: How Many, and Where?

**Intro (draft):** Parcel lockers let a delivery network serve a whole area from a handful
of sites, typically hosted inside supermarkets and kiosks. The planning questions are how
many sites are needed and where they should go. This analysis answers both for Espoo, a
polycentric city of around 320,000, using only the kinds of location Budbee currently hosts
its lockers in. It measures walking time along real streets and paths from every populated
250 m grid cell to the nearest site, and adds sites one at a time where each cuts the most
total walking. It runs as a short pipeline of Python scripts on open data, producing a
formatted Excel workbook, with the cartography built in QGIS.

All three maps share one frame: Espoo's built-up belt (Kauklahti and Espoonlahti across to
Leppavaara and Otaniemi), cropped tight in the upper part of the portrait frame, with
rail and metro lines and the main centre names for orientation.

**Map 1 - Where people live, and where lockers could go.** Cells shaded by residents;
candidate sites as small dots coloured by chain, shopping centres marked. Shows the
polycentric pattern and that stores cluster in the same centres. Legend: resident classes,
chain colours, scale bar, north arrow.

**Map 2 - The first ten lockers.** Cells shaded by walking-time band to the nearest of the
first 10 sites; sites as numbered yellow crosses with a dark outline. Legend column: bands,
then a numbered list of the 10 sites (name, residents served) ending with "10 lockers: X%
within 10 min, average walk Y min".

**Map 3 - Reaching 90% of what is possible.** (Working title: N sites bring 90% of the
residents who could ever be within 10 minutes of these host types.) Same frame and bands,
all N sites coloured by priority tier: tier 1 (the first 10) keep their numbered crosses
from Map 2, tiers 2-4 as dots in three colours. Legend column: bands plus a small tier
table (tier, sites, share within 10 minutes reached, share of the achievable maximum).
The message is the diminishing return: each tier needs more sites for less progress
(tiers of 10, 9, 15 and 13 sites reach 31%, 52%, 75% and 90% of the achievable maximum).

**Key findings:** written after the run with concrete numbers: the coverage curve, the cost
of the last 10%, which chains' stores are chosen most, where coverage stays expensive.

**Limitations (draft, refine after the run):**
- A from-scratch design on open data, not an audit of any operator's actual network.
- Residents stand in for demand; pickups near work or on commutes are not captured.
- Sites are limited to the location types Budbee currently uses; candidate stores come
  from OpenStreetMap, which may miss some (R-kioski especially).
- One locker per site, no capacity limits.
- Lockers across the Helsinki boundary are ignored, so edge areas look slightly worse
  served than they are.
- 250 m grid resolution (about a 3-minute walk per cell); some small cells are
  privacy-suppressed.

**Footer:** data sources (HSY, OpenStreetMap contributors) and
`github.com/samw0907/ParcelNetwork`.
