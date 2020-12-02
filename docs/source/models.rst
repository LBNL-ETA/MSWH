Multiscale Solar Water Heating (MSWH)
=====================================

Scope
^^^^^

The main purpose of the Multiscale Solar Water Heating (MSWH) software is to model energy use for individual and community scale solar water heating projects in California.

The package contains functional and unit tests and it is structured so that it can be extended with further technologies, applications, and locations.

Usage
^^^^^

The user provides a climate zone for a project, occupancy for each household, and whether any of the occupants stay at home during the day. The software can then load a set of example California specific hourly domestic hot water end-use load profiles from a database, size, and locate the systems. Next, the user can simulate the hourly system performance over a period of one representative year, visualize and explore the simulation results using time-series plots for temperature profiles, heat and power rates, or look at annual summaries. Similarly, the user can model individual household solar water heating projects and base case conventional gas tank water heater systems, such that the results can be compared between the individual, community-scale, and base case systems.

This functionality is readily available through a `Jupyter notebook <https://github.com/LBNL-ETA/MSWH/blob/v2.0.0/scripts/MSWH%20System%20Tool.ipynb>`_ and a `Django web framework graphical user interface (GUI) <https://github.com/LBNL-ETA/MSWH/tree/v2.0.0/web>`_, depending on what level of detail the user would like to access. Please see the README file on the `MSWH repo <https://github.com/LBNL-ETA/MSWH>`_ for further usage and installation instructions.

System performance time series visualizations are available both in example notebooks and through the GUI, either spun off locally or `using a web deployed version <https://solar.floweragenda.org/>`_.

Features
^^^^^^^^

This software package contains the following Python modules:

* Solar irradiation on a tilted surface.

* Simplified component models for:

    * Converters: solar collectors, electric resistance heater, gas burner, photovoltaic panels, heat pump.
    * Storage: solar thermal tank, heat pump thermal tank, conventional gas tank water heater.
    * Distribution: distribution and solar pump, piping losses.

* Preconfigured system simulation models for: 

    * Base case gas tank water heaters.
    * Solar thermal water heaters (solar collector feeding a storage tank, with a tankless gas water heater backup in a new installation cases and a basecase gas tank water heater in a retrofit case). 
    * Solar electric water heaters (grid supported photovoltaic panel powering a heat pump storage tank with an electric resistance backup).

* Database with component performance parameters, California specific weather data, and domestic hot water end-use load profiles.

* Django web framework to configure project, parametrize components and `simulate from a web browser <https://solar.floweragenda.org/>`_.

We also developed component sizing rules and size scaling rules to account for the household occupancy and project scale, respectively. The rules are readily available in the example notebooks and can easily be modified for exploratory purposes that we further describe in the Statement of Need section. For the sizing and scaling rules, we used the following data sources: expert knowledge, web-scraped data with the help of a tool described in :cite:`Gerke:2017`, sizing rules available in :cite:`Csi_thermal:2016`, and certification databases such as :cite:`Ccms:2018` and :cite:`Cec_appliance:2019`.

Approach to Component and System Modeling and Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this section we briefly introduce the characteristics of the underlying models and simulation. 

We performed an extensive literature rewiew prior to developing the models. Modelica buildings library by :cite:`Wetter:2014` exceeds the level of detail but proves too detailed and thus somewhat slow for our particular application. SAM tool (:cite:`Blair:2014`) has a fitting level of detail, provides most of the system models that we needed but for our purposes proves not flexible enough in terms of modifying the system configuration, automating the size scaling, and embedding it into our custom life-cycle cost framework.

Namely, to capture a sufficient level of detail of the California demographics, such as variability in climate zones, household types, and household occupancy, we wanted to be able to simulate a few alternative water heating systems in each of the California sample households. Secondly, to get a more realistic picture of the effect of thermal storage and distribution system losses, we opted to perform a simulation with relatively short time-steps of one hour for a duration of one representative year. We were not able to identify an open source tool that is capable of firstly satisfying the simulation speed requirement combined with the necessary level of detail for our analysis and secondly providing the flexibility for us to customize various integral parts of the analysis such as automate the component and system size scaling, specify hot water load profiles and solar radiation for each household or group of households in the sample.

To satisfy our research need we thus opted to develop lightweight simulation models for all involved systems that would allow for around 120,000 simulation runs together with the component sizing and life-cycle cost analysis to be performed on a computer with a 12-core processor in about 8 hours. The users can expect a single solar water heater simulation model to run in less than one second (the developers were experiencing run times on the order of 0.2 seconds), providing an almost instantaneous experience for a user only seeking to design and investigate a single system.

We developed and implemented simplified fast performing energy balance based component models. We connected the component models into two preconfigured solar water heating systems, that are both provided with the MSWH software. Those models are:

* Solar thermal collector, hot water thermal storage tank, with a selection of backups: gas storage water heater or an instantaneous gas water heater.
* Photovoltaic panel, heat pump tank water heater, with an electric resistance water heater as backup.

We built a simple simulation solver that uses the explicit forward Euler method to solve the balance equations in each simulation time-step.

The component models were either developed from scratch or implemented in Python based on existing models identified in the literature. We implemented the following existing or new models:

* Solar irradiation on a tilted surface model is based on equations found in :cite:`Duffie:2013`.
* Solar collector models and model parameters are based on :cite:`Ashrae:2013` and :cite:`Srcc:2013`.
* We converted the natural gas tank water heater model from :cite:`Lutz:1998` into an hourly time-step model implementation.
* Photovoltaic model is based on a simplified model found in :cite:`Wetter:2014`.
* Heat pump water heater tank is based on :cite:`Sparn:2014`.
* Solar thermal tank is a phenomenological model based on ideas very similar to the model developed for NREL's SAM software (:cite:`Blair:2014`), as described in :cite:`DiOrio:2014`.
* Simplified performance data-based gas burner model was implemented to represent instantaneous gas water heater.
* Simple electric resistance model was implemented to represent instantaneous electric water heater.
* We developed a simplified data based solar and distribution pump model.
* To model the distribution piping network we developed a simplified model that is capable of accounting for thermal losses at stagnation and flows on-demand with correction factors available to help account for the relatively long time-step of one hour.

More details on the hot water demand model used in creating the database of sample hot water use load profiles, as well as extensive detail on the software's solar radiation, component and system models can be found in the project report by :cite:`Coughlin:2021`. :cite:`Gerhart:2019` thesis provides additional details on the solar electric system model development.

Note that the weather data are currently mostly limited to California and can be extended to other climate zones. An example climate zone outside of California was added for Banja Luka, Bosnia and Herzegovina, through an `additional example Jupyter notebook <https://github.com/LBNL-ETA/MSWH/blob/v2.0.0/scripts/MSWH%20System%20Tool%20-%20Additional%20Climate.ipynb>`_. The water consumption profiles can be highly location specific and their development for additional climate zones would require new research efforts. A quick approximation may be made with caution by scaling the California profiles to match the location-specific estimate of the average annual water use. This is possible as the shape of each daily profile can be assumed similar and sufficiently variable to allow for the study of transient and peak load effects at any location. The weather processor is TMY3 enabled and the user may populate the database with additional climates as needed.

The energy sources we consider are solar irradiation, gas, and electricity. The source energy is converted, if needed stored, and distributed to meet the end-use loads for each household.

Upon assembling the components into systems, we perform an annual simulation with hourly timesteps. We solve any differential equations for each time step using an explicit forward Euler method, a first order technique that provides a good approximation given the dynamics of the process observed and the level of detail required in our analysis.

We configure and size each MSWH thermal configuration so that it complies with the CSI-T (California Solar Initiative - Thermal) rebate program sizing requirements. The system model assumes appropriate flow and temperature controls and includes freeze and stagnation protection.

Future Applications - Statement of Need
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When it comes to the future application of the MSWH software, we can envision four main groups of users:

* Researchers and policy developers.
* Solar water heating planners, designers, and contractors.
* Homeowners.
* Educators.

If the features of the existing MSWH software are sufficient for their application, the policy developers and researchers could utilize the existing MSWH software by embedding it into some larger analysis framework they construct such that it provides answers to their specific research questions. Should they require additional system configurations and even additional components, the existing framework should be expanded in line with the structure made available to the user in the MSWH software. When systems are added following the structure of the existing systems, the addition of such a new system to the GUI is made possible by using the flexible web framework.

Solar thermal water heating system planners, designers, and contractors may find it useful to have access to a freely available simulation tool, such as the MSWH software, that they can use to evaluate various system designs. The design parameters that such users can easily modify are household occupancies, climate zone, collector and tank sizes, component performance parameters such as insulation level of any thermal storage tanks, and types of solar collectors. The MSWH software relies on standard collector rating data readily available for most designs found on the market today. For each proposed design the MSWH software will output, among other results, the solar fraction and the backup energy use on an annual level, the two variables allowing for a quick cross-comparison for the proposed designs.

Similarly, homeowners considering transitioning to a solar water heating system may be interested in analyzing a hypothetical system before seeking further professional help. Or, some homeowners may simply be interested in learning about both solar water heating systems and system simulation in general. Another example use case would be to enable the occupants of households that:

* Are retrofitting an existing system due to an increase or decrease in occupancy, or
* Already possess one of the components and are looking to appropriately size the others

to simulate alternatives and compare the obtained energy consumption and solar fraction results for any alternative designs they like to define.

Lastly, simulation tools tend to be inaccessible to non-technical users, both in terms of usage and the chance for the user to understand the underlying codebase just by reading through it. The MSWH software provides a unique insight into what actually happens in a relatively simple mezzo-level simulation model due to the use of readable Python code, while the example notebooks and GUI allow for instant utilization of the models. These features make the code suitable also for educators.

Code Development and Code Contributions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We welcome code contributions. The development primarily takes place on the `MSWH GitHub repository <https://github.com/LBNL-ETA/MSWH>`_. Please refer to the `contributing guidelines <https://github.com/LBNL-ETA/MSWH/blob/master/contributing.md>`_ and `README.md <https://github.com/LBNL-ETA/MSWH/blob/master/README.md>`_ for further instructions, including those on running the unit tests.