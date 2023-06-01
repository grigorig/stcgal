文档说明 Explanation
-------------------
此文档翻译自README.MD

This document was translated from README.MD

最后修改时间：2020年6月8日

Last modified time: June 8, 2020


stcgal - 用于STC MCU的ISP闪存工具
===============================

stcgal是用于[STC MCU Ltd]的命令行闪存编程工具。
兼容8051微控制器。


STC微控制器具有基于UART / USB的引导加载程序（BSL）。
它采用系统内编程，即基于数据包的协议通过串行链路刷新代码存储器和IAP存储器。
BSL还用于配置各种设备选项。
不幸的是，该协议没有公开记录，STC仅提供（粗略的）Windows GUI应用程序进行编程


stcgal是STC的Windows软件的功能全面的开源替代品。
它支持多种MCU，非常便携，适合自动下载。

特点
--------

* 支持STC 89/90/10/11/12/15/8/32系列
* UART和USB BSL支持
* 显示信息
* 确定工作频率
* 程序闪存
* 程序IAP / EEPROM
* 设置设备选项
* 读取唯一的设备ID（STC 10/11/12/15/8）
* 设置RC振荡器频率（STC 15/8）
* 自动电源（使用DTR切换或自定义Shell命令循环）
* 自动UART协议检测

快速开始
----------

安装stcgal（可能需要root /管理员权限）：
    
    pip3 install stcgal

呼叫stcgal并显示的用法：

    stcgal -h

更多的信息
-------------------

[安装方法](doc/zh_CN/INSTALL.md)

[如何取使用](doc/zh_CN/USAGE.md)

[常见问题](doc/zh_CN/FAQ.md)

[支持的MCU型号](doc/zh_CN/MODELS.md)

执照
-------

stcgal是根据MIT许可发布的。
