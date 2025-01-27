# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 11:49:38 2024

@author: chihiro
"""
import os
import geopandas as gpd

def main(line_shp, out_dir, road_shp):

    
    gdf_line = gpd.read_file(line_shp)
    gdf_road = gpd.read_file(road_shp)
    
    #Clip lines by road
    for i,row in gdf_road.iterrows():
        clipped_lines = gpd.clip(gdf_line, row.geometry)
        if len(clipped_lines)>0:
            outfile = out_dir + os.sep + f"lines_{i}.shp"
            clipped_lines.to_file(outfile)


if __name__=="__main__":
    main()
