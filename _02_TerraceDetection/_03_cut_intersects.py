# -*- coding: utf-8 -*-
"""
Cut 3 intersecting and shorted line by 8 m
"""

import os
from shapely.geometry import Point, LineString, Polygon,MultiPoint, MultiLineString
from shapely.geometry import shape
import geopandas as gpd
import numpy as np
import pandas as pd
import itertools
import glob
import collections
import time

# line_dir = r'D:\Malaysia\01_Brueprint\09_Terrace_detection\9_filterd_line\_divided'
# out_dir = r'D:\Malaysia\01_Brueprint\09_Terrace_detection\10_cut_by_intersect'
# epsg_use = 'epsg:32648'

# lines_list = glob.glob(line_dir+"/*.shp")
# line_shp_path = lines_list[10]
# # line_shp_path = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\9_filterd_line\_divided\centerlines_45_00.shp"


def main(line_shp_path, out_dir):
    start = time.time()
    
    # ultiLineString
    def multi2single(gpdf_test):
        exploded_all = gpdf_test.explode(index_parts=True)
        exploded_reset = exploded_all.reset_index()
        columns_to_drop = ['level_0','level_1']
        gdf_dropped = exploded_reset.drop(columns=columns_to_drop)
    
        return gdf_dropped
    

    gpdf = gpd.read_file(line_shp_path)
    
    multi_rows = gpdf[gpdf.geometry.type == 'MultiLineString']
    
    if len(multi_rows) >0:
      single_lines = multi2single(gpdf)
      lines = list(single_lines.geometry.values)
    else:
      lines = [li.geometry for row, li in gpdf.iterrows()] #No multiLinestring
    
    ## remove None type
    lines = [li for li in lines if li is not None]
    """#　Collect 3 lines and their intersection"""    
    inters_pair = []
    inters_lines = []
    # ライン3つと交点を抽出する
    for line1, line2,line3 in itertools.combinations(lines,3): #3つ取り出す組み合わせ(順不同)
      if line1.intersects(line2) and line1.intersects(line3) and line2.intersects(line3):
        inter1 = line1.intersection(line2)
        inter2 = line1.intersection(line3)
        inter3 = line2.intersection(line3)
        if inter1==inter2 and inter2==inter3 and "Point" == inter1.type:
          inters_pair.append([inter1, line1,line2, line3])
          inters_lines.append([line1,line2,line3])
        else:
          pass
    
    """#Collect lines which were not selected"""
    # Selected lines 選ばれたライン(ばらしてリストへ)
    individual_inters_lines = []
    for lis in inters_lines:
      for l in lis:
        individual_inters_lines.append(l)
    
    individual_inters_lines_set = set(individual_inters_lines)
    
    #Not selected lines選ばれなかったライン
    line_non_inters = list(set(individual_inters_lines_set)^set(lines))
    
    """#Erasing the shortest line from the intersection to buff_distance"""
    #短いラインを切る（1つだと残るかも）
    
    buff_distance = 8
    cut_lines =[]
    cut_lines_oris =[]
    long_lines =[]
    
    for i,lins in enumerate(inters_lines):
      tmp_list =[li.length for li in lins]
      tmp_array = np.array(tmp_list)
      index_sort = tmp_array.argsort() #小さい順に並んでる
      shortest_id_list = list(index_sort[0:1]) #[0:1]短い1本、[0:2]短い2本
      target_lines = [lins[i] for i in shortest_id_list] #切るライン
     # buffer作成
      inter_point = inters_pair[i][0]
      buff_poly = inter_point.buffer(buff_distance)
    
      # まずgdfに変換する
      cut_tar_lines =[]
      cut_line_ori =[]
      data_poly = {"geometry":[buff_poly]}
      gdf_buff = gpd.GeoDataFrame(data_poly, geometry="geometry")
      for target in target_lines:
        data_line = {"geometry":[target]}
        gdf_tar_line = gpd.GeoDataFrame(data_line, geometry="geometry")
        cut_tar_line_ori = target #これが他の組み合わせのときのlongにならない必要がある
        cut_tar_line = gdf_tar_line.difference(gdf_buff).values[0] #ここで実行。切られたLine Stringになる
        cut_tar_lines.append(cut_tar_line)
        cut_line_ori.append(cut_tar_line_ori)
        #ここまでで3本ラインセットのうち短いものとそのオリジナルのリストを作成（内輪リスト）
    
      #長いものを全体リストに入れる
      if len(shortest_id_list) == 2: #短いの2つcutの場合
        long_line = [li for i,li in enumerate(lins) if i == index_sort[2]] #index_sort[2]
        long_lines.append(long_line) #長いものの全体リスト
    
      if len(shortest_id_list) == 1: #短いの1つcutの場合
        long_line = [li for i,li in enumerate(lins) if i != shortest_id_list[0]]
        long_lines.append(long_line) #長いものの全体リスト
    
      cut_lines.append(cut_tar_lines) #切ったラインリストを全体リストへ
      cut_lines_oris.append(cut_line_ori) #切られたラインのオリジナルリスト
    
    
    """To individual lines"""
    def individuals(bunch_list):
        individual_list = []
        for cut in bunch_list:
          for c in cut:
            individual_list.append(c)
        return individual_list
        
    cut_lines_individual = individuals(cut_lines)
    cut_lines_ori_individual = individuals(cut_lines_oris)
    long_lines_individual = individuals(long_lines)
    
    
    """# Correct duplicated shorted lines 最短ラインの重複を解消する
    
    まず重複している組み合わせを抽出する
    """
    
    #同じshortを選んでいる組み合わせを見つける(oriを抽出)
    cut_collections = collections.Counter(cut_lines_ori_individual) #valkueと個数の組み合わせ
    same_short = [k for k,c in cut_collections.items() if c>1] #2回以上選ばれたLindStringのリスト(values)
    
    #そのLinestring(value)がどのindexなのか探す
    same_idx_list = []
    for same in same_short:
      idx_list =[]
      for i,ori in enumerate(inters_lines):
        try:
          same_idx = [ori.index(same)] #これは3本の中でのindex
          if len(same_idx) >0:
            idx_list.append(i)
        except ValueError:
          pass
      idx_list_set = list(set(idx_list))
      same_idx_list.append(idx_list_set)
    
    
    """ Overlaying lines were found. 
    Collect lines to be replaced with overlaying lines.
    Overlayしていたのであとで差し替えるcut済み最短ラインを抽出"""
    
    #overlayしてる2本をcutlinesから抽出(あとで消すやつ)
    overlays_list = []
    for idxs in same_idx_list:
      overlays=[]
      for i in idxs:
        overlays.append(cut_lines[i][0])
      overlays_list.append(overlays)
    
    # overlays_list #already cut
    
    overlays_list_individual = [item for sublist in overlays_list for item in sublist]
    
    """ Extract and remain overlaying parts
    Overlay部分だけを抽出して残す"""
    
    #overlay部分だけを抽出して残す
    overlay_part =[]
    for over in overlays_list:
      part = over[0].intersection(over[1]) #intersectionだと切り出し、intersectだとTrueっていう出力だった
      part2 = part.intersection(over[0])
      overlay_part.append(part2)
    
    # overlay_part #to be used
    
    # Correct Multistring, and connect
    overlay_results=[]
    for mul in overlay_part:
        if not not mul:
          test_data = {"geometry":[mul]}
          test_part_gdf = gpd.GeoDataFrame(test_data, geometry="geometry")
          test_gdf = multi2single(test_part_gdf)
        
          # To one Linestring
          coords_list = []
          for i,l in test_gdf.iterrows():
            coordss = list(l.geometry.coords)
            coords_list.append(coordss)
        
          connected_coords = []
          for co in coords_list:
            connected_coords.append(co[0])
        
          connected_line = LineString(connected_coords)
          overlay_results.append(connected_line)
    
    # overlay_results # to be used
    
    """ Replaced oevrlaying lines with corrected lines
    lines あとで消すやつで抽出したラインとoverlay_resultを置換する"""
    # delete cut_lines first
    cut_line_remove = list(set(cut_lines_individual) - set(overlays_list_individual))
    # add lines in overlayをつなげたラインを足す
    cut_line_results = cut_line_remove + overlay_results
    
    
    """# remove long lines if same cut lines exist
    longからcut_oriと同じものがあれば消す"""
    #longからcut_oriと同じものがあれば消す
    long_set = list(set(long_lines_individual) - set(cut_lines_ori_individual))
    
    # long_setにshortのが残ってるので、long_setとcut_line_resultsがintersectしてたら消すことにする
    
    long_clean = long_set
    
    """# Merge Lines"""
    lines_after_cut = line_non_inters + cut_line_results + long_clean
    
    
    """#Export to shp"""
    gdf_export = gpd.GeoDataFrame(geometry=lines_after_cut)
    # gdf_export.crs = epsg_use
    gdf_export = gdf_export.set_crs(gpdf.crs, allow_override=True)
    gdf_export["length"] = gdf_export.geometry.length
    
    outfile = os.path.join(out_dir, os.path.basename(line_shp_path)[:-4] +"_cut.shp")
    gdf_export.to_file(outfile)
    
    end = time.time()
    time_diff = end - start
    print(time_diff/60, "min")
    

if __name__=="__main__":
    main()