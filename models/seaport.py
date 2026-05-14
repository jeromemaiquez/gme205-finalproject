from models.hub import Hub
from enum import Enum
from typing import Self
import pyvisgraph as vg

class SeaportType(Enum):
    BASE = 1
    TERMINAL = 2
    OTHER_GOVT = 3
    PRIVATE = 4

class Seaport(Hub):
    """
    Child class of Hub specifically to model seaports.
    Has seaport-specific attributes and calculates distance
    via visibility graphs (using the pyvisgraph package).

    Additional attributes:
    - un_locode: str
        The unique UN/LOCODE code for the seaport
    - pmo: str
        The port management office (PMO) overseeing the seaport
    - seaport_type: int
        The seaport classification (base, terminal, other government, private)
    - num_berths: int
        No. of berths in the seaport, as a proxy for capacity
    - outflow: int
        Total outflow of passengers/vehicles from the hub.
        Used to calibrate the radiation flow model
    """

    _graph = None

    def __init__(
        self, 
        name: str, 
        lon: float, 
        lat: float, 
        un_locode: str,
        pmo: str,
        seaport_type: int,
        num_berths: int = None,
        attraction: float | None = None,
        outflow: int | None = None
    ):
        super().__init__(name, lon, lat, attraction, outflow)
        self.un_locode = un_locode
        self.pmo = pmo
        self.seaport_type = SeaportType(seaport_type).name
        self.num_berths = num_berths

    def distance_to(self, other: Self):
        """
        Computes the maritime distance between two seaports,
        measured as the shortest path along the PH coastal visibility graph.
        """
        if Seaport._graph is None:
            raise RuntimeError("Maritime graph not initialized")
        shortest = Seaport.maritime_route(self.lon, self.lat, other.lon, other.lat, Seaport._graph)
        segment_distances = [
            Hub.haversine_m(
                shortest[i][0], shortest[i][1], 
                shortest[i+1][0], shortest[i+1][1]
            ) 
            for i in range(len(shortest) - 1)
        ]
        return sum(segment_distances)

    def _route_coords(self, other):
        return Seaport.maritime_route(self.lon, self.lat, other.lon, other.lat, Seaport._graph)

    @classmethod
    def set_graph(cls, graph):
        """
        Initializes the visibility graph used by the class for the project.
        """
        cls._graph = graph
    
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

    def __repr__(self):
        return (
            f"Seaport name: {self.name}\n"
            f"Seaport UN/LOCODE: {self.un_locode}\t Seaport PMO: {self.pmo}\n"
            f"Seaport coordinates: {self.geometry.coords[0]}\n"
            f"Seaport attraction: {self.attraction}"
        )