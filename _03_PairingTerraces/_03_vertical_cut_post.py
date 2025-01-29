# -*- coding: utf-8 -*-
"""
Process lines which have gone in the previous vertical cut process
"""

import math
import os
import shapely
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString
import fiona
import geopandas as gpd
# import matplotlib.pyplot as plt
import pandas as pd
import rasterio
from rasterstats import zonal_stats
import time



def main(before_cut_linepath, after_cut_dir, dem_path):
    start = time.time()
    
    after_cut_linepath = os.path.join(after_cut_dir, f'{os.path.basename(before_cut_linepath)[:-4]}_vertical.shp')
    out_dir = os.path.join(after_cut_dir,"post")
    os.makedirs(out_dir, exist_ok=True)
    tmp_dir =os.path.join(after_cut_dir,"3_merge_and_separated")
    
    
    def multi2single(gpdf_test):
    
        exploded_all = gpdf_test.explode()
        exploded_reset = exploded_all.reset_index()
        columns_to_drop = ['level_0','level_1']
        gdf_dropped = exploded_reset.drop(columns=columns_to_drop)
    
        return gdf_dropped
    
    def multiline_gdf_to_linelist(gdf):
      multi_rowslist = gdf[gdf.geometry.type == 'MultiLineString']
      if len(multi_rowslist) >0:
        single_line_gdf = multi2single(gdf)
        lineslist = list(single_line_gdf.geometry.values)
      else:
        lineslist = [line.geometry for i,line in gdf.iterrows()]
    
      return lineslist
    
    
    gpdf_before = gpd.read_file(before_cut_linepath)
    gpdf_after = gpd.read_file(after_cut_linepath)
    
    """cehck by intersect"""
    
    # Create a GeoDataFrame with the intersection of the two shapefiles
    gdf_difference = gpd.overlay(gpdf_before, gpdf_after, how='difference')
    
    ### remove multiline
    multi_rows = gdf_difference[gdf_difference.geometry.type == 'MultiLineString']
    
    if len(multi_rows) >0:
      single_lines = multi2single(gdf_difference)
      lines_rev = list(single_lines.geometry.values)
    else:
      lines_rev = [line.geometry for i,line in gdf_difference.iterrows()]
    
    
    data = {"geometry":lines_rev}
    gdf_difference_rev = gpd.GeoDataFrame(data) # crs = "EPSG:32648"
    gdf_difference_rev = gdf_difference_rev.set_crs(gpdf_before.crs, allow_override=True)
    gdf_difference_rev["length"] = gdf_difference_rev.geometry.length
    
    
    """merge separated lines (after this, before is checked by intersection)
    """
    
    multi_rows = gpdf_before[gpdf_before.geometry.type == 'MultiLineString']
    
    if len(multi_rows) >0:
      single_lines = multi2single(gpdf_before)
      lines = list(single_lines.geometry.values)
    else:
      lines = [line.geometry for i,line in gpdf_before.iterrows()]
    
    
    src = fiona.open(before_cut_linepath)
    crs = src.crs
    driver = src.driver
    
    ## Multiline String object makes error
    check_multi = [shapely.geometry.shape(feature["geometry"]) for feature in src]
    check_multi = [l for l in check_multi if l.geom_type != "MultiLineString"]
    merged_geometries = shapely.ops.linemerge(check_multi)
    
    schema = {
        "geometry": merged_geometries.geom_type,
        "properties": {
            "length": "float"
        }}
    
    out_path = tmp_dir + "/merged.shp"
    with fiona.open(out_path, "w", driver=driver, crs=crs, schema=schema) as dest:
        dest.write({
            "geometry": shapely.geometry.mapping(merged_geometries),
            "id":"-1",
            "properties": {
                "length": merged_geometries.length
            }
        })
    
    
    data_merged = {"geometry":[merged_geometries]}
    gdf_merged = gpd.GeoDataFrame(data_merged)
    gdf_merged = gdf_merged.set_crs(gpdf_before.crs, allow_override=True)
    
    gdf_sep = gdf_merged.explode()
    gdf_sep["length"] = gdf_sep.geometry.length
    
    
    src.close()
    
    thre = 3
    gdf_sep_long = gdf_sep[gdf_sep.length>3]
    
    lines_rev = [g.geometry for i,g in gdf_sep_long.iterrows()]
    
    
    ### Collect lines before cut by intersecting or connecting #igonre <1m
    lines_to_be_cut = []
    for i,row in gdf_difference_rev.iterrows():
      if row.geometry.length > 1:
        diff_line = row.geometry
        for i, ori in gpdf_before.iterrows(): #gpdf_before_rev
          intercheck = ori.geometry.intersects(diff_line)
          if intercheck:
            to_be_cut = ori.geometry
            lines_to_be_cut.append(to_be_cut)
            #collect lines connecting with lines_to_be_cut
            for i2, ori2 in gpdf_before.iterrows(): #gpdf_before_rev
              if ori2.geometry != to_be_cut:
                intercheck2 = ori2.geometry.intersects(to_be_cut)
                if intercheck2:
                  to_be_cut2 = ori2.geometry
                  lines_to_be_cut.append(to_be_cut2)
      else:
        pass
    
    
    """# DEMでGrouping"""
    
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
      stat_dic[line] = stats_temp[0]
    
    
    max_list,min_list,mean_list,std_list,geom_list = [],[],[],[],[]
    
    for k,v in stat_dic.items():
      max_list.append(v["max"])
      min_list.append(v["min"])
      mean_list.append(v["mean"])
      std_list.append(v["std"])
      geom_list.append(k)
    
    data = {"mean":mean_list, "max":max_list, "min":min_list, "std":std_list,"geometry":geom_list}
    gdf_line_stats = gpd.GeoDataFrame(data)
    gdf_line_stats = gdf_line_stats.set_crs(gpdf_before.crs, allow_override=True)
    gdf_line_stats["length"] = gdf_line_stats.geometry.length
    
    
    gdf_sort = gdf_line_stats.sort_values(by='mean', ascending=False).reset_index()

    
    height_diff = 1
    
    max_dem_mean = gdf_sort["mean"].max()
    min_dem_mean = gdf_sort["mean"].min()
    gdf_sort["Group"] = 0 #dammy
    
    gp_num = math.ceil((max_dem_mean - min_dem_mean)/height_diff)
    for g in range(gp_num):
      range_upper = max_dem_mean - height_diff*(g)
      range_lower = max_dem_mean - height_diff*(g+1)
      for i,line in gdf_sort.iterrows():
        mean_val = line["mean"]
        if mean_val <= range_upper and mean_val >= range_lower:
          gdf_sort.iat[i,-1] = g+1
    
    
    gdf_sort["LineID"] = gdf_sort["index"] #column名
    gdf_sort["Processed"] = 0 #dammy
    gdf_sort["Pair"] = 0 #dammy
    gdf_sort["Pair2"] = 0 #dammy
    
    """vertical def"""
    
    def pointref_to_pointT2(Pref,T2_line_geoseries):
      distance = T2_line_geoseries.distance(Pref) #起点Pから直近のラインまでの距離
      PointT2 = T2_line_geoseries.interpolate(T2_line_geoseries.project(Pref)) #P0
      return PointT2, distance #GeoSeries point, [m]
    
    """#collect ID of lines_to_be_cut"""
    
    ## connecting lines with gdf_sort
    IDs=[]
    for li in lines_to_be_cut:
      for i,row in gdf_sort.iterrows():
        inter = row.geometry.intersects(li)
        if inter:
          IDs.append(i)
    
    
    #バッファー距離
    search_m = 9
    
    gdf_sort_copy = gdf_sort.copy(deep=True)
    initial_num = len(gdf_sort_copy)
    
    for lii in IDs:
      #T1
      line_1st = gdf_sort[lii:lii+1].geometry.values[0] #cut only this
    
      T1_buff = line_1st.buffer(search_m)

      inters_T2 = []
      for i, li in gdf_sort.iterrows():
        if li.geometry.intersection(T1_buff):
          inters_T2.append(li.geometry)
    
      vertical_points_list_ = []
      for inter in inters_T2:
        endpts = {}
        gdf_check2 = gdf_sort[gdf_sort['geometry'] == inter]
        grp2 = gdf_check2.Group.values[0]
        endpts[(Point(list(inter.coords[0])), Point(list(inter.coords[-1])))] = grp2
    
        inters_target = inters_T2
        # inters_target.remove(inter)
    
        vertical_p_list_ = []
        for ee, g in endpts.items():
          for tar in inters_target:
            gdf_check4 = gdf_sort[gdf_sort['geometry'] == tar]
            processed = gdf_check4.Processed.values[0]
            if processed == 0:
              gdf_check3 = gdf_sort[gdf_sort['geometry'] == tar]
              grp3 = gdf_check3.Group.values[0]
              if grp3 != g:
                for e in ee:
                  ver_p, ver_dis = pointref_to_pointT2(e, tar)
                  vertical_p_list_.append(ver_p)
              else: 
                continue
            else:
              continue
    
        if len(vertical_p_list_) >0:
          vertical_p_list = vertical_p_list_
          vertical_points_list_.append(vertical_p_list)
    
    
      vertical_points_list = [x for row in vertical_points_list_ for x in row] #解体
    
    
      coords = line_1st.coords
      j = None
    
      j_list_ = []
      for p in vertical_points_list:
        for i in range(len(coords) - 1):
          distance_line_point = LineString(coords[i:i + 2]).distance(p)
          if distance_line_point < 0.0000001:
                j = i
                j_list_.append(j)
    
      j_list = list(set(j_list_))
      j_list.sort()
    
      if len(j_list) >0:
        j_list_guu = j_list
    
        for_slice = []
        for j in range(len(j_list_guu)):
          if j ==0:
            for_sli = [0]
            sli_val = j_list_guu[j]+1
            for_sli.append(sli_val)
            for_slice.append(for_sli)
          elif j >0:
            sli_val_ = j_list_guu[j-1]
            sli_val = j_list_guu[j]+1
            for_sli = [sli_val_, sli_val]
            for_slice.append(for_sli)
    
        if [0,1] in for_slice:
          for_slice.remove([0,1])
    
        for_slice = for_slice + [[j_list_guu[-1]]]
        print(for_slice)
    
    
        for_slice_mid = [for_slice[s] for s in range(len(for_slice)) if s != len(for_slice)-1]
        for_slice_rev = [sli for sli in for_slice_mid if (sli[1]-sli[0]) >2 ] + [for_slice[-1]]

        del_sli = []
        for d in for_slice:
          if (len(d) >1) and (d not in for_slice_rev):
            del_sli.append(d)
        del_sli_ind = [for_slice.index(d) for d in del_sli]
    
        val_sli = []
        for d in for_slice:
          if d in for_slice_rev:
            val_sli.append(d)
        valid_sli_ind = [for_slice.index(d) for d in val_sli if d in for_slice]
    
        new_sli = []
        for di in del_sli_ind:
          if (di != 0) and len(for_slice[di+1])>1:
            new_0 = for_slice[di-1][1]-1
            new_1 = for_slice[di+1][1]
            new_sli.append([new_0,new_1])
    
        for_slice_ind = [r for r in range(len(for_slice))]
        for_slice_use = [r for r in for_slice_ind if (r not in del_sli_ind) and (r not in [j+1 for j in del_sli_ind])] #del_sli_indと、del_sli_ind+1の位置でもない
    
        for_slice_rev_fin_ = [for_slice[s] for s in for_slice_use] + new_sli
        for_slice_rev_fin_sort = sorted(for_slice_rev_fin_, key=lambda x:(x[0]))
        
        if len(for_slice_rev_fin_sort)>0:
          if for_slice_rev_fin_sort[-1] != for_slice[-1]:
            for_slice_rev_fin_sort = for_slice_rev_fin_sort +  [for_slice[-1]] #末尾の1要素が抜けてしまっていたら復元する
    
        ## ------------------------------------------------------------------------------
    
        slice_lines = []
        for i, sli in enumerate(for_slice_rev_fin_sort): #for_slice
          if i != len(for_slice_rev_fin_sort) -1: #for_slice
            slis = coords[sli[0] : sli[1]]
            slice_lines.append(slis)
          else:
            slis = coords[sli[-1] :]
            slice_lines.append(slis)
    
        cut_line_strings = []
        for cut in slice_lines:
          if len(cut) !=1:
            cut_line = LineString(cut)
            cut_line_strings.append(cut_line)
    
        gdf_c = gdf_sort[gdf_sort['geometry'] ==line_1st] #inters_T2[ti]
        if len(gdf_c) >0:
          gp_cut = gdf_c.Group.values[0]
          gp_ind = gdf_c.LineID.values[0]
          data_cut = {"geometry":cut_line_strings, "Group":gp_cut, "Processed":1, "LineID":gp_ind}
          gdf_cut = gpd.GeoDataFrame(data_cut)
          gdf_cut = gdf_cut.set_crs(gpdf_before.crs, allow_override=True)
    
          gdf_sort.drop(gdf_sort.loc[gdf_sort["geometry"] ==line_1st ].index, inplace=True)
          merged = pd.concat([gdf_sort, gdf_cut], ignore_index=True)
          gdf_sort = gpd.GeoDataFrame(merged, geometry='geometry')

        else:
          pass
    
      else:
        pass
    
    gdf_sort["length"] = gdf_sort.geometry.length
    
    gdf_sort_unique = gdf_sort.drop_duplicates()
    
    # #Ploting
    # fig, ax = plt.subplots(figsize=(5, 5))
    
    # # for li in cut_line_strings:
    # #   linestring_x, linestring_y = li.xy
    # #   ax.plot(linestring_x, linestring_y, color='red', label='Linestring')
    
    # for li in lines_to_be_cut:
    #   linestring_x, linestring_y = li.xy
    #   ax.plot(linestring_x, linestring_y, color='pink', label='Linestring')
    
    # #Plot buffer
    # x,y = T1_buff.exterior.xy
    # ax.plot(x, y,color='green', label='Polygon')
    
    # for p in vertical_points_list:
    #   x,y = p.xy
    #   ax.plot(x[0],y[0],"go", label='Point')
    
    """collect row of cut"""
    
    gdf_cut_done_list = []
    gdf_cut_done = gdf_sort_unique[gdf_sort_unique["index"].isna()] #Use `to_crs()` to transform geometries to the same CRS before merging.
    gdf_cut_done_list.append(gdf_cut_done)
    
    """insert them to final output"""
    
    gdf_cut_done_list.append(gpdf_after)
    gdf_cut_done_list = [g.set_crs(gpdf_before.crs, allow_override=True) for g in gdf_cut_done_list]
    gdf_vertical_result = pd.concat(gdf_cut_done_list)
    
    
    """#Export"""
    filename = os.path.basename(after_cut_linepath)[:-4]
    outfile = out_dir + os.sep + filename + "_post.shp"
    gdf_vertical_result.to_file(outfile) #crs = "EPSG:32648"
    
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )

if __name__=="__main__":
    main()