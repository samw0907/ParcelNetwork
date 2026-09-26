# scripts/04_site_selection.py
"""
Step 4: Site selection.

For each candidate site, computes the walking distance along the network to every
populated cell (one shortest-path run per site, limited to the walk cap), adds the
snap distance at both ends and converts to minutes at WALK_SPEED_M_PER_MIN. Walks
longer than WALK_CAP_MIN, or unreachable, count as WALK_CAP_MIN.

Sites are then chosen greedily. Start with no lockers (every cell at the cap). At
each step add the candidate that most reduces total resident walking time
(residents times capped minutes), and update each cell to its nearest chosen site.

Stopping rule: even with every candidate open, only part of the population is
within TARGET_MIN minutes (the ceiling). Selection stops when the share within
TARGET_MIN reaches TARGET_SHARE of that ceiling, or at MAX_SITES.

Output: data/processed/selection.gpkg
  cells_access    cell polygons: residents, district, min_10, band_10, site_10,
                  min_final, band_final, site_final
  sites_selected  chosen sites in rank order (points), with a priority tier:
                  tier 1 the first SNAPSHOT_SITES, then tiers ending where the
                  share within TARGET_MIN reaches each TIER_MILESTONES fraction of
                  the ceiling, the last tier ending at the stopping point
  coverage_curve  one row per number of sites (no geometry)
  run_summary     ceiling, target and final N as item / value rows (no geometry)
"""

import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd
import pyogrio
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

from config import (BAND_EDGES_MIN, GRID_GPKG, MAX_SITES, PROCESSED_DIR, SELECTION_GPKG,
                    SITES_GPKG, SNAP_EXCLUDE_M, SNAPS_GPKG, SNAPSHOT_SITES, TARGET_CRS,
                    TARGET_MIN, TARGET_SHARE, TIER_MILESTONES, WALK_CAP_MIN,
                    WALK_SPEED_M_PER_MIN)

PROJECTED_GRAPH = PROCESSED_DIR / "walk_network_3067.graphml"
REPORT_MIN = [5, 10, 15]


def graph_to_matrix(graph):
    """Undirected sparse distance matrix (metres), keeping the shortest of any
    parallel edges, and a node id -> row lookup."""
    nodes = list(graph.nodes)
    index = {n: i for i, n in enumerate(nodes)}
    edges = pd.DataFrame(
        [(index[u], index[v], d["length"]) for u, v, d in graph.edges(data=True)],
        columns=["u", "v", "length"],
    )
    edges[["u", "v"]] = np.sort(edges[["u", "v"]].to_numpy(), axis=1)
    edges = edges[edges["u"] != edges["v"]].groupby(["u", "v"], as_index=False)["length"].min()
    matrix = csr_matrix((edges["length"], (edges["u"], edges["v"])),
                        shape=(len(nodes), len(nodes)))
    return matrix, index


def band_labels():
    edges = BAND_EDGES_MIN
    labels = [f"under {edges[0]}"]
    labels += [f"{a}-{b}" for a, b in zip(edges[:-1], edges[1:])]
    labels += [f"over {edges[-1]}"]
    return labels


def to_band(minutes):
    """Walk-time band; a cell exactly on an edge (e.g. 10.0) goes in the lower band,
    matching 'within 10 minutes'."""
    bins = [-np.inf] + BAND_EDGES_MIN + [np.inf]
    return pd.cut(minutes, bins=bins, labels=band_labels(), right=True).astype(str)


def coverage(minutes, residents):
    """Average capped walk and share within each REPORT_MIN threshold."""
    total = residents.sum()
    row = {"avg_walk_min": float(np.average(minutes, weights=residents))}
    for t in REPORT_MIN:
        row[f"share_{t}min"] = float(residents[minutes <= t].sum() / total)
    return row


# --- Main --------------------------------------------------------------------

def main():
    cells = gpd.read_file(GRID_GPKG, layer="cells")
    snaps = gpd.read_file(SNAPS_GPKG, layer="cells")
    site_snaps = gpd.read_file(SNAPS_GPKG, layer="sites")
    candidates = gpd.read_file(SITES_GPKG, layer="candidates")

    cells = cells.merge(snaps[["cell_id", "node_id", "snap_m"]], on="cell_id")
    n_excluded = int((cells["snap_m"] > SNAP_EXCLUDE_M).sum())
    res_excluded = int(cells.loc[cells["snap_m"] > SNAP_EXCLUDE_M, "residents"].sum())
    cells = cells[cells["snap_m"] <= SNAP_EXCLUDE_M].reset_index(drop=True)
    sites = candidates.merge(site_snaps[["site_id", "node_id", "snap_m"]], on="site_id")

    print("Loading walking network")
    graph = ox.load_graphml(PROJECTED_GRAPH)
    matrix, index = graph_to_matrix(graph)

    cap_m = WALK_CAP_MIN * WALK_SPEED_M_PER_MIN
    print(f"Shortest paths from {len(sites)} sites (limit {cap_m:,.0f} m)")
    site_rows = [index[n] for n in sites["node_id"]]
    cell_cols = np.array([index[n] for n in cells["node_id"]])
    network_m = dijkstra(matrix, directed=False, indices=site_rows, limit=cap_m)[:, cell_cols]
    walk_m = network_m + sites["snap_m"].to_numpy()[:, None] + cells["snap_m"].to_numpy()[None, :]
    minutes = np.minimum(walk_m / WALK_SPEED_M_PER_MIN, WALK_CAP_MIN)   # sites x cells

    residents = cells["residents"].to_numpy(dtype=float)
    total = residents.sum()

    all_open = minutes.min(axis=0)
    ceiling = residents[all_open <= TARGET_MIN].sum() / total
    target = TARGET_SHARE * ceiling

    print("Greedy selection")
    current = np.full(len(cells), float(WALK_CAP_MIN))
    nearest = np.full(len(cells), -1)
    chosen, site_rows_out, curve_rows = [], [], []
    snapshot = None
    while True:
        improved = np.minimum(current[None, :], minutes)
        saved = ((current[None, :] - improved) * residents).sum(axis=1)
        saved[chosen] = -1
        k = int(saved.argmax())

        newly = minutes[k] < current
        current = np.where(newly, minutes[k], current)
        nearest = np.where(newly, k, nearest)
        chosen.append(k)
        n = len(chosen)

        cov = coverage(current, residents)
        site = sites.iloc[k]
        site_rows_out.append({
            "rank": n, "site_id": int(site["site_id"]), "name": site["name"],
            "chain": site["chain"], "district": site["district"],
            "residents_new": int(residents[newly].sum()),
            "resident_min_saved": float(saved[k]), **cov,
            "geometry": site.geometry,
        })
        curve_rows.append({"n_sites": n, **cov})

        if n == SNAPSHOT_SITES:
            snapshot = (current.copy(), nearest.copy())
        if cov[f"share_{TARGET_MIN}min"] >= target:
            stop_reason = "target reached"
            break
        if n >= MAX_SITES:
            stop_reason = "MAX_SITES reached"
            break

    n_final = len(chosen)
    min_10, near_10 = snapshot

    def site_id_of(nearest_index):
        """Chosen site id per cell; blank where no chosen site is within the cap."""
        ids = pd.Series(sites["site_id"].to_numpy()[nearest_index], dtype="Int64")
        return ids.mask(nearest_index < 0)

    cells_access = gpd.GeoDataFrame({
        "cell_id": cells["cell_id"],
        "residents": cells["residents"],
        "district": cells["district"],
        "min_10": min_10,
        "band_10": to_band(min_10),
        "site_10": site_id_of(near_10),
        "min_final": current,
        "band_final": to_band(current),
        "site_final": site_id_of(nearest),
    }, geometry=cells.geometry, crs=TARGET_CRS)

    sites_selected = gpd.GeoDataFrame(site_rows_out, geometry="geometry", crs=TARGET_CRS)
    nearest_final = cells_access.groupby("site_final")["residents"].sum()
    sites_selected["residents_nearest_final"] = (
        sites_selected["site_id"].map(nearest_final).fillna(0).astype(int))
    curve = pd.DataFrame(curve_rows)

    share_col = f"share_{TARGET_MIN}min"
    tier_ends = [SNAPSHOT_SITES]
    for fraction in TIER_MILESTONES:
        tier_ends.append(int(curve.loc[curve[share_col] >= fraction * ceiling, "n_sites"].min()))
    tier_ends.append(n_final)
    sites_selected["tier"] = np.searchsorted(tier_ends, sites_selected["rank"]) + 1

    # Walk-time distribution at the two map snapshots, to check the band edges.
    fine_bins = [-np.inf, 3, 5, 7.5, 10, 12.5, 15, 20, 25, 29.99, np.inf]
    fine_labels = ["<=3", "3-5", "5-7.5", "7.5-10", "10-12.5", "12.5-15", "15-20",
                   "20-25", "25-30", "capped 30"]
    dist = pd.DataFrame({
        f"{SNAPSHOT_SITES} sites": pd.Series(residents).groupby(
            pd.cut(min_10, fine_bins, labels=fine_labels), observed=False).sum() / total,
        f"{n_final} sites": pd.Series(residents).groupby(
            pd.cut(current, fine_bins, labels=fine_labels), observed=False).sum() / total,
    })
    bands = pd.DataFrame({
        f"{SNAPSHOT_SITES} sites": cells_access.groupby("band_10")["residents"].sum() / total,
        f"{n_final} sites": cells_access.groupby("band_final")["residents"].sum() / total,
    }).reindex(band_labels()).fillna(0)

    if SELECTION_GPKG.exists():
        SELECTION_GPKG.unlink()
    cells_access.to_file(SELECTION_GPKG, layer="cells_access", driver="GPKG")
    sites_selected.to_file(SELECTION_GPKG, layer="sites_selected", driver="GPKG")
    pyogrio.write_dataframe(curve, SELECTION_GPKG, layer="coverage_curve", driver="GPKG")
    run_summary = pd.DataFrame([
        ("residents", total),
        ("cells", len(cells)),
        ("cells_excluded", n_excluded),
        ("candidates", len(sites)),
        ("ceiling_share", ceiling),
        ("ceiling_avg_walk_min", float(np.average(all_open, weights=residents))),
        ("target_share", target),
        ("n_final", n_final),
        ("target_reached", int(stop_reason == "target reached")),
    ], columns=["item", "value"])
    pyogrio.write_dataframe(run_summary, SELECTION_GPKG, layer="run_summary", driver="GPKG")

    print("\n--- Summary ---")
    print(f"Cells used: {len(cells):,} ({total:,.0f} residents); excluded for snap > "
          f"{SNAP_EXCLUDE_M} m: {n_excluded} cells, {res_excluded} residents")
    print(f"Ceiling (all {len(sites)} candidates open): {ceiling:.1%} within {TARGET_MIN} min, "
          f"average walk {np.average(all_open, weights=residents):.1f} min")
    print(f"Target: {TARGET_SHARE:.0%} of ceiling = {target:.1%} within {TARGET_MIN} min")
    print(f"Stopped at N = {n_final} sites ({stop_reason})")

    show = [SNAPSHOT_SITES] + list(range(20, n_final, 10)) + [n_final]
    view = curve[curve["n_sites"].isin(show)].copy()
    for col in view.columns[2:]:
        view[col] = (view[col] * 100).round(1)
    view["avg_walk_min"] = view["avg_walk_min"].round(1)
    print("\nCoverage curve (shares in %):")
    print(view.to_string(index=False))

    print("\nChosen sites:")
    tbl = sites_selected[["rank", "tier", "name", "chain", "district", "residents_new",
                          "residents_nearest_final"]]
    print(tbl.to_string(index=False))
    print("\nPriority tiers:")
    tier_rows, start = [], 1
    for tier, end in enumerate(tier_ends, start=1):
        share = curve.loc[curve["n_sites"] == end, share_col].iloc[0]
        tier_rows.append({"tier": tier, "ranks": f"{start}-{end}", "sites": end - start + 1,
                          f"within_{TARGET_MIN}min_after_%": round(share * 100, 1),
                          "share_of_ceiling_%": round(share / ceiling * 100, 1)})
        start = end + 1
    print(pd.DataFrame(tier_rows).to_string(index=False))

    print("\nChosen sites by chain:")
    print(sites_selected["chain"].value_counts().to_string())

    print("\nWalk-time distribution (share of residents):")
    print((dist * 100).round(1).to_string())
    print("\nDefault bands (share of residents):")
    print((bands * 100).round(1).to_string())

    print(f"\nWrote {SELECTION_GPKG}")
    print(f"  layer 'cells_access'   {len(cells_access):,} polygons")
    print(f"  layer 'sites_selected' {len(sites_selected)} points")
    print(f"  layer 'coverage_curve' {len(curve)} rows")
    print(f"  layer 'run_summary'    {len(run_summary)} rows")


if __name__ == "__main__":
    main()
