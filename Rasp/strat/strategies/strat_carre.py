from strat.actions import RobotActions
import time
METADATA={"name":"strat_carre","score":0}
def run(robot: RobotActions):
    print("Start strat_carre")
    robot.set_pos(2750, 1800, -90)
    robot.goto(2750, 800, 180, force=10)
    robot.goto(1750, 800, 90, force=10)
    robot.goto(1750, 1400, 90, force=10)
    robot.goto(2750, 1400, 90, force=10)
    robot.stop()
    
    print("End")