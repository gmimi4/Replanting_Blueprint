# -*- coding: utf-8 -*-


import os
import glob
from tqdm import tqdm
import geopandas as gpd
import pandas as pd
import subprocess


"""###### CS image ######"""

""" #Set the main dir"""
cs_dir = "your path" + os.sep + "01_CS"


"""# Gausian filtering of DEM for slope
"""
os.chdir('set path to ReplantingBlueprint')
from _01_CreateCSimage import _01_Gaussian

dem_raster = "set your dem path"
out_dir = cs_dir
os.makedirs(out_dir,exist_ok=True)

# run
_01_Gaussian.main(dem_raster, out_dir)


"""# Generate slope and curvature
   # you need arcpy for curvature image. please assign python engine for arcpy
"""
os.chdir('set path to ReplantingBlueprint')

arcpy_path = '#your arcpy path'
py_path = './_01_CreateCSimage/_02_Slope_Curvature.py'

# run
process = subprocess.run([arcpy_path, py_path], stdout=subprocess.PIPE, shell=True)


"""# Generate CS image
"""
os.chdir('set path to ReplantingBlueprint')
from _01_CreateCSimage import _03_CSMap_export

# set the path to slope and curvature that you created
slope_raster = cs_dir + os.sep + "*_slope.tif" #check the path
curve_raster = cs_dir + os.sep + "*_curv_fin.tif" #check the path
out_dir = cs_dir

# run
_03_CSMap_export.main(slope_raster, curve_raster, out_dir)



