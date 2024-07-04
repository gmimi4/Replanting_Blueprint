# -*- coding: utf-8 -*-
"""02_cut_intersects_2lines_pairing.ipynb
2本のラインのなす角が狭かったらエラーとして、短い方を(8m)バッファーで切る
"""

import os
from shapely.geometry import Point, LineString, Polygon,MultiPoint, MultiLineString
import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np
import itertools
import glob
# import glob

# out_dir = r'D:\Malaysia\01_Brueprint\12_Pairing_terraces\2_cut\2_2cut'

# lines_list = glob.glob(line_dir+"/*.shp")
# line_shp_path = r"D:\Malaysia\01_Brueprint\12_Pairing_terraces\2_cut\1_3cut\_test\_centerlines_45_cut_cut2ls_merge_45_06_connect_sq_cut.shp"
# line_shp_path = sys.argv[1]

def main(line_shp_path, out_dir):

    def multi2single(gpdf_test):
        gpdf_multiline = gpdf_test[gpdf_test.geometry.type == 'MultiLineString']
    
        exploded_all = gpdf_test.explode()
        exploded_reset = exploded_all.reset_index()
        columns_to_drop = ['level_0','level_1']
        gdf_dropped = exploded_reset.drop(columns=columns_to_drop)
    
        return gdf_dropped
    
    """#linesをsingle featureにする
    """
    
    gpdf = gpd.read_file(line_shp_path)
    # make sure gpdf does not have none row
    gpdf = gpdf[gpdf.geometry != None]
    
    multi_rows = gpdf[gpdf.geometry.type == 'MultiLineString']
    
    if len(multi_rows) >0:
      single_lines = multi2single(gpdf)
      lines = list(single_lines.geometry.values)
    else: #no multiLinestring
      # lines = [shape(line.geometry) for line in fiona.open(line_shp_path,'r')]
      lines = [g.geometry for i,g in gpdf.iterrows()]
    
    """#角度で絞る"""
    
    def unit_vector(vector): #array座標でよいと思う
        """ Returns the unit vector of the vector.  """
        return vector / np.linalg.norm(vector) #np.linalg.norm() #default is None: ユークリッド(長さ)
    
    def angle_between(v1, v2):
        v1_u = unit_vector(v1)
        v2_u = unit_vector(v2)
        return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))) #np.dot: 内積を計算, #np.clip: min, maxにそろえる, #np.arccos: 逆コサイン
    
    """#2本のラインと交点のセットを探す"""
    
    inters_pair = []
    # ライン2つと交点を抽出する
    for line1, line2 in itertools.combinations(lines,2): #２つ取り出す組み合わせ(順不同)
      if line1.intersects(line2):
        inter = line1.intersection(line2)
        if "Point" == inter.type:
          inters_pair.append([inter, line1,line2])
        else:
          pass
    
    
    """直近座標から抽出"""
    
    error_lines_ori = []
    angle_thre = 45#60
    
    #直近座標から抽出
    for pair in inters_pair:
      #交点から最も近い座標をそれぞれのラインから2つ抽出し、直線をつくる
      line_1_x, line_1_y = pair[1].coords.xy[0], pair[1].coords.xy[1] #x,yのarray
      line_2_x, line_2_y = pair[2].coords.xy[0], pair[2].coords.xy[1] #
      point_x, point_y = pair[0].coords.xy[0], pair[0].coords.xy[1]
      dist_1 = np.sqrt((np.array(line_1_x) - np.array(point_x))**2 + (np.array(line_1_y) - np.array(point_y))**2)
      dist_2 = np.sqrt((np.array(line_2_x) - np.array(point_x))**2 + (np.array(line_2_y) - np.array(point_y))**2)
      # get index
      arg_indx_1 = dist_1.argsort()#[::-1] #遠い順に並べる場合[::-1]
      idx_1 = np.where(arg_indx_1==1)[0] #交点から（交点箇所以外で）"1番目に遠い"Linestringの座標 *近すぎるとうまくいかない?
      arg_indx_2 = dist_2.argsort()#[::-1]
      idx_2 = np.where(arg_indx_2==1)[0]
    
      # make new vector from lines #交点を原点ゼロとしたベクトル
      vec_1_ = (np.array(line_1_x)[idx_1] - np.array(point_x),  np.array(line_1_y)[idx_1] - np.array(point_y))
      vec_1 = (vec_1_[0][0], vec_1_[1][0])
      vec_2_ = (np.array(line_2_x)[idx_2] - np.array(point_x),  np.array(line_2_y)[idx_2] - np.array(point_y))
      vec_2 = (vec_2_[0][0], vec_2_[1][0])
      angle = angle_between(vec_1, vec_2)
    
      if angle < (180-angle_thre): #エラーラインの抽出
        test_dic = {1:pair[1].length, 2:pair[2].length}
        min_test = min(pair[2].length, pair[1].length) #なす角度が大きいペアのうち短い方をエラーラインとする
        error_index = [k for k,v in test_dic.items() if v== min_test][0]
        error_line = pair[error_index]
        error_lines_ori.append([pair[0], error_line]) #error lineを集める, ポイントとセットにする
    
    len(error_lines_ori)
    
    """#交点からbuff_distanceの距離まで最短ラインを切る（Arcで言うerase）"""
    
    #短いラインを切る    
    buff_distance = 1
    cut_lines =[]
    
    for i,lin in enumerate(error_lines_ori):
     # buffer作成
      inter_point = lin[0]
      target = lin[1]
      buff_poly = inter_point.buffer(buff_distance)
      # まずgdfに変換する
      data_poly = {"geometry":[buff_poly]}
      gdf_buff = gpd.GeoDataFrame(data_poly, geometry="geometry")
    
      data_line = {"geometry":[target]}
      gdf_tar_line = gpd.GeoDataFrame(data_line, geometry="geometry")
      cut_tar_line = gdf_tar_line.difference(gdf_buff).values[0] #ここで実行。切られたLine Stringになる
    
      cut_lines.append(cut_tar_line)
    
    
    """#error line orijinalとcutしたerror lineを置換する"""
    #ばらす
    error_lines_ori_individual = [e[1] for e in error_lines_ori]
    
    #empty除外
    cut_lines_individual = [c for c in cut_lines if c.length>0]
    
    #cut_linesからerrorlines_oriをまず消す
    cut_line_remove = list(set(lines) - set(error_lines_ori_individual))
    
    #cutしたラインを足す
    cut_line_results = cut_line_remove + cut_lines_individual
    
    #Plot for check
    # fig = plt.figure(figsize=(8, 8))
    
    #----------------
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
    # ax2.set_title("error_lines_ori_individual")
    # name = error_lines_ori_individual
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
    # ax4.set_title("cut_lines_individual")
    # name = cut_lines_individual
    # linestring_x_ =[]
    # linestring_y_ =[]
    # for i in range(len(name)):
    #   line_x, line_y = name[i].xy
    #   linestring_x_.append(line_x)
    #   linestring_y_.append(line_y)
    # #lines
    # for i in range(len(name)):
    #   ax4.plot(linestring_x_[i], linestring_y_[i], color = 'aquamarine', label='Linestring')
    
    # for a in [ax1,ax2,ax3,ax4]:
    #   for i in range(len(inters_pair)):
    #     a.plot(inters_pair[i][0].x, inters_pair[i][0].y, 'ro', label='Point')
    
    """#Export to shp"""
    
    gdf_export = gpd.GeoDataFrame(geometry=cut_line_results)
    gdf_export.crs = 'epsg:32648'
    gdf_export["length"] = gdf_export.geometry.length
    
    outfile = os.path.join(out_dir, os.path.basename(line_shp_path)[:-4] +f"_cut2.shp")
    gdf_export.to_file(outfile)


if __name__=="__main__":
    main()