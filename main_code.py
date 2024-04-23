import os.path as osp
# import shutil

import yaml

def get_default_config():
    config_file = 'config.yaml'
    with open(config_file) as f:
        config = yaml.safe_load(f)

    return config

from multiprocessing import Pipe, Process
import cam
import main_robot
import sub_robot

def main_robot_task(config, conn1, conn2): 
    main_robot.indy_task(config, conn1, conn2)

def sub_robot_task(config, conn):
    sub_robot.indy_task(config, conn)

def cam_task(config, cam_type, conn):
    if cam_type == 'AK':
        cam.kinect(config, conn)

    if cam_type == 'RS':
        cam.realsense(config, conn)

# 메인 프로그램 실행
if __name__ == '__main__':
    config = get_default_config()
    
    if config['vision']['camera'] == 'realsenseD435':
        cam_type = 'RS'
        
        conn11, conn12 = Pipe()
        conn21, conn22 = Pipe()
        print('robot task start')
        p1 = Process(target=main_robot_task, args=(config, conn11, conn21)) # main robot task
        p2 = Process(target=sub_robot_task, args=(config, conn12,)) # sub robot task
        p3 = Process(target=cam_task, args=(config, cam_type, conn22,)) # cam task
        p1.start()
        p2.start()
        p3.start()
        p1.join()
        p2.join()
        p3.join()

    else:
        cam_type = 'AK'
        