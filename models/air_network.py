from models.network import Network
from models.airport import Airport
from models.hub import Hub
import networkx as nx

class AirNetwork(Network):
    """
    `Network` child class to specifically represent networks of airports.
    Uses the Haversine method to calculate inter-airport distances.

    Attributes:
    - hubs: list[Airport]
        List of airports to include in the network
    - graph: networkx.Graph
        nx.Graph object linking the airports (Default: None)
    """
    def __init__(self, hubs: list[Airport], graph: nx.Graph | None = None):
        if any([isinstance(h, Airport) == False for h in hubs]):
            raise ValueError("`hubs` parameter must be list of `Hub` objects or its child classes.")
        
        super().__init__(hubs, graph)
    
    def distance_between(self, hub1: Hub, hub2: Hub):
        """Returns the distance between two airports."""
        return Network.haversine_m(hub1.lon, hub1.lat, hub2.lon, hub2.lat)
    
    def build_graph(self):
        """Builds a networkx.Graph representing the network of airports."""
        hub_ids = [h.iata_code for h in self.hubs]
        hub_lonlats = [(h.lon, h.lat) for h in self.hubs]

        # G = nx.complete_graph(hub_ids)
        G = nx.complete_graph(hub_lonlats)
        self.graph = G
        
    def compute_graph_distances(self):
        """Assigns distances as weights to the edges of the graph."""
        hub_ids = [h.iata_code for h in self.hubs]
        lats = [h.lat for h in self.hubs]
        lons = [h.lon for h in self.hubs]
        distances = {}

        distance_matrix = Network.compute_haversine_matrix(lons, lats)

        # for idx1, hub1_id in enumerate(hub_ids):
        #     for idx2, hub2_id in enumerate(hub_ids):
        #         if hub1_id != hub2_id:
        #             distances[(hub1_id, hub2_id)] = distance_matrix[idx1, idx2]
        
        for idx1, hub1_lonlat in enumerate(zip(lons, lats)):
            for idx2, hub2_lonlat in enumerate(zip(lons, lats)):
                if hub1_lonlat != hub2_lonlat:
                    distances[(hub1_lonlat, hub2_lonlat)] = distance_matrix[idx1, idx2]

        nx.set_edge_attributes(self.graph, distances, "distance_m")
    
    def _route_coords(self, hub1: Airport, hub2: Airport):
        """
        Generates a list of (lon, lat) tuples representing the points
        along the shortest route between two airports.
        """
        lonlats = Network._geod.npts(
            hub1.lon, hub1.lat, 
            hub2.lon, hub2.lat, 
            npts=10
        )

        return [(hub1.lon, hub1.lat)] + lonlats + [(hub2.lon, hub2.lat)]