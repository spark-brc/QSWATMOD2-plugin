# <img src="./imgs/icon.png" style="float" width="60" align="center"> &nbsp; QSWATMOD2

#### :exclamation: ***Note:*** `QSWATMOD2 is compatible with QGIS3.`

[QSWATMOD](https://swat.tamu.edu/software/swat-modflow/) is a QGIS-based graphical user interface that facilitates linking SWAT and MODFLOW, running SWAT-MODFLOW simulations, and viewing results.  

This repository contains source codes and an executable for the new version of QSWATMOD.
All other materials: example dataset and tutorial document can be downloaded from the old version of QSWATMOD repository.
- **[Installer](https://github.com/spark-brc/QSWATMOD2/tree/master/Installer):** QSWATMOD 2.0.exe
- **[Inputs](https://github.com/spark-brc/QSWATMOD2/tree/master/Inputs):** ExampleDataset.zip
- **[Source Code](https://github.com/spark-brc/QSWATMOD2/tree/master/QSWATMOD2)**
- **[Tutorial Document](https://github.com/spark-brc/qswatmod/blob/master/QSWATMOD%20Tutorial.pdf)**

-----
# Installation
The QGIS3 software must be installed on the system prior to the installation of QSWATMOD2. We've tested QSWATMOD2 with the "latest release" (3.12.2) and  “long term release (LTR)” (3.10.4 ~ 3.10.5) versions of QGIS3.

- Install one of the versions of QGIS. It can be downloaded from https://qgis.org/en/site/forusers/download.html.
- Download [the QSWATMOD installer](https://github.com/spark-brc/QSWATMOD2/blob/master/Installer) and install it by running QSWATMOD 2.0.exe or a later version. The QSWATMOD2 is installed into the user's home directory *(~\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\QSWATMOD2)*, which we will refer to as the QSWATMOD2 plugin directory.

<p align="center">
    <img src="./imgs/fig_01.png" width="200" align="center">
</p>
<p align="center">
    <img src="./imgs/fig_02.png" width="500">
</p>

QSWATMOD2 includes all dependencies directly in the plugin to avoid user-installation.  
- Open QGIS3 after the installation of QSWATMOD2 is finished.

If you don't see QSWAMOD2 icon on the toolbar,
- Go to Plugins menu and open Manage and Install Plugins
<p align="center">
    <img src="./imgs/fig_03.png" width="700">
</p>

- Click the installed tab and check QSWATMOD2 box to activate the plugin.
<p align="center">
    <img src="./imgs/fig_04.png" width="450">

Now, you will see the QSWATMOD2 icon on the toolbar.
<p align="center">
    <img src="./imgs/fig_05.png" width="300">
</p>

<br>

# New features added to QSWATMOD2

There are two additional features in QSWATMOD2.
- ### Add or subtract rows and columns  
    The "Create grid" algorithm in QGIS uses a given extent, not the numbers of row and column. Thus, it occasionally creates more number of colum or row, or less number of them.
    Once a MODFLOW grid is created, first check the numbers of column and row by labeling 'col' or 'row' on the 'mf_grid' layer. <br>
    For example, I want to create 700 by 700m MODFLOW grid with the given subbasin extent (**same as MODFLOW option 2** in linking process) and it results in one column short on the MODFLOW grid.
    <p align="center">
        <img src="./imgs/fig_06.png" width="1200">
    </p>

- ### Threshold setting on DHRU size

    During the linking process, some watersheds might generate a number of very small sizes of DHRUs (overlapping sizes on MODFLOW grid) compared to their HRUs. Although their sizes are small and those DRHUs pass small amounts of deep percolation to the MODFLOW domain they can slow down the linkage and simulation speed of a huge and complicated SWAT-MODFLOW model.
    <br>
    
    The threshold setting on DRHU size option has been tested with the example data set. We tested several threshold settings on DHRU size using full DHRUs (no threshold), > 9000, > 30000, > 60000, and > 125000 m<sup>2</sup>. The following figures show differences from different threshold settings and a proper threshold setting on DHRU size might speed up the linking process and its simulation without lossing any information (deep percolation rate).

    <br>
    <p align="center">
        <img src="./imgs/fig_07.png" width="1200">
    </p>

<br>
<br>

In addition, [documentation and the SWAT-MODFLOW executable](https://swat.tamu.edu/software/swat-modflow/) are available as downloads. QSWATMOD and SWAT-MODFLOW have been tested in several watersheds. However, no warranty is given that either the model or tool is completely error-free. If you encounter problems with the model, tool or have suggestions for improvement, please comment at [the SWAT-MODFLOW Google group](https://groups.google.com/forum/?hl=en#!forum/swat-modflow) or [QSWATMOD github](https://github.com/spark-brc/qswatmod/issues).

A publication documenting QSWATMOD and an example application can be found here:  
[https://doi.org/10.1016/j.envsoft.2018.10.017](https://doi.org/10.1016/j.envsoft.2018.10.017)

# References
[Bailey, R.T., Wible, T.C., Arabi, M., Records, R.M. and Ditty, J., 2016. Assessing regional‐scale spatio‐temporal patterns of groundwater–surface water interactions using a coupled SWAT‐MODFLOW model. Hydrological processes, 30(23), pp.4420-4433, https://doi.org/10.1002/hyp.10933.](https://onlinelibrary.wiley.com/doi/abs/10.1002/hyp.10933)

[Bakker, M., Post, V., Langevin, C. D., Hughes, J. D., White, J. T., Starn, J. J. and Fienen, M. N., 2016, Scripting MODFLOW Model Development Using Python and FloPy: Groundwater, v. 54, p. 733–739, doi:10.1111/gwat.12413.](https://ngwa.onlinelibrary.wiley.com/doi/full/10.1111/gwat.12413)