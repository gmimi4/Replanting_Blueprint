# -*- coding: utf-8 -*-

import os
import glob
from tqdm import tqdm
import geopandas as gpd
import pandas as pd


"""###### Pairing terraces ######"""

"""# Set root directory
"""
pairing_terrace_dir = "your path" + os.sep + "05_Pairing_terraces"
os.makedirs(pairing_terrace_dir, exist_ok=True)
### set DEM path
dem_path = "set DEM path"


"""# Vertically cut lines at endpoints of each other
"""
#20min
os.chdir('set path to ReplantingBlueprint')
from _03_PairingTerraces import _03_vertical_cut

line_shps = glob.glob(rf"your path to 04_Terrace_detection\06_cut_by_intersect\2_2cut" + os.sep + "*.shp")
out_dir = pairing_terrace_dir + os.sep + "01_vertical_cut" + os.sep + f"extent{pagenum}"
os.makedirs(out_dir, exist_ok=True)

for shp in tqdm(line_shps):
    print(shp)
    _03_vertical_cut.main(shp, out_dir, dem_path)



"""# dissapered lines extracted and vertically cut (some lines dissapeared somehow)  
"""
#5min
os.chdir('set path to ReplantingBlueprint')
from _03_PairingTerraces import _03_vertical_cut_post

# before vertical cut
line_shps = glob.glob(rf"your path" + os.sep + "04_Terrace_detection\06_cut_by_intersect\2_2cut\extent{pagenum}" + os.sep + "*.shp")
# after_cut_dir
after_cut_dir = pairing_terrace_dir + os.sep + "01_vertical_cut" + os.sep + f"extent{pagenum}"
# after_cut_dir = out_dir

for shp in tqdm(line_shps):
  _03_vertical_cut_post.main(shp, after_cut_dir, dem_path) 


"""# Assign T1T2 and pairID
"""
#30-45min
os.chdir('set path to ReplantingBlueprint')
from _03_PairingTerraces import _04_paringID

pagenum = 
after_cut_dir = pairing_terrace_dir + os.sep + "01_vertical_cut" + os.sep + f"extent{pagenum}"
in_dir = after_cut_dir + os.sep + "post"
line_shps = glob.glob(in_dir + os.sep + "*shp")
out_dir_d2 = pairing_terrace_dir + os.sep + "02_pairing" + os.sep + f"extent{pagenum}"
os.makedirs(out_dir_d2, exist_ok=True)


for shp in tqdm(line_shps):
  _04_paringID.main(shp, dem_path, out_dir_d2)


"""# connect neighboring lines which have same pairID
"""
#1 min
os.chdir('set path to ReplantingBlueprint')
from _03_PairingTerraces import _05_paringID_post

#1min
pagenum = #! 
out_dir_d2 = pairing_terrace_dir + os.sep + "02_pairing" + os.sep + f"extent{pagenum}"
line_shps = glob.glob(out_dir_d2 + os.sep + "*T1T2.shp")
out_dir_d3 = os.path.dirname(line_shps[0]) + os.sep + "_post"
os.makedirs(out_dir_d3, exist_ok=True)

for shp in tqdm(line_shps):
  _05_paringID_post.main(shp, out_dir_d3)
  


"""# Put direction
"""
#1 min
os.chdir('set path to ReplantingBlueprint')
from _03_PairingTerraces import _06_put_direction

pagenum = #1
out_dir_d2 = pairing_terrace_dir + os.sep + "02_pairing" + os.sep + f"extent{pagenum}"
out_dir_d3 = out_dir_d2 + os.sep + "_post"
line_shps = glob.glob(out_dir_d3 + os.sep + "*.shp")
out_dir_d4 = pairing_terrace_dir + os.sep + "03_direction" +os.sep + f"extent{pagenum}"
os.makedirs(out_dir_d4, exist_ok=True)

for shp in tqdm(line_shps):
  _06_put_direction.main(shp, dem_path, out_dir_d4)


"""#merge #for check
"""
# 1min
line_dir = out_dir_d4
out_dir_d4_ = line_dir + os.sep +"check_merge"
os.makedirs(out_dir_d4_,exist_ok=True)

line_shps = glob.glob(line_dir +os.sep + "*shp")
gdfs = [gpd.read_file(shp) for shp in line_shps]
merged_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)
out_mergefile = out_dir_d4_ + os.sep + "merge_direction_rev_skelton_back.shp"
merged_gdf.to_file(out_mergefile, encoding='utf-8')