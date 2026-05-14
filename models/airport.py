from hub import Hub
from enum import Enum
import math
from typing import Self

class AirportType(Enum):
    INTERNATIONAL = 1
    PRINCIPAL_1 = 2
    PRINCIPAL_2 = 3
    COMMUNITY = 4

class Airport(Hub):
    """
    Child class of Hub specifically to model airports.
    Has airport-specific attributes and calculates 
    distance via the Haversine distance method.

    Additional attributes:
    - iata_code: str
        The unique IATA code for the airport
    - icao_code: str
        The unique ICAO code for the airport
    - airport_type: int
        The airport's class (international, principal I and II, community)
    - num_runways: int
        No. of runways in the airport, as a proxy for capacity
    - outflow: int
        Total outflow of passengers/aircraft from the airport.
        Used to calibrate the radiation flow model
    """

    def __init__(
        self, 
        name: str, 
        lon: float, 
        lat: float, 
        iata_code: str,
        icao_code: str,
        airport_type: int,
        num_runways: int = None,
        attraction: float | None = None,
        outflow: int | None = None
    ):
        super().__init__(name, lon, lat, attraction, outflow)
        self.iata_code = iata_code
        self.icao_code = icao_code
        self.airport_type = AirportType(airport_type).name
        self.num_runways = num_runways

    def distance_to(self, other: Self):
        """
        Computes the great-circle distance between two Airports
        using the Haversine distance method.
        """
        return Hub.haversine_m(self.lon, self.lat, other.lon, other.lat)
    
    def _route_coords(self, other: Self):
        """
        Generates a list of (lon, lat) tuples representing the points
        along the shortest route between two airports.
        """
        lonlats = Hub._geod.npts(
            self.lon, self.lat, 
            other.lon, other.lat, 
            npts=10
        )

        return [(self.lon, self.lat)] + lonlats + [(other.lon, other.lat)]

    def __repr__(self):
        return (
            f"Airport name: {self.name}\n"
            f"IATA Code: {self.iata_code}\t ICAO Code: {self.icao_code}\n"
            f"Airport coordinates: {self.geometry.coords[0]}\n"
            f"Airport attraction: {self.attraction}"
        )