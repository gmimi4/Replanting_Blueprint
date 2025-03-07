# -*- coding: utf-8 -*-
"""
delete points too close each other
delete points within road if it is endpoint
"""

import os
import glob
from tqdm import tqdm
import geopandas as gpd
import pandas as pd
import time



def main(in_dir, road_shp, close_thre):
    start = time.time()
    
    """# merge"""
    shps = glob.glob(os.path.join(in_dir, "*.shp"))

    out_dir = in_dir + os.sep + f"merge_{close_thre}m"
    os.makedirs(out_dir, exist_ok=True)

    gdfs = [gpd.read_file(shp) for shp in shps]
    merged_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)


    """# Delete points within 6ft from road # a little bit shorter than 6ft
    """
    close_limit = close_thre

    #add Processed field
    merged_gdf["Processed"]=0
    merged_gdf["del"]=0
    merged_gdf['buffer'] = merged_gdf['geometry'].buffer(close_limit)
  
    gdf_points = merged_gdf
    gdf_road = gpd.read_file(road_shp)

    road_distance = 6*0 #rev not eliminate points within 6ft unless endpoints
    road_buff = gdf_road.buffer(road_distance)
    gdf_road_buff = gpd.GeoDataFrame(geometry=road_buff)

    gdf_road_buff["tmp"] = 1
    gdf_road_dissolve = gdf_road_buff.dissolve(by='tmp')

    ### Polygon #use this
    buff_boundary = gdf_road_dissolve.geometry.values[0]

    ## exclude points within buffer
    valid_ps = gdf_points[~buff_boundary.contains(gdf_points.geometry)]

    
    """ # Delete too clopse points 
    """
    #add Processed field
    valid_ps["Processed"]=0
    valid_ps["del"]=0
    valid_ps['buffer'] = valid_ps['geometry'].buffer(close_limit)

    for i,row in tqdm(valid_ps.iterrows()):
      # print(i)
      if row.Processed != 1:
        buff_poly = row.buffer
        gdf_buff = gpd.GeoDataFrame({"geometry":[buff_poly]})
        gdf_buff = gdf_buff.set_crs(merged_gdf.crs, allow_override=True)
        
        points_within = gpd.sjoin(valid_ps, gdf_buff, predicate='within')
        points_within_list = points_within.geometry.tolist()
        points_valid = [p for p in points_within_list if p != row.geometry]
        points_valid2 = [p for p in points_valid if valid_ps[valid_ps.geometry==p].Processed.values[0] == 0]
        # print(len(points_within_list), len(points_valid),len(points_valid2))
        idxes_del = valid_ps[valid_ps.geometry.isin(points_valid2)].index.tolist() #自身以外のひっかかるポイントのidx
        valid_ps.loc[idxes_del,"del"] =1
        idxes_all = idxes_del + [i]
        valid_ps.loc[idxes_all,"Processed"] =1
      else:
        continue

    gdf_points_fin = valid_ps[~(valid_ps["del"] == 1)]

    points_fin = gdf_points_fin.geometry.tolist()

    #export points
    geometry = gpd.GeoSeries(points_fin)
    gdf = gpd.GeoDataFrame(geometry=geometry, columns=['geometry'])

    #Final Export
    gdf = gdf.set_crs(merged_gdf.crs, allow_override=True)
    outfile = os.path.join(out_dir, "merge_all_points_6ftfin.shp")
    gdf.to_file(outfile)
    
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )


if __name__ =="__main__":
    main()
    
    
