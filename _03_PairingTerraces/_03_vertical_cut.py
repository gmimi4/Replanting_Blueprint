# -*- coding: utf-8 -*-


import math
import os
import shapely
from shapely.geometry import Point, LineString, Polygon,MultiPoint, MultiLineString
from shapely.geometry import shape
# import matplotlib.pyplot as plt
import fiona
import geopandas as gpd
import pandas as pd
import rasterio
from rasterstats import zonal_stats
import time



def main(line_shp_path, out_dir, dem_path):
    start = time.time()
    tmp_dir =os.path.join(out_dir,"3_merge_and_separated")
    os.makedirs(tmp_dir, exist_ok=True)
    
    gpdf = gpd.read_file(line_shp_path)
    
    def multi2single(gpdf_test):
    
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
    
    
    lines = [shape(line.geometry) for line in fiona.open(line_shp_path,'r')]
    
    """#Connect all lines #muletiline, then to single lines
    """
    
    src = fiona.open(line_shp_path)
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
    gdf_merged = gdf_merged.set_crs(gpdf.crs, allow_override=True) 
    
    gdf_sep = gdf_merged.explode()
    gdf_sep["length"] = gdf_sep.geometry.length
    
    
    src.close()
    
    """delete short isolated line"""
    thre = 3
    gdf_sep_long = gdf_sep[gdf_sep.length>thre]
    
    lines_rev = [g.geometry for i,g in gdf_sep_long.iterrows()]
    
    # #Plot for check
    # fig = plt.figure(figsize=(5, 5))
    
    # #----------------
    # ax1 = fig.add_subplot(1,1,1)
    # name = lines_rev
    # ax1.set_title("lines_rev")
    # linestring_x_ =[]
    # linestring_y_ =[]
    # for i in range(len(name)):
    #   line_x, line_y = name[i].xy
    #   linestring_x_.append(line_x)
    #   linestring_y_.append(line_y)
    # for i in range(len(name)):
    #   ax1.plot(linestring_x_[i], linestring_y_[i], color = 'aquamarine', label='Linestring')
    
    """# Grouping by DEM"""
    
    dem_src = rasterio.open(dem_path)
    raster_data = dem_src.read(1)
    transform = dem_src.transform
    
    stat_dic = {}
    for line in lines_rev:
      gdf_convert = gpd.GeoDataFrame(geometry=[line])
      try:
        stats_temp = zonal_stats(gdf_convert.geometry, raster_data, affine=transform, stats=["max","min","mean", "std"]) #辞書になる、リストに入る
      except: #error: height and width must be >0
        #create center point to collect dem value
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
    gdf_line_stats = gdf_line_stats.set_crs(gpdf.crs, allow_override=True)
    gdf_line_stats["length"] = gdf_line_stats.geometry.length
    
    """sort by mean from high ele
    #gdf_sort
    """    
    gdf_sort = gdf_line_stats.sort_values(by='mean', ascending=False).reset_index()

    
    """Groupding by *m step"""
    
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
    
    #small Group number for high ele    
    gdf_sort["LineID"] = gdf_sort["index"] #column名
    gdf_sort["Processed"] = 0 #dammy
    gdf_sort["Pair"] = 0 #dammy
    gdf_sort["Pair2"] = 0 #dammy
    
    """vertical def"""
    def pointref_to_pointT2(Pref,T2_line_geoseries):
      distance = T2_line_geoseries.distance(Pref) #from P to nearest line
      PointT2 = T2_line_geoseries.interpolate(T2_line_geoseries.project(Pref)) #P0
      return PointT2, distance #GeoSeries point, [m]
    
    
    """#Collect neghboring line by Buffer"""
    search_m = 9
    
    gdf_sort_copy = gdf_sort.copy(deep=True)
    initial_num = len(gdf_sort_copy)
    
    for lii in range(initial_num):
      print(lii)
      #T1
      line_1st = gdf_sort[lii:lii+1].geometry.values[0]
    
      T1_buff = line_1st.buffer(search_m)
    
      inters_T2 = []
      for i, li in gdf_sort.iterrows():
        if li.geometry.intersection(T1_buff):
          inters_T2.append(li.geometry)
    
      ## ------------- cut each other by endpoints --------------------
      #collect intersecting points from endpoints to line
      vertical_points_list_ = []
      for inter in inters_T2: #including T1
        endpts = {}
        gdf_check2 = gdf_sort[gdf_sort['geometry'] == inter]
        grp2 = gdf_check2.Group.values[0]
        endpts[(Point(list(inter.coords[0])), Point(list(inter.coords[-1])))] = grp2 #各endpointのセットタプルがkey（リストだとえらー）, Groupが値の辞書
    
        #vertical line
        inters_target = inters_T2
    
        vertical_p_list_ = []
        for ee, g in endpts.items():
          for tar in inters_target:
            gdf_check4 = gdf_sort[gdf_sort['geometry'] == tar]
            processed = gdf_check4.Processed.values[0]
            if processed == 0:
              gdf_check3 = gdf_sort[gdf_sort['geometry'] == tar]
              grp3 = gdf_check3.Group.values[0]
              if grp3 != g: #avoid same Group from making vertical cut
                for e in ee:
                  ver_p, ver_dis = pointref_to_pointT2(e, tar) #P0
                  vertical_p_list_.append(ver_p)
    
        if len(vertical_p_list_) >0:
          vertical_p_list = vertical_p_list_
          vertical_points_list_.append(vertical_p_list)
    
    
      vertical_points_list = [x for row in vertical_points_list_ for x in row] #解体
    

      for ti in range(len(inters_T2)):
        coords = inters_T2[ti].coords
        j = None
    
        j_list_ = []
        for p in vertical_points_list:
          for i in range(len(coords) - 1):
            distance_line_point = LineString(coords[i:i + 2]).distance(p) #intersects cannot work?
            if distance_line_point < 0.0000001: #very small distance
                  j = i
                  j_list_.append(j)
    
        j_list = list(set(j_list_))
        j_list.sort()
    
        if len(j_list) >0: #at least one intersection
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
    
          #remove [0,1]
          if [0,1] in for_slice:
            for_slice.remove([0,1])
    
          for_slice = for_slice + [[j_list_guu[-1]]]
    
          ## ---- for_slice, 2 datapoint will be very short and delete such ones -------------------
          for_slice_mid = [for_slice[s] for s in range(len(for_slice)) if s != len(for_slice)-1] #最後の1要素だけのを除いたリスト
          for_slice_rev = [sli for sli in for_slice_mid if (sli[1]-sli[0]) >2 ] + [for_slice[-1]]
          #find false index
          del_sli = []
          for d in for_slice:
            if (len(d) >1) and (d not in for_slice_rev):
              del_sli.append(d)
          del_sli_ind = [for_slice.index(d) for d in del_sli]
    
          #find true index
          val_sli = []
          for d in for_slice:
            if d in for_slice_rev:
              val_sli.append(d)
          valid_sli_ind = [for_slice.index(d) for d in val_sli if d in for_slice]
    
          #remake
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
    
          #confirm for valid slice
          if len(for_slice_rev_fin_sort)>0:
            if for_slice_rev_fin_sort[-1] != for_slice[-1]:
              for_slice_rev_fin_sort = for_slice_rev_fin_sort +  [for_slice[-1]] #末尾の1要素が抜けてしまっていたら復元する
    
            ## ------------------------------------------------------------------------------
    
            #collect coords after cut
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
    
    
            #input same Group
            gdf_c = gdf_sort[gdf_sort['geometry'] == inters_T2[ti]]
            if len(gdf_c) >0: #?
              gp_cut = gdf_c.Group.values[0]
              gp_ind = gdf_c.LineID.values[0]

              data_cut = {"geometry":cut_line_strings, "Group":gp_cut, "Processed":1, "LineID":gp_ind} #処理済みを入れる
              gdf_cut = gpd.GeoDataFrame(data_cut)
              gdf_cut = gdf_cut.set_crs(gpdf.crs, allow_override=True)
    
              # remove inters_T2[ti] from gdf and replace with cut_line_strings
              gdf_sort.drop(gdf_sort.loc[gdf_sort["geometry"] == inters_T2[ti]].index, inplace=True) #古いライン削除
              merged = pd.concat([gdf_sort, gdf_cut], ignore_index=True) #新しいラインs挿入
              gdf_sort = gpd.GeoDataFrame(merged, geometry='geometry')
              
    
          else:
            continue
    
        else: #len(j_list) 0: #no intersection
          pass
    
    gdf_sort["length"] = gdf_sort.geometry.length
    
    gdf_sort_unique = gdf_sort.drop_duplicates()

    
    # #Ploting
    # fig, ax = plt.subplots(figsize=(5, 5))
    
    # # Plot the linestring
    # # for li in lines_gp_tests:
    # #   linestring_x, linestring_y = li.xy
    # #   ax.plot(linestring_x, linestring_y, color='blue', label='Linestring')
    
    # for li in inters_T2:
    #   linestring_x, linestring_y = li.xy
    #   ax.plot(linestring_x, linestring_y, color='red', label='Linestring')
    
    # for li in inters_target:
    #   linestring_x, linestring_y = li.xy
    #   ax.plot(linestring_x, linestring_y, color='pink', label='Linestring')
    
    # #Plot buffer
    # x,y = T1_buff.exterior.xy
    # ax.plot(x, y,color='green', label='Polygon')
    
    """#Export"""
    
    gdf_sort_unique = gdf_sort_unique.set_crs(gpdf.crs, allow_override=True)
    filename = os.path.basename(line_shp_path)[:-4]
    outfile = os.path.join(out_dir, filename + "_vertical.shp")
    gdf_sort_unique.to_file(outfile) #crs = "EPSG:32648"
    
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )


if __name__=="__main__":
    main()