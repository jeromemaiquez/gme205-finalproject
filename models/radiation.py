from models.hub import Hub
from models.network import Network
import numpy as np
import pandas as pd
from tqdm import tqdm

# Feedback 1: radiation model loops too slow for 100+ seaports (need way to optimize)
# Feedback 2: test results show that Huff model may be needed to replace simple isochrones

class Radiation:
    """
    The radiation model for human migration. This model assumes that the choice
    of a traveler's destination consists of two steps:

        1. Each opportunity in every location is assigned a "fitness", represented by a
        number :math:`z`, chosen from some distribution :math:`P(z)` whose value represents
        the quality of the opoprtunity for the traveler.
        2. The traveler ranks all opportunities according to their distances from the origin
        location and chooses the closest opportunity with a fitness higher than the traveler's
        fitness threshold (another number extracted from the fitness distribution :math:`P(z)`).

    Thus, the average number of travelers from location :math:`i` to location :math:`j` takes the form:

        .. math::
            T_{ij} = O_i \\frac{1}{1 - \\frac{m_i}{M}} \\frac{m_i m_j}{(m_i + s_{ij})(m_i + m_j + s_{ij})}.

    The destination of the :math:`O_i` trips originating in :math:`i` is sampled from a distribution
    of probabilities that a trip originating in :math:`i` ends in location :math:`j`. This probability depends on:
        
        - the number of opportunities at the origin :math:`m_i`
        - the number of opportunities at the destination :math:`m_j`
        - the number of opportunities :math:`s_{ij}` within a circle of radius :math:`r_{ij}`
        centered in :math:`i` (excluding the source and destination themselves).

    This conditional probability needs to be normalized so that the probability that a trip originating in the
    region of interest ends in this region is equal to 1. In case of a finite system it is possible to show
    that this is equal to :math:`1 - \\frac{m_i}{M}`, where :math:`M=\\sum_i m_i` is the total number of opportunities.

    In the original version of the radiation model, the number of opportunities is approximated by the population,
    but the total inflows :math:`D_j` to each destination can also be used.

    Note: adapted from the scikit-mobility Python package implementation of RadiationModel
    https://github.com/scikit-mobility/scikit-mobility/blob/master/skmob/models/radiation.py

    Parameters
    ----------
    name: str, optional
        the name of the instantiation of the radiation model.
    locations: list[Hub]
        the list of Hub objects on which to apply the radiation model.
    
    References
    ----------

    .. [SGMB2012] Simini, F., Gonzàlez, M. C., Maritan, A. & Barabasi, A.-L. (2012) A universal model for mobility and migration patterns. Nature 484(7392), 96-100, https://www.nature.com/articles/nature10856
    .. [MSJB2013] Masucci, A. P., Serras, J., Johansson, A., & Batty, M. (2013). Gravity versus radiation models: On the importance of scale and heterogeneity in commuting flows. Physical Review E, 88(2), 022812.

    """

    def __init__(self, network: Network, name='Radiation Model'):
        self.name_ = name
        self.network = network

    def _get_flows(self, origin: Hub, total_relevance: float):
        """
        Compute the flows from location `origin` to all other locations.

        Parameters
        ----------
        origin: Hub
            Hub object representing the origin location
        
        total_relevance: float
            sum of all Hub relevances
        
        Returns
        -------
        flows: np.ndarray
            flows generated from `origin` to the other locations
        
        Notes
        ------
        `m`  :  relevance of origin
        `n`  :  relevance of destination
        `s`  :  relevance in the circle between origin and destination
        """
        flows = []
        probs = []

        origin_id = getattr(origin, self.id_attribute)
        origin_relevance = self.relevance[origin_id]

        try:
            origin_outflow = self.outflow[origin_id]
        except AttributeError:
            origin_outflow = 1

        if origin_outflow > 0.0:
            normalization_factor = 1.0 / (1.0 - origin_relevance / total_relevance)

            # destinations_and_distances = []
            # for destination in tqdm(self.locations):
            #     destination_id = getattr(destination, self.id_attribute)
            #     if destination_id != origin_id:
            #         destinations_and_distances += \
            #             [(destination_id, origin.distance_to(destination))]

            dests_and_dists = self.network.compute_single_source_distances(origin)
            destinations_and_distances = [(dest, dist) for dest, dist in zip(dests_and_dists.keys(), dests_and_dists.values())]

            destinations_and_distances.sort(key=lambda x: x[1])

            sum_inside = 0.0
            for destination_id, _ in destinations_and_distances:
                destination_relevance = self.relevance[destination_id]
                prob_origin_destination = normalization_factor * \
                    (origin_relevance * destination_relevance) / \
                    ((origin_relevance + sum_inside) * (
                        origin_relevance + sum_inside + destination_relevance
                    ))
                
                sum_inside += destination_relevance
                flows += [[origin_id, destination_id]]
                probs.append(prob_origin_destination)
            
            probs = np.array(probs)
            quantities = np.rint(origin_outflow * probs)
            flows = [flows[i] + [od] for i, od in enumerate(quantities)]

        return flows

    def simulate(
        self,
        id_attribute: str,
        outflow: str = "outflow",
        relevance: str = "attraction",
        directed: bool = False
    ):
        """
        Run the simulation of the radiation model.

        Parameters
        ----------
        id_attribute: str
            the Hub attribute representing the Hub unique identifier.
        outflow: str | list[float]
            the Hub attribute or list of values representing its size/total outflow. Default is 'outflow'.
        relevance: str | list[float]
            the Hub attribute or list of values representing a measure of its 'relevance'. Default is 'attraction'.
        directed: bool
            whether the output flow matrix has different values for loc_i --> loc_j and loc_j --> loc_i. Default is False.
            
        Returns
        -------
        pandas.DataFrame
            origin-destination flows generated by the radiation model.
        """
        self.id_attribute = id_attribute
        self.lats_lngs = [hub.coords for hub in self.network.hubs]
        
        self.relevance = {getattr(hub, self.id_attribute): getattr(hub, relevance) for hub in self.network.hubs}

        self.outflow = {getattr(hub, self.id_attribute): getattr(hub, outflow) for hub in self.network.hubs}

        total_relevance = np.sum(list(self.relevance.values()))

        all_flows = []
        for origin in tqdm(self.network.hubs):
            flows_from_origin = self._get_flows(origin, total_relevance)
        
            if len(flows_from_origin) > 0:
                all_flows += list(flows_from_origin)

        # print(all_flows)    
        return self._from_matrix_to_flowdf(all_flows, directed)
    
    def _from_matrix_to_flowdf(self, all_flows, directed: bool):
        """Convert flow array into a pandas DataFrame."""
        output_list = [[i, j, flow] for i, j, flow in all_flows if flow > 0.]
        df_flows = pd.DataFrame(output_list, columns=["origin", "destination", "flow"])
        df_flows = df_flows[df_flows["origin"] != df_flows["destination"]]
        if not directed:
            df_flows["od_pair"] = df_flows.apply(lambda row: tuple({row["origin"], row["destination"]}), axis=1)
            df_flows = df_flows.groupby("od_pair").agg({"flow": "sum"}).reset_index(drop=False)
            df_flows[["origin", "destination"]] = pd.DataFrame(df_flows["od_pair"].apply(lambda x: list(x)).to_list())
            df_flows = df_flows.drop(columns=["od_pair"])[["origin", "destination", "flow"]]
        
        self.flows = df_flows
        # return df_flows
    
    def get_pair_flow(self, hub1_id: str, hub2_id: str):
        """Returns the flow between two hubs, denoted by their ID attribute."""
        df_flows = self.flows
        is_od = df_flows.apply(lambda row: {row["origin"], row["destination"]}, axis=1) == {hub1_id, hub2_id}

        if not is_od.any:
            raise KeyError("The hub ID pair is not found in the flow matrix.")

        pair_flow = df_flows.loc[is_od, "flow"].values[0]
        return pair_flow
    