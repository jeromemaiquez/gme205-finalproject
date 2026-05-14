from models.hub import Hub

class Network():
    """
    Base class for networks of transport hubs (airport and seaport),
    where routing/distance functionalities are assigned.
    
    Attributes:
    - hubs: list[Hub]
        List of hubs to include in the network
    """

    def __init__(self, hubs: list[Hub]):
        if any([isinstance(h, Hub) == False for h in hubs]):
            raise ValueError("`hubs` parameter must be list of `Hub` objects or its child classes.")
        
        self.hubs = hubs
        self.graph = None
    
    def distance_between(self, hub1: Hub, hub2: Hub):
        # return Hub.haversine_m(hub1.lon, hub1.lat, hub2.lon, hub2.lat)
        raise NotImplementedError("Must be implemented by the child classes `AirNetwork` or `SeaNetwork`.")
    
    def build_graph(self):
        raise NotImplementedError("Must be implemented by the child classes `AirNetwork` or `SeaNetwork`.")

    def compute_all_pairs_distances(self):
        raise NotImplementedError("Must be implemented by the child classes `AirNetwork` or `SeaNetwork`.")