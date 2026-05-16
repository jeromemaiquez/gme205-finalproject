import pyvisgraph as vg
import folium
import shapely
import geopandas as gpd
import pandas as pd
import openrouteservice as ors
from dotenv import load_dotenv

import sys
import os
import json
from pathlib import Path

WORK_DIR = Path().resolve()
DATA_DIR = WORK_DIR / "data"
OUTPUT_DIR = WORK_DIR / "output"

dir_models = WORK_DIR / "models"
sys.path.append(os.path.abspath(dir_models))

fp_airports = DATA_DIR / "GmE205_AirportData.csv"
fp_seaports = DATA_DIR / "GmE205_SeaportData.csv"
fp_graph = DATA_DIR / "PH_SeaRouteGraph.pk1"
fp_cost = DATA_DIR / "202001_PH_Motorized-Land_Friction_Surface_2019.tif"

fp_isochrones = OUTPUT_DIR / "PH_AirportIsochrones.geoparquet"
fp_sea_isochrones = OUTPUT_DIR / "PH_SeaportIsochrones.geoparquet"
fp_sea_hinterlands = OUTPUT_DIR / "PH_SeaportHinterlands.geoparquet"

fp_output_map = OUTPUT_DIR / "test_output.html"
fp_output_flows_air = OUTPUT_DIR / "PH_AirportFlows.csv"
fp_output_flows_sea = OUTPUT_DIR / "PH_SeaportFlows.csv"

from models.hub import Hub
from models.airport import Airport
from models.seaport import Seaport
from models.catchment import draw_isochrones, draw_hinterlands
from models.air_network import AirNetwork
from models.sea_network import SeaNetwork
from models.radiation import Radiation

# Import existing VisGraph for sea routes & assign to Seaport class
# VisGraph was pre-made due to long build times (~35 minutes)
searoute_graph = vg.VisGraph()
searoute_graph.load(fp_graph)
# SeaNetwork.set_graph(searoute_graph)

# Prepare OpenRouteService API client (for isochrone generation)
load_dotenv()
ORS_API_KEY = os.getenv("ORS_API_KEY")
client = ors.Client(ORS_API_KEY)

# Read in data for airports and seaports
df_airports = pd.read_csv(fp_airports)
df_seaports = pd.read_csv(fp_seaports)

airports = []
seaports = []

# Airport instantiation

for idx, row in df_airports.iterrows():
    airport = Airport(
        name=row["airport_name"],
        lon=row["longitude"],
        lat=row["latitude"],
        iata_code=row["iata_code"],
        icao_code=row["icao_code"],
        airport_type=row["airport_class"],
        outflow=row["n_passengers"]
    )
    airports.append(airport)

# Attraction calculation for airports

print("Generating isochrones for list of Airport objects...")
if not fp_isochrones.exists():
    gdf_airport_catchments = draw_isochrones(client, airports, "iata_code")
    gdf_airport_catchments.to_parquet(fp_isochrones)
else:
    print("Loading existing isochrone data...")
    gdf_airport_catchments = gpd.read_parquet(fp_isochrones)

for airport in airports:
    airport_id = airport.iata_code
    attraction = gdf_airport_catchments.loc[
        gdf_airport_catchments.hub_id == airport_id, "total_pop"
    ].values[0]
    airport.set_attraction(attraction)
 
# AirNetwork instantiation and testing

air_network = AirNetwork(airports)

print(
    f"Distance between {airports[0].iata_code} and {airports[1].iata_code}",
    air_network.distance_between(airports[0], airports[1])
)

air_network.build_graph()
air_network.compute_graph_distances()

print(list(air_network.graph.nodes)[:5])
print(list(air_network.graph.edges)[:5])

air_dest_dist = air_network.compute_single_source_distances(airports[0])
print(f"First 5 distances to {airports[0].iata_code}")
print({k: air_dest_dist[k] for k in list(air_dest_dist)[:5]})

# Seaport instantiation

for idx, row in df_seaports.iterrows():
    seaport = Seaport(
        name=row["seaport_name"],
        lon=row["longitude"],
        lat=row["latitude"],
        un_locode=row["un_locode"],
        pmo=row["pmo"],
        seaport_type=row["seaport_type"],
        outflow=row["n_passengers"]
    )
    seaports.append(seaport)

# Attraction calculation for seaports
print("Generating isochrones for list of Seaport objects...")
if not fp_sea_isochrones.exists():
    gdf_seaport_catchments = draw_isochrones(client, seaports, "un_locode")
    gdf_seaport_catchments.to_parquet(fp_sea_isochrones)
else:
    print("Loading existing isochrone data...")
    gdf_seaport_catchments = gpd.read_parquet(fp_sea_isochrones)

for seaport in seaports:
    seaport_id = seaport.un_locode
    attraction = gdf_seaport_catchments.loc[
        gdf_seaport_catchments.hub_id == seaport_id, "total_pop"
    ].values[0]
    seaport.set_attraction(attraction)

# SeaNetwork instantiation and testing

sea_network = SeaNetwork(seaports, searoute_graph)

print(
    f"Distance between {seaports[0].un_locode} and {seaports[1].un_locode}",
    sea_network.distance_between(seaports[0], seaports[1])
)

sea_network.build_graph()
sea_network.compute_graph_distances()

print(list(sea_network.graph.nodes)[:5])
print(list(sea_network.graph.edges)[:5])
print([n for n in sea_network.graph.nodes if n.startswith("PH")][:10])

sea_dest_dist = sea_network.compute_single_source_distances(seaports[0])
print(f"First 5 distances to {seaports[0].un_locode}")
print({k: sea_dest_dist[k] for k in list(sea_dest_dist)[:5]})

print("Done!")

# print("Generating hinterlands for list of Seaport objects...")
# if not fp_sea_hinterlands.exists():
#     gdf_seaport_catchments = draw_hinterlands(fp_cost, seaports, "un_locode")
#     gdf_seaport_catchments.to_parquet(fp_sea_hinterlands)
# else:
#     print("Loading existing hinterland data...")
#     gdf_seaport_catchments = gpd.read_parquet(fp_sea_hinterlands)

air_radiation = Radiation(air_network, name="Airport Radiation")
df_air_flows = air_radiation.simulate(id_attribute="iata_code")
df_air_flows.to_csv(fp_output_flows_air)

sea_radiation = Radiation(sea_network, name="Seaport Radiation")
df_sea_flows = sea_radiation.simulate(id_attribute="un_locode")
df_sea_flows.to_csv(fp_output_flows_sea)

# print(airports[:2])

# Create map for visualization (to be moved later in a separate script)
# m = folium.Map(location=(14.6042, 120.9822), zoom_start=6)

# # Adding airport locations and route to map
# folium.GeoJson(
#     shapely.to_geojson(airport_route), 
#     style_function=lambda feature: {"color": "red"}
# ).add_to(m)
# folium.Marker(airport1.coords, icon=folium.Icon("red")).add_to(m)
# folium.Marker(airport2.coords, icon=folium.Icon("red")).add_to(m)

# # Adding seaport locations and route to map
# folium.GeoJson(
#     shapely.to_geojson(seaport_route), 
#     style_function=lambda feature: {"color": "blue"}
# ).add_to(m)
# folium.Marker(seaport1.coords, icon=folium.Icon("blue")).add_to(m)
# folium.Marker(seaport2.coords, icon=folium.Icon("blue")).add_to(m)

# folium.GeoJson(
#     gdf_seaport_catchments.to_json(),
#     style_function=lambda feature: {"color": "grey"}
# ).add_to(m)

# m.save(fp_output_map)