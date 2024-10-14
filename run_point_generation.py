# -*- coding: utf-8 -*-
"""
"""

import os
import glob
from tqdm import tqdm
import geopandas as gpd
import pandas as pd
import rasterio


"""# Set root directory
"""
generate_points_dir = "your path" + os.sep + "06_Generate_points"
os.makedirs(generate_points_dir, exist_ok=True)



"""#Create road 2.5m buffer poly
"""
road_line = "your road line shp"
gdf_road = gpd.read_file(road_line)
gdf_buff = gdf_road.buffer(2.5)
road_buff_path = os.path.dirname(road_line) + os.sep + "road_buff25.shp"
gdf_buff.to_file(road_buff_path)


"""#Generating Points
"""
#1min
os.chdir('set path to ReplantingBlueprint')
from _04_Point_generation import _01_generate_points_slope_adjust_6ft

pagenum = #1
line_shps = glob.glob(rf"{your path + os.sep + 05_Pairing_terraces + os.sep + 03_direction +os.sep + extent{pagenum}"+os.sep+"*.shp")
out_dir = generate_points_dir + os.sep + "01_allpoints" + os.sep + f"extent{pagenum}"
os.makedirs(out_dir, exist_ok=True)

for shp in tqdm(line_shps):
    print(shp)
    _01_generate_points_slope_adjust_6ft.main(shp, road_buff_path, out_dir)
    

"""# merge all points,
   # delete points within 6ft from Road
   # eliminate close points
 """
# 15-25 min
os.chdir('set path to ReplantingBlueprint')
from _04_Point_generation import _02_mege_and_eliminate_points

pagenum = 2
out_dir = generate_points_dir + os.sep + "01_allpoints" + os.sep + f"extent{pagenum}"
in_dir = out_dir
close_thre = 5

_02_mege_and_eliminate_points.main(in_dir, road_buff_path, close_thre)


"""# extract points for target area
# out_dir is same as input points
"""
# few second
target_area = "path to target area polygon"

point_shp = in_dir + os.sep + "merge"+ os.sep + "merge_all_points_6ftfin.shp"

gdf_area = gpd.read_file(target_area)
gdf_point = gpd.read_file(point_shp)

points_within_polygon = gpd.sjoin(gdf_point, gdf_area, how='inner', op='within')

out_dir = os.path.dirname(point_shp)
filename = os.path.basename(point_shp)[:-4]+"_target.shp"
outfile = out_dir + os.sep + filename
points_within_polygon.to_file(outfile)




print("All process done")


