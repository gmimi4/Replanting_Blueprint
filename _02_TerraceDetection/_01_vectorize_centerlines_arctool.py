import arcpy
import os, sys

arcpy.env.overwriteOutput = True

polygon_path = sys.argv[1]
out_dir = sys.argv[2]
gdb = sys.argv[3]
arcpy.env.workspace =gdb

filename = os.path.basename(polygon_path)[:-4]
# copy to gdb to secure arcpy processing
arcpy.CopyFeatures_management(polygon_path, gdb + os.sep + filename)

# obtain feature
fcs = arcpy.ListFeatureClasses("*")
fc = [f for f in fcs if filename in f][0]

# Select background subtype
inputLyr = arcpy.management.MakeFeatureLayer(fc, "inputLyr")
inputLyr_sel = arcpy.SelectLayerByAttribute_management("inputLyr", "SUBSET_SELECTION", "rval=1") #rval=1 edges or #1 background"

# Execute Polygon To Centerline # It seems to work in gdb environment
outfile = gdb + os.sep + "centerlines"
arcpy.topographic.PolygonToCenterline(inputLyr_sel, outfile)

out_shpfile = out_dir + os.sep + "centerlines_back.shp"
arcpy.CopyFeatures_management(outfile, out_shpfile)