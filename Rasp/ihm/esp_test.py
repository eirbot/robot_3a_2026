import serial, time # type: ignore

ESP_PORTS = ["/dev/ttyUSB1", "/dev/ttyUSB2"]

def test_esp32():
    for port in ESP_PORTS:
        try:
            with serial.Serial(port, 115200, timeout=1) as ser:
                ser.write(b"TEST\n")
                time.sleep(0.1)
                resp = ser.read_all().decode(errors="ignore")
                print(f"[ESP] {port}: {resp.strip() or 'aucune réponse'}")
        except Exception as e:
            print(f"[ESP] {port}: erreur {e}")
