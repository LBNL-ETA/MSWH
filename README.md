# Multiscale Solar Water Heating
**Solar water heating system modeling and simulation for individual and community scale projects**

## Repository Content

Folder | Content
------ | ------
[mswh](mswh) | Python module to calculate solar irradiation on a tilted surface ([mswh/system/source_and_sink.py](mswh/system/source_and_sink.py)) <br><br> Python module with simplified component models ([mswh/system/components.py](mswh/system/components.py)) for Converter (solar collectors, electric resistance heater, gas burner, photovoltaic panels, heat pump), Storage (solar thermal tank, heat pump thermal tank, conventional gas tank water heater), and Distribution (distribution and solar pump, piping losses) components <br><br> Python module with preconfigured system simulation models ([mswh/system/models.py](mswh/system/models.py)) for: base case gas tank water heaters, solar thermal water heaters (solar collector feeding a storage tank, with a tankless gas water heater backup in a new installation cases and a base case gas tank water heater in a retrofit case) and solar electric water heaters (heat pump storage tank with an electric resistance backup) <br><br> Database with component performance parameters, California specific weather data and domestic hot water end-use load profiles ([mswh/comm/swh_system_input.db](mswh/comm/mswh_system_input.db)) <br><br> Modules to communicate with the database ([mswh/comm/sql.py](mswh/comm/sql.py)), unit conversion and plotting modules in [mswh/tools](mswh/tools)
[scripts](scripts) | Jupyter notebooks with preconfigured models and any side analysis if applicable
[web](web) | Django web framework to configure project, parametrize components and run simulation from a web browser
[docs](docs) | [Sphinx documentation](https://lbnl-eta.github.io/MSWH/). To build HTML or LaTeX use `make html` or `make latex`

## Statement of Need

We envision four main groups of users for the MSWH software:

* Researchers and policy developers.
* Solar water heating planners, designers and contractors.
* Homeowners.
* Educators.

The policy developers and researchers could utilize the existing MSWH software by embedding it into some larger analysis framework they construct such that it provides answers to their specific research questions.

The professional planners, designers, and contractors of solar thermal water heating systems might find it useful to have access to a freely available simulation tool such as the MSWH software, that they can use to evaluate alternative system designs.

Homeowners considering transitioning to a solar water heating system may be interested in doing the math before seeking further professional help, or just for their own education and curiosity about both solar water heating systems and system simulation in general.

Educators may wish and find it useful to utilize the MSWH simulation tool in the classroom when teaching the basics of energy simulation.

## Usage

The fastest way to explore the preset simulations is to use the [`MSWH System Tool`](scripts/MSWH&#32;System&#32;Tool.ipynb) notebook. In the notebook the user provides a climate zone for a project, an occupancy for each household and whether any of the occupants stay at home during the day. The notebook can then load a set of example California specific hourly domestic hot water end-use load profiles from a database, size and locate the systems. The user can now simulate the hourly system performance over a period of one representative year, visualize and explore the simulation results using time-series plots for temperature profiles, heat and power rates, or look at annual summaries. Similarly the user can model individual household solar water heating projects and base case conventional gas tank water heater systems, such that the results can be compared between the individual, community and base case systems. All simulation and sizing parameters are exposed in the notebook and the user can easily change them if needed.

If you opt to use the web framework the shortest path to explore the simulaton results after [setting up a local server](#django-web-framework-deployment) is to:

* Click on `Configurations` on the landing page.
* Click on `Simulate` for any of the example preconfigured systems (`Solar Thermal New` or `Solar Electric`). This leads the user to a visualization page with hourly timeseries results for a representative year.
* Play with sizes and performance parameters of preconfigured components.

To configure new system types in the web framework (such as `Solar Thermal Retrofit`) one would need to map it through the backend analogously to the currently preconfigured systems.

An example demonstrating usage of the simulation models for an additional climate outside 
of California, that is Banja Luka in Bosnia & Herzegovina, is provided in [this notebook](scripts/MSWH&#32;System&#32;Tool&#32;-&#32;Additional&#32;Climate.ipynb).

## Setup and Installation

1. Make sure that `pip` [is installed](https://pip.pypa.io/en/stable/installing/).
   
2. Unless you already have [`conda`](https://docs.conda.io/en/latest/) installed, please install the lightweight option [`Miniconda`](https://docs.conda.io/en/latest/miniconda.html) or [`Anaconda`](https://docs.anaconda.com/anaconda/install/) software.

### Simple Installation Using `Conda`

1. If you are familiar with `conda` and experienced with virtual environments
 you can perform the package installation using the following set of commands:

        conda create -n mswh -c conda-forge -c plotly python=3.8 pip git-lfs jupyterlab plotly-orca
        conda activate mswh
        git lfs install
        git clone https://github.com/LBNL-ETA/MSWH.git
        cd MSWH
        pip install -e .

    To ensure functionality of the example notebooks install the following:

        python -m ipykernel install --user --name mswh
        jupyter labextension install jupyterlab-plotly

The examples are best explored using `JupyterLab`. Please check out the
[JupyterLab documentation](https://jupyterlab.readthedocs.io/en/latest/)
for further help as needed.

### Detailed Installation Steps

If for any reason a user encounters difficulties with the simple installation 
instructions, the user is encouraged to consult a [more detailed installation guide that is 
posted with the code documentation](https://lbnl-eta.github.io/MSWH/source/installation.html).

## Django Web Framework Deployment

1. If the installation succeeded, to run the Django application navigate to the `web` folder (there should be a `manage.py` file) and start the development server on your local machine with:

        python manage.py runserver

   Now you can open your browser and type in `localhost:8000` (or `127.0.0.1:8000` if you are on a Windows machine) to start the web interface.

   Note that to build Python extensions one needs to have `python3.x-dev` installed.

2. To deploy publicly create a file `local_settings.py` and store it in the same directory as the `settings.py`. Then add a constant called `SECRET_KEY = '<random_string>'`. The random string should be 50 characters long and can be  created (on Linux) by using the following command as super user:

        </dev/urandom tr -dc '1234567890!#$?*#-.,+qwertyuiopQWERTYUIOPasdfghjklASDFGHJKLzxcvbnmZXCVBNM' | head -c50; echo ""

    An example for a good secret key is this:

    `SECRET_KEY = 'O&2aYmv%)0B5#U-'9qsLTpfItC9N*V?%3L#fOHxDO,zyUm*S,U'`
    
## Contributing

All are invited to contribute to the MSWH software through following the [Guidelines for Contributors](contributing.md).

### Automated tests

To run tests, from the `MSWH` folder use the following command modified according to the test module and method you intend to run:

    python -m unittest mswh.{my_module}.tests.{test_my_module}.{MyModuleTests}.{test_my_method}

## Publications

The code was used for the following publications:
* CEC report (in press)
* [ACEEE paper and video presentation](https://aceee2020.conferencespot.org/event-data/pdf/catalyst_activity_10923/catalyst_activity_paper_20200812133157248_498ce455_3a9c_4278_9088_6e3fdce5745b)

* Hannes' Master Thesis (in press)

## About

The software may be distributed under the copyright and a BSD license provided in [legal.md](legal.md).

Milica Grahovac, Robert Hosbach, Katie Coughlin, Mohan Ganeshalingam and Hannes Gerhart created the contents of this repo
in the scope of the CEC "Costs and Benefits of Community vs. Individual End-Use Infrastructure for Solar Water Heating" project.

To cite use format provided at the [DOE CODE](https://www.osti.gov/doecode/biblio/26000) MSWH record.

## Acknowledgements

This work was supported by the California Energy Commission, Public Interest Energy Research Program, under Contract No. PIR-16-022.

We thank the reviewers and the editor of [The Journal of Open Source Software (JOSS)](https://joss.theoj.org/), [Bryn Pickering](@brynpickering), [Nithiya Streethran](@nmstreethran), and [Stefan Pfenninger](@sjpfenninger) for their contributions in improving the code, the examples and the code documentation for the code release 2.0.0.

