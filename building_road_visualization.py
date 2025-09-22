"""
Building and Road Visualization Program
A simple program to visualize buildings and roads from GML files
"""

import geopandas as gpd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd
import os
import time
import pickle
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

# Configuration
BLDG_DIRECTORY = "bldg"
ROAD_DIRECTORY = "tran"

# Building GML files
BLDG_GML_FILES = [
    r"52350338_bldg_6697_op.gml",
    r"52350328_bldg_6697_op.gml",
    r"52350318_bldg_6697_op.gml",
    r"52350339_bldg_6697_op.gml",
    r"52350329_bldg_6697_op.gml",
    r"52350319_bldg_6697_op.gml",
    r"52350430_bldg_6697_op.gml",
    r"52350420_bldg_6697_op.gml",
    r"52350410_bldg_6697_op.gml"
]

# Road GML files  
ROAD_GML_FILES = [
    r"52350338_tran_6697_op.gml",
    r"52350328_tran_6697_op.gml",
    r"52350318_tran_6697_op.gml",
    r"52350339_tran_6697_op.gml",
    r"52350329_tran_6697_op.gml",
    r"52350319_tran_6697_op.gml",
    r"52350430_tran_6697_op.gml",
    r"52350420_tran_6697_op.gml",
    r"52350410_tran_6697_op.gml"
]

# Cache file paths
BUILDINGS_PKL = "buildings_cache.pkl"
ROADS_PKL = "roads_cache.pkl"

def load_buildings():
    """Load building data from GML files or cache"""
    if os.path.exists(BUILDINGS_PKL):
        print("Loading buildings from cache...")
        with open(BUILDINGS_PKL, 'rb') as f:
            return pickle.load(f)
    
    print("Loading building GML files...")
    start_time = time.time()
    
    building_gdfs = []
    for file in BLDG_GML_FILES:
        file_path = os.path.join(BLDG_DIRECTORY, file)
        if os.path.exists(file_path):
            try:
                # Try different drivers to handle complex geometry types
                drivers = ['GML', 'OGRSQL']
                gdf = None
                
                for driver in drivers:
                    try:
                        gdf = gpd.read_file(file_path, driver=driver)
                        break
                    except Exception:
                        continue
                
                if gdf is None:
                    # Try with GDAL options to handle complex geometries
                    try:
                        gdf = gpd.read_file(file_path, 
                                          engine='pyogrio',
                                          use_arrow=False)
                    except Exception as e:
                        print(f"Failed to load {file}: {e}")
                        continue
                
                if gdf is not None and len(gdf) > 0:
                    # Filter out unsupported geometry types
                    valid_geom_types = ['Polygon', 'MultiPolygon', 'Point', 'LineString', 'MultiLineString']
                    gdf = gdf[gdf.geometry.geom_type.isin(valid_geom_types)]
                    
                    if len(gdf) > 0:
                        building_gdfs.append(gdf)
                        print(f"Loaded: {file} ({len(gdf)} features)")
                    else:
                        print(f"No valid geometries in {file}")
                
            except Exception as e:
                print(f"Failed to load {file}: {e}")
    
    if building_gdfs:
        buildings_gdf = pd.concat(building_gdfs, ignore_index=True)
        
        # Save to cache
        with open(BUILDINGS_PKL, 'wb') as f:
            pickle.dump(buildings_gdf, f)
        
        end_time = time.time()
        print(f"Buildings loaded in {end_time - start_time:.2f} seconds")
        print(f"Total buildings: {len(buildings_gdf)}")
        return buildings_gdf
    else:
        print("No building files found!")
        return None

def load_roads():
    """Load road data from GML files or cache"""
    if os.path.exists(ROADS_PKL):
        print("Loading roads from cache...")
        with open(ROADS_PKL, 'rb') as f:
            return pickle.load(f)
    
    print("Loading road GML files...")
    start_time = time.time()
    
    road_gdfs = []
    for file in ROAD_GML_FILES:
        file_path = os.path.join(ROAD_DIRECTORY, file)
        if os.path.exists(file_path):
            try:
                gdf = gpd.read_file(file_path)
                road_gdfs.append(gdf)
                print(f"Loaded: {file}")
            except Exception as e:
                print(f"Failed to load {file}: {e}")
    
    if road_gdfs:
        roads_gdf = pd.concat(road_gdfs, ignore_index=True)
        
        # Save to cache
        with open(ROADS_PKL, 'wb') as f:
            pickle.dump(roads_gdf, f)
        
        end_time = time.time()
        print(f"Roads loaded in {end_time - start_time:.2f} seconds")
        print(f"Total road features: {len(roads_gdf)}")
        return roads_gdf
    else:
        print("No road files found!")
        return None

def create_visualization(buildings_gdf, roads_gdf):
    """Create the main visualization"""
    print("Creating visualization...")
    
    # Ensure both datasets use the same CRS (EPSG:6669)
    if buildings_gdf is not None:
        if buildings_gdf.crs.to_epsg() != 6669:
            buildings_gdf = buildings_gdf.to_crs(epsg=6669)
    
    if roads_gdf is not None:
        if roads_gdf.crs.to_epsg() != 6669:
            roads_gdf = roads_gdf.to_crs(epsg=6669)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 12))
    
    # Plot roads first (as background)
    if roads_gdf is not None and len(roads_gdf) > 0:
        roads_gdf.plot(ax=ax, color='lightgray', linewidth=1, alpha=0.7, label='Roads')
    
    # Plot buildings on top
    if buildings_gdf is not None and len(buildings_gdf) > 0:
        buildings_gdf.plot(ax=ax, color='lightblue', edgecolor='darkblue', 
                          linewidth=0.5, alpha=0.8, label='Buildings')
    
    # Set plot properties
    ax.set_title('Buildings and Roads Visualization', fontsize=16, fontweight='bold')
    ax.set_xlabel('X Coordinate (m)', fontsize=12)
    ax.set_ylabel('Y Coordinate (m)', fontsize=12)
    
    # Add legend
    legend_elements = [
        Patch(facecolor='lightblue', edgecolor='darkblue', label='Buildings'),
        Patch(facecolor='lightgray', label='Roads')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=12)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Set equal aspect ratio
    ax.set_aspect('equal')
    
    # Add north arrow
    ax.annotate('↑ North', xy=(0.02, 0.98), xycoords='axes fraction',
                fontsize=14, ha='left', va='top', fontweight='bold')
    
    # Adjust layout
    plt.tight_layout()
    
    return fig, ax

def print_data_info(buildings_gdf, roads_gdf):
    """Print information about the loaded data"""
    print("\n" + "="*50)
    print("DATA SUMMARY")
    print("="*50)
    
    if buildings_gdf is not None:
        print(f"Buildings:")
        print(f"  - Total features: {len(buildings_gdf)}")
        print(f"  - CRS: {buildings_gdf.crs}")
        print(f"  - Bounds: {buildings_gdf.total_bounds}")
        if len(buildings_gdf) > 0:
            print(f"  - Columns: {list(buildings_gdf.columns)}")
    else:
        print("Buildings: No data loaded")
    
    if roads_gdf is not None:
        print(f"\nRoads:")
        print(f"  - Total features: {len(roads_gdf)}")
        print(f"  - CRS: {roads_gdf.crs}")
        print(f"  - Bounds: {roads_gdf.total_bounds}")
        if len(roads_gdf) > 0:
            print(f"  - Columns: {list(roads_gdf.columns)}")
    else:
        print("\nRoads: No data loaded")
    
    print("="*50)

def main():
    """Main function"""
    print("Building and Road Visualization Program")
    print("======================================")
    
    # Load data
    buildings_gdf = load_buildings()
    roads_gdf = load_roads()
    
    # Print data information
    print_data_info(buildings_gdf, roads_gdf)
    
    # Check if we have any data to visualize
    if buildings_gdf is None and roads_gdf is None:
        print("No data to visualize! Please check your data files.")
        return
    
    # Create visualization
    fig, ax = create_visualization(buildings_gdf, roads_gdf)
    
    print("\nVisualization created successfully!")
    print("Saving plot as 'building_road_visualization.png'...")
    
    # Save the plot instead of showing it
    plt.savefig('building_road_visualization.png', dpi=300, bbox_inches='tight')
    print("Plot saved successfully!")
    print("You can view the image file: building_road_visualization.png")

if __name__ == "__main__":
    main()