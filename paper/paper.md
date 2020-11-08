---
title: 'Multiscale Solar Water Heating'
tags:
  - Python
  - system
  - component
  - simulation
  - solar thermal water heating
  - solar electric water heating
  - heat pump water heating
  - natural gas water heating
  - photovoltaic
  - flat plate solar collector
  - evacuated tubes solar collector
  - hot water demand
  - solar radiation
  - thermal storage
  - solar water heating
  - sizing

authors:
  - name: Milica Grahovac^[corresponding author]
    affiliation: "1"
  - name: Katie Coughlin
    affiliation: "1"
  - name: Hannes Gerhart^[at the time of code creation was at affiliation 1 and 2, now is at affiliation 3]
    affiliation: "1, 2, 3"
  - name: Robert Hosbach
    affiliation: "1"

affiliations:
  - name: Lawrence Berkeley National Laboratory, Berkeley, CA
    index: 1
  - name: Technical University of Munich, Munich, Germany
    index: 2
  - name: Cloudflare, Inc.
    index: 3

date: September 7, 2020
bibliography: paper.bib
---


# Summary

The Multiscale Solar Water Heating (MSWH) is a software package to simulate individual and community scale solar water heating projects and allow for a comparison with the simulation performance of conventional natural gas tank water heaters. The package contains a [Jupyter notebook with examples](https://github.com/LBNL-ETA/MSWH/blob/master/scripts/MSWH%20System%20Tool.ipynb), a GUI (graphical user interface) developed using Django Framework and both functional and unit tests. In addition, the package is structured so that it can be extended with further technologies, applications and locations as needed.

We developed and implemented simplified fast performing energy balance based models. We connected the models into two preconfigured solar water heating systems that are provided with the MSWH software:

* Solar thermal collector, hot water thermal storage tank, with a selection of backups: gas storage water heater or an instantaneous gas water heater.
* Photovoltaic panel, heat pump tank water heater, with an electric resistance water heater as backup.

We built a simple simulation solver that uses explicit forward Euler method to solve the balance equations in each simulation time-step.

The component models were either developed from scratch or implemented in Python based on existing models identified in literature. We implemented the following existing or new models:

* Solar irradiation on a tilted surface model is based on equations found in @Duffie:2013.
* Solar collector models and model parameters are based on @Ashrae:2013 and @Srcc:2013.
* We converted natural gas tank water heater model from @Lutz:1998 into a hourly time-step model implementation.
* Photovoltaic model is based on a simplified model found in @Wetter:2014.
* Heat pump water heater tank is based on @Sparn:2014.
* Solar thermal tank is a phenomenological model based on ideas very similar to the model developed for NREL's SAM software [@Blair:2014].
* Simplified performance data based gas burner model was implemented to represent instantaneous gas water heater.
* Simple electric resistance model was implemented to represent instantaneous electric water heater.
* We developed a simplified data based solar and distribution pump model.
* To model the distribution piping network we developed a simplified model that is capable of accounting for thermal losses at stagnation and flows on demand with correction factors available to help account for the relatively long time-step of one hour.

We performed extensive validation of [component models](https://github.com/LBNL-ETA/MSWH/blob/master/mswh/system/tests/test_components.py) and [system models](https://github.com/LBNL-ETA/MSWH/blob/master/mswh/system/tests/test_models.py) against performance results obtained using freely available open source tools and certification data generated using commercial tools. The validation models are a part of the test suite and show good agreement in all test comparisons.

To evaluate a potential solar water heating project at design phase by looking at its simulation performance the user should create an instance of each system. For this, as is done in the detailed examples we provided in [example notebooks](https://github.com/LBNL-ETA/MSWH/tree/master/scripts), the user needs to specify the following:

* The project location by choosing one of the climate zones for which data is available in our database. The database includes 16 California climate zone files and can be extended for other regions.
* For each household: count of people supplied by the system and whether there is any daytime occupancy.

We developed component sizing rules and size scaling rules to account for household occupancy and project scale, respectively. The rules are readily available in the example notebooks and can easily be modified for exploratory purposes. For example, users who already have a solar water heating system and are planning to increase the occupancy, are retrofitting an existing system or already possess one of the components and are looking to appropriately size the others can simulate alternatives and compare their energy consumption and solar fraction results. As data sources for the sizing and scaling rules we used expert knowledge, web-scraped data with the help of a tool described in @Gerke:2017 and freely available certification databases such as @Ccms:2018 and @Cec_appliance:2019 as well as sizing rules available in @Csi_thermal:2016.

Performance visualization is available both in example notebooks and through the Django based GUI.

An application of the models can be to explore the benefits of grouping multiple households to be served by a single solar water heating system in comparison to a system installed in a single household. Another application of the model is to calculate gas savings when changing from a gas water heater to a solar water heater in a single household.

More details on the hot water demand model used in creating the database of sample hot water use load profiles are freely available with the software. The software's solar radiation, component and system models for conventional natural gas and solar thermal water heating can be found in the project report by @Coughlin:2020 for which this software was developed. The software found its application in performing the engineering analysis to estimate energy consumption and savings in the project report, as well as in @Grahovac:2020. @Gerhart:2019 explains in his master's thesis the development of the GUI that effectively is a flexible web framework custom built to facilitate easy addition of new system models if those are added to the MSWH software. @Gerhart:2019 also provides details on the solar electric system model development. The code is also available as DOE CODE, see @Doecode:2019.

Note that the weather data are currently limited to California and can be extended to other climate zones. An example climate zone outside of California was added for Banja Luka, Bosnia and Herzegovina. As the water consumption profiles are highly location specific and their development for additional climate zones would require new research efforts, a quick approximation may be made with caution by scaling the California profiles to match the location specific estimate of the average annual water use.

# Statement of Need

A project that prompted the development of this software is described in @Coughlin:2020. The project enquired whether, on the state level in California, there exist any economic benefits from grouping households to be served by one community-level solar water heating installation, in comparison to having a single solar water heating installation in each household.

Our primary motivation to develop a new software was the combination of the following factors:

* The level of detail
* The required simulation time
* Simplicity of integration within the larger life-cycle cost framework as presented in @Coughlin:2020 and @Grahovac:2020

Modelica buildings library by @Wetter:2014 satisfies and exceeds the level of detail but proves too detailed and thus slow for our particular application. SAM tool [@Blair:2014] has a good level of detail, provides most of the system models that we needed but for our purposes proves not flexible enough in terms of modifying the system configuration, automating the size scaling and embedding it into our custom life-cycle cost framework.

Namely, in order to capture a sufficient level of detail of the California demographics, such as variability in climate zones, household types, and household occupancy, we wanted to be able to simulate a few alternative water heating systems in each of the California sample households. Secondly, to get a more realistic picture of the effect of thermal storage and distribution system losses, we opted to perform a simulation with relatively short time-steps of 1 hour for a duration of one representative year. We were not able to identify an open source tool that is capable of firstly satisfying the simulation speed requirement combined with the necessary level of detail for our analysis and secondly providing the flexibility for us to customize various integral parts of the analysis such as automate the component and system size scaling, specify hot water load profiles and solar radiation for each household or group of households in the sample.

To satisfy our research need we thus opted to develop lightweight simulation models for all involved systems that would allow for around 120 thousand simulation runs together with the component sizing and life-cycle cost analysis to be performed on a computer with a 12-core processor in about 8 hours. The users can expect a single solar water heater simulation model to run for about 0.16 seconds, providing an almost instantaneous experience for a user only seeking to design and investigate a single system.

When it comes to future application of the MSWH software, we can envision three main groups of users:

* Researchers and policy developers
* Solar water heating planners, designers and contractors
* Homeowners
* Educators

If the features the existing MSWH software are sufficient for their application, the policy developers and researchers could utilize the existing MSWH software by embedding it into some larger analysis framework they construct such that it provides answers to their specific research questions. Should they have a need for additional system configurations and even additional components, the existing framework should be expanded in line with the structure made available to the user in the MSWH software. When systems are added following the structure of the existing systems, an addition of such new system to the GUI is made possible by using the flexible web framework. 

For those who in their professional life deal with planning, designing and contracting of the solar thermal water heating systems it might be useful to have an access to a freely available simulation tool that they can use to evaluate various system designs. The design parameters that such users can easily modify are household occupancies, climate zone, collector and tank sizes, component performance parameters such as insulation level of any thermal storage tanks, and types of solar collectors. The MSWH software relies on standard collector rating data readily available for most designs found on the market today. For each proposed design the MSWH software will output, among other, the solar fraction and the backup energy use on an annual level, the two variables allowing for a quick cross-comparison for the proposed designs.

Similarly to the previous category, the homeowners considering transitioning to a solar water heating system may be interested in doing the math before seeking further professional help, or just for their own education and curiosity about both solar water heating systems and system simulation in general. 

Often simulation tools are largely inaccessible to non-technical users both in terms of usage and the ability to understanding the underlying codebase. With a combination of code, example notebooks and GUI the MSWH software provides a unique insight in what actually happens in a relatively simple mezzo-level simulation model.

# Acknowledgements

This work was supported by the California Energy Commission, Public Interest Energy Research Program, under Contract No. PIR-16-022. We thank Vagelis Vossos and Mohan Ganeshalingam for their contributions and support.

# References
