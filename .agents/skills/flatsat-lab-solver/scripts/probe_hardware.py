#!/usr/bin/env python3
"""
Hardware probe utility for FlatSat labs.
Detects connected ST-Link probes, queries target MCU device IDs,
matches them to active serial ports, and outputs/updates connections.json.
"""

import os
import sys
import glob
import json
import subprocess
import re

PROGRAMMER_PATHS = [
    "/Applications/STMicroelectronics/STM32Cube/STM32CubeProgrammer/STM32CubeProgrammer.app/Contents/Resources/bin/STM32_Programmer_CLI",
    "STM32_Programmer_CLI",
]

MCU_DEVICE_ID_MAP = {
    "0x419": {"mcu": "STM32F429ZI", "family": "GenF4", "fqbn": "STMicroelectronics:stm32:GenF4:pnum=GENERIC_F429ZITX"},
    "0x431": {"mcu": "STM32F411RE", "family": "GenF4", "fqbn": "STMicroelectronics:stm32:GenF4:pnum=GENERIC_F411RETX"},
    "0x414": {"mcu": "STM32F103RC", "family": "GenF1", "fqbn": "STMicroelectronics:stm32:GenF1:pnum=GENERIC_F103RCTX"},
}

def find_programmer_cli():
    for p in PROGRAMMER_PATHS:
        if os.path.exists(p):
            return p
        # Check in PATH
        try:
            res = subprocess.run(["which", p], capture_output=True, text=True)
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
    return None

def get_serial_ports():
    ports = glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
    return sorted(ports)

def probe_stlink_probes(cli_path):
    # Query all probes
    cmd = [cli_path, "-c", "port=SWD"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = res.stdout + res.stderr
    
    # Extract ST-Link SNs
    sns = []
    for line in out.splitlines():
        m = re.search(r"ST-LINK SN\s*:\s*([A-Za-z0-9]+)", line)
        if m:
            sn = m.group(1).strip()
            if sn not in sns:
                sns.append(sn)
    if not sns:
        # Check single probe output
        m = re.search(r"Serial number\s*:\s*([A-Za-z0-9]+)", out)
        if m:
            sns.append(m.group(1).strip())
            
    probes = []
    for sn in sns:
        info_cmd = [cli_path, "-c", "port=SWD", f"sn={sn}"]
        r = subprocess.run(info_cmd, capture_output=True, text=True)
        r_out = r.stdout + r.stderr
        
        dev_id = None
        dev_m = re.search(r"Device ID\s*:\s*(0x[0-9a-fA-F]+)", r_out)
        if dev_m:
            dev_id = dev_m.group(1).lower()
            
        mcu_info = MCU_DEVICE_ID_MAP.get(dev_id, {"mcu": "Unknown", "family": "Unknown", "fqbn": "Unknown"})
        probes.append({
            "sn": sn,
            "device_id": dev_id,
            "mcu": mcu_info["mcu"],
            "fqbn": mcu_info["fqbn"]
        })
    return probes

def main():
    cli = find_programmer_cli()
    ports = get_serial_ports()
    print(f"[PROBE] Found {len(ports)} serial ports: {ports}")
    
    if not cli:
        print("[WARN] STM32_Programmer_CLI not found. Listing serial ports only.")
        return

    probes = probe_stlink_probes(cli)
    print(f"[PROBE] Found {len(probes)} ST-Link probes:")
    for p in probes:
        print(f"  SN: {p['sn']} | DeviceID: {p['device_id']} | MCU: {p['mcu']}")

    # If connections.json exists, update it or generate sample
    conn_path = "connections.json"
    if os.path.exists(conn_path):
        with open(conn_path, "r") as f:
            existing = json.load(f)
        print(f"\n[INFO] Current {conn_path}: {json.dumps(existing, indent=2)}")
    else:
        print(f"\n[INFO] {conn_path} not found. Create one mapping roles (OBC, COMMS, GroundStation) to ports.")

if __name__ == "__main__":
    main()

