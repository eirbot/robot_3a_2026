#!/usr/bin/env python3
"""
auto_infer_c1.py
Analyse automatique d'un dump brute C1M1-R2 (c1_raw_capture.bin).
Teste plusieurs longueurs de descriptor et tailles de paquets, cherche
champs plausibles (angle 0..360, distance 0..30000), et renvoie les
meilleures hypothèses.

Usage:
  python3 auto_infer_c1.py c1_raw_capture.bin
"""
import sys, collections, struct, math

FILENAME = sys.argv[1] if len(sys.argv) > 1 else "c1_raw_capture.bin"
data = open(FILENAME, "rb").read()
N = len(data)
print(f"[INFO] fichier {FILENAME}, taille {N} bytes")

# candidats d'entêtes détectés (observés dans ton dump)
headers = [b'\xA5\x5A', b'\xA5\x20', b'\xA5\x25', b'\xA5\xA5', b'\x5B', b'\x59']

# hypothèses
descriptor_lengths = [6,7,8,9,10,11,12,14]   # size of descriptor after header
# hypothèse de taille par bloc (après descriptor) — points groupés (3..20) * item_size
candidate_item_sizes = [3,4,5,6,7,8,9,10,12]
candidate_group_counts = [1,2,3,4,6,8,12,16]

# helper: check plausibility of an interpreted (angle, dist)
def plausible(angle_deg, dist_mm):
    if not (0.0 <= angle_deg < 360.0): return False
    if not (0 <= dist_mm <= 30000): return False
    return True

# find header positions
hdr_pos = {}
for h in headers:
    pos = []
    i = data.find(h)
    while i != -1:
        pos.append(i)
        i = data.find(h, i+1)
    hdr_pos[h] = pos
    print(f"[FOUND] header {h.hex()} count={len(pos)}")

# function to try parse at offset with given item_size and group_count
def score_hypothesis(start_off, item_size, group_count, offset_into_group=0):
    # try to extract sequential items and compute plausibility ratio
    # we will interpret each item as a pair (angle, dist) from combinations of bytes
    # Try several interpretations:
    # - angle from 2 bytes (uint16) / 100 or / 64
    # - dist from 2 bytes (uint16) / 1 or /4
    # We'll test multiple bitshifts/combinations.
    max_items = 2000
    good = 0
    total = 0
    items = []
    i = start_off
    # read up to max_items items while in bounds
    while total < max_items and i + item_size <= N:
        chunk = data[i:i+item_size]
        total += 1
        # try several decodings
        ok = False
        decoded = None
        # try angle as uint16 little, dist as uint16 little (various scalings)
        if item_size >= 4:
            # two first bytes -> angle_raw ; next two -> dist_raw
            a_raw = struct.unpack_from("<H", chunk, 0)[0]
            d_raw = struct.unpack_from("<H", chunk, 2)[0]
            for a_scale in (100.0, 64.0, 128.0, 256.0, 10.0):
                for d_scale in (1.0, 4.0, 2.0):
                    angle = a_raw / a_scale
                    dist = d_raw / d_scale
                    if plausible(angle, dist):
                        ok = True
                        decoded = (angle, dist)
                        break
                if ok: break
        # if item_size >=5 or 6, try other offsets: angle from bytes 1-2, dist from 3-4 etc.
        if not ok and item_size >=5:
            try:
                a_raw = struct.unpack_from("<H", chunk, 1)[0]
                d_raw = struct.unpack_from("<H", chunk, 3)[0]
                angle = a_raw / 100.0
                dist = d_raw / 4.0
                if plausible(angle, dist):
                    ok = True; decoded=(angle,dist)
            except:
                pass
        if ok:
            good += 1
            items.append(decoded)
        i += item_size
    score = good / total if total>0 else 0
    return score, total, good, items[:5]

# enumerate hypotheses anchored on header positions
results = []
# take first few header positions as anchors
anchor_positions = []
for h, poslist in hdr_pos.items():
    if poslist:
        anchor_positions += poslist[:10]
anchor_positions = sorted(set(anchor_positions))[:80]

print(f"[INFO] testing hypotheses on {len(anchor_positions)} anchor positions")

for item_size in candidate_item_sizes:
    for group_count in candidate_group_counts:
        # compute group byte length
        group_len = item_size * group_count
        # test each anchor as start of a group payload (after a header + descriptor)
        for desc_len in descriptor_lengths:
            for anchor in anchor_positions:
                # assume descriptor includes header length -> payload start at anchor+2+desc_len
                payload_start = anchor + 2 + desc_len
                if payload_start + group_len*3 > N:
                    continue
                score, total, good, sample_items = score_hypothesis(payload_start, item_size, group_count)
                if score > 0.6 and total>30 and good>20:
                    results.append((score, anchor, desc_len, item_size, group_count, total, good, sample_items))

# sort and show top candidates
results.sort(reverse=True, key=lambda x: (x[0], x[5]))
print(f"[RESULT] found {len(results)} promising hypotheses")
for r in results[:20]:
    score, anchor, desc_len, item_size, group_count, total, good, sample = r
    print(f" score={score:.3f} anchor={anchor} desc_len={desc_len} item_size={item_size} group_count={group_count} total={total} good={good} sample={sample}")

if not results:
    print("[INFO] aucune hypothèse très convaincante trouvée — on peut augmenter DURATION et réessayer ou affiner les heuristiques.")
else:
    print("[INFO] si un candidat te semble plausible, je génère le parseur exact.")

# also print a short hexdump head for manual inspection
print("\n[HEXHEAD] first 256 bytes:")
import binascii
print(binascii.hexlify(data[:256]).decode('ascii'))
