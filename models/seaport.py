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

    def get_seaport_type(self):
        """Returns the airport class/type of an airport."""
        return self.airport_type
    
    def get_pmo(self):
        """Returns the seaport's port management office (PMO)."""
        return self.pmo
    
    def get_hub_id(self):
        """Returns the ID of the seaport."""
        return self.un_locode

    def __repr__(self):
        return (
            f"Seaport name: {self.name}\n"
            f"Seaport UN/LOCODE: {self.un_locode}\t Seaport PMO: {self.pmo}\n"
            f"Seaport coordinates: {self.geometry.coords[0]}\n"
            f"Seaport attraction: {self.attraction}"
        )