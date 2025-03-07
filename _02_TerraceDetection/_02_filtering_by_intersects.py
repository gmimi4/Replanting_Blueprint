# -*- coding: utf-8 -*-

import os,sys
from shapely.geometry import Point, LineString, Polygon,MultiPoint, MultiLineString
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import itertools
import time


def main(line_shp_path, out_dir, minlen):
    start = time.time() 
    
    # MultiLineString to single
    def multi2single(gpdf_test):
        
        exploded_all = gpdf_test.explode()
        exploded_reset = exploded_all.reset_index()
        columns_to_drop = ['level_0','level_1']
        gdf_dropped = exploded_reset.drop(columns=columns_to_drop)
    
        return gdf_dropped
    
    gpdf = gpd.read_file(line_shp_path)
    gpdf = gpdf[gpdf.geometry!=None] #delete None geometry
    
    # Find multiLineStrings
    multi_rows = gpdf[gpdf.geometry.type == 'MultiLineString']
    
    if len(multi_rows) >0:
      single_lines = multi2single(gpdf)
      lines = list(single_lines.geometry.values)
    else: # no multistrings
      lines = gpdf.geometry.to_list()
    
    
    """#intersecting points list"""        
    inters = []
    
    for line1, line2 in itertools.combinations(lines,2): #Combination of two lines (no order)
      if line1.intersects(line2):
        inter = line1.intersection(line2)
        if "Point" == inter.geom_type: #inter.type:
          inters.append(inter)
        elif "MultiPoint" == inter.geom_type:
          inters.extend([Point(pt.x, pt.y) for pt in inter.geoms])
        elif "MultiLineString" == inter.geom_type:
          multiLine = [line for line in inter.geoms]
          first_coords = multiLine[0].coords[0]
          last_coords = multiLine[len(multiLine)-1].coords[1]
          inters.append(Point(first_coords[0],first_coords[1]))
          inters.append(Point(last_coords[0],last_coords[1]))
        elif "GeometryCollection" == inter.geom_type:
          for geom in inter:
            if "Point" == geom.type:
              inters.append(geom)
            elif "MultiPoint" == geom.type: #ok??
              inters.extend([pt for pt in geom])
            elif "MultiLineString" == geom.type:
              multiLine = [line for line in geom]
              first_coords = multiLine[0].coords[0]
              last_coords = multiLine[len(multiLine)-1].coords[1]
              inters.append(Point(first_coords[0],first_coords[1]))
              inters.append(Point(last_coords[0],last_coords[1]))
    
    
    
    """#Filtering by angle"""
    def unit_vector(vector):
        """ Returns the unit vector of the vector.  """
        return vector / np.linalg.norm(vector) #np.linalg.norm() #default is None: Eucledean
    
    def angle_between(v1, v2):
        v1_u = unit_vector(v1)
        v2_u = unit_vector(v2)
        return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))) #np.clip: min, max
    
    """Extract short lines (suspicious lines) and the intersecting lines"""
    inters_pair = []
    # Find two lines and one intersection
    for line1, line2 in itertools.combinations(lines,2):
      if line1.intersects(line2):
        inter = line1.intersection(line2)
        if "Point" == inter.type:
          inters_pair.append([inter, line1,line2])
        else:
          pass
    
    
    # Exclude pair of long lines, #allow longer than 15m
    inters_pair2 = []
    inters2 = []
    for i in  inters_pair:
      if i[1].length > minlen and i[2].length > minlen:
        pass
      else:
        inters_pair2.append(i)
        inters2.append(i[0])
    
    
    """Extract from the nearest and farthest coordinates"""
    error_lines = []
    angle_thre = 45
    
    #from the nearest
    for pair in inters_pair2:
      #Extract the two coordinates closest to the intersection from each line and create a straight line
      line_1_x, line_1_y = pair[1].coords.xy[0], pair[1].coords.xy[1]
      line_2_x, line_2_y = pair[2].coords.xy[0], pair[2].coords.xy[1]
      point_x, point_y = pair[0].coords.xy[0], pair[0].coords.xy[1]
      dist_1 = np.sqrt((np.array(line_1_x) - np.array(point_x))**2 + (np.array(line_1_y) - np.array(point_y))**2)
      dist_2 = np.sqrt((np.array(line_2_x) - np.array(point_x))**2 + (np.array(line_2_y) - np.array(point_y))**2)
      # get index
      arg_indx_1 = dist_1.argsort() #if Sort in order of distance (from farthest to nearest) [::-1]
      idx_1 = np.where(arg_indx_1==1)[0] #from intersecting point to the furtherst Linestring coord
      arg_indx_2 = dist_2.argsort()#[::-1]
      idx_2 = np.where(arg_indx_2==1)[0]
    
      # make new vector from intersection
      vec_1_ = (np.array(line_1_x)[idx_1] - np.array(point_x),  np.array(line_1_y)[idx_1] - np.array(point_y))
      vec_1 = (vec_1_[0][0], vec_1_[1][0])
      vec_2_ = (np.array(line_2_x)[idx_2] - np.array(point_x),  np.array(line_2_y)[idx_2] - np.array(point_y))
      vec_2 = (vec_2_[0][0], vec_2_[1][0])
      angle = angle_between(vec_1, vec_2)
    
      if angle > angle_thre and angle < (180-angle_thre):
        test_dic = {1:pair[1].length, 2:pair[2].length}
        min_test = min(pair[2].length, pair[1].length) #error with short line if angle is large
        error_index = [k for k,v in test_dic.items() if v== min_test][0]
        error_line = pair[error_index]
        error_lines.append(error_line) #error lineを集める
    
    
    # from farthest
    for pair in inters_pair2:
      line_1_x, line_1_y = pair[1].coords.xy[0], pair[1].coords.xy[1]
      line_2_x, line_2_y = pair[2].coords.xy[0], pair[2].coords.xy[1]
      point_x, point_y = pair[0].coords.xy[0], pair[0].coords.xy[1]
      dist_1 = np.sqrt((np.array(line_1_x) - np.array(point_x))**2 + (np.array(line_1_y) - np.array(point_y))**2)
      dist_2 = np.sqrt((np.array(line_2_x) - np.array(point_x))**2 + (np.array(line_2_y) - np.array(point_y))**2)

      arg_indx_1 = dist_1.argsort()[::-1] 
      idx_1 = np.where(arg_indx_1==1)[0]
      arg_indx_2 = dist_2.argsort()[::-1]
      idx_2 = np.where(arg_indx_2==1)[0]
    
      vec_1_ = (np.array(line_1_x)[idx_1] - np.array(point_x),  np.array(line_1_y)[idx_1] - np.array(point_y))
      vec_1 = (vec_1_[0][0], vec_1_[1][0])
      vec_2_ = (np.array(line_2_x)[idx_2] - np.array(point_x),  np.array(line_2_y)[idx_2] - np.array(point_y))
      vec_2 = (vec_2_[0][0], vec_2_[1][0])
      angle = angle_between(vec_1, vec_2)
    
      if angle > angle_thre and angle < (180-angle_thre):
        test_dic = {1:pair[1].length, 2:pair[2].length}
        min_test = min(pair[2].length, pair[1].length)
        error_index = [k for k,v in test_dic.items() if v== min_test][0]
        error_line = pair[error_index]
        error_lines.append(error_line) # collect error lines
    
    
    # lines refining
    lines_by_angle = list(set(lines)^set(error_lines))
    
    
    # #Plot
    # linestring_x_ =[]
    # linestring_y_ =[]
    
    # for i in range(len(lines_by_angle)):
    #   line_x, line_y = lines_by_angle[i].xy
    #   linestring_x_.append(line_x)
    #   linestring_y_.append(line_y)
    
    # #Plotting
    # fig, ax = plt.subplots(figsize=(10,8))
    
    # #lines
    # for i in range(len(lines_by_angle)):
    #   ax.plot(linestring_x_[i], linestring_y_[i], color = 'aquamarine', label='Linestring')
    
    # #points
    # for i in range(len(inters2)):
    #   ax.plot(inters2[i].x, inters2[i].y, 'ro', label='Point')
    
    """#Export to shp"""
    gdf_angle = gpd.GeoDataFrame(geometry=lines_by_angle)
    gdf_angle = gdf_angle.set_crs(gpdf.crs, allow_override=True)
    gdf_angle["length"] = gdf_angle.geometry.length
    
    outfile = os.path.join(out_dir, os.path.basename(line_shp_path)[:-4] +f"_{angle_thre}.shp")
    gdf_angle.to_file(outfile)
    
    end = time.time()
    time_diff = end - start
    print(time_diff/60, "min") 

if __name__=="__main__":
    main()



