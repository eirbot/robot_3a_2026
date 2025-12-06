import tkinter as tk
from PIL import Image, ImageTk
import numpy as np

class Robot:

    DEG_TO_RAD = np.pi/180

    def __init__(self, canvas, pixel_to_meters, x, y, theta):
        self.canvas = canvas
        self.pixel_to_meters = pixel_to_meters
        self.meters_to_pixel = 1/pixel_to_meters
        self.x = y #inversement du x et du y pour avoir z vers le haut et correspondre au repère du robot
        self.y = x
        self.theta = theta

        self.robot_image = Image.open("robot.png")

        width_PIL, height_PIL = self.robot_image.size
        ratio = height_PIL/width_PIL
        self.width = int(0.364*self.meters_to_pixel)
        self.height = int(ratio*0.364*self.meters_to_pixel)

        self.robot_PIL_resized = self.robot_image.resize((self.width, self.height), Image.LANCZOS)
        self.robot_PIL = self.robot_PIL_resized
        self.afficher_robot()
        self.move_absolu(self.x, self.y, self.theta)

    def afficher_robot(self):
        self.robot_photo = ImageTk.PhotoImage(self.robot_PIL)
        self.robot_id = self.canvas.create_image((self.x+1.5)*self.meters_to_pixel, self.y*self.meters_to_pixel, anchor="center", image=self.robot_photo, tags="robot")

    def rotate(self, theta):
        self.theta = theta
        self.robot_PIL = self.robot_PIL_resized.rotate(self.theta, expand=True)
        self.robot_photo = ImageTk.PhotoImage(self.robot_PIL)

    def move_absolu(self, x, y, theta):
        self.x = y
        self.y = x
        self.rotate(theta)
        self.canvas.coords(self.robot_id, (self.x+1.5)*self.meters_to_pixel , self.y*self.meters_to_pixel)
        self.canvas.itemconfig(self.robot_id, image=self.robot_photo)