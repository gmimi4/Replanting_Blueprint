# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 11:49:38 2024

@author: chihiro
"""
import os
import geopandas as gpd

def main(line_shp, out_dir, road_shp):
    # line_shp = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\11_connect_lines\centerlines_45_cut_cut2ls_merge_45_connect_sq2_road_over3.shp"
    # road_shp = r"D:\Malaysia\01_Brueprint\11_Roads\roads_manual_poly.shp"
    # out_dir= r"D:\Malaysia\01_Brueprint\12_Pairing_terraces\1_divided_lines"
    
    gdf_line = gpd.read_file(line_shp)
    gdf_road = gpd.read_file(road_shp)
    
    #roadポリゴンでlineをクリップ
    for i,row in gdf_road.iterrows():
        clipped_lines = gpd.clip(gdf_line, row.geometry)
        outfile = out_dir + f"\\lines_{i}.shp"
        clipped_lines.to_file(outfile, crs="EPSG:32648")


if __name__=="__main__":
    main()
