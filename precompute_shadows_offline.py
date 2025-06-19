import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.ops import unary_union
from shapely.geometry import LineString
from astral import LocationInfo
from astral.sun import elevation, azimuth
from datetime import datetime, timedelta, timezone
import pickle

import os

interval_minutes = 1
start_dt = datetime(2024, 12, 5, 9, tzinfo=timezone(timedelta(hours=9)))
end_dt = datetime(2024, 12, 5, 10, tzinfo=timezone(timedelta(hours=9)))

#######################################
# Function 1: Compute merged shadow for a single time point
#######################################
def compute_shadow_union_at_time(building_gdf, date_time, height_column='default_height'):
    city = LocationInfo(
        name="Osaka",
        region="Japan",
        timezone="Asia/Tokyo",
        latitude=34.6937,
        longitude=135.5023
    )
    solar_elev = elevation(city.observer, date_time)
    solar_azi = azimuth(city.observer, date_time)

    if solar_elev <= 0:
        return None  # No sunlight

    sun_vec = np.array([
        np.cos(np.radians(solar_elev)) * np.sin(np.radians(solar_azi)),
        np.cos(np.radians(solar_elev)) * np.cos(np.radians(solar_azi)),
        np.sin(np.radians(solar_elev))
    ])

    def shadow_for_building(geom, h):
        polygons = geom.geoms if geom.geom_type == 'MultiPolygon' else [geom]
        shadow_lines = []
        for poly in polygons:
            # Only use xy, ignore z
            base_coords = [(x, y) for x, y, *rest in poly.exterior.coords]

            shadow_coords = [
                (
                    x - h / np.tan(np.radians(solar_elev)) * sun_vec[0],
                    y - h / np.tan(np.radians(solar_elev)) * sun_vec[1]
                )
                for (x, y) in base_coords
            ]

            for base, shadow in zip(base_coords, shadow_coords):
                shadow_lines.append(LineString([base, shadow]))
        union_lines = unary_union(shadow_lines)
        return union_lines.convex_hull

    building_gdf['shadow_temp'] = building_gdf.apply(
        lambda row: shadow_for_building(row.geometry, row[height_column]),
        axis=1
    )

    shadow_gdf = building_gdf.dropna(subset=['shadow_temp']).set_geometry('shadow_temp')

    if shadow_gdf.empty:
        return None
    return unary_union(shadow_gdf.geometry)


#######################################
# Function 2: Batch compute shadows for all time slices
#######################################
def precompute_shadow_unions(building_gdf, start_dt, end_dt, interval_minutes, height_column='default_height'):
    current_time = start_dt
    time_to_union = {}
    while current_time <= end_dt:
        print(f"Computing: {current_time}...")
        union_geom = compute_shadow_union_at_time(building_gdf, current_time, height_column)
        time_to_union[current_time] = union_geom
        current_time += timedelta(minutes=interval_minutes)
    return time_to_union


#######################################
# Read GML building data
#######################################
bldg_directory = "bldg"
bldg_gml_files = [
    r"51357451_bldg_6697_op.gml",
    r"51357452_bldg_6697_op.gml",
    r"51357453_bldg_6697_op.gml",
    r"51357461_bldg_6697_op.gml",
    r"51357462_bldg_6697_op.gml",
    r"51357463_bldg_6697_op.gml",
    r"51357471_bldg_6697_op.gml",
    r"51357472_bldg_6697_op.gml",
    r"51357473_bldg_6697_op.gml"
]

bldg_gdf_list = [gpd.read_file(f"{bldg_directory}{os.path.sep}{file}") for file in bldg_gml_files]
bldg_merged_gdf = pd.concat(bldg_gdf_list, ignore_index=True)

if bldg_merged_gdf.crs.to_epsg() != 6669:
    bldg_merged_gdf = bldg_merged_gdf.to_crs(epsg=6669)

# Determine the height column, or use default if not found
height_column = None
for col in bldg_merged_gdf.columns:
    if 'height' in col.lower():
        height_column = col
        break
if height_column is None:
    height_column = 'default_height'
    bldg_merged_gdf[height_column] = 3.0
else:
    bldg_merged_gdf[height_column] = bldg_merged_gdf[height_column].fillna(3)

#######################################
# Set time range for shadow calculation
#######################################


#######################################
# Start batch computation and save results
#######################################

print(f"[INFO] Shadow calculation range: {start_dt} ~ {end_dt}, interval: {interval_minutes} minutes")
time_to_union = precompute_shadow_unions(bldg_merged_gdf, start_dt, end_dt, interval_minutes, height_column)

valid_count = sum(1 for v in time_to_union.values() if v)
print(f"[INFO] Shadow calculation complete, valid time slices: {valid_count}")

#######################################
# Save results
#######################################
# Automatically generate output file name
# Get bounding box coordinates (in degrees)
bounds = bldg_merged_gdf.to_crs(epsg=4326).total_bounds  # Convert to WGS84 lat/lon
minx, miny, maxx, maxy = bounds  # Lower left (minx, miny), upper right (maxx, maxy)

# Keep 4 decimal places
minx_str = f"{minx:.4f}"
miny_str = f"{miny:.4f}"
maxx_str = f"{maxx:.4f}"
maxy_str = f"{maxy:.4f}"

# Compose output file name
date_str = start_dt.strftime("%Y%m%d")
start_str = start_dt.strftime("%H%M")
end_str = end_dt.strftime("%H%M")
output_file = (
    f"shadows_{date_str}_{start_str}_{end_str}_{interval_minutes}min_"
    f"LL_{minx_str}_{miny_str}_UR_{maxx_str}_{maxy_str}.pkl"
)

# Save to file
with open(output_file, 'wb') as f:
    pickle.dump(time_to_union, f)

print(f"[SUCCESS] Shadow cache saved to {output_file}")

