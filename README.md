![Image](https://github.com/user-attachments/assets/5a26b2d7-1ec3-494b-9901-0ad97415c001)

# Replanting Blueprint
This program was developed on Windows.
You need to change path to associated files in the codes depending on your work directories.
This progarm utilizes arcpy in creating slope, curvature and vectorizing line images. These steps will replace arcpy with open source libraries in the future.  
Reference of this progrma is from the following with some modification:  
Chihiro Naito, and Wataru Takeuchi, 2024. Development of automated UAV LiDAR based blueprint in oil palm replanting on terraces. Earth Environ. Sci. 1412 012018, https://doi.org/10.1088/1755-1315/1412/1/012018.

## Data used
The following data is needed for creating planting points.
- DEM
- Road line shapefile
- Extend area polyggon shapefile divided by road
- Extent area polygon shapefile
- ArcGIS Pro gdb file (.gdb)

## Creation of CS image (_01_CreateCSimage)
Open "run_CSimg.py" and set pathes as required.

- _01_Gaussian.py
  * No need edit. DEM is smoothened by Gausian filter for generating a curvature image.
- _02_Slope_Curvature.py
  * Set the path to original DEM and Gaussian filtered DEM. 
- _03_CSMap_export.py
  * No need edit. CS map is exported.


## Terrace detection by deep learning and error removal of detected terraces lines (_02_TerraceDetection)
After terraces are segmented, open "run_terrace_detection.py" and set pathes as required.

- _00_dilation_swin.py
  * No need edit. Segmented image is smoothened by morphological processing.
- _00_skelton.py
  * No need edit. Smoothened image is skeltonized.
- _01_vectorize_centerlines.py
  * Set the path to arcpy and to "_01_vectorize_centerlines_arctool.py" in this code.
- _02_filtering_by_intersects.py
  * No need edit, but you can change the angle threshold "angle_thre" (default 45).
- _03_cut_intersects.py
  * No need edit, but you can change the cut distance "buff_distance" (default 8).
- _04_cut_intersects_2lines.py
  * No need edit, but you can change the cut distance "buff_distance" (default 8) and the angle threshold "angle_thre" (default 45).
- _05_connect_nearlines.py
  * No need edit, but you can change the distance threshold "linestring.length" (default 5) and the angle threshold "angle_thre" (default 45).
- _06_erase_by_roads.py
  * No need edit.
- _07_cut_intersects_pairing.py
  * No need edit, but you can change the cut distance "buff_distance" (default 1).
- _08_cut_intersects_2lines_pairing.py
  * No need edit, but you can change the cut distance "buff_distance" (default 1) and the angle threshold "angle_thre" (default 45).
- _99_devide_line_roads.py
  * No need edit. Terrace lines are divided by road.


## Pairing terraces for point generation (_03_PairingTerraces)
Open "run_pairing_terrace.py" and set pathes as required.

- _03_vertical_cut.py
  * No need edit. This code cuts lines at the endpoints of neighboring lines.
- _03_vertical_cut_post.py
  * No need edit. This code finds lines unprocessed in the previous step and cut them.
- _04_paringID.py
  * No need edit. This code assigns T1 and T2, and the identical pair numbers for paired terraces using DEM information.
- _05_paringID_post.py
  * No need edit. This code assgins the same pairing ID for neighboring and connecting lines.
- _06_put_direction.py
  * No need edit. This code assigns the direction of the area toward which points will be generated


## Point generation (_04_Point_generation)
Open "run_point_generation.py" and set pathes as required.
- _01_generate_points_slope_adjust_6ft.py
  * No need edit.
  * This code generates points on T1 at a contant distance and on T2 at varying distance depending on the terrace interval.
  * This code adjusts palm intervals within 2 feet for the last two points to optimze the planting density.
  * This code avoids generating points within 6 feet from road edges.
- _02_mege_and_eliminate_points.py
  * No need edit, but you can change the distance threshold "close_thre".
  * This code merges all generated points and eliminates too close points within the threshold ("close_thre") each other.
