# Summary

We developed the Multiscale Solar Water Heating (MSWH) software to enable users to model energy use for individual and community scale solar water heating projects in California and compare it with the performance of conventional natural gas tank water heaters. The package contains a [Jupyter notebook with examples](https://github.com/LBNL-ETA/MSWH/blob/master/scripts/MSWH%20System%20Tool.ipynb), a GUI developed using Django Framework and both functional and unit tests. In addition, the package is structured so that it can be extended with further technologies, applications and locations as needed.

We use simplified fast performing energy balance based models. We connect the models into two preconfigured systems that are provided with MSWH:
* Solar thermal collector, hot water thermal storage tank, with a selection of backups: gas storage water heater, instantaneous gas water heater
* Photovoltaic panel, heat pump water heater hot water thermal storage tank, electric resistance water heater as backup

We built a simple simulation solver that uses explicit forward Euler method to solve the balance equations in each simulation time-step.

The component models we either identified in the existing literature and created a custom Python implementation, or we developed new models. In our implementation we create custom implementation of the following existing or new models:
* Solar irradiation on a tilted surface model is based on [ref duffy beckman]
* Solar collector models and model parameters are based on [ref SRCC] and [ASHRAE]
* We convert natural gas tank water heater model with the methodology published in [ref WHAM] into a hourly time-step model in our implementation
* Photovoltaic model based on a simplified model found in [modelica builings library]
* Heat pump water heater tank was modeled based on [ref NREL]
* Solar thermal tank is a phenomenology based model that relies on [ref NREL SAM]
* simplified performance data based gas burner model to represent instantaneous gas water heater
* simple electric resistance model to represent instantaneous electric gas
water heater
* simplified data based solar and distribution pump model
* to model the distribution piping network we developed a simplified model that is capable of accounting for thermal losses at stagnation and flows on demand with correction factors available to help account for the long time-step of 1h.

When using the models the user needs to provide a climate zone for a project, an occupancy for each household and whether any of the occupants stay at home during the day. The software can then load a set of example California specific hourly domestic hot water end-use load profiles from a database that we developed, size and locate the systems. The user can now simulate the hourly system performance over a period of one representative year, visualize and explore the simulation results using time-series plots for temperature profiles, heat and power rates, or look at annual summaries. Similarly the user can model individual household solar water heating projects and base case conventional gas tank water heater systems, such that the results can be compared between the individual, community and base case systems.

The application of the models can be to explore the benefits of grouping multiple households to be served by a single solar water heating system in comparison to a system installed in a single household. An another application of the model is to calculate gas savings when changing from a gas water heater to a solar water heater in a single household.

More on the hot water demand model, solar radiation, component and system models can be found in [ref Report]. The simulation models were also used in [ACEEE ref] and [Hannes theses ref].

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
