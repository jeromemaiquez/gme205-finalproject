from shapely import Point, LineString
from pyproj import Geod
from pathlib import Path
from typing import Self
import math

class Hub:
    """
    Base class for transport hubs (airport and seaport),
    which are modeled as point locations.

    Attributes:
    - name: str
        Name of the transport hub
    - lon: float
        Longitude of the transport hub
    - lat: float
        Latitude of the transport hub
    - attraction: int/float
        Attraction/size score of the transport hub
    - outflow: int
        Total outflow of passengers/vehicles from the hub.
        Used to calibrate the radiation flow model
    """

    _geod = Geod(ellps='WGS84')

    def __init__(
            self, 
            name: str, 
            lon: float, 
            lat: float, 
            attraction: float | None = None,
            outflow: int | None = None 
    ):
        if not (-180 <= lon <= 180):
            raise ValueError("Longitude must be between -180 and 180") 
        if not (-90 <= lat <= 180):
            raise ValueError("Latitude must be between -90 and 90")
        
        self.lon = lon
        self.lat = lat
        self.coords = (self.lat, self.lon)
        self.geometry = Point(lon, lat)
        self.name = name
        self.attraction = attraction
        self.outflow = outflow

    def set_attraction(self, value: int | float, override: bool = False) -> None:
        """
        Assigns a value as a score signifying "attraction"
        or "size" of a given hub in the radiation model.

        Attributes:
        - value: int or float
            Value to assign as the hub's attraction/size score
        - override: bool
            If True, overrides any existing attraction score
        """
        if self.attraction:
            if not override:
                raise ValueError("Hub already has an attraction score. Set `override=True` if you wish to override")
        
        self.attraction = value
    
    def distance_to(self, other) -> float:
        raise NotImplementedError("Must be implemented by Airport or Seaport subclass")
    
    def _route_coords(self, other: Self):
        raise NotImplementedError("Must be implemented by Airport or Seaport subclass")

    def route_linestring(self, other: Self):
        """
        Generates a LineString geometry from the shortest path
        between two airports (great-circle arc).
        """
        all_points = self._route_coords(other)

        return LineString(all_points)

    @staticmethod
    def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        return Hub._geod.line_length([lon1, lon2], [lat1, lat2])

    def __repr__(self):
        return (
            f"Hub name: {self.name}\n"
            f"Hub coordinates: {self.geometry.coords[0]}\n"
            f"Hub attraction: {self.attraction}"
        )
    
