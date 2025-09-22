import os
import pickle
import time
from datetime import datetime, timezone, timedelta

import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.ops import unary_union

from rich.progress import Progress

# If you need projection or Transformer:
from pyproj import Transformer

def precompute_shadow_ratios():
    """
    Batch compute the shadow coverage ratio for each (edge, time slice):
    shadow_ratio = shadow_length / total_edge_length
    Save the results to a .pkl file for fast loading in the main program,
    avoiding real-time intersection calculations.
    """

    # --------------------- (1) Load building & shadow data ---------------------
    print("Loading building and shadow data...")
    # Example: load the merged building GeoDataFrame
    bldg_pkl = r"bldg_merged_LL_135.4748_34.6749_UR_135.5129_34.7026.pkl"
    # Load the shadow {time: geometry} dictionary
    # For example, the 1-minute interval .pkl file
    shadow_file = r"shadows_20250924_1400_1700_1min_LL_135.4748_34.6749_UR_135.5129_34.7026.pkl"
    with open(bldg_pkl,'rb') as f:
        building_gdf = pickle.load(f)

    # Ensure projection is EPSG:6669
    if building_gdf.crs.to_epsg() != 6669:
        building_gdf = building_gdf.to_crs(epsg=6669)

    with open(shadow_file, 'rb') as f:
        time_to_union = pickle.load(f)
    # time_to_union: dict[datetime -> MultiPolygon/Polygon/... or None]

    # --------------------- (2) Load or get OSM graph & convert to EPSG:6669 ---------------------
    print("Loading OSM graph...")
    # Build bounding box
    building_gdf_wgs84 = building_gdf.to_crs(epsg=4326)
    minx, miny, maxx, maxy = building_gdf_wgs84.total_bounds
    # OSMnx requires (north, south, east, west)
    north, south, east, west = maxy, miny, maxx, minx

    # Use local cached OSM pkl if available, otherwise download
    map_id = f"{north}_{south}_{east}_{west}"
    osm_file = f"osmnx_graph_{map_id}.pkl"
    if os.path.exists(osm_file):
        with open(osm_file,"rb") as f:
            G = pickle.load(f)
    else:
        G = ox.graph_from_bbox(north=north, south=south, east=east, west=west, network_type="bike")
        with open(osm_file,"wb") as f:
            pickle.dump(G,f)

    # Extract edges
    gdf_edges = ox.graph_to_gdfs(G, nodes=False)
    # If original is 4326, convert to 6669
    if gdf_edges.crs.to_epsg() != 4326:
        gdf_edges = gdf_edges.to_crs(epsg=4326)
    gdf_edges = gdf_edges.to_crs(epsg=6669)

    # --------------------- (3) Batch intersection calculation ---------------------
    print("Batch computing shadow coverage ratio for each edge and time slice...")

    # Store results in a dict or DataFrame
    # Here we use dict: precomputed[(u,v,k, t)] = ratio
    precomputed = {}

    # Sort times to ensure processing order
    sorted_times = sorted(time_to_union.keys())

    total_edges = len(gdf_edges)
    start_time_all = time.time()
    count_inter = 0

    with Progress() as p:
        task = p.add_task("Processing edges ...", total=len(gdf_edges.index))
        p.update(task, advance=0)

        for i, (u,v,k) in enumerate(gdf_edges.index):
            edge_geom = gdf_edges.loc[(u,v,k),'geometry']
            edge_len = edge_geom.length

            # Process each time slice
            for t in sorted_times:
                shadow_poly = time_to_union[t]
                if shadow_poly is None or shadow_poly.is_empty:
                    ratio = 0.0
                else:
                    # Perform intersection
                    count_inter += 1
                    inters = edge_geom.intersection(shadow_poly)
                    shadow_len = inters.length if (not inters.is_empty) else 0.0
                    ratio = shadow_len / edge_len if edge_len > 0 else 0.0

                precomputed[(u,v,k,t)] = ratio

            update_period = 100
            if (i+1) % update_period == 0:
                #print(f"Processed {i+1}/{total_edges} edges...")
                p.update(task, advance=update_period)

    end_time_all = time.time()
    print("========== Offline batch computation complete ==========")
    print(f"Processed {total_edges} edges × {len(sorted_times)} time slices -> {count_inter} intersection() calls")
    print(f"Total elapsed time: {end_time_all - start_time_all:.2f} seconds")

    # --------------------- (4) Save to pkl ---------------------
    # Extract time and bounding box info from shadow_file name (assuming consistent naming)
    shadow_filename = os.path.basename(shadow_file).replace("shadows_", "").replace(".pkl", "")
    # Compose output file name
    out_file = f"edge_shadow_ratios_{shadow_filename}.pkl"
    with open(out_file, "wb") as f:
        pickle.dump(precomputed, f)

    print(f"Results saved to {out_file}, ready for direct use in the main program!")


if __name__ == '__main__':
    precompute_shadow_ratios()
