import numpy as np
import matplotlib.pyplot as plt

# === 1 Définir les points de contrôle (P0, P1, P2, P3)
P0 = np.array([0, 0])
P1 = np.array([1, 2])
P2 = np.array([3, 3])
P3 = np.array([4, 0])

# === 2️ Fonction de Bézier cubique
def bezier_cubique(t, P0, P1, P2, P3):
    """
    Calcule les coordonnées de la courbe de Bézier cubique
    pour un paramètre t (0 <= t <= 1)
    """
    return (
        (1 - t)**3 * P0 +
        3 * (1 - t)**2 * t * P1 +
        3 * (1 - t) * t**2 * P2 +
        t**3 * P3
    )

# === 3️ Calcul de la courbe pour plusieurs valeurs de t

def bezier_cubique_discret(n, P0, P1, P2, P3):
    t_vals = np.linspace(0, 1, n)
    return (np.array([bezier_cubique(t, P0, P1, P2, P3) for t in t_vals]))


# === 4️ Affichage avec matplotlib
# plt.figure(figsize=(6, 4))
# plt.plot(curve[:, 0], curve[:, 1], 'b-', label="Courbe de Bézier")
# plt.plot([P0[0], P1[0], P2[0], P3[0]],
#          [P0[1], P1[1], P2[1], P3[1]], 'k--', label="Polygone de contrôle")
# plt.scatter([P0[0], P1[0], P2[0], P3[0]],
#             [P0[1], P1[1], P2[1], P3[1]], color='red', zorder=5)

# plt.legend()
# plt.title("Courbe de Bézier cubique (4 points)")
# plt.axis("equal")
# plt.grid(True)
# plt.show()
