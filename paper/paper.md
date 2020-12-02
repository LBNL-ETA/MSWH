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
  - name: Hannes Gerhart^[At the time of code creation was at affiliation 1 and 2]
    affiliation: "1, 2"
  - name: Robert Hosbach
    affiliation: "1"

affiliations:
  - name: Lawrence Berkeley National Laboratory, Berkeley, CA, USA
    index: 1
  - name: Technical University of Munich, Munich, Germany
    index: 2

date: September 7, 2020
bibliography: paper.bib
---


# Summary

The Multiscale Solar Water Heating (MSWH) package simulates individual and community scale solar water heating projects and allows for a comparison with the simulation performance of conventional natural gas tank water heaters (WH). The package contains a [Jupyter notebook with examples](https://github.com/LBNL-ETA/MSWH/blob/v2.0.0/scripts/MSWH%20System%20Tool.ipynb), a [graphical user interface (GUI) developed using Django Framework](https://github.com/LBNL-ETA/MSWH/tree/v2.0.0/web) and both functional and unit tests. System performance time series visualizations are available both in example notebooks and through the GUI, either spun off locally or [using a web deployed version](https://solar.floweragenda.org/).

The package was developed in the scope of a California Energy Commission (CEC) funded project looking at costs and benefits of using community versus individual scale solar thermal water heating systems. The database included in the MSWH software focuses primarily on California-specific hot water use profiles and climate data, but can structurally accommodate any further climate zones. The scale refers to the number of households served by a single system. Therefore, one can apply the models to explore the benefits of grouping multiple households to be served by a single solar water heating system in comparison to a system installed in a single household. Another example application of the models is to enable calculation of gas savings when switching from a gas WH to a solar WH in a single household.

The preconfigured system simulation models provided in the package include base-case gas tank WH and the following solar WH configurations with solar storage tanks:

* Solar thermal collector WH with either a tankless or a tank gas WH backup.
* Solar electric photovoltaic WH with a heat pump storage tank and an electric resistance backup.

[This documentation page](https://lbnl-eta.github.io/MSWH/source/models.html#approach-to-component-and-system-modeling-and-simulation) provides more details about the implemented models, the modeling approach, and the references used in some of the model development.

To evaluate a solar water heating project at the design phase by looking at its simulation performance the user should create a system instance for each compared system. This is described in detail in our [example notebooks](https://github.com/LBNL-ETA/MSWH/tree/v2.0.0/scripts). The user needs to specify the following:

* The project location by choosing one of the climate zones for which data is available in our database. The database includes 16 California climate zones and can be extended to other regions.
* For each household: count of people supplied by the system and whether there is any daytime household occupancy.

The MSWH software was used to perform the engineering analysis to estimate energy consumption and savings in the @Coughlin:2021 project report as well as in the @Grahovac:2020 research paper. @Gerhart:2019 published a master's thesis that explains the development of [the GUI](https://github.com/LBNL-ETA/MSWH/tree/v2.0.0/web) and how to effectively utilized it as a flexible web framework custom-built to facilitate easy addition of new MSWH software system models.

The MSWH software is both accessible to a user and functionally robust. We performed extensive validation of [component models](https://github.com/LBNL-ETA/MSWH/blob/v2.0.0/mswh/system/tests/test_components.py) and [system models](https://github.com/LBNL-ETA/MSWH/blob/v2.0.0/mswh/system/tests/test_models.py) against performance results obtained using freely available open source tools and certification data generated using commercial tools. The validation models are a part of the test suite and show good agreement in all test comparisons.

The package is structured so that it can be extended with further technologies, applications, and locations as needed. The weather data are currently mostly limited to California and can be extended to other climate zones. An example climate zone outside of California was added for Banja Luka, Bosnia and Herzegovina, through an [additional example Jupyter notebook](https://github.com/LBNL-ETA/MSWH/blob/v2.0.0/scripts/MSWH&#32;System&#32;Tool&#32;-&#32;Additional&#32;Climate.ipynb).

The code is available as DOE CODE, see @Doecode:2019.

# Statement of Need

A project that prompted the development of this software is described in @Coughlin:2021. The project enquired whether, on the state level in California, there exist any economic benefits from grouping households to be served by one community-level solar water heating installation, in comparison to having a single solar water heating installation in each household.

Our primary motivation to develop new software was the combination of the following needs:

* The level of detail sufficient to allow for an investigation of transient effects of thermal storage.
* The simulation time for a single system short enough to allow for over 100 thousand simulations to be performed on a personal computer within a reasonable amount of time, as this is how many we needed to be performed in a single state-level analysis run.
* Simplicity of integration within the larger life-cycle cost framework as presented in @Coughlin:2021 and @Grahovac:2020.

We developed lightweight models that allow for around 120,000 hourly annual system simulation runs, including component auto-sizing and life-cycle cost analysis to be performed on a computer with a 12-core processor in about 8 hours. The users can expect a single solar WH simulation to complete in less than 0.2 seconds.

The policy developers and researchers could utilize the existing MSWH software by embedding it into a larger analysis framework they construct such that it provides answers to their specific research questions. Solar thermal water heating system planners, designers, and contractors may find it useful to have access to a freely available simulation tool that they can use to evaluate various system designs. Homeowners considering transitioning to a solar water heating system may be interested in analyzing a hypothetical system before seeking professional assistance. Further  future use is elaborated in [this section of the code documentation](https://lbnl-eta.github.io/MSWH/source/models.html#future-applications-statement-of-need).

Simulation tools tend to be inaccessible to non-technical users. The MSWH software provides a unique insight into what actually happens in a relatively simple mezzo-level simulation model due to the use of readable Python code, while the example notebooks and the GUI allow for instant utilization of the models. These features also make the code suitable for educators.

# Acknowledgements

This work was supported by the California Energy Commission, Public Interest Energy Research Program, under Contract No. PIR-16-022. We thank Vagelis Vossos and Mohan Ganeshalingam for their contributions and support.

We dedicate this paper to Dino Kosić.

# References
