# scripts/01_population_grid.py
"""
Step 1: Population grid, study area and map context.

Fetches from the HSY open WFS: the 250 m population grid, municipal boundaries,
major districts, rail and metro lines, stations and sea area. Builds the study
area as the union of Espoo and Kauniainen, keeps the grid cells whose centroid
falls inside it, and attaches a major district to each cell by centroid.

Only total residents (asukkaita) are used. HSY suppresses the age bands in small
cells for privacy (coded 99); these cells are counted and reported, and the
resident total is compared with the official Statistics Finland population.

Every raw WFS response is cached under data/raw/ and reused on later runs.
Everything is reprojected from EPSG:3879 to EPSG:3067.

Output layers in data/processed/grid.gpkg:
  cells       populated cells in the study area (cell_id, residents, district)
  study_area  Espoo + Kauniainen, one polygon
  districts   the seven Espoo major districts plus Kauniainen
  rail_metro  rail and metro lines, clipped to the context extent
  stations    rail and metro stations (map labels only, never candidates)
  sea         sea area, clipped to the context extent

Source data and licensing: see DATA_SOURCES.md.
"""

import json

import geopandas as gpd
import requests

from config import GRID_GPKG, GRID_YEAR, HSY_CRS, MUNICIPALITIES, RAW_DIR, TARGET_CRS

# --- Configuration ---------------------------------------------------------

HSY_WFS_URL = "https://kartta.hsy.fi/geoserver/wfs"
PAGE_SIZE = 5000

LAYERS = {
    "grid": f"asuminen_ja_maankaytto:Vaestotietoruudukko_{GRID_YEAR}",
    "municipalities": "taustakartat_ja_aluejaot:seutukartta_kunta_2021",
    "districts": "taustakartat_ja_aluejaot:seutukartta_suur_2021",
    "rail_metro": "taustakartat_ja_aluejaot:seutukartta_juna_metro_radat",
    "stations": "taustakartat_ja_aluejaot:seutukartta_asemat",
    "sea": "asuminen_ja_maankaytto:maanpeite_merialue_2024",
}

AGE_BANDS = ["ika0_9", "ika10_19", "ika20_29", "ika30_39", "ika40_49",
             "ika50_59", "ika60_69", "ika70_79", "ika_yli80"]
SUPPRESSED = 99

# Context layers are clipped to the study area's bounding box plus this margin.
CONTEXT_MARGIN_M = 3000

# Official population at 31 December, Statistics Finland table 11ra
# (StatFin vaerak, "Vaesto 31.12."), Espoo KU049 + Kauniainen KU235, fetched
# 2026-09-25. Both years are shown because the grid's reference date is checked
# against them.
OFFICIAL_POPULATION = {
    2024: 320_931 + 10_253,
    2025: 325_716 + 10_318,
}
MAX_GAP = 0.05


# --- Helpers -------------------------------------------------------------------

def fetch_layer(key):
    """Return one HSY WFS layer as a GeoDataFrame in HSY_CRS, paging through the
    server limit. The combined GeoJSON is cached in data/raw/ and never refetched."""
    layer = LAYERS[key]
    cache = RAW_DIR / f"hsy_{layer.split(':')[1]}.geojson"
    if cache.exists():
        print(f"  using cached {cache.name}")
    else:
        print(f"  downloading {layer}")
        features, start = [], 0
        while True:
            params = {
                "service": "WFS", "version": "2.0.0", "request": "GetFeature",
                "typeNames": layer, "outputFormat": "application/json",
                "count": PAGE_SIZE, "startIndex": start,
            }
            resp = requests.get(HSY_WFS_URL, params=params, timeout=120)
            resp.raise_for_status()
            body = resp.json()
            page = body["features"]
            features.extend(page)
            if len(page) < PAGE_SIZE:
                break
            start += PAGE_SIZE
        if len(features) != body["numberMatched"]:
            raise SystemExit(f"{layer}: got {len(features)} of {body['numberMatched']} features")
        payload = {"type": "FeatureCollection", "features": features}
        cache.write_text(json.dumps(payload), encoding="utf-8")

    # The cached GeoJSON carries no CRS member; HSY publishes in EPSG:3879,
    # easting first.
    gdf = gpd.read_file(cache)
    return gdf.set_crs(HSY_CRS, allow_override=True)


# --- Main --------------------------------------------------------------------

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    GRID_GPKG.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching HSY layers")
    raw = {key: fetch_layer(key).to_crs(TARGET_CRS) for key in LAYERS}

    municipalities = raw["municipalities"]
    in_area = municipalities[municipalities["nimi"].isin(MUNICIPALITIES)]
    missing = set(MUNICIPALITIES) - set(in_area["nimi"])
    if missing:
        raise SystemExit(f"Municipalities not found in boundary layer: {missing}")
    study_area = gpd.GeoDataFrame(
        {"name": [" + ".join(MUNICIPALITIES)]},
        geometry=[in_area.geometry.union_all()], crs=TARGET_CRS,
    )
    area_geom = study_area.geometry.iloc[0]

    codes = set(in_area["kunta"])
    districts = raw["districts"]
    districts = districts[districts["kunta"].isin(codes)][["kunta", "nimi", "geometry"]]
    districts = districts.rename(columns={"kunta": "municipality_code", "nimi": "district"})
    districts = districts.sort_values(["municipality_code", "district"]).reset_index(drop=True)

    print("\nSelecting grid cells by centroid")
    grid = raw["grid"]
    n_grid_all = len(grid)
    centroids = grid.geometry.centroid
    cells = grid[centroids.within(area_geom)].copy()

    joined = gpd.sjoin(
        gpd.GeoDataFrame(geometry=cells.geometry.centroid, crs=TARGET_CRS),
        districts[["district", "geometry"]], how="left", predicate="within",
    )
    joined = joined[~joined.index.duplicated(keep="first")]
    cells["district"] = joined["district"]

    age = cells[AGE_BANDS]
    all_suppressed = (age == SUPPRESSED).all(axis=1)
    any_suppressed = (age == SUPPRESSED).any(axis=1)
    band_sum = age.where(age != SUPPRESSED).sum(axis=1)
    band_mismatch = int((band_sum != cells["asukkaita"])[~any_suppressed].sum())

    cells = cells.rename(columns={"index": "cell_id", "asukkaita": "residents"})
    cells["residents"] = cells["residents"].astype(int)
    zero_cells = int((cells["residents"] <= 0).sum())
    cells = cells[["cell_id", "residents", "district", "geometry"]]
    cells = cells.sort_values("cell_id").reset_index(drop=True)

    # Context layers, clipped to a margin around the study area.
    minx, miny, maxx, maxy = area_geom.bounds
    extent = (minx - CONTEXT_MARGIN_M, miny - CONTEXT_MARGIN_M,
              maxx + CONTEXT_MARGIN_M, maxy + CONTEXT_MARGIN_M)
    rail_metro = raw["rail_metro"][["tyyppi", "rata", "geometry"]].clip(extent)
    stations = raw["stations"][["tyyppi", "asema", "geometry"]].clip(extent)
    sea = raw["sea"][["geometry"]].clip(extent)
    sea = gpd.GeoDataFrame(geometry=[sea.geometry.union_all()], crs=TARGET_CRS)

    if GRID_GPKG.exists():
        GRID_GPKG.unlink()
    cells.to_file(GRID_GPKG, layer="cells", driver="GPKG")
    study_area.to_file(GRID_GPKG, layer="study_area", driver="GPKG")
    districts.to_file(GRID_GPKG, layer="districts", driver="GPKG")
    rail_metro.to_file(GRID_GPKG, layer="rail_metro", driver="GPKG")
    stations.to_file(GRID_GPKG, layer="stations", driver="GPKG")
    sea.to_file(GRID_GPKG, layer="sea", driver="GPKG")

    total = int(cells["residents"].sum())
    by_district = (
        cells.groupby("district", dropna=False)
        .agg(cells=("cell_id", "size"), residents=("residents", "sum"))
        .sort_values("residents", ascending=False)
    )
    by_district["share"] = (by_district["residents"] / total * 100).round(1)

    print("\n--- Summary ---")
    print(f"Grid layer: {LAYERS['grid']} ({n_grid_all:,} cells across HSY area)")
    print(f"Study area: {' + '.join(MUNICIPALITIES)}, {area_geom.area / 1e6:,.1f} km2")
    print(f"Cells with centroid in study area: {len(cells):,}")
    print(f"Residents in those cells: {total:,}")
    print(f"Cells with residents <= 0: {zero_cells}")
    print(f"Cells without a district: {int(cells['district'].isna().sum())}")

    print("\nPrivacy suppression (age bands coded 99):")
    print(f"  all age bands suppressed: {int(all_suppressed.sum())} cells, "
          f"{int(cells.loc[all_suppressed.values, 'residents'].sum()):,} residents")
    print(f"  at least one band coded 99: {int(any_suppressed.sum())} cells")
    print(f"  unsuppressed cells whose age bands do not sum to residents: {band_mismatch}")

    print("\nComparison with official population (Statistics Finland 11ra, 31.12.):")
    for year, official in OFFICIAL_POPULATION.items():
        gap = (total - official) / official
        flag = "" if abs(gap) <= MAX_GAP else "  EXCEEDS 5% - STOP"
        print(f"  {year}: {official:,}  grid gap {total - official:+,} ({gap:+.1%}){flag}")

    print("\nResidents by district:")
    print(by_district.to_string())

    print(f"\nWrote {GRID_GPKG}")
    print(f"  layer 'cells'      {len(cells):,} polygons")
    print(f"  layer 'study_area' 1 polygon")
    print(f"  layer 'districts'  {len(districts)} polygons")
    print(f"  layer 'rail_metro' {len(rail_metro)} lines "
          f"({', '.join(sorted(rail_metro['tyyppi'].unique()))})")
    print(f"  layer 'stations'   {len(stations)} points "
          f"({', '.join(sorted(stations['tyyppi'].unique()))})")
    print(f"  layer 'sea'        1 polygon (clipped to study area + {CONTEXT_MARGIN_M / 1000:.0f} km)")


if __name__ == "__main__":
    main()
