
import tkinter as tk
import math

class Dialogue:

    def __init__(self, root, label, point):
        self.root = root
        self.point = point
        self.label = label
            
        frame = tk.Frame(root)
        frame.pack(pady=2)

        txt = self.label + "    X :"
        tk.Label(frame, text=txt).pack(side="left", padx=5) # On inverse les axes par rapport à tkinter pour correspondre à la table
        self.entreey = tk.Entry(frame, width=10)
        self.entreey.pack(side="left", padx=5)
        self.entreey.insert(0, str(math.floor(point.y*100)/100))
        self.entreey.bind("<Return>", self.human_to_boite)

        tk.Label(frame, text="Y :").pack(side="left", padx=5) # On inverse les axes par rapport à tkinter pour correspondre à la table
        self.entreex = tk.Entry(frame, width=10)
        self.entreex.pack(side="left", padx=5)
        self.entreex.insert(0, str(math.floor(point.x*100)/100))
        self.entreex.bind("<Return>", self.human_to_boite)

    
    def human_to_boite(self, event):
        try:
            self.point.x = float(self.entreex.get())
            self.point.y = float(self.entreey.get())
            self.point.move(self.point.x, self.point.y)
            print(f"Nouvelle valeur : {self.point.x}, {self.point.y}")
        except ValueError:
            print("Entrée invalide")

    def schema_to_boite(self, valuex, valuey):
        self.point.x = valuex
        self.entreex.delete(0, tk.END)
        self.entreex.insert(0, str(math.floor(self.point.x*100)/100))

        self.point.y = valuey
        self.entreey.delete(0, tk.END)
        self.entreey.insert(0, str(math.floor(self.point.y*100)/100))




