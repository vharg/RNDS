import geopandas as gpd
import pandas as pd
import numpy as np


def prepare_roads(roads):
    """
    Preparing roads for use in the analysis. OSM contains a lot of unnecessary information, which we remove.
    We also add a unique "Road_ID" field that is used later in the analysis for attribute joins.

    Parameters
    ----------
    roads : GeoDataFrame of the roads under consideration that has been downloaded from OpenStreetMap.

    Returns
    ----------
    GeoDataFrame of OSM roads file with the necessary modifications for analysis

    """
    print("Preparing roads file")
    roads = roads[['fid', 'osm_id', 'name', 'highway', 'geometry']]
    roads['Road_ID'] = np.arange(len(roads))

    return(roads)

def Assign_road_hierarchy(roads):
    """
    Fucntion assigns the hierarchy scores based on the criteria outlined in Hayes et al.

    Parameters
    ----------
    roads : GeoDataFrame output from the prepare_roads function.

    Returns
    ----------
    GeoDataFrame of the OSM roads file with assigned road hierarchy score.

    """
    print("Assigning road hierarchy scores to road network")
    roads.loc[roads['highway'] == 'motorway', 'hierarchy'] = 4
    roads.loc[roads['highway'] == 'motorway_link', 'hierarchy'] = 4
    roads.loc[roads['highway'] == 'trunk', 'hierarchy'] = 3
    roads.loc[roads['highway'] == 'trunk_link', 'hierarchy'] = 3
    roads.loc[roads['highway'] == 'primary', 'hierarchy'] = 3
    roads.loc[roads['highway'] == 'primary_link', 'hierarchy'] = 3
    roads.loc[roads['highway'] == 'secondary', 'hierarchy'] = 2
    roads.loc[roads['highway'] == 'secondary_link', 'hierarchy'] = 2
    roads.loc[roads['highway'] == 'tertiary', 'hierarchy'] = 2
    roads.loc[roads['highway'] == 'tertiary_link', 'hierarchy'] = 2
    roads.loc[roads['highway'] == 'unclassified', 'hierarchy'] = 1
    roads.loc[roads['highway'] == 'residential', 'hierarchy'] = 1
    roads.loc[roads['highway'] == 'living_street', 'hierarchy'] = 1
    roads.loc[roads['highway'] == 'service', 'hierarchy'] = 1
    roads.loc[roads['highway'] == 'road', 'hierarchy'] = 1
    roads.loc[roads['highway'] == 'unknown', 'hierarchy'] = 1
    roads.loc[roads['highway'] == 'pedestrian', 'hierarchy'] = 0
    print("Assigning road hierarchy scores to road network is complete")

    return(roads)

def Assign_strategic_nodes(roads, Strategic_nodes):
    """
    This function moves strategic nodes to their nearest road segment and then assigns a score to the road segment.
    The score is assigned based upon the criteria outlines in Hayes et al.

    Parameters
    ----------
    roads : GeoDataFrame output from the Assign_road_hierarchy function
    Strategic_nodes : GeoDataframe of the location and typology of each strategic node.

    Returns
    ----------
    GeoDataFrame that includes the strategic node score for each road segment (Node score)

    """
    print("Reprojecting road network and strategic nodes to pseudo mercator")
    roads = roads.to_crs(epsg=3857)
    Strategic_nodes = Strategic_nodes.to_crs(epsg=3857)

    # Use spatial index to search for nearest lines
    print("Setting spatial index")
    roads.sindex
    offset = 500
    bbox = Strategic_nodes.bounds + [-offset, -offset, offset, offset]
    hits = bbox.apply(lambda row: list(roads.sindex.intersection(row)), axis=1)

    tmp = pd.DataFrame({
        # index of points table
        "pt_idx": np.repeat(hits.index, hits.apply(len)),  # ordinal position of line - access via iloc later
        "line_i": np.concatenate(hits.values)
    })

    tmp = tmp.join(roads.reset_index(drop=True), on="line_i")

    tmp = tmp.join(Strategic_nodes.geometry.rename("point"), on="pt_idx")

    tmp = gpd.GeoDataFrame(tmp, geometry="geometry", crs=Strategic_nodes.crs)

    print("Finding closest road to each strategic node")
    # Find closest line to each point
    tmp["snap_dist"] = tmp.geometry.distance(gpd.GeoSeries(tmp.point))
    tmp = tmp.loc[tmp.snap_dist <= offset]
    tmp = tmp.sort_values(by=["snap_dist"])

    print("Snapping nodes to nearest road")
    closest = tmp.groupby("pt_idx").first()
    closest = gpd.GeoDataFrame(closest, geometry="geometry")
    pos = closest.geometry.project(gpd.GeoSeries(closest.point))
    new_pts = closest.geometry.interpolate(pos)

    snapped = gpd.GeoDataFrame(closest, geometry=new_pts)
    updated_points = Strategic_nodes.drop(columns=["geometry"]).join(snapped)
    updated_points = updated_points.dropna(subset=["geometry"])

    join = roads.merge(updated_points, on='Road_ID', how='left')

    print("Counting number of snapped nodes touching each road")
    Number_nodes = join.groupby('Road_ID').count()

    roads_SN = roads.merge(Number_nodes['point'], on='Road_ID', how='left')

    print("Assigning strategic node score")
    roads_SN.loc[roads_SN['point'] == 0, 'Node score'] = 0
    roads_SN.loc[roads_SN['point'] == 1, 'Node score'] = 4
    roads_SN.loc[roads_SN['point'] == 2, 'Node score'] = 8
    roads_SN.loc[roads_SN['point'] == 3, 'Node score'] = 12
    roads_SN.loc[roads_SN['point'] > 3, 'Node score'] = 16

    print("Strategic node score successfully applied")

    return(roads_SN)

def Assign_community_facilities(POIs, roads, roads_SN):
    """
    This function assigns am access to community facilities score by moving each POI to the nearest road segment.
    Scores assigned to segments based on the criteria outlines in Hayes et al.

    Parameters
    ----------
    roads : GeoDataFrame that is the output of the Assign_road_hierarchy function
    roads_SN : GeoDataFrame that is the output of the Assign_strategic_nodes function
    POIs : GeoDataFrame that has the location and typology of different ammenities.

    Returns
    ----------
    GeoDataFrame that contains an access to commmunity facilities score (Priority)
    """
    print("Assigning access to community services and facilities score")
    # Set the priority score for POI
    print("Setting priority scores for each point of interest")

    POIs.loc[(POIs['amenity'] == 'police') |
             (POIs['amenity'] == 'hospital') |
             (POIs['amenity'] == 'rescue_station') |
             (POIs['amenity'] == "fire_station"),
             'Priority'] = 4
    POIs.loc[(POIs['amenity'] == 'supermarket') |
             (POIs['amenity'] == 'prison') |
             (POIs['amenity'] == 'waste_transfer_station') |
             (POIs['amenity'] == 'lighthouse') |
             (POIs['amenity'] == 'social_facility') |
             (POIs['amenity'] == "bank") |
             (POIs['amenity'] == 'shelter') |
             (POIs['amenity'] == 'pharmacy') |
             (POIs['amenity'] == 'water_well') |
             (POIs['amenity'] == 'dentist') |
             (POIs['amenity'] == 'doctors') |
             (POIs['amenity'] == 'embassy') |
             (POIs['amenity'] == 'town_hall') |
             (POIs['amenity'] == 'public_building') |
             (POIs['amenity'] == 'water_tower') |
             (POIs['amenity'] == 'nursing_home') |
             (POIs['amenity'] == 'courthouse') |
             (POIs['amenity'] == 'fuel') |
             (POIs['amenity'] == 'consulate') |
             (POIs['amenity'] == 'chemist') |
             (POIs['amenity'] == 'veterinary'),
             'Priority'] = 3
    POIs.loc[(POIs['amenity'] == 'kindergarten') |
             (POIs['amenity'] == 'school') |
             (POIs['amenity'] == 'library') |
             (POIs['amenity'] == 'college') |
             (POIs['amenity'] == "university"),
             'Priority'] = 2
    POIs['Priority'].fillna(0.1, inplace=True)

    # --- Snap all POI to nearest road, but with a maximum tolerance of 50 m ---
    # Convert data to pseudo mercator
    print("Reprojecting POI to pseudo mercator")
    POI = POIs.to_crs(epsg=3857)

    # Use spatial index to search for nearest lines
    print("Setting spatial index")
    offset_POI = 25
    bbox_POI = POI.bounds + [-offset_POI, -offset_POI, offset_POI, offset_POI]
    hits_POI = bbox_POI.apply(lambda row: list(roads.sindex.intersection(row)), axis=1)

    tmp_POI = pd.DataFrame({
        # index of points table
        "pt_idx": np.repeat(hits_POI.index, hits_POI.apply(len)),  # ordinal position of line - access via iloc later
        "line_i": np.concatenate(hits_POI.values)
    })

    tmp_POI = tmp_POI.join(roads.reset_index(drop=True), on="line_i")
    tmp_POI = tmp_POI.join(POI.geometry.rename("point"), on="pt_idx")
    tmp_POI = gpd.GeoDataFrame(tmp_POI, geometry="geometry", crs=POI.crs)

    print("Finding closest road to each POI")
    # Find closest line to each point
    tmp_POI["snap_dist"] = tmp_POI.geometry.distance(gpd.GeoSeries(tmp_POI.point))
    tmp_POI = tmp_POI.loc[tmp_POI.snap_dist <= offset_POI]
    tmp_POI = tmp_POI.sort_values(by=["snap_dist"])

    print("Snapping nodes to nearest road")
    closest_POI = tmp_POI.groupby("pt_idx").first()
    closest_POI = gpd.GeoDataFrame(closest_POI, geometry="geometry")
    pos_POI = closest_POI.geometry.project(gpd.GeoSeries(closest_POI.point))
    new_pts_POI = closest_POI.geometry.interpolate(pos_POI)

    snapped_POI = gpd.GeoDataFrame(closest_POI, geometry=new_pts_POI)
    updated_points_POI = POI.drop(columns=["geometry"]).join(snapped_POI, lsuffix='_x', rsuffix='')
    updated_points_POI = updated_points_POI.dropna(subset=["geometry"])

    roads_SN['Road_ID'] = roads_SN['Road_ID'].astype(object)
    updated_points_POI['Road_ID'] = updated_points_POI['Road_ID'].astype(object)

    join_3 = roads_SN.merge(updated_points_POI, on='Road_ID', how='left')

    print("Summing priority scores for each road")
    Sum_POI = join_3.groupby(['Road_ID'])['Priority'].sum().reset_index()

    print("merging roads with summed POI")
    roads_SN_POI = roads_SN.merge(Sum_POI, on='Road_ID', how='left')

    return(roads_SN_POI)

def Assign_criticality(roads_SN_POI):
    """
    This function calculates the criticality score for the road network.
    Criticality is assigned based on the criteria outlined in Hayes et al.

    Parameters
    ----------
    roads_SN_POI : GeoDataFrame that is the output of the Assign_community_faciities function

    Returns
    ----------
    GeoDataFrame that contains the criticality score obtained for the road network (Criticality score)
    """
    print("Merging road networks")
    roads_criticality = roads_SN_POI

    print("Calculating criticality")
    roads_criticality['Criticality'] = (roads_criticality['Node score'] * 0.33) + \
                                       (roads_criticality['Priority'] * 0.33) + \
                                       (roads_criticality['hierarchy'] * 0.33)
    # Percentile_25 = roads_criticality.Criticality.quantile(0.25)
    Percentile_50 = roads_SN_POI.Criticality.quantile(0.50)
    Percentile_90 = roads_criticality.Criticality.quantile(0.90)
    Percentile_99 = roads_criticality.Criticality.quantile(0.99)

    print("Assigning criticality score")
    roads_criticality.loc[roads_criticality['Criticality'] <= Percentile_50, 'Criticality score'] = 1
    roads_criticality.loc[roads_criticality['Criticality'] > Percentile_50, 'Criticality score'] = 10
    roads_criticality.loc[roads_criticality['Criticality'] > Percentile_90, 'Criticality score'] = 100
    roads_criticality.loc[roads_criticality['Criticality'] > Percentile_99, 'Criticality score'] = 1000

    return(roads_criticality)

def Get_LoR_Score (roads_criticality):
    """
    This function assigns a length of road score to each road segment within the road network
    Length of road score assigned based on criteria outlined in Hayes et al.

    Parameters
    ----------
    roads_criticality : GeoDataFrame that is the output of the Assign_criticality function

    Returns
    ----------
    GeoDataFrame that contains a length of road score (LoR score)

    """
    print("reprojecting roads layer")
    roads_criticality = roads_criticality.to_crs(epsg=3857)
    print("Calculating segment lengths")
    roads_criticality['length'] = roads_criticality["geometry"].length
    print("Obtaining quantiles")
    Percentile_25 = roads_criticality['length'].quantile(0.25)
    Percentile_50 = roads_criticality['length'].quantile(0.50)
    Percentile_75 = roads_criticality['length'].quantile(0.75)
    print("Assigning length of road score")
    roads_criticality.loc[roads_criticality['length'] <= Percentile_25, 'LoR score'] = 0.01
    roads_criticality.loc[roads_criticality['length'] > Percentile_25, 'LoR score'] = 0.1
    roads_criticality.loc[roads_criticality['length'] > Percentile_50, 'LoR score'] = 1
    roads_criticality.loc[roads_criticality['length'] > Percentile_75, 'LoR score'] = 10

    return(roads_criticality)


