from hub import Hub

import openrouteservice as ors
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
import rasterio as rio
from rasterio import features
import numpy as np
from skimage.graph import MCP_Geometric

import time

def draw_isochrones(
        client: ors.Client, 
        hubs: list[Hub], 
        hub_id: str,
        travel_range: int = 3_600,
        get_pop: bool = True,
) -> gpd.GeoDataFrame:
    """
    Returns a geopandas.GeoDataFrame of isochrone polygons
    for a list of Hub objcts via the OpenRouteService API

    Attributes:
    - client: ors.Client
        Client object supplied with the API key
    - hubs: list[Hub]
        List of Hub objects for which to create isochrones
    - travel_range: int
        Ranges to calculate travel duration for (in seconds)
    - get_pop: bool
        If True, calculates total population inside isochrone.
        Population data from GHSL by the EU JRC
    """
    all_isochrones = []

    for i in tqdm(range(0, len(hubs), 5)):
        try:
            chunk_hubs = hubs[i:i+5]
        except IndexError:  # If len(chunk_hubs) < 5
            chunk_hubs = hubs[i:]
        
        locations = [hub.coords[::-1] for hub in chunk_hubs]
        
        attributes = None
        if get_pop:
            attributes = ["total_pop"]

        chunk_isochrones = ors.isochrones.isochrones(
            client=client,
            locations=locations,
            range=[travel_range],
            attributes=attributes
        )

        gdf_chunk = gpd.GeoDataFrame.from_features(chunk_isochrones)

        all_isochrones.append(gdf_chunk)

        time.sleep(5)
        # break

    # print(chunk_isochrones)
    
    df_isochrones = pd.concat(all_isochrones, ignore_index=True)
    gdf_isochrones = gpd.GeoDataFrame(data=df_isochrones, geometry=df_isochrones.geometry, crs="EPSG:4326")
    gdf_isochrones["hub_id"] = gdf_isochrones.index.to_series().apply(
       lambda idx: getattr(hubs[idx], hub_id)
    )

    return gdf_isochrones

def draw_hinterlands(
        cost_raster: str,
        hubs: list[Hub],
        id_attribute: str,
        capacity_attribute: str = "outflow",
        beta: float = 2.0
):
    """
    Returns a geopandas.GeoDataFrame of hinterland polygons for a list 
    of Hub objects via the multiplicatively weighted Voronoi diagram (MWVD) method.

    Attributes:
    - cost_raster: str
        the filepath of the raster representing travel costs
    - hubs: list[Hub]
        the list of Hub objects for which to draw hinterlands
    - capacity_attribute: str
        the name of the Hub attribute representing its capacity. Default is "outflow"\
    - beta: float
        the value of the friction coefficient. Default is 1.0
    """

    hubs_coords = []
    hubs_capacities = []

    with rio.open(cost_raster) as src:
        cost_grid = src.read(1) * 1_000 # convert values from min/m to min/km (i.e., min/pixel)
        profile = src.profile
        transform = src.transform

        for hub in hubs:
            # print(hub.un_locode)
            lat, lon = hub.coords
            capacity = getattr(hub, capacity_attribute)
            row, col = src.index(lon, lat)
            hubs_coords.append((row, col))
            hubs_capacities.append(capacity)
    
    # min_weighted_cost = np.full(cost_grid.shape, np.inf)
    service_area_map = np.full(cost_grid.shape, -1, dtype=np.int32)

    mcp = MCP_Geometric(cost_grid)

    for i, (coord, capacity) in enumerate(zip(hubs_coords, hubs_capacities)):
        # 1. Compute least-cost distance from this Hub to all cells
        # find_costs returns cumulative cost distance 'd'
        d, _ = mcp.find_costs(starts=[coord])

        # # Manual cap on travel time
        # d_cap = np.where(d < 15, d, np.inf)

        # 2. Apply Huff-like weighting: Cost = (d^beta) / Capacity
        min_weighted_cost = np.power(np.full(cost_grid.shape, 60), beta) / np.log(capacity / 60)
        weighted_d = (np.power(d, beta)) / np.log(capacity / (d+1))
        weighted_d = np.where(d < 60, weighted_d, np.inf)

        # 3. Update the map where this Hub is the 'cheapest' option
        mask = weighted_d < min_weighted_cost
        min_weighted_cost[mask] = weighted_d[mask]
        service_area_map[mask] = i
    
    excluded_areas = service_area_map != -1

    results = (
        {"properties": {"raster_val": v}, "geometry": s}
        for i, (s, v) in enumerate(
            features.shapes(service_area_map, mask=excluded_areas, transform=transform)
        )
    )

    gdf_hinterlands = gpd.GeoDataFrame.from_features(list(results), crs="EPSG:4326")
    gdf_hinterlands["hub_id"] = gdf_hinterlands.raster_val.apply(
        lambda idx: getattr(hubs[int(idx)], id_attribute)
    )

    gdf_hinterlands = gdf_hinterlands.dissolve(by="hub_id")

    return gdf_hinterlands

