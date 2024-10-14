# -*- coding: utf-8 -*-
"""
# Crop raster
# Skeltonize to extract lines
"""
import os
from skimage.morphology import skeletonize
import rasterio
from rasterio.mask import mask
import numpy as np
import geopandas as gpd
from rasterio import Affine
import cv2
import time


def main(image_path, clip_poly, out_skelton_dir):
    start = time.time()
    
    gdf = gpd.read_file(clip_poly)
    
    with rasterio.open(image_path) as src:
        arr = src.read(1)
        # Extract the EPSG code
        crs = src.crs
        epsg_use = crs.to_epsg()
        meta = src.meta.copy()
        #Crop image by polygon
        clipped, transform = mask(src, gdf.geometry, crop=True)
    
        out_dir = os.path.dirname(image_path)
        filename = os.path.basename(image_path)[:-4]
        output_file = out_dir + f"\\{filename}_clip.tif"
        
        meta.update({
            "height": clipped.shape[1],
            "width": clipped.shape[2],
            "transform": transform
        })
            
        # Create a new GeoTIFF file for the clipped raster
        with rasterio.open(output_file, 'w', **meta) as dst:
            dst.write(clipped)
    
    
    ### Open clipped img
    with rasterio.open(output_file) as src:
        arr = src.read(1)
    
    """ If convert background """
    #Currentry 10:terrace, 1: background, 0:nodata ---> 1:background, 0:others    
    arr_bi = np.where(arr == 0, np.nan, arr) #nodata
    arr_bi = np.where(arr_bi == 10, 0, arr_bi)
    
    
    """ If convert edges 
    # to nan,1
    arr_bi = np.where(arr != 10, np.nan, 1) #10: edge arr !=10 did not work
    ## background (work)
    arr_bi = np.where(arr == 10, np.nan, arr) #10: edge 1 or nan
    """
    
    #check
    # import matplotlib.pyplot as plt
    # plt.imshow(arr_bi)  # 'viridis' is just one of many available colormaps
    # plt.colorbar()
    # plt.show()
    
    """ #skelton """
    skeleton = skeletonize(arr_bi) #2d array bool
    # skeleton_result =  np.where(skeleton, arr_bi, 0)
    skeleton_result = skeleton.astype('uint8')
    
    """ #dilation """
    size_d = 3
    kernel = np.ones((size_d,size_d),np.uint8)
    dilation = cv2.dilate(skeleton_result,kernel,iterations = 1)
    
    # Export to tif
    output_skeltonfile = out_skelton_dir + os.sep + f"{os.path.basename(image_path)[:-4]}_skelton.tif"
    with rasterio.open(output_skeltonfile, 'w', driver='GTiff', height=arr_bi.shape[0], width=arr_bi.shape[1],
                       count=1, dtype='uint8', crs=src.crs, transform=src.transform) as dst:
        dst.write(dilation,1)
        
        
    end = time.time()
    time_diff = end - start
    print(time_diff/60, "min")

if __name__=="__main__":
    main()
    