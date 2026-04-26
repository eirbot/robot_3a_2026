import json
import math
import matplotlib.pyplot as plt


def speed_plot():

    with open("logs_vitesse.txt", "r") as f:
        time_plot = [0]
        position_x = [0]
        position_y = [0]
        speed_forward_plot = [0]
        speed_rotation_plot = [0]
        for index, line in enumerate(f):
            if index == 0: 
                point = json.loads(line)
                previous_point = point
            else:
                point = json.loads(line)
                diffL = diff(point, previous_point)

                time_plot.append(diffL[0]+time_plot[len(time_plot)-1])
                position_x.append(point["x"])
                position_y.append(point["y"])
                speed_forward_plot.append(diffL[1]/diffL[0])
                speed_rotation_plot.append(diffL[2]/diffL[0])

                previous_point = point
        
        fig, axes = plt.subplots(2, 2)
        axes[0,0].plot(time_plot, position_x, label="position_x")
        axes[1,0].plot(time_plot, position_y, label="speed rotation")
        axes[0,1].plot(time_plot, speed_forward_plot, label="speed forward")
        axes[1,1].plot(time_plot, speed_rotation_plot, label="speed rotation")

        axes[0,1].set_xlim(0, 4)
        axes[0,1].set_ylim(0, 1.5)

        axes[1,1].set_xlim(0, 4)
        axes[1,1].set_ylim(-300, 300)

        plt.show()

def diff(point, previous_point):
    position_diff = math.sqrt((previous_point["x"] - point["x"])**2 + (previous_point["y"] - point["y"])**2)
    angle_diff = point["theta"] - previous_point["theta"]
    time_diff = point["time"] - previous_point["time"]
    return [time_diff, position_diff, angle_diff]

speed_plot()