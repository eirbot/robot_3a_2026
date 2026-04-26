import serial.tools.list_ports

def find_esp32_port():
    ports = serial.tools.list_ports.comports()

    ESP32_IDS = [
        (0x1A86, 0x7523),  # CH340
        (0x10C4, 0xEA60),  # CP2102
        (0x303A, None),    # Espressif native USB
    ]

    for port in ports:
        vid = port.vid
        pid = port.pid

        if vid is None:
            continue

        for vid_ref, pid_ref in ESP32_IDS:
            if vid == vid_ref and (pid_ref is None or pid == pid_ref):
                return port.device

    # fallback
    for port in ports:
        desc = port.description.lower()
        if ("ch340" in desc or
            "cp210" in desc or
            "usb serial" in desc or
            "espressif" in desc):
            return port.device

    return None
