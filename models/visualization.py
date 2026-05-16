from models.network import Network
from models.air_network import AirNetwork
from models.sea_network import SeaNetwork
from models.hub import Hub
import folium
import matplotlib.pyplot as plt
from pyproj import Geod
from shapely import to_geojson, LineString
import geopandas as gpd
import pyvisgraph as vg
import contextily as cx
from rasterio.crs import CRS
from pathlib import Path

def route_coords(hub1: Hub, hub2: Hub):
    """
    Generates a list of (lon, lat) tuples representing the points
    along the shortest Haversine route between two hubs.
    """
    geod = Geod(ellps="WGS84")
    lonlats = geod.npts(
          hub1.lon, hub1.lat,
          hub2.lon, hub2.lat,
          npts=10
    )
    return [(hub1.lon, hub1.lat)] + lonlats + [(hub2.lon, hub2.lat)]

def flows_to_linestring(df_flows: gpd.GeoDataFrame, network: Network):
    """
    Converts a pd.DataFrame of origin-destination flows into a gpd.GeoDataFrame,
    with the route linestrings as the geometries.
    """
    if isinstance(network, AirNetwork):
            id_attribute = "iata_code"
    elif isinstance(network, SeaNetwork):
            id_attribute = "un_locode"

    df_flows["orig_hub"] = df_flows["origin"].apply(
        lambda x: [n for n in network.hubs if getattr(n, id_attribute) == x][0]
    )

    df_flows["dest_hub"] = df_flows["destination"].apply(
        lambda x: [n for n in network.hubs if getattr(n, id_attribute) == x][0]
    )

    df_flows["geometry"] = df_flows.apply(
        lambda row: LineString(
            route_coords(row["orig_hub"], row["dest_hub"])
        ), axis=1
    )

    gdf_flows = gpd.GeoDataFrame(
        data=df_flows[["origin", "destination", "flow"]],
        geometry=df_flows["geometry"],
        crs="EPSG:4326"
    )

    return gdf_flows

def nodes_to_points(network: Network):
    """
    Converts a pd.DataFrame of origin-destination flows into a gpd.GeoDataFrame,
    with the route linestrings as the geometries.
    """
    if isinstance(network, AirNetwork):
            id_attribute = "iata_code"
    elif isinstance(network, SeaNetwork):
            id_attribute = "un_locode"
    
    all_nodes = [getattr(h, id_attribute) for h in network.hubs]
    all_lons = [h.lon for h in network.hubs]
    all_lats = [h.lat for h in network.hubs]

    gdf_nodes = gpd.GeoDataFrame(
          data=all_nodes,
          geometry=gpd.points_from_xy(all_lons, all_lats, crs="EPSG:4326"),
          crs="EPSG:4326"
    )

    gdf_nodes.columns = ["node_id", "geometry"]

    return gdf_nodes

def plot_visgraph(vis_graph: vg.VisGraph, fp_out: str | Path):
    """Plots the edges of a VisGraph for debugging."""
    fig, ax = plt.subplots()
    for edge in vis_graph.visgraph.get_edges():
        ax.plot(
            [edge.p1.x, edge.p2.x],
            [edge.p1.y, edge.p2.y],
            color="blue", alpha=0.5
        )
    cx.add_basemap(ax, crs=CRS.from_epsg(4326))

    plt.savefig(fp_out, dpi=300)


