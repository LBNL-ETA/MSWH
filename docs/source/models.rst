.. _sec_sys_mod:

Multiscale Solar Water Heating (MSWH)
-------------------------------------

Scope
^^^^^

The main purpose of the Multiscale Solar Water Heating (MSWH) software is to model energy use for individual and community scale solar water heating projects in California.

The package contains functional and unit tests and it is structured so that it can be extended with further technologies, applications and locations.

Usage
^^^^^

The user provides a climate zone for a project, an occupancy for each household and whether any of the occupants stay at home during the day. The software can then load a set of example California specific hourly domestic hot water end-use load profiles from a database, size and locate the systems. The user can now simulate the hourly system performance over a period of one representative year, visualize and explore the simulation results using time-series plots for temperature profiles, heat and power rates, or look at annual summaries. Similarly the user can model individual household solar water heating projects and base case conventional gas tank water heater systems, such that the results can be compared between the individual, community and base case systems.

This functionality is readily available through a Jupyter notebook and a Django web framework, depending on what level of detail the user would like to access. Please see the README file on the `MSWH repo <https://github.com/LBNL-ETA/MSWH>`_ for usage and installation details.

Features
^^^^^^^^

This software package contains the following Python modules:

* Solar irradiation on a tilted surface

* Simplified component models for Converter (solar collectors, electric resistance heater, gas burner, photovoltaic panels, heat pump), Storage (solar thermal tank, heat pump thermal tank, conventional gas tank water heater), and Distribution (distribution and solar pump, piping losses) components

* Preconfigured system simulation models for: base case gas tank water heaters, solar thermal water heaters (solar collector feeding a storage tank, with a tankeless gas water heater backup in a new installation cases and a basecase gas tank water heater in a retrofit case) and solar electric water heaters (heat pump storage tank with an electric resistance backup)

* Database with component performance parameters, California specific weather data and domestic hot water end-use load profiles

* Django web framework to configure project, parametrize components and run simulation from a web browser

Approach to System Modeling and Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The energy sources we consider are solar irradiation, gas and electricity. The source energy is converted, if needed stored, and distributed to meet the end-use loads for each household.

Upon assembling the components into systems, we perform an annual simulation with hourly timesteps. We solve any differential equations for each time step using an explicit forward Euler method, a first order technique that provides a good approximation given the dynamics of the process observed and the level of detail required in our analysis.

We configure and size each MSWH thermal configuration so that it complies with the CSI-thermal rebate program sizing requirements. The system model assumes appropriate flow and temperature controls and includes freeze and stagnation protection.
