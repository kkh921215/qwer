import time
import numpy as np
import pandas as pd

## communication message
MSG_CAM_READY = 0
MSG_TRIGGER = 1
MSG_PROG_STOP = 2
MSG_DETECTED = 3
MSG_NOTHING = 4



def fair_task(config,conn):
    from fair_robot_func import wait_until_robot_finished
    import frrpc
    CAMWIDTH=config["vision"]["camwidth"]
    ROBOT_IP=config["robot"]["robot_ip"]
    robot = frrpc.RPC(ROBOT_IP)
    print("robot is connected")

    recv=conn.recv()
    if recv==MSG_CAM_READY: print("robot and cam are ready")
    else: raise Exception("not ready")

    #set speed 
    robot.Mode(0)    # auto mode  
    robot.SetSpeed(7)
    robot.Mode(1)    # manual mode
    robot.SetSpeed(7)

    # reset error
    robot.ResetAllError() 
    
    # robot tasks start
    robot.Mode(0)
    robot.ProgramLoad('/fruser/supplyWater.lua')
    robot.ProgramRun()
    wait_until_robot_finished(robot)
    conn.send(MSG_TRIGGER)

    recv=conn.recv()
    if recv==MSG_DETECTED:
        cam_data = conn.recv()
        print('Robot received data: \n ', cam_data)
        # detect where the cups exist out of three area
        cup_existence={"First":False,"Second":False,"Third":False}
        for i in range(len(cam_data)):
            # load x location of object
            x_location=float(cam_data.loc[i, ['X']])
            if x_location<(CAMWIDTH/3):
                cup_existence["First"]=True
            elif x_location>((2*CAMWIDTH)/3):
                cup_existence["Third"]=True
            else:
                cup_existence["Second"]=True
        print(cup_existence)
        if cup_existence["First"]==True:
            current_cup=1
            robot.Mode(0)
            robot.ProgramLoad('/fruser/pickcup1.lua')
            robot.ProgramRun()
            wait_until_robot_finished(robot)
        elif cup_existence["Second"]==True:
            current_cup=2
            robot.Mode(0)
            robot.ProgramLoad('/fruser/pickcup2.lua')
            robot.ProgramRun()
            wait_until_robot_finished(robot)
        elif cup_existence["Third"]==True:
            current_cup=3
            robot.Mode(0)
            robot.ProgramLoad('/fruser/pickcup3.lua')
            robot.ProgramRun()
            wait_until_robot_finished(robot)
        else :
            print("There is no cup")
            raise Exception("no cup")
        time.sleep(1)
        robot.Mode(0)
        robot.ProgramLoad('/fruser/powderdrop.lua')
        robot.ProgramRun()
        wait_until_robot_finished(robot)
        if current_cup==1:
            robot.Mode(0)
            robot.ProgramLoad('/fruser/putcup1.lua')
            robot.ProgramRun()
            wait_until_robot_finished(robot)
        elif current_cup==2:
            robot.Mode(0)
            robot.ProgramLoad('/fruser/putcup2.lua')
            robot.ProgramRun()
            wait_until_robot_finished(robot)
        elif current_cup==3:
            robot.Mode(0)
            robot.ProgramLoad('/fruser/putcup3.lua')
            robot.ProgramRun()
            wait_until_robot_finished(robot)
        robot.Mode(0)
        robot.ProgramLoad('/fruser/restpartDripCoffee.lua')
        robot.ProgramRun()
        wait_until_robot_finished(robot)


    elif recv==MSG_NOTHING:
        raise Exception("cam error")
    conn.send(MSG_PROG_STOP)
    conn.close()
if __name__=="__main__":
    import frrpc
    robot = frrpc.RPC('192.168.58.2')
    # robot.SetSpeed(15)
    # robot.Mode(0)
    # robot.p()
    # robot.ProgramLoad('/fruser/supplyWater.lua')
    # robot.ProgramRun()
    # wait_until_robot_finished(robot)