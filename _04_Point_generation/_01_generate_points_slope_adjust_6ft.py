# -*- coding: utf-8 -*-

import os
from shapely.geometry import Point, LineString, MultiLineString, Polygon,MultiPoint,MultiPolygon,LinearRing
# import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np
import math
import time


def main(line_shp_path, road_shp, out_dir):
    start = time.time()
    
    """gdf lines"""
    gdf_line = gpd.read_file(line_shp_path)
    
    """lines"""
    
    lines = gdf_line.geometry.tolist()
    
    """Roads  
    first point being 6 feet from the edge of the collection road.
    """
    
    gdf_road = gpd.read_file(road_shp)
    
    #buffer of road edge
    road_distance = 6*0.3048 #m
    road_buff = gdf_road.buffer(road_distance)
    gdf_road_buff = gpd.GeoDataFrame(geometry=road_buff)
    
    #Dissolve
    gdf_road_buff["tmp"] = 1
    gdf_road_dissolve = gdf_road_buff.dissolve(by='tmp')
    
    ### Polygon #use this
    buff_boundary = gdf_road_dissolve.geometry.values[0]
    
    
    """# def start point based on direction"""        
    def get_startpoint(linestring, direction):
      ## endpoint (smaller x)
      x_0,y_0 = linestring.coords.xy
      p00 = Point(x_0[0], y_0[0])
      p_1 = Point(x_0[-1], y_0[-1])
      if direction =="east":
        x_min_idx = [p00.x, p_1.x].index(min([p00.x, p_1.x]))
        p0 = [p00, p_1][x_min_idx]
      ## endpoint (larger y)
      if direction =="south":
        y_max_idx = [p00.y, p_1.y].index(max([p00.y, p_1.y]))
        p0 = [p00, p_1][y_max_idx]
    
      return p0
    
    ### end side too
    def get_startpoint_end(linestring, direction):
      x_0,y_0 = linestring.coords.xy
      p00 = Point(x_0[0], y_0[0])
      p_1 = Point(x_0[-1], y_0[-1])
      if direction =="east":
        x_min_idx = [p00.x, p_1.x].index(max([p00.x, p_1.x]))
        p0 = [p00, p_1][x_min_idx]
      if direction =="south":
        y_max_idx = [p00.y, p_1.y].index(min([p00.y, p_1.y]))
        p0 = [p00, p_1][y_max_idx]
        
      return p0
    
    """#def　point_from_6ft
    get intersection with Road buffer.
    If starting point (smaller x or larger y) is not within buff, p0 is original endpoint
    """
    class roadedge_6ft:
        def __init__(self, linestring, direction, gdf_buff = gdf_road_dissolve):
            self.linestring = linestring
            self.direction = direction
            gdf_buff = gdf_road_dissolve
            
        # make line at intersection with buffer
        def point_from_6ft(self):
        # def point_from_6ft(linestring, direction, gdf_buff=gdf_road_dissolve):
          buff_boundary = gdf_road_dissolve.geometry.values[0]
        
          ## original endpoints (smaller x)
          x_0,y_0 = self.linestring.coords.xy
          p00 = Point(x_0[0], y_0[0])
          p_1 = Point(x_0[-1], y_0[-1])
          if self.direction =="east":
            x_min_idx = [p00.x, p_1.x].index(min([p00.x, p_1.x]))
            p0 = [p00, p_1][x_min_idx]
          ## original endpoints (larger y)
          if self.direction =="south":
            y_max_idx = [p00.y, p_1.y].index(max([p00.y, p_1.y]))
            p0 = [p00, p_1][y_max_idx]
        
        
          if buff_boundary.contains(p0):
            inters = gdf_road_dissolve.intersection(self.linestring)
            try:
              endp1, endp2 = Point([inters.values[0].xy[0][0],inters.values[0].xy[1][0]]),  Point([inters.values[0].xy[0][-1],inters.values[0].xy[1][-1]]) #LineString #端点をつくる
              ori_tar = self.linestring
        
            except:
              if (inters.geom_type.values[0] == "MultiLineString"): #.all
                individual_lines = list(inters.values[0].geoms) #LineString list
                           
                # get line for starting point at the end
                oristarts_dic = {}
                oristarts_list = []
                if self.direction == "east":
                  for i in individual_lines:
                    ori_p0 = get_startpoint(i, "east")
                    oristarts_dic[ori_p0] = i
                    oristarts_list.append(ori_p0)
                  # compare ori endpoints
                  x_list = [x.xy[0] for x in oristarts_list] #xy[0][0]
                  x_min_idx = x_list.index(min(x_list))
                  p_key = [p for p in oristarts_list if p.xy[0] == x_list[x_min_idx]][0]
                  ori_tar = oristarts_dic[p_key]
                if self.direction == "south":
                  for i in individual_lines:
                    ori_p0 = get_startpoint(i, "south")
                    oristarts_dic[ori_p0] = i
                    oristarts_list.append(ori_p0)

                  y_list = [x.xy[1] for x in oristarts_list] #x.xy[0][1]
                  y_max_idx = y_list.index(max(y_list))
                  p_key = [p for p in oristarts_list if p.xy[1] == y_list[y_max_idx]][0]
                  ori_tar = oristarts_dic[p_key]
        
              elif (inters.geom_type.values[0] == "LineString"):
                endp1, endp2 = Point([inters.values[0].xy[0][0],inters.values[0].xy[1][0]]),  Point([inters.values[0].xy[0][-1],inters.values[0].xy[1][-1]]) #LineString #端点をつくる
                ori_tar = self.linestring
        
              else: 
                endp_use = p0
                ori_tar = self.linestring
        
              endp1, endp2 = Point([ori_tar.xy[0][0],ori_tar.xy[1][0]]),  Point([ori_tar.xy[0][-1],ori_tar.xy[1][-1]]) #LineString #端点をつくる
    
             
            ###　not p0
            endp_use = [p for p in [endp1, endp2] if p != p0]
            if len(endp_use) >0:
                endp_use = endp_use[0]
            else:
                endp_use = p0 
        
          else:
            endp_use = p0
        
          return endp_use #intersection
        
        
        ### End side too
        def point_from_6ft_end(self):

          buff_boundary = gdf_road_dissolve.geometry.values[0]
        
          x_0,y_0 = self.linestring.coords.xy
          p00 = Point(x_0[0], y_0[0])
          p_1 = Point(x_0[-1], y_0[-1])
          if self.direction =="east":
            x_min_idx = [p00.x, p_1.x].index(max([p00.x, p_1.x]))
            p0 = [p00, p_1][x_min_idx]
          if self.direction =="south":
            y_max_idx = [p00.y, p_1.y].index(min([p00.y, p_1.y]))
            p0 = [p00, p_1][y_max_idx]
        
          if buff_boundary.contains(p0):
            inters = gdf_road_dissolve.intersection(self.linestring)
            try: 
              endp1, endp2 = Point([inters.values[0].xy[0][0],inters.values[0].xy[1][0]]),  Point([inters.values[0].xy[0][-1],inters.values[0].xy[1][-1]]) #LineString #端点をつくる
              ori_tar = self.linestring
            except:
              if (inters.geom_type.values[0] == "MultiLineString"): #.all
                individual_lines = list(inters.values[0].geoms) #LineString list
                           
                oristarts_dic = {}
                oristarts_list = []
                if self.direction == "east":
                  for i in individual_lines:
                    ori_p0 = get_startpoint_end(i, "east")
                    oristarts_dic[ori_p0] = i
                    oristarts_list.append(ori_p0)
              
                  x_list = [x.xy[0] for x in oristarts_list] #xy[0][0]
                  x_min_idx = x_list.index(max(x_list))
                  p_key = [p for p in oristarts_list if p.xy[0] == x_list[x_min_idx]][0]
                  ori_tar = oristarts_dic[p_key]
                if self.direction == "south":
                  for i in individual_lines:
                    ori_p0 = get_startpoint_end(i, "south")
                    oristarts_dic[ori_p0] = i
                    oristarts_list.append(ori_p0)
                  
                  y_list = [x.xy[1] for x in oristarts_list] #x.xy[0][1]
                  y_max_idx = y_list.index(min(y_list))
                  p_key = [p for p in oristarts_list if p.xy[1] == y_list[y_max_idx]][0]
                  ori_tar = oristarts_dic[p_key]
        
              elif (inters.geom_type.values[0] == "LineString"):
                endp1, endp2 = Point([inters.values[0].xy[0][0],inters.values[0].xy[1][0]]),  Point([inters.values[0].xy[0][-1],inters.values[0].xy[1][-1]]) #LineString #端点をつくる
                ori_tar = self.linestring
        
              else: 
                endp_use = p0
                ori_tar = self.linestring
        
              endp1, endp2 = Point([ori_tar.xy[0][0],ori_tar.xy[1][0]]),  Point([ori_tar.xy[0][-1],ori_tar.xy[1][-1]]) #LineString #端点をつくる
             
            
            endp_use = [p for p in [endp1, endp2] if p != p0]
            if len(endp_use) >0: #念のため
                endp_use = endp_use[0]
            else:
                endp_use = p0
        
          else:
            endp_use = p0
        
          return endp_use  
    
    
    """# def get minimum x/largest y based on direction"""
    
    def min_Linex(linestring, direction): #note： largely winding lines may miss appropriate direction...
      if direction =="east":
        xx = linestring.coords.xy[0]
        xmin_idx = [xx[0], xx[-1]].index(min([xx[0], xx[-1]]))
        xmin = [xx[0], xx[-1]][xmin_idx]
        result = xmin
      if direction =="south":
        xx = linestring.coords.xy[1]
        ymax_idx = [xx[0], xx[-1]].index(max([xx[0], xx[-1]]))
        ymax = [xx[0], xx[-1]][ymax_idx]
        result = ymax
    
      return result
    
    """#gdf_T1s, gdf_T2s"""
    
    gdf_T1s = gdf_line.query("T1T2==1")
    gdf_T2s = gdf_line.query("T1T2==2")
    
    gdf_T1s.loc[:,"Processed"] = 0
    gdf_T2s.loc[:,"Processed"] = 0
    
    
    """#def num_points # count the number of available points with some adjustments"""
    
    def num_points(linestring, p_edge, direction): #not consider p_end
      length_T = linestring.length
    
      #subtract the distance to the first point from the edge (namely, subtracting the effect of 6gt)(shapely.projectの起点の指定の仕方が分からないのでポイントからの距離にする)
      line_endpoint = get_startpoint(linestring, direction)
      edge_to_p0 = line_endpoint.distance(p_edge) # Euclidean distance
      valid_len  = length_T - edge_to_p0
    
      #24 ft
      num_points = math.floor(valid_len/ (24*0.3048)) #integer
      num_decim = math.modf(valid_len/ (24*0.3048))[0] #decimal part
      
      if num_points >1:
          if num_decim <= 0.6: #if lacking length is short enough to make adjustment (22 ft interval*1 palms)
              num_points = num_points +1
              adjutment_num = 1
          elif num_decim > 0.6 and num_decim <= 1.19: #if lacking length is short enough to make adjustment (22 ft interval*2 palms)
              num_points = num_points +1
              adjutment_num = 2
          else:
              num_points = num_points # no adjustable lacking distance
              adjutment_num = 0
      else:
         num_points = num_points
         adjutment_num = 0
      
      return num_points, adjutment_num
    
    """#def plot on T1
    with adjustment
    """
    class generate_pointT1:
        def __init__(self, PointT1_start, pfix, t1_line, adi_, last2point, distance=24):
            self.PointT1_start = PointT1_start
            self.pfix = pfix
            self.t1_line = t1_line
            self.adi_ = adi_
            self.last2point = last2point
            distance = 24
            
        def buffer_for_pointT1_any_adj(self): 
          if self.adi_ ==1 or self.adi_ ==2:  #adjust points i th point from the last (counting naturally) 
            buffer_distance = 22*0.30 # adjustment
          else:
            buffer_distance = 24*0.3048 # [m]
        
          buffer_poly = self.PointT1_start.buffer(buffer_distance)
        
          # find intersecting points
          intersection = self.t1_line.intersection(buffer_poly.exterior) #P1 and the other
        
          # Extract intersection points if they exist
          intersection_points_list = []
          if intersection.geom_type == 'Point':
            intersection_points_list.append((intersection.x, intersection.y))
            PointT1_next = Point(intersection_points_list)
        
          # point farther from start
          elif intersection.geom_type == 'MultiPoint':
            intersection_points_list.extend([(np.array(point.coords)[0][0], np.array(point.coords)[0][1]) for point in intersection.geoms]) #point list取得
            
            
            distances = {}
            for p in intersection_points_list:
              dis = Point([p]).distance(self.last2point)
              distances[ Point([p])]=dis
            disonly = list(distances.values())
            dis_sort = sorted(disonly)
            PointT1_next = [p for p, d in distances.items() if d == dis_sort[-1]][0]
        
          else:
            PointT1_next = Point()
        
          return PointT1_next
        
        ### No adjustment ver
        def buffer_for_pointT1_any(self):
          buffer_distance = 24*0.3048 # [m]
        
          buffer_poly = self.PointT1_start.buffer(buffer_distance)
        
          # find intersecting points
          intersection =self.t1_line.intersection(buffer_poly.exterior) #P1 and the other
        
          # Extract intersection points if they exist
          intersection_points_list = []
          if intersection.geom_type == 'Point':
            intersection_points_list.append((intersection.x, intersection.y))
            PointT1_next = Point(intersection_points_list)
        
          
          elif intersection.geom_type == 'MultiPoint':
            intersection_points_list.extend([(np.array(point.coords)[0][0], np.array(point.coords)[0][1]) for point in intersection.geoms]) #point list取得
            
            
            distances = {}
            for p in intersection_points_list:
              dis = Point([p]).distance(self.last2point)
              distances[ Point([p])]=dis
            disonly = list(distances.values())
            dis_sort = sorted(disonly)
            PointT1_next = [p for p, d in distances.items() if d == dis_sort[-1]][0]
        
          else:
            PointT1_next = Point()
        
          return PointT1_next
    
    
    
    def multipoint_to_singlepoints(multipoint):
      points_lilst = []
      p_list = list(multipoint.geoms)
      for p in p_list:
        points_lilst.append(p)
    
      return points_lilst
    
    
    """#def plot on T2
    """
    class generate_pointT2():
        def __init__(self, PointT2_start, pfix, t2_line, adi_, last2point, distance2t2):
            self.PointT2_start = PointT2_start
            self.pfix = pfix
            self.t2_line = t2_line
            self.adi_ = adi_
            self.distance2t2 = distance2t2
            self.last2point = last2point
            
        def buffer_for_pointT2_any_adj(self): #P0, 54ft-dietance, T2
              
          if self.adi_ ==1 or self.adi_ ==2:  #adjust points i th point from the last (counting naturally) 
            remain_distance = 54*0.3048 - self.distance2t2 -2*0.3 # adjustment
          else:
            remain_distance = 54*0.3048 - self.distance2t2 # [m]
                
          buffer_poly = self.PointT2_start.buffer(remain_distance)
        
          # find intersecting points
          intersection = self.t2_line.intersection(buffer_poly.exterior)
        
          # Extract intersection points if they exist
          intersection_points_list = []
          if intersection.geom_type == 'Point':
            intersection_points_list.append((intersection.x, intersection.y))
            PointT2_next = Point(intersection_points_list)
          elif intersection.geom_type == 'MultiPoint':
            intersection_points_list.extend([(np.array(point.coords)[0][0], np.array(point.coords)[0][1]) for point in intersection.geoms]) #point list取得
            
            
            #compare distance from 2nd last point
            distances = {}
            for p in intersection_points_list:
              dis = Point([p]).distance(self.last2point)
              distances[ Point([p])]=dis
            disonly = list(distances.values())
            dis_sort = sorted(disonly)
            PointT2_next = [p for p, d in distances.items() if d == dis_sort[-1]][0]
            
            
          else:
            PointT2_next = Point()
          
          return PointT2_next
        
        
        def buffer_for_pointT2_any(self):
              
          remain_distance = 54*0.3048 - self.distance2t2
              
          buffer_poly = self.PointT2_start.buffer(remain_distance)
        
          # find intersecting points
          intersection = self.t2_line.intersection(buffer_poly.exterior)
        
          # Extract intersection points if they exist
          intersection_points_list = []
          if intersection.geom_type == 'Point':
            intersection_points_list.append((intersection.x, intersection.y))
            PointT2_next = Point(intersection_points_list)
          elif intersection.geom_type == 'MultiPoint':
            intersection_points_list.extend([(np.array(point.coords)[0][0], np.array(point.coords)[0][1]) for point in intersection.geoms]) #point list取得
                        
            #compare distance from 2nd last point
            distances = {}
            for p in intersection_points_list:
              dis = Point([p]).distance(self.last2point)
              distances[ Point([p])]=dis
            disonly = list(distances.values())
            dis_sort = sorted(disonly)
            PointT2_next = [p for p, d in distances.items() if d == dis_sort[-1]][0]
                
          else:
            PointT2_next = Point()
        
          return PointT2_next
    
    """#def reference_point to T2"""
    
    def pointref_to_pointT2(Pref,T2_linestring):
      distance_2T2 = T2_linestring.distance(Pref)
      PointT2 = T2_linestring.interpolate(T2_linestring.project(Pref)) #P0
      return PointT2#, distance_2T2
    
    """# def 角度取得"""
    
    def unit_vector(vector): 
        """ Returns the unit vector of the vector.  """
        return vector / np.linalg.norm(vector) 
    
    def angle_between(v1, v2):
        v1_u = unit_vector(v1)
        v2_u = unit_vector(v2)
        return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))
    

    def angle_vector(pvec, pcenter, line_from, line_to):
      
      pvec = pointref_to_pointT2(pcenter, line_to)
      
      ptmp = line_from.interpolate(1) #1m any
      
      vec1 = [pvec, pcenter]
      vec2 = [ptmp, pcenter]
      v1 = [np.array(pvec.xy[0][0]-pcenter.xy[0][0]), np.array(pvec.xy[1][0]-pcenter.xy[1][0]) ]
      v2 = [np.array(ptmp.xy[0][0]-pcenter.xy[0][0]), np.array(ptmp.xy[1][0]-pcenter.xy[1][0]) ]
      angle_ = angle_between(v1,v2)
    
      return angle_
    
    """#def find nearest line_t1"""
    
    def find_line_t1(pairid, t2_line, direc):
      gdf_T1pair = gdf_T1s.query(f"Pair=={pairid}")
      t1_list = gdf_T1pair.geometry.tolist()
    
      #p0 on T2 
      p0_class = roadedge_6ft(t2_line, direc, gdf_buff=gdf_road_dissolve)
      p0 = p0_class.point_from_6ft()
    
      distances = {}
      for t1 in t1_list:
        dis = p0.distance(t1)
        distances[t1] = dis
      disonly = list(distances.values())
      disonly_sort = sorted(disonly)
      t1_line = [k for k, v in distances.items() if v == disonly_sort[0]][0]
    
      return t1_line
    
    #If no same pair, collect another line by buff
    def find_line_t1_backup(t2_line, direc):
      gdf = gpd.GeoDataFrame(geometry=[t2_line])
      buff_t2 = gdf.buffer(15) #15m buffer
    
      #collect by buffer
      t1_list = []
      for i, li in gdf_T1s.iterrows():
        if li.geometry.intersects(buff_t2).any():
          t1_list.append(li.geometry)
    
      #p0 on T2
      p0_class = roadedge_6ft(t2_line, direc, gdf_buff=gdf_road_dissolve)
      p0 = p0_class.point_from_6ft()
    
      #compare distance from p0. Group from higher ele (small G)
      gp2 = gdf_T2s[gdf_T2s.geometry==t2_line].Group2.values[0]
      distances = {}
      for t1 in t1_list:
        gp1 = gdf_T1s[gdf_T1s.geometry==t1].Group2.values[0]
        if gp1 <= gp2:
          dis = p0.distance(t1)
          distances[t1] = dis
    
      disonly = list(distances.values())
      disonly_sort = sorted(disonly)
      t1_line = [k for k, v in distances.items() if v == disonly_sort[0]][0]
    
      return t1_line
    
    
    
    """#Run
    #line_t2
    """
    
    #T2 lines
    t2_list = gdf_T2s.geometry.values.tolist()
    
    points_all_T2 = []
    
    for line_t2 in t2_list:
      pair = gdf_T2s[gdf_T2s.geometry==line_t2].Pair.values[0]
      dire = gdf_T2s[gdf_T2s.geometry==line_t2].direction.values[0]
    
      ######## p0 on T2 edge 6ft
      #Processed =0
      check_processed = gdf_T2s[gdf_T2s.geometry==line_t2].Processed.values[0]
      if check_processed ==0:
        ### whole line not within Road buff
        if gdf_road_dissolve.contains(line_t2).all(): #road contains the whole line
           continue
        else:
          p0_class = roadedge_6ft(line_t2, dire, gdf_buff=gdf_road_dissolve)
          p0_ = p0_class.point_from_6ft()
          p0_end = p0_class.point_from_6ft_end()
      else:
        continue
    
      #nearest T1
      try:
        line_t1 = find_line_t1(pair, line_t2, dire)
      except: # if no corresponding pair, find by buff
        line_t1 = find_line_t1_backup(line_t2, dire)
    
      ######## num of points in T2
      direction = gdf_T2s[gdf_T2s.geometry==line_t2].direction.values[0]
      num_pointsT2, adj = num_points(line_t2, p0_, direction)
    
      ######## Plot on T2
      start_point = p0_
      points_lineT2 = [p0_, p0_end]
      
      for i in range(num_pointsT2):
        ## ensure no empty point
        points_lineT2 = [p for p in points_lineT2 if not p.is_empty]
          
        adji = num_pointsT2 -i #n th from last
        
        if i >=2 and len(points_lineT2)>4: #points_lineT2 already has 2 points
            las2p = points_lineT2[-2]
        else: #i=0
            las2p = p0_
        
        p_ref = pointref_to_pointT2(p0_, line_t1) #on T1
        angle = angle_vector(p_ref, p0_, line_t2, line_t1)
        if not ((angle > 45) & (angle < 135)): #check geological relation
          # find another T1 from start point
          distances = {}
          group_t2 = gdf_T2s[gdf_T2s.geometry == line_t2].Group2.values[0]
          for l in gdf_T1s.geometry.tolist():
            if l != line_t1:
              dis = l.distance(p0_)
              if dis != 0: 
                distances[l] = dis
          disonly = list(distances.values())
          disonly_sort = sorted(disonly)
          for d in disonly_sort:
            line = [k for k, v in distances.items() if v == d][0]
            group = gdf_T1s[gdf_T1s.geometry == line].Group2.values[0]
            #T1 with higher Group
            if group <= group_t2:
              sel_t1 = [k for k, v in distances.items() if v == d][0]
              break
            else:
              continue
          try:
              line_t1 = sel_t1 #update line_t1
          except:
              line_t1 = line_t1 #no change
    
        ### Return distance
        if len(start_point.xy[0]) ==0:
          start_point  = p0_
        else:
          pass
        distance_return = line_t1.distance(start_point)
        if distance_return > 30*0.3048: #9.144m, #plot like T1
          if adj >0:
              generate_pointT1_class =  generate_pointT1(start_point, p0_, line_t2, adji, las2p, distance=24)
              pointT2_next = generate_pointT1_class.buffer_for_pointT1_any_adj()
              
              if type(pointT2_next) == tuple:
                pointT2_next_p = Point(pointT2_next)
                points_lineT2.append(pointT2_next_p)
                start_point = pointT2_next_p
              else:
                points_lineT2.append(pointT2_next)
                start_point = pointT2_next
          else: #adj==0
              generate_pointT1_class =  generate_pointT1(start_point, p0_, line_t2, adji, las2p, distance=24)
              pointT2_next = generate_pointT1_class.buffer_for_pointT1_any()
              
              if type(pointT2_next) == tuple:
                pointT2_next_p = Point(pointT2_next)
                points_lineT2.append(pointT2_next_p)
                start_point = pointT2_next_p
              else:
                points_lineT2.append(pointT2_next)
                start_point = pointT2_next
    
        else: #within 9.144m, #Plot on T2 as usual
          if adj >0:
              generate_pointT2_class = generate_pointT2(start_point, p0_, line_t2, adji, las2p, distance_return)
              pointT2_next = generate_pointT2_class.buffer_for_pointT2_any_adj()
              
              if type(pointT2_next) == tuple:
                pointT2_next_p = Point(pointT2_next)
                points_lineT2.append(pointT2_next_p)
                start_point = pointT2_next_p
              else:
                points_lineT2.append(pointT2_next)
                start_point = pointT2_next
          else: # no adjustment
              generate_pointT2_class = generate_pointT2(start_point, p0_, line_t2, adji, las2p, distance_return)
              pointT2_next = generate_pointT2_class.buffer_for_pointT2_any()
              
              if type(pointT2_next) == tuple:
                pointT2_next_p = Point(pointT2_next)
                points_lineT2.append(pointT2_next_p)
                start_point = pointT2_next_p
              else:
                points_lineT2.append(pointT2_next)
                start_point = pointT2_next
                
    
      points_all_T2.append(points_lineT2)
    
    #ばらす
    points_all_T2_flat = []
    for pp in points_all_T2:
      if type(pp) == list:
        for p in pp:
          if type(p)==tuple:
            poi = Point([p])
            points_all_T2_flat.append(poi)
          else:
            points_all_T2_flat.append(p)
    
    points_all_T2_set= list(set(points_all_T2_flat))
    
    """#line_t1
    """
    
    t1_list = gdf_T1s.geometry.values.tolist()
    
    points_all_T1 = []
    ######### Plot on T1
    for line_t1 in t1_list:
      #test line_t1 = gdf_T1s[gdf_T1s.Pair==1159].geometry.loc[304]
    
      direction = gdf_T1s[gdf_T1s.geometry==line_t1].direction.values[0]
    
      #T1 edge point
      ### 
      if gdf_road_dissolve.contains(line_t1).all():
           continue
      else:
          p0_t1_class = roadedge_6ft(line_t1, direction, gdf_buff=gdf_road_dissolve)
          p0_t1 = p0_t1_class.point_from_6ft()
          p0_t1_end = p0_t1_class.point_from_6ft_end()
    

      num_pointsT1, adj = num_points(line_t1, p0_t1, direction)
    
      ######## Plot on T1
      start_point = p0_t1
      points_lineT1 = [p0_t1, p0_t1_end]
      for i in range(num_pointsT1):
        adji = num_pointsT1 -i
        
        if i >=2 and len(points_lineT1)>4:
            las2p = points_lineT1[-2]
        else:
            las2p = p0_t1
    
        if adj>0:  #adjustment available    
            generate_pointT1_class =  generate_pointT1(start_point, p0_t1, line_t1, adji, las2p, distance=24)
            pointT_next = generate_pointT1_class.buffer_for_pointT1_any_adj()
            
            if type(pointT_next) == tuple:
              start_point = Point([pointT_next])
            else:
              start_point = pointT_next
            points_lineT1.append(start_point) 
        
        else: # no adjustment
            generate_pointT1_class = generate_pointT1(start_point, p0_t1, line_t1, adji, las2p, distance=24)
            pointT_next = generate_pointT1_class.buffer_for_pointT1_any()
            
            if type(pointT_next) == tuple:
              start_point = Point([pointT_next])
            else:
              start_point = pointT_next
            points_lineT1.append(start_point)
        
      points_all_T1.append(points_lineT1)
          
    
    #ばらす
    points_all_T1_flat = []
    for pp in points_all_T1:
      if type(pp) == list:
        for p in pp:
          if type(p)==tuple:
            poi = Point([p])
            points_all_T1_flat.append(poi)
          else:
            points_all_T1_flat.append(p)
    
    
    points_all_T1_set= list(set(points_all_T1_flat))
    
    
    """#Finalize"""
    ########## Finalize
    points_T1T2 = points_all_T1_set + points_all_T2_set
    
    #Correct duplicates
    points_T1T2_set = list(set(points_T1T2))
    
    #remove empty
    points_T1T2_valid = [p for p in points_T1T2_set if not p.is_empty]
    
    gdf_points = gpd.GeoDataFrame({"geometry":points_T1T2_valid, "Processed":0, "del":0})
    gdf_points = gdf_points.set_crs(gdf_line.crs, allow_override=True)
    
    gdf_points['buffer'] = gdf_points['geometry'].buffer(4)
    
    
    gdf_points_fin = gdf_points
    
    points_T1T2_fin = gdf_points_fin.geometry.tolist()
    
    
    """#Export"""
    
    #export points
    geometry = gpd.GeoSeries(points_T1T2_fin)
    gdf = gpd.GeoDataFrame(geometry=geometry, columns=['geometry'])
    gdf = gdf.set_crs(gdf_line.crs, allow_override=True)
    
    # Output shapefile path
    filename = os.path.basename(line_shp_path)[:-4]
    output_shapefile_path = os.path.join(out_dir,f"{filename}_allpoints.shp")
    # Export the GeoDataFrame to a shapefile
    gdf.to_file(output_shapefile_path)
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )
    

if __name__=="__main__":
    main()
    

#### Plot for check
# fig = plt.figure(figsize=(5, 5))
# ax1 = fig.add_subplot(1,1,1)
# ### poly
# # x,y = terr_use.exterior.xy
# # ax1.plot(x, y, color='grey', label='Polygon')
# ### point
# ax1.plot(endp_use.xy[0][0], endp_use.xy[1][0], "o", color="black")
# # ax1.plot(p0.xy[0][0], p0.xy[1][0], "o", color="black")
# # for p in points_all_T1_set:
# #     ax1.plot(p.xy[0][0], p.xy[1][0], "o", color='orange')
# ### line
# ax1.plot(line_t1.xy[0], line_t1.xy[1], color='green')
# ax1.plot(inters.geometry.values[0].xy[0], inters.geometry.values[0].xy[1], color='black')