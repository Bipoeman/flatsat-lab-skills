# Hardware Mapping & Multi-Board Flashing Guide

## 1. Multi-Probe ST-Link Identification
When multiple STM32 Nucleo/Discovery boards are plugged into the host via USB, standard Arduino IDE / `arduino-cli upload` fails because `STM32_Programmer_CLI` cannot decide which probe to flash.

To solve this:
1. Probe all connected ST-Link serial numbers:
   ```bash
   /Applications/STMicroelectronics/STM32Cube/STM32CubeProgrammer/STM32CubeProgrammer.app/Contents/Resources/bin/STM32_Programmer_CLI -c port=SWD
   ```
2. Identify target MCU Device ID for each probe:
   ```bash
   STM32_Programmer_CLI -c port=SWD sn=<PROBE_SN>
   ```
   Common FlatSat Device IDs:
   - `0x419` -> STM32F429ZI (High-performance OBC / MCU with large flash & RAM)
   - `0x431` -> STM32F411RE (COMMS / Radio Controller)
   - `0x414` -> STM32F103RC (Ground Station / Telemetry Node)

3. Record the mapping into `connections.json`:
   ```json
   {
     "OBC": {
       "port": "/dev/cu.usbmodem11402",
       "sn": "0674FF505372485067084036",
       "mcu": "STM32F429ZI",
       "fqbn": "STMicroelectronics:stm32:GenF4:pnum=GENERIC_F429ZITX"
     },
     "COMMS": {
       "port": "/dev/cu.usbmodem11302",
       "sn": "066CFF505372485067084037",
       "mcu": "STM32F411RE",
       "fqbn": "STMicroelectronics:stm32:GenF4:pnum=GENERIC_F411RETX"
     },
     "GroundStation": {
       "port": "/dev/cu.usbmodem102",
       "sn": "066DFF495375485067021847",
       "mcu": "STM32F103RC",
       "fqbn": "STMicroelectronics:stm32:GenF1:pnum=GENERIC_F103RCTX"
     }
   }
   ```

## 2. Compilation and Flashing Procedure
1. **Compile with Generic FQBN**:
   ```bash
   arduino-cli compile --fqbn <FQBN> <SketchDir> --output-dir build/<BoardName>
   ```
2. **Flash Specific Board via Serial Number**:
   ```bash
   STM32_Programmer_CLI -c port=SWD sn=<PROBE_SN> -w build/<BoardName>/<SketchName>.ino.bin 0x08000000 -v -rst
   ```
   `-rst` ensures the microcontroller performs a clean hardware reset and begins executing firmware immediately.

