# Multiscale Solar Water Heating
**Solar water heating system modeling and simulation for individual and community scale projects**

## Repository Content

Folder | Content
------ | ------
[mswh](mswh) | Python module to calculate solar irradiation on a tilted surface ([mswh/system/source_and_sink.py](mswh/system/source_and_sink.py)) <br><br> Python module with simplified component models ([mswh/system/components.py](mswh/system/components.py)) for Converter (solar collectors, electric resistance heater, gas burner, photovoltaic panels, heat pump), Storage (solar thermal tank, heat pump thermal tank, conventional gas tank water heater), and Distribution (distribution and solar pump, piping losses) components <br><br> Python module with preconfigured system simulation models ([mswh/system/models.py](mswh/system/models.py)) for: base case gas tank water heaters, solar thermal water heaters (solar collector feeding a storage tank, with a tankeless gas water heater backup in a new installation cases and a base case gas tank water heater in a retrofit case) and solar electric water heaters (heat pump storage tank with an electric resistance backup) <br><br> Database with component performance parameters, California specific weather data and domestic hot water end-use load profiles ([mswh/comm/swh_system_input.db](mswh/comm/swh_system_input.db)) <br><br> Modules to communicate with the database ([mswh/comm/sql.py](mswh/comm/sql.py)), unit conversion and plotting modules in [mswh/tools](mswh/tools)
[scripts](scripts) | Jupyter notebooks with preconfigured models and any side analysis if applicable
[web](web) | Django web framework to configure project, parametrize components and run simulation from a web browser
[docs](docs) | Sphinx documentation. To build html or latex use `make html` or `make latex`

## Usage

The fastest way to explore the preset simulations is to use the [`Project Level SWH System Tool`](scripts/Project&#32;Level&#32;SWH&#32;System&#32;Tool.ipynb) notebook. In the notebook the user provides a climate zone for a project, an occupancy for each household and whether any of the occupants stay at home during the day. The notebook can then load a set of example California specific hourly domestic hot water end-use load profiles from a database, size and locate the systems. The user can now simulate the hourly system performance over a period of one representative year, visualize and explore the simulation results using time-series plots for temperature profiles, heat and power rates, or look at annual summaries. Similarly the user can model individual household solar water heating projects and base case conventional gas tank water heater systems, such that the results can be compared between the individual, community and base case systems. All simulation and sizing parameters are exposed in the notebook and the user can easily change them if needed.

If you opt to use the web framework the shortest path to explore the simulaton results after [setting up a local server](#django-web-framework-deployment) is to:

* Click on `Configurations` on the landing page
* Click on `Simulate` for any of the example preconfigured systems (`Solar Thermal New` or `Solar Electric`). This leads the user to a visualization page with hourly timeseries results for a representative year. 
* Play with sizes and performance parameters of preconfigured components.

To add new system types (such as `Solar Thermal Retrofit`) one would need to map it through the backend analogously to the preconfigured systems.

## Setup and Installation

1. Download this repository with:

        git clone https://github.com/LBNL-ETA/MSWH.git

     Since the repo comes with database files, please download, install [`git large file storage`](https://git-lfs.github.com/) and set up respective hooks with:

        git lfs install

2. It is recommended to create a new Python environment in order to avoid interference with the system-wide Python installation, for example by using `virtualenv` (see [here](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/)) or `Anaconda` (see [here](https://docs.anaconda.com/anaconda/install/)). After having installed one of the mentioned tools, run one of the following commands in the terminal to create a new environment (with the name `mswh`).

    When using `Anaconda` (the environment is stored under the home directory in `~/anaconda3/envs/`):

          conda create -n mswh python=3.6

    When using `virtualenv` (the environment is stored in `<path_to_env>`). The environment will simply use the system Python3 subversion:

          (on Linux) python3 -m virtualenv <path_to_env>/mswh,
                     or with a specific python version: virtualenv -p /usr/bin/python3.6 <path_to_env>/mswh

          (on MacOS) python3 -m venv <path_to_env>/mswh

     To ensure the same python kernel can be used in a jupyter notebook:

          python -m ipykernel install --name mswh

3. Now the virtual environment needs to be activated, by running one of the following commands:

    When using `virtualenv` (on Linux or Mac):

        source <path_to_env>/mswh/bin/activate

    When using `virtualenv` (on Windows):

        <path_to_env>\Scripts\activate.bat

    When using `Anaconda`:

        conda activate mswh

    When using `virtualenv`:

        source <path_to_env>/mswh/bin/activate

    After having activated the virtual environment, the name of it should appear before the prompt in the terminal.

    For deactivating use `conda deactivate` or `deactivate`.

4.  To install the necessary Python packages navigate to the `setup.py` directory and run:

        pip install -e .

    The `-e` flag is only necessary if one would like changes to the source code be reflected immediately (without having to rerun the `setup.py` script with every change to the source code). If you just want to run the project application, you can omit the `-e` flag.

## Django Web Framework Deployment

1. If the installation succeeded, to run the Django application navigate to the `web` folder (there should be a `manage.py` file) and start the development server on your local machine with:

        python manage.py runserver

   Now you can open your browser and type in `localhost:8000` (or `127.0.0.1:8000` if you are on a Windows machine) to start the web interface.

   Note that to build python extensions one needs to have `python3.x-dev` installed.

2. To deploy publicly create a file `local_settings.py` and store it in the same directory as the `settings.py`. Then add a constant called `SECRET_KEY = '<random_string>'`. The random string should be 50 characters long and can created (on Linux) by using the following command as super user:

        </dev/urandom tr -dc '1234567890!#$?*#-.,+qwertyuiopQWERTYUIOPasdfghjklASDFGHJKLzxcvbnmZXCVBNM' | head -c50; echo ""

    An example for a good secret key is this:

    `SECRET_KEY = 'O&2aYmv%)0B5#U-'9qsLTpfItC9N*V?%3L#fOHxDO,zyUm*S,U'`

## Contributing

Anyone may contribute features with the appropriate tests using the issue tracker, forks and pull requests. Please 
check out [code documentation](https://lbnl-eta.github.io/MSWH/) for guidance.

To run tests:

    python -m unittest swh.{my_module}.tests.{test_my_module}.{MyModuleTests}.{test_my_method}

## Publications

The code was used for the following publications:
* CEC Report (link will be posted upon publishing)
* Master Thesis (link will be posted upon publishing)

## About

The software may be distributed under the copyright and license provided in [legal.md](legal.md).

Milica Grahovac, Robert Hosbach, Katie Coughlin, Mohan Ganeshalingam and Hannes Gerhart created the contents of this repo
in the scope of the CEC "Costs and Benefits of Community vs. Individual End-Use Infrastructure for Solar Water Heating" project.
