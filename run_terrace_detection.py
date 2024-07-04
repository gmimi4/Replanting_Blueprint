# -*- coding: utf-8 -*-

import os
import glob
from tqdm import tqdm
import geopandas as gpd
import pandas as pd


"""###### Detecting terraces ######"""
"""#U-Net
"""
# use Google Colab

"""# dilation and erosion for smoothing
"""
# 30 sec
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _00_dilation

img_path = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\2_prediction\OUT\mosaic.tif" #this is mosaic tif of UNet output
out_dir = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\3_dilation\_Test"
## set epsg code in the py file

#run
_00_dilation.main(img_path, out_dir)


"""#Vectorize for center lines using arcpy
"""
# 1 min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _01_vectorize_centerlines

image_path = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\3_dilation\mosaic_e5_d2_clip.tif"
out_dir = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\4_centerlines"

##run
_01_vectorize_centerlines.main(image_path, out_dir)



"""#Error removal #"""
"""
# remove lines intersecing over 45 degree
"""
# 10-15 min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _02_filtering_by_intersects

line_shp_path = out_dir + os.sep + "centerlines.shp"
out_dir = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\9_filterd_line"

_02_filtering_by_intersects.main(line_shp_path, out_dir)


"""#Divide lines for faster processing
"""
#3min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _99_devide_lines

# out_dir = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\9_filterd_line"
line_dir = out_dir
out_dir = line_dir + os.sep + '_divided'

_99_devide_lines.main(line_dir, out_dir)


"""#Cut 3 intersecting and shorted line by 8 m
"""
# 0.5min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _03_cut_intersects

line_dir = r'D:\Malaysia\01_Brueprint\09_Terrace_detection\9_filterd_line\_divided'
out_dir_d03 = r'D:\Malaysia\01_Brueprint\09_Terrace_detection\10_cut_by_intersect'

line_shps = glob.glob(line_dir +os.sep + "*shp")
for shp in tqdm(line_shps):
    _03_cut_intersects.main(shp, out_dir)


"""#Cut 2 intersecting and shorted line by 8 m
"""
# 1min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _04_cut_intersects_2lines
    
# out_dir_d03 = r'D:\Malaysia\01_Brueprint\09_Terrace_detection\10_cut_by_intersect'
line_dir = out_dir_d03
out_dir_d04 = r'D:\Malaysia\01_Brueprint\09_Terrace_detection\10_cut_by_intersect_2lines'    

line_shps = glob.glob(line_dir +os.sep + "*shp")
for shp in tqdm(line_shps):
    _04_cut_intersects_2lines.main(shp, out_dir)
    
    
"""#merge
"""
# 1min
line_dir = out_dir_d04
out_dir_d04_ = line_dir + os.sep +"merge"
os.makedirs(out_dir_d04_,exist_ok=True)

line_shps = glob.glob(line_dir +os.sep + "*shp")
gdfs = [gpd.read_file(shp) for shp in line_shps]
merged_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)
out_mergefile = out_dir_d04_ + os.sep + "centerlines_45_cut_cut2ls_merge.shp"
merged_gdf.to_file(out_mergefile, encoding='utf-8')


"""#Iterrate procedure _02_filtering_by_intersects & dividing
"""
# 1 min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _02_filtering_by_intersects

line_shp_path = out_mergefile
out_dir_d05 = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\9_filterd_line\2nd_iteration"
os.makedirs(out_dir_d05, exist_ok=True)

_02_filtering_by_intersects.main(line_shp_path, out_dir)


"""#Divide lines for faster processing
"""
#3:30min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _99_devide_lines

line_dir = out_dir_d05
# line_dir = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\9_filterd_line\2nd_iteration"
out_dir_d99 = line_dir + os.sep + '_divided_cut2lis'
os.makedirs(out_dir_d99, exist_ok=True)

_99_devide_lines.main(line_dir, out_dir_d99)



"""#Connect lines within 5m and angle 135<225 by Least square searching
"""
#7min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _05_connect_nearlines_rev3

line_dir = out_dir_d99
# line_dir = r'D:\Malaysia\01_Brueprint\09_Terrace_detection\9_filterd_line\2nd_iterration\_divided_cut2lis'
out_dir_d05 = r'D:\Malaysia\01_Brueprint\09_Terrace_detection\11_connect_lines\centerlines_45_cut_cut2ls_45_connectSQ2'

line_shps = glob.glob(line_dir + os.sep + '*shp')

for shp in tqdm(line_shps):
    print(shp)
    _05_connect_nearlines_rev3.main(shp, out_dir_d05)


"""#Remove lines within roads
"""
#10 sec (moment)
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _06_erase_by_roads

# out_dir_d05 = r'D:\Malaysia\01_Brueprint\09_Terrace_detection\11_connect_lines\centerlines_45_cut_cut2ls_45_connectSQ2'
in_dir = out_dir_d05
out_dir_d06 = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\11_connect_lines"
road_line = r"D:\Malaysia\01_Brueprint\11_Roads\roads_manual.shp"

_06_erase_by_roads.main(in_dir, out_dir_d06, road_line)
# outfile: "D:\Malaysia\01_Brueprint\09_Terrace_detection\11_connect_lines\centerlines_45_cut_cut2ls_merge_45_connect_sq2_road.shp"


"""#Divie lines by roads
"""
# moment
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _99_devide_line_roads

line_shp = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\11_connect_lines\centerlines_45_cut_cut2ls_merge_45_connect_sq2_road.shp"
out_dir = r"D:\Malaysia\01_Brueprint\12_Pairing_terraces\1_divided_lines"
road_shp = r"D:\Malaysia\01_Brueprint\11_Roads\roads_manual_poly.shp" #polygon

_99_devide_line_roads.main(line_shp, out_dir, road_shp)


"""#Cut the shorted lines by 1m if 3 lines intersect
"""
# 1.5 min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _07_cut_intersects_pairing

#処理前のラインリスト
line_shps = glob.glob(r'D:\Malaysia\01_Brueprint\12_Pairing_terraces\1_divided_lines\*shp')
out_dir = r"D:\Malaysia\01_Brueprint\12_Pairing_terraces\2_cut\1_3cut"
for shp in tqdm(line_shps):
    _07_cut_intersects_pairing.main(shp,out_dir)
    
    
"""#Cut the shortest lines by 1m if 2 lines intersect
"""
#1min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _02_TerraceDetection import _08_cut_intersects_2lines_pairing

line_shps = glob.glob(r'D:\Malaysia\01_Brueprint\12_Pairing_terraces\2_cut\1_3cut\*shp')
out_dir = r"D:\Malaysia\01_Brueprint\12_Pairing_terraces\2_cut\2_2cut"

for shp in line_shps:
  _08_cut_intersects_2lines_pairing.main(shp, out_dir)



