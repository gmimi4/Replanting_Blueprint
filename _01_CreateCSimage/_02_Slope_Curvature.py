#C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
import arcpy
import os
from osgeo import gdal
import numpy as np
from osgeo import osr

arcpy.env.overwriteOutput = True


dem_raster = r"E:\Malaysia\Pegah_san\01_DEM_SLOPE_Curvature\FELDA20160316_DTM_32647_05m.tif"
dem_gaussian = r"E:\Malaysia\Pegah_san\01_DEM_SLOPE_Curvature\FELDA20160316_DTM_32647_05m_k5s3.tif"
out_dir = r"E:\Malaysia\Pegah_san\01_DEM_SLOPE_Curvature"
epsg_code = 32647 #32648

oridem_filename = os.path.basename(dem_raster)[:-4]
gausdem_filename = os.path.basename(dem_gaussian)[:-4]

# ===========Slope===========
#Original Dem
out_slope = out_dir+"\\"+oridem_filename+"_slope.tif"
arcpy.ddd.Slope(dem_raster, out_slope, "DEGREE", "", "PLANAR", "METER","GPU_THEN_CPU")

# ===========Curvature===========
out_curv = out_dir+"\\"+gausdem_filename+"_curv.tif"
arcpy.ddd.Curvature(dem_gaussian, out_curv, "1")

# delete exordinary values maybe ±100 <- denpending on sites
thresh = 200
curve_src = gdal.Open(out_curv, gdal.GA_ReadOnly)
curve_band = curve_src.GetRasterBand(1)
curve_arr_ori = curve_band.ReadAsArray()
#curve_arr_ori.max()
curve_arr_remove_1 = np.where(curve_arr_ori>thresh,thresh,curve_arr_ori)
curve_arr_remove_2 = np.where(curve_arr_remove_1<-1*thresh,-1*thresh, curve_arr_remove_1)

#ファイルの書き出し
xsize=curve_src.RasterXSize #水平方向ピクセル数 h
ysize=curve_src.RasterYSize #垂直方向ピクセル数 w
band=1
dtype = gdal.GDT_Float32

out_curv_fin = out_curv.replace(".tif","_fin.tif")
output = gdal.GetDriverByName('GTiff').Create(out_curv_fin, xsize, ysize, band, dtype)
output.SetGeoTransform(curve_src.GetGeoTransform())

srs = osr.SpatialReference() #空間参照情報
srs.ImportFromEPSG(epsg_code)
output.SetProjection(srs.ExportToWkt())
output.GetRasterBand(1).WriteArray(curve_arr_remove_2) #出力画像のバンド1に計算結果を入れる
output.FlushCache() #書き出し
output = None

#delete file
#os.remove(out_curv)