import time
import numpy as np
import pandas as pd

## communication message
MSG_CAM_READY = 0
MSG_TRIGGER = 1
MSG_PROG_STOP = 2
MSG_DETECTED = 3
MSG_NOTHING = 4

THRES = 150 # 버섯 간의 최소 거리


def indy_task(conn):
    from indy_utils import indydcp_client as client

    # Calibration
    # xy 변환 계수 (calib에서 계산된 c의 값을 여기에 입력)
    CALIXY =np.array([
                [0.001, 0],
                [0, -0.001],
                [0.032, 0.120]
                ])
    # z 변환 계수 (calib에서 계산된 dz의 값을 여기에 입력)
    CALIZ = [-0.001, 0.162] 

    # Joint Absolute
    # J_HOME = [-35.475080505877855, 4.988428541451775, -116.84790745255161, -3.9359336324260017, -66.96455247331815, 52.93974319307279]
    # J_SNAPSHOT = [-35.475080505877855, 4.988428541451775, -116.84790745255161, -3.9359336324260017, -66.96455247331815, 52.93974319307279]

    # Joint Relative

    # Task Absolute
    # T_SNAPSHOT = [0.12409614611516706, -0.3346026287736437, 0.4021447276175354, -178.696795466206, 3.5941979489750335, 93.1295902722251]

    # Task Relative
    MOVE_UP = [0, 0, 0.200, 0, 0, 0] # 수직 위 방향으로 이동할 거리(200mm)

    '''----plc 통신----'''
    from plc_communication import plc_commu
    HOST="192.168.0.105"
    PORT=5001
    plc=plc_commu(HOST,PORT)
    '''-------------------------------------'''

    ## Robot info
    robot_ip = "192.168.0.8" # indy 로봇의 IP
    robot_name = "NRMK-Indy7"
    indy = client.IndyDCPClient(robot_ip, robot_name)

    indy.connect()

    # 로봇의 현재 상태 확인
    status = indy.get_robot_status()
    indy.set_joint_vel_level(1)
    indy.set_task_vel_level(1)
    # indy.go_home()
    # indy.wait_for_move_finish()
    print(status)
    
    plc.writebit('M1103',[0])
    plc.writebit('M1102',[1])
    time.sleep(2)
    plc.writebit('M1100',[0])
    plc.writebit('M1101',[1])
    plc.writebit('M1114',[1])
    plc.writebit('M1115',[0])
    plc.writebit('M1116',[0])
    time.sleep(1)
    
    if status['home'] == 1 and status['ready'] == 1 and status['error'] == 0:
        print('robot is ready')
    
        cam_data = conn.recv()
        print('Robot received data: ', cam_data)
        while True:
        ##Left sol M address##
        # Up/Down 실린더 : UP 1101 DOWN 1100
        # In/Out 실린더 : In 1103 Out 1102
        # Pull/Push 실린더 : Pull 1104 Push 1105
        # 바스켓 그립 그리퍼 : Grip 1114 off Ungrip 1114 on
        # Up/Down 그리퍼 : UP 1115 off DOWN 1115 on
        # 니들 그리퍼 : 켜짐 1116 on 꺼짐 1116 off
            plc.writebit('M110',[0])
            print('Please order')
            while True:
                start_recv=plc.readbit("M100",2)
                if start_recv[0]==1:
                    start_prog=0 # Left Start 
                    break   
                elif start_recv[1]==1:
                    start_prog=1 # Right Start
                    break

            if start_prog == 0:
                if cam_data == MSG_CAM_READY:
                    print('cam is ready')
                    
                    ## 스냅샷 위치 이동
                    indy.execute_move('l-snapshot')
                    indy.wait_for_move_finish()

                    conn.send(MSG_TRIGGER)
                    cam_data = conn.recv()
                    print('Robot received data: ', cam_data)
                    
                    if cam_data == MSG_DETECTED:
                        cam_data = conn.recv()
                        print('Robot received data: ', cam_data)
                        df_list = cam_data
                        for idx in df_list.index:
                            print(df_list)
                            indy.execute_move('l-snapshot')
                            indy.wait_for_move_finish()
                            obj_pos = df_list.loc[idx, ['x3d', 'y3d', 'z3d']]
                            pre_pos = np.array(obj_pos[0:2], dtype=float)
                            pre_pos = np.append(pre_pos, [1], axis=0)
                            dxy = pre_pos @ CALIXY
                            ## 촬영 위치로부터 이동해야 할 xy 상대 task 좌표
                            dxy= np.append(dxy,[0,0,0,0],axis=0)
                            dz = [0, 0, float(obj_pos[2]) * CALIZ[0] + CALIZ[1], 0, 0, 0] # 촬영 위치로부터 이동해야 할 z 상대 task 좌표
                            print(dxy)
                            print(dz)
                            ## xy 상대 좌표 이동
                            indy.task_move_by(dxy)
                            indy.wait_for_move_finish()

                            ## 돈까스 위치로 접근
                            indy.task_move_by(dz)
                            indy.wait_for_move_finish()

                            ## 돈까스 잡기
                            plc.writebit("M1116",[1])
                            time.sleep(0.2)

                            ## 돈까스 픽업
                            indy.task_move_by(MOVE_UP)
                            indy.wait_for_move_finish()

                        # indy.go_home()
                        # indy.wait_for_move_finish()
                        

                        ## 돈까스 시퀀스 시작 ##
                        ## 돈까스 내려놓기
                        indy.execute_move('l-don-drop')
                        indy.wait_for_move_finish()
                        plc.writebit('M1116',[0])
                        time.sleep(0.1)
                        
                        ## 로봇 빼서 대기하기
                        indy.execute_move('l-drop-back')
                        indy.wait_for_move_finish()

                        ## 돈까스 튀기기
                        #실린더 down -> in -> timer 5min -> out -> up
                        plc.writebit('M1101',[0])
                        plc.writebit('M1100',[1])
                        time.sleep(2)
                        plc.writebit('M1102',[0])
                        plc.writebit('M1103',[1])
                        time.sleep(180)
                        plc.writebit('M1103',[0])
                        plc.writebit('M1102',[1])
                        time.sleep(2)
                        plc.writebit('M1100',[0])
                        plc.writebit('M1101',[1])
                        time.sleep(30)

                        ## 바스켓 픽업 대기
                        indy.execute_move('l-basket-pick')
                        indy.wait_for_move_finish()

                        ## 바스켓 픽
                        #그리퍼 down -> grip -> 바스켓 pull
                        plc.writebit('M1115',[1])
                        time.sleep(0.2)
                        plc.writebit('M1114',[0])
                        time.sleep(0.5)
                        plc.writebit('M1105',[0])
                        plc.writebit('M1104',[1])
                        time.sleep(1)

                        ## 바스켓 아웃
                        indy.execute_move('l-basket-out')
                        indy.wait_for_move_finish()
                        #실린더 down
                        plc.writebit('M1101',[0])
                        plc.writebit('M1100',[1])
                        time.sleep(1.5)

                        ## 돈까스 배출
                        indy.execute_move('l-don-out')
                        indy.wait_for_move_finish()
                        indy.execute_move('l-dust')
                        indy.wait_for_move_finish()
                        time.sleep(30)

                        ## 바스켓 대기
                        indy.execute_move('l-basket-put-wait')
                        indy.wait_for_move_finish()
                        #실린더 up
                        plc.writebit('M1100',[0])
                        plc.writebit('M1101',[1])
                        time.sleep(2)
                        
                        ## 바스켓 put in
                        indy.execute_move('l-basket-put')
                        indy.wait_for_move_finish()
                        #실린더 push -> ungrip
                        plc.writebit('M1104',[0])
                        plc.writebit('M1105',[1])
                        time.sleep(1)
                        plc.writebit('M1114',[1])
                        time.sleep(0.2)
                        plc.writebit('M1115',[0])
                        time.sleep(0.2)

                        ## 홈 위치 복귀
                        indy.go_home()
                        indy.wait_for_move_finish()
                        plc.writebit('M110',[1])
                        time.sleep(5)

                    else:
                        print('retry snapshot')

                else:
                    print('please check cam')

            elif start_prog == 99 :
                if cam_data == MSG_CAM_READY:
                    print('cam is ready')

                    ## 스냅샷 위치 이동
                    indy.execute_move('r-snapshot')
                    indy.wait_for_move_finish()

                    conn.send(MSG_TRIGGER)
                    cam_data = conn.recv()
                    print('Robot received data: ', cam_data)
                    
                    if cam_data == MSG_DETECTED:
                        cam_data = conn.recv()
                        print('Robot received data: ', cam_data)
                        df_list = cam_data
                        order = df_list.sort_values('order', ascending=True).index
                        for idx in order:
                            indy.execute_move('r-snapshot')
                            indy.wait_for_move_finish()
                            if df_list.loc[idx, 'dist'] > THRES:
                                break
                            obj_pos = df_list.loc[idx, ['X', 'Y', 'z3d']]
                            pre_pos = np.array(obj_pos[0:2], dtype=float)
                            pre_pos = np.append(pre_pos, [1], axis=0)
                            dxy = pre_pos @ CALIXY
                            ## 촬영 위치로부터 이동해야 할 xy 상대 task 좌표
                            dxy= np.append(dxy,[0,0,0,0],axis=0)
                            dz = [0, 0, float(obj_pos[2]) * CALIZ[0] + CALIZ[1], 0, 0, 0] # 촬영 위치로부터 이동해야 할 z 상대 task 좌표

                            ## xy 상대 좌표 이동
                            indy.task_move_by(dxy)
                            indy.wait_for_move_finish()

                            ## 돈까스 위치로 접근
                            indy.task_move_by(dz)
                            indy.wait_for_move_finish()

                            ## 돈까스 잡기
                            plc.writebit("M1116",[1])
                            time.sleep(0.2)

                            ## 돈까스 픽업
                            indy.task_move_by(MOVE_UP)
                            indy.wait_for_move_finish()

                    # indy.go_home()
                    # indy.wait_for_move_finish()
                    conn.send(MSG_PROG_STOP)

                    ## 돈까스 시퀀스 시작 ##
                    ## 돈까스 내려놓기
                    indy.execute_move('r-don-drop')
                    indy.wait_for_move_finish()
                    plc.writebit('M1116',[0])
                    time.sleep(0.1)
                    
                    ## 로봇 빼서 대기하기
                    indy.execute_move('r-drop-back')
                    indy.wait_for_move_finish()

                    ## 돈까스 튀기기
                    #실린더 down -> in -> timer 5min -> out -> up

                    ## 바스켓 픽업 대기
                    indy.execute_move('r-basket-pick')
                    indy.wait_for_move_finish()

                    ## 바스켓 픽
                    #그리퍼 down -> grip -> pull

                    ## 바스켓 아웃
                    indy.execute_move('r-basket-out')
                    indy.wait_for_move_finish()
                    #실린더 down

                    ## 돈까스 배출
                    indy.execute_move('r-don-out')
                    indy.wait_for_move_finish()
                    indy.execute_move('r-dust')
                    indy.wait_for_move_finish()

                    ## 바스켓 대기
                    indy.execute_move('r-basket-put-wait')
                    indy.wait_for_move_finish()
                    #실린더 up
                    
                    ## 바스켓 put in
                    indy.execute_move('r-basket-put')
                    indy.wait_for_move_finish()
                    #실린더 push -> ungrip

                    ## 스냅샷 위치 복귀
                    indy.execute_move('r-go-snapshot')
                    indy.wait_for_move_finish()


                else:
                    print('please check cam')

    else:
        print('please check robot status')

    conn.send(MSG_PROG_STOP)
    print('Robot task stop')
    indy.disconnect()
    conn.close()


def fanuc_task(conn):
    CALIB1=[[  -0.007998  ,  0.91357   ,  0.01892 ], # 고정
    [  -0.836571 ,  -0.018644,   -0.000386], # 고정
    [   0.002375 ,   0.014936  ,  0.984037], # 고정
    [ 124.95368  ,  25.680308, -162.073189]] # X,Y,Z 변경 위치
    CALIB2=[[  -0.007998  ,  0.91357   ,  0.01892 ], # 미사용
    [  -0.836571 ,  -0.018644,   -0.000386], # 미사용
    [   0.002375 ,   0.014936  ,  0.984037], # 미사용
    [ 127.95368  ,  -30.680308, -170.073189]] # 미사용
    '''---- fanuc 통신----'''
    from fanac_commu import fanuc_pos, POS, PROG_STAT, ALM
    HOST = '192.168.0.223'
    PORT = 502
    POS1 = {'addr': 0, 'keys': POS.columns}
    XYZ = POS.columns[0:6]
    PR1 = {'addr': 50, 'keys': XYZ}
    STAT1 = {'addr': 100, 'keys': PROG_STAT.columns}
    ALM1 = {'addr': 150, 'keys': ALM.columns}


    TRIG_CUSTOMXYZSLOW= {'addr': 350, 'values': np.array([1, 0, 0, 0, 0, 0, 0], np.int16)} #move to pr[1]   # R[131]
    TRIG_CUSTOMXYZFAST= {'addr': 350, 'values': np.array([0, 1, 0, 0, 0, 0, 0], np.int16)}                  # R[132]
    TRIG_CUSTOM1= {'addr': 350, 'values': np.array([0, 0, 1, 0, 0, 0, 0], np.int16)}    # Right_1           # R[133]
    TRIG_CUSTOM2= {'addr': 350, 'values': np.array([0, 0, 0, 1, 0, 0, 0], np.int16)}    # Right_2           # R[134]
    TRIG_CUSTOM3= {'addr': 350, 'values': np.array([0, 0, 0, 0, 1, 0, 0], np.int16)}    # Left_1            # R[135]
    TRIG_CUSTOM4= {'addr': 350, 'values': np.array([0, 0, 0, 0, 0, 1, 0], np.int16)}    # Left_2            # R[136]
    TRIG_ALL_RESET={'addr': 350, 'values': np.array([0, 0, 0, 0, 0, 0, 0], np.int16)}
    TRIG_INITIAL = {'addr': 250, 'values': np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], np.int16)} #initialize register 
    TRIG_PORKGRAB= {'addr': 250, 'values': np.array([0, 0, 0, 0, 1, 0, 0, 0, 0, 0], np.int16)} # ROBOTio [4]             R[105]
    TRIG_UPDOWN= {'addr':250, 'values':np.array([0, 0, 0, 0, 0, 1, 0, 0, 0, 0], np.int16)} # ROBOTio [5]                 R[106]
    TRIG_BASKETGRAB= {'addr':250, 'values':np.array([0, 0, 0, 0, 0, 0, 1, 0, 0, 0], np.int16)} # ROBOTio [6]             R[107]
    TRIG_RIGHTUPDOWN= {'addr':250, 'values':np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0], np.int16)} # ROBOTio [7]  R[108]
    TRIG_RIGHTINOUT= {'addr':250, 'values':np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 0], np.int16)} # ROBOTio [8]    R[109]
    TRIG_RIGHTPULLPUSH= {'addr':250, 'values':np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1], np.int16)} # ROBOTio [9] R[110]
    PORK_NUM={'addr': 380, 'values': np.array([0], np.int16)}     #R[171]
    START_TRIG= {'addr': 300, 'values': np.array([0], np.int16)}  #R[151]
    PLC_TRIG={'addr': 400, 'values': np.array([1], np.int16)}     #R[161]
    '''----------------------------------------------------'''

    '''----plc 통신----'''
    from plc_communication import plc_commu
    PLCHOST = '192.168.0.105'
    PLCPORT = 5001
    '''-------------------------------------'''
    fanuc=fanuc_pos(HOST,PORT)
    plc=plc_commu(PLCHOST,PLCPORT)
    fanuc.write_registers(TRIG_INITIAL)
    fanuc.write_registers(START_TRIG)
    fanuc.write_registers(TRIG_ALL_RESET)
    fanuc.write_registers(PORK_NUM)
    plc.writebit("M100",[0,0])
    print("press start button")
    while True:
        start_signal=fanuc.read_registers(START_TRIG,print_=False)
        if start_signal==[1]:
            print("start robot task")
            start_signal=fanuc.write_registers(START_TRIG)
            break
        time.sleep(0.1)
    cam_data = conn.recv()
    print('Robot received data: ', cam_data)
    while True:
        while True:
        # 그리퍼 켜짐 1102: 1103: close
        # 1100 꺼지면 up
        #미쓰비씨 확인
        #그리고 끄기
            recv=plc.readbit("M100",2)
            if recv[0]==1:
                recv_d=0 
                break   
            elif recv[1]==1:
                recv_d=1
                break
        if recv_d==0:
            plc.writebit("M1114",[0])
            plc.writebit("M1115",[0])
            plc.writebit("M1116",[0])
            # plc.writebit("M1107",[0])
            # plc.writebit("M1106",[1])
            current_state=fanuc.read_registers(TRIG_INITIAL,print_=True)
            # current_state[4]= 1
            fanuc.move_to_prog(TRIG_CUSTOM1,{'addr':250, 'values':np.array(current_state, np.int16)})
            IOcontrol(fanuc,START_TRIG,TRIG_INITIAL,plc,current_state,PLC_TRIG)

            for i in range(2): # 반복 동작 시 사용
                conn.send(MSG_TRIGGER)
                conn.send(0)

                cam_data = conn.recv()
                print('Robot received data: ', cam_data)
                if cam_data == MSG_DETECTED:
                    cam_data = conn.recv()
                    print('Robot received data: ', cam_data)
                    df_ins=cam_data
                    # df_ins.drop(df_ins[(df_ins['X']<791)].index, inplace=True)
                    if df_ins.empty:
                        print("empty")
                        continue
                    df_ins.reset_index(drop=True,inplace=True)
                    df_ins.sort_values('size',ascending=False)
                    [dx,dy,dz]=df_ins.loc[0,['x3d','y3d','z3d']]
                    if np.all([[dx,dy,dz],[0,0,0]]):
                        plc.writebit("M100",[0,0])
                        continue
                    print('1')
                    print([dx,dy,dz])
                    
                    dxyz=np.array([dx,dy,dz,1]) @ CALIB1
                    print(dxyz)
                    print("2")
                    fanuc.move_by([dxyz[0],dxyz[1],0],POS1,PR1,TRIG_CUSTOMXYZFAST)
                    fanuc.wait_for_finish(START_TRIG)

                    fanuc.move_by([0,0,dxyz[2]-50],POS1,PR1,TRIG_CUSTOMXYZFAST)
                    fanuc.wait_for_finish(START_TRIG)

                    fanuc.move_by([0, 0, 50],POS1,PR1,TRIG_CUSTOMXYZSLOW)
                    fanuc.wait_for_finish(START_TRIG)
                    time.sleep(0.1)

                    plc.writebit("M1116",[1])

                    time.sleep(0.3)
                    #--이줄에 도구 입력

                    fanuc.move_by([0, 0, -100],POS1,PR1,TRIG_CUSTOMXYZFAST)
                    fanuc.wait_for_finish(START_TRIG)
                    current_state=fanuc.read_registers(TRIG_INITIAL,print_=True)
                    current_state[4]=1
                    current_state[7]=1     
                    fanuc.write_registers({'addr': 380, 'values': np.array([i], np.int16)} )   # 반복 동작 시 사용       
                    fanuc.move_to_prog(TRIG_CUSTOM2,{'addr':250, 'values':np.array(current_state, np.int16)})
                    IOcontrol(fanuc,START_TRIG,TRIG_INITIAL,plc,current_state,PLC_TRIG)
                    print("____________")

                else: # 반복 동작 시 사용
                    print("444444444444")
                    current_state=fanuc.read_registers(TRIG_INITIAL,print_=True)
                    current_state[7]=1
                    fanuc.write_registers({'addr': 380, 'values': np.array([4], np.int16)} )          
                    fanuc.move_to_prog(TRIG_CUSTOM2,{'addr':250, 'values':np.array(current_state, np.int16)})
                    IOcontrol(fanuc,START_TRIG,TRIG_INITIAL,plc,current_state,PLC_TRIG)
                
        elif recv_d==1:
            cnt=0
            while cnt<=1:
                conn.send(MSG_TRIGGER)
                conn.send(0)
                cam_data = conn.recv()
                print('Robot received data: ', cam_data)
                if cam_data == MSG_DETECTED:
                    cam_data = conn.recv()
                    print('Robot received data: ', cam_data)
                    df_ins=cam_data
                    df_ins.drop(df_ins[(df_ins['X']>791)].index, inplace=True)
                    if df_ins.empty:
                        continue
                    df_ins.reset_index(drop=True,inplace=True)
                    df_ins.sort_values('size',ascending=False)
                    [dx,dy,dz]=df_ins.loc[0,['x3d','y3d','z3d']]
                    if np.all([[dx,dy,dz],[0,0,0]]):
                        plc.writebit("M100",[0,0])
                        continue
                    
                    print([dx,dy,dz])
                    dxyz=np.array([dx,dy,dz,1]) @ CALIB2
                    movepoint=[[64,-756,240,0,-8,0],[-40,-695,240,0,-8,0]]
                    fanuc.move_by([dxyz[0],dxyz[1],0],POS1,PR1,TRIG_CUSTOMXYZFAST)
                    fanuc.wait_for_finish(START_TRIG)

                    fanuc.move_by([0,0,dxyz[2]-50],POS1,PR1,TRIG_CUSTOMXYZFAST)
                    fanuc.wait_for_finish(START_TRIG)

                    fanuc.move_by([0, 0, 50],POS1,PR1,TRIG_CUSTOMXYZSLOW)
                    fanuc.wait_for_finish(START_TRIG)
                    time.sleep(0.1)
                    plc.writebit("M1102",[0,1])
                    plc.writebit("M1110",[0,0])
                    time.sleep(0.3)
                    #--이줄에 도구 입력
                    fanuc.move_by([0, 0, -100],POS1,PR1,TRIG_CUSTOMXYZFAST)
                    fanuc.wait_for_finish(START_TRIG)
                    
                    fanuc.move_to([7,-684,-156],POS1,PR1,TRIG_CUSTOMXYZFAST)
                    fanuc.wait_for_finish(START_TRIG)

                    fanuc.move_to_angle(movepoint[cnt],POS1,PR1,TRIG_CUSTOMXYZFAST)
                    fanuc.wait_for_finish(START_TRIG)

                    time.sleep(0.1)
                    plc.writebit("M1102",[1,1])
                    plc.writebit("M1110",[1,1])
                    time.sleep(0.3)
                    if cnt==0:
                        fanuc.move_to_angle([7,-684,-156,0,0,0],POS1,PR1,TRIG_CUSTOMXYZFAST)
                        fanuc.wait_for_finish(START_TRIG)

                        fanuc.move_to_angle([-22,-85,-242,0,0,0],POS1,PR1,TRIG_CUSTOMXYZFAST)
                        fanuc.wait_for_finish(START_TRIG)

                    cnt+=1

                    
            current_state=fanuc.read_registers(TRIG_INITIAL,print_=True)
            current_state[2]=1
            fanuc.move_to_prog({'addr':250, 'values':np.array(current_state, np.int16)})
            IOcontrol(fanuc,START_TRIG,TRIG_INITIAL,plc,current_state,PLC_TRIG)
        plc.writebit("M100",[0,0])            
        time.sleep(1)
        
    conn.send(MSG_PROG_STOP)
    print('Robot task stop')
    conn.close()

def IOcontrol(fanuc,START_TRIG,TRIG_INITIAL,plc,current_state,PLC_TRIG):
    print("IOcontrol")
    while True:
        ROBOTio=fanuc.read_registers(TRIG_INITIAL,print_=False)
        if ROBOTio[4]!=current_state[4]:
            current_state[4]=ROBOTio[4]
            if ROBOTio[4]==1: # REG(105)
                plc.writebit("M1116",[1])
                fanuc.write_registers(PLC_TRIG)
            elif ROBOTio[4]==0:
                plc.writebit("M1116",[0])
                fanuc.write_registers(PLC_TRIG)
            else: print("error in IO")

        if ROBOTio[5]!=current_state[5]:
            current_state[5]=ROBOTio[5]
            if ROBOTio[5]==1: # REG(106)
                plc.writebit("M1115",[1])
                fanuc.write_registers(PLC_TRIG)
            elif ROBOTio[5]==0:
                plc.writebit("M1115",[0])
                fanuc.write_registers(PLC_TRIG)
            else: print("error in IO")

        if ROBOTio[6]!=current_state[6]:
            current_state[6]=ROBOTio[6]
            if ROBOTio[6]==1: # REG(107)
                plc.writebit("M1114",[1])
                fanuc.write_registers(PLC_TRIG)
            elif ROBOTio[6]==0:
                plc.writebit("M1114",[0])
                fanuc.write_registers(PLC_TRIG)
            else: print("error in IO")

        if ROBOTio[7]!=current_state[7]:
            current_state[7]=ROBOTio[7]
            if ROBOTio[7]==1: # REG(108)
                plc.writebit("M1106",[0])
                plc.writebit("M1107",[1])
                fanuc.write_registers(PLC_TRIG)
            elif ROBOTio[7]==0:
                plc.writebit("M1107",[0])
                plc.writebit("M1106",[1])
                fanuc.write_registers(PLC_TRIG)
            else: print("error in IO")   

        if ROBOTio[8]!=current_state[8]:
            current_state[8]=ROBOTio[8]
            if ROBOTio[8]==1: # REG(109)
                plc.writebit("M1110",[0])
                plc.writebit("M1111",[1])
                fanuc.write_registers(PLC_TRIG)
            elif ROBOTio[8]==0:
                plc.writebit("M1111",[0])
                plc.writebit("M1110",[1])
                fanuc.write_registers(PLC_TRIG)
            else: print("error in IO")  

        if ROBOTio[9]!=current_state[9]:
            current_state[9]=ROBOTio[9]
            if ROBOTio[9]==1: # REG(110)
                plc.writebit("M1112",[0])
                plc.writebit("M1113",[1])
                fanuc.write_registers(PLC_TRIG)
            elif ROBOTio[9]==0:
                plc.writebit("M1113",[0])
                plc.writebit("M1112",[1])
                fanuc.write_registers(PLC_TRIG)
            else: print("error in IO")       
        if fanuc.check_finish(START_TRIG)==1:
            print("out")
            break

if __name__ == '__main__':
    import time
    import pymcprotocol
    from indy_utils import indydcp_client as client 

    
    '''----plc 통신----'''
    from plc_communication import plc_commu
    HOST="192.168.0.105"
    PORT=5001
    plc=plc_commu(HOST,PORT)
    '''-------------------------------------'''

    ## Robot info
    robot_ip = "192.168.0.8" # indy 로봇의 IP
    robot_name = "NRMK-Indy7"
    indy = client.IndyDCPClient(robot_ip, robot_name)

    indy.connect()

    # indy.execute_move('l-snapshot')
    # indy.wait_for_move_finish()

    # # 로봇의 현재 상태 확인
    # status = indy.get_robot_status()
    # indy.set_joint_vel_level(1)
    # indy.set_task_vel_level(1)
    # indy.go_home()
    # indy.wait_for_move_finish()
    # plc.writebit('M1100',[0])
    # plc.writebit('M1101',[1])
    # plc.writebit('M1114',[1])
    # plc.writebit('M1115',[0])
    # plc.writebit('M1116',[1])
    # time.sleep(1)
    # print(status)
    
    # if status['home'] == 1 and status['ready'] == 1 and status['error'] == 0:
    #     print('robot is ready')

    #     ## 돈까스 시퀀스 시작 ##
    #     ## 돈까스 내려놓기
    #     indy.execute_move('l-don-drop')
    #     indy.wait_for_move_finish()
    #     plc.writebit('M1116',[0])
    #     time.sleep(0.1)
        
    #     ## 로봇 빼서 대기하기
    #     indy.execute_move('l-drop-back')
    #     indy.wait_for_move_finish()

    #     ## 돈까스 튀기기
    #     #실린더 down -> in -> timer 5min -> out -> up
    #     plc.writebit('M1101',[0])
    #     plc.writebit('M1100',[1])
    #     time.sleep(2)
    #     plc.writebit('M1102',[0])
    #     plc.writebit('M1103',[1])
    #     time.sleep(10)
    #     plc.writebit('M1103',[0])
    #     plc.writebit('M1102',[1])
    #     time.sleep(0.5)
    #     plc.writebit('M1100',[0])
    #     plc.writebit('M1101',[1])
    #     time.sleep(2)

    ## 바스켓 픽업 대기
    indy.execute_move('l-basket-pick')
    indy.wait_for_move_finish()

    ## 바스켓 픽
    #그리퍼 down -> grip -> 바스켓 pull
    plc.writebit('M1115',[1])
    time.sleep(0.2)
    plc.writebit('M1114',[0])
    time.sleep(0.2)
    plc.writebit('M1105',[0])
    plc.writebit('M1104',[1])
    time.sleep(0.2)

    ## 바스켓 아웃
    indy.execute_move('l-basket-out')
    indy.wait_for_move_finish()
    #실린더 down
    plc.writebit('M1101',[0])
    plc.writebit('M1100',[1])
    time.sleep(2)

    ## 돈까스 배출
    indy.execute_move('l-don-out')
    indy.wait_for_move_finish()
    indy.execute_move('l-dust')
    indy.wait_for_move_finish()

    ## 바스켓 대기
    indy.execute_move('l-basket-put-wait')
    indy.wait_for_move_finish()
    #실린더 up
    plc.writebit('M1100',[0])
    plc.writebit('M1101',[1])
    time.sleep(2)
    
    ## 바스켓 put in
    indy.execute_move('l-basket-put')
    indy.wait_for_move_finish()
    #실린더 push -> ungrip
    plc.writebit('M1104',[0])
    plc.writebit('M1105',[1])
    time.sleep(1)
    plc.writebit('M1114',[1])
    time.sleep(0.2)

    ## 스냅샷 위치 복귀
    indy.execute_move('l-go-snapshot')
    indy.wait_for_move_finish()
    indy.go_home()
    indy.wait_for_move_finish()
    
    # else:
    #     print('end')
    
    indy.disconnect()