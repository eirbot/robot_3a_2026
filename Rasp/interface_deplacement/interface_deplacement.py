import tkinter as tk
from PIL import Image, ImageTk

def resize_image(event):
    """Redimensionne l’image en gardant le ratio"""
    global displayed_image, photo, img_scale, offset_x, offset_y

    container_width = event.width
    container_height = event.height

    img_ratio = original_image.width / original_image.height
    container_ratio = container_width / container_height

    if container_ratio > img_ratio:
        new_height = container_height
        new_width = int(new_height * img_ratio)
    else:
        new_width = container_width
        new_height = int(new_width / img_ratio)

    # Calcul du facteur d’échelle et des marges (centrage)
    img_scale = new_width / original_image.width
    offset_x = (container_width - new_width) // 2
    offset_y = (container_height - new_height) // 2

    # Redimensionnement de l’image
    displayed_image = original_image.resize((new_width, new_height), Image.LANCZOS)
    photo = ImageTk.PhotoImage(displayed_image)
    label.config(image=photo)
    label.image = photo

def on_click(event):
    """Récupère les coordonnées du clic (dans l’image originale)"""
    x_click = event.x
    y_click = event.y

    # Vérifie si le clic est à l’intérieur de l’image affichée
    if offset_x <= x_click <= offset_x + displayed_image.width and \
       offset_y <= y_click <= offset_y + displayed_image.height:
        # Convertit les coordonnées en repère de l’image originale
        x_img = float((x_click - offset_x) / displayed_image.width *3 - 1.5)
        y_img = float((y_click - offset_y) / displayed_image.height *2)
        print(f"Clic sur l’image : (x= {x_img:.3f} m, y= {y_img:.3f} m) ")
    else:
        print("Clic en dehors de l’image")

root = tk.Tk()
root.title("Interface de déplacement")
root.geometry("900x600+0+0")

original_image = Image.open("table_coupe_2026.png")

photo = ImageTk.PhotoImage(original_image)
label = tk.Label(root, image=photo, bg="black")
label.pack(fill="both", expand=True)

# Variables globales pour l’échelle et le décalage
img_scale = 1.0
offset_x = offset_y = 0
displayed_image = original_image

# Événements
label.bind("<Configure>", resize_image)
label.bind("<Button-1>", on_click)  # clic gauche

root.mainloop()
