Frequently Asked Questions
==========================

### Is it possible to read code (or EEPROM) memory out of a chip?

By design, this is not possible with STC's bootloader protocols. This is considered a security feature by STC. There is no known workaround at this time. See issue #7 for more details and discussion.

### Which serial interfaces have been tested with stcgal?

stcgal should work fine with common 16550 compatible UARTs that are traditionally available on many platforms. However, nowadays, USB-based UARTs are the typical case. The following USB-based UART interface chips have been successfully tested with stcgal:

* FT232 family (OS: Linux, Windows)
* CH340/CH341 (OS: Windows, Linux requires Kernel 4.10)
* PL2303 (OS: Windows, Linux)
* CP2102 (OS: Windows, Linux, macOS)

Interfaces that are known to not work:

* Raspberry Pi Mini UART (lacks parity support, enable the PL011 UART instead)

In general, stcgal requires accurate baud rate timings and parity support.

### stcgal fails to start with the error `module 'serial' has no attribute 'PARITY_NONE'` or similar

There is a module name conflict between the PyPI package 'serial' (a data serialization library) and the PyPI package 'pyserial' (the serial port access library needed by stcgal). You have to uninstall the 'serial' package (`pip3 uninstall serial`) and reinstall 'pyserial' (`pip3 install --force-reinstall pyserial`) to fix this. There is no other known solution at the moment.

### stcgal fails to recognize the MCU and is stuck at "Waiting for MCU"

There are a number of issues that can result in this symptom:

* Electrical issues and wrong connections. Make sure that RX/TX, GND and VCC are connected correctly. If you do not use the autoreset feature, also make sure to connect power only after stcgal starts, as the bootloader is only invoked on power-on reset.
* Parasitic powering through I/O pins. The MCU can be powered through I/O pins (such as RX/TX) even if VCC is not connected. In this case, the power-on reset logic does not work. See next question.
* Serial interface incompatibilities. Some USB-based UARTs have bad compatibility with STC MCUs for various reasons. You can try to lower the handshake baudrate from the standard 2400 baud to 1200 baud with the option `-l 1200`, which works around these issues in some cases.

### How can I avoid parasitic powering?

Various remedies are possible to avoid parasitic powering.

* You can try to connect a resistor (< 1k) between MCU VCC and GND to short-circuit injected power and hopefully drop the voltage below the brown-out value.
* Another option is to insert series resistor on I/O lines that might inject power. Try a value like 1k on the RX/TX lines, for instance.
* Yet another possibility is to switch GND instead of VCC. This should be a fairly reliable solution in most cases.

### RC frequency trimming fails

First, make sure that the frequency specified uses the correct unit. The frequency is specified in kHz and the safe range is approximately 5000 kHz - 30000 kHz. Furthermore, frequency trimming uses the UART clock as the clock reference, so UART incompatibilities or clock inaccuracies can also result in issues with frequency trimming. If possible, try another UART chip.

### Baud rate switching fails or flash programming fails

This can especially happen at high programming baud rates, e.g. 115200 baud. Try a lower baudrate, or stick to the default of 19200 baud. Some USB UARTs are known to cause problems due to inaccurate timing as well, which can lead to various issues.

### How can I use the autoreset feature?

The standard autoreset feature works somewhat similarly to Arduino. DTR is an active low signal, and is asserted on startup of stcgal for 500 ms and then deasserted for the rest of the programming sequence. On a standard USB UART, this results in 500 ms low pulse, followed by a high phase. The stcgal author recommends the following circuit:

```
VCC --o      o-- MCU GND
      |      |
     .-.     |
     | | 1k  |
     | |     |
     '_'     |
      |      |
      |   ||-+
DTR --o --||<- BS170/BSS138
          ||-| (N-CH MOSFET)
             |
             |
GND ---------o
```

This circuit uses an N-channel MOSFET as a low-side switch to switch the MCU's GND. VCC is directly connected. This avoids parasitic powering issues. The pull-up resistor ensures that the MCU is switched on when the DTR input is floating.

