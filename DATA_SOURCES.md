# Data Sources

All sources are open data and keyless. Verify layer names before downloading, as services
add and rename layers between years. Layer names below were checked on 2026-09-25.

---

## 1. Population grid, boundaries and map context: HSY WFS

**HSY (Helsinki Region Environmental Services) open GeoServer WFS**

Endpoint: `https://kartta.hsy.fi/geoserver/wfs`

Request pattern (GeoJSON output):

```
?service=WFS&version=2.0.0&request=GetFeature
&typeNames=<layer>&outputFormat=application/json
```

Use `GetCapabilities` to list layers. Page through results (`count` / `startIndex`) if a
layer is larger than the server's feature limit.

Layers used:

| Layer | Use |
|---|---|
| `asuminen_ja_maankaytto:Vaestotietoruudukko_2025` | 250 m population grid (latest; years 2015-2025 available). Check for a newer year at build time. |
| `taustakartat_ja_aluejaot:seutukartta_kunta_2021` | Municipal boundaries: build the Espoo + Kauniainen study area |
| `taustakartat_ja_aluejaot:seutukartta_suur_2021` | Major districts (suuralueet), for the district summary |
| `taustakartat_ja_aluejaot:seutukartta_juna_metro_radat` | Rail and metro lines (map context) |
| `taustakartat_ja_aluejaot:seutukartta_asemat` | Stations (map labels and context only, never candidates) |
| `asuminen_ja_maankaytto:maanpeite_merialue_2024` | Sea area (basemap); use a newer year if available |

Population grid notes:

- Native CRS **EPSG:3879** (ETRS-GK25). Reproject to EPSG:3067 on load.
- 5,826 cells across the four HSY cities in the 2025 layer.
- Fields: `index` (cell id), `asukkaita` (total residents), `asvaljyys` (average floor area
  per resident), age bands `ika0_9` ... `ika_yli80`, `paivitys_pvm` (update date).
- **Privacy suppression:** in small cells the age bands are coded `99` (seen in a cell with
  6 residents), while `asukkaita` is still given. This project uses `asukkaita` only.
  Step 1 must report how many cells are suppressed and check whether any cells are dropped
  entirely, by comparing the total against the official population.
- Licence: HSY open data is published under CC BY 4.0. Confirm on the HSY open data page
  and attribute as "Helsinki Region Environmental Services HSY".

Field names confirmed in Step 1 (2026-09-25):

- `seutukartta_kunta_2021`: `nimi` (municipality name), `kunta` (code; Espoo 049,
  Kauniainen 235)
- `seutukartta_suur_2021`: `nimi` (district name), `kunta` (municipality code)
- `seutukartta_juna_metro_radat`: `tyyppi` (`l_jrata` rail, `l_metror` metro), `rata`
- `seutukartta_asemat`: `tyyppi` (`juna-asemat`, `metroasemat`), `asema` (name)
- All layers are served in EPSG:3879, easting first. The server returned every layer in
  a single request (no feature limit hit); the script still pages and checks the count.
- Age bands are suppressed (coded 99) in every cell with fewer than 100 residents.

Official population used for the Step 1 check: Statistics Finland StatFin table 11ra
(`https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/vaerak/11ra.px`), "Vaesto 31.12.",
Espoo KU049 + Kauniainen KU235.

---

## 2. Candidate sites: OpenStreetMap via Overpass

Endpoint: `https://overpass-api.de/api/interpreter`. It often returns 504 or 429 under
load; the script retries after a pause. Do not use public mirrors: in Step 2 the
kumi.systems mirror served OSM data four months old. The query uses `out geom;` (not
`out geom tags;`, which drops relation members) so shopping centre outlines are
available. The raw JSON is cached to `data/raw/overpass_shops_espoo.json`, and the
summary prints its `timestamp_osm_base`.

Tags:

- `shop=supermarket`, `shop=convenience`, `shop=kiosk` (and `shop=department_store` if
  chain stores use it)
- `shop=mall` for shopping centres

Chain matching, case-insensitive, on `brand`, `name` and `operator`:

| Chain | Patterns |
|---|---|
| S Group | Prisma, S-market, Sale, Alepa (Food Market Herkku if present) |
| K Group | K-Citymarket, K-Supermarket, K-Market (K-Extra if present) |
| Lidl | Lidl |
| R-kioski | R-kioski |

Planning check (2026-09-25, bounding box around Espoo, not clipped to the boundary): 171
supermarket, convenience and kiosk objects, of which K Group 51, S Group 44, Lidl 16,
R-kioski 11. R-kioski looks low; Step 2 must report counts for the owner to spot-check.

Why only these location types: Budbee's press releases name S Group (HOK-Elanto), K Group,
Lidl and R-kioski as its locker hosts, and Budbee Boxes are found in shopping centres
(Sello, A Bloc). See `BACKGROUND.md` section 2.

- Licence: Open Database Licence. Attribution: "(c) OpenStreetMap contributors".

---

## 3. Walking network: OpenStreetMap via OSMnx

- `osmnx.graph_from_polygon(<study area buffered 500 m, in EPSG:4326>, network_type="walk")`
- Cache the downloaded graph (GraphML) in `data/raw/` so it is fetched once.
- Project to EPSG:3067 for distances in metres.
- Licence: ODbL, as above.

---

## 4. Budbee context (text only, not data)

These are sources for the background text and page framing. No Budbee data is used in the
analysis. Budbee's own API (`developer.budbee.com`) has country-wide locker and postcode
endpoints, but they require merchant credentials (HTTP 401 without), so they are not used.

- Locker hosts (HOK-Elanto, Lidl, R-kioski): https://news.cision.com/fi/miltton/r/budbee-laajentaa-toimintaansa-pakettiautomaatteihin---yli-100-paikasta-suomessa-loytyy-pian-taysin-u,c3345351
- Locker hosts (K Group, Lidl, S Group, R-kioski) and northern expansion, Nov 2025: https://newsroom.notified.com/news/389186/budbee-part-of-the-instabee-group-expands-fur
- 15 new locker-only towns, May 2025: https://dawn.fi/uutiset/2025/05/28/budbee-pakettiautomaatit-15-uutta-paikkakuntaa
- West coast expansion, March 2026: https://press.instabee.com/posts/pressreleases/instabee-groupin-budbee-laajenee-voimakkaasti
- Pori and Rauma, 2024: https://www.ostologistiikka.fi/kuljetus/budbee-laajentaa-kahteen-uuteen-kaupunkiin/
- Budbee Box at A Bloc, Otaniemi: https://abloc.fi/en/stores/budbee-box/
- Budbee Box at Sello: https://www.sello.fi/palvelut/pakettiautomaatit-posti-pakettipiste-ja-budbee

---

## 5. Coordinate reference systems

- HSY data arrives in EPSG:3879. OSM and Overpass return EPSG:4326.
- Store and export everything in **EPSG:3067** (ETRS-TM35FIN), the standard national
  projected CRS, with distances in metres.
- Set the QGIS project CRS to EPSG:3067.

---

## 6. Attribution block for the poster

> Population grid and map context: Helsinki Region Environmental Services HSY, CC BY 4.0.
> Stores and walking network: (c) OpenStreetMap contributors, ODbL.
