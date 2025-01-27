# -*- coding: utf-8 -*-

import os
import glob
from tqdm import tqdm
import geopandas as gpd
import pandas as pd
from pathlib import Path


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
 
thre_str = str(thre).replace(".","")
outdilationmame = Path(img_path).stem + f"_{thre_str}_e{size_erosion}_d{size_dilation}.tif"

"""# Extract line by skelton and dilation
"""
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _00_skelton

image_path =  terrace_detection_dir + os.sep + "00_preparation" + os.sep + outdilationmame
clip_shp = "path to clipping shp"
out_dir = terrace_detection_dir + os.sep + "00_preparation"
out_skelton_dir = out_dir + os.sep + "_skelton"
os.makedirs(out_skelton_dir, exist_ok=True)
#run
_00_skelton.main(image_path, clip_shp, out_skelton_dir)



"""#Vectorize for center lines using arcpy
"""
# 1 min
out_dir = terrace_detection_dir + os.sep + "01_centerlines"
os.makedirs(out_dir, exist_ok=True)

# -----------------------------------------------------------------------------------
### !!! Please directly go to and RUN _01_vectorize_centerlines.py ### 
# -----------------------------------------------------------------------------------
### !!! Please set arcpy path, pypath, gdb path in _01_vectorize_centerlines.py ### 
# -----------------------------------------------------------------------------------


"""#Error removal """
"""
# remove lines intersecing over 45 degree
"""
# 10-15 min
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _02_filtering_by_intersects

line_shp_path = terrace_detection_dir + os.sep + "01_centerlines" + os.sep + "centerlines_back.shp"
out_dir = terrace_detection_dir + os.sep + "02_filterd_line"
os.makedirs(out_dir, exist_ok=True)
minlen = 8 #shorter than this removed

_02_filtering_by_intersects.main(line_shp_path, out_dir, minlen)



"""# *Remove lines within roads
"""
#10 sec
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _06_erase_by_roads

in_dir = out_dir
out_dir_d2 = terrace_detection_dir + os.sep + "03_filt_divided_road" + os.sep + "1_filtered_road"
os.makedirs(out_dir_d2, exist_ok=True)
road_line = "set your road line shp"

_06_erase_by_roads.main(in_dir, out_dir_d2, road_line)



"""#Divide lines for faster processing #divide by roads
"""
#10 sec
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _99_devide_line_roads

line_shp = glob.glob(os.path.join(out_dir_d2,"*.shp"))[0]
out_dir_d3 = terrace_detection_dir + os.sep + "03_filt_divided_road" + os.sep + "2_divided_road"
os.makedirs(out_dir_d3, exist_ok=True)
road_poly_shp = "set area polygon divided by roads" #polygon

_99_devide_line_roads.main(line_shp, out_dir_d3, road_poly_shp)



"""#3 intersecting and cut shortest line by 8 m
"""
# 10min
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _03_cut_intersects

line_dir = terrace_detection_dir + os.sep + "03_filt_divided_road" + os.sep + "2_divided_road"
# line_dir = out_dir_d3
out_dir_d4 = terrace_detection_dir + os.sep + "03_cut_by_intersect"
os.makedirs(out_dir_d4, exist_ok=True)

line_shps = glob.glob(line_dir +os.sep + "*shp")
for shp in tqdm(line_shps):
    _03_cut_intersects.main(shp, out_dir_d4)


"""#2 intersecting and cut shortest line by 8 m
"""
# 1min
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _04_cut_intersects_2lines
    
out_dir_d4 = terrace_detection_dir + os.sep + "03_cut_by_intersect"
line_dir = out_dir_d4
out_dir_d5 = terrace_detection_dir + os.sep + "04_cut_by_intersect_2lines"
os.makedirs(out_dir_d5, exist_ok=True)

line_shps = glob.glob(line_dir +os.sep + "*shp")
for shp in tqdm(line_shps):
    _04_cut_intersects_2lines.main(shp, out_dir_d5)
    
    
"""#merge #for check
"""
# 1min
out_dir_d5 = terrace_detection_dir + os.sep + "04_cut_by_intersect_2lines"
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
# 15-20 min
os.chdir('set path to ReplantingBlueprint')
from _02_TerraceDetection import _05_connect_nearlines

out_dir_d5 = terrace_detection_dir + os.sep + "04_cut_by_intersect_2lines"
line_dir = out_dir_d5
out_dir_d6 = terrace_detection_dir + os.sep + "05_connect_lines"
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
out_dir_d6 = terrace_detection_dir + os.sep + "05_connect_lines"
#Line list before processing
line_shps = glob.glob(out_dir_d6 + os.sep + "*.shp")
out_dir_d7 = terrace_detection_dir + os.sep + "06_cut_by_intersect" + os.sep + "1_3cut"
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
