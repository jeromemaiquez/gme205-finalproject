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
DATA_DIR = WORK_DIR / "own_data"
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
fp_output_flows = OUTPUT_DIR / "PH_SeaportFlows.csv"

from airport import Airport
from seaport import Seaport
from catchment import draw_isochrones, draw_hinterlands
from radiation import Radiation

# Test for Airport
# airport1_data = {
#     "name": "Ninoy Aquino International Airport",
#     "lon": 121.0165,
#     "lat": 14.5123,
#     "iata_code": "MNL",
#     "icao_code": "RPLL",
#     "airport_type": 1
# }

# airport2_data = {
#     "name": "Laguindingan Airport",
#     "lon": 124.4572,
#     "lat": 8.6125,
#     "iata_code": "CGY",
#     "icao_code": "RPMY",
#     "airport_type": 2
# }

# airport1 = Airport(**airport1_data)
# airport2 = Airport(**airport2_data)

# print("\nAirport 2 details:\n---", airport2, sep="\n")
# print(f"Distance between airports 1 and 2: {airport1.distance_to(airport2)} m")
# print(f"Route coordinates between airports 1 and 2: {airport1._route_coords(airport2)}")

# airport_route = airport1.route_linestring(airport2)
# print(f"Geometry of route between airports 1 and 2: {airport_route}")

# Test for Seaport

# Import existing VisGraph for sea routes & assign to Seaport class
# VisGraph was pre-made due to long build times (~35 minutes)
searoute_graph = vg.VisGraph()
searoute_graph.load(fp_graph)
Seaport.set_graph(searoute_graph)

# seaport1_data = {
#     "name": "Port of Manila",
#     "lon": 120.9500,
#     "lat": 14.5833,
#     "un_locode": "PHMNL",
#     "pmo": "NCR",
#     "seaport_type": 1
# }

# seaport2_data = {
#     "name": "Port of Cagayan de Oro",
#     "lon": 124.6623,
#     "lat": 8.4939,
#     "un_locode": "PHCDO",
#     "pmo": "MO/C",
#     "seaport_type": 1
# }

# seaport1 = Seaport(**seaport1_data)
# seaport2 = Seaport(**seaport2_data)

# print("\nSeaport 2 details:\n---", seaport2, sep="\n")
# print(f"Distance between seaports 1 and 2: {seaport1.distance_to(seaport2)} m")
# print(f"Route coordinates between seaports 1 and 2: {seaport1._route_coords(seaport2)}")

# seaport_route = seaport1.route_linestring(seaport2)
# print(f"Geometry of route between seaports 1 and 2: {seaport_route}")

load_dotenv()
ORS_API_KEY = os.getenv("ORS_API_KEY")
client = ors.Client(ORS_API_KEY)

# df_airports = pd.read_csv(fp_airports)
df_seaports = pd.read_csv(fp_seaports)

# airports = []
seaports = []

# for idx, row in df_airports.iterrows():
#     airport = Airport(
#         name=row["airport_name"],
#         lon=row["longitude"],
#         lat=row["latitude"],
#         iata_code=row["iata_code"],
#         icao_code=row["icao_code"],
#         airport_type=row["airport_class"],
#         outflow=row["n_passengers"]
#     )
#     airports.append(airport)

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

# print("Generating isochrones for list of Airport objects...")
# if not fp_isochrones.exists():
#     gdf_airport_catchments = draw_isochrones(client, airports, "iata_code")
#     gdf_airport_catchments.to_parquet(fp_isochrones)
# else:
#     print("Loading existing isochrone data...")
#     gdf_airport_catchments = gpd.read_parquet(fp_isochrones)

# print("Generating isochrones for list of Seaport objects...")
# if not fp_sea_isochrones.exists():
#     gdf_seaport_catchments = draw_isochrones(client, seaports, "un_locode")
#     gdf_seaport_catchments.to_parquet(fp_sea_isochrones)
# else:
#     print("Loading existing isochrone data...")
#     gdf_seaport_catchments = gpd.read_parquet(fp_sea_isochrones)

print("Generating hinterlands for list of Seaport objects...")
if not fp_sea_hinterlands.exists():
    gdf_seaport_catchments = draw_hinterlands(fp_cost, seaports, "un_locode")
    gdf_seaport_catchments.to_parquet(fp_sea_hinterlands)
else:
    print("Loading existing hinterland data...")
    gdf_seaport_catchments = gpd.read_parquet(fp_sea_hinterlands)

print("Done!")

# for seaport in seaports:
#     seaport_id = seaport.un_locode
#     attraction = gdf_seaport_catchments.loc[
#         gdf_seaport_catchments.hub_id == seaport_id, "total_pop"
#     ].values[0]
#     seaport.set_attraction(attraction)

# radiation_model = Radiation(seaports[:5])
# df_sea_flows = radiation_model.simulate(id_attribute="un_locode")
# df_sea_flows.to_csv(fp_output_flows)

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