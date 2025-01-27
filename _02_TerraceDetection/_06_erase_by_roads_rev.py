# -*- coding: utf-8 -*-
"""
Erase lines overlapping with roads
"""

import os,sys
import geopandas as gpd
import glob
import pandas as pd
import time


def main(in_dir, out_dir, road_line):
    start = time.time()
    
    line_shps = glob.glob(in_dir+ os.sep + "*.shp")
    line_gdfs = [gpd.read_file(shp) for shp in line_shps]
    
    outfile = os.path.basename(line_shps[0])[:-4] + "_road.shp"
    
    
    """#merge"""
    line_merge = pd.concat(line_gdfs)
    
    """#erase by road"""
    #2.5 m buffer supposed to road width
    gdf_roadline = gpd.read_file(road_line)
    ser_road = gdf_roadline.buffer(2.5)
    gdf_road = gpd.GeoDataFrame({"geometry":ser_road})
    #Export
    # gdf_road.to_file(os.path.dirname(road_line) + os.sep + "road_buff25.shp") #crs="EPSG:32648"
    
    gdf_erasedline = gpd.overlay(line_merge, gdf_road, how='difference')
    
    """#Multipart to single part"""
    def multi2single(gpdf_test):
        gpdf_multiline = gpdf_test[gpdf_test.geometry.type == 'MultiLineString']
    
        exploded_all = gpdf_test.explode() #index_parts=True
        exploded_reset = exploded_all.reset_index()
        columns_to_drop = ['level_0','level_1']
        gdf_dropped = exploded_reset.drop(columns=columns_to_drop)
    
        return gdf_dropped
    
    multi_rows = gdf_erasedline[gdf_erasedline.geometry.type == 'MultiLineString']
    
    if len(multi_rows) >0:
      single_lines = multi2single(gdf_erasedline)
      lines = list(single_lines.geometry.values)
    else:
      lines = [line.geometry for i,line in gdf_erasedline.iterrows()]
    
    
    """#if delete short line (not applicable here)"""
    gdf_single = gpd.GeoDataFrame({"geometry":lines})
    gdf_single = gdf_single.set_crs(gdf_roadline.crs, allow_override=True)
    
    gdf_single["length"] = gdf_single.geometry.length

    gdf_erasedline = gdf_single
    
    #Export
    gdf_erasedline.to_file(out_dir+ os.sep + outfile) #crs="EPSG:32648"
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )



if __name__=="__main__":
    main()