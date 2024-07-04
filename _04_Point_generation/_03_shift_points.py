# -*- coding: utf-8 -*-
"""
ensure 3 ft from wall of backslope
shift points 3ft using U-Net output based polygon
"""

import os
import shapely
from shapely.geometry import Point, LineString, MultiLineString, Polygon,MultiPoint,MultiPolygon,LinearRing
# import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np
import rasterio
from tqdm import tqdm
import time


# point_shp = r"D:\Malaysia\01_Brueprint\13_Generate_points\merge_allpoints_fin_6ft_targetarea.shp"
# unet_poly = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\3_dilation\mosaic_e5_d2_clip_arc.shp"
# dem_path = r"D:\Malaysia\01_Brueprint\05_R_DEM\DEM_05m_R_kring.tif"
# out_dir = r'D:\Malaysia\01_Brueprint\13_Generate_points\02_shift_3ft'


def main(point_shp, unet_poly, dem_path, out_dir):
    start = time.time()
    
    gdf_points = gpd.read_file(point_shp)
    gdf_poly = gpd.read_file(unet_poly)
    
    ### dem
    ele_dic ={}
    src = rasterio.open(dem_path)
    arr = src.read(1)
    
            
    """ # vertical line from point to polygon"""
    new_points =[]
    for i, row in tqdm(gdf_points.iterrows()):
        # test_p = gdf_points.loc[0].geometry
        test_p = row.geometry
        gdf_testp = gpd.GeoDataFrame({"geometry":[test_p]})
        
        try:    
            # and clip for making smaller area
            test_p_buff = test_p.buffer(10)
            gdf_poly_clip = gpd.clip(gdf_poly, test_p_buff)
            # extract polygon used for terraces
            gdf_poly_terr = gdf_poly_clip[gdf_poly_clip.val==1]
            
            
            gdf_terr = gdf_poly_terr.explode(index_parts=True)
            
            # extract polygon within which point is located
            terr_use = [pol.geometry for row, pol in gdf_terr.iterrows() if test_p.within(pol.geometry)][0]
            gdf_terr_use = gpd.GeoDataFrame({"geometry":[terr_use]})
            
            ## find nearest points on edges of poly using shapely.ops.nearest_points
            gdf_testp["nearest_polypoint"]= gdf_testp.geometry.apply(
                lambda x: shapely.ops.nearest_points(g1=x, g2=gdf_terr_use.iloc[0].geometry.boundary)[1])
            
            nearest_p1 = gdf_testp.nearest_polypoint.geometry[0]
            
            ## Make linestring with point and nearest point, and obtain another intersect
            line = LineString([test_p, nearest_p1])
            
            # extend line from edge -> point -> another side
            direction = np.array(test_p.xy) - np.array(nearest_p1.xy)
            direction = np.array([n[0] for n in direction])
            direction = direction / np.linalg.norm(direction)
            new_end = np.array([test_p.xy[0][0], test_p.xy[1][0]]) + 5 * direction # extend rate: multiply 3
            new_p = Point(new_end)
            line_extended = LineString([test_p, new_p])
            
            # Obtain new intersection
            poly_line = gdf_terr_use.exterior.geometry[0] # exterior
            nearest_p2 = line_extended.intersection(poly_line)
            
            
            ### Compare elevation at nearest_p1 and nearest_p2
            ele_dic ={}

            for nearest in [nearest_p1, nearest_p2]:
                coords = (nearest.xy[0][0], nearest.xy[1][0]) #lon, latの順
                pixel_coords = src.index(*coords)
                elevation = arr[pixel_coords]
                ele_dic[nearest] = elevation
            
            # select higher elevation's point
            nearest_p = max(ele_dic, key=ele_dic.get)
            
            
            # make line again from point to nearest point
            line_fin = LineString([nearest_p, test_p]) #set starting point as nearest_p
            
            
            ### Shift point along line_fin (precisely, replace the point)
            shiftm = 3 * 0.3048 # m
            shift_p = line_fin.interpolate(shiftm)
            
            new_points.append(shift_p)
            
        except:
            new_points.append(test_p)
            
            # #### Plot for check
            # fig = plt.figure(figsize=(5, 5))
            # ax1 = fig.add_subplot(1,1,1)
            # ### poly
            # x,y = terr_use.exterior.xy
            # ax1.plot(x, y, color='grey', label='Polygon')
            # ### point
            # ax1.plot(test_p.xy[0][0], test_p.xy[1][0], "o", color="black")
            # ax1.plot(gdf_testp.nearest_polypoint.geometry[0].xy[0][0], gdf_testp.nearest_polypoint.geometry[0].xy[1][0], "o", color='orange')
            # ax1.plot(nearest_p1.xy[0][0], nearest_p1.xy[1][0], "o", color="red")
            # ax1.plot(nearest_p2.xy[0][0], nearest_p2.xy[1][0], "o", color='orange')
            # ax1.plot(nearest_p.xy[0][0], nearest_p.xy[1][0], "o", color="red")
            # ax1.plot(shift_p.xy[0][0], shift_p.xy[1][0], "o", color="red")
            # ### line
            # ax1.plot(line.xy[0], line.xy[1], color='green')
            # ax1.plot(line_extended.xy[0], line_extended.xy[1], color='green')
            
        
    # """#Export"""
    gdf = gpd.GeoDataFrame({"geometry":new_points})
    # Output shapefile path
    
    outfilename = os.path.basename(point_shp)[:-4]
    output_shapefile_path = os.path.join(out_dir,f"{outfilename}_shift.shp")
    # Export the GeoDataFrame to a shapefile
    gdf.to_file(output_shapefile_path, crs="EPSG:32648")
    
    end = time.time()
    diff_time = end -start
    m, s = divmod(diff_time, 60)
    print(m, "min", s, "sec" )


if __name__ =="__main__":
    main()
    
    
