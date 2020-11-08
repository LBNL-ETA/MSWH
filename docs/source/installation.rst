.. _sec_pkg_ins:

Package Installation
--------------------

Most users will be able to install the MSWH Python package by following the 
`Setup and Installation and Simple Installation Using Conda <https://github.com/LBNL-ETA/MSWH#setup-and-installation>`_ 
section of the README.md file that is displayed at the landing page of the MSWH repository. Please use those instructions
as the primary approach to MSWH package installation.

The set of instructions presented here is intended for technical users that are relatively new to virtual environments 
or Python in general, for users who encountered issues with the 
simple installation instructions available in the `README.md <https://github.com/LBNL-ETA/MSWH>`_ file, or any other 
users looking for a reminder on some of the installation steps. These instructions also show to the users how to 
utilize an alternative Python package management system, `venv <https://docs.python.org/3.8/library/venv.html>`_.

Please make sure to install ``pip`` and, in case you are not using ``venv``, ``conda`` as instructed 
in `Setup and Installation on the readme file <https://github.com/LBNL-ETA/MSWH#setup-and-installation>`_.

Here are the detailed steps to install the `MSWH Python package <https://github.com/LBNL-ETA/MSWH>`_:

#. Since the repo comes with database files, please download, install and see the documentation for `git large file storage <https://git-lfs.github.com/>`_.

#. It is recommended to create a new ``Python`` environment in order to avoid interference with the system-wide Python installation, 
   for example by using `conda <(https://docs.conda.io/en/latest/>`_ or `venv <https://docs.python.org/3.8/library/venv.html>`_. 
   Depending on the approach you take, pick one of the commands below and run it in a terminal to create a new environment named, for instance, ``mswh``.

    If you use ``conda`` from the repo clone folder run:

    .. code-block:: console

        conda create -n mswh python=3.8

    If you use ``venv``, for example on ``Linux``:

    .. code-block:: console

        python3.8 -m venv <path_to_env>/mswh

    With ``<path_to_env>`` as your selected folder path to store virtual
    environments.

#. Now the virtual environment needs to be activated, by running one of the following commands:

    When using ``Anaconda`` or ``Miniconda``:

    .. code-block:: console

        conda activate mswh

    When using ``venv``:

    .. code-block:: console

        source <path_to_env>/mswh/bin/activate

    After having activated the virtual environment, the name of it should appear before the prompt in the terminal.

    For deactivating use:
    
    .. code-block:: console
    
        conda deactivate

#. To make use of example ``Jupyter notebooks`` one should have `JupyterLab <https://jupyter.org/install>`_ installed. 
   To ensure the same Python kernel can be used in a ``Jupyter notebook``, activate the virtual environment and run:

    .. code-block:: console
        
        python -m ipykernel install --user --name mswh

   Users with admin privileges can skip the ``--user`` flag.

   If you have any issues with plots not being displayed when running the example notebooks,
   please install the following:

    .. code-block:: console

        jupyter labextension install jupyterlab-plotly

#. Clone the repository with:
    
    .. code-block:: console
        
        git clone https://github.com/LBNL-ETA/MSWH.git

#.  To install the necessary Python packages navigate to the ``setup.py`` directory and run:

    .. code-block:: console
        
        pip install -e .

    The ``-e`` flag is only necessary if one would like changes to the source code be reflected immediately 
    (without having to rerun the ``setup.py`` script with every change to the source code). 
    If you just want to run the project application, you can omit the ``-e`` flag.

#. To use the plotting capabilities, also required when running tests, please install `orca <https://github.com/plotly/orca>`_.
