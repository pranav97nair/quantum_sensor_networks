# quantum_sensor_networks
Code used to simulate multi-party computations with networks of quantum sensors during my internship at LIP6, Paris in 2025.

This repository includes Python code and data files used for implementing various simulation tasks during my project, as well as various
simulation results. Each sub-directory is independent, so they can be downloaded and tested individually.

Before running the code in any of the sub-directories, you will need to install the Netsquid package by creating an account and 
following the instructions at https://forum.netsquid.org/

After this you will need to download the squidasm directory included in this project, or to ensure you have the latest version follow
the instructions at https://squidasm.readthedocs.io/en/latest/installation.html

The general layout of each sub-directory is as follows:\n
/ : Application files defining various node programs and executables for various simulations\n
/qia_params : Contains network configuration data files with latest parameter values for various network noise profiles from QIA
/data : Contains .txt files with numerical results from the simulations
/plotting : Contains python files for plotting the simulation results 
/figures : Contains plots of the simulation results made in matplotlib
/logs : Contains simulation log files


