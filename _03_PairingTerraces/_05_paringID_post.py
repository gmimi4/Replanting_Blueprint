# -*- coding: utf-8 -*-
"""
# Assgin the same pairing ID for neighboring and connecting lines
# for lines which apart each other are not processed because they produce multilinestrings 
"""
 
import os
import shapely
from shapely.geometry import Point, LineString, Polygon,MultiPoint, MultiLineString
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import itertools
from collections import Counter
import time



def main(line_shp_path, out_dir):
    start = time.time()
    
    """#gpdf"""
    
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
        if type(mm) != list:
          indiv_list.append(mm)
        else:
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
    
    
    """gdf_T1s, gdf_T2s"""
    
    gdf_T1s = gpdf.query("T1T2==1")
    gdf_T2s = gpdf.query("T1T2==2")
    pair_list = list(set(gdf_T2s.Pair.values))
    
    ### in case T1 and T2 = 0 (no data)
    if len(gdf_T1s) ==0 and len(gdf_T2s) ==0:
        gpdf["T1T2"] = 1
        gdf_T1s = gpdf.query("T1T2==1")
        pair_list = list(set(gdf_T1s.Pair.values))
        
        
    
    def merge_by_pair(pairid, gdf, t1t2num):
      gdf_pair = gdf.query(f"Pair=={pairid}")
      gdf_pair_list = gdf_pair.geometry.tolist()
    
      inters = []
      for l1,l2 in itertools.combinations(gdf_pair_list, 2):
        if l1.intersects(l2):
          inters.append([l1,l2])
      inters_indiv = list(set(flatten_list(inters)))
    
      line_merge = shapely.ops.linemerge([shapely.geometry.shape(row) for row in inters_indiv] )
    
      #Put major Group
      gdf_group_list = gdf_pair.Group2.tolist()
      element_counts = Counter(gdf_group_list)
      most_Group = max(element_counts, key=element_counts.get)
    
      data1 = {"geometry":[line_merge],"Pair":pairid,"T1T2":t1t2num,"Group2":most_Group,"Processed":0}
      gdf_merge = gpd.GeoDataFrame(data1)
    
    
      return gdf_merge, inters_indiv #gdf_concat
    
    
    """Run"""
    
    #Updating pairs. # If there is no T2, pass to T1 processing.
    if len(gdf_T2s) >0:
        #T2
        to_removes=[]
        to_merge = []
        pair_list = list(set(gdf_T2s.Pair.values))
        for pair in pair_list:
          gdf_merge, inters_to_remove = merge_by_pair(pair, gdf_T2s, 2)
          to_merge.append(gdf_merge)
          to_removes.append(inters_to_remove)
        
        to_removes_all = flatten_list(to_removes)
        
        #merge
        gdf_merge_all = pd.concat(to_merge)
        #remove empty
        gdf_merge_all = gdf_merge_all[~gdf_merge_all['geometry'].is_empty]
        #remove multiline
        single_gdf = multi2single(gdf_merge_all)
        
        gdf_T_non = gdf_T2s[~gdf_T2s['geometry'].isin(to_removes_all)]
        gdf_concat = pd.concat([gdf_T_non, single_gdf])
        gdf_concat["length"] = gdf_concat.geometry.length
        
        gdf_T2s = gdf_concat
    
    #T1
    pair_list = list(set(gdf_T1s.Pair.values))
    try:
        pair_list.remove(-99)
    except:
        pass
    to_removes=[]
    to_merge = []
    
    for pair in pair_list:
      gdf_merge, inters_to_remove = merge_by_pair(pair, gdf_T1s, 1)
      to_merge.append(gdf_merge)
      to_removes.append(inters_to_remove)
    
    to_removes_all = flatten_list(to_removes)
    
    #merge
    gdf_merge_all = pd.concat(to_merge)
    #remove empty
    gdf_merge_all = gdf_merge_all[~gdf_merge_all['geometry'].is_empty]
    #remove multiline
    single_gdf = multi2single(gdf_merge_all)
    
    #update gdf
    gdf_T_non = gdf_T1s[~gdf_T1s['geometry'].isin(to_removes_all)]
    gdf_concat = pd.concat([gdf_T_non, single_gdf])
    gdf_concat["length"] = gdf_concat.geometry.length
    
    gdf_T1s = gdf_concat
    
    """concat"""
    gdf_fin = pd.concat([gdf_T1s, gdf_T2s])
    
    
    """#Export"""
    gdf_fin = gdf_fin.set_crs(gpdf.crs,  allow_override=True)
    filename = os.path.basename(line_shp_path)[:-4]
    outfile = out_dir + "/" + filename + "_post.shp"
    gdf_fin.to_file(outfile)
    
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )


if __name__=="__main__":
    main()