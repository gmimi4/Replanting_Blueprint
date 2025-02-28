# -*- coding: utf-8 -*-


import os
import glob
from tqdm import tqdm
import geopandas as gpd
import pandas as pd
import subprocess


"""###### CS image ######"""

""" #Set the main dir"""
root_dir = "set your path"
cs_dir = root_dir + os.sep + "01_CS"
os.makedirs(cs_dir, exist_ok=True)

ReplantingBlueprint = 'set path to ReplantingBlueprint'

"""# Gausian filtering of DEM for slope
"""
os.chdir(ReplantingBlueprint)
from _01_CreateCSimage import _01_Gaussian

dem_raster = "set your dem path"
out_dir = cs_dir
os.makedirs(out_dir,exist_ok=True)

# run
_01_Gaussian.main(dem_raster, out_dir)


"""# Generate slope and curvature
   # you need arcpy for curvature image. please assign python engine for arcpy
"""
os.chdir(ReplantingBlueprint)
arcpy_path = '#set your arcpy path'
py_path = './_01_CreateCSimage/_02_Slope_Curvature.py'

# -----------------------------------------------------------------------
### Please set the following path and setting in _02_Slope_Curvature.py:
# -----------------------------------------------------------------------
# dem_raster path
# dem_gaussian path

# run
process = subprocess.run([arcpy_path, py_path], stdout=subprocess.PIPE, shell=True)


"""# Generate CS image
"""
os.chdir(ReplantingBlueprint)
from _01_CreateCSimage import _03_CSMap_export

dem_name = os.path.basename(dem_raster)[:-4]
slope_raster = cs_dir + os.sep + f"{dem_name}_slope.tif"
curve_raster = cs_dir + os.sep + f"{dem_name}_k5s3_curv_fin.tif"
out_dir = cs_dir

# run
_03_CSMap_export.main(slope_raster, curve_raster, out_dir)



