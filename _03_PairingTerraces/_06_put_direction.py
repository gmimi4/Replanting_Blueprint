# -*- coding: utf-8 -*-

import os
import rasterio
import geopandas as gpd
# import matplotlib.pyplot as plt
import numpy as np
from numpy.lib.stride_tricks import as_strided
import math
import fiona
from shapely.geometry import Point, LineString, Polygon,MultiPoint, MultiLineString
import shapely
import time

# line_shp_path = '/content/drive/MyDrive/Malaysia/Blueprint/12_Pairing_terraces/4_vertical_cut/centerlines_45_cut_cut2ls_merge_45_connect_merge_over5_road_sing_1_cut_cut2_vertical.shp'
# line_shp_path = sys.argv[1]
# dem_path = '/content/drive/MyDrive/Malaysia/Blueprint/DEM/02_R_Out/DEM_05m_R_kring.tif'
# out_dir = '/content/drive/MyDrive/Malaysia/Blueprint/13_Generate_points/01_put_direction'
# os.makedirs(tmp_dir2, exist_ok=True)

def main(line_shp_path, dem_path, out_dir):
    
    start = time.time()

    gpdf = gpd.read_file(line_shp_path)
    
    
    def rasterize_vector(linestring, resolution):
      geom = [linestring]#linestring_list
    
      #make tmp gdf_line
      gdf_line = gpd.GeoDataFrame({"geometry":[linestring]})
      x_min, y_min, x_max, y_max = gdf_line.total_bounds
    
      # Create the raster dataset
      rows = math.ceil((y_max - y_min) / resolution)
      cols = math.ceil((x_max - x_min) / resolution)
      if rows ==0:
        rows=1
      if cols==0:
        cols=1
    
      #rasterio.transform.from_origin(west, north, xsize, ysize)
      new_transform = rasterio.transform.from_origin(x_min, y_max, resolution, resolution)
    
      # Rasterize vector using the shape and coordinate system of the raster
      rasterized = rasterio.features.rasterize(geom,
                                      out_shape = (rows, cols),
                                      fill = 0,
                                      out = None,
                                      transform = new_transform,
                                      all_touched = False,
                                      default_value = 1,
                                      dtype = "uint8")
    
      return rasterized #ndarray
    
    
    #tmp_dirに入れる
    tmp_dir = out_dir + os.sep + "tmp"
    os.makedirs(tmp_dir,exist_ok=True)
    
    src = fiona.open(line_shp_path)
    crs = src.crs
    driver = src.driver
    
    merged_geometries = shapely.ops.linemerge([shapely.geometry.shape(feature["geometry"]) for feature in src])
    
    schema = {
        "geometry": merged_geometries.geom_type,
        "properties": {
            "length": "float"
        }}
    
    
    #分離
    data_merged = {"geometry":[merged_geometries]}
    gdf_merged = gpd.GeoDataFrame(data_merged, crs = "EPSG:32648")
    
    
    """#ラスター化(def使わず)"""
    
    res = 1
    
    geom = gpdf.geometry
    #make tmp gdf_line
    gdf_line = gdf_merged
    x_min, y_min, x_max, y_max = gdf_line.total_bounds
    
    # Create the raster dataset
    rows = math.ceil((y_max - y_min) / res)
    cols = math.ceil((x_max - x_min) / res)
    if rows ==0:
      rows=1
    if cols==0:
      cols=1
    
    #rasterio.transform.from_origin(west, north, xsize, ysize)
    new_transform = rasterio.transform.from_origin(x_min, y_max, res, res)
    
    # Rasterize vector using the shape and coordinate system of the raster
    rasterized = rasterio.features.rasterize(geom,
                                    out_shape = (rows, cols),
                                    fill = 0,
                                    out = None,
                                    transform = new_transform,
                                    all_touched = False,
                                    default_value = 1,
                                    dtype = "uint8")
    
    # plt.imshow(rasterized, cmap='viridis')
    
    """#3by3ウィンドウを取り出す."""
    
    #長さがresolution*3ウィンドウサイズ以下の場合は何もしない
    windowsize = 3
    res = 1
    sub_shape = (windowsize, windowsize)
    
    lin_arr = rasterized
    
    view_shape = tuple(np.subtract(lin_arr.shape, sub_shape) + 1) + sub_shape #np.subtract: 2つのarrayの差分を得る, #端は落ちてる #(130, 145, 3, 3)
    arr_view = as_strided(lin_arr, view_shape, lin_arr.strides* 2) #a.stridesで(行方向,列方向)の必要なバイト数*2d（全体とウィンドウのスライディング、ぽい）
    arr_view = arr_view.reshape((-1,) + sub_shape) #np.reshape(-1): 1行にする　これで3*3のリストになる #次の行が続く形になると思う
    
    south_list =[]
    east_list =[]
    for view in arr_view:
    # view = np.array([[1, 0,0], [0, 1, 1],[1, 0, 0]]) #for debug
    #真ん中を取得
      center = view[1,1]
      if center ==0:
        continue
      else:
        right = view[1,2]
        if right ==1:
          east_list.append(1)
        else:
          down = view[2,1]
          if down ==1:
            south_list.append(1)
          else:
            direction = "tmp"
    
    if len(east_list) != len(south_list):
      larger_indx = [len(east_list), len(south_list)].index(max(len(east_list), len(south_list)))
      direction = ["east", "south"][larger_indx]
    else:
      direction = "east"
    
    gpdf["direction"] = direction
    
    
    filename = os.path.basename(line_shp_path)[:-4]
    outfile = out_dir + "/" + filename + "_dire.shp"
    gpdf.to_file(outfile, crs = "EPSG:32648")
    
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )


if __name__=="__main__":
    main()

