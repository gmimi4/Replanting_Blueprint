import arcpy
import os

arcpy.env.overwriteOutput = True

polygon_path = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\3_dilation\mosaic_e5_d2_clip.shp"
out_dir = r"D:\Malaysia\01_Brueprint\09_Terrace_detection\4_centerlines"
gdb = r"C:\Users\chihiro\Desktop\PhD\Malaysia\Arc_Malaysia\Malaysia_Blueprint\Malaysia_Blueprint.gdb"
arcpy.env.workspace =gdb

filename = os.path.basename(polygon_path)[:-4]
# copy to gdb to secure arcpy processing
arcpy.CopyFeatures_management(polygon_path, gdb + os.sep + filename)

# obtain feature
fcs = arcpy.ListFeatureClasses("*")
fc = [f for f in fcs if filename in f][0]

# Select background subtype
# sql_query = "{} = {}".format(arcpy.AddFieldDelimiters(polygon_path, 'rasterval'), int(1))
inputLyr = arcpy.management.MakeFeatureLayer(fc, "inputLyr")
inputLyr_sel = arcpy.SelectLayerByAttribute_management("inputLyr", "SUBSET_SELECTION", "rval = 1")

# Execute Polygon To Centerline # It seems to work in gdb environment
outfile = gdb + os.sep + "centerlines"
arcpy.topographic.PolygonToCenterline(inputLyr_sel, outfile)

out_shpfile = out_dir + os.sep + "centerlines.shp"
arcpy.CopyFeatures_management(outfile, out_shpfile)