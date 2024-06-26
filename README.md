# Integrating road criticality into road disruption assessments
 This repository contains code to produce a criticality roads file for use in road disruption assessments for volcanic eruptions from [Hayes et al. (2022)](https://doi.org/10.1186/s13617-022-00118-x). 
 
## Libraries/packages
- Geopandas 0.8.2
- Pandas 1.2.2
- Numpy 1.20.1

## Steps to produce a road criticality file

### Data
The data used in this work can be obtained from fully open data sources. 

#### OpenStreetMap
We used OpenStreetMap data downloaded from [geofabrik](https://download.geofabrik.de/asia/indonesia.html). We then used [OSMOSIS](https://wiki.openstreetmap.org/wiki/Osmosis) to extract: 1) a roads file and, 2) a POI file (see paper for filtering method). We then clipped these files to the extent of the island of Java. The roads file is then placed within the "Geospatial\_data/roads" folder and the POI file was placed within the "Geospatial\_data/POI" folder. Note:  as these files are very large, they're not included in the repository. 

#### Strategic nodes
The file data file is a "strategic nodes" file. Multiple used was compiled from a variety of data sources:  
- [Airports](https://ourairports.com)  
- [Border crossings](https://data.humdata.org/dataset/global-border-crossing-points)  
- [Power plants](https://datasets.wri.org/dataset/globalpowerplantdatabase)  
- [Sea ports](https://data.humdata.org/dataset/world-port-index)  

These data were then compiled into a single, global strategic nodes shapefile. This file was then added to the "Geospatial\_data/Strategic\_nodes" folder.


### Process
- Create a folder called "Geospatial\_data". Within that folder create three additional folders called: "roads", "POI", and "Strategic\_nodes". Place each of your files (roads, filtered points of interest, and Strategic nodes) into each respective folder.
- The "Java\_criticality.py" script is then run (note: make sure the file names for roads, POI, and Strategic\_nodes are consistent between the script and those in the folders). 
- This script will use the functions contained within  "RNDS\_functions.py" to produce a road criticality file. Included within this file will be a criticality score and a length of road score. This file can then be used to assess road disruption as per the process outline in Hayes et al. (submitted). Please see the accompanying Jupyter Notebook for a worked through example of this approach. 
- Once the criticality file is produced, the user can then assess impact to the road network (we do not provide a script for this here). Multiplying the Criticality score, LoR score, and impact score will then yield a Road Segment Disruption Score (RSDS) for each road segment. Summing all RSDS for all road segments will yield an overall Road Network Disruption Score (RNDS) that can be used to compare the potential disruption between scenarios, hazards, and/or volcanoes. 
- The last step (assessing impact and calculating RSDS/RNDS) is left to the user to do, depending on their needs. For the work presented in Hayes et al. (submitted) we simply used QGIS to overlay the hazard data with the criticality file. However, if many scenarios are to be used, the user may wish to produce a function that loops through this process. 

