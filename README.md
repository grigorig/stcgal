stcgal - STC MCU ISP flash tool
===============================

stcgal is a command line flash programming tool for STC MCU Ltd. [1]
8051 compatible microcontrollers. The name was inspired by avrdude [2].

STC microcontrollers have an UART/USB based boot strap loader (BSL). It
utilizes a packet-based protocol to flash the code memory and IAP
memory over a serial link. This is referred to as in-system programming
(ISP).  The BSL is also used to configure various (fuse-like) device
options. Unfortunately, this protocol is not publicly documented and
STC only provide a (crude) Windows GUI application for programming.

stcgal is a full-featured Open Source replacement for STC's Windows
software; it supports a wide range of MCUs, it is very portable and
suitable for automation.

[1] http://stcmcu.com/
[2] http://www.nongnu.org/avrdude/

Supported MCU models
--------------------

stcgal should fully support STC 89/90/10/11/12/15 series MCUs.

So far, stcgal was tested with the following MCU models:

* STC89C52RC (BSL version: 4.3C/6.6C)
* STC90C52RC (BSL version: 4.3C)
* STC89C54RD+ (BSL version: 4.3C)
* STC12C2052 (BSL version: 5.8D)
* STC12C2052AD (BSL version: 5.8D)
* STC12C5608AD (BSL version: 6.0G)
* STC12C5A16S2 (BSL version: 6.2I)
* STC12C5A60S2 (BSL version: 6.2I/7.1I)
* STC11F02E (BSL version: 6.5K)
* STC10F04XE (BSL version: 6.5J)
* STC11F08XE (BSL version: 6.5M)
* STC12C5204AD (BSL version: 6.6H)
* STC15F104E (BSL version: 6.7Q)
* STC15F204EA (BSL version: 6.7R)
* STC15L104W (BSL version: 7.1.4Q)
* STC15F104W (BSL version: 7.1.4Q)
* IAP15F2K61S2 (BSL version: 7.1.4S)
* STC15L2K16S2 (BSL version: 7.2.4S)
* STC15W408AS (BSL version: 7.2.4T)
* STC15W4K56S4 (BSL version: 7.3.4T, UART and USB mode)

Compatibility reports, both negative and positive, are welcome.

Features
--------

* UART and USB BSL support
* Display part info
* Determine operating frequency
* Program flash memory
* Program IAP/EEPROM
* Set device options
* Read unique device ID (STC 10/11/12/15)
* Trim RC oscillator frequency (STC 15)
* Automatic power-cycling with DTR toggle
* Automatic UART protocol detection

Installation
------------

stcgal requires Python 3.2 (or later) and pySerial. USB support is
optional and requires pyusb 1.0.0b2 or later. You can run stcgal
directly with the included ```stcgal.py``` script. The recommended
method for permanent installation is to use Python's setuptools. Run
```./setup.py build``` to build and ```sudo ./setup.py install```
to install stcgal. A permanent installation provides the ```stcgal```
command.

Usage
-----

Call stcgal with ```-h``` for usage information.

```
usage: stcgal.py [-h] [-a] [-P {stc89,stc12a,stc12,stc15a,stc15,auto}]
                 [-p PORT] [-b BAUD] [-l HANDSHAKE] [-o OPTION] [-t TRIM] [-D]
                 [code_image] [eeprom_image]

stcgal 1.0 - an STC MCU ISP flash tool
(C) 2014-2015 Grigori Goronzy
https://github.com/grigorig/stcgal

positional arguments:
  code_image            code segment file to flash (BIN/HEX)
  eeprom_image          eeprom segment file to flash (BIN/HEX)

optional arguments:
  -h, --help            show this help message and exit
  -a, --autoreset       cycle power automatically by asserting DTR
  -P {stc89,stc12a,stc12,stc15a,stc15,auto}, --protocol {stc89,stc12a,stc12,stc15a,stc15,auto}
                        protocol version
  -p PORT, --port PORT  serial port device
  -b BAUD, --baud BAUD  transfer baud rate (default: 19200)
  -l HANDSHAKE, --handshake HANDSHAKE
                        handshake baud rate (default: 2400)
  -o OPTION, --option OPTION
                        set option (can be used multiple times)
  -t TRIM, --trim TRIM  RC oscillator frequency in kHz (STC15 series only)
  -D, --debug           enable debug output
```

Most importantly, ```-p``` sets the serial port to be used for programming.

### Protocols

STC MCUs use a variety of related but incompatible protocols for the
BSL. The protocol can be specified with the ```-P``` flag. By default
UART protocol autodetection is used. The mapping between protocols
and MCU series is as follows:

* ```stc89``` STC89/90 series
* ```stc12a``` STC12x052 series and possibly others
* ```stc12b``` STC12x52 series, STC12x56 series and possibly others
* ```stc12``` Most STC10/11/12 series
* ```stc15a``` STC15x104E and STC15x204E(A) series
* ```stc15``` Most STC15 series
* ```usb15``` USB support on STC15W4 series
* ```auto``` Automatic detection of UART based protocols (default)

The text files in the doc/ subdirectory provide an overview over
the reverse engineered protocols used by the BSLs. For more details,
please read the source code.

### Getting MCU information

Call stcgal without any file to program. It will dump information
about the MCU, e.g.:

```
$ ./stcgal.py -P stc15
Waiting for MCU, please cycle power: done
Target model:
  Name: IAP15F2K61S2
  Magic: F449
  Code flash: 61.0 KB
  EEPROM flash: 0.0 KB
Target frequency: 10.046 MHz
Target BSL version: 7.1S
Target wakeup frequency: 34.771 KHz
Target options:
  reset_pin_enabled=False
  clock_source=internal
  clock_gain=high
  watchdog_por_enabled=False
  watchdog_stop_idle=True
  watchdog_prescale=256
  low_voltage_reset=True
  low_voltage_threshold=3
  eeprom_lvd_inhibit=True
  eeprom_erase_enabled=False
  bsl_pindetect_enabled=False
  por_reset_delay=long
  rstout_por_state=high
  uart2_passthrough=False
  uart2_pin_mode=normal
Disconnected!
```

### Program the flash memory

stcgal supports Intel HEX encoded files as well as binary files. Intel
HEX is autodetected by file extension (.hex, .ihx or .ihex).

Call stcgal just like before, but provide the path to the code image:

```
$ ./stcgal.py -P stc15 hello.hex
Waiting for MCU, please cycle power: done
Target model:
  Name: IAP15F2K61S2
  Magic: F449
  Code flash: 61.0 KB
  EEPROM flash: 0.0 KB
Target frequency: 10.046 MHz
Target BSL version: 7.1S
Target wakeup frequency: 34.771 KHz
Target options:
  reset_pin_enabled=False
  clock_source=internal
  clock_gain=high
  watchdog_por_enabled=False
  watchdog_stop_idle=True
  watchdog_prescale=256
  low_voltage_reset=True
  low_voltage_threshold=3
  eeprom_lvd_inhibit=True
  eeprom_erase_enabled=False
  bsl_pindetect_enabled=False
  por_reset_delay=long
  rstout_por_state=high
  uart2_passthrough=False
  uart2_pin_mode=normal
Loading flash: 80 bytes (Intel HEX)
Trimming frequency: 10.046 MHz
Switching to 19200 baud: done
Erasing flash: done
Writing 256 bytes: .... done
Setting options: done
Target UID: 0D000021022632
Disconnected!
```

You can also program the EEPROM part of the memory, if applicable. Add
the EEPROM image path to the commandline after the flash image path.

stcgal uses a conservative baud rate of 19200 bps by
default. Programming can be sped up by choosing a faster baud rate
with the flag ```-b```.

### Device options

stcgal dumps a number of target options. These can be modified as
well. Provide one (or more) ```-o``` flags followed by a key-value
pair on the commandline to adjust these settings. For instance, you can
enable the external crystal as clock source:

```
$ ./stcgal.py -P stc15 -o clock_source=external hello.bin
```

Please note that device options can only be set when flash memory is
programmed!

#### Option keys

Not all parts support all options. The protocols or parts that support each option are listed in the description.

Option key                    | Possible values   | Protocols/Models    | Description
------------------------------|-------------------|---------------------|------------
```cpu_6t_enabled```          | true/false        | STC89 only          | 6T fast mode
```bsl_pindetect_enabled```   | true/false        | All                 | BSL only enabled when P3.2/P3.3 or P1.0/P1.1 (depends on model) are low
```eeprom_erase_enabled```    | true/false        | All                 | Erase EEPROM with next programming cycle
```clock_gain```              | low/high          | All with XTAL pins  | Clock gain for external crystal
```ale_enabled```             | true/false        | STC89 only          | ALE pin enabled if true, normal GPIO if false
```xram_enabled```            | true/false        | STC89 only          | Use internal XRAM (STC89 only)
```watchdog_por_enabled```    | true/false        | All                 | Watchdog state after power-on reset (POR)
```low_voltage_reset```       | low/high          | STC12A/STC12        | Low-voltage reset level (low: ~3.3V, high: ~3.7V)
```low_voltage_reset```       | true/false        | STC12               | Enable RESET2 pin low voltage detect
```low_voltage_reset```       | true/false        | STC15A              | Enable low-voltage reset (brownout)
```clock_source```            | internal/external | STC12A+ with XTAL   | Use internal (RC) or external (crystal) clock
```watchdog_stop_idle```      | true/false        | STC12A+             | Stop watchdog in IDLE mode
```watchdog_prescale```       | 2,4,8,...,256     | STC12A+             | Watchdog timer prescaler, must be a power of two.
```reset_pin_enabled```       | true/false        | STC12+              | RESET pin enabled if true, normal GPIO if false
```oscillator_stable_delay``` | 4096,...,32768    | STC11F series only  | Crystal stabilization delay in clocks. Must be a power of two.
```por_reset_delay```         | short/long        | STC12+              | Power-on reset (POR) delay
```low_voltage_threshold```   | 0...7             | STC15A+             | Low-voltage detection threshold. Model specific.
```eeprom_lvd_inhibit```      | true/false        | STC15A+             | Ignore EEPROM writes in low-voltage situations
```rstout_por_state```        | low/high          | STC15+              | RSTOUT pin state after power-on reset
```uart2_passthrough```       | true/false        | STC15+              | Pass-through UART1 to UART2 pins (for single-wire UART mode)
```uart2_pin_mode```          | push-pull/normal  | STC15+              | Output mode of UART2 TX pin
```cpu_core_voltage```        | low/mid/high      | STC15W+             | CPU core voltage (low: ~2.7V, mid: ~3.3V, high: ~3.6V)

### Frequency trimming

If the internal RC oscillator is used (```clock_source=internal```),
stcgal can execute a trim procedure to adjust it to a given value. This
is only supported by STC15 series. The trim values are stored with
device options. Use the ```-t``` flag to request trimming to a certain
value. Generally, frequencies between 4 and 35 MHz can be achieved. If
trimming fails, stcgal will abort.

### Automatic power-cycling

STC's microcontrollers require a power-on reset to invoke the bootloader,
which can be inconvenient. stcgal can use the DTR control signal of a
serial interface to automate this. The DTR signal is asserted for
approximately 500 ms when the autoreset feature is enabled with the
```-a``` flag. This requires external circuitry to actually switch the
power. In some cases, when the microcontroller draws only little power,
it is possible to directly supply power from the DTR signal, however.

### Exit status

The exit status is 0 if no error occured while executing stcgal. Any
error, such as a protocol error or I/O error, results in an exit
status of 1. If the the user aborted stcgal by pressing CTRL-C,
that results in an exit status of 2.

### USB support

STC15W4 series have an USB-based BSL that can be optionally
used. USB support in stcgal is experimental and might change in the
future. USB mode is enabled by using the ```usb15``` protocol. The
port (```-p```) flag as well as the baudrate options are ignored for
the USB protocol. RC frequency trimming is not supported.

License
-------

stcgal is published under the MIT license.
