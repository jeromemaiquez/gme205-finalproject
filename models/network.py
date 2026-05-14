from models.hub import Hub
import networkx as nx
import numpy as np
from shapely import LineString
from pyproj import Geod
from typing import Iterable

class Network():
    """
    Base class for networks of transport hubs (airport and seaport),
    where routing/distance functionalities are assigned.
    
    Attributes:
    - hubs: list[Hub]
        List of hubs to include in the network
    - graph: networkx.Graph
        nx.Graph object linking the hubs (Default: None)
    """
    _geod = Geod(ellps="WGS84")

    def __init__(self, hubs: list[Hub], graph: nx.Graph | None = None):
        if any([isinstance(h, Hub) == False for h in hubs]):
            raise ValueError("`hubs` parameter must be list of `Hub` objects or its child classes.")
        
        self.hubs = hubs
        self.graph = graph
    
    def distance_between(self, hub1: Hub, hub2: Hub):
        """Returns the distance between two hubs."""
        # return Hub.haversine_m(hub1.lon, hub1.lat, hub2.lon, hub2.lat)
        raise NotImplementedError("Must be implemented by the child classes `AirNetwork` or `SeaNetwork`.")
    
    def build_graph(self):
        """Builds a networkx.Graph representing the network of hubs."""
        raise NotImplementedError("Must be implemented by the child classes `AirNetwork` or `SeaNetwork`.")

    def compute_graph_distances(self):
        """Assigns distances as weights to the edges of the graph."""
        raise NotImplementedError("Must be implemented by the child classes `AirNetwork` or `SeaNetwork`.")
    
    def _route_coords(self, hub1: Hub, hub2: Hub):
        raise NotImplementedError("Must be implemented by AirNetwork or SeaNetwork subclass")

    def route_linestring(self, hub1: Hub, hub2: Hub):
        """
        Generates a LineString geometry from the shortest path
        between two airports (great-circle arc).
        """
        all_points = self._route_coords(hub1, hub2)

        return LineString(all_points)

    @staticmethod
    def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        return Network._geod.line_length([lon1, lon2], [lat1, lat2])

    @staticmethod
    def compute_haversine_matrix(lons: Iterable[float], lats: Iterable[float]):
        """Compute a 2D distance matrix using the Haversine method."""
        R = 6371.0

        lats = np.radians(lats)
        lons = np.radians(lons)

        dlat = lats[:, np.newaxis] - lats
        dlon = lons[:, np.newaxis] - lons

        a = (
            np.sin(dlat / 2.0) ** 2 
            + np.cos(lats[:, np.newaxis]) 
            * np.cos(lats) * np.sin(dlon / 2.0) ** 2
        )

        c = 2.0 * np.arcsin(np.sqrt(a))

        return R * c