"""
demo_data.py — Generate realistic sample grid data for Seoul
=============================================================
Creates a GeoDataFrame of ~700 1km grid cells covering Seoul,
with simulated noise, population, and EBD values.

Replace with your real data by placing seoul_grid_1km.geojson
in the data/ directory.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box

from ebd import calc_rr, calc_paf, classify_risk, DISABILITY_WEIGHT

# Cluster definitions
CLUSTER_INFO = {
    0: {"name": "High-rise mixed-use",               "name_ko": "고층 복합용도",      "noise": "Motorcycle traffic"},
    1: {"name": "Rail & traffic-heavy residential",   "name_ko": "철도·교통 밀집 주거", "noise": "Railway, road traffic"},
    2: {"name": "Green & low-noise residential",      "name_ko": "녹지·저소음 주거",   "noise": "Low-level mixed"},
    3: {"name": "High-density with construction",     "name_ko": "고밀도 건설지역",    "noise": "Construction equipment"},
    4: {"name": "Public urban core",                  "name_ko": "도심 공공지역",      "noise": "Signal (siren), road"},
}


def generate_demo_grid(seed: int = 42) -> gpd.GeoDataFrame:
    """Generate a demo GeoDataFrame of Seoul grid cells."""
    rng = np.random.default_rng(seed)

    # Seoul approximate bounds
    lat_min, lat_max = 37.44, 37.69
    lng_min, lng_max = 126.78, 127.17
    step = 0.009  # ~1km at Seoul's latitude

    center_lat = (lat_min + lat_max) / 2
    center_lng = (lng_min + lng_max) / 2

    rows = []
    gid = 0

    for lat in np.arange(lat_min, lat_max, step):
        for lng in np.arange(lng_min, lng_max, step):
            # Rough circular mask for Seoul
            dist = np.sqrt(((lat - center_lat) * 111) ** 2 +
                           ((lng - center_lng) * 88) ** 2)
            if dist > 16:
                continue

            # Simulate values with spatial gradients
            dist_norm = dist / 16  # 0 = center, 1 = edge

            lden = rng.normal(65 - dist_norm * 10, 5)
            lden = np.clip(lden, 40, 85)

            pop = int(rng.normal(15000 - dist_norm * 8000, 4000))
            pop = max(500, pop)

            elderly_ratio = rng.uniform(0.08, 0.28)
            elderly = int(pop * elderly_ratio)

            # EBD: higher in center (more pop, more noise)
            mortality = rng.normal(28.5, 5)
            prevalence = rng.normal(420, 80)
            rem_life = rng.normal(15.2, 2)

            rr = calc_rr(lden)
            paf = calc_paf(rr)
            deaths = pop * (max(mortality, 5) / 100_000)
            ylls = deaths * max(rem_life, 5)
            ylds = pop * (max(prevalence, 50) / 100_000) * DISABILITY_WEIGHT
            dalys = ylls + ylds
            ebd = paf * dalys

            cluster_id = rng.integers(0, 5)
            ci = CLUSTER_INFO[cluster_id]
            risk = classify_risk(elderly, ebd)

            geom = box(lng, lat, lng + step, lat + step)

            rows.append({
                "grid_id": f"G{gid:04d}",
                "geometry": geom,
                "Lden": round(lden, 1),
                "EBD": round(ebd, 1),
                "risk_level": risk,
                "cluster_id": cluster_id,
                "cluster_name": ci["name"],
                "cluster_name_ko": ci["name_ko"],
                "population": pop,
                "elderly_pop": elderly,
                "dominant_noise": ci["noise"],
            })
            gid += 1

    gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    return gdf


def load_grid_data(path: str = "data/seoul_grid_1km.geojson") -> gpd.GeoDataFrame:
    """
    Load real GeoJSON if available, otherwise generate demo data.
    """
    try:
        gdf = gpd.read_file(path)
        if len(gdf) > 0:
            return gdf
    except Exception:
        pass

    return generate_demo_grid()
