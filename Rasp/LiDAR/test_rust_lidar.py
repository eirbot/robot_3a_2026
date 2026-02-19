#!/usr/bin/env python3
import sys
import os

# Ajoute le dossier courant au PYTHONPATH pour trouver les modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from rplidar_c1m1 import RPLidarC1M1
    print("[TEST] Import réussi de RPLidarC1M1")
    
    lidar = RPLidarC1M1()
    if lidar.is_rust:
        print("[TEST] SUCCÈS : Le driver Rust est actif !")
    else:
        print("[TEST] ATTENTION : Le driver Python est utilisé (Rust non détecté ou erreur d'import)")
        
except Exception as e:
    print(f"[TEST] ERREUR : {e}")

# Note: on ne tente pas de connexion ici car pas de LIDAR branché probablement
