from models.network import Network
from models.seaport import Seaport
from models.hub import Hub
import networkx as nx
import pyvisgraph as vg
import numpy as np
from sklearn.neighbors import BallTree

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
        self.hubs = hubs
        self.vis_graph = vis_graph
        self.build_graph()

        super().__init__(hubs, self.graph)

    def distance_between(self, hub1: Seaport, hub2: Seaport):
        """
        Returns the maritime distance between two seaports,
        measured as the shortest path alng the PH coastal visibility graph.
        """
        shortest = SeaNetwork.maritime_route(hub1.lon, hub1.lat, hub2.lon, hub2.lat, self.vis_graph)
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
        hub_ids = [h.un_locode for h in self.hubs]
        hub_coords = [(h.lon, h.lat) for h in self.hubs]

        # hub_closest = [
        #     SeaNetwork.closest_visible_point(
        #         hub.lon, hub.lat,
        #         self.vis_graph, 
        #         as_coords=False
        #     )
        #     for hub in self.hubs
        # ]
        # print(hub_closest[:5])

        # self.vis_graph.update(hub_closest)

        G = nx.Graph()

        node_id_attr = {}
        node_coords = []
        for idx, node in enumerate(self.vis_graph.graph.graph.keys()):
            # G.add_node((node.x, node.y))
            node_id = str(idx)
            G.add_node(node_id, coords=(node.x, node.y))
            node_id_attr[node] = node_id
            node_coords.append((node.x, node.y))
             
        for edge in self.vis_graph.graph.edges:
            p1 = edge.p1
            p2 = edge.p2

            node1_id = node_id_attr[p1]
            node2_id = node_id_attr[p2]

            G.add_edge(node1_id, node2_id)
        
        for hub_id, coord in zip(hub_ids, hub_coords):
            G.add_node(hub_id, coords=(coord[0], coord[1]))
            nearest_neighbor = SeaNetwork.nearest_existing_point(
                (coord[0], coord[1]),
                node_coords
            )
            G.add_edge(hub_id, node_id_attr[nearest_neighbor])
        
        self.graph = G

    def compute_graph_distances(self):
        """Assigns distances as weights to the edges of the graph."""
        distances = {
            (u, v): Network.haversine_m(
                self.graph.nodes[u]["coords"][0],
                self.graph.nodes[u]["coords"][1],
                self.graph.nodes[v]["coords"][0],
                self.graph.nodes[v]["coords"][1]
            ) 
            for u, v in self.graph.edges
        }

        nx.set_edge_attributes(self.graph, distances, "distance_m")

    def compute_single_source_distances(self, source: Seaport):
        # source_coords = SeaNetwork.closest_visible_point(source.lon, source.lat, self.vis_graph)

        # destination_coords = [
        #     SeaNetwork.closest_visible_point(dest.lon, dest.lat, self.vis_graph)
        #     for dest in self.hubs if dest != source
        # ]

        destinations = [h.un_locode for h in self.hubs if h != source]

        # Calculate distance between a source node and all other nodes in the graph
        destinations_and_distances = nx.single_source_dijkstra_path_length(
            self.graph,
            source.un_locode,
            weight="distance_m"
        )

        # Filter results only to dest nodes that represent ports
        destinations_and_distances = {
            dest: destinations_and_distances[dest]
            for dest in destinations_and_distances
            if dest in destinations
        }

        return destinations_and_distances

    @staticmethod
    def closest_visible_point(
        lon: float, 
        lat: float, 
        graph: vg.VisGraph, 
        as_coords: bool = True
    ):
        """
        Returns the coastal vertex closest to a given point.
        Allows inland locations (e.g. ports) to be included in a SeaNetwork.
        """
        vg_point = vg.Point(lon, lat)
        pt_in_poly = graph.point_in_polygon(vg_point)
        
        closest = (
            graph.closest_point(vg_point, pt_in_poly) 
            if pt_in_poly != -1 else vg_point
        )

        if as_coords == False:
            return closest

        closest_coords = (closest.x, closest.y)

        return closest_coords


    def _route_coords(self, hub1: Seaport, hub2: Seaport):
        return Seaport.maritime_route(hub1.lon, hub1.lat, hub2.lon, hub2.lat, self.vis_graph)

    @staticmethod
    def nearest_existing_point(
        target: tuple[float, float],
        candidates: list[tuple[float, float]],
    ):
        """Finds the nearest existing candidate point to a given target."""
        target_array = np.array([target])
        candidates_array = np.array(candidates)
        
        target_rad = np.deg2rad(target_array)
        candidates_rad = np.deg2rad(candidates_array)

        tree = BallTree(candidates_rad, metric="haversine")
        _, index = tree.query(target_rad, k=1)

        nearest_point = candidates_array[index[0][0]]
        return vg.Point(*nearest_point)

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