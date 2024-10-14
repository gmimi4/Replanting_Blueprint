# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 14:44:46 2024

@author: chihiro
"""

from PIL import Image
import os
import math
from osgeo import gdal
import numpy as np
import matplotlib.cm as cm
import time


def main(slope_raster, curve_raster, out_dir):
    start = time.time()
    
    tmp_dir = out_dir + os.sep + "_tmp"
    os.makedirs(tmp_dir,exist_ok=True)
    slope_name = os.path.basename(slope_raster)[:-4]
    curve_name = os.path.basename(curve_raster)[:-4]
    cs_name = "CSimage.tif"
    
    #get shape and make array
    # slope
    slope_src = gdal.Open(slope_raster, gdal.GA_ReadOnly)
    slope_band = slope_src.GetRasterBand(1)
    slope_arr_ori = slope_band.ReadAsArray()
    
    # curvature
    curve_src = gdal.Open(curve_raster, gdal.GA_ReadOnly)
    curve_band = curve_src.GetRasterBand(1)
    curve_arr_ori = curve_band.ReadAsArray()
    
    # convert error minus to 0 or nan
    slope_arr_remove_1 = np.where(slope_arr_ori>90,90,slope_arr_ori)
    slope_arr_remove = np.where(slope_arr_remove_1<0,0,slope_arr_remove_1)
    # curvは不要なはず
    curve_arr_remove = curve_arr_ori
    
    
    """#to RGB"""
    #slope
    sm = cm.ScalarMappable(norm=None, cmap=cm.Reds)
    slope_array = sm.to_rgba(slope_arr_remove, alpha=0.8,bytes=True)
    img_slope = Image.fromarray(slope_array)
    #curv
    sm2 = cm.ScalarMappable(norm=None, cmap=cm.Blues_r)
    curve_array = sm2.to_rgba(curve_arr_remove,  alpha=1,bytes=True)
    img_cur= Image.fromarray(curve_array)
    
    cs_img = Image.alpha_composite(img_cur, img_slope)
    
    #for check
    # cs_img.save(os.path.join(out_dir,cs_name[:-4]+".png"))
    
    out_path = os.path.join(out_dir, cs_name)
    
    #  Set the Pixel Data
    cs_img_arr = np.array(cs_img) #4band
    
    r_pixels = cs_img_arr[:,:,0]
    g_pixels = cs_img_arr[:,:,1]
    b_pixels = cs_img_arr[:,:,2]
    alpha_pixels = cs_img_arr[:,:,3]
    pixels_list = [r_pixels, g_pixels, b_pixels, alpha_pixels]
    
    # create the 3-band raster file
    in_ds = gdal.Open(slope_raster)
    geotransform = in_ds.GetGeoTransform()
    
    originY = geotransform[3]
    originX = geotransform[0]
    pixelWidth = 1 #int(geotransform[1])
    pixelHeight = 1 #int(geotransform[5]*-1)
    num_bands = 4  # Number of bands
    # data_type = in_band.DataType
    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(out_path, cs_img_arr.shape[1],  cs_img_arr.shape[0], num_bands, gdal.GDT_Byte)
    out_ds.SetGeoTransform(in_ds.GetGeoTransform())
    
    out_ds.SetProjection(in_ds.GetProjection())
    
    for i, band_data in enumerate(pixels_list):
        outband = out_ds.GetRasterBand(i+1)
        outband.WriteArray(band_data)
    
    out_ds = None
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )
    

if __name__=="__main__":
    main()