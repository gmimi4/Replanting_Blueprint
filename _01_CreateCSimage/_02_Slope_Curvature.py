#C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
import arcpy
import os
from osgeo import gdal
import numpy as np
from osgeo import osr
from pyproj import CRS

arcpy.env.overwriteOutput = True


dem_raster = "set DEM path"
dem_gaussian = "set Gaussian DEM path"
out_dir = os.path.dirname(dem_gaussian)

oridem_filename = os.path.basename(dem_raster)[:-4]
gausdem_filename = os.path.basename(dem_gaussian)[:-4]

# ===========Slope===========
#Original Dem
out_slope = out_dir+os.sep+oridem_filename+"_slope.tif"
arcpy.ddd.Slope(dem_raster, out_slope, "DEGREE", "", "PLANAR", "METER","GPU_THEN_CPU")

# ===========Curvature===========
out_curv = out_dir+os.sep+gausdem_filename+"_curv.tif"
arcpy.ddd.Curvature(dem_gaussian, out_curv, "1")

# delete exordinary values maybe ±100 <- denpending on sites
thresh = 200
curve_src = gdal.Open(out_curv, gdal.GA_ReadOnly)
curve_band = curve_src.GetRasterBand(1)
curve_arr_ori = curve_band.ReadAsArray()
curve_arr_remove_1 = np.where(curve_arr_ori>thresh,thresh,curve_arr_ori)
curve_arr_remove_2 = np.where(curve_arr_remove_1<-1*thresh,-1*thresh, curve_arr_remove_1)

xsize=curve_src.RasterXSize # h
ysize=curve_src.RasterYSize # w
band=1
dtype = gdal.GDT_Float32

out_curv_fin = out_curv.replace(".tif","_fin.tif")
output = gdal.GetDriverByName('GTiff').Create(out_curv_fin, xsize, ysize, band, dtype)
output.SetGeoTransform(curve_src.GetGeoTransform())

projection = curve_src.GetProjection()
srs = osr.SpatialReference()
srs.ImportFromWkt(projection)
# print(srs.ExportToWkt()) #check
epsg_code = srs.GetAttrValue("AUTHORITY", 1)
if epsg_code == None:
    crs = CRS.from_wkt(srs.ExportToWkt())
    epsg_code = crs.to_epsg()
srs.ImportFromEPSG(int(epsg_code))
output.SetProjection(srs.ExportToWkt())
output.GetRasterBand(1).WriteArray(curve_arr_remove_2)
output.FlushCache()
output = None
