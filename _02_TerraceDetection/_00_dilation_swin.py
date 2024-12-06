# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 10:39:07 2023

@author: chihiro
"""

import os
import rasterio
import numpy as np
import cv2
from pathlib import Path
import geopandas as gpd
# from rasterio.features import geometry_mask
from rasterio.features import shapes
mask = None
# from shapely.geometry import shape
import time


# img_path = r"E:\Malaysia\01_Blueprint\Pegah_san\03_UNet\OUT_swinBi\_mosaic\swinBi_mosaic.tif"
# out_dir = os.path.dirname(img_path)

def main(img_path, out_dir,size_e, size_d):
    start = time.time()
    
    img_array = rasterio.open(img_path).read(1)
    
    """ # filtering by threshold """
    thre = 0.025#0.03
    thre_str = str(thre).replace(".","")
    """ #change terrace value to 10"""
    img_array_rev = np.where(img_array>=thre, 10,img_array)
    img_array_rev = np.where(img_array_rev<10, 1,img_array_rev)
    img_array_rev = img_array_rev.astype('uint8')
        
    ## => erodsion by 5*5 kernel -> dilation by 2*2 kernel
    ### EROSION ###
    size_e = 2
    kernel = np.ones((size_e,size_e),np.uint8)
    erosion5 = cv2.erode(img_array_rev,kernel,iterations = 1)
    
    ### DILATION ###
    size_d = 2
    kernel = np.ones((size_d,size_d),np.uint8)
    dilation3 = cv2.dilate(erosion5,kernel,iterations = 1)
    
    
    with rasterio.open(img_path) as src:
            kwargs = src.meta
            kwargs.update(
            dtype=rasterio.uint8,
            nodata=0
            
            )
            
            epsg_code = src.crs.to_epsg()
    
            out_file = out_dir + os.sep + Path(img_path).stem + f"_{thre_str}_e{size_e}_d{size_d}.tif"
            with rasterio.Env(OSR_WKT_FORMAT="WKT2_2018"):
                with rasterio.open(out_file, 'w', **kwargs) as dst:
                    dst.write(dilation3, 1)
    
    """ #convert to polygon """
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
    
    # output_shapefile_path = out_dir + os.sep + Path(input_ras).stem + ".shp"
    # gpd_polygonized_raster.to_file(output_shapefile_path)
    
    
    
    end = time.time()
    time_diff = end - start
    print(time_diff/60, "min")
    
    

if __name__=="__main__":
    main()
    
        





