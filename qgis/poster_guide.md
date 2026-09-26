# QGIS poster guide

Step 7: a one-page poster in the RoutePlan layout (see CLAUDE.md section 9), with three
Espoo map panels:

1. **Where people live, and where lockers could go** - residents per cell, all 80
   candidate sites by chain.
2. **The first ten lockers** - walking time to the nearest of sites 1-10.
3. **Reaching 90% of what is possible** - walking time with all 47 sites, sites coloured
   by priority tier.

Everything comes from `outputs/gis/parcelnetwork.gpkg` (EPSG:3067). All figures quoted
below are from the current run (N = 47) and match the Excel workbook.

Colours are suggestions that suit the black page, beige land and light grey sea. Where
the RoutePlan template already defines a colour (the yellow, the page black), use the
template's exact value.

---

## 0. Set up the project

1. Open QGIS > **Project > New**.
2. **Project > Properties > CRS**: search `3067`, pick **ETRS89 / TM35FIN(E,N)**
   (EPSG:3067) > OK.
3. **Project > Properties > General > Background color**: `#EDE6D6` (beige land; the
   sea layer draws over it). OK.
4. **Project > Save As** > `qgis/parcelnetwork.qgz` (inside this project folder).
5. Drag `outputs/gis/parcelnetwork.gpkg` from the Browser panel (or Windows Explorer)
   into the Layers panel. In the dialog tick **all 8 layers** > **Add Layers**.

### Duplicate the layers that appear on more than one map

The three maps show different fields of the same layers, so each needs its own copy.
Right-click a layer > **Duplicate Layer**, then right-click the copy > **Rename Layer**:

| Original | Copies (rename to) | Used on |
|---|---|---|
| `cells` | `cells - residents`, `cells - 10 sites`, `cells - 47 sites` | Maps 1, 2, 3 |
| `sites_selected` | `sites - first 10`, `sites - by tier` | Maps 2, 3 |

Rename the original `cells` to `cells - residents` and make two duplicates; rename the
original `sites_selected` to `sites - by tier` and make one duplicate.

### Layer order (top to bottom)

```
sites - first 10
sites - by tier
candidates
stations
rail_metro
districts
study_area
cells - 10 sites
cells - 47 sites
cells - residents
sea
```

Drag layers in the Layers panel to match.

---

## 1. Palette

| Use | Colour |
|---|---|
| Page background | `#000000` (or the template's black) |
| Title, headings, panel borders, site crosses | template yellow (if starting fresh: `#F2C200`) |
| Land (project and map-frame background) | `#EDE6D6` |
| Sea | `#D9DCDF` |
| Rail and metro lines | `#4A4A4A` |
| Study-area outline | `#6B6B6B` |
| Map label text | `#1F2933` |

Walking-time bands (Maps 2 and 3, identical), teal for short walks to coral for long:

| Band (minutes) | Colour |
|---|---|
| under 5 | `#0F6E6E` |
| 5-10 | `#4FA3A0` |
| 10-15 | `#BFDCD6` |
| 15-20 | `#F2B89C` |
| over 20 | `#D9674E` |

---

## 2. Base layers (shared by all three maps)

### sea
Double-click `sea` > **Symbology** > Simple fill: Fill `#D9DCDF`, **Stroke style: No
Pen**. OK.

### study_area
Symbology > Simple fill: **Fill style: No Brush**; Stroke `#6B6B6B`, width `0.5` mm.

### districts (optional, faint)
Symbology > Simple fill: **No Brush**; Stroke white, width `0.3` mm, Stroke style **Dash
Line**. Leave it off if the map looks busy.

### rail_metro
1. Symbology > **Categorized** > Value `tyyppi` > **Classify**.
2. `l_jrata` (rail): double-click the symbol > Simple line `#4A4A4A`, width `0.45` mm.
3. `l_metror` (metro): Simple line `#4A4A4A`, width `0.45` mm, **Stroke style: Dash
   Line**.
4. Untick the "all other values" row. Rename the two legend labels to `Rail` and
   `Metro` (double-click the Legend column).

### stations - centre names only
Stations are labels, not symbols.

1. Symbology > Single symbol > Simple marker, size `1.2` mm, fill `#4A4A4A`, stroke white
   `0.2` mm. (Or set the symbol opacity to 0% if you want labels only.)
2. Right-click `stations` > **Filter** > enter:
   ```
   "asema" IN ('Tapiola','Leppävaara','Matinkylä','Espoonlahti','Espoo','Kauklahti',
               'Kivenlahti','Aalto-yliopisto','Kauniainen','Niittykumpu','Kilo')
   ```
   OK. (Trim the list at the end if labels crowd.)
3. **Labels** tab > **Single Labels** > Value: click the **e** (expression) button:
   ```
   CASE
     WHEN "asema" = 'Espoo' THEN 'Espoon keskus'
     WHEN "asema" = 'Aalto-yliopisto' THEN 'Otaniemi'
     ELSE "asema"
   END
   ```
4. **Text**: Size `7`, colour `#1F2933`, Style **Italic**.
5. **Buffer**: tick **Draw text buffer**, size `0.8` mm, colour `#EDE6D6`.
6. **Placement**: **Around point**, distance `1.2` mm.

---

## 3. Map 1 - Where people live, and where lockers could go

### cells - residents (graduated)
1. Double-click `cells - residents` > **Symbology** > **Graduated**.
2. **Value**: `residents`. **Mode**: any; you will set the breaks by hand.
3. Set **Classes** to `4` > **Classify**.
4. Double-click each value range in the **Values** column and set:

   | Range | Label | Colour | Cells | Share of residents |
   |---|---|---|---|---|
   | 1 - 50 | 1-50 | `#DCE3EA` | 794 | 5% |
   | 51 - 250 | 51-250 | `#A7B8C9` | 1,006 | 41% |
   | 251 - 750 | 251-750 | `#6F8BA6` | 313 | 38% |
   | 751 - 1900 | over 750 | `#34506E` | 56 | 16% |

5. For each class symbol (or once, via the top **Symbol** button before classifying):
   Simple fill, **Stroke style: No Pen**. (A stroke draws hairlines between cells.)

### candidates (by chain, shopping centres marked)
1. Double-click `candidates` > **Symbology** > **Categorized** > Value `chain` >
   **Classify**.
2. Set each symbol:

   | Chain | Marker | Size | Fill | Stroke |
   |---|---|---|---|---|
   | S Group | circle | 2.2 mm | `#2E8B57` | white 0.3 mm |
   | K Group | circle | 2.2 mm | `#E07B24` | white 0.3 mm |
   | Lidl | circle | 2.2 mm | `#2F5DA8` | white 0.3 mm |
   | R-kioski | circle | 2.2 mm | `#C0392B` | white 0.3 mm |
   | Shopping centre | **square** | 3.2 mm | `#1F1F1F` | white 0.4 mm |

3. Untick the "all other values" row.
4. **Control feature rendering order** (button at the bottom of Symbology) > add `chain`
   so shopping centres draw on top; or simply move the Shopping centre category to the
   bottom of the list.

Candidate counts for the legend: S Group 25, Shopping centre 23, K Group 22, Lidl 8,
R-kioski 2 (80 sites; shopping centres include the stores inside them).

---

## 4. Map 2 - The first ten lockers

### cells - 10 sites (walking-time bands)
1. Double-click `cells - 10 sites` > **Symbology** > **Categorized** > Value `band_10` >
   **Classify**.
2. Drag the categories into order: `under 5`, `5-10`, `10-15`, `15-20`, `over 20`.
   Untick "all other values".
3. Double-click each symbol and set the band colour from section 1, **Stroke style: No
   Pen**.
4. Rename the legend labels to `under 5 min`, `5-10 min`, `10-15 min`, `15-20 min`,
   `over 20 min`.
5. Save the style for reuse: bottom-left **Style > Save Style...** > `qgis/bands.qml`.

### sites - first 10 (numbered yellow crosses)
1. Right-click `sites - first 10` > **Filter** > `"rank" <= 10` > OK.
2. **Symbology** > Single symbol. Build two stacked marker layers:
   - Click the existing **Simple Marker**: shape **Cross fill** (the filled plus sign),
     size `4.8` mm, fill `#1F1F1F`, stroke `#1F1F1F` width `0.6` mm. This is the dark
     outline.
   - Click the green **+** to add a second Simple Marker; make sure it sits **above**
     the first in the symbol tree: shape **Cross fill**, size `4.0` mm, fill the
     template yellow, **Stroke style: No Pen**.
3. **Labels** tab > **Single Labels** > Value `rank`.
   - **Text**: Style **Bold**, size `8`, colour `#1F1F1F`.
   - **Buffer**: `1.0` mm, colour the template yellow (or white).
   - **Placement**: **Cartographic**, distance `2.2` mm.
   - **Rendering**: tick **Show all labels for this layer (including colliding
     labels)**.

### The Map 2 site list (legend column text)
Residents within a 10-minute walk of each site, with the first ten open. The ten sum
to 61,018 residents, which is the 18.6%.

```
 1  Iso Omena               9,983
 2  Sello                   8,013
 3  Suvelan Ostari          8,119
 4  Lippulaiva              6,363
 5  K-Market Pohjantähti    4,576
 6  Kauppakeskus Niitty     6,914
 7  Alepa Karakallio        3,734
 8  S-market Saunalahti     4,969
 9  Kauppakeskus Grani      3,008
10  Suuris                  5,339

10 lockers: 18.6% within 10 min,
average walk 19.4 min
```

Head it `Residents within 10 min`. Use a monospace font (Consolas or Courier New) so
the numbers line up, or a two-column label pair.

---

## 5. Map 3 - Reaching 90% of what is possible

### cells - 47 sites (same bands)
1. Right-click `cells - 10 sites` > **Styles > Copy Style > All Style Categories**.
2. Right-click `cells - 47 sites` > **Styles > Paste Style > All Style Categories**.
3. Double-click `cells - 47 sites` > Symbology > change **Value** from `band_10` to
   `band_final`. The categories keep their colours because the band names match. Check
   all five are still ticked and in order. OK.

### sites - by tier (rule-based)
1. Double-click `sites - by tier` > **Symbology** > **Rule-based**.
2. Edit the default rule, then add three more with the green **+**:

   | Rule label | Filter | Symbol |
   |---|---|---|
   | Tier 1: sites 1-10 | `"tier" = 1` | the numbered yellow cross from Map 2 (copy the symbol: in `sites - first 10` Symbology right-click the symbol > Copy Symbol, then Paste Symbol here) |
   | Tier 2: sites 11-19 | `"tier" = 2` | circle `2.8` mm, fill template yellow, stroke `#1F1F1F` 0.4 mm |
   | Tier 3: sites 20-34 | `"tier" = 3` | circle `2.2` mm, fill white, stroke `#1F1F1F` 0.4 mm |
   | Tier 4: sites 35-47 | `"tier" = 4` | circle `1.7` mm, fill `#8A8A8A`, stroke `#1F1F1F` 0.3 mm |

   Size and brightness fall with priority, so the build order reads at a glance.
3. **Labels** tab > **Rule-based labeling** > one rule, Filter `"tier" = 1`, Value
   `rank`, same settings as the Map 2 numbers. Only the first ten are numbered.

### The Map 3 tier table (legend column text)

```
Tier  Sites   Within 10 min   Of the maximum
 1    1-10        18.6%            31%
 2    11-19       31.1%            52%
 3    20-34       45.1%            75%
 4    35-47       54.4%            90%

All 80 candidates open: 60.2% at most
```

Two sentences can sit under it: "Each tier needs more sites for less progress. The
last 13 sites add 9 points of coverage."

---

## 6. Map themes (one per panel)

Map themes store which layers are visible, so each layout frame can show its own set.

1. In the Layers panel, tick only the Map 1 layers:
   `candidates`, `stations`, `rail_metro`, `study_area`, `cells - residents`, `sea`
   (and `districts` if used).
2. Layers panel toolbar > the **eye** icon (**Manage Map Themes**) > **Add Theme...** >
   name `Map 1` > OK.
3. Tick only the Map 2 layers:
   `sites - first 10`, `stations`, `rail_metro`, `study_area`, `cells - 10 sites`, `sea`.
   Eye icon > **Add Theme...** > `Map 2`.
4. Tick only the Map 3 layers:
   `sites - by tier`, `stations`, `rail_metro`, `study_area`, `cells - 47 sites`, `sea`.
   Eye icon > **Add Theme...** > `Map 3`.
5. **Ctrl+S**.

If you change a style later, the themes keep up. If you change which layers belong on
a map, re-tick them and use the eye icon > **Replace Theme** > the theme name.

---

## 7. Print layout

### Reuse the RoutePlan layout (recommended)
The poster reuses the RoutePlan layout exactly, so start from it rather than rebuilding:

1. Open the RoutePlanner QGIS project. **Project > Layout Manager** > open the poster
   layout.
2. In the layout window: **Layout > Save as Template...** > save as
   `ParcelNetwork/qgis/routeplan_layout.qpt` (a new file; nothing in RoutePlanner changes).
   Close the RoutePlanner project without saving.
3. Reopen `qgis/parcelnetwork.qgz`. **Project > Layout Manager** > under **New from
   template** choose **Specific** > browse to `routeplan_layout.qpt` > **Create...** >
   name it `ParcelNetwork poster`.
4. The map frames will show Scotland extents and old legends. Work through the panels
   below, replacing content but keeping positions, sizes and borders.

If you cannot save a template, rebuild the layout by hand: page size as RoutePlan,
**Page Properties** > background `#000000`, then the items below in the same positions.

### Each map panel

For each of the three map frames:

1. Click the map frame > **Item Properties**.
2. **Layers**: tick **Follow map theme** > choose `Map 1`, `Map 2` or `Map 3`.
3. **Extents**: type the extent below, then press Enter. All three frames use exactly
   the same numbers so they share one frame and scale:

   | | Value |
   |---|---|
   | X min | `365500` |
   | Y min | `6667000` |
   | X max | `381000` |
   | Y max | `6688000` |

   This covers the built-up belt from Kauklahti and Espoonlahti across to Leppävaara and
   Otaniemi, plus the two northern tier 3-4 sites (Niipperi and Kalajärvi). It is taller
   than wide (15.5 x 21 km), so it suits a portrait frame. If the frame's proportions
   differ, QGIS widens one side; that is fine. To crop tighter on the belt only, use
   Y max `6683000` (the two northern sites then fall outside Map 3; say so in the
   caption).
4. **Main Properties > Scale**: note the value QGIS shows, round it to a clean number
   (e.g. `1:110 000`) and type the same value into all three frames.
5. **Background**: tick, colour `#EDE6D6` (the land colour, in case the frame shows
   areas beyond the sea layer).
6. **Frame**: keep the template's yellow border.

### Legends

For each panel's legend column:

1. Click the legend item > **Item Properties** > **Map**: set to that panel's frame.
2. Untick **Auto update**.
3. Under **Legend items**, remove every row you do not want (select > red minus), and
   double-click rows to rename them.
4. Tick **Only show items inside linked map** (under **Filter legend by map content**)
   if stray layers appear.

Legend contents:

| Panel | Legend rows | Extra items |
|---|---|---|
| Map 1 | `cells - residents` classes (title `Residents per 250 m cell`), `candidates` chains (title `Candidate sites`), Rail, Metro | **Scale bar** (Add Item > Scale Bar, Map = Map 1 frame, units Kilometers, 2 km segments, Single Box, yellow text) and **North arrow** (Add Item > North Arrow), both in this column |
| Map 2 | `cells - 10 sites` bands (title `Walk to nearest locker`), one cross symbol (`Locker, numbered by build order`) | The site list label (section 4) |
| Map 3 | `cells - 47 sites` bands (same title), the four tier rules (title `Build priority`) | The tier table label (section 5) |

For the list and table: **Add Item > Add Label**, paste the text, font Consolas 7-8 pt,
white or light grey on black.

### Panel titles and captions (four lines each)

Panel titles in the template yellow:

- `1  Where people live, and where lockers could go`
- `2  The first ten lockers`
- `3  Reaching 90% of what is possible`

Captions:

**Map 1**
> Residents per 250 m cell (HSY 2025) and the 80 candidate sites.
> Stores and shopping centres cluster in the same centres as people:
> Leppävaara, Tapiola, Matinkylä, Espoonlahti and Espoon keskus.
> Between them, lower-density neighbourhoods have few candidates.

**Map 2**
> Walking time to the nearest of the first ten sites.
> The four largest shopping centres come first.
> Together the ten put 18.6% of residents within 10 minutes;
> a quarter still have no locker within 30 minutes.

**Map 3**
> Walking time with all 47 sites, coloured by build tier.
> 54.4% are within 10 minutes: 90% of the 60.2% that any network
> of these host types could reach. Late sites each add little:
> the last 13 add 9 points of coverage.

---

## 8. Page text

### Title
**Placing Parcel Lockers: How Many, and Where?**

### Intro
> Parcel lockers let a delivery network serve a whole area from a handful of sites,
> typically hosted inside supermarkets and kiosks. The planning questions are how many
> sites are needed and where they should go. This analysis answers both for Espoo, a
> polycentric city of around 325,000, using only the kinds of location Budbee currently
> hosts its lockers in. It measures walking time along real streets and paths from every
> populated 250 m grid cell to the nearest site, and adds sites one at a time where each
> cuts the most total walking. It runs as a short pipeline of Python scripts on open
> data, producing a formatted Excel workbook, with the cartography built in QGIS.

### Method & Scoring
- **Demand:** 328,618 residents in 2,169 populated 250 m cells (HSY 2025), each measured
  from its centre.
- **Candidates:** 80 sites from OpenStreetMap: S Group, K Group, Lidl and R-kioski stores
  and shopping centres, the location types Budbee hosts its lockers in. Stores inside a
  shopping centre count as the centre.
- **Walking time** along streets and paths (OpenStreetMap, shared foot and cycle paths
  included) at 4.8 km/h, capped at 30 minutes.
- **Greedy build:** add one site at a time, each the one that cuts total resident
  walking time the most. The order is a build sequence.
- **Stopping point:** with all 80 open, 60.2% of residents are within 10 minutes. The
  build stops at 90% of that: 47 sites.
- **Priority tiers** mark the first ten, then 50%, 75% and 90% of that maximum.

### Key findings
- No network of these host types puts more than **60%** of residents within a 10-minute
  walk: stores cluster in the centres.
- **47 sites** reach 90% of that ceiling: 54% within 10 minutes, 81% within 15,
  average walk 10.5 minutes.
- **The first ten do the most:** 19% within 10 minutes. Site 1, Iso Omena, saves 27
  times the walking of site 47.
- **Each tier needs more sites for less:** 10 sites reach the first 31% of the maximum,
  the last 13 add only 15%.
- **Shopping centres lead:** 16 of the 23 are chosen, including the first four (Iso
  Omena, Sello, Suvelan Ostari, Lippulaiva).
- **The edges stay expensive:** at 47 sites, 16% within 10 minutes in Suur-Kauklahti and
  18% in Pohjois-Espoo, against 68% in Suur-Leppävaara.

### Limitations
- A from-scratch design on open data, not an audit of any operator's actual network.
- Residents stand in for demand; pickups near work or on commutes are not captured.
- Sites are limited to the location types Budbee currently uses; stores come from
  OpenStreetMap and may be incomplete or out of date (three closed R-kioskis removed).
- One locker per site, no capacity limits.
- Lockers across the Helsinki and Vantaa boundaries are ignored, so edge areas look
  slightly worse served than they are.
- 250 m cells (about a 3-minute walk) measured from their centres; the greedy order is
  close to, but not guaranteed to be, the best set for each size.

### Footer
Left:
> Population grid and map context: Helsinki Region Environmental Services HSY, CC BY 4.0.
> Stores and walking network: (c) OpenStreetMap contributors, ODbL.

Right:
> github.com/samw0907/ParcelNetwork

---

## 9. Check and export

1. Judge label sizes in the layout at 100% zoom, not in the main canvas: label sizes are
   in points, so they only look right at the printed scale.
2. Check that Maps 2 and 3 use identical band colours and legend wording.
3. Spell-check the text boxes. Site names come from OpenStreetMap; one has a typo,
   "K-Market Iiivisniemi" (should be Iivisniemi, site 40). It is not labelled on the
   maps, but correct it if you add it anywhere.
4. **Layout > Export as PDF...** for the final poster (tick **Always export as vector**
   if offered, for crisp text).
5. **Layout > Export as Image...** > PNG, **300 dpi**, for a preview image.
6. **Ctrl+S** to save the project.

---

## 10. Field reference

| Layer | Field | Meaning |
|---|---|---|
| cells | `residents` | residents in the cell (HSY 2025) |
| cells | `min_10`, `band_10`, `site_10` | walk minutes, band and nearest site id with sites 1-10 open (`site_10` blank if none within 30 min) |
| cells | `min_final`, `band_final`, `site_final` | the same with all 47 sites open |
| candidates | `chain`, `merged_names` | chain, and stores merged into the site |
| candidates | `rank`, `tier` | build order and tier if chosen, blank if not |
| sites_selected | `rank`, `tier` | build order (1-47) and priority tier (1-4) |
| sites_selected | `residents_new` | residents brought closer when the site was added |
| sites_selected | `residents_nearest_final` | residents for whom it is the nearest of the 47 |
| stations | `asema`, `tyyppi` | station name; `juna-asemat` rail, `metroasemat` metro |
| rail_metro | `tyyppi` | `l_jrata` rail, `l_metror` metro |
