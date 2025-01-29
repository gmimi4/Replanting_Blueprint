# -*- coding: utf-8 -*-

import math
import os
import shapely
from shapely.geometry import Point, LineString, Polygon,MultiPoint, MultiLineString
# import matplotlib.pyplot as plt
import geopandas as gpd
import itertools
import rasterio
from rasterstats import zonal_stats
import time


def main(line_shp_path, dem_path, out_dir):
    
    start = time.time()

    gpdf = gpd.read_file(line_shp_path)
    
    
    """def Multiline to single line"""
    
    def multi2single(gpdf_test):
    
        exploded_all = gpdf_test.explode()
        exploded_reset = exploded_all.reset_index()
        columns_to_drop = ['level_0','level_1']
        gdf_dropped = exploded_reset.drop(columns=columns_to_drop)
    
        return gdf_dropped
    
    def flatten_list(multi_list):
      indiv_list =[]
      for mm in multi_list:
        for m in mm:
          indiv_list.append(m)
    
      indivs = list(set(indiv_list))
      return indivs
    
    multi_rows = gpdf[gpdf.geometry.type == 'MultiLineString']
    
    if len(multi_rows) >0:
      single_lines = multi2single(gpdf)
      lines = list(single_lines.geometry.values)
    else:
      lines = [line.geometry for i,line in gpdf.iterrows()]
    
    #Connect lines overlapping with longer than 0m
    inters_pair =[]
    for line1, line2 in itertools.combinations(lines,2):
      if line1.intersects(line2):
        inter = line1.intersection(line2)
        inter_distance = inter.length
        if inter_distance > 0:
          inters_pair.append([line1, line2])
        else:
          continue
    
    concatline_list=[]
    for inter_lines in inters_pair:
      line_merge = shapely.ops.linemerge([shapely.geometry.shape(row) for i, row in [inter_lines]] )
      concatline_list.append(line_merge)
    
    inters_pair_indiv_=[]
    for ll in inters_pair:
      for l in ll:
        inters_pair_indiv_.append(l)
    inters_pair_indiv = list(set(inters_pair_indiv_))
    
    line_remoev = list(set(lines) ^ set(inters_pair_indiv))
    lines_rev = line_remoev + concatline_list
    
    
    """# Grouping by DEM
    """
    
    dem_src = rasterio.open(dem_path)
    raster_data = dem_src.read(1)
    transform = dem_src.transform
    
    stat_dic = {}
    for line in lines_rev:
      gdf_convert = gpd.GeoDataFrame(geometry=[line])
      try:
        stats_temp = zonal_stats(gdf_convert.geometry, raster_data, affine=transform, stats=["max","min","mean", "std"]) #辞書になる、リストに入る
      except: #error: height and width must be >0
        center_point = line.interpolate(0.5, normalized=True)
        stats_temp = zonal_stats(center_point, raster_data, affine=transform, stats=["max","min","mean", "std"])
      LineID_ori = gpdf[gpdf["geometry"]==line]["LineID"].values[0]
      stats_temp_dic = stats_temp[0]
      stats_temp_dic["LineID"] = LineID_ori
      stat_dic[line] = stats_temp_dic
    
    
    max_list,min_list,mean_list,std_list,geom_list,LineID_list = [],[],[],[],[],[]
    
    for k,v in stat_dic.items():
      max_list.append(v["max"])
      min_list.append(v["min"])
      mean_list.append(v["mean"])
      std_list.append(v["std"])
      LineID_list.append(v["LineID"])
      geom_list.append(k)
    
    data = {"mean":mean_list, "max":max_list, "min":min_list, "std":std_list,"LineID":LineID_list,"geometry":geom_list}
    gdf_line_stats = gpd.GeoDataFrame(data)
    gdf_line_stats = gdf_line_stats.set_crs(gpdf.crs, allow_override=True)
    gdf_line_stats["length"] = gdf_line_stats.geometry.length
    
    
    gdf_sort = gdf_line_stats.sort_values(by='mean', ascending=False).reset_index(drop=True)
    
    
    height_diff = 1
    
    max_dem_mean = gdf_sort["mean"].max()
    min_dem_mean = gdf_sort["mean"].min()
    gdf_sort["Group2"] = 0 #dammy
    
    gp_num = math.ceil((max_dem_mean - min_dem_mean)/height_diff)
    for g in range(gp_num):
      range_upper = max_dem_mean - height_diff*(g)
      range_lower = max_dem_mean - height_diff*(g+1)
      for i,line in gdf_sort.iterrows():
        mean_val = line["mean"]
        if mean_val <= range_upper and mean_val >= range_lower:
          gdf_sort.iat[i,-1] = g+1
    
    gdf_sort["LineID2"] = gdf_sort.index
    gdf_sort["Processed"] = 0 #dammy
    gdf_sort["Pair"] = 0 #dammy
    gdf_sort["T1T2"] = 0 #dammy
    gdf_sort["INFIL"] = 0 #dammy
    

    
    def pointref_to_pointT2(Pref,T2_line_geoseries):
      distance = T2_line_geoseries.distance(Pref)
      PointT2 = T2_line_geoseries.interpolate(T2_line_geoseries.project(Pref)) #P0
      return PointT2, distance #GeoSeries point, [m]
    
    def distance_from_center_to_lines(linestring, gdf_lines):
      test_mid_point = linestring.interpolate(0.5, normalized = True)
      near_dic = {}
      for testi, testli in gdf_lines.iterrows():
        if (testli.geometry != linestring):
          near_vale_dic = {}
          test_distance = testli.geometry.distance(test_mid_point)
          LineID = testli.LineID
          Group2 = testli.Group2
          Processed = testli.Processed
          Pair = testli.Pair
          T1T2 = testli.T1T2
          INFIL = testli.INFIL
          near_vale_dic["distance"] = test_distance
          near_vale_dic["midpoint"] = test_mid_point
          near_vale_dic["LineID"] = LineID
          near_vale_dic["Group2"] = Group2
          near_vale_dic["Processed"] = Processed
          near_vale_dic["Pair"] = Pair
          near_vale_dic["T1T2"] = T1T2
          near_vale_dic["INFIL"] = INFIL

          near_dic[testli.geometry] = near_vale_dic
    
    
      near_dic_sort = sorted(near_dic.items(), key=lambda x: x[1]["distance"])
    
      return near_dic_sort
    

    def get_line_attributes(linestring_1, tupple_val, source_gdf=gdf_sort):
      attribute_list = ["LineID","Group2","Processed","Pair","T1T2","INFIL"]
      self_attributes_dic = {}
      partner_attributes_dic = {}
    
      for a in attribute_list:
        attr_self = source_gdf.loc[source_gdf.geometry == linestring_1][a].values[0]
        attr_near = tupple_val[1][a]
    
        self_attributes_dic[a] = attr_self
        partner_attributes_dic[a] = attr_near
    
      return self_attributes_dic, partner_attributes_dic
    
    
    def put_different_T1T2(target_linestring_1, source_tupple_val, idx_self, source_gdf=gdf_sort):
      source_T1T2 = source_tupple_val[1]["T1T2"]
      if source_T1T2 ==1:
        source_gdf.loc[idx_self,"T1T2"] = 2
      if source_T1T2 ==2:
        source_gdf.loc[idx_self,"T1T2"] = 1
    
    def put_same_T1T2(target_linestring_1, source_tupple_val, idx_self, source_gdf=gdf_sort):
      source_T1T2 = source_tupple_val[1]["T1T2"]
      source_gdf.loc[idx_self,"T1T2"] = source_T1T2
    
    def put_Infilling(target_linestring_1, source_tupple_val, idx_self, source_gdf=gdf_sort):
      chck_distance = source_tupple_val[1]["distance"]
      if chck_distance > 14.63:
        source_gdf.loc[idx_self,"INFIL"] = 1
    
    """def T1 to highre, T2 to lower"""
    def put_lines_T1T2(idx_self, idx_partner, source_gdf=gdf_sort):
      Group_1 = source_gdf.loc[idx_self,"Group2"]
      Group_2 = source_gdf.loc[idx_partner,"Group2"]
      if Group_1 < Group_2: #1 high
        source_gdf.loc[idx_self,"T1T2"] = 1
        source_gdf.loc[idx_partner,"T1T2"] = 2
      if Group_1 > Group_2: #2 high
        source_gdf.loc[idx_self,"T1T2"] = 2
        source_gdf.loc[idx_partner,"T1T2"] = 1
    
    def convert1_2(input_int:int):
      if input_int==1:
        output =2
      if input_int==2:
        output =1
      if input_int==0:
        output =0

    
    """#Run"""
    gdf_sort_copy = gdf_sort.copy(deep=True)
    
    for i in range(len(gdf_sort_copy)):
    
      ### 1) create dic of distace from center
      lin = gdf_sort[i:i+1].geometry.values[0]
    
      if gdf_sort.loc[gdf_sort.geometry==lin]["Processed"].values[0]==0:
        neardict = distance_from_center_to_lines(lin, gdf_sort)
        
        ## ensure len(neardict)>0
        if len(neardict)==0:
            self_idx = gdf_sort.loc[gdf_sort.geometry == lin].index[0]
            gdf_sort.loc[self_idx,"T1T2"] = 1
            gdf_sort.loc[self_idx,"INFIL"] = 1
            gdf_sort.loc[self_idx,"Processed"] = 1
        
        ### if nearest distance >14.69, it's infilling
        elif neardict[0][1]["distance"] >14.69:
            self_idx = gdf_sort.loc[gdf_sort.geometry == lin].index[0]
            gdf_sort.loc[self_idx,"T1T2"] = 1
            gdf_sort.loc[self_idx,"INFIL"] = 1
            gdf_sort.loc[self_idx,"Processed"] = 1
            continue
        
        else:
            # collect value of near_dict neighboring. should be 0th in ordinary location (up&down)
            for vi,val in enumerate(neardict):
        
              self_attr_dic, partner_attr_dic = get_line_attributes(lin, val, source_gdf=gdf_sort)
        
              self_idx = gdf_sort.loc[gdf_sort.geometry == lin].index[0]
              partner_idx = gdf_sort.loc[gdf_sort.geometry == val[0]].index[0]
        
              ### 2)LineID(ori) different & ### 3) line Group differen -------------------------------
              if (self_attr_dic["LineID"] != partner_attr_dic["LineID"]) and (self_attr_dic["Group2"] != partner_attr_dic["Group2"]):
                ##if Process=1, already T1T2
                if partner_attr_dic["Processed"] ==1:
                  put_different_T1T2(lin, val, self_idx, source_gdf=gdf_sort)
                  gdf_sort.loc[self_idx,"Processed"] = 1
                  break
        
                ##見つけたラインのProcess !=1 （no T1T2)
                ## find 2nd nearest line for right location
                for vi2 in range(vi+1,len(neardict),1):
                  self_attr_dic2, partner_attr_dic2 = get_line_attributes(lin, neardict[vi2], source_gdf=gdf_sort)
                  #if same LineID, go to next 2nd
                  if self_attr_dic["LineID"] == partner_attr_dic2["LineID"]:
                    continue
                  #diff LineID & Processed !=1
                  if (self_attr_dic["LineID"] != partner_attr_dic2["LineID"]) and (partner_attr_dic2["Processed"]!=1):
                    #1 to higher line
                    put_lines_T1T2(self_idx, partner_idx, source_gdf=gdf_sort)
                    gdf_sort.loc[self_idx,"Processed"] = 1
                    gdf_sort.loc[partner_idx,"Processed"] = 1
                    break
        
                  #diff LineID & Processed ==1
                  if (self_attr_dic2["LineID"] != partner_attr_dic2["LineID"]) and (partner_attr_dic2["Processed"]==1):
                    #not 2nd's
                    put_different_T1T2(lin, neardict[vi2], self_idx, source_gdf=gdf_sort)
                    lin_t1t2 = gdf_sort.loc[self_idx, "T1T2"]
                    gdf_sort.loc[partner_idx, "T1T2"] = convert1_2(lin_t1t2)
                    gdf_sort.loc[self_idx,"Processed"] = 1
                    break
                else:
                    continue
                break
        
        
              ### 2)LineID(ori) diff & ### 3) Group same -------------------------------
              if (self_attr_dic["LineID"] != partner_attr_dic["LineID"]) and (self_attr_dic["Group2"] == partner_attr_dic["Group2"]):
                continue
        

              if (self_attr_dic["LineID"] == partner_attr_dic["LineID"]) and (partner_attr_dic["Processed"]!=1):
                continue
        
              
              if (self_attr_dic["LineID"] == partner_attr_dic["LineID"]) and (partner_attr_dic["Processed"]==1):
                put_same_T1T2(lin, val, self_idx, source_gdf=gdf_sort)
                gdf_sort.loc[self_idx,"Processed"] = 1
                break #out from neardict
        
            else:
              break
    
    #Ploting
    # fig, ax = plt.subplots(figsize=(5, 5))
    
    # # gdf_sort.plot(column='T1T2',ax=ax, legend=True)
    # gdf_sort.plot(column='Pair',ax=ax, legend=True)
    
    # for li in [lin]:
    #   linestring_x, linestring_y = li.xy
    #   ax.plot(linestring_x, linestring_y, color='black', label='Linestring')
    
    # for li in [neardict[0][0]]: #, neardict[1][0], neardict[2][0]
    #   linestring_x, linestring_y = li.xy
    #   ax.plot(linestring_x, linestring_y, color='red', label='Linestring')
    
    # for p in [neardict[0][1]["midpoint"]]: #midpointはどれも同じ
    #   x,y = p.xy
    #   ax.plot(x[0], y[0], 'bo',  label='Point')
    
    # plt.show()
    
    """#Run"""
    gdf_sort["Processed"] =0
    
    gdf_sort_copy = gdf_sort.copy(deep=True)
    

    for i in range(len(gdf_sort_copy)):

      lin = gdf_sort[i:i+1].geometry.values[0]
    
      if (gdf_sort.loc[gdf_sort.geometry==lin]["Processed"].values[0]==0) and ( gdf_sort.loc[gdf_sort.geometry==lin]["T1T2"].values[0]==1):
        neardict = distance_from_center_to_lines(lin, gdf_sort)
    
        for vi,val in enumerate(neardict):
          
          self_attr_dic, partner_attr_dic = get_line_attributes(lin, val, source_gdf=gdf_sort)
    
          if partner_attr_dic["T1T2"] ==1:
            continue
    
          self_idx = gdf_sort.loc[gdf_sort.geometry == lin].index[0]
          partner_idx = gdf_sort.loc[gdf_sort.geometry == val[0]].index[0]
    
          
          if (self_attr_dic["LineID"] != partner_attr_dic["LineID"]) and (self_attr_dic["Group2"] != partner_attr_dic["Group2"]):
            
            if val[1]["INFIL"] ==1:
              gdf_sort.loc[self_idx,"Pair"] = -99
              gdf_sort.loc[self_idx,"Processed"] = 1
              break
            else:
              group1 = self_attr_dic["Group2"]
              group2 = partner_attr_dic["Group2"]
              if partner_attr_dic["Processed"] ==0:
                
                if group1 < group2:
                  gdf_sort.loc[self_idx,"Pair"] = i+1
                  gdf_sort.loc[partner_idx,"Pair"] = i+1
                  gdf_sort.loc[self_idx,"Processed"] = 1
                  gdf_sort.loc[partner_idx,"Processed"] = 1
                  break
                
                if group1 > group2:
                  continue
    
              if partner_attr_dic["Processed"] ==1:
                if group1 < group2:
                  pair2 = gdf_sort.loc[partner_idx,"Pair"]
                  gdf_sort.loc[self_idx,"Pair"] = pair2
                  gdf_sort.loc[self_idx,"Processed"] = 1
                  break
                if group1 > group2:
                  continue
    
          
          if (self_attr_dic["LineID"] == partner_attr_dic["LineID"]) and (partner_attr_dic["Processed"]==0):
            continue
    
          
          if (self_attr_dic["LineID"] == partner_attr_dic["LineID"]) and (partner_attr_dic["Processed"]==1):
            continue
    
    """#Run for forgotten Pair T2
    step2 is needed
    """
    #input same line attr for forgotten T2 as neighboring line. #If neghboring is T1, find nearest T2
    
    gdf_T2_0 = gdf_sort[(gdf_sort["Pair"]==0) & (gdf_sort["T1T2"]==2)] #抽出
    gdf_sort_copy = gdf_T2_0
    
    for i in range(len(gdf_sort_copy)):

      lin = gdf_T2_0[i:i+1].geometry.values[0]
    
      for i, row in gdf_sort.iterrows():
        lin_sort = row.geometry
        if lin.intersects(lin_sort):
          reference_line = lin_sort
          reference_pair = row.Pair
          if reference_pair != 0:
            break
    
      self_idx = gdf_sort.loc[gdf_sort.geometry == lin].index[0] #gdf_sort内でのインデックス取得
      gdf_sort.loc[self_idx, "Pair"] = reference_pair
    
    """step2
    isolated T2 is same pair as neighbouring T1 
    """
    gdf_T2_0 = gdf_sort[(gdf_sort["Pair"]==0) & (gdf_sort["T1T2"]==2)]
    gdf_sort_copy = gdf_T2_0 
    
    for i in range(len(gdf_sort_copy)):
      lin = gdf_T2_0[i:i+1].geometry.values[0]
    
      neardict = distance_from_center_to_lines(lin, gdf_sort)
      self_idx = gdf_sort.loc[gdf_sort.geometry == lin].index[0]
    
      for vi, val in enumerate(neardict):
        self_attr_dic, partner_attr_dic = get_line_attributes(lin, val, source_gdf=gdf_sort)
        if (partner_attr_dic["T1T2"] ==1) and (partner_attr_dic["Group2"] < self_attr_dic["Group2"]):
          gdf_sort.loc[self_idx, "Pair"] = partner_attr_dic["Pair"]
          gdf_sort.loc[self_idx, "Processed"] = 1
          break
        else:
          continue
    
    
    """#Export"""
    gdf_sort = gdf_sort.set_crs(gpdf.crs, allow_override=True)
    filename = os.path.basename(line_shp_path)[:-4]
    outfile = out_dir + os.sep + filename + "_T1T2.shp"
    gdf_sort.to_file(outfile)
    
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )

if __name__=="__main__":
    main()