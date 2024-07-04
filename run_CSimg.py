# -*- coding: utf-8 -*-


import os
import glob
from tqdm import tqdm
import geopandas as gpd
import pandas as pd
import subprocess


"""###### CS image ######"""
"""# Gausian filtering of DEM for slope
"""
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
# os.chdir(r'C:\Users\chihiro\Desktop\Python\Blueprint\CSMap\for_local_processing')
from _01_CreateCSimage import _01_Gaussian

dem_raster = r"D:\Malaysia\01_Brueprint\05_R_DEM\DEM_05m_R_kring.tif" #set path to your dem tif
out_dir = os.path.dirname(dem_raster) #same as dem directory
epsg_use = 32648 #set spatial reference epsg of your site

os.makedirs(out_dir,exist_ok=True)
# run
_01_Gaussian.main(dem_raster, out_dir, epsg_use)


"""# Generate slope and curvature
   # you need arcpy for curvature image. please assign python engine for arcpy
"""
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')

### please set the following path and setting in _02_Slope_Curvature.py:
# dem_raster path
# dem_gaussian path
# out_dir path
# epsg_code

arcpy_path = r'C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy' #your arcpy path
py_path = './_01_CreateCSimage/_02_Slope_Curvature.py'

# run
process = subprocess.run([arcpy_path, py_path], stdout=subprocess.PIPE, shell=True)


"""# Generate CS image
"""
os.chdir(r'C:\Users\chihiro\Desktop\GitHub\ReplantingBlueprint')
from _01_CreateCSimage import _03_CSMap_export

# set the following path
slope_raster = r"D:\Malaysia\01_Brueprint\07_SLOPE\SLOPE_05m_R_kring.tif"
curve_raster = r"D:\Malaysia\01_Brueprint\06_Curve\DEM_05m_R_kring_curv.tif"
out_dir = r'D:\Malaysia\01_Brueprint\08_CSMap_test'
epsg_code = 32648

# run
_03_CSMap_export.main(slope_raster, curve_raster, out_dir, epsg_code)



