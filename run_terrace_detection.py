# -*- coding: utf-8 -*-

import os
import glob
from tqdm import tqdm
import geopandas as gpd
import pandas as pd


"""###### Detecting terraces ######"""
### Afrer detecting terraces by deep learning ###

"""# Set root directory
"""
terrace_detection_dir = "your path" + os.sep + "04_Terrace_detection"
os.makedirs(terrace_detection_dir, exist_ok=True)

"""# dilation and erosion for smoothing
"""
### binary image is assigned with values of 10 and 0
# 30 sec
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _00_dilation_swin

img_path = "path to output image of deep learning" 
out_dir = terrace_detection_dir + os.sep + "00_preparation"
os.makedirs(out_dir, exist_ok=True)
size_erosion = 2
size_dilation = 2
thre = 0.025 #threhold for swin output
#run
_00_dilation_swin.main(img_path, out_dir, size_erosion, size_dilation, thre)


"""# Extract line by skelton and dilation
"""
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _00_skelton

image_path =  terrace_detection_dir + os.sep + "00_preparation" + os.sep + "out_extent3_binary_e2_d2.tif"
clip_shp = "path to clipping shp"
out_dir = terrace_detection_dir + os.sep + "00_preparation"
out_skelton_dir = out_dir + os.sep + "_skelton"
os.makedirs(out_skelton_dir, exist_ok=True)
#run
_00_skelton.main(image_path, clip_shp, out_skelton_dir)



"""#Vectorize for center lines using arcpy
"""
# 1 min
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _01_vectorize_centerlines

image_path = out_skelton_dir + os.sep + "*_skelton.tif" #file name of skeltonized img
clip_shp = "path to clipping shp"
out_dir = terrace_detection_dir + os.sep + "01_centerlines" + os.sep + "extent3"
os.makedirs(out_dir, exist_ok=True)

# -----------------------------------------------------------------------------------
### !!! Please set arcpy path, pypath, gdb path in _01_vectorize_centerlines.py ### 
# -----------------------------------------------------------------------------------
##run
_01_vectorize_centerlines.main(image_path, clip_shp, out_dir,clip_bool=True)



"""#Error removal """
"""
# remove lines intersecing over 45 degree
"""
# 10-15 min
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _02_filtering_by_intersects

pagenum = #1 #If you divide target areas into blocks
line_shp_path = terrace_detection_dir + os.sep + "01_centerlines" + os.sep + f"extent{pagenum}" + os.sep + "centerlines_back.shp"
out_dir = terrace_detection_dir + os.sep + "02_filterd_line" + os.sep + f"extent{pagenum}"
os.makedirs(out_dir, exist_ok=True)
minlen = 8

_02_filtering_by_intersects.main(line_shp_path, out_dir, minlen)



"""# *Remove lines within roads
"""
#10 sec
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _06_erase_by_roads

pagenum = #1
in_dir = out_dir
out_dir_d2 = terrace_detection_dir + os.sep + "03_filt_divided_road" + os.sep + "1_filtered_road" + os.sep + f"extent{pagenum}"
os.makedirs(out_dir_d2, exist_ok=True)
road_line = "set your road line shp"

_06_erase_by_roads.main(in_dir, out_dir_d2, road_line)



"""#Divide lines for faster processing #divide by roads
"""
#10 sec
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _99_devide_line_roads

pagenum = #1
line_shp = glob.glob(os.path.join(out_dir_d2,"*.shp"))[0]
out_dir_d3 = terrace_detection_dir + os.sep + "03_filt_divided_road" + os.sep + "2_divided_road" + os.sep + f"extent{pagenum}"
os.makedirs(out_dir_d3, exist_ok=True)
road_poly_shp = "set area polygon divided by roads" #polygon

_99_devide_line_roads.main(line_shp, out_dir_d3, road_poly_shp)



"""#Cut 3 intersecting and shorted line by 8 m
"""
# 5min -> 10~20min
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _03_cut_intersects

pagenum = #1
line_dir = terrace_detection_dir + os.sep + "03_filt_divided_road" + os.sep + "2_divided_road" + os.sep + f"extent{pagenum}"
# line_dir = out_dir_d3
out_dir_d4 = terrace_detection_dir + os.sep + "03_cut_by_intersect" + os.sep + f"extent{pagenum}"
os.makedirs(out_dir_d4, exist_ok=True)

line_shps = glob.glob(line_dir +os.sep + "*shp")
for shp in tqdm(line_shps):
    _03_cut_intersects.main(shp, out_dir_d4)


"""#Cut 2 intersecting and shorted line by 8 m
"""
# 1min
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _04_cut_intersects_2lines
    
pagenum = #1
out_dir_d4 = terrace_detection_dir + os.sep + "03_cut_by_intersect" + os.sep + f"extent{pagenum}"
line_dir = out_dir_d4
out_dir_d5 = terrace_detection_dir + os.sep + "04_cut_by_intersect_2lines" + os.sep + f"extent{pagenum}"
os.makedirs(out_dir_d5, exist_ok=True)

line_shps = glob.glob(line_dir +os.sep + "*shp")
for shp in tqdm(line_shps):
    _04_cut_intersects_2lines.main(shp, out_dir_d5)
    
    
"""#merge #for check
"""
# 1min
pagenum = 1
out_dir_d5 = terrace_detection_dir + os.sep + "04_cut_by_intersect_2lines" + os.sep + f"extent{pagenum}"
line_dir = out_dir_d5
out_dir_d5_ = line_dir + os.sep +"merge"
os.makedirs(out_dir_d5_,exist_ok=True)

line_shps = glob.glob(line_dir +os.sep + "*shp")
gdfs = [gpd.read_file(shp) for shp in line_shps]
merged_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)
out_mergefile = out_dir_d5_ + os.sep + "centerlines_45_cut_cut2ls_merge.shp"
merged_gdf.to_file(out_mergefile, encoding='utf-8')




"""#Connect lines within 5m and angle 135<225 by Least square searching
"""
#7min -> 15-20 min
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _05_connect_nearlines

pagenum = #1
out_dir_d5 = terrace_detection_dir + os.sep + "04_cut_by_intersect_2lines" + os.sep + f"extent{pagenum}"
line_dir = out_dir_d5
out_dir_d6 = terrace_detection_dir + os.sep + "05_connect_lines" + os.sep + f"extent{pagenum}"
os.makedirs(out_dir_d6, exist_ok=True)

line_shps = glob.glob(line_dir + os.sep + '*shp')

for shp in tqdm(line_shps):
    _05_connect_nearlines.main(shp, out_dir_d6)


"""#Cut the shorted lines by 1m if 3 lines intersect
"""
# 1.5 min -> 25-50 min
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _07_cut_intersects_pairing

pagenum = 1
out_dir_d6 = terrace_detection_dir + os.sep + "05_connect_lines" + os.sep + f"extent{pagenum}"
#Line list before processing
line_shps = glob.glob(out_dir_d6 + os.sep + "*.shp")
out_dir_d7 = terrace_detection_dir + os.sep + "06_cut_by_intersect" + os.sep + "1_3cut" + os.sep + f"extent{pagenum}"
os.makedirs(out_dir_d7, exist_ok=True)

for shp in tqdm(line_shps):
    _07_cut_intersects_pairing.main(shp, out_dir_d7)
    
    
"""#Cut the shortest lines by 1m if 2 lines intersect
"""
#1min
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _08_cut_intersects_2lines_pairing

pagenum =1
out_dir_d7 = terrace_detection_dir + os.sep + "06_cut_by_intersect" + os.sep + "1_3cut" + os.sep + f"extent{pagenum}"
line_shps = glob.glob(out_dir_d7 + os.sep + "*.shp")
out_dir_d10 = terrace_detection_dir + os.sep + "06_cut_by_intersect" + os.sep +"2_2cut" + os.sep + f"extent{pagenum}"
os.makedirs(out_dir_d10, exist_ok=True)

for shp in line_shps:
  _08_cut_intersects_2lines_pairing.main(shp, out_dir_d10)

"""#merge #for check"""
# 1min
line_dir = out_dir_d10
out_dir_d10_ = line_dir + os.sep +"check_merge"
os.makedirs(out_dir_d10_,exist_ok=True)

line_shps = glob.glob(line_dir +os.sep + "*shp")
gdfs = [gpd.read_file(shp) for shp in line_shps]
merged_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)
out_mergefile = out_dir_d10_ + os.sep + "merge_connect_cut_cut2.shp"
merged_gdf.to_file(out_mergefile, encoding='utf-8')
