
import os, sys
from osgeo import gdal
import numpy as np
from osgeo import osr
from tqdm import tqdm
import time


def main(dem_raster, out_dir):
    start = time.time()
    ras_file_name = os.path.basename(dem_raster)[:-4]
    
    # ===========Gaussian fiilter===========
    k=5 #kernel window size
    s=3 #siguma
    size = k // 2
    
    dem_src = gdal.Open(dem_raster, gdal.GA_ReadOnly)
    dem_band = dem_src.GetRasterBand(1)
    dem_arr_ori = dem_band.ReadAsArray()
    w,h = dem_arr_ori.shape
    
    img = dem_arr_ori
    ## 0 padding
    _img = np.zeros((w+2*size,h+2*size), dtype=np.float32)
    _img[size:size+w,size:size+h] = img.copy().astype(np.float32)
    dst = _img.copy()
    
    # kernel filter
    ker = np.zeros((k,k), dtype=np.float)
    
    for x in range(-1*size,k-size):
        for y in range(-1*size,k-size):
          ker[x+size,y+size] = (1/(2*np.pi*(s**2)))*np.exp(-1*(x**2+y**2)/(2*(s**2)))
    ker /= ker.sum()
    
    for x in tqdm(range(w)):
       for y in range(h):
           dst[x+size,y+size] = np.sum(ker*_img[x:x+k,y:y+k])
    
    #delete outliers
    dst = dst[size:size+w,size:size+h].astype(np.float32)
    dst_max = np.nanmax(dst)
    dst_min = np.nanmin(dst)
    dst_convert = np.where(dst<-100, -np.nan, dst)    
    
    #export to file
    xsize=dem_src.RasterXSize # h
    ysize=dem_src.RasterYSize # w
    band=1
    dtype = gdal.GDT_Float32
    
    out_file = out_dir + os.sep + os.sep + ras_file_name+f"_k{k}s{s}.tif"
    output = gdal.GetDriverByName('GTiff').Create(out_file, xsize, ysize, band, dtype)
    output.SetGeoTransform(dem_src.GetGeoTransform())
    
    projection = dem_src.GetProjection()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(projection)
    epsg_code = srs.GetAttrValue("AUTHORITY", 1)
    srs.ImportFromEPSG(int(epsg_code))
    output.SetProjection(srs.ExportToWkt())
    output.GetRasterBand(1).WriteArray(dst_convert)
    output.FlushCache()
    output = None
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )
    

if __name__=="__main__":
    main()