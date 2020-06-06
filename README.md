[![Build Status](https://travis-ci.org/grigorig/stcgal.svg)](https://travis-ci.org/grigorig/stcgal)
[![Coverage Status](https://coveralls.io/repos/github/grigorig/stcgal/badge.svg?branch=coveralls)](https://coveralls.io/github/grigorig/stcgal?branch=coveralls)
[![PyPI version](https://badge.fury.io/py/stcgal.svg)](https://badge.fury.io/py/stcgal)

stcgal - STC MCU ISP flash tool
===============================

stcgal is a command line flash programming tool for [STC MCU Ltd](http://stcmcu.com/).
8051 compatible microcontrollers.

  stcgal是用于[STC MCU Ltd]的命令行闪存编程工具。
  兼容8051微控制器。

STC microcontrollers have an UART/USB based boot strap loader (BSL). It
utilizes a packet-based protocol to flash the code memory and IAP
memory over a serial link. This is referred to as in-system programming
(ISP).  The BSL is also used to configure various (fuse-like) device
options. Unfortunately, this protocol is not publicly documented and
STC only provide a (crude) Windows GUI application for programming.

  STC微控制器具有基于UART / USB的引导加载程序（BSL）。
  它采用系统内编程，即基于数据包的协议通过串行链路刷新代码存储器和IAP存储器。
  BSL还用于配置各种设备选项。
  不幸的是，该协议没有公开记录，STC仅提供（粗略的）Windows GUI应用程序进行编程

stcgal is a full-featured Open Source replacement for STC's Windows
software; it supports a wide range of MCUs, it is very portable and
suitable for automation.

  stcgal是STC的Windows软件的功能全面的开源替代品。
  它支持多种MCU，非常便携，适合自动下载。

Features    特点
--------

* Support for STC 89/90/10/11/12/15/8 series                        
    支持STC 89/90/10/11/12/15/8系列
* UART and USB BSL support                                          
    UART和USB BSL支持
* Display part info                                                 
    显示信息
* Determine operating frequency                                     
    确定工作频率
* Program flash memory                                              
    程序闪存
* Program IAP/EEPROM                                                
    程序IAP / EEPROM
* Set device options                                                
    设置设备选项
* Read unique device ID (STC 10/11/12/15/8)                         
    读取唯一的设备ID（STC 10/11/12/15/8）
* Trim RC oscillator frequency (STC 15/8)                           
    设置RC振荡器频率（STC 15/8）
* Automatic power-cycling with DTR toggle or a custom shell command 
    自动电源（使用DTR切换或自定义Shell命令循环）
* Automatic UART protocol detection                                 
    自动UART协议检测

Quickstart    快速开始
----------

Install stcgal (might need root/administrator privileges):安装stcgal（可能需要root /管理员权限）
    
    pip3 install stcgal

Call stcgal and show usage:呼叫stcgal并显示的用法

    stcgal -h

Further information    更多的信息
-------------------

[Installation](doc/INSTALL.md)

[How to use stcgal](doc/USAGE.md)

[Frequently Asked Questions](doc/FAQ.md)

[List of tested MCU models](doc/MODELS.md)

License
-------

stcgal is published under the MIT license.
