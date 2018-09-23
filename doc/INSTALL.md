Installation
============

stcgal requires Python 3.2 (or later), pyserial 3.0 or later and
TQDM 4.0.0 or later. USB support is optional and requires pyusb
1.0.0b2 or later. You can run stcgal directly with the included
```stcgal.py``` script if the dependencies are already installed.

There are several options for permanent installation:

* Use Python3 and ```pip```. Run ```pip3 install stcgal``` to
install the latest release of stcgal globally on your system.
This may require administrator/root permissions for write access
to system directories.

* Use setuptools. Run ```./setup.py build``` to build and
```sudo ./setup.py install``` to install stcgal.
