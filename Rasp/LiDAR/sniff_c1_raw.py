#!/usr/bin/env python3
"""
Sniffer pour RPLIDAR C1M1-R2
- envoie la commande de start scan (0xA5 0x20)
- lit le flux série brut
- sauvegarde un fichier binaire
- affiche des dumps hex et tentatives d'analyse (détection de motifs / longueurs)
"""

import serial, time, sys, os, collections, struct

PORT = "/dev/ttyUSB0"
BAUD = 460800
OUT_BIN = "c1_raw_capture.bin"
DURATION = 15       # durée de capture en secondes (ajuste)
PRINT_EVERY = 1.0   # intervalle d'affichage en secondes

def hexdump(buf, max_bytes=64):
    s = " ".join(f"{b:02X}" for b in buf[:max_bytes])
    if len(buf) > max_bytes:
        s += " ..."
    return s

def find_repeats(data, min_len=3, max_len=64):
    """
    Cherche motifs répétitifs dans data ; renvoie top candidats (motif, count).
    Simple sliding-window frequency test.
    """
    freq = collections.Counter()
    N = len(data)
    for L in range(min_len, max_len+1):
        for i in range(0, N - L + 1):
            freq[data[i:i+L]] += 1
    # garder motifs qui apparaissent > 1
    common = [(k, v) for k, v in freq.items() if v > 1]
    common.sort(key=lambda kv: kv[1], reverse=True)
    return common[:50]

def try_sync_positions(data, sync_bytes):
    """renvoie indices où sync_bytes apparait"""
    idxs = []
    i = data.find(sync_bytes)
    while i != -1:
        idxs.append(i)
        i = data.find(sync_bytes, i+1)
    return idxs

def main():
    print(f"[INFO] Ouverture port {PORT} à {BAUD} bauds")
    ser = serial.Serial(PORT, BAUD, timeout=0.5)
    # vider buffers
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # envoi commande start scan (A5 20) - commun pour rplidar
    print("[INFO] Envoi commande start scan 0xA5 0x82")
    ser.write(b'\xA5\x82')
    time.sleep(0.05)

    print(f"[INFO] Capture {DURATION}s dans {OUT_BIN} ...")
    with open(OUT_BIN, "wb") as f:
        t0 = time.time()
        last_print = t0
        while time.time() - t0 < DURATION:
            chunk = ser.read(4096)
            if chunk:
                f.write(chunk)
            # affichage périodique
            if time.time() - last_print >= PRINT_EVERY:
                # lire un échantillon du début du fichier pour diagnostic rapide
                f.flush()
                filesize = os.path.getsize(OUT_BIN)
                print(f"[INFO] captured {filesize} bytes")
                last_print = time.time()
        ser.close()
    print("[INFO] Fin capture")

    # --- analyse basique du fichier capturé ---
    data = open(OUT_BIN, "rb").read()
    print(f"[ANALYSE] taille fichier: {len(data)} bytes")
    print("[ANALYSE] hexdump (début) :", hexdump(data[:128], 128))
    print("[ANALYSE] hexdump (offset 128:256) :", hexdump(data[128:256], 128))

    # rechercher des positions probables d'un descriptor (ex: A5 5A ou A5 A5, etc.)
    # on cherche motifs d'en-tête typiques : 0xA5, 0x5A, 0xAA, 0x55
    candidates = [b'\xA5', b'\xA5\x5A', b'\xA5\xA5', b'\x59', b'\xA5\x20', b'\xA5\x25']
    for c in candidates:
        idxs = try_sync_positions(data, c)
        if idxs:
            print(f"[ANALYSE] motif {c.hex()} trouvé {len(idxs)} fois, premiers idx: {idxs[:10]}")

    # histogramme des longueurs entre motifs 0xA5 occurrences (pour estimer longueur descriptor/paquet)
    a5_idxs = try_sync_positions(data, b'\xA5')
    diffs = []
    for i in range(1, len(a5_idxs)):
        diffs.append(a5_idxs[i] - a5_idxs[i-1])
    if diffs:
        from statistics import mean, median, pstdev
        print(f"[ANALYSE] a5 count={len(a5_idxs)}, mean diff={mean(diffs):.1f}, median={median(diffs):.1f}, stdev={pstdev(diffs):.1f}")
        # top 10 most common diffs
        freq = collections.Counter(diffs)
        print("[ANALYSE] top diffs:", freq.most_common(10))

    # chercher motifs fréquents
    print("[ANALYSE] recherche de motifs fréquents (peut prendre du temps)...")
    common = find_repeats(data, min_len=3, max_len=12)
    for k, v in common[:12]:
        print(f" motif({len(k)} bytes) x{v} : {k.hex()}")

    # essayer d'interpréter blocs : rechercher paquets où la 1ère octet a bit0 = start_flag (valeur impaire typiquement)
    print("[ANALYSE] tenter de repérer paquets 5-octets style old-rplidar (start flag bit)") 
    # on balaye en cherchant octets impairs qui pourraient être start flags
    starts = [i for i, b in enumerate(data) if b & 0x1]
    print(f"[ANALYSE] found {len(starts)} candidate start bytes (bit0=1). sample idxs: {starts[:20]}")
    if len(starts) >= 20:
        # calcule diff moyen entre starts
        diffs2 = [starts[i+1] - starts[i] for i in range(len(starts)-1)]
        from collections import Counter
        print("[ANALYSE] common gaps between start bytes:", Counter(diffs2).most_common(10))

    print("[ANALYSE] terminé — envoie-moi les premiers 800-2000 octets (hex) si tu veux que je déduise le format.")
    print(f"[ANALYSE] tu peux afficher un dump hex par ex: head -c 1024 {OUT_BIN} | xxd -g 1 -u")
    return 0

if __name__ == "__main__":
    main()
