import time
import numpy as np
import pandas as pd

from plc_com import plc_slmp

## communication message
MSG_READY = 0
MSG_TRIGGER = 1
MSG_PROG_START = 2
MSG_PROG_STOP = 3
MSG_DETECTED = 4
MSG_NOTHING = 5
MSG_DONE = 6

# PLC command
COMM1 = 'open'
COMM2 = 'close'
COMM3 = 'up'
COMM4 = 'down'
COMM5 = 'release'
COMM6 = 'hold'
COMM7 = 'grip'
COMM8 = 'ungrip'

UP = [0, 0, 0.050, 0, 0, 0]

# Excute Move
p1="tray-1-pick"
po1="tray-1-out"
p2="tray-2-pick"
po2="tray-2-out"
p3="tray-3-pick"
po3="tray-3-out"
p4="tray-4-pick"
po4="tray-4-out"
p5="tray-5-pick"
po5="tray-5-out"
p6="tray-6-pick"
po6="tray-6-out"
p7="tray-7-pick"
po7="tray-7-out"
p8="tray-8-pick"
po8="tray-8-out"

def indy_task(config, conn):
    from indy_utils import indydcp_client as client

    ## Robot info
    robot_ip = config['sub_robot']['robot_ip']
    robot_name = config['sub_robot']['robot_name']
    indy = client.IndyDCPClient(robot_ip, robot_name)

    J_VEL = config['sub_robot']['joint_vel']
    T_VEL = config['sub_robot']['task_vel']
    CALIXYZ = config['sub_robot']['cali']
    OFFSET = config['sub_robot']['offset']

    MODE = 1 # 실제 정식동작: 1, 전시회 버전(정식X, 모션만): 9

    #PLC Ref
    fx5u = plc_slmp(config, 1)

    indy.connect()
    indy.set_joint_vel_level(J_VEL)
    indy.set_task_vel_level(T_VEL)

    # 로봇의 현재 상태 확인
    status = indy.get_robot_status()
    print('Sub Robot status:', status)
    if list(status.values()) == [1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0]:
        print('Sub robot is ready')
        conn.send(MSG_READY)
        if MODE == 1:
            while True: # 루프 시작
                
                sv_list = ['line1']
                j_list = [p1,p2,p3,p4,p5,p6,p7,p8]
                jo_list = [po1,po2,po3,po4,po5,po6,po7,po8]

                for i in sv_list: # 라인 반복
                    fx5u.servo_pos(i)
                    for jp, jop in zip(j_list, jo_list): # j_list: # pick 반복
                        print("sub/In:",jp,"Out:", jop)
                        ##AGV 신호 필요
                        while True:
                            msg = conn.recv()
                            print('Sub Robot received msg data: ',msg)
                            if msg == MSG_PROG_START:
                                print('Sub Robot recv OK')
                                ## 추가 할 부분
                                ## IO initializing
                                
                                fx5u.M_IO(COMM8)
                                time.sleep(0.5)
                                
                                ## pick seedling
                                indy.go_home()
                                indy.wait_for_move_finish()
                                # pick move 1
                                indy.set_default_program(8)
                                print("Current default program index: ", indy.get_default_program_idx())
                                print("Start the loaded default program")
                                indy.execute_move(jp)
                                indy.wait_for_move_finish()
                                
                                # pick command
                                fx5u.M_IO(COMM7)
                                # time.sleep(0.5)
                                
                                # pick out 1
                                indy.execute_move(jop)
                                indy.wait_for_move_finish()

                                msg = conn.recv()
                                if msg == MSG_DONE:
                                    msg = conn.recv()
                                    print('Sub Robot received msg data: ', msg)
                                    obj_pos = msg
                                    dxyz = obj_pos @ CALIXYZ
                                    print('Sub/CALIXYZ:',CALIXYZ, 'dxyz: ', dxyz)
                                    if dxyz[2] < OFFSET: # safety offset
                                        print('dz error: ', dxyz[2])
                                        dxyz[2] = OFFSET
                                    dxy = np.append(dxyz[0:2], [0, 0, 0, 0], axis=0) # 촬영 위치로부터 이동해야 할 xy 상대 task 좌표
                                    dz = [0, 0, float(dxyz[2]) + 0.010, 0, 0, 0] # 촬영 위치로부터 이동해야 할 z 상대 task 좌표
                                    print("sub dxy=",dxy,"sub dz=",dz)

                                    # xy 상대 좌표 이동
                                    indy.task_move_by(dxy)
                                    indy.wait_for_move_finish()

                                    # z축 상대 이동
                                    indy.task_move_by(dz)
                                    indy.wait_for_move_finish()

                                    fx5u.M_IO(COMM8)
                                    # time.sleep(0.5)

                                    ## 로봇 이동
                                    indy.task_move_by(UP)
                                    indy.wait_for_move_finish()
                                    indy.go_home()
                                    indy.wait_for_move_finish()

                                    ## 추가 할 부분
                                    ## move to next position

                                    conn.send(MSG_DONE)
                                    print("Sub cycle finish")


                                elif msg == MSG_PROG_STOP:
                                    print("sub break???")
                                    indy.go_home()
                                    indy.wait_for_move_finish()
                                # break # AGV이동시 삭제
                                print("sub break1")
                                break
                            print("sub break2")
                break
            print("All break")
            
        elif MODE == 9: #test 전시회 버전
            while True: # 루프 시작
                
                sv_list = ['line1']
                # j_list = [p1,p2,p3,p4,p5,p6,p7,p8]
                # jo_list = [po1,po2,po3,po4,po5,po6,po7,po8]
                j_test = [p1]
                jo_test = [po1]

                for i in sv_list: # 라인 반복         ##현재 잠시 생략
                    fx5u.servo_pos(i)
                    for jp, jop in zip(j_test, jo_test): # j_list: # pick 반복
                        print("Sub/In:",jp,"Out:", jop)
                        ##AGV 신호 필요
                        while True:
                            msg = conn.recv()
                            print('Sub Robot received msg data: ',msg)
                            if msg == MSG_PROG_START:
                                print('Sub Robot recv OK')
                                ## 추가 할 부분
                                ## IO initializing
                                
                                # fx5u.M_IO(COMM8)
                                # time.sleep(0.5)
                                
                                # for i in sv_list: # 라인 반복         ##현재 잠시 생략
                                #     fx5u.servo_pos(i)
                                #     # fx5u.M_IO(COMM3)
                                
                                ## pick seedling
                                indy.go_home()
                                indy.wait_for_move_finish()
                                # pick move 1
                                indy.set_default_program(2)
                                print("Current default program index: ", indy.get_default_program_idx())
                                print("Start the loaded default program")
                                indy.execute_move(jp)
                                indy.wait_for_move_finish()
                                
                                # pick command
                                # fx5u.M_IO(COMM7)
                                # time.sleep(0.5)
                                
                                # pick out 1
                                indy.execute_move(jop)
                                indy.wait_for_move_finish()

                                msg = conn.recv()
                                if msg == MSG_DONE:
                                    msg = conn.recv()
                                    print('Sub Robot received msg data: ', msg)
                                    obj_pos = msg
                                    dxyz = obj_pos @ CALIXYZ
                                    print('Sub/CALIXYZ:',CALIXYZ, 'dxyz: ', dxyz)
                                    if dxyz[2] < OFFSET: # safety offset
                                        print('dz error: ', dxyz[2])
                                        dxyz[2] = OFFSET
                                    dxy = np.append(dxyz[0:2], [0, 0, 0, 0], axis=0) # 촬영 위치로부터 이동해야 할 xy 상대 task 좌표
                                    dz = [0, 0, float(dxyz[2]) + 0.010, 0, 0, 0] # 촬영 위치로부터 이동해야 할 z 상대 task 좌표

                                    # xy 상대 좌표 이동
                                    indy.task_move_by(dxy)
                                    indy.wait_for_move_finish()

                                    # z축 상대 이동
                                    indy.task_move_by(dz)
                                    indy.wait_for_move_finish()

                                    # fx5u.M_IO(COMM8)
                                    # time.sleep(0.5)

                                    ## 로봇 이동
                                    indy.go_home()
                                    indy.wait_for_move_finish()

                                    ## 추가 할 부분
                                    ## move to next position

                                    conn.send(MSG_DONE)
                                    print("Sub cycle finish")

                                    # fx5u.M_IO(COMM4)          ##현재 잠시 생략
                                    # i=i+1 # servo for문 +1
                                    # print("cycle finish")

                                elif msg == MSG_PROG_STOP:
                                    indy.go_home()
                                    indy.wait_for_move_finish()
                                # break # AGV이동시 삭제
                                break
                            print("break")


    else:
        print('Sub Robot / please check robot status')

    indy.disconnect()
    conn.close()