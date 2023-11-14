from multiprocessing import Pipe, Process
import cam
import task
import argparse

import yaml

def get_default_config():
    config_file = 'config.yaml'
    with open(config_file) as f:
        config = yaml.safe_load(f)

    return config

def robot_task(config,robot_type, conn):
    if robot_type == 'fair3':
        task.fair_task(config,conn)

    if robot_type == 'fanuc':
        task.fanuc_task(config,conn)

def cam_task(config,prog, cam_type, conn):
    if cam_type == 'AK':
        cam.kinect(config,prog, conn)

    if cam_type == 'RS':
        cam.realsense(config,prog, conn)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="select mode")
    parser.add_argument(
        '-mode',
        default = 5,
        help = 'train only (1), image test (2), detect (3), auto label (4), screen shot(5)',
    )

    parser.add_argument(
        '-cam',
        default = 'RS',
        help = 'Azure Kinect DK (AK), Realsense D435 (RS)',
    )

    parser.add_argument(
        '-robot',
        default = 'N',
        help = 'fair3, without Robot (N)',
    )

    args = parser.parse_args()
    prog = int(args.mode)
    cam_type = args.cam
    robot_type = args.robot
    # robot_type='N'
    print('prog: ', prog, ', cam: ', cam_type, ', robot: ', robot_type)
    config = get_default_config()
    if prog == 1:
        print('train start')

    elif prog == 2 or prog == 4:
        print('image test start')
        cam.img_test(prog)

    elif prog == 5 or robot_type == 'N':
        print('Saves snapshot from the camera. \n q to quit \n spacebar to save the snapshot')
        if cam_type == 'AK':
            cam.kinect(config,prog, None)

        if cam_type == 'RS':
            cam.realsense(config,prog, None)

    elif prog == 3:
        conn1, conn2 = Pipe()
        print('robot task start')
        p1 = Process(target=robot_task, args=(config,robot_type, conn1,)) #robot task
        p2 = Process(target=cam_task, args=(config,prog, cam_type, conn2,)) # Object detection task
        p1.start()
        p2.start()
        p1.join()
        p2.join()