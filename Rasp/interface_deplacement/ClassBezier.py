
import bezier
import numpy as np

class Bezier:

    def __init__(self, canvas, displayed_image, label, point1, point2, point3, point4, nb_points):
        self.canvas = canvas
        self.displayed_image = displayed_image
        self.label = label
        self.point1 = point1
        self.point2 = point2
        self.point3 = point3
        self.point4 = point4

        self.nb_points = nb_points

        self.offset_x = 0
        self.offset_y = 0
        
        self.calcul(nb_points)

    def resize_affichage(self, displayed_image, offset_x, offset_y):
        self.displayed_image = displayed_image
        self.offset_x = offset_x
        self.offset_y = offset_y
    
    def calcul(self, nb_point):
        # On inverse les axes par rapport à tkinter pour correspondre à la table
        self.trajectoire = bezier.bezier_cubique_discret(nb_point, np.array([self.point1.y, self.point1.x]), np.array([self.point2.y, self.point2.x]), np.array([self.point3.y, self.point3.x]), np.array([self.point4.y, self.point4.x]))

    def affiche(self):

        traj_pix = np.zeros_like(self.trajectoire)
        traj_pix[:, 0] = self.offset_x + (self.trajectoire[:, 1] + 1.5) / 3 * self.displayed_image.width # On inverse les axes par rapport à tkinter pour correspondre à la table
        traj_pix[:, 1] = self.offset_y + (self.trajectoire[:, 0]) / 2 * self.displayed_image.height # On inverse les axes par rapport à tkinter pour correspondre à la table

        
        self.canvas.delete("vecteur")
        self.canvas.create_line((self.point1.x+1.5)/3*900, self.point1.y/2*600, (self.point2.x+1.5)/3*900, self.point2.y/2*600, fill="blue", width=2, tags="vecteur")
        self.canvas.create_line((self.point3.x+1.5)/3*900, self.point3.y/2*600, (self.point4.x+1.5)/3*900, self.point4.y/2*600, fill="blue", width=2, tags="vecteur")
        
        self.canvas.delete(self.label)
        self.__affiche_points(traj_pix)

    def __affiche_points(self, liste_coordonnes):
        """Affiche la courbe de Bézier sous forme de segments"""
        for i_coord in range(liste_coordonnes.shape[0] - 1):
            self.canvas.create_line(
                liste_coordonnes[i_coord][0], liste_coordonnes[i_coord][1],
                liste_coordonnes[i_coord + 1][0], liste_coordonnes[i_coord + 1][1],
                fill="red", width=2, tags=self.label
            )



