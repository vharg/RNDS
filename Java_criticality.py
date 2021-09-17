from RNDS_functions import prepare_roads
from RNDS_functions import Assign_road_hierarchy
from RNDS_functions import Assign_strategic_nodes
from RNDS_functions import Assign_community_facilities
from RNDS_functions import Assign_criticality
from RNDS_functions import Get_LoR_Score
import os
import geopandas as gpd

print("Assigning directories")
dir = os.path.dirname(__file__)
roads_dir = os.path.join(dir, 'Geospatial_data/roads')
POIs_dir = os.path.join(dir, 'Geospatial_data/POI')
Strategic_nodes_dir = os.path.join(dir, "Geospatial_data/Strategic_nodes")

print("Reading in the data")
roads = gpd.read_file(roads_dir + "/Java_roads.shp") # Note: Make sure this is consistent with your file name for roads
POIs = gpd.read_file(POIs_dir + "/filtered_POIs.gpkg") # Note: Make sure this is consistent with your file name for POIs
Strategic_nodes = gpd.read_file(Strategic_nodes_dir + "/Strategic_nodes.gpkg") # Note: Make sure this is consistent with your file name for strategic_nodes

# Preparing the roads file
roads = prepare_roads(roads)

# Assigning road hierarchy scores
roads = Assign_road_hierarchy(roads)

# Assigning strategic node scores (access to important facilities)
roads_SN = Assign_strategic_nodes(roads, Strategic_nodes)

# Assigning access to community facilities
roads_SN_POI = Assign_community_facilities(POIs, roads, roads_SN)

# Calculating the road criticality score
roads_criticality = Assign_criticality(roads_SN_POI)

# Calculating the length of road score for each segment
roads_criticality_LoR = Get_LoR_Score(roads_criticality=roads_criticality)

# Saving the road criticality file as a shapefile
print("Saving road criticality to shapefile")
roads_criticality_LoR.to_file("Java_roads_criticality.shp", driver="ESRI Shapefile") # change filename as desired


