# Replanting Blueprint
This program was developed on Windows.
You need to change path to associated files in the codes depending on your work environment.
This progarm utilizes arcpy in creating slope, curvature and vectorizing line images. These steps will replace arcpy with open source libraries in the future.
Deep learning programs will be shared when it gets ready.

## Creation of CS image (_01_CreateCSimage)
Please run codes in "run_CSimg.py"

You need DEM for initiating the program
- _01_Gaussian.py
  * You need process DEM with Gausian filter for generating a curvature image.
- _02_Slope_Curvature.py
  * Use original DEM for slope image, and Gaussian filtered DEM for curvature image.
- _03_CSMap_export.py

## Terrace detection by deep learning (_02_TerraceDetection)
Deep learning programs will be shared when it gets ready.
After terraces were segmented, run "run_terrace_detection.py"

- _00_dilation.py
- _01_vectorize_centerlines.py
  * You need to set the path to arcpy and path to "_01_vectorize_centerlines_arctool.py" in the code.
- _02_filtering_by_intersects.py
  * You can change the angle threshold "angle_thre" (default 45).
- _03_cut_intersects.py
  * You can change the cut distance "buff_distance" (default 8).
- _04_cut_intersects_2lines.py
  * You can change the cut distance "buff_distance" (default 8).
  * You can change the angle threshold "angle_thre" (default 45).
- _05_connect_nearlines.py
  * You can change the distance threshold "linestring.length" (default 5).
  * You can change the angle threshold "angle_thre" (default 45).
- _06_erase_by_roads.py
- _07_cut_intersects_pairing.py
  * You can change the cut distance "buff_distance" (default 1).
- _08_cut_intersects_2lines_pairing.py
  * You can change the cut distance "buff_distance" (default 1).
  * You can change the angle threshold "angle_thre" (default 45).
- _99_devide_line_roads.py
- _99_devide_lines.py

## Pairing terraces for point generation (_03_PairingTerraces)
Please run codes in "run_pairing_terrace.py"

- _03_vertical_cut.py
  * This code cut lines at the endpoints of neighboring lines
_03_vertical_cut_post.py
  * This code does the same process as the previous step, especially for lines which have gone after the previous step.
- _04_paringID.py
  * This code assign T1 and T2, and then the identical pair numbers for paired terraces.
  * This process uses the elevation information.
- _05_paringID_post.py
  * Assgin the same pairing ID for neighboring and connecting lines
  * Lines which apart each other are not processed because they produce multilinestrings
- _06_put_direction.py
  * This code assign the direction of the area to all lines

## Point generation (_04_Point_generation)
Please run codes in "run_point_generation.py"
- _01_generate_points_slope_adjust_6ft.py
  * This code generates points on T1 at a contant distance and on T2 at varying distance depending on the terrace interval.
  * This code adjusts palm intervals within 2 feet for the last two points to optimze the planting density.
  * This code avoids generating points within 6 feet from road edges.
- _02_mege_and_eliminate_points.py
  * This code merges all generated points and eliminates too close points within 4 m each other.
