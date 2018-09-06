Installation
============

stcgal requires Python 3.2 (or later) and pySerial. USB support is
optional and requires pyusb 1.0.0b2 or later. You can run stcgal
directly with the included ```stcgal.py``` script if the dependencies
are already installed.

There are several options for permanent installation:

* Use Python3 and ```pip```. Run
```pip3 install git+https://github.com/grigorig/stcgal.git```
to install the latest version of stcgal globally on your system.
This may require administrator/root permissions for write access
to system directories.

* Use setuptools. Run ```./setup.py build``` to build and
```sudo ./setup.py install``` to install stcgal.
