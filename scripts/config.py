# scripts/config.py
"""
Shared constants for the Parcel Locker Network analysis.

Paths, coordinate systems, study area, candidate chain patterns and every
threshold used by more than one script. Values used by only one script stay at
the top of that script. Scripts are run from the project root, so all paths are
relative to it.
"""

from pathlib import Path

# --- Paths -----------------------------------------------------------------

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
OUTPUTS_DIR = Path("outputs")
GIS_DIR = OUTPUTS_DIR / "gis"

GRID_GPKG = PROCESSED_DIR / "grid.gpkg"
SITES_GPKG = PROCESSED_DIR / "sites.gpkg"
SNAPS_GPKG = PROCESSED_DIR / "snaps.gpkg"
SELECTION_GPKG = PROCESSED_DIR / "selection.gpkg"
WALK_GRAPH = RAW_DIR / "walk_network.graphml"

OUT_XLSX = OUTPUTS_DIR / "parcel_locker_analysis.xlsx"
OUT_GIS_GPKG = GIS_DIR / "parcelnetwork.gpkg"

# --- Coordinate reference systems -------------------------------------------

TARGET_CRS = "EPSG:3067"   # ETRS-TM35FIN, metres. Everything is stored in this.
HSY_CRS = "EPSG:3879"      # ETRS-GK25, as published by HSY
WGS84 = "EPSG:4326"        # OSM and Overpass

# --- Study area and population ----------------------------------------------

GRID_YEAR = 2025
MUNICIPALITIES = ["Espoo", "Kauniainen"]

# --- Candidate sites --------------------------------------------------------

# Case-insensitive regular expressions, matched against brand, name and operator.
# Limited to the location types Budbee currently hosts its lockers in.
CHAIN_PATTERNS = {
    "S Group": [r"\bprisma\b", r"\bs-market\b", r"\bsale\b", r"\balepa\b",
                r"\bfood market herkku\b"],
    "K Group": [r"\bk-citymarket\b", r"\bk-supermarket\b", r"\bk-market\b",
                r"\bk-extra\b"],
    "Lidl": [r"\blidl\b"],
    "R-kioski": [r"\br-kioski\b"],
}
MALL_CHAIN = "Shopping centre"   # any shop=mall

SITE_MERGE_M = 50       # candidates closer than this are merged into one site

# --- Walking network and snapping -------------------------------------------

SNAP_FLAG_M = 200       # cells snapped further than this are flagged
SNAP_EXCLUDE_M = None   # set in Step 3 from the snap-distance distribution

# --- Walking time and site selection ----------------------------------------

WALK_SPEED_M_PER_MIN = 80   # 4.8 km/h
WALK_CAP_MIN = 30           # longer walks count as 30 in the objective
TARGET_MIN = 10
TARGET_SHARE = 0.90         # stop when this share of residents is within TARGET_MIN
SNAPSHOT_SITES = 10         # Map 2 snapshot
MAX_SITES = 60

# Walking-time band edges in minutes: under 5, 5-10, 10-15, 15-20, over 20.
# Maps 2 and 3 use identical bands.
BAND_EDGES_MIN = [5, 10, 15, 20]
