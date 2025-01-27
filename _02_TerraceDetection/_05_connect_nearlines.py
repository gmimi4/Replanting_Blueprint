# -*- coding: utf-8 -*-
"""
Connect nearest line with a wide angle
"""

import os
from shapely.geometry import Point, LineString, Polygon,MultiPoint, MultiLineString
import geopandas as gpd
# import matplotlib.pyplot as plt
import numpy as np
import itertools
import glob
import time


def main(line_shp_path, out_dir):
    start = time.time()
    tmp_dir = os.path.dirname(out_dir) + os.sep +'_tmp'
    # clean tmp dir
    tmps = glob.glob(tmp_dir + os.sep + "*")
    for t in tmps:
        os.remove(t)
        

    filename = os.path.basename(line_shp_path)[:-4]
    
    gpdf = gpd.read_file(line_shp_path)
    
    """#lines to single feature
    """
    def multi2single(gpdf_test):
        gpdf_multiline = gpdf_test[gpdf_test.geometry.type == 'MultiLineString']
    
        exploded_all = gpdf_test.explode()
        exploded_reset = exploded_all.reset_index()
        columns_to_drop = ['level_0','level_1']
        gdf_dropped = exploded_reset.drop(columns=columns_to_drop)
    
        return gdf_dropped
    
    multi_rows = gpdf[gpdf.geometry.type == 'MultiLineString']
    
    if len(multi_rows) >0:
      single_lines = multi2single(gpdf)
      lines = list(single_lines.geometry.values)
    else:
      lines = [line.geometry for i,line in gpdf.iterrows()]

    
    """Angle def"""
    def unit_vector(vector):
        """ Returns the unit vector of the vector.  """
        return vector / np.linalg.norm(vector)
    
    def angle_between(v1, v2):
        v1_u = unit_vector(v1)
        v2_u = unit_vector(v2)
        return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))
    
    def angle_between_intersection(li1,li2,po):
      line_1_x, line_1_y = li1.coords.xy[0], li1.coords.xy[1] #x,yのarray
      line_2_x, line_2_y = li2.coords.xy[0], li2.coords.xy[1] #
      point_x, point_y = po.coords.xy[0], po.coords.xy[1]
      dist_1 = np.sqrt((np.array(line_1_x) - np.array(point_x))**2 + (np.array(line_1_y) - np.array(point_y))**2)
      dist_2 = np.sqrt((np.array(line_2_x) - np.array(point_x))**2 + (np.array(line_2_y) - np.array(point_y))**2)
      # get index
      arg_indx_1 = dist_1.argsort()#[::-1]
      idx_1 = np.where(arg_indx_1==1)[0]
      arg_indx_2 = dist_2.argsort()#[::-1]
      idx_2 = np.where(arg_indx_2==1)[0]
    
      vec_1_ = (np.array(line_1_x)[idx_1] - np.array(point_x),  np.array(line_1_y)[idx_1] - np.array(point_y))
      vec_1 = (vec_1_[0][0], vec_1_[1][0])
      vec_2_ = (np.array(line_2_x)[idx_2] - np.array(point_x),  np.array(line_2_y)[idx_2] - np.array(point_y))
      vec_2 = (vec_2_[0][0], vec_2_[1][0])
      angle = angle_between(vec_1, vec_2)
    
      return angle
    
    """#connecting lines     """

    #### Plot for check
    # fig = plt.figure(figsize=(5, 5))
    # ax1 = fig.add_subplot(1,1,1)
    ### poly
    # x,y = terr_use.exterior.xy
    # ax1.plot(x, y, color='grey', label='Polygon')
    ### point
    # ax1.plot(p0.xy[0][0], p0.xy[1][0], "o", color="black")
    # ax1.plot(p0_.xy[0][0], p0_.xy[1][0], "o", color="black")
    # ax1.plot(p0.xy[0][0], p0.xy[1][0], "o", color="black")
    # ax1.plot(first_ext_coords[0], first_ext_coords[1], "o", color="black")
    
    # for p in points_all_T1_set:
    #     ax1.plot(p.xy[0][0], p.xy[1][0], "o", color='orange')
    ### line
    # ax1.plot(linestring.xy[0], linestring.xy[1], color='green')
    # ax1.plot(inters.xy[0], inters.xy[1], color='red')
    # ax1.plot(last_coords[0], last_coords[1], color='blue')
    # ax1.plot(inters.geometry.values[0].xy[0], inters.geometry.values[0].xy[1], color='black')
    
    
    ### rev: connect by 5 m length of both edges (if short line 5>, collect 5 points)
    def least_square_line(linestring):
      x_0,y_0 = linestring.coords.xy
      p0 = Point(x_0[0], y_0[0])
      p0_ = Point(x_0[-1], y_0[-1])
      
      if linestring.length >5:
          # make buffer from edge for intersecting line          
          p0_buff, p0_buff_ = p0.buffer(5), p0_.buffer(5)
          inters = linestring.intersection(p0_buff)
          inters_ = linestring.intersection(p0_buff_)
          try:
              first_coords = inters.coords.xy #tupple of arrayx, arrayy # inters.geom_type
              last_coords = inters_.coords.xy
          except: #If Multilinestring, opt 5 points
              first_coords = (x_0[0:5], y_0[0:5])
              last_coords = (x_0[-5:-1], y_0[-5:-1])
      else:    
          ## 5 points
          first_coords = (x_0[0:5], y_0[0:5])
          last_coords = (x_0[-5:-1], y_0[-5:-1])
          
      first_x, first_y = np.array(first_coords[0]), np.array(first_coords[1]) #original line vertex
      last_x,  last_y = np.array(last_coords[0]), np.array(last_coords[1])
    
      first_A = np.stack([first_x, np.ones(len(first_x))]).T
      m_first, c_first = np.linalg.lstsq(first_A, first_y, rcond=None)[0]
      last_A = np.stack([last_x, np.ones(len(last_x))]).T
      m_last, c_last = np.linalg.lstsq(last_A, last_y, rcond=None)[0]
    
      ## obtain extrimity coords of least sq lines
      first_leastline_ext = m_first*(first_x[0]) + c_first #sq line vertex （ｙ）
      last_leastline_ext = m_last*(last_x[-1]) + c_last
    
      first_ext_coords = (first_x[0], first_leastline_ext) #(x,LSQ(x))
      last_ext_coords = (last_x[-1], last_leastline_ext)
      
      first_ext_point = Point(first_ext_coords)
      last_ext_point = Point(last_ext_coords)
    
      # return first_ext_coords, last_ext_coords, [m_first, c_first], [m_last, c_last] #SQ
      return first_ext_point, last_ext_point, [m_first, c_first], [m_last, c_last] #SQ
    
    
    
    def xy_to_Linestring(xarray, yarray):
      cooo = [(x,y) for x,y in zip(xarray, yarray)]
      line_sq_string = LineString(cooo)
    
      return line_sq_string
    
    
    
    def connected_list(linestring_list):

      connected_line =[]
      ori_lines = []
    
      li_li_distance = 5
      angle_thre = 45
    
      # Check the distance between two lines. 
      # Distance from endpoint of least square line to another line. if distance < threshold, connect them
      for line1, line2 in itertools.combinations(linestring_list, 2): #２つ取り出す組み合わせ(順不同)
    
        ## make endpoints
        p1near_sq, p1far_sq, mc1_first, mc1_last = least_square_line(line1) #LSQ points
        p1near = Point(line1.coords.xy[0][0], line1.coords.xy[1][0]) #line1
        p1far = Point(line1.coords.xy[0][-1], line1.coords.xy[1][-1])
    
        line1_x_first = np.array(line1.coords.xy[0][0:5])
        line1_x_last = np.array(line1.coords.xy[0][-6:-1])
    
        p2near_sq, p2far_sq, mc2_first, mc2_last = least_square_line(line2)
        p2near = Point(line2.coords.xy[0][0], line2.coords.xy[1][0]) #line2
        p2far = Point(line2.coords.xy[0][-1], line2.coords.xy[1][-1])
    
        line2_x_first = np.array(line2.coords.xy[0][0:5])
        line2_x_last = np.array(line2.coords.xy[0][-6:-1])
        
        sq_point_dic = {p1near_sq: p1near, p2near_sq: p2near, p1far_sq: p1far, p2far_sq: p2far}
    
        # Distance from original endpoint -> sq
        distance1 = p1near_sq.distance(p2near_sq)
        distance2 = p1near_sq.distance(p2far_sq)
        distance3 = p1far_sq.distance(p2near_sq)
        distance4 = p1far_sq.distance(p2far_sq)
        
        distance_dic = {distance1:[p1near_sq, p2near_sq], distance2: [p1near_sq, p2far_sq],
                       distance3:[p1far_sq, p2near_sq], distance4: [p1far_sq, p2far_sq]}
        
        distance_list = [distance1, distance2, distance3, distance4]
        distance = min(distance_list)

    
        if distance >0 and distance < li_li_distance:
          #Collect two points and make a new Line string
          pointlist = distance_dic[distance]
          new_pp_sq = distance_dic[distance]
          new_pp = [sq_point_dic[new_pp_sq[0]], sq_point_dic[new_pp_sq[1]]]
          
          line1_sq_y = mc1_first[0]*line1_x_first + mc1_first[1]
          line1_sq = xy_to_Linestring(line1_x_first, line1_sq_y)

          p0 = new_pp_sq[0]
          p02 = new_pp_sq[1]
    
          new_line_sq = LineString(new_pp_sq)
          new_line = LineString(new_pp)
          ##angle between new line and original line should not be small
    
          angle1 = angle_between_intersection(new_line_sq, line1_sq, p0)

          if (angle1 > (180 -angle_thre)) and (angle1 < (180+angle_thre)): #135°- 225°    
            connected_line.append(new_line)
            ori_lines.append(line1) 
            ori_lines.append(line2)
          else:
            pass
    
        else:
          pass
    
      return connected_line, ori_lines
    
    
    """ # add new line"""
    new_line_list, ori_lines_list = connected_list(lines)
    
    line_results = lines + new_line_list
    

    gdf_export = gpd.GeoDataFrame(geometry=line_results)
    gdf_export = gdf_export.set_crs(gpdf.crs, allow_override=True)
    gdf_export["length"] = gdf_export.geometry.length
    
    outfile = os.path.join(out_dir, f"_{filename}_connect_sq.shp")
    gdf_export.to_file(outfile)
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )


if __name__=="__main__":
    main()