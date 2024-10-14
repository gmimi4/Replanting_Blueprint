# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 10:39:07 2023

@author: chihiro
"""

import os
import rasterio
import numpy as np
from matplotlib import pyplot as plt
import cv2
from rasterio.crs import CRS
from pathlib import Path
import geopandas as gpd
from rasterio.features import shapes
mask = None
import time



def main(img_path, out_dir,size_e, size_d):
    start = time.time()
    
    img_array = rasterio.open(img_path).read(1)
    # change terrace value to 10
    img_array_rev = np.where(img_array==0,10,img_array)
    
    cmap = plt.cm.get_cmap("gray").copy()
    # cmap.set_bad(color='black')
    cmap.set_under(color='grey')
    cmap.set_over('White')
    # plt.imshow(img_array_rev, cmap=cmap, vmin=3, vmax=9) #White is 10
    
    ### EROSION ###
    # size_e = 5
    kernel = np.ones((size_e,size_e),np.uint8)
    erosion5 = cv2.erode(img_array_rev,kernel,iterations = 1)
    
    ### DILATION ###
    # size_d = 2
    kernel = np.ones((size_d,size_d),np.uint8)
    dilation3 = cv2.dilate(erosion5,kernel,iterations = 1)
    
    
    with rasterio.open(img_path) as src:
            crs = src.crs
            epsg_code = crs.to_epsg()
            kwargs = src.meta
            kwargs.update(
            driver = "GTiff",
            dtype=rasterio.float32,
            count = 1
            )
    
            out_file = out_dir + os.sep + Path(img_path).stem + f"_e{size_e}_d{size_d}.tif"
            with rasterio.Env(OSR_WKT_FORMAT="WKT2_2018"):
                with rasterio.open(out_file, 'w', **kwargs) as dst:
                    dst.write(dilation3, 1)
        
    
    #convert to polygon
    input_ras = out_file
    
    with rasterio.open(input_ras) as src:
        image = src.read(1)
        results = ({'properties': {'raster_val': v}, 'geometry': s}
        for i, (s, v) 
            in enumerate(
                shapes(image, mask=mask, transform=src.transform)))
        
        # The result is a generator of GeoJSON features
        geoms = list(results)
       
    
    gpd_polygonized_raster  = gpd.GeoDataFrame.from_features(geoms)
    
    gpd_polygonized_raster.crs = f"EPSG:{epsg_code}"
    
    output_shapefile_path = out_dir + os.sep + Path(input_ras).stem + ".shp"
    gpd_polygonized_raster.to_file(output_shapefile_path)
    
    end = time.time()
    time_diff = end - start
    print(time_diff/60, "min")
    

if __name__=="__main__":
    main()
    






