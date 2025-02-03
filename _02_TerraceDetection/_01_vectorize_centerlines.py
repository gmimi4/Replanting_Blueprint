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

root_dir = "set your path again"
terrace_detection_dir = root_dir + os.sep + "04_Terrace_detection"
image_path = "path to _skelton.tif"
clip_shp = "path to clip shp"
out_center_dir = terrace_detection_dir + os.sep + "01_centerlines" #+ os.sep + pagenum
os.makedirs(out_center_dir, exist_ok=True)
clip_bool=True

## use arcgis at present #excute in command
arcpy_path = r'C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy' # set your ArcGIS path

py_path = os.path.abspath(r"_01_vectorize_centerlines_arctool.py")

gdb = r"E:\Malaysia\01_Blueprint\SDGuthrie\Arc_SDGuthrie\SDGuthrie\MyProject.gdb" ## set ArcGIS gdb path

# def main(image_path, clip_shp, out_dir, clip_bool=True):
out_dir = out_center_dir
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

process = subprocess.run([arcpy_path, py_path, outpoly, out_dir, gdb], stdout=subprocess.PIPE, shell=True)
print("centerlines created")

end = time.time()
time_diff = end - start
print(time_diff/60, "min")

# if __name__=="__main__":
#     main()


