# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 10:36:20 2023

@author: chihiro
"""
import os
import rasterio
from rasterio.features import shapes
import geopandas as gpd
import subprocess
import time


image_path = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\3_dilation\mosaic_e5_d2_clip.tif"
out_dir = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\4_centerlines"
epsg_use = 32648

def main(image_path, out_dir, epsg_use):
    start = time.time()
    """
    # Convert raster to polygon
    """
    src = rasterio.open(image_path)
    arr = src.read(1)
    
    transform = src.transform
    shapes_list = list(shapes(arr, mask=None, transform=transform))
    results = ({'properties': {'rval': v}, 'geometry': s} for i, (s, v) in enumerate(shapes_list)) #"val" should be less than 5 characters for later arcpy 
    geoms=list(results)
    polygons_gdf = gpd.GeoDataFrame.from_features(geoms)
    polygons_gdf.set_crs(epsg=epsg_use, inplace=True)
    
    # export polygonized raster to raster directory
    outpoly = image_path.replace(".tif", ".shp")
    polygons_gdf.to_file(outpoly)
    
    
    """
    # Vectorize for centerlines of background using ArcGIS
    """
    ## use arcgis at present #excute in command
    arcpy_path = r'C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy' # set your ArcGIS path
    py_path = r'C:\Users\chihiro\Desktop\Python\Blueprint\Terrace_detection\for_local_processing\_01_vectorize_centerlines_arctool.py'
    
    process = subprocess.run([arcpy_path, py_path], stdout=subprocess.PIPE, shell=True)
    print("centerlines created")

    end = time.time()
    time_diff = end - start
    print(time_diff/60, "min")

if __name__=="__main__":
    main()


