#C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
import os, sys
from osgeo import gdal
import numpy as np
from osgeo import osr
from tqdm import tqdm
import time

# dem_raster = r"D:\Malaysia\01_Brueprint\05_R_DEM\DEM_05m_R_kring.tif"
# out_dir = r"D:\Malaysia\01_Brueprint\05_R_DEM"
# epsg_code = 32648 #32648

# os.makedirs(out_dir,exist_ok=True)
def main(dem_raster, out_dir,epsg_code):
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
    ## 0パディング処理
    _img = np.zeros((w+2*size,h+2*size), dtype=np.float32)
    _img[size:size+w,size:size+h] = img.copy().astype(np.float32)
    dst = _img.copy()
    
    # フィルタ作成
    ker = np.zeros((k,k), dtype=np.float)
    
    for x in range(-1*size,k-size):
        for y in range(-1*size,k-size):
          ker[x+size,y+size] = (1/(2*np.pi*(s**2)))*np.exp(-1*(x**2+y**2)/(2*(s**2)))
    ker /= ker.sum()
    
    for x in tqdm(range(w)):
       for y in range(h):
           dst[x+size,y+size] = np.sum(ker*_img[x:x+k,y:y+k])
    
    #異常値になるから削除
    dst = dst[size:size+w,size:size+h].astype(np.float32)
    # 異常値除外
    dst_max = np.nanmax(dst)
    dst_min = np.nanmin(dst)
    # dst_convert = np.where(dst==100, np.nan, dst)
    dst_convert = np.where(dst<-100, -np.nan, dst)
    # dst_convert = np.where(dst_convert>999, 100, dst_convert) #要検討
    
    
    #ファイルの書き出し　
    xsize=dem_src.RasterXSize #水平方向ピクセル数 h
    ysize=dem_src.RasterYSize #垂直方向ピクセル数 w
    band=1
    dtype = gdal.GDT_Float32
    
    out_file = out_dir + "\\"+ras_file_name+f"_k{k}s{s}.tif"
    output = gdal.GetDriverByName('GTiff').Create(out_file, xsize, ysize, band, dtype)
    output.SetGeoTransform(dem_src.GetGeoTransform())
    #ul_xやh_resの取得
    #ul_x #始点端経度, h_res#西東解像度, ul_y#始点端緯度,v_res#南北解像度
    
    srs = osr.SpatialReference() #空間参照情報
    srs.ImportFromEPSG(epsg_code)
    output.SetProjection(srs.ExportToWkt())
    output.GetRasterBand(1).WriteArray(dst_convert) #出力画像のバンド1に計算結果を入れる
    output.FlushCache() #書き出し
    output = None
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )
    

if __name__=="__main__":
    main()