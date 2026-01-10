import numpy as np
import matplotlib.pyplot as plt

# === Fonction de Bézier cubique ===
def bezier_cubique(t, P0, P1, P2, P3):
    """
    Calcule les coordonnées de la courbe de Bézier cubique
    pour un paramètre t (0 <= t <= 1).
    """
    # La formule mathématique vectorielle
    return (
        (1 - t)**3 * P0 +
        3 * (1 - t)**2 * t * P1 +
        3 * (1 - t) * t**2 * P2 +
        t**3 * P3
    )

# === Calcul de la courbe pour plusieurs valeurs de t ===
def bezier_cubique_discret(n, P0, P1, P2, P3):
    """
    Génère n points le long de la courbe.
    Convertit automatiquement les entrées (tuples) en vecteurs numpy.
    """
    # --- CORRECTION CRITIQUE ICI ---
    # On transforme les tuples (x,y) en array numpy pour permettre les maths (multiplication par float)
    P0 = np.array(P0)
    P1 = np.array(P1)
    P2 = np.array(P2)
    P3 = np.array(P3)
    # -------------------------------

    t_vals = np.linspace(0, 1, n)
    
    # On retourne un tableau de points
    return np.array([bezier_cubique(t, P0, P1, P2, P3) for t in t_vals])