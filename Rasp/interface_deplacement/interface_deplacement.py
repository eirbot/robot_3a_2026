import tkinter as tk
from tkinter import simpledialog
import numpy as np
import bezier
import ClassPoint
import ClassDialogue
import ClassRobot
import ClassBezier
import serial
import json
from serial.serialutil import SerialException
import time
import ast
from PIL import Image, ImageTk
from esp32_detect import find_esp32_port

points_courbe_bezier = 20

def resize_image():
    """Redimensionne l’image en gardant le ratio"""
    global displayed_image, photo, img_scale, offset_x, offset_y

    global container_width
    global container_height

    img_ratio = original_image.width / original_image.height
    container_ratio = container_width / container_height

    if container_ratio > img_ratio:
        new_height = container_height
        new_width = int(new_height * img_ratio)
    else:
        new_width = container_width
        new_height = int(new_width / img_ratio)

    img_scale = new_width / original_image.width
    offset_x = (container_width - new_width) // 2
    offset_y = (container_height - new_height) // 2

    displayed_image = original_image.resize((new_width, new_height), Image.LANCZOS)
    photo = ImageTk.PhotoImage(displayed_image)

    # Supprime uniquement l’ancienne image de fond
    canvas.delete("background")
    bg = canvas.create_image(offset_x, offset_y, anchor="nw", image=photo, tags="background")
    canvas.tag_lower(bg)
    canvas.image = photo  # éviter le garbage collector



def on_drag(event):
    """Quand on déplace la souris tout en maintenant le clic"""
    if drag_data["item"]==point0.id:
        dx = (event.x - drag_data["x"])/900*3
        dy = (event.y - drag_data["y"])/600*2
        point0.moved(dx,dy)
        drag_data["x"] = event.x
        drag_data["y"] = event.y

        robot.move_absolu(point0.y, point0.x, 0) # Commenter ces lignes si manque de puissance sur la machine
        root.update()

    if drag_data["item"]==point1.id:
        dx = (event.x - drag_data["x"])/900*3
        dy = (event.y - drag_data["y"])/600*2
        point1.moved(dx,dy)
        drag_data["x"] = event.x
        drag_data["y"] = event.y
    elif drag_data["item"]==point2.id:
        dx = (event.x - drag_data["x"])/900*3
        dy = (event.y - drag_data["y"])/600*2
        point2.moved(dx,dy)
        drag_data["x"] = event.x
        drag_data["y"] = event.y
    elif drag_data["item"]==point3.id:
        dx = (event.x - drag_data["x"])/900*3
        dy = (event.y - drag_data["y"])/600*2
        point3.moved(dx,dy)
        drag_data["x"] = event.x
        drag_data["y"] = event.y
    elif drag_data["item"]==point4.id:
        dx = (event.x - drag_data["x"])/900*3
        dy = (event.y - drag_data["y"])/600*2
        point4.moved(dx,dy)
        drag_data["x"] = event.x
        drag_data["y"] = event.y

    if len(segments):
        segments[segment_on_edit].calcul(points_courbe_bezier)
        segments[segment_on_edit].affiche() 

def on_release(event):
    x_click = event.x
    y_click = event.y

    if drag_data["item"] is not None:
        if offset_x <= x_click <= offset_x + displayed_image.width and \
        offset_y <= y_click <= offset_y + displayed_image.height:
            x_img = float((x_click - offset_x) / displayed_image.width * 3 - 1.5)
            y_img = float((y_click - offset_y) / displayed_image.height * 2)
            if drag_data["item"]==point0.id:
                indice_point = drag_data["item"]- point0.id
                point0.x = x_img
                point0.y = y_img
                Boite0.schema_to_boite(x_img, y_img)
                envoyer("SET POSE")

            if drag_data["item"]==point1.id:
                indice_point = drag_data["item"]- point1.id
                point1.x = x_img
                point1.y = y_img
                Boite1.schema_to_boite(x_img, y_img)
            if drag_data["item"]==point2.id:
                indice_point = drag_data["item"]- point2.id
                point2.x = x_img
                point2.y = y_img
                Boite2.schema_to_boite(x_img, y_img)
            if drag_data["item"]==point3.id:
                indice_point = drag_data["item"]- point3.id
                point3.x = x_img
                point3.y = y_img
                Boite3.schema_to_boite(x_img, y_img)
            if drag_data["item"]==point4.id:
                indice_point = drag_data["item"]- point4.id
                point4.x = x_img
                point4.y = y_img
                Boite4.schema_to_boite(x_img, y_img)
        else:
            print("Clic en dehors de l’image")
        
        if(len(segments)):
            segments[segment_on_edit].calcul(points_courbe_bezier)
            segments[segment_on_edit].affiche()

        robot.move_absolu(point0.y, point0.x, 0)
        root.update()


    drag_data["item"] = None

def on_click(event):

    """Quand on clique, on vérifie si on clique sur le point"""
    items = canvas.find_overlapping(event.x, event.y, event.x, event.y)
    if point0.id in items:
        drag_data["item"] = point0.id
        drag_data["x"] = event.x
        drag_data["y"] = event.y
    if point1.id in items:
        drag_data["item"] = point1.id
        drag_data["x"] = event.x
        drag_data["y"] = event.y
    elif point2.id in items:
        drag_data["item"] = point2.id
        drag_data["x"] = event.x
        drag_data["y"] = event.y
    elif point3.id in items:
        drag_data["item"] = point3.id
        drag_data["x"] = event.x
        drag_data["y"] = event.y
    elif point4.id in items:
        drag_data["item"] = point4.id
        drag_data["x"] = event.x
        drag_data["y"] = event.y

def on_enter(event):
    if len(segments):
        segments[segment_on_edit].calcul(points_courbe_bezier)
        segments[segment_on_edit].affiche() 

def envoyer(message):

    if(len(message)!=0):
        port = find_esp32_port()

        if port:
            print("ESP32 détecté sur :", port)
        else:
            print("Aucun ESP32 détecté.")

        try :
            with serial.Serial(port=port,baudrate=115200,timeout=1) as ser:
                time.sleep(0.1)

                if not isinstance(message, str):
                    trajectoire_bezier_mm = message
                    for coordonnee in trajectoire_bezier_mm:
                        coordonnee[0] *= 1000
                        coordonnee[1] *= 1000
                    trajectoire_bezier_string = json.dumps(trajectoire_bezier_mm.tolist())

                    ser.write((trajectoire_bezier_string+'\n').encode())
                    print("Trajectoire envoyé")
                    print("Réponse ESP (ctrl+C pour stoper) : ")
                    while True:
                        msg = ser.readline().decode(errors="ignore").strip()
                        if msg:
                            print(">>", msg)
                            if(msg[0]=='['):
                                msg_list = ast.literal_eval(msg)
                                robot.move_absolu(msg_list[0], msg_list[1], msg_list[2]*180/np.pi)
                                root.update()
                elif(message[0:8]=="SET POSE"):
                    print("Changement de position de robot depuis l'interface")
                    ser.write((f"SET POSE {robot.y*1000} {robot.x*1000} {robot.theta}\n").encode())
        except SerialException as e:
            print("Echec de l'envoie des données vers le port COM :\n", e)
        except KeyboardInterrupt:
            print("Arrêt du programme.")
    else:
        print("message vide")

def nouveau_segment():
    global segments, segment_on_edit
    label = "bezier"+ str(segment_on_edit+1)
    
    if(len(segments)):
        point1.move(point4.x, point4.y)
        point2.move(point4.x+0.1, point4.y)
        point3.move(point4.x+0.2, point4.y)
        point4.move(point4.x+0.3, point4.y)

    new_bezier = ClassBezier.Bezier(canvas, displayed_image, label, point1, point2, point3, point4)
    segments.append(new_bezier)
    segment_on_edit = len(segments)-1

def simu_robot(k=0):
    # positions = [[0,-1.5],[0,1.5],[2,1.5],[2,-1.5]]
    # robot.move_absolu(positions[k%4][0], positions[k%4][1], k*10)

    if(trajectoire_bezier.size!=0):
        len = trajectoire_bezier.shape[0]
        theta = 180+ np.atan2(( trajectoire_bezier[(k-1)%len][1] - trajectoire_bezier[k%len][1]),(trajectoire_bezier[(k-1)%len][0] - trajectoire_bezier[k%len][0] ))*180/np.pi
        robot.move_absolu(trajectoire_bezier[k%len][0], trajectoire_bezier[k%len][1], theta)
    else:
        k=0

    if k < 10000:
        root.after(100, rotate_loop, k+1)

root = tk.Tk()
root.title("Interface de déplacement")
root.geometry("900x730+0+0")
container_width = 900
container_height = 600
pixels_to_meters = 3/container_width

original_image = Image.open("table_coupe_2026.png")

canvas = tk.Canvas(root, bg="black")
canvas.pack(fill="both", expand=True)

photo = ImageTk.PhotoImage(original_image)
bg = canvas.create_image(0, 0, anchor="nw", image=photo, tags="background")
canvas.tag_lower(bg)

robot = ClassRobot.Robot(canvas, pixels_to_meters, 0, 0, 0)

# simu_robot()

img_scale = 1.0
offset_x = offset_y = 0
displayed_image = original_image

point0 = ClassPoint.Point(canvas, 0, 0) #position initiale du robot

point1 = ClassPoint.Point(canvas, 1, 1, 6, "red") #parametres courbe de bezier
point2 = ClassPoint.Point(canvas, 1.1, 1, 6, "yellow") #parametres courbe de bezier
point3 = ClassPoint.Point(canvas, 1.2, 1, 6, "green") #parametres courbe de bezier
point4 = ClassPoint.Point(canvas, 1.3, 1, 6, "blue") #parametres courbe de bezier

segments = []
segment_on_edit = -1

Boite0 = ClassDialogue.Dialogue(root, "Position Robot", point0)

Boite1 = ClassDialogue.Dialogue(root, "Point1", point1)
Boite2 = ClassDialogue.Dialogue(root, "Point2", point2)
Boite3 = ClassDialogue.Dialogue(root, "Point3", point3)
Boite4 = ClassDialogue.Dialogue(root, "Point4", point4)

bouton1 = tk.Button(root, text="Envoyer", command=lambda: envoyer(segments[segment_on_edit].trajectoire))
bouton1.pack()

bouton2 = tk.Button(root, text="Nouveau segment", command=lambda: nouveau_segment())
bouton2.pack()

drag_data = {"x": 0, "y": 0, "item": None}

resize_image()

canvas.bind("<Button-1>", on_click)
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<ButtonRelease-1>", on_release)
root.bind("<Return>", on_enter)



root.mainloop()


