# -*- coding: utf-8 -*-
"""
Created on Fri Apr 19 15:37:13 2024

@author: chihiro
"""

import os
import glob
import geopandas as gpd
import pandas as pd
import fiona
from shapely.geometry import shape
from shapely.geometry import Polygon
import numpy as np
from shapely.geometry import Point, LineString, Polygon,MultiPoint, MultiLineString
import time


# line_dir = r'D:\Malaysia\01_Brueprint\09_Terrace_detection\9_filterd_line'
# out_dir = line_dir + os.sep + '_divided'
# os.makedirs(out_dir, exist_ok=True)

def main(line_dir, out_dir):
    start = time.time()
    
    lines_list = glob.glob(line_dir + os.sep + "*.shp")
    
    if len(lines_list) >1:
        #merge all lines
        gpdf_list =[]
        for line in lines_list:
          gdf_line = gpd.read_file(line)
          gpdf_list.append(gdf_line)
        gpdf = gpd.GeoDataFrame(pd.concat(gpdf_list), columns=["length","geometry"])
    
    elif len(lines_list) ==1:
        line_shp_path = lines_list[0]
        gpdf = gpd.read_file(line_shp_path)
        
    else:
        print("no lines")
        
    
    # MultiLineStringがあれば処理をする
    multi_rows = gpdf[gpdf.geometry.type == 'MultiLineString']
    
    def multi2single(gpdf_test):
        exploded_all = gpdf_test.explode()
        exploded_reset = exploded_all.reset_index()
        columns_to_drop = ['level_0','level_1']
        gdf_dropped = exploded_reset.drop(columns=columns_to_drop)
    
        return gdf_dropped
    
    
    if len(multi_rows) >0:
      single_lines = multi2single(gpdf)
      lines = list(single_lines.geometry.values)
    else:
      lines = [shape(line.geometry) for line in fiona.open(line_shp_path,'r')] #multiLinestringがなかったとき
    
    
    """ #Prepare 40000 m2 grid to divide #any length and height and width ok but 40000m2 will better
    """
    xmin, ymin, xmax, ymax = gpdf.total_bounds
    hei = 100
    wide = 400
    cols = list(np.arange(xmin, xmax + wide, wide))
    rows = list(np.arange(ymin, ymax + hei, hei))
    
    polygons = []
    for x in cols[:-1]:
        for y in rows[:-1]:
            polygons.append(Polygon([(x,y), (x+wide, y), (x+wide, y+hei), (x, y+hei)]))
    
    grid = gpd.GeoDataFrame({'geometry':polygons})
    #check
    # grid.plot(color='None')
    
    """ # Obtain centroid of lines
    """
    filename = os.path.basename(line_shp_path)[:-4]
    length = len(str(len(grid)))
    
    for i,g in grid.iterrows():
      line_centers = gpdf.geometry.centroid
      bool_idx = line_centers.within(g.geometry) #bool
      line_in = gpdf[bool_idx]
      outfilename = os.path.join(out_dir, filename +f"_{str(i).zfill(length)}.shp")
      line_in.to_file(outfilename)
      
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )
  

if __name__ =="__main__":
    main()
  
  