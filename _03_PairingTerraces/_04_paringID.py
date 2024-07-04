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

# line_shp_path = '/content/drive/MyDrive/Malaysia/Blueprint/12_Pairing_terraces/4_vertical_cut/centerlines_45_cut_cut2ls_merge_45_connect_merge_over5_road_sing_1_cut_cut2_vertical.shp'
# line_shp_path = sys.argv[1]
# dem_path = '/content/drive/MyDrive/Malaysia/Blueprint/DEM/02_R_Out/DEM_05m_R_kring.tif'
# out_dir = '/content/drive/MyDrive/Malaysia/Blueprint/12_Pairing_terraces/5_paring'
# os.makedirs(tmp_dir2, exist_ok=True)

def main(line_shp_path, dem_path, out_dir):
    
    start = time.time()

    gpdf = gpd.read_file(line_shp_path)
    
    
    """def Multiline to single line"""
    
    # MultiLineStringがあれば処理をする
    def multi2single(gpdf_test):
    
        # 上記のMultipolygonはたぶん削除してる
        exploded_all = gpdf_test.explode()
        exploded_reset = exploded_all.reset_index()
        columns_to_drop = ['level_0','level_1']
        gdf_dropped = exploded_reset.drop(columns=columns_to_drop)
    
        return gdf_dropped
    
    """def 二重リストをばらす"""
    def flatten_list(multi_list):
      indiv_list =[]
      for mm in multi_list:
        for m in mm:
          indiv_list.append(m)
    
      indivs = list(set(indiv_list))
      return indivs
    
    """#lines作成"""
    multi_rows = gpdf[gpdf.geometry.type == 'MultiLineString']
    
    if len(multi_rows) >0:
      single_lines = multi2single(gpdf)
      lines = list(single_lines.geometry.values)
    else:
      lines = [line.geometry for i,line in gpdf.iterrows()]
    
    """#重複削除する"""
    #0mより大きいオーバーラップがあるラインの組み合わせを抽出,つなげる
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
    
    #Lines更新
    #ばらす
    inters_pair_indiv_=[]
    for ll in inters_pair:
      for l in ll:
        inters_pair_indiv_.append(l)
    inters_pair_indiv = list(set(inters_pair_indiv_))
    
    #除外
    line_remoev = list(set(lines) ^ set(inters_pair_indiv))
    #足して更新
    lines_rev = line_remoev + concatline_list
    
    
    """# DEMでGrouping
    
    linesに同一ラインがあったことを確認したが、以下の処理で辞書のキーでなくなるのでよしとする
    """
    
    dem_src = rasterio.open(dem_path)
    raster_data = dem_src.read(1)
    transform = dem_src.transform
    
    #linesでゾーナル #元のLineIDも入れる
    stat_dic = {}
    for line in lines_rev:
      gdf_convert = gpd.GeoDataFrame(geometry=[line])
      try:
        stats_temp = zonal_stats(gdf_convert.geometry, raster_data, affine=transform, stats=["max","min","mean", "std"]) #辞書になる、リストに入る
      except: #error: height and width must be >0
        #中間地点にpointつくってそのDEM値を拾う
        center_point = line.interpolate(0.5, normalized=True)
        stats_temp = zonal_stats(center_point, raster_data, affine=transform, stats=["max","min","mean", "std"])
      LineID_ori = gpdf[gpdf["geometry"]==line]["LineID"].values[0]
      stats_temp_dic = stats_temp[0]
      stats_temp_dic["LineID"] = LineID_ori
      stat_dic[line] = stats_temp_dic
    
    
    # gdfに整形する
    max_list,min_list,mean_list,std_list,geom_list,LineID_list = [],[],[],[],[],[]
    
    for k,v in stat_dic.items():
      max_list.append(v["max"])
      min_list.append(v["min"])
      mean_list.append(v["mean"])
      std_list.append(v["std"])
      LineID_list.append(v["LineID"])
      geom_list.append(k)
    
    data = {"mean":mean_list, "max":max_list, "min":min_list, "std":std_list,"LineID":LineID_list,"geometry":geom_list}
    gdf_line_stats = gpd.GeoDataFrame(data, crs = "EPSG:32648")
    gdf_line_stats["length"] = gdf_line_stats.geometry.length
    
    """mean順に上から並べる
    
    #gdf_sort
    """
    
    gdf_sort = gdf_line_stats.sort_values(by='mean', ascending=False).reset_index(drop=True)
    
    """一番高いDEMから*m刻みでグループ化してみる"""
    
    height_diff = 1
    
    max_dem_mean = gdf_sort["mean"].max()
    min_dem_mean = gdf_sort["mean"].min()
    gdf_sort["Group2"] = 0 #dammy
    
    gp_num = math.ceil((max_dem_mean - min_dem_mean)/height_diff)
    for g in range(gp_num): #切り上げ　下端のレンジは広くなる
      range_upper = max_dem_mean - height_diff*(g)
      range_lower = max_dem_mean - height_diff*(g+1)
      for i,line in gdf_sort.iterrows():
        mean_val = line["mean"]
        if mean_val <= range_upper and mean_val >= range_lower:
          gdf_sort.iat[i,-1] = g+1
    
    #高いほどGroup小さい
    
    # line列、pair列、pair2列作成
    gdf_sort["LineID2"] = gdf_sort.index
    gdf_sort["Processed"] = 0 #dammy
    gdf_sort["Pair"] = 0 #dammy
    gdf_sort["T1T2"] = 0 #dammy
    gdf_sort["INFIL"] = 0 #dammy #infillingが必要なとき
    
    """#def
    
    垂線def
    """
    #起点Pからラインまで垂線を下ろしたときの交点
    
    def pointref_to_pointT2(Pref,T2_line_geoseries):
      distance = T2_line_geoseries.distance(Pref) #起点Pから直近のラインまでの距離
      PointT2 = T2_line_geoseries.interpolate(T2_line_geoseries.project(Pref)) #P0
      return PointT2, distance #GeoSeries point, [m]
    
    """def センターポイントから直近のラインを探す"""
    def distance_from_center_to_lines(linestring, gdf_lines):
      test_mid_point = linestring.interpolate(0.5, normalized = True) #中央に点作成
      near_dic = {}
      for testi, testli in gdf_lines.iterrows():
        if (testli.geometry != linestring): #自分じゃないとき
          near_vale_dic = {}
          test_distance = testli.geometry.distance(test_mid_point)
          LineID = testli.LineID
          Group2 = testli.Group2
          Processed = testli.Processed
          Pair = testli.Pair
          T1T2 = testli.T1T2
          INFIL = testli.INFIL
          near_vale_dic["distance"] = test_distance
          near_vale_dic["midpoint"] = test_mid_point #midpointはどの要素も同じものが入る
          near_vale_dic["LineID"] = LineID
          near_vale_dic["Group2"] = Group2
          near_vale_dic["Processed"] = Processed
          near_vale_dic["Pair"] = Pair
          near_vale_dic["T1T2"] = T1T2
          near_vale_dic["INFIL"] = INFIL

          near_dic[testli.geometry] = near_vale_dic
    
      #自身を再度抜く
    
      # distanceでソート #タプルで返される(linestring, 辞書)
      near_dic_sort = sorted(near_dic.items(), key=lambda x: x[1]["distance"])
    
      return near_dic_sort
    
    """def LineStringのIDとかの属性情報をgdf_sortから取得する  
    1本はgdf_sortから抽出するライン。もう1本は上記のnear_dic_sortのさらにfor loopで返された直近ライン情報のタプル
    """
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
    
    """def 異なるT1T2値を入れる"""
    
    def put_different_T1T2(target_linestring_1, source_tupple_val, idx_self, source_gdf=gdf_sort):
      source_T1T2 = source_tupple_val[1]["T1T2"]
      if source_T1T2 ==1:
        source_gdf.loc[idx_self,"T1T2"] = 2
      if source_T1T2 ==2:
        source_gdf.loc[idx_self,"T1T2"] = 1
    
    """def 同じT1T2入れる"""
    def put_same_T1T2(target_linestring_1, source_tupple_val, idx_self, source_gdf=gdf_sort):
      source_T1T2 = source_tupple_val[1]["T1T2"]
      source_gdf.loc[idx_self,"T1T2"] = source_T1T2
    
    """def 距離が空いていたらINFILいれる"""
    def put_Infilling(target_linestring_1, source_tupple_val, idx_self, source_gdf=gdf_sort):
      chck_distance = source_tupple_val[1]["distance"]
      if chck_distance > 14.63:
        source_gdf.loc[idx_self,"INFIL"] = 1
    
    """def 高い方にT1、低い方にT2入れる"""
    def put_lines_T1T2(idx_self, idx_partner, source_gdf=gdf_sort):
      Group_1 = source_gdf.loc[idx_self,"Group2"]
      Group_2 = source_gdf.loc[idx_partner,"Group2"]
      if Group_1 < Group_2: #1の方が高い
        source_gdf.loc[idx_self,"T1T2"] = 1
        source_gdf.loc[idx_partner,"T1T2"] = 2
      if Group_1 > Group_2: #2の方が高い
        source_gdf.loc[idx_self,"T1T2"] = 2
        source_gdf.loc[idx_partner,"T1T2"] = 1
    
    """def 1が入力されたら2を返す"""
    def convert1_2(input_int:int):
      if input_int==1:
        output =2
      if input_int==2:
        output =1
      if input_int==0:
        output =0

    
    """#実行 -T1T2だけ入れるやつ(採用)"""
    gdf_sort_copy = gdf_sort.copy(deep=True) #全く参照しない
    
    for i in range(len(gdf_sort_copy)):
    
      ### 1) centerから距離の辞書をつくる
      lin = gdf_sort[i:i+1].geometry.values[0] #一本ずつ抽出
    
      #このlinのProceesedであれば進める
      if gdf_sort.loc[gdf_sort.geometry==lin]["Processed"].values[0]==0:
        neardict = distance_from_center_to_lines(lin, gdf_sort) #タプルで返される(linestring, 辞書)
        
        ### if nearest distance >14.69, it's infilling
        if neardict[0][1]["distance"] >14.69:
            self_idx = gdf_sort.loc[gdf_sort.geometry == lin].index[0]
            gdf_sort.loc[self_idx,"T1T2"] = 1
            gdf_sort.loc[self_idx,"INFIL"] = 1
            gdf_sort.loc[self_idx,"Processed"] = 1
            continue
        
        else:
            # 0番目から近傍near_dictの要素を抽出する。普通に上下の配置なら0番目（最近傍）のみで終わる、はず
            for vi,val in enumerate(neardict):
              ##属性情報の取得
              self_attr_dic, partner_attr_dic = get_line_attributes(lin, val, source_gdf=gdf_sort)
        
              self_idx = gdf_sort.loc[gdf_sort.geometry == lin].index[0] #gdf_sort内でのインデックス取得
              partner_idx = gdf_sort.loc[gdf_sort.geometry == val[0]].index[0] #gdf_sort内でのインデックス取得
        
              ### 2)見つけたラインのLineID(ori)が異なる & ### 3) 見つけたラインのGroupが異なる -------------------------------
              if (self_attr_dic["LineID"] != partner_attr_dic["LineID"]) and (self_attr_dic["Group2"] != partner_attr_dic["Group2"]):
                ##見つけたラインのProcess=1なら（T1T2があるはず）
                if partner_attr_dic["Processed"] ==1:
                  put_different_T1T2(lin, val, self_idx, source_gdf=gdf_sort)
                  gdf_sort.loc[self_idx,"Processed"] = 1
                  break
        
                ##見つけたラインのProcess !=1異なる（T1T2がまだない）
                ## 2番目に近いラインを探して位置関係を正しくする
                for vi2 in range(vi+1,len(neardict),1):
                  self_attr_dic2, partner_attr_dic2 = get_line_attributes(lin, neardict[vi2], source_gdf=gdf_sort)
                  #2番目とLineID同じなら次の2番目探す
                  if self_attr_dic["LineID"] == partner_attr_dic2["LineID"]:
                    continue
                  #LineID異なる & Processed !=1異なる
                  if (self_attr_dic["LineID"] != partner_attr_dic2["LineID"]) and (partner_attr_dic2["Processed"]!=1):
                    #高い方に1
                    put_lines_T1T2(self_idx, partner_idx, source_gdf=gdf_sort)
                    gdf_sort.loc[self_idx,"Processed"] = 1
                    gdf_sort.loc[partner_idx,"Processed"] = 1
                    break
        
                  #LineID異なる & Processed ==1
                  if (self_attr_dic2["LineID"] != partner_attr_dic2["LineID"]) and (partner_attr_dic2["Processed"]==1):
                    #①は2番目じゃない方入れる
                    put_different_T1T2(lin, neardict[vi2], self_idx, source_gdf=gdf_sort)
                    #さいしょの②は①じゃない方のT1T2 **②に入れること
                    lin_t1t2 = gdf_sort.loc[self_idx, "T1T2"]
                    gdf_sort.loc[partner_idx, "T1T2"] = convert1_2(lin_t1t2)
                    gdf_sort.loc[self_idx,"Processed"] = 1
                    break
                else:
                    continue
                break
        
        
              ### 2)見つけたラインのLineID(ori)が異なる & ### 3) 見つけたラインのGroupが同じ -------------------------------
              if (self_attr_dic["LineID"] != partner_attr_dic["LineID"]) and (self_attr_dic["Group2"] == partner_attr_dic["Group2"]):
                continue
        
              ### 2)見つけたラインのLineID(ori)が同じ & ### 3) 見つけたラインのProcess !=1違う -------------------------------
              if (self_attr_dic["LineID"] == partner_attr_dic["LineID"]) and (partner_attr_dic["Processed"]!=1):
                continue
        
              ### 2)見つけたラインのLineID(ori)が同じ & ### 3) 見つけたラインのProcess ==1 -------------------------------
              if (self_attr_dic["LineID"] == partner_attr_dic["LineID"]) and (partner_attr_dic["Processed"]==1):
                put_same_T1T2(lin, val, self_idx, source_gdf=gdf_sort)
                gdf_sort.loc[self_idx,"Processed"] = 1
                break #neardictの直近リストから抜ける
        
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
    
    """#実行 -Pair入れるやつ"""
    #Processedをリセット
    gdf_sort["Processed"] =0
    
    gdf_sort_copy = gdf_sort.copy(deep=True) #全く参照しない
    

    for i in range(len(gdf_sort_copy)):
      ### 1) centerから距離の辞書をつくる
      lin = gdf_sort[i:i+1].geometry.values[0] #一本ずつ抽出
    
      #このlinのProceesed、かつ、T1であれば進める
      if (gdf_sort.loc[gdf_sort.geometry==lin]["Processed"].values[0]==0) and ( gdf_sort.loc[gdf_sort.geometry==lin]["T1T2"].values[0]==1):
        neardict = distance_from_center_to_lines(lin, gdf_sort) #タプルで返される(linestring, 辞書)
    
        # 0番目から近傍near_dictの要素を抽出する。普通に上下の配置なら0番目（最近傍）のみで終わる、はず
        for vi,val in enumerate(neardict):
          ##属性情報の取得
          self_attr_dic, partner_attr_dic = get_line_attributes(lin, val, source_gdf=gdf_sort)
    
          #ライン②はT2に絞る
          if partner_attr_dic["T1T2"] ==1:
            continue
    
          self_idx = gdf_sort.loc[gdf_sort.geometry == lin].index[0] #gdf_sort内でのインデックス取得
          partner_idx = gdf_sort.loc[gdf_sort.geometry == val[0]].index[0] #gdf_sort内でのインデックス取得
    
          ### 2)見つけたラインのLineID(ori)が異なる & ### 3) 見つけたラインのGroupが異なる -------------------------------
          if (self_attr_dic["LineID"] != partner_attr_dic["LineID"]) and (self_attr_dic["Group2"] != partner_attr_dic["Group2"]):
            ##distanceがInfillか
            if val[1]["INFIL"] ==1:
              # gdf_sort.loc[self_idx,"INFIL"] = 1
              gdf_sort.loc[self_idx,"Pair"] = -99
              gdf_sort.loc[self_idx,"Processed"] = 1
              break
            else:
              ## 見つけたラインのProcess=0なら
              group1 = self_attr_dic["Group2"]
              group2 = partner_attr_dic["Group2"]
              if partner_attr_dic["Processed"] ==0:
                #①が高ければPair入れる
                if group1 < group2:
                  gdf_sort.loc[self_idx,"Pair"] = i+1
                  gdf_sort.loc[partner_idx,"Pair"] = i+1
                  gdf_sort.loc[self_idx,"Processed"] = 1
                  gdf_sort.loc[partner_idx,"Processed"] = 1
                  break
                #①が低ければ次に近いのを探す
                if group1 > group2:
                  continue
    
              ## 見つけたラインのProcess=1なら
              if partner_attr_dic["Processed"] ==1:
                if group1 < group2:
                  pair2 = gdf_sort.loc[partner_idx,"Pair"]
                  gdf_sort.loc[self_idx,"Pair"] = pair2
                  gdf_sort.loc[self_idx,"Processed"] = 1
                  break
                if group1 > group2:
                  continue
    
          ### 2)見つけたラインのLineID(ori)が同じ & ### 3) 見つけたラインがProcessed=0----------------------------------------------------
          if (self_attr_dic["LineID"] == partner_attr_dic["LineID"]) and (partner_attr_dic["Processed"]==0):
            continue
    
          ### 2)見つけたラインのLineID(ori)が同じ & ### 3) 見つけたラインがProcessed==1----------------------------------------------------
          if (self_attr_dic["LineID"] == partner_attr_dic["LineID"]) and (partner_attr_dic["Processed"]==1):
            continue
    
    """#実行 Pair T2の処理漏れ対処
    案1(続けて案2が必要) 今のところこっち
    """
    #処理漏れT2は隣接するラインの属性を入れる. #隣接がT1だったらその次の直近のT2にする
    
    gdf_T2_0 = gdf_sort[(gdf_sort["Pair"]==0) & (gdf_sort["T1T2"]==2)] #抽出
    gdf_sort_copy = gdf_T2_0 #全く参照しない
    
    for i in range(len(gdf_sort_copy)):
      # print(i)
      ### 1) centerから距離の辞書をつくる
      lin = gdf_T2_0[i:i+1].geometry.values[0] #一本ずつ抽出
    
      #隣接を探す. あったら次に進む
      for i, row in gdf_sort.iterrows():
        lin_sort = row.geometry
        if lin.intersects(lin_sort):
          reference_line = lin_sort
          #referenceにPairが入っていること確認
          reference_pair = row.Pair
          if reference_pair != 0:
            break
    
      self_idx = gdf_sort.loc[gdf_sort.geometry == lin].index[0] #gdf_sort内でのインデックス取得
      gdf_sort.loc[self_idx, "Pair"] = reference_pair
    
    """案1の次に実行(これだけでいいかもしれないがまだ要検討)
    
    孤立してて0のままのT2は直近のT1（高い位置）のPairとする
    """
    gdf_T2_0 = gdf_sort[(gdf_sort["Pair"]==0) & (gdf_sort["T1T2"]==2)] #抽出
    gdf_sort_copy = gdf_T2_0 #全く参照しない
    
    for i in range(len(gdf_sort_copy)):
      ### 1) centerから距離の辞書をつくる
      lin = gdf_T2_0[i:i+1].geometry.values[0] #一本ずつ抽出
    
      neardict = distance_from_center_to_lines(lin, gdf_sort)
      self_idx = gdf_sort.loc[gdf_sort.geometry == lin].index[0]
    
      #0番目のT1、かつGroup1はT1が高い位置
      for vi, val in enumerate(neardict):
        self_attr_dic, partner_attr_dic = get_line_attributes(lin, val, source_gdf=gdf_sort)
        if (partner_attr_dic["T1T2"] ==1) and (partner_attr_dic["Group2"] < self_attr_dic["Group2"]):
          gdf_sort.loc[self_idx, "Pair"] = partner_attr_dic["Pair"]
          gdf_sort.loc[self_idx, "Processed"] = 1
          break
        else:
          continue
    
    
    """#Export"""
    filename = os.path.basename(line_shp_path)[:-4]
    outfile = out_dir + "/" + filename + "_T1T2.shp"
    gdf_sort.to_file(outfile, crs = "EPSG:32648")
    
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )

if __name__=="__main__":
    main()