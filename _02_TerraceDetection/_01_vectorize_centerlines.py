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

# ----------------------------------------------------------
### Please set arcpy_path, py_path and gdb path in the code
# ----------------------------------------------------------

def main(image_path, clip_shp, out_dir, clip_bool=True):
    start = time.time()
    """
    # Convert raster to polygon
    """
    src = rasterio.open(image_path)
    arr = src.read(1)
    crs = src.crs
    epsg_use = crs.to_epsg()
    
    transform = src.transform
    shapes_list = list(shapes(arr, mask=None, transform=transform))
    results = ({'properties': {'rval': v}, 'geometry': s} for i, (s, v) in enumerate(shapes_list)) #"val" should be less than 5 characters for later arcpy 
    geoms=list(results)
    polygons_gdf = gpd.GeoDataFrame.from_features(geoms)
    polygons_gdf.set_crs(epsg=epsg_use, inplace=True)
    
    # export polygonized raster to raster directory
    outpoly = image_path.replace(".tif", ".shp") #output in tif dir
    
    ## clip
    if clip_bool:
        gdf_clip = gpd.read_file(clip_shp)
        clip_poly = polygons_gdf.clip(gdf_clip.geometry)
        clip_poly.to_file(outpoly)
    
    else:
        polygons_gdf.to_file(outpoly)
    
    
    """
    # Vectorize for centerlines of background using ArcGIS
    """
    ## use arcgis at present #excute in command
    arcpy_path = r'C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy' # set your ArcGIS path
    ## set polygon path!!!
    py_path = r"path to _02_TerraceDetection\_01_vectorize_centerlines_arctool.py"
    ## set gdb path
    gdb = r"path to .gdb"

    process = subprocess.run([arcpy_path, py_path, outpoly, out_dir, gdb], stdout=subprocess.PIPE, shell=True)

    end = time.time()
    time_diff = end - start
    print(time_diff/60, "min")

if __name__=="__main__":
    main()


