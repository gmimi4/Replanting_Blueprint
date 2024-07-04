# -*- coding: utf-8 -*-

import os
import glob
from tqdm import tqdm
import geopandas as gpd
import pandas as pd


"""###### Pairing terraces ######"""

"""# Vertically cut lines at edges of each other
"""
#20min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _03_PairingTerraces import _03_vertical_cut

line_shps = glob.glob(r'D:\Malaysia\01_Brueprint\12_Pairing_terraces\2_cut\2_2cut\*shp')
out_dir = r"D:\Malaysia\01_Brueprint\12_Pairing_terraces\4_vertical_cut"
dem_path = r"D:\Malaysia\01_Brueprint\05_R_DEM\DEM_05m_R_kring.tif"

for shp in tqdm(line_shps):
    print(shp)
    _03_vertical_cut.main(shp, out_dir, dem_path)



"""# dissapered lines extracted and vertically cut (some lines dissapeared somehow)  
"""
#2min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _03_PairingTerraces import _03_vertical_cut_post

# before vertical cut
line_shps = glob.glob(r'D:\Malaysia\01_Brueprint\12_Pairing_terraces\2_cut\2_2cut\*shp')
after_cut_dir = r"D:\Malaysia\01_Brueprint\12_Pairing_terraces\4_vertical_cut"
dem_path = r"D:\Malaysia\01_Brueprint\05_R_DEM\DEM_05m_R_kring.tif"

for shp in tqdm(line_shps):
  _03_vertical_cut_post.main(shp, after_cut_dir, dem_path) 


"""# Assign T1T2 and pairID
"""
#10min
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _03_PairingTerraces import _04_paringID

line_shps = glob.glob(r'D:\Malaysia\01_Brueprint\12_Pairing_terraces\4_vertical_cut\post\*shp')
dem_path = r"D:\Malaysia\01_Brueprint\05_R_DEM\DEM_05m_R_kring.tif"
# out_dir = r"D:\Malaysia\01_Brueprint\12_Pairing_terraces\5_pairing"
out_dir = r"D:\Malaysia\01_Brueprint\12_Pairing_terraces\5_pairing"

for shp in tqdm(line_shps):
  _04_paringID.main(shp, dem_path, out_dir)


"""# connect neighboring lines which have same pairID
"""
#20 sec
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _03_PairingTerraces import _05_paringID_post_rev

#1min
line_shps = glob.glob(r'D:\Malaysia\01_Brueprint\12_Pairing_terraces\5_pairing\*T1T2.shp')
out_dir = os.path.dirname(line_shps[0]) + os.sep + "_post"
os.makedirs(out_dir, exist_ok=True)

for shp in tqdm(line_shps):
  _05_paringID_post_rev.main(shp, out_dir)
  


"""# Put direction
"""
#39 sec
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _03_PairingTerraces import _06_put_direction

line_shps = glob.glob(r'D:\Malaysia\01_Brueprint\12_Pairing_terraces\5_pairing\_post\*vertical_post_T1T2_post.shp')
dem_path = r"D:\Malaysia\01_Brueprint\05_R_DEM\DEM_05m_R_kring.tif"
out_dir = os.path.dirname(line_shps[0]) + os.sep + "_direction"
os.makedirs(out_dir, exist_ok=True)

for shp in tqdm(line_shps):
  _06_put_direction.main(shp, dem_path, out_dir)
