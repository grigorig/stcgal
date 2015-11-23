stcgal - STC MCU flash tool
===========================

stcgal is a command line flash programming tool for STC MCU Ltd. [1]
8051 compatible microcontrollers. The name was inspired by avrdude [2].

STC microcontrollers have a UART based boot strap loader (BSL). It
utilizes a packet-based protocol to flash the code memory and IAP
memory. The BSL is also used to configure various (fuse-like) device
options. Unfortunately, this protocol is not publicly documented and
STC only provide a (crude) Windows GUI application for programming.

stcgal is a full-featured replacement for STC's Windows software;
it is very portable and suitable for automation.

[1] http://stcmcu.com/
[2] http://www.nongnu.org/avrdude/

Supported MCU models
--------------------

stcgal should fully support STC 89/90/10/11/12/15 series MCUs.

So far, stcgal was tested with the following MCU models:

* STC89C52RC (BSL version: 4.3C)
* STC12C2052AD (BSL version: 5.8D)
* STC12C5A60S2 (BSL version: 6.2I)
* STC11F08XE (BSL version: 6.5M)
* STC15F104E (BSL version: 6.7Q)
* STC15F204EA (BSL version: 6.7R)
* STC15L104W (BSL version: 7.1Q)
* IAP15F2K61S2 (BSL version: 7.1S)

More compatibility testing is going to happen soon.

Features
--------

* Display part info
* Determine operating frequency
* Program flash memory
* Program IAP/EEPROM
* Set device options
* Read unique device ID (STC 10/11/12/15)
* Trim RC oscillator frequency (STC 15)

Installation
------------

stcgal requires Python 3.2 (or later) and pySerial. You can run stcgal
directly with the included ```stcgal.py``` script. The recommended
method for permanent installation is to use Python's setuptools. Run
```./setup.py build``` to build and ```sudo ./setup.py install```
to install stcgal.

Usage
-----

See ```stcgal.py -h``` for usage information.

```
$ ./stcgal.py -h
usage: stcgal.py [-h] [-P {stc89,stc12a,stc12,stc15a,stc15}] [-p PORT]
                 [-b BAUD] [-l HANDSHAKE] [-o OPTION] [-t TRIM] [-D]
                 [code_binary] [eeprom_binary]

stcgal - an STC MCU ISP flash tool

positional arguments:
  code_binary           code segment binary file to flash
  eeprom_binary         eeprom segment binary file to flash

optional arguments:
  -h, --help            show this help message and exit
  -P {stc89,stc12a,stc12,stc15a,stc15}, --protocol {stc89,stc12a,stc12,stc15a,stc15}
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
BSL. The protocol must be specified with the ```-P``` flag. Here's
the general mapping between protocols and MCU series:

* ```stc89``` STC 89/90 series
* ```stc12a``` STC12Cx052AD and possibly others
* ```stc12``` Most STC10/11/12 series
* ```stc15a``` STC15x104E and STC15x204E(A) series
* ```stc15``` Most STC15 series

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
```

### Program the flash memory

stcgal supports Intel HEX encoded files as well as binary files. Intel
HEX is autodetected by file extension (.hex, .ihx or .ihex).

Call stcgal just like before, but provide the path to the code binary:

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
the EEPROM binary to the commandline after the code binary.

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

Option key                    | Possible values   | Description
------------------------------|-------------------|------------
```cpu_6t_enabled```          | true/false        | 6T fast mode (STC89 only)
```bsl_pindetect_enabled```   | true/false        | BSL only enabled when P3.2/P3.3 or P1.0/P1.1 (depends on model) are low
```eeprom_erase_enabled```    | true/false        | Erase EEPROM with next programming cycle
```clock_gain```              | low/high          | Clock gain for external crystal
```ale_enabled```             | true/false        | ALE pin enabled if true, normal GPIO if false (STC89 only)
```xram_enabled```            | true/false        | Use internal XRAM (STC89 only)
```watchdog_por_enabled```    | true/false        | Watchdog after power-on reset (POR)
```low_voltage_detect```      | true/false        | Low-voltage detection (brownout) (STC12A+)
```clock_source```            | internal/external | Use internal (RC) or external (crystal) clock (STC12A+, not on all models)
```watchdog_stop_idle```      | true/false        | Stop watchdog in IDLE mode (STC12A+)
```watchdog_prescale```       | 2,4,8,...,256     | Watchdog timer prescaler. Must be a power of two. (STC12A+)
```reset_pin_enabled```       | true/false        | RESET pin enabled if true, normal GPIO if false (STC12+)
```oscillator_stable_delay``` | 4096,...,32768    | Crystal stabilization delay in clocks. Must be a power of two. (STC11F series only)
```por_reset_delay```         | short/long        | Power-on reset (POR) delay (STC12+)
```low_voltage_threshold```   | 0...7             | Low-voltage detection threshold. Model specific. (STC15A+)
```eeprom_lvd_inhibit```      | true/false        | Ignore EEPROM writes in low-voltage situations (STC15A+)
```rstout_por_state```        | low/high          | RSTOUT pin state after power-on reset (STC15)
```uart2_passthrough```       | true/false        | Pass-through UART1 to UART2 pins (for single-wire UART mode) (STC15)
```uart2_pin_mode```          | push-pull/normal  | Output mode of UART2 TX pin (STC15)

### Frequency trimming

If the internal RC oscillator is used (```clock_source=internal```),
stcgal can execute a trim procedure to adjust it to a given value. This
is only supported by STC15 series. The trim values are stored with
device options. Use the ```-t``` flag to request trimming to a certain
value. Generally, frequencies between 4 and 35 MHz can be achieved. If
trimming fails, stcgal will abort.

License
-------

stcgal is published under the MIT license.
