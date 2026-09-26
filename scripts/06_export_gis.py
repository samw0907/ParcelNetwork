# scripts/06_export_gis.py
"""
Step 6: Export GIS layers.

Collects the analysis outputs into a single GeoPackage, outputs/gis/parcelnetwork.gpkg,
for manual cartography in QGIS. Every layer is written in EPSG:3067 (ETRS-TM35FIN).
This script does no styling; the maps are made by hand.

Layers:
  cells           populated 250 m cells with residents and walk-time attributes at
                  10 sites (min_10, band_10, site_10) and at the final N (min_final,
                  band_final, site_final). Maps 1-3.
  candidates      all candidate sites with chain, plus chosen rank and tier (blank if
                  not chosen). Map 1.
  sites_selected  chosen sites with rank and priority tier. Maps 2-3.
  study_area      Espoo + Kauniainen
  districts       seven Espoo major districts plus Kauniainen
  rail_metro      rail and metro lines (context)
  stations        rail and metro stations (labels only)
  sea             sea area (basemap)
"""

import geopandas as gpd

from config import GRID_GPKG, OUT_GIS_GPKG, SELECTION_GPKG, SITES_GPKG, TARGET_CRS

# output layer name -> (source GeoPackage, source layer)
LAYERS = {
    "cells": (SELECTION_GPKG, "cells_access"),
    "candidates": (SITES_GPKG, "candidates"),
    "sites_selected": (SELECTION_GPKG, "sites_selected"),
    "study_area": (GRID_GPKG, "study_area"),
    "districts": (GRID_GPKG, "districts"),
    "rail_metro": (GRID_GPKG, "rail_metro"),
    "stations": (GRID_GPKG, "stations"),
    "sea": (GRID_GPKG, "sea"),
}


def main():
    OUT_GIS_GPKG.parent.mkdir(parents=True, exist_ok=True)
    if OUT_GIS_GPKG.exists():
        OUT_GIS_GPKG.unlink()

    chosen = gpd.read_file(SELECTION_GPKG, layer="sites_selected")[["site_id", "rank", "tier"]]

    print(f"Writing {OUT_GIS_GPKG}")
    counts = {}
    for out_layer, (src_path, src_layer) in LAYERS.items():
        gdf = gpd.read_file(src_path, layer=src_layer)
        if gdf.crs is None:
            raise SystemExit(f"{src_path.name}:{src_layer} has no CRS; cannot export")
        if out_layer == "candidates":
            gdf = gdf.merge(chosen, on="site_id", how="left")
            gdf[["rank", "tier"]] = gdf[["rank", "tier"]].astype("Int64")
        gdf = gdf.to_crs(TARGET_CRS)
        gdf.to_file(OUT_GIS_GPKG, layer=out_layer, driver="GPKG")
        counts[out_layer] = (len(gdf), ", ".join(sorted(gdf.geom_type.unique())))

    print("\n--- Summary ---")
    for layer, (n, geom_types) in counts.items():
        print(f"  {layer:<15} {n:>5,} features  {geom_types}")
    print(f"\nAll layers written in {TARGET_CRS}")


if __name__ == "__main__":
    main()
