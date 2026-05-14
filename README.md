# Project Title
GmE 205 - Laboratory Exercise 6

# How to set up the virtual environment
1. Create a folder on your computer and open it in your IDE (e.g., VS Code)
2. Open the terminal then create the virtual environment by running the following:
    ```
    py -m venv .venv
    .\.venv\Scripts\activate
    ```
3. Press ```Ctrl + Shift + P``` in VS Code, search for *Python: Select Interpreter*, then choose the interpreter inside the ```.venv``` folder
4. Install the required packages by running the following in the terminal:
    ```
    python -m pip install --upgrade pip
    pip install <package1> <package2>
    ```
5. (Recommended) List the installed packages via:
    ```
    pip freeze > requirements.txt
    ```

# How to run Python scripts

In the terminal, ensuring that ```(.venv)``` is present in the prompt, run the following:
    ```
    python <folder/script_name.py>
    ```

# Reflections - Part D
- Part B Summary
    
    `SpatialObject` was created as the parent class, while the following 3 classes inherited from it: `Parcel`, `Building`, and `Road`. The methods `distance_to()` and `intersects()` were implemented at the base level and shared across the child classes. As for relationships:
    - a `Parcel` had zero or more contained `Building`s and zero or more adjacent `Road`s
    - a `Building` had one `Parcel` it was located on and zero or more `Household`s residing there
    - a `Road` had zero or more `Parcel`s it was adjacent to

- Part C Summary

    The classes in my model were the base class `Hub`, its child classes `Airport` and `Seaport`, and the analyzer class `RadiationModel` (to still be implemented). As for the `Hub` class and its children, the shared attributes are:
    - `hub_name`
    - `lat` and `lon` for the location
    - `attraction` for the attraction/size score
    
    Meanwhile, the child classes `Airport` and `Seaport` had their unique attributes, such as `iata_code` and `icao_code` for `Airport` and `un_locode` and `pmo` for `Seaport`. The shared methods are:
    - `distance_to()` (which was duck-typed for `Airport` and `Seaport`),
    - `_route_coords()`: a private method to return the points along the shortest route between a `Hub` and an `other`
    - `route_linestring()`: a method returning a shapely.LineString object for the shortest route between a `Hub` and an `other`
    - `set_attraction()`: assigns an attraction score to a `Hub` (i.e., from some external calculation, e.g., catchment-based metric)

    Although not implemented yet, I anticipate challenges in coming up with `RadiationModel` and what exact relationship it will have with the `Hub` class. There may even have to be additional classes for `Catchment` (which would also have to be related to a `Hub`), but I am still not sure if this is necessary.

    The fiile name of my UML JPG image is `uml/Gme205_FinalProject_UML.drawio.png`.

- Final Reflections

    1. I found it straightforward to translate inheritance and attributes into code, since this mostly involved adding these into the `__init__()` constructor method of the class. It was more difficult to implement methods, especially polymorphic ones such as `distance_to()`.
    2. Although not done yet, I anticipate it will be a challenge to implement the `RadiationModel` class and establish its exact relationship with the `Hub` class, since any given radiation model has to involve multiple `Hub`s of the same type (either all `Airport`s or all `Seaport`s).
    3. I had to revise some parts of my UML (and my design overall) during implementation, since I had to decide on the go whether a given solution is the best one or not given the project goals. I envision this will remain the case as I continue implementing the rest of the model, with catchment-level attraction calculation and the radiation model.
    4. OOAD is a critical first step in embarking on any OOP app development project. Before writing any code down, it is important to at least have an idea on what the main classes are, what their attributes and methods are, and who is related to whom. Are some classes parents and children of each other? How are other classes referenced in others? Even though the exact design might still change during implementation, having that initial picture will help guide the rest of the implementation towards a clear goal.

# Next Steps

- [x] New `Network` class to store routing/distance functionalities across a list of `Hub` objects
- [x] Child classes of `AirNetwork` and `SeaNetwork`
    - `AirNetwork`: via Haversine distance
    - `SeaNetwork`: convert pyvisgraph.VisGraph to nx.MultiGraph --> nx.multi_source_path_length
= [x] `Hub`, `Airport` and `Seaport` classes to lose `distance_to()` and related methods
    - `Hub`: `assign_attraction`, `assign_population`, `get_hub_id`, etc.
    - `Airport`:  `get_hub_id` (IATA or ICAO), `get_airport_type`
    - `Seaport`: `get_hub_id` (UN/LOCODE), `get_pmo`, `get_seaport_type`
- [ ] `RadiationModel` to use pre-computed distance matrix from `Network` or its children + vectorized operations for its calculations