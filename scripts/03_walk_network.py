# scripts/03_walk_network.py
"""
Step 3: Walking network and snapping.

Downloads the OpenStreetMap walking network for the study area buffered by
NETWORK_BUFFER_M, so paths near the boundary connect. The filter is OSMnx's
standard "walk" filter with one change: cycleways are kept. Finland maps most
footpaths as shared foot and cycle paths (highway=cycleway, foot=designated),
which the standard filter drops; cycleways tagged foot=no are still excluded. Keeps
the largest connected part of the network (small detached pieces, such as paths on
islands with no bridge, would otherwise trap a snapped point), and projects it to
EPSG:3067.

Every populated cell centroid and every candidate site is snapped to its nearest
network node, and the straight-line snap distance is recorded. Step 4 adds the snap
distance to the network walking distance at both ends. Cells snapped further than
SNAP_FLAG_M are flagged and reported, with the distribution used to set
SNAP_EXCLUDE_M.

Outputs:
  data/raw/walk_network_with_cycleways.graphml   unprojected graph (cache)
  data/processed/walk_network_3067.graphml   largest component, projected (Step 4)
  data/processed/snaps.gpkg              layers cells and sites (points) with
                                         node_id and snap_m

Source data and licensing: see DATA_SOURCES.md.
"""

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd

from config import (GRID_GPKG, PROCESSED_DIR, RAW_DIR, SITES_GPKG, SNAP_FLAG_M,
                    SNAPS_GPKG, TARGET_CRS, WALK_GRAPH, WGS84)

# --- Configuration ---------------------------------------------------------

NETWORK_BUFFER_M = 500

# OSMnx's "walk" filter (osmnx 2.1) with "cycleway" removed from the excluded
# highway types.
WALK_FILTER = (
    '["highway"]["area"!~"yes"]["access"!~"private"]'
    '["highway"!~"abandoned|bus_guideway|construction|motor|no|planned|platform|'
    'proposed|raceway|razed|rest_area|services"]'
    '["foot"!~"no"]["service"!~"private"]'
    '["sidewalk"!~"separate"]["sidewalk:both"!~"separate"]'
    '["sidewalk:left"!~"separate"]["sidewalk:right"!~"separate"]'
)
PROJECTED_GRAPH = PROCESSED_DIR / "walk_network_3067.graphml"

# OSMnx caches its raw Overpass responses here, alongside the other raw data.
ox.settings.cache_folder = str(RAW_DIR / "osmnx_cache")
ox.settings.use_cache = True

# Snap-distance thresholds tabulated to choose SNAP_EXCLUDE_M.
SNAP_STEPS_M = [100, 150, 200, 300, 400, 500, 750, 1000]


def load_walk_graph(study_area):
    """Unprojected walking graph for the buffered study area, from cache if present."""
    if WALK_GRAPH.exists():
        print(f"  using cached {WALK_GRAPH.name}")
        return ox.load_graphml(WALK_GRAPH)

    print("  downloading walking network (several minutes)")
    polygon = study_area.buffer(NETWORK_BUFFER_M).to_crs(WGS84).iloc[0]
    graph = ox.graph_from_polygon(polygon, custom_filter=WALK_FILTER, retain_all=True)
    ox.save_graphml(graph, WALK_GRAPH)
    return graph


def snap(graph, points):
    """Nearest node id and straight-line distance (m) for each point."""
    nodes, dists = ox.distance.nearest_nodes(
        graph, points.x.values, points.y.values, return_dist=True
    )
    return np.asarray(nodes), np.asarray(dists)


def weighted_percentile(values, weights, q):
    order = np.argsort(values)
    cum = np.cumsum(weights[order]) / weights.sum()
    return values[order][np.searchsorted(cum, q / 100)]


# --- Main --------------------------------------------------------------------

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    study_area = gpd.read_file(GRID_GPKG, layer="study_area")
    cells = gpd.read_file(GRID_GPKG, layer="cells")
    sites = gpd.read_file(SITES_GPKG, layer="candidates")

    print("Loading walking network")
    graph = load_walk_graph(study_area)
    n_nodes_all, n_edges_all = graph.number_of_nodes(), graph.number_of_edges()
    n_components = nx.number_weakly_connected_components(graph)

    largest = max(nx.weakly_connected_components(graph), key=len)
    graph = graph.subgraph(largest).copy()

    print("Projecting to", TARGET_CRS)
    graph = ox.project_graph(graph, to_crs=TARGET_CRS)
    ox.save_graphml(graph, PROJECTED_GRAPH)

    print("Snapping cells and sites to the nearest node")
    cell_points = cells.geometry.centroid
    cell_nodes, cell_snap = snap(graph, cell_points)
    site_nodes, site_snap = snap(graph, sites.geometry)

    cells_out = gpd.GeoDataFrame(
        {"cell_id": cells["cell_id"], "residents": cells["residents"],
         "district": cells["district"], "node_id": cell_nodes,
         "snap_m": cell_snap.round(1)},
        geometry=cell_points, crs=TARGET_CRS,
    )
    sites_out = gpd.GeoDataFrame(
        {"site_id": sites["site_id"], "name": sites["name"], "chain": sites["chain"],
         "node_id": site_nodes, "snap_m": site_snap.round(1)},
        geometry=sites.geometry, crs=TARGET_CRS,
    )

    if SNAPS_GPKG.exists():
        SNAPS_GPKG.unlink()
    cells_out.to_file(SNAPS_GPKG, layer="cells", driver="GPKG")
    sites_out.to_file(SNAPS_GPKG, layer="sites", driver="GPKG")

    residents = cells_out["residents"].to_numpy(dtype=float)
    total = residents.sum()
    flagged = cells_out[cells_out["snap_m"] > SNAP_FLAG_M]

    print("\n--- Summary ---")
    print(f"Downloaded network: {n_nodes_all:,} nodes, {n_edges_all:,} edges, "
          f"{n_components:,} connected pieces")
    print(f"Largest connected piece kept: {graph.number_of_nodes():,} nodes, "
          f"{graph.number_of_edges():,} edges "
          f"({n_nodes_all - graph.number_of_nodes():,} nodes dropped)")

    pct = [50, 90, 95, 99, 100]
    print("\nCell snap distance (m), by cell:     " + "  ".join(
        f"p{q} {np.percentile(cell_snap, q):.0f}" for q in pct))
    print("Cell snap distance (m), by resident: " + "  ".join(
        f"p{q} {weighted_percentile(cell_snap, residents, q):.0f}" for q in pct))
    print("Site snap distance (m):              " + "  ".join(
        f"p{q} {np.percentile(site_snap, q):.0f}" for q in pct))

    print(f"\nFlagged cells (snap > {SNAP_FLAG_M} m): {len(flagged)} cells, "
          f"{int(flagged['residents'].sum()):,} residents")
    print("\nCells and residents beyond each snap distance:")
    steps = pd.DataFrame({
        "snap_over_m": SNAP_STEPS_M,
        "cells": [int((cell_snap > s).sum()) for s in SNAP_STEPS_M],
        "residents": [int(residents[cell_snap > s].sum()) for s in SNAP_STEPS_M],
    })
    steps["share_residents"] = (steps["residents"] / total * 100).round(2)
    print(steps.to_string(index=False))

    print("\nFlagged cells, largest snap first:")
    show = flagged.sort_values("snap_m", ascending=False)
    print(show[["cell_id", "residents", "district", "snap_m"]].head(25).to_string(index=False))

    print("\nSites with the largest snap distance:")
    print(sites_out.sort_values("snap_m", ascending=False)[
        ["site_id", "name", "chain", "snap_m"]].head(5).to_string(index=False))

    print(f"\nWrote {PROJECTED_GRAPH}")
    print(f"Wrote {SNAPS_GPKG}")
    print(f"  layer 'cells' {len(cells_out):,} points")
    print(f"  layer 'sites' {len(sites_out)} points")


if __name__ == "__main__":
    main()
