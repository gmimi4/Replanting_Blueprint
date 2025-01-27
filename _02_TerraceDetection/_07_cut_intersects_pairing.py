# -*- coding: utf-8 -*-
"""Cut the shorted lines by 1m if 3 lines intersect
"""

import os
from shapely.geometry import Point, LineString, Polygon,MultiPoint, MultiLineString
import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np
import itertools
# import glob
import collections


def main(line_shp_path, out_dir):
    def multi2single(gpdf_test):
        gpdf_multiline = gpdf_test[gpdf_test.geometry.type == 'MultiLineString']
    
        exploded_all = gpdf_test.explode()
        exploded_reset = exploded_all.reset_index()
        columns_to_drop = ['level_0','level_1']
        gdf_dropped = exploded_reset.drop(columns=columns_to_drop)
    
        return gdf_dropped
    
    """#lines to single feature
    """
    
    gpdf = gpd.read_file(line_shp_path)
    # make sure gpdf does not have none row
    gpdf = gpdf[gpdf.geometry != None]
    
    multi_rows = gpdf[gpdf.geometry.type == 'MultiLineString']
    
    if len(multi_rows) >0:
      single_lines = multi2single(gpdf)
      lines = list(single_lines.geometry.values)
    else: #no multiLinestring
      lines = [g.geometry for i,g in gpdf.iterrows()]
     
    
    """#Collect 3 intersecting lines and intersection"""
    
    inters_pair = []
    inters_lines = []

    for line1, line2,line3 in itertools.combinations(lines,3):
      if line1.intersects(line2) and line1.intersects(line3) and line2.intersects(line3):
        inter1 = line1.intersection(line2)
        inter2 = line1.intersection(line3)
        inter3 = line2.intersection(line3)
        if inter1==inter2 and inter2==inter3 and "Point" == inter1.type:
          inters_pair.append([inter1, line1,line2, line3])
          inters_lines.append([line1,line2,line3])
        elif "MultiPoint" == inter1.type or "MultiPoint" == inter2.type or "MultiPoint" == inter3.type:
          inters_pair.append([inter1, line1,line2, line3])
          inters_lines.append([line1,line2,line3])
        else:
          pass
    
    """#collect not-selected lines"""
    individual_inters_lines = []
    for lis in inters_lines:
      for l in lis:
        individual_inters_lines.append(l)
    
    individual_inters_lines_set = set(individual_inters_lines)
    
    line_non_inters = list(set(individual_inters_lines_set)^set(lines))
    
    """#cut line by 1m from intersection """
    
    buff_distance = 1
    cut_lines =[]
    cut_lines_oris =[]
    long_lines =[]
    
    for i,lins in enumerate(inters_lines):
      tmp_list =[li.length for li in lins]
      tmp_array = np.array(tmp_list)
      index_sort = tmp_array.argsort()
      shortest_id_list = list(index_sort[0:1])
      target_lines = [lins[i] for i in shortest_id_list]
     # buffer
      inter_point = inters_pair[i][0]
      buff_poly = inter_point.buffer(buff_distance)
    
      cut_tar_lines =[]
      cut_line_ori =[]
      data_poly = {"geometry":[buff_poly]}
      gdf_buff = gpd.GeoDataFrame(data_poly, geometry="geometry")
      for target in target_lines:
        data_line = {"geometry":[target]}
        gdf_tar_line = gpd.GeoDataFrame(data_line, geometry="geometry")
        cut_tar_line_ori = target
        cut_tar_line = gdf_tar_line.difference(gdf_buff).values[0]
        cut_tar_lines.append(cut_tar_line)
        cut_line_ori.append(cut_tar_line_ori)
    
      if len(shortest_id_list) == 2:
        long_line = [li for i,li in enumerate(lins) if i == index_sort[2]] #index_sort[2]
        long_lines.append(long_line)
    
      if len(shortest_id_list) == 1:
        long_line = [li for i,li in enumerate(lins) if i != shortest_id_list[0]]
        long_lines.append(long_line)
    

      cut_lines.append(cut_tar_lines)
      cut_lines_oris.append(cut_line_ori)
    
    """to individuals"""
    
    cut_lines_individual = []
    for cut in cut_lines:
      for c in cut:
        cut_lines_individual.append(c)
    
    cut_lines_ori_individual = []
    for cut in cut_lines_oris:
      for c in cut:
        cut_lines_ori_individual.append(c)
    
    long_lines_individual = []
    for lon in long_lines:
      for l in lon:
        long_lines_individual.append(l)
    
    """#Correct overlapping of shortest lines """
    cut_collections = collections.Counter(cut_lines_ori_individual)
    same_short = [k for k,c in cut_collections.items() if c>1]
    
    same_idx_list = []
    for same in same_short:
      idx_list =[]
      for i,ori in enumerate(inters_lines):
        try:
          same_idx = [ori.index(same)]
          if len(same_idx) >0:
            idx_list.append(i)
        except ValueError:
          pass
      idx_list_set = list(set(idx_list))
      same_idx_list.append(idx_list_set)
    
    
    """Collect Overlapping line to replace with cut ones"""
    overlays_list = []
    for idxs in same_idx_list:
      overlays=[]
      for i in idxs:
        overlays.append(cut_lines[i][0])
      overlays_list.append(overlays)
    
    overlays_list_individual = [item for sublist in overlays_list for item in sublist]

    
    overlay_part =[]
    for over in overlays_list:
      part = over[0].intersection(over[1])
      part2 = part.intersection(over[0])
      overlay_part.append(part2)
    
    #Empty
    overlay_part = [o for o in overlay_part if not o.is_empty] #to be used
    
    #correct Multistring
    overlay_results=[]
    for mul in overlay_part:
        checktype = mul.geom_type
        if checktype =="MultiLineString":
          test_data = {"geometry":[mul]}
          test_part_gdf = gpd.GeoDataFrame(test_data, geometry="geometry")
          test_gdf = multi2single(test_part_gdf)
    
          # to one Linestring
          coords_list = []
          for i,l in test_gdf.iterrows():
            coordss = list(l.geometry.coords)
            coords_list.append(coordss)
    
          connected_coords = []
          for co in coords_list:
            connected_coords.append(co[0])
    
          connected_line = LineString(connected_coords)
          overlay_results.append(connected_line)
        
        else:
            overlay_results.append(mul)
    
    # overlay_results #to be used
    
    """Replace with overlapping line"""
    cut_line_remove = list(set(cut_lines_individual) - set(overlays_list_individual))
    #add overlapping line
    cut_line_results = cut_line_remove + overlay_results
    
    
    """#delete long if cut in another pairing"""
    long_set = list(set(long_lines_individual) - set(cut_lines_ori_individual))
        
    long_clean = long_set
    
    
    """#concat"""
    lines_after_cut = line_non_inters + cut_line_results + long_clean
    
    #Plot for check
    # fig = plt.figure(figsize=(8, 8))
    
    # #----------------
    # ax1 = fig.add_subplot(2,2,3)
    # name = cut_line_results
    # ax1.set_title("cut_line_results")
    # linestring_x_ =[]
    # linestring_y_ =[]
    # for i in range(len(name)):
    #   line_x, line_y = name[i].xy
    #   linestring_x_.append(line_x)
    #   linestring_y_.append(line_y)
    # #lines
    # for i in range(len(name)):
    #   ax1.plot(linestring_x_[i], linestring_y_[i], color = 'aquamarine', label='Linestring')
    
    # #----------------
    # ax2 = fig.add_subplot(2,2,4)
    # ax2.set_title("long_set")
    # name = long_set
    # linestring_x_ =[]
    # linestring_y_ =[]
    # for i in range(len(name)):
    #   line_x, line_y = name[i].xy
    #   linestring_x_.append(line_x)
    #   linestring_y_.append(line_y)
    # #lines
    # for i in range(len(name)):
    #   ax2.plot(linestring_x_[i], linestring_y_[i], color = 'aquamarine', label='Linestring')
    
    # #----------------
    # ax3 = fig.add_subplot(2,2,1)
    # ax3.set_title("Original")
    # name = lines
    # linestring_x_ =[]
    # linestring_y_ =[]
    # for i in range(len(name)):
    #   line_x, line_y = name[i].xy
    #   linestring_x_.append(line_x)
    #   linestring_y_.append(line_y)
    # #lines
    # for i in range(len(lines)):
    #   ax3.plot(linestring_x_[i], linestring_y_[i], color = 'aquamarine', label='Linestring')
    
    
    # #----------------
    # ax4 = fig.add_subplot(2,2,2)
    # ax4.set_title("lines_after_cut")
    # name = lines_after_cut
    # linestring_x_ =[]
    # linestring_y_ =[]
    # for i in range(len(name)):
    #   line_x, line_y = name[i].xy
    #   linestring_x_.append(line_x)
    #   linestring_y_.append(line_y)
    # #lines
    # for i in range(len(name)):
    #   ax4.plot(linestring_x_[i], linestring_y_[i], color = 'aquamarine', label='Linestring')
    
    # #points
    # for a in [ax1,ax2,ax3,ax4]:
    #   for i in range(len(inters_pair)):
    #     a.plot(inters_pair[i][0].x, inters_pair[i][0].y, 'ro', label='Point')
    
    """#Export to shp"""
    gdf_export = gpd.GeoDataFrame(geometry=lines_after_cut)
    gdf_export = gdf_export.set_crs(gpdf.crs, allow_override=True)
    gdf_export["length"] = gdf_export.geometry.length
    
    ### Eliminate Points
    gdf_export = gdf_export[gdf_export.geometry.type != 'Point']
    
    outfile = os.path.join(out_dir, os.path.basename(line_shp_path)[:-4] +f"_cut.shp")
    gdf_export.to_file(outfile)

if __name__=="__main__":
    main()