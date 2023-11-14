import frrpc
from fair_robot_func import wait_until_robot_finished
robot = frrpc.RPC('192.168.58.2')
print("robot is connected")
robot.ImmStopJOG()