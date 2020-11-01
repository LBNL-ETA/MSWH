
Most users should be able to install the package by following the 
`Setup and Installation and Simple Installation Using Conda <https://github.com/LBNL-ETA/MSWH#setup-and-installation>`_ 
section of the MSWH repo `README` file. 

The set of instructions presented here are intended for 
technical users that are relatively new to virtual environments or `Python` in general, or for users who had any issues with the 
simple installation instructions available in the `README` file. Here we also show to the users how to utilize an alternative 
package management system in `Python`, [`venv`](https://docs.python.org/3.8/library/venv.html).

Please make sure to install `pip` and, in case you are not using `venv`, `conda` as instructed 
in `Setup and Installation on the readme file <https://github.com/LBNL-ETA/MSWH#setup-and-installation>`_.

Here are the detailed steps to install the `MSWH Python package <https://github.com/LBNL-ETA/MSWH>`_:

1. Since the repo comes with database files, please download, install and see the documentation for [`git large file storage`](https://git-lfs.github.com/).

2. It is recommended to create a new `Python` environment in order to avoid interference with the system-wide Python installation, for example by using [`conda`](https://docs.conda.io/en/latest/) or [`venv`](https://docs.python.org/3.8/library/venv.html). Depending on the approach you take, pick one of the commands below and run it in a terminal to create a new environment named, for instance, `mswh`.

    If you use `conda` from the repo clone folder run:

        conda create -n mswh python=3.8

    If you use `venv`, for example on `Linux`:

        python3.8 -m venv <path_to_env>/mswh

    With ``<path_to_env>`` as your selected folder path to store virtual
    environments.

3. Now the virtual environment needs to be activated, by running one of the following commands:

    When using `Anaconda` or `Miniconda`:

        conda activate mswh

    When using `venv`:

        source <path_to_env>/mswh/bin/activate

    After having activated the virtual environment, the name of it should appear before the prompt in the terminal.

    For deactivating use `conda deactivate` or `deactivate`.

4. To make use of example `Jupyter notebooks` one should have [`JupyterLab`](https://jupyter.org/install) installed. To ensure the same Python kernel can be used in a `Jupyter notebook`, activate the virtual environment and run:

        python -m ipykernel install --user --name mswh

   Users with admin privileges can skip the `--user` flag.

   If you have any issues with plots not being displayed when running the example notebooks,
   please install the following:

        jupyter labextension install jupyterlab-plotly

5. Clone the repository with:

        git clone https://github.com/LBNL-ETA/MSWH.git

6.  To install the necessary Python packages navigate to the `setup.py` directory and run:

        pip install -e .

    The `-e` flag is only necessary if one would like changes to the source code be reflected immediately (without having to rerun the `setup.py` script with every change to the source code). If you just want to run the project application, you can omit the `-e` flag.

7. To use the plotting capabilities, also required when running tests, please install [`orca`](https://github.com/plotly/orca).

