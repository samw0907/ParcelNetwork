# scripts/02_candidate_sites.py
"""
Step 2: Candidate locker sites.

Queries OpenStreetMap via the Overpass API for supermarkets, convenience stores,
kiosks, department stores and shopping centres inside the study area's bounding
box, then keeps only the location types Budbee currently hosts its lockers in:
stores of S Group, K Group, Lidl and R-kioski, plus shopping centres (shop=mall).
Chains are matched case-insensitively on brand, name and operator using the
patterns in config.py. Only points inside the study area polygon are kept, and a
short documented list of stale OSM objects is excluded.

Merging: a store inside a shopping centre's outline, or within SITE_MERGE_M of it,
counts as that shopping centre, and shopping centre parts that touch are one site.
Other candidates within SITE_MERGE_M of each other are also merged. Each cluster
keeps one representative (shopping centre > supermarket chain > R-kioski, then
the largest named centre) and records the names merged into it.

Output: data/processed/sites.gpkg, layer candidates
  (site_id, name, chain, merged_names, district, osm_ref)

The raw Overpass response is cached in data/raw/ and reused on later runs.
Source data and licensing: see DATA_SOURCES.md.
"""

import json
import re
import time

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union

from config import (CHAIN_PATTERNS, GRID_GPKG, MALL_CHAIN, RAW_DIR, SITE_MERGE_M,
                    SITES_GPKG, TARGET_CRS, WGS84)

# --- Configuration ---------------------------------------------------------

# Main endpoint only: public mirrors were found to serve months-old data.
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT = 180
OVERPASS_ATTEMPTS = 4
RETRY_WAIT_S = 60
SHOP_TAGS = ["supermarket", "convenience", "kiosk", "department_store", "mall"]

# Full geometry is requested so shopping centre outlines are available.
OSM_CACHE = RAW_DIR / "overpass_shops_espoo.json"

# OSM objects excluded after checking, 2026-09-25.
EXCLUDE_OSM = {
    # R-kioskis not on the official store list (r-kioski.fi/kioskit), closed
    "node/277393439": "R-kioski Suvela, Sokinsuontie 4",
    "node/497225406": "R-kioski Mankkaanportti",
    "node/6312649691": "R-kioski Keilaniemi metro",
    # Tagged shop=mall but a car dealership building
    "way/322049136": "MotorCenter Espoonlahti",
}

# Representative priority within a merged cluster (lower wins).
PRIORITY = {MALL_CHAIN: 0, "S Group": 1, "K Group": 1, "Lidl": 1, "R-kioski": 2}

# Names that look like a chain but did not match a pattern are listed for review.
NEAR_MISS = re.compile(r"prisma|s-?market|\bsale\b|alepa|herkku|citymarket|"
                       r"k-?super|k-?market|k-?extra|lidl|r-?kioski|kioski", re.I)


def build_overpass_query(bbox):
    """Shops of the listed types inside a (south, west, north, east) box."""
    box = ",".join(str(v) for v in bbox)
    lines = "\n".join(f'  nwr["shop"="{tag}"]({box});' for tag in SHOP_TAGS)
    return (
        f"[out:json][timeout:{OVERPASS_TIMEOUT}];\n"
        f"(\n{lines}\n);\n"
        "out geom;\n"
    )


def fetch_shops(bbox):
    """Return the raw Overpass JSON, querying only if the cache is absent."""
    if OSM_CACHE.exists():
        print(f"  using cached {OSM_CACHE.name}")
        return json.loads(OSM_CACHE.read_text(encoding="utf-8"))

    for attempt in range(1, OVERPASS_ATTEMPTS + 1):
        print(f"  querying Overpass API (attempt {attempt})")
        try:
            resp = requests.post(
                OVERPASS_URL,
                data={"data": build_overpass_query(bbox)},
                headers={"User-Agent": "parcel-network-analysis/1.0 (open data project)"},
                timeout=OVERPASS_TIMEOUT + 30,
            )
            if resp.ok:
                payload = resp.json()
                OSM_CACHE.write_text(json.dumps(payload), encoding="utf-8")
                return payload
            print(f"    HTTP {resp.status_code}")
        except requests.RequestException as exc:
            print(f"    {type(exc).__name__}")
        if attempt < OVERPASS_ATTEMPTS:
            time.sleep(RETRY_WAIT_S)
    raise SystemExit("Overpass API unavailable; try again later.")


def element_shape(el):
    """Point for a node, polygon for a closed way or multipolygon relation, else
    None. Coordinates are lon/lat."""
    if el["type"] == "node":
        return Point(el["lon"], el["lat"])
    if el["type"] == "way" and "geometry" in el:
        coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
        if len(coords) >= 4 and coords[0] == coords[-1]:
            return Polygon(coords)
        return LineString(coords) if len(coords) >= 2 else None
    if el["type"] == "relation":
        outers = [
            LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
            for m in el.get("members", [])
            if m.get("role") == "outer" and len(m.get("geometry", [])) >= 2
        ]
        polygons = list(polygonize(unary_union(outers))) if outers else []
        if polygons:
            return unary_union(polygons)
    return None


def shops_geodataframe(payload):
    """One row per shop: a point location plus, for shopping centres, the outline."""
    rows = []
    for el in payload.get("elements", []):
        shape = element_shape(el)
        if shape is None:
            continue
        tags = el.get("tags", {})
        rows.append({
            "osm_ref": f"{el['type']}/{el['id']}",
            "shop": tags.get("shop", ""),
            "name": tags.get("name", ""),
            "brand": tags.get("brand", ""),
            "operator": tags.get("operator", ""),
            "label": display_name(tags),
            "shape": shape,
        })
    gdf = gpd.GeoDataFrame(rows, geometry="shape", crs=WGS84).to_crs(TARGET_CRS)

    # Location: the centroid, or a point on the surface if the centroid falls
    # outside (L-shaped buildings).
    centroid = gdf.geometry.centroid
    inside = gdf.geometry.contains(centroid) | (gdf.geometry.geom_type == "Point")
    gdf["location"] = centroid.where(inside, gdf.geometry.representative_point())

    is_outline = (gdf["shop"] == "mall") & gdf.geometry.geom_type.isin(
        ["Polygon", "MultiPolygon"])
    gdf["footprint"] = gdf.geometry.where(is_outline, gdf["location"])
    gdf["outline_m2"] = np.where(is_outline, gdf.geometry.area, 0.0)
    return gdf.set_geometry("location").drop(columns="shape")


def display_name(tags):
    """Name that tells chain stores apart: 'K-Market' becomes 'K-Market Kilo' from
    the OSM branch tag, or 'Lidl Kurjenkellontie' from the street if there is no
    branch."""
    name = tags.get("name", "")
    branch = tags.get("branch", "")
    street = tags.get("addr:street", "")
    if branch and branch.lower() not in name.lower():
        return f"{name} {branch}".strip()
    if name and name == tags.get("brand") and street:
        return f"{name} {street}"
    return name


def classify(row):
    """Chain for one shop, or None if it is not a qualifying location type."""
    if row["shop"] == "mall":
        return MALL_CHAIN
    text = " | ".join([row["brand"], row["name"], row["operator"]])
    for chain, patterns in CHAIN_PATTERNS.items():
        if any(re.search(p, text, re.I) for p in patterns):
            return chain
    return None


def merge_sites(candidates):
    """Group candidates whose footprints (shopping centre outline, or point) lie
    within SITE_MERGE_M of each other, chained so A-B and B-C form one cluster,
    and keep one representative per cluster."""
    candidates = candidates.reset_index(drop=True)
    footprints = gpd.GeoSeries(candidates["footprint"], crs=TARGET_CRS)
    left, right = footprints.sindex.query(footprints, predicate="dwithin",
                                          distance=SITE_MERGE_M)
    n = len(candidates)
    adj = coo_matrix((np.ones(len(left)), (left, right)), shape=(n, n))
    _, labels = connected_components(adj, directed=False)
    candidates = candidates.assign(
        cluster=labels,
        priority=candidates["chain"].map(PRIORITY),
        unnamed=candidates["name"] == "",
    )

    rows = []
    for _, group in candidates.groupby("cluster"):
        group = group.sort_values(["priority", "unnamed", "outline_m2", "name"],
                                  ascending=[True, True, False, True])
        rep = group.iloc[0]
        others = group.iloc[1:]
        rows.append({
            "name": rep["label"] or f"({rep['chain']}, unnamed)",
            "chain": rep["chain"],
            "merged_names": "; ".join(
                f"{r['label'] or '(unnamed)'} [{r['chain']}]" for _, r in others.iterrows()
            ),
            "n_merged": len(others),
            "osm_ref": rep["osm_ref"],
            "geometry": rep["location"],
        })
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=TARGET_CRS)


# --- Main --------------------------------------------------------------------

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    study_area = gpd.read_file(GRID_GPKG, layer="study_area")
    districts = gpd.read_file(GRID_GPKG, layer="districts")
    area_geom = study_area.geometry.iloc[0]
    west, south, east, north = study_area.to_crs(WGS84).total_bounds

    print("Fetching shops from OpenStreetMap")
    payload = fetch_shops((south, west, north, east))
    osm_timestamp = payload.get("osm3s", {}).get("timestamp_osm_base", "unknown")
    shops = shops_geodataframe(payload)
    n_bbox = len(shops)
    shops = shops[shops.within(area_geom)].copy()
    print(f"  {n_bbox} shops in the bounding box, {len(shops)} inside the study area")

    shops["chain"] = shops.apply(classify, axis=1)
    matched = shops[shops["chain"].notna()].copy()
    unmatched = shops[shops["chain"].isna()]

    excluded = matched[matched["osm_ref"].isin(EXCLUDE_OSM)]
    missing_exclusions = set(EXCLUDE_OSM) - set(excluded["osm_ref"])
    matched = matched[~matched["osm_ref"].isin(EXCLUDE_OSM)]

    near_miss = unmatched[
        unmatched[["name", "brand", "operator"]].agg(" ".join, axis=1).str.contains(NEAR_MISS)
    ]
    unnamed = matched[matched["name"] == ""]

    sites = merge_sites(matched)
    joined = gpd.sjoin(sites, districts[["district", "geometry"]], how="left",
                       predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")]
    sites["district"] = joined["district"]
    sites = sites.sort_values(["district", "chain", "name"]).reset_index(drop=True)
    sites.insert(0, "site_id", range(1, len(sites) + 1))

    out = sites[["site_id", "name", "chain", "merged_names", "district", "osm_ref",
                 "geometry"]]
    if SITES_GPKG.exists():
        SITES_GPKG.unlink()
    out.to_file(SITES_GPKG, layer="candidates", driver="GPKG")

    n_outlines = int((matched["outline_m2"] > 0).sum())
    n_malls = int((matched["chain"] == MALL_CHAIN).sum())

    print("\n--- Summary ---")
    print(f"OSM data timestamp: {osm_timestamp}")
    print("Shops inside the study area by shop tag:")
    print(shops["shop"].value_counts().to_string())
    print(f"\nUnmatched (dropped): {len(unmatched)}")
    print(f"Excluded by list: {len(excluded)}")
    for ref in excluded["osm_ref"]:
        print(f"  {ref}  {EXCLUDE_OSM[ref]}")
    if missing_exclusions:
        print(f"  WARNING: exclusions not found in data: {sorted(missing_exclusions)}")

    print("\nMatched before merging, by chain and shop tag:")
    print(pd.crosstab(matched["chain"], matched["shop"], margins=True).to_string())

    print(f"\nMerging: {len(matched)} candidates -> {len(sites)} sites "
          f"({int(sites['n_merged'].sum())} merged away, "
          f"{int((sites['n_merged'] > 0).sum())} clusters)")
    print(f"  shopping centres with an outline: {n_outlines} of {n_malls} "
          f"(others merged as points within {SITE_MERGE_M} m)")
    for _, s in sites[sites["n_merged"] > 0].iterrows():
        print(f"  {s['name']} [{s['chain']}] <- {s['merged_names']}")

    print("\nFinal candidates by chain:")
    print(sites["chain"].value_counts().to_string())
    print("\nFinal candidates by district:")
    print(pd.crosstab(sites["district"], sites["chain"], margins=True).to_string())

    print(f"\nNear misses (chain-like text, no pattern match): {len(near_miss)}")
    for _, r in near_miss.iterrows():
        print(f"  {r['osm_ref']} shop={r['shop']} name='{r['name']}' "
              f"brand='{r['brand']}' operator='{r['operator']}'")
    print(f"Chain stores with no name (before merging): {len(unnamed)}")
    for _, r in unnamed.iterrows():
        print(f"  {r['osm_ref']} shop={r['shop']} chain={r['chain']}")
    n_unnamed_sites = int(sites["name"].str.startswith("(").sum())
    print(f"Sites still unnamed after merging: {n_unnamed_sites}")

    print(f"\nWrote {SITES_GPKG}")
    print(f"  layer 'candidates' {len(sites)} points")


if __name__ == "__main__":
    main()
