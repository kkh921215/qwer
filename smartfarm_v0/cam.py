import cv2
import os
import numpy as np
import time
import pandas as pd

import detect

## communication message
MSG_READY = 0
MSG_TRIGGER = 1
MSG_PROG_START = 2
MSG_PROG_STOP = 3
MSG_DETECTED = 4
MSG_NOTHING = 5

# 작업 경로
WORK_DIR = ''
VAR_OUTPUT_DIR = WORK_DIR + 'output' # 모델이 저장된 경로
VAR_TEST_DIR = WORK_DIR + 'test' # 테스트 이미지 경로
VAR_RES_DIR = WORK_DIR + 'result' # 실행 결과를 저장할 경로
VAR_TRAIN_DIR = WORK_DIR + 'train' # 실행 결과를 저장할 경로
VAR_LABEL_DIR = WORK_DIR + 'label' # 라벨링 결과를 저장할 경로
VAR_SNAP_DIR = WORK_DIR + 'data'

s_path = VAR_TEST_DIR
m_path = VAR_OUTPUT_DIR
r_path = VAR_RES_DIR
t_path = VAR_RES_DIR
l_path = VAR_LABEL_DIR
d_path = VAR_SNAP_DIR

def kinect(model_config, conn):
    pass

def realsense(model_config, conn):
    import pyrealsense2 as rs

    FRAME_WIDTH = model_config['vision']['frame_width']
    FRAME_HEIGHT = model_config['vision']['frame_height']

    color_intrin = None
    depth_intrin = None
    depth_to_color_extrin = None

    pipeline = rs.pipeline()
    config = rs.config()
    dev = rs.device()
    config.enable_stream(rs.stream.depth, FRAME_WIDTH, FRAME_HEIGHT, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, FRAME_WIDTH, FRAME_HEIGHT, rs.format.bgr8, 30)

    profile = pipeline.start(config)
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    align_to = rs.stream.color
    align = rs.align(align_to)

    if conn:
        conn.send(MSG_READY)

    # load detecting model
    if model_config['vision']['model'] == 'detectron2':
        VS = detect.dtron2(model_config['vision'])
    elif model_config['vision']['model'] == 'yolo':
        VS = detect.yolov8(model_config['vision'])

    cv2.namedWindow('Realsense2 D435 Image', cv2.WINDOW_NORMAL)
    idx = 0
    while True:
        ### Aruco marker detecting start & camera setting
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        aligned_depth_frames = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        if not aligned_depth_frames or not color_frame: continue
    
        color_intrin = color_frame.profile.as_video_stream_profile().intrinsics
        depth_intrin = aligned_depth_frames.profile.as_video_stream_profile().intrinsics
        depth_to_color_extrin = aligned_depth_frames.profile.get_extrinsics_to(color_frame.profile)
        depth_frame = aligned_depth_frames.get_data()

        depth_img = np.asanyarray(depth_frame) # depth 이미지
        color_img = np.asanyarray(color_frame.get_data()) # color 이미지

        colordepth = cv2.convertScaleAbs (depth_img, alpha=0.05)
        colordepth = cv2.applyColorMap(colordepth, cv2.COLORMAP_JET)

        stack_img = np.hstack((color_img, colordepth))

        # Plot the image
        cv2.imshow('Realsense2 D435 Image', stack_img)

        key = cv2.waitKey(1) & 0xFF
        if conn:
            key = None
            if conn.poll():
                robot_msg = conn.recv()
                if robot_msg == MSG_TRIGGER:
                    key = ord(' ')
                elif robot_msg == MSG_PROG_STOP:
                    key = ord('q')
            else:
                continue

        # Press q key to stop
        if key == ord('q'):
            break

        elif key == ord(' '):
            # 촬영된 이미지와 인식 결과 저장
            print("Saving image ", idx)
            os.makedirs(d_path, exist_ok=True)

            fname = 'orgimg_' + str(idx) + '.jpg'
            out_1 = os.path.join(d_path, fname)
            cv2.imwrite(out_1, color_img)

            fname = 'orgdepth_' + str(idx) + '.png'
            out_2 = os.path.join(d_path, fname)
            cv2.imwrite(out_2, depth_img)

            img = color_img
            df_obj, min_idx, nxt_dst = VS.run_on_image(img, idx)
            if not (df_obj is None):
                [xp, yp] = np.array(df_obj.loc[min_idx, ['X', 'Y']], dtype=int)
                dist = aligned_depth_frames.get_distance(xp, yp)
                depth_point = rs.rs2_deproject_pixel_to_point(color_intrin, [xp, yp], dist*depth_scale)
                [x3d, y3d, z3d] = rs.rs2_transform_point_to_point(depth_to_color_extrin, depth_point)
                [x3d, y3d, z3d] = [pos*1000 for pos in [x3d, y3d, z3d]]
                df_obj.loc[min_idx, ['x3d', 'y3d', 'z3d']] = [x3d, y3d, z3d]
                conn.send(MSG_DETECTED)
                conn.send(np.array(df_obj.loc[min_idx, ['x3d', 'y3d', 'z3d']]))
                conn.send(df_obj.loc[min_idx, 'dist'])
                conn.send(nxt_dst)
            else:
                conn.send(MSG_NOTHING)
            idx += 1

    print('Program Stop')
    pipeline.stop()
    if conn:
        conn.close()