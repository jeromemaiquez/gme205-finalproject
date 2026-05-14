from models.network import Network
from models.seaport import Seaport
from models.hub import Hub
import networkx as nx
import pyvisgraph as vg

class SeaNetwork(Network):
    """
    `Network` child class to specifically represent networks of seaports.
    Uses a visibility graph to calculate inter-port routes and the Haversine method for distances.
    
    Attributes:
    - hubs: list[Seaport]
        List of seaports to include in the network.
    - vis_graph: pyvisgraph.VisGraph
        vg.VisGraph linking the seaports and coastal vertices.
        This will be converted into an nx.Graph.
    """
    def __init__(
            self, 
            hubs: list[Seaport], 
            vis_graph: vg.VisGraph
    ):
        if any([isinstance(h, Seaport) == False for h in hubs]):
            raise ValueError("`hubs` parameter must be list of `Hub` objects or its child classes.")
        self.vis_graph = vis_graph
        self.build_graph()

        super().__init__(hubs, self.graph)

    def distance_between(self, hub1: Seaport, hub2: Seaport):
        """
        Returns the maritime distance between two seaports,
        measured as the shortest path alng the PH coastal visibility graph.
        """
        shortest = Seaport.maritime_route(hub1.lon, hub1.lat, hub2.lon, hub2.lat, self.vis_graph)
        segment_distances = [
            Network.haversine_m(
                shortest[i][0], shortest[i][1], 
                shortest[i+1][0], shortest[i+1][1]
            ) 
            for i in range(len(shortest) - 1)
        ]
        return sum(segment_distances)

    def build_graph(self):
        """Builds a networkx.Graph representing the network of seaports and coastal vertices."""
        G = nx.Graph()

        for node in self.vis_graph.graph.graph.keys():
            G.add_node((node.x, node.y))
        
        for edge in self.vis_graph.graph.edges:
            p1 = edge.p1
            p2 = edge.p2
            G.add_edge((p1.x, p1.y), (p2.x, p2.y))
        
        self.graph = G

    def compute_graph_distances(self):
        """Assigns distances as weights to the edges of the graph."""
        distances = {(u, v): Network.haversine_m(u[0], u[1], v[0], v[1]) for u, v in self.graph.edges}

        nx.set_edge_attributes(self.graph, distances, "distance_m")

    def _route_coords(self, hub1: Seaport, hub2: Seaport):
        return Seaport.maritime_route(hub1.lon, hub1.lat, hub2.lon, hub2.lat, self.vis_graph)

    @staticmethod
    def maritime_route(lon1: float, lat1: float, lon2: float, lat2: float, graph: vg.VisGraph) -> list:
        """
        Generates a list of point coordinates along the shortest maritime route between two points
        (i.e., along a visibility graph, with island polygons as obstacles to travel).
        """
        origin = vg.Point(lon1, lat1)
        destination = vg.Point(lon2, lat2)

        poly_o = graph.point_in_polygon(origin)
        poly_d = graph.point_in_polygon(destination)

        start = graph.closest_point(origin, poly_o) if poly_o != -1 else origin
        end = graph.closest_point(destination, poly_d) if poly_d != -1 else destination

        shortest = graph.shortest_path(start, end)

        return [(point.x, point.y) for point in shortest]