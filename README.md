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
* Program flash memory
* Program IAP/EEPROM
* Set device options
* Read unique device ID (STC 10/11/12/15)
* Trim RC oscillator frequency (STC 15)

Installation
------------

stcgal requires Python 3.2 (or later) and pySerial. Apart from that,
no particular installation is required.

Usage
-----

See ```stcgal.py -h``` for usage information.

### Protocols

STC MCUs use a variety of related but incompatible protocols for the
BSL. The protocol must be specified with the ```-p``` flag. Here's
the general mapping between protocols and MCU series:

*   ```stc89```
    STC 89/90 series

*   ```stc12a```
    STC12Cx052AD and possibly others

*   ```stc12```
    Most STC10/11/12 series

*   ```stc15a```
    STC15x104E and STC15x204E(A) series

*   ```stc15```
    Most STC15 series

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
Target frequency: 11.054 MHz
Target BSL version: 7.1S
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
  power_on_reset_delay=long
  rstout_por_state=high
  uart_passthrough=False
  uart_pin_mode=normal
Disconnected!
```

### Program the flash memory

Please note that stcgal only handles raw binary encoded files at this
point. You can easily convert common Intel HEX files with
```objcopy -I ihex -O binary input.hex output.bin```.

Call stcgal just like before, but provide the path to the code binary:

```
$ ./stcgal.py -P stc15 hello.bin
Waiting for MCU, please cycle power: done
Target model:
  Name: IAP15F2K61S2
  Magic: F449
  Code flash: 61.0 KB
  EEPROM flash: 0.0 KB
Target frequency: 11.054 MHz
Target BSL version: 7.1S
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
  power_on_reset_delay=long
  rstout_por_state=high
  uart_passthrough=False
  uart_pin_mode=normal
Trimming frequency: 11.104 MHz
Switching to 19200 baud: done
Erasing flash: done
Writing 256 bytes: .... done
Setting options: done
Target UID: 0D000021022632
Disconnected!
```

You can also program the EEPROM part of the memory, if applicable. Add
the EEPROM image to the commandline after the code binary.

stcgal uses a conservative baud rate of 19200 bps by
default. Programming can be sped up by choosing a faster baud rate
with the flag ```-b```.

### Device options

stcgal dumps a number of target options. These can be modified as
well. Provide one (or more) ```-o``` flags followed by a key-value
pair on the commandline to adjust these settings.

Detailed documentation for the settings is not available yet. Please
refer to STC-ISP and the datasheets.

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
