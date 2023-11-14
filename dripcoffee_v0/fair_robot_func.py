import time
#----------------get_cart_ret_joint_cart_relative-----------------------
# The parameter desc_pos get cartesian coordinate (dx,dy,dz,drx,dry,drz)
# If tool_Coordinate=True, return value based on tool coordinate otherwise based on base coordinate
# Return joint position, cartesian coordinate
def get_cart_ret_joint_cart_relative(robot,desc_pos,tool_Coordinate: bool=True):
    if tool_Coordinate==True: type=2
    else: type=1
    ret1=robot.GetInverseKin(type,desc_pos,-1)
    if ret1[0]!=0:
        return False,0,0
    ret2=robot.GetForwardKin(ret1[1:])
    if ret2[0]!=0:
        return False,0,0
    return True,ret1[1:],ret2[1:]
#----------------get_cart_ret_joint_absolute-----------------------
# The parameter desc_pos get cartesian coordinate (x,y,z,rx,ry,rz)
# and return joint position
def get_cart_ret_joint_absolute(robot,desc_pos): 
    ret1=robot.GetInverseKin(0,desc_pos,-1)
    if ret1[0]!=0:
        return False,0
    return True,ret1[1:]  
#----------------get_joint_ret_cart_absolute-----------------------
# The parameter joint_pos get joint position (r1,r2,r3,r4,r5,r6)
# and return cartesian coordinate
def get_joint_ret_cart_absolute(robot,joint_pos):
    ret1=robot.GetForwardKin(joint_pos)
    if ret1[0]!=0:
        return False,0
    return True,ret1[1:] 
#----------------About parameter-----------------------
#robot: fair_robot instance, tool_num: tool coordinate number, speed: speed of movement, 
#acceleration: acceleration of movement, ovl: speed scaling factor [0~100], blendT: smoothing time [ms] (-1: no blending)
#blendR: smooth radius [mm] (-1: no blending), pos: a position where you want to go

#---------------get_cart_joint_move_absolute----------------
# The parameter pos gets cartesian coordinates (x,y,z,rx,ry,rz)
# Robot moves absolutely based on base coordinates
# if success , return 0 ; else return -1
def get_cart_joint_move_absolute(robot,tool_num ,wobj_num,speed,acceleration,ovl,blendT,pos): 
    eP1=[0.000,0.000,0.000,0.000]
    dP1=[0.000,0.000,0.000,0.000,0.000,0.000]
    ret,output=get_cart_ret_joint_absolute(robot,pos)
    if ret==False:
        return -1
    robot.MoveJ(output,pos,tool_num,wobj_num,speed,acceleration,ovl,eP1,blendT,0,dP1)
    return 0
#---------------get_joint_joint_move_absolute----------------
# The parameter pos gets joint position (r1,r2,r3,r4,r5,r6)
# Robot moves absolutely based on base coordinates
# success : return 0 , fail : return -1
def get_joint_joint_move_absolute(robot,tool_num ,wobj_num,speed,acceleration,ovl,blendT,pos):
    eP1=[0.000,0.000,0.000,0.000]
    dP1=[0.000,0.000,0.000,0.000,0.000,0.000]  
    ret,output=get_joint_ret_cart_absolute(robot,pos)
    if ret==False:
        return -1
    robot.MoveJ(pos,output,tool_num,wobj_num,speed,acceleration,ovl,eP1,blendT,0,dP1)
    return 0
#---------------get_cart_joint_move_relative_tool_coord----------------
# The parameter pos gets cartesian coordinates (x,y,z,rx,ry,rz)
# Robot moves relatively based on tool coordinate
# success : return 0 , fail : return -1
# ex) pos=[0,0,10,0,0,90] robot moves 10 in z-axis direction and turns 90 degrees relative to the z-axis based on tool coordinate 
def get_cart_joint_move_relative_tool_coord(robot,tool_num ,wobj_num,speed,acceleration,ovl,blendT,pos,input=1):
    eP1=[0.000,0.000,0.000,0.000]
    desc_pos= robot.GetActualTCPPose(0)
    if desc_pos[0]!=0:
        return -1
    joint_pos= robot.GetActualJointPosDegree(0)
    if joint_pos[0]!=0:
        return -1
    robot.MoveJ(joint_pos[1:],desc_pos[1:],tool_num,wobj_num,speed,acceleration,ovl,eP1,blendT,2,pos)
    return 0
#---------------get_cart_joint_move_relative_base_coord----------------
# The parameter pos gets cartesian coordinates (x,y,z,rx,ry,rz)
# Robot moves relatively based on base coordinate
# success : return 0 , fail : return -1
# ex) pos=[0,0,10,0,0,90] robot moves 10 in z-axis direction and turns 90 degrees relative to the z-axis based on base coordinate 
def get_cart_joint_move_relative_base_coord(robot,tool_num ,wobj_num,speed,acceleration,ovl,blendT,pos): 
    eP1=[0.000,0.000,0.000,0.000]
    desc_pos= robot.GetActualTCPPose(0)
    if desc_pos[0]!=0:
        return -1
    joint_pos= robot.GetActualJointPosDegree(0)
    if joint_pos[0]!=0:
        return -1
    robot.MoveJ(joint_pos[1:],desc_pos[1:],tool_num,wobj_num,speed,acceleration,ovl,eP1,blendT,1,pos)
    return 0
#---------------get_cart_linear_move_absolute----------------
# The parameter pos gets cartesian coordinates (x,y,z,rx,ry,rz)
# Robot moves absolutely based on base coordinate
# Robot moves linearly
# success : return 0 , fail : return -1
def get_cart_linear_move_absolute(robot,tool_num ,wobj_num,speed,acceleration,ovl,blendR,pos): 
    eP1=[0.000,0.000,0.000,0.000]
    dP1=[0.000,0.000,0.000,0.000,0.000,0.000]
    ret,output=get_cart_ret_joint_absolute(robot,pos)
    if ret==False:
        return -1
    robot.MoveL(output,pos,tool_num,wobj_num,speed,acceleration,ovl,eP1,blendR,0,0,dP1)
    return 0
#--------------get_joint_linear_move_absolute-----------------
# The parameter pos gets joint position (r1,r2,r3,r4,r5,r6)
# Robot moves absolutely based on base coordinate
# Robot moves linearly
# success : return 0 , fail : return -1
def get_joint_linear_move_absolute(robot,tool_num ,wobj_num,speed,acceleration,ovl,blendR,pos):
    eP1=[0.000,0.000,0.000,0.000]
    dP1=[0.000,0.000,0.000,0.000,0.000,0.000]   
    ret,output=get_joint_ret_cart_absolute(robot,pos)
    if ret==False:
        return -1
    robot.MoveL(pos,output,tool_num,wobj_num,speed,acceleration,ovl,eP1,blendR,0,0,dP1)
    return 0
#--------------get_cart_linear_move_relative_tool_coord-----------------
# The parameter pos gets cartesian coordinates (x,y,z,rx,ry,rz)
# Robot moves relatively based on tool coordinate
# Robot moves linearly
# success : return 0 , fail : return -1
def get_cart_linear_move_relative_tool_coord(robot,tool_num ,wobj_num,speed,acceleration,ovl,blendR,pos): 
    eP1=[0.000,0.000,0.000,0.000]
    desc_pos= robot.GetActualTCPPose(0)
    if desc_pos[0]!=0:
        return -1
    joint_pos= robot.GetActualJointPosDegree(0)
    if desc_pos[0]!=0:
        return -1
    robot.MoveL(joint_pos[1:],desc_pos[1:],tool_num,wobj_num,speed,acceleration,ovl,eP1,blendR,0,2,pos)
    return 0
#--------------get_cart_linear_move_relative_base_coord-----------------
# The parameter pos gets cartesian coordinates (x,y,z,rx,ry,rz)
# Robot moves relatively based on base coordinate
# Robot moves linearly
# success : return 0 , fail : return -1
def get_cart_linear_move_relative_base_coord(robot,tool_num ,wobj_num,speed,acceleration,ovl,blendR,pos): 
    eP1=[0.000,0.000,0.000,0.000]
    desc_pos= robot.GetActualTCPPose(0)
    if desc_pos[0]!=0:
        return -1
    joint_pos= robot.GetActualJointPosDegree(0)
    if desc_pos[0]!=0:
        return -1
    robot.MoveL(joint_pos[1:],desc_pos[1:],tool_num,wobj_num,speed,acceleration,ovl,eP1,blendR,0,1,pos)
    return 0
#--------------wait_until_robot_finished-----------------
#Wait until robot is stopped
def wait_until_robot_finished(robot):
    time.sleep(0.5)
    try:
        past=robot.GetProgramState()[1]
    except:
        past=1
    while True:
        try:
            current=robot.GetProgramState()[1]
        except:
            current=past
        if (past!=1 and current==1) or (past==1 and current==1):
            print("program is finished")
            robot.Mode(1) # turn to the manual mode
            break
        past=current
        time.sleep(0.5)

def program_start(robot, robot_mode, robot_speed, robot_name):
    if robot_mode == 'auto':
        robot.Mode(0)
    elif robot_mode == 'manual':
        robot.Mode(1)
    robot.SetSpeed(robot_speed)
    robot.ProgramLoad('/fruser/%d.lua' % robot_name)
    robot.ProgramRun()
    wait_until_robot_finished(robot)