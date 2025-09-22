import os
import geopandas as gpd
import pandas as pd

bldg_directory = "bldg"
bldg_gml_files = [
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

bldg_gdf_list = [gpd.read_file(f"{bldg_directory}{os.path.sep}{file}") for file in bldg_gml_files]
bldg_merged_gdf = pd.concat(bldg_gdf_list, ignore_index=True)


# 2. 计算 WGS84 边界框并格式化为字符串
bounds = bldg_merged_gdf.to_crs(epsg=4326).total_bounds
minx, miny, maxx, maxy = bounds
minx_str = f"{minx:.4f}"
miny_str = f"{miny:.4f}"
maxx_str = f"{maxx:.4f}"
maxy_str = f"{maxy:.4f}"

# 3. 构造文件名并保存为 .pkl 文件
filename = f"bldg_merged_LL_{minx_str}_{miny_str}_UR_{maxx_str}_{maxy_str}.pkl"
save_path = rf"{filename}"
bldg_merged_gdf.to_pickle(save_path)

print(f"已保存至: {save_path}")
