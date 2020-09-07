# Summary

We developed the Multiscale Solar Water Heating (MSWH) software to enable users to model energy use for individual and community scale solar water heating projects and compare it with the performance of conventional natural gas tank water heaters. The package contains a [Jupyter notebook with examples](https://github.com/LBNL-ETA/MSWH/blob/master/scripts/MSWH%20System%20Tool.ipynb), a GUI developed using Django Framework and both functional and unit tests. In addition, the package is structured so that it can be extended with further technologies, applications and locations as needed.

We use simplified fast performing energy balance based models. We connect the models into two preconfigured systems that are provided with MSWH:
* Solar thermal collector, hot water thermal storage tank, with a selection of backups: gas storage water heater, instantaneous gas water heater
* Photovoltaic panel, heat pump water heater hot water thermal storage tank, electric resistance water heater as backup

We built a simple simulation solver that uses explicit forward Euler method to solve the balance equations in each simulation time-step.

The component models we either identified in the existing literature and created a custom Python implementation, or we developed new models. In our implementation we implemented the following existing or new models:
* Solar irradiation on a tilted surface model is based on [ref duffy beckman]
* Solar collector models and model parameters are based on [ref SRCC] and [ASHRAE]
* We converted natural gas tank water heater model from [ref WHAM] into a hourly time-step model implementation
* Photovoltaic model based on a simplified model found in [modelica buildings library]
* Heat pump water heater tank was modeled based on [ref NREL]
* Solar thermal tank is a phenomenology based model based on ideas similar to model used in [ref NREL SAM]
* Simplified performance data based gas burner model to represent instantaneous gas water heater
* Simple electric resistance model to represent instantaneous electric gas
water heater
* Simplified data based solar and distribution pump model
* To model the distribution piping network we developed a simplified model that is capable of accounting for thermal losses at stagnation and flows on demand with correction factors available to help account for the relatively long time-step of 1h.

We performed extensive validation of [component models](https://github.com/LBNL-ETA/MSWH/blob/master/mswh/system/tests/test_components.py) and [system models](https://github.com/LBNL-ETA/MSWH/blob/master/mswh/system/tests/test_models.py) against performance results obtained using freely available open source tools and certification data generated using commercial tools. The validation models are a part of the test suite and show good agreement in all test comparisons.

To evaluate a potential solar water heating project by looking at its simulation performance the user should create an instance of each system. For this, and the detailed examples are is provided in [example notebooks](https://github.com/LBNL-ETA/MSWH/tree/master/scripts), the user needs to specify:
* The project location by choosing one of the climate zones for which data is available in our database. The database includes 16 CA climate zone files and can be extended for other regions.
* For each household: count of people supplied by the system and whether there is any daytime occupancy.

We developed component sizing rules and size scaling rules to account for household occupancy and project scale, respectively. The rules are readily available in the example notebooks and can easily be modified for exploratory purposes. For example,  users who already have a solar water heating system and are planning to increase the occupancy, are retrofitting an existing system or already poses one of the components and are looking to appropriately size the others can simulate alternatives and compare their the energy consumption and solar fraction results.

Performance visualization is available both in example notebooks and through
the Django based GUI.

The application of the models can be to explore the benefits of grouping multiple households to be served by a single solar water heating system in comparison to a system installed in a single household. An another application of the model is to calculate gas savings when changing from a gas water heater to a solar water heater in a single household.

More on the hot water demand model, solar radiation, component and system models can be found in [ref Report] project report for which this software was developed. The software found its application in [ACEEE ref] and [Hannes theses ref].

# Statement of Need

The project that prompted the development of this software, described in [ref Report] was enquiring whether there are any economic benefits in grouping households to be served by a single solar water heating installation, in comparison to single household solar water heating installations on the state of California level.

Our primary motivation to develop this software was the combination of the level of detail and the required simulation time. Namely, in order to capture sufficient level of detail of the California demographics, such as variability in climate zones, household types, and household occupancy, we wanted to be able to simulate a few alternative water heating systems in each of the California sample households. Secondly, to get a more realistic picture of the effect of thermal storage and distribution system losses, we opted to perform a simulation with relatively short time-steps of 1h for a duration of one representative year. We were not able to identify an open source tool that is capable of firstly satisfying the simulation speed requirement combined with the necessary level of detail for our analysis and secondly providing the flexibility for us to customize various integral parts of the analysis such as automate the component and system size scaling, specify hot water load profiles and solar radiation for each household or group of households in the sample.

To satisfy our research need we thus opted to develop lightweight simulation models for all involved systems that would allow for around 120 thousand simulation runs together with the component sizing and life-cycle cost analysis to be performed on a PC with 12 cores in about 8h. The users can expect a single solar water heater simulation model to run for about 0.16 seconds, providing an almost instantaneous experience for a user only seeking to design and investigate a single system.

# Acknowledgments

This work was supported by the California Energy Commission, Public Interest Energy Research Program, under Contract No. PIR-16-022.

# References

ACEEE
Report in press
Hannes thesis
Modelica Buildings library
IDEA data collection framework paper
Solar engineering
SRCC certification data


- go through refs of the report
