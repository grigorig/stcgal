文档说明 Explanation
------------------------
此文档翻译自INSTALL.md

This document was translated from INSTALL.md

最后修改时间：2020年6月8日

Last modified time: June 8, 2020

安装说明
============

stcgal需要Python 3.2（或更高版本），pyserial 3.0或更高版本以及TQDM 4.0.0或更高版本。 
USB支持是可选的，并且需要pyusb 1.0.0b2或更高版本。如果已经安装了依赖项，则可以使用包含的
```stcgal.py``` 脚本直接运行stcgal。

永久安装有几种选择：

* 使用Python3和```pip```。运行```pip3 install stcgal```
在系统上全局安装最新版本的stcgal。
这可能需要管理员/ root用户权限才能进行写到系统目录。

* 使用setuptools。运行`./setup.py build`来构建，并运行'sudo ./setup.py install`'来安装stcgal。
