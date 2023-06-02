文档说明 Explanation
------------------------
此文档翻译自USAGE.md

This document was translated from USAGE.md

最后修改时间：2020年6月8日

Last modified time: June 8, 2020

使用方法
=====

使用 ```-h``` 调用stcgal以获取使用信息。（'//'后面是翻译，实际使用过程中没有后面内容）

```
usage: stcgal [-h] [-e] [-a] [-A {dtr,rts}] [-r RESETCMD]
              [-P {stc89,stc12a,stc12b,stc12,stc15a,stc15,stc8,stc8d,stc8g,usb15,auto}]
              [-p PORT] [-b BAUD] [-l HANDSHAKE] [-o OPTION] [-t TRIM] [-D]
              [-V]
              [code_image] [eeprom_image]

stcgal 1.7 - an STC MCU ISP flash tool
(C) 2014-2018 Grigori Goronzy and others
https://github.com/grigorig/stcgal

positional arguments:
  code_image            code segment file to flash (BIN/HEX)      //代码段文件刷新
  eeprom_image          eeprom segment file to flash (BIN/HEX)    //EEPROM段文件刷新

optional arguments:
  -h, --help            show this help message and exit           //显示此帮助消息并退出
  -a, --autoreset       cycle power automatically by asserting DTR//断言DTR自动重启电源
  -A {dtr,rts}, --resetpin {dtr,rts}
                        pin to hold down when using --autoreset (default: DTR)
  -r RESETCMD, --resetcmd RESETCMD
                        shell command for board power-cycling (instead of DTR //用于板上电重启的shell命令（而不是DTR断言）
                        assertion)
  -P {stc89,stc12a,stc12b,stc12,stc15a,stc15,stc8,stc8d,stc8g,usb15,auto}, --protocol {stc89,stc12a,stc12b,stc12,stc15a,stc15,stc8,stc8d,stc8g,usb15,auto}
                        protocol version (default: auto)          //协议版本（芯片系列）（在默认状态为auto）
  -p PORT, --port PORT  serial port device                        //串口设备
  -b BAUD, --baud BAUD  transfer baud rate (default: 115200)      //传输波特率（默认值：115200）
  -l HANDSHAKE, --handshake HANDSHAKE
                        handshake baud rate (default: 2400)       //握手波特率（默认值：2400）
  -o OPTION, --option OPTION
                        set option (can be used multiple times, see//设置选项（可以多次使用，请参阅文档）
                        documentation)
  -t TRIM, --trim TRIM  RC oscillator frequency in kHz (STC15+ series only)//RC振荡器频率（kHz）（仅STC15 +系列）
  -D, --debug           enable debug output                         //启用调试输出
  -V, --version         print version info and exit                 //打印版本信息并退出
```

最重要的是， ```-p``` 设置用于编程的串行端口。

### 传输波特率

所有从 STC15 系列开始的 MCU 都支持默认值 115200 波特，至少是之前的 STC12C5A56S2。
对于较旧的 MCU，您可能必须使用 ```-b 19200``` 才能正确操作。

### 通讯协议与规定

STC MCU对BSL使用各种相关但不兼容的协议。协议可以用```-P``` 标志来指定。
默认情况下，使用UART协议自动检测。协议与MCU系列的对应关系如下：

* ```auto``` 自动检测基于UART的协议（默认）
* ```stc89``` STC89/90 系列 
* ```stc89a``` STC89/90 系列（BSL 7.2.5C）
* ```stc12a``` STC12x052 系列和其他类似系列
* ```stc12b``` STC12x52 系列, STC12x56 系列和其他类似系列
* ```stc12``` 多数 STC10/11/12 系列
* ```stc15a``` STC15x104E 和 STC15x204E(A) 系列
* ```stc15``` 多数 STC15 系列
* ```stc8``` STC8A8K64S4A12 和 STC8F 系列
* ```stc8d``` 所有 STC8 和 STC32 系列
* ```stc8g``` STC8G1 和 STC8H1 系列
* ```usb15``` 支持USB的STC15W4系列

doc / reverse-engineering子目录中的文本文件提供了BSL使用的反向工程协议的概述。
有关更多详细信息，请阅读源代码。

### 获取MCU信息

调用stcgal而不编写任何文件。它将转储有关MCU的信息，例如：（'//'后面是翻译，实际使用过程中没有后面内容）

```
$ ./stcgal.py -P stc15
Waiting for MCU, please cycle power: done   //等待MCU，请重启电源
Target model:
  Name: IAP15F2K61S2
  Magic: F449
  Code flash: 61.0 KB
  EEPROM flash: 0.0 KB
Target frequency: 10.046 MHz                //单片机频率
Target BSL version: 7.1S                    //单片机BSL版本
Target wakeup frequency: 34.771 KHz         //单片机唤醒频率
Target options:
  reset_pin_enabled=False                   //复位引脚启用状态
  clock_source=internal                     //时钟来源
  clock_gain=high                           
  watchdog_por_enabled=False                //看门狗状态
  watchdog_stop_idle=True
  watchdog_prescale=256                     //看门狗预分频系数
  low_voltage_reset=True                    //低电压复位
  low_voltage_threshold=3
  eeprom_lvd_inhibit=True
  eeprom_erase_enabled=False
  bsl_pindetect_enabled=False
  por_reset_delay=long
  rstout_por_state=high
  uart2_passthrough=False                   //串口2直通
  uart2_pin_mode=normal                     //串口2引脚模式
Disconnected!
```

如果识别失败,阅读[FAQ(chinese)](FAQ.md)

### 编程Flash闪存

stcgal支持Intel十六进制编码文件以及二进制文件。 
Intel HEX通过文件扩展名(. hex,. ihx 或者. ihex ) 自动测试。

像前面一样调用 stcgal，但提供代码映像的路径：

```
$ ./stcgal.py -P stc15 hello.hex
Waiting for MCU, please cycle power: done
Target model:
  Name: IAP15F2K61S2
  Magic: F449
  Code flash: 61.0 KB
  EEPROM flash: 0.0 KB
Target frequency: 10.046 MHz              //单片机频率
Target BSL version: 7.1S                  //单片机BSL版本
Target wakeup frequency: 34.771 KHz       //单片机唤醒频率
Target options:
  reset_pin_enabled=False                 //复位引脚启用状态
  clock_source=internal                   //时钟来源
  clock_gain=high
  watchdog_por_enabled=False              //看门狗状态
  watchdog_stop_idle=True
  watchdog_prescale=256                   //看门狗预分频系数
  low_voltage_reset=True                  //低电压复位
  low_voltage_threshold=3
  eeprom_lvd_inhibit=True
  eeprom_erase_enabled=False
  bsl_pindetect_enabled=False
  por_reset_delay=long
  rstout_por_state=high
  uart2_passthrough=False                 //串口2直通
  uart2_pin_mode=normal                   //串口2模式
Loading flash: 80 bytes (Intel HEX)
Trimming frequency: 10.046 MHz
Switching to 19200 baud: done
Erasing flash: done
Writing 256 bytes: .... done
Setting options: done
Target UID: 0D000021022632
Disconnected!
```

还可以编程存储器的EEPROM部分，。 将 Flash 图像路径添加到命令行后添加EEPROM图像路径。

stcgal默认使用 19200 bps的保守波特率。 可以通过标志```-b```选择更快的波特率来加快编程速度。

### 设备选项

stcgal转储了许多目标选项。 也可以修改这些。 在命令行上提供一个( 或者更多) `-o` 标志，后面跟一个 key-value 对来调整这些设置。 
例如你可以将外部晶体启用为时钟源：

```
$ ./stcgal.py -P stc15 -o clock_source=external hello.bin
```

请注意，设备选项只能在 Flash 内存被编程时设置 ！

#### 命令行选项键

并非所有部件都支持所有选项。 描述中列出了支持每个选项的协议或者部分。

选项密钥                       | 可能的值           | 协议/模型           | 描述
------------------------------|-------------------|---------------------|------------
```cpu_6t_enabled```          | true/false        | 仅STC89             | 6T快速模式
```bsl_pindetect_enabled```   | true/false        | 全部                | BSL仅在 p3。2/p3。3 或者 p1.0/p1.1 ( 取决于模型) 低时启用
```eeprom_erase_enabled```    | true/false        | 全部                | 使用下一个编程周期擦除 EEPROM
```clock_gain```              | low/high          | 所有带XTAL引脚       | 外部晶体的时钟增益
```ale_enabled```             | true/false        | 仅STC89             | 如果 true，正常 GPIO，如果 false，则启用ALE引脚
```xram_enabled```            | true/false        | 仅STC89             | 使用内部 XRAM ( 仅适用于 STC89 )
```watchdog_por_enabled```    | true/false        | 全部                | 复位复位后的看门狗状态( POR )
```low_voltage_reset```       | low/high          | STC12A/STC12        | 低电压复位级别( 低：~3.3V, 高： ~3.7V)
```low_voltage_reset```       | true/false        | STC12               | 启用RESET2引脚低压检测
```low_voltage_reset```       | true/false        | STC15A              | 启用低电压复位( brownout )
```clock_source```            | internal/external | 带XTAL的STC12A+     | 使用内部( RC ) 或者外部( 晶体) 时钟
```watchdog_stop_idle```      | true/false        | STC12A+             | 在空闲模式停止看门狗
```watchdog_prescale```       | 2,4,8,...,256     | STC12A+             | 看门狗定时器预分频器，必须是两个电源。
```reset_pin_enabled```       | true/false        | STC12+              | 如果 true，正常 GPIO，如果 false，则复位引脚
```oscillator_stable_delay``` | 4096,...,32768    | 仅STC11F系列         | 时钟中的晶体稳定延迟。 一定是 two。
```por_reset_delay```         | short/long        | STC12+              | 复位复位( POR ) 延迟
```low_voltage_threshold```   | 0...7             | STC15A+             | 低电压检测阈值。型号特定
```eeprom_lvd_inhibit```      | true/false        | STC15A+             | 在低电压情况下忽略EEPROM写入
```rstout_por_state```        | low/high          | STC15+              | 上电复位后的RSTOUT / RSTSV引脚状态
```uart1_remap```             | true/false        | STC8                | 通过UART1到UART2引脚( 用于单导线UART模式)
```uart2_passthrough```       | true/false        | STC15+              | 直通UART1至UART2引脚（用于单线UART模式）
```uart2_pin_mode```          | push-pull/normal  | STC15+              | UART2 TX引脚的输出模式
```cpu_core_voltage```        | low/mid/high      | STC15W+             | CPU核心电压( 低：~2.7V, mid: ~3.3V, 高：~3.6V)
```epwm_open_drain```         | true/false        | STC8                | 上电复位后，对EPWM引脚使用漏极开路引脚模式
```program_eeprom_split```    | 512 - 65024       | STC8A8 w/ 64 KB     | 选择代码闪存和EEPROM闪存之间的划分（以512字节块为单位）

### 频率微调

如果使用内部RC振荡器 (```clock_source=internal```),
stcgal可以执行修整过程以将其调整为给定值。 仅在STC15系列及更高版本中受支持。
调整值与设备选项一起存储。 使用 ```-t``` 标志请求对某个值进行修剪。 
通常可以实现4000到30000 kHz之间的频率。 如果修剪失败，stcgal将中止。

### 自动功率循环

STC的微控制器需要上电复位才能调用引导加载程序，这可能很不方便。
stcgal可以使用串行接口的DTR控制信号来自动执行此操作。
当通过```-a```用自动复位功能时，DTR信号有效约500 ms。
这需要外部电路来实际切换电源。
在某些情况下，当微控制器仅消耗很少的功率时，就有可能直接从DTR信号提供功率。

作为DTR的替代方法，可以使用定制的shell命令或外部脚本（通过-r选项）来重置设备。
您应将命令与```-a```选项一起指定。不要忘了引号 ！

例如:

```
  $ ./stcgal.py -P stc15 -a -r "echo 1 > /sys/class/gpio/gpio666/value"
```
或者

```
  $ ./stcgal.py -P stc15 -a -r "./powercycle.sh"
```

### 退出状态

如果在执行stcgal时没有发生错误，则退出状态为 0.。
任何错误( 如协议错误或者 I/O 错误) 都会导致退出状态 1。
如果用户按ctrl键中止 stcgal，则会导致退出状态为 2.

### USB支持

STC15W4系列具有一个基于USB的BSL，可以选择性的使用它。 
stcgal中的USB支持是实验性的，将来可能会改变。 
USB模式是通过使用“ usb15”协议启用的。 
USB协议会忽略端口（```-p```）标志以及波特率选项。同时不支持RC频率调整。
