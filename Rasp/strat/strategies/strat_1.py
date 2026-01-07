from strat.actions import RobotActions
import time
METADATA={"name":"strat_1","score":0}
def run(robot: RobotActions):
    print("Start strat_1")
    robot.set_pos(2750, 1800, -90)
    robot.goto(1600, 1000, -90, force=400)
    robot.prendreKapla(hauteur=0)
    robot.retournerKapla()
    robot.goto(1000, 500, 90, force=650)
    robot.poseKapla(hauteur=0)
    robot.stop()
    
    print("End")