import time
import numpy as np
import pandas as pd
import socket

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

# Task POS R
DIG_DOWN = [0, 0, -0.010, 0, 0, 0] # 단위 m(미터)
DIG_UP = [0, 0, 0.200, 0, 0, 0]

from plc_com import plc_slmp

def indy_task(config, conn1, conn2):
    from indy_utils import indydcp_client as client

    ## PLC connect
    fx5u = plc_slmp(config, 0)

    # ## AGV Connect
    # # 호스트와 포트 설정
    # host = '192.168.0.7'  # 서버의 IP 주소
    # # host = '172.20.10.13'
    # port = 23450       # 사용할 포트 번호

    # # 소켓 생성
    # server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # # 소켓을 지정된 호스트와 포트에 바인딩
    # server_socket.connect((host, port))


    ## Robot info
    robot_ip = config['main_robot']['robot_ip']
    robot_name = config['main_robot']['robot_name']
    indy = client.IndyDCPClient(robot_ip, robot_name)

    J_VEL = config['main_robot']['joint_vel']
    T_VEL = config['main_robot']['task_vel']
    CALIXYZ = config['main_robot']['cali']
    OFFSET = config['main_robot']['offset']

    indy.connect()
    indy.set_joint_vel_level(J_VEL)
    indy.set_task_vel_level(T_VEL)

    # 로봇의 현재 상태 확인
    status = indy.get_robot_status()
    print('Main Robot status:', status)
    if list(status.values()) == [1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0]:
        print('Main robot is ready')

        cam_data = conn2.recv()
        print('Main Robot received cam data: ', cam_data)
        sub_data = conn1.recv()
        print('Main Robot received sub data: ', sub_data)
        if cam_data == MSG_READY & sub_data == MSG_READY:
            print('Main system is ready')
            print('program start')
            fx5u.bit_write('M100', [0])                         #
            time.sleep(0.2)                                     #

            while True: # 루프 시작
                # ##AGV 신호 필요
                # while True:
                #     message_to_send_input = 'Start'
                #     server_socket.send(message_to_send_input.encode())
                #     time.sleep(0.3)
                #     data = server_socket.recv(1024).decode()
                #     d_start = data[-1]
                #     # print(data[-1])
                #     if d_start=='Y':
                #         print(f"서버로부터 받은 메시지: {data[-1]}")
                #         AGV_START = 'Y' # 임시 AGV 신호
                #         break
                #     else:
                #         # print(data[-1],'!')
                #         time.sleep(0.1)
                #         continue

                #-------임시 비트------------------------------------#
                # fx5u.bit_write('M100', [1])                         #
                # time.sleep(0.5)                                     #
                START = fx5u.bit_read('M100', 1) # 임시 AGV 신호 #
                # print(START)
                if START == [1]:
                    AGV_START = 'Y'
                    break

                #-------임시 비트------------------------------------#

            if AGV_START == 'Y':
                fx5u.bit_write('M100', [0])
                print('AGV Start')
                fx5u.M_IO(COMM2)
                # fx5u.servo_pos('line1')
                conn1.send(MSG_PROG_START)
                print('send OK')

                ## go to snapshot point
                SNAPSHOT = [0.6550484649406423, -38.33847172004385, -62.35944259265649, -0.07309715346535135, -78.06003683864995, 91.5647359413736] # joint pos
                indy.joint_move_to(SNAPSHOT)
                indy.wait_for_move_finish()
                time.sleep(1)

                # -------AGV 이동 명령-------
                # # Message to Send """AGR/GO/99(Go) AGR/GO/0(Stop) AGR/GO/(음수)(Back)"""
                # message_to_send = 'AGR/GO/40'
                # server_socket.send(message_to_send.encode())

                # while True:
                #     criterion = 150 ## 거리 설정
                #     conn2.send(MSG_TRIGGER)
                #     cam_data = conn2.recv()
                #     print('Main Robot received cam data: ', cam_data)
                #     if cam_data == MSG_DETECTED:
                #         cam_data = conn2.recv()
                #         min_dist = conn2.recv()
                #         next_dist = conn2.recv()
                #         print('min dist: ', min_dist)
                #         if min_dist < criterion:
                #             message_to_send = 'AGR/GO/0'
                #             server_socket.send(message_to_send.encode())
                #             time.sleep(1)
                #             if min_dist > criterion:
                #                 min_cal = min_dist - criterion + 15
                #                 message_to_send = f'AGR/GO/{min_cal}'
                #                 server_socket.send(message_to_send.encode())
                #             break

                while True:
                    conn2.send(MSG_TRIGGER)
                    cam_data = conn2.recv()
                    print('Main Robot received cam data: ', cam_data)

                    if cam_data == MSG_DETECTED:
                        cam_data = conn2.recv()
                        min_dist = conn2.recv() # AGV
                        next_dist = conn2.recv()
                        print('Main Robot received cam_data: ', cam_data)
                        print('Main Robot received next_dist: ', next_dist)
                        if next_dist < 18:
                            next_dist = 18
                            print('New next_dist: ', next_dist)

                        obj_pos = cam_data
                        obj_pos = np.append(obj_pos, [1], axis=0)
                        dxyz = obj_pos @ CALIXYZ
                        print('Main/CALIXYZ:',CALIXYZ, 'dxyz: ', dxyz)
                        print('dxy: ', dxyz[0],',',dxyz[1])
                        print('dz: ', dxyz[2])
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

                        # 땅 파기
                        fx5u.M_IO(COMM1)
                        fx5u.M_IO(COMM2)
                        indy.task_move_by(DIG_DOWN)
                        indy.wait_for_move_finish()
                        fx5u.M_IO(COMM1)
                        fx5u.M_IO(COMM2)
                        indy.task_move_by(DIG_DOWN)
                        indy.wait_for_move_finish()
                        fx5u.M_IO(COMM1)

                        conn1.send(MSG_DONE)
                        conn1.send(obj_pos)

                        sub_data = conn1.recv()
                        if sub_data == MSG_DONE:
                            indy.task_move_by(DIG_UP)
                            indy.wait_for_move_finish()
                            indy.go_home()
                            indy.wait_for_move_finish() ## AGV 신호 적용 시 적용
                            break ## AGV 신호 적용 후 삭제
                        # time.sleep(0.5) 
                        
                        # # Message to Send """AGR/GO/99(Go) AGR/GO/0(Stop) AGR/GO/(음수)(Back)"""
                        # message_to_send = 'AGR/GO/99'
                        # server_socket.send(message_to_send.encode())
                        # time.sleep(6)

                        # indy.joint_move_to(SNAPSHOT)
                        # indy.wait_for_move_finish()
                        # time.sleep(1)
                        # while True:
                        #     criterion = 77 ## 거리 설정
                        #     conn2.send(MSG_TRIGGER)
                        #     cam_data = conn2.recv()
                        #     print('Main Robot received cam data: ', cam_data)
                        #     if cam_data == MSG_DETECTED:
                        #         cam_data = conn2.recv()
                        #         min_dist = conn2.recv()
                        #         next_dist = conn2.recv()
                        #         if min_dist < criterion:
                        #             message_to_send = 'AGR/GO/0'
                        #             server_socket.send(message_to_send.encode())
                        #             if min_dist > criterion:
                        #                 min_cal = min_dist - criterion + 15
                        #                 message_to_send = f'AGR/GO/{min_cal}'
                        #                 server_socket.send(message_to_send.encode())
                        #             break
                    
                        # message_to_send = f'AGR/GO/{next_dist}'
                        # server_socket.send(message_to_send.encode())
                        # time.sleep(6)

                    elif cam_data == MSG_NOTHING:
                        pass

            # indy.wait_for_move_finish() ## AGV 신호 적용 후 삭제

        else:
            print('Main Robot / please check cam')

    else:
        print('Main Robot / please check robot status')

    print('니가 왜 여기에......')
    conn1.send(MSG_PROG_STOP)
    conn2.send(MSG_PROG_STOP)
    print('program stop')
    indy.disconnect()
    fx5u.close()
    conn1.close()
    conn2.close()