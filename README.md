# Project Title
GmE 205 - Final Project

### Estimating demand for domestic air & sea travel via radiation modeling

# Objective

The main objective of the project is to:

> Develop a Python-based tool to estimate PH domestic air & sea travel demand using a radiation model based on distance and catchment-level relevance

Specific objectives include:
- calculate distances between hubs (airports or seaports) based on the specific characteristics of air vs. sea travel
- estimate the "relevance" of a hub based on the total population inside its catchment
- compute pairwise potential travel demand (measured as passenger flow) between hubs

# System Design
![UML Diagram](uml/Gme205_FinalProject_UML_.drawio.png)

The overall object-oriented design of this project can be split into 3 main parts:

1. **Hub**: base class for nodes of inter-island transport, containing shared attributes and methods for both Airports and Seaports
    - shared attributes: hub name, lat-lon coordinates, attraction/relevance, outflow
    - methods to set a hub's attraction & outflow
    - **Airport**: extends attributes to include IATA & ICAO code + airport type
    - **Seaport**: extends attributes to include UN/LOCODE, PMO, and seaport type
2. **Network**: base class for networks of transit hubs that share a travel mode, responsible for distance calculations between hubs
    - attributes: list of hubs (either all sea or all air), nx.Graph() of links between hubs
    - methods: graph builder, 3 distance calculations
        - pairwise
        - network-wide
        - single-source (1 origin to all other destinations)
3. **Radiation**: class containing radiation modeling logic
    - requires a network of airports & seaports
    - model simulation is kept separate from model instantiation by using a method, which requests hub attribute names for ID, outflow, and relevance
    - uses Networkx for efficient OD matrix creation

# Radiation Model

The radiation model for human migration. This model assumes that the choice of a traveler's destination consists of two steps:

1. Each opportunity in every location is assigned a "fitness", represented by a number :math:`z`, chosen from some distribution :math:`P(z)` whose value represents the quality of the opoprtunity for the traveler.
2. The traveler ranks all opportunities according to their distances from the origin
location and chooses the closest opportunity with a fitness higher than the traveler's
fitness threshold (another number extracted from the fitness distribution :math:`P(z)`).

Thus, the average number of travelers from location :math:`i` to location :math:`j` takes the form:
    $$
    T_{ij} = O_i \frac{1}{1 - \frac{m_i}{M}} \frac{m_i m_j}{(m_i + s_{ij})(m_i + m_j + s_{ij})}.
    $$

The destination of the $`O_i`$ trips originating in $`i`$ is sampled from a distribution
of probabilities that a trip originating in $`i`$ ends in location $`j`$. This probability depends on:
        
- the number of opportunities at the origin $`m_i`$
- the number of opportunities at the destination $`m_j`$
- the number of opportunities $`s_{ij}`$ within a circle of radius $`r_{ij}`$ centered in $`i`$ (excluding the source and destination themselves).

This conditional probability needs to be normalized so that the probability that a trip originating in the region of interest ends in this region is equal to 1. In case of a finite system it is possible to show that this is equal to $`1 - \frac{m_i}{M}`$, where $`M=\sum_i m_i`$ is the total number of opportunities.

In the original version of the radiation model, the number of opportunities is approximated by the population,
but the total inflows $`D_j`$ to each destination can also be used.

Note: adapted from the scikit-mobility Python package implementation of RadiationModel
https://github.com/scikit-mobility/scikit-mobility/blob/master/skmob/models/radiation.py

# Task List

- [x] New `Network` class to store routing/distance functionalities across a list of `Hub` objects
- [x] Child classes of `AirNetwork` and `SeaNetwork`
    - `AirNetwork`: via Haversine distance
    - `SeaNetwork`: convert pyvisgraph.VisGraph to nx.MultiGraph --> nx.multi_source_path_length
= [x] `Hub`, `Airport` and `Seaport` classes to lose `distance_to()` and related methods
    - `Hub`: `assign_attraction`, `assign_population`, `get_hub_id`, etc.
    - `Airport`:  `get_hub_id` (IATA or ICAO), `get_airport_type`
    - `Seaport`: `get_hub_id` (UN/LOCODE), `get_pmo`, `get_seaport_type`
- [x] `Radiation` to use pre-computed distance matrix from `Network` or its children + vectorized operations for its calculations
- [x] Update UML diagram to reflect new `Network` classes and revisions to `Hub` and `Radiation` classes

