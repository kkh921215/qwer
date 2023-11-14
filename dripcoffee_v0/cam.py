import cv2
import os
import numpy as np
import time

import detect

## communication message
MSG_CAM_READY = 0
MSG_TRIGGER = 1
MSG_PROG_STOP = 2
MSG_DETECTED = 3
MSG_NOTHING = 4

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

# def kinect(config, opt, conn):
#     import pyk4a
#     from pyk4a import Config, PyK4A
#     from pyk4a.helpers import colorize
#     k4a = PyK4A(
#         Config(
#             color_resolution=pyk4a.ColorResolution.RES_1080P,
#             depth_mode=pyk4a.DepthMode.WFOV_2X2BINNED,
#             color_format= pyk4a.ImageFormat.COLOR_BGRA32,
#             camera_fps= pyk4a.FPS.FPS_30,
#             synchronized_images_only= True,
#         )
#     )
#     k4a.start()

#     if conn:
#         conn.send(MSG_CAM_READY)
#     # load detecting model
#     VS = detect.Visualization(m_path,config["vision"]["class_name"])
#     cv2.namedWindow('Azure Kinect DK Image', cv2.WINDOW_NORMAL)

#     idx = 0
#     while True:
#         # Get capture
#         capture = k4a.get_capture()

#         # Get the color image from the capture
#         color_img=capture.color

#         # Get the colored depth
#         depth_img = capture.transformed_depth

#         # color_depth = colorize(capture.transformed_depth, (None, 1000))
#         # new_img=convert_img2train(color_img,color_depth)
#         # cv2.imshow('Azure Kinect DK Image', new_img)
#         # stack_img = np.hstack((new_img, color_depth))

#         # Plot the image
#         cv2.imshow('Azure Kinect DK Image', color_img)

#         key = cv2.waitKey(1) & 0xFF
#         if conn:
#             key = None
#             if conn.poll():
#                 robot_msg = conn.recv()
#                 if robot_msg == MSG_TRIGGER:
#                     key = ord(' ')
#                 elif robot_msg == MSG_PROG_STOP:
#                     key = ord('q')
#                 elif robot_msg == MSG_PROG_STOP:
#                     break
#             else:
#                 continue

#         # Press q key to stop
#         if key == ord('q'):
#             break

#         elif key == ord(' '):
#             # 촬영된 이미지와 인식 결과 저장
#             # new_img=convert_img2train(color_img,color_depth)
#             print("Saving image ", idx)
#             os.makedirs(d_path, exist_ok=True)
            
#             fname = 'orgimg_' + str(idx) + '.jpg'
#             out_1 = os.path.join(d_path, fname)
#             cv2.imwrite(out_1, color_img)

#             fname = 'orgdepth_' + str(idx) + '.jpg'
#             out_2 = os.path.join(d_path, fname)
#             cv2.imwrite(out_2, depth_img)

#             # fname = 'manimg_' + str(idx) + '.jpg'
#             # out_3 = os.path.join(d_path, fname)
#             # cv2.imwrite(out_3, new_img)
#             if opt == 3:
#                 img = color_img[:,:,0:3]
#                 df_ins = VS.run_on_image(img, idx)
#                     # elif pork_type==1:
#                     #     df_ins = VSSMALL.run_on_image(new_img, idx) 

#                 if len(df_ins) > 0:
#                     # for i in range(len(df_ins)):
#                     #     [xp, yp] = np.array(df_ins.loc[i, ['X', 'Y']], dtype=int)
#                     #     x_cord=[]
#                     #     y_cord=[]
#                     #     z_cord=[]
#                     #     for j in range(10):
#                     #         capture = k4a.get_capture()
#                     #         color_image=capture.color
#                     #         depth_image=capture.transformed_depth_point_cloud.reshape(-1,3)
#                     #         width=color_image.shape[1]
#                     #         height=color_image.shape[0]
#                     #         xyz_array=depth_image.reshape(height,width,3)
#                     #         [x3d, y3d, z3d] = xyz_array[yp,xp]
#                     #         x_cord.append(x3d)
#                     #         y_cord.append(y3d)
#                     #         z_cord.append(z3d)
#                     #     x_median=np.median(x_cord)
#                     #     y_median=np.median(y_cord)
#                     #     z_median=np.median(z_cord)
#                     #     print('x3d 평균:{} x3d 분산;{} x3d 표준편차:{} x3d 중간값:{}'
#                     #     .format(np.mean(x_cord),np.var(x_cord),np.std(x_cord),x_median))
#                     #     print('y3d 평균:{} y3d 분산;{} y3d 표준편차:{} y3d 중간값:{}'
#                     #     .format(np.mean(y_cord),np.var(y_cord),np.std(y_cord),y_median))
#                     #     print('z3d 평균:{} z3d 분산;{} z3d 표준편차:{} z3d 중간값:{}'
#                     #     .format(np.mean(z_cord),np.var(z_cord),np.std(z_cord),z_median))

#                     #     # [x3d, y3d, z3d] = [x3d*1000, y3d*1000, z3d*1000]
#                     #     df_ins.loc[i, ['x3d', 'y3d', 'z3d']] = [x_median, y_median, z_median]
#                     if conn:
#                         conn.send(MSG_DETECTED)
#                         conn.send(df_ins)
#                 else:
#                     if conn:
#                         conn.send(MSG_NOTHING)
#             idx += 1

#     print('Program Stop')
#     cv2.destroyAllWindows()
#     k4a.stop()
#     if conn:
#         print('connection close')
#         conn.close()
        
def img_test(prog):
    from detectron2.data.detection_utils import read_image

    # load detecting model
    VS = detect.Visualization(m_path)

    if prog == 2:
        path = s_path

    if prog == 4:
        path = l_path

    fnames = os.listdir(path)
    idx = 0
    for fname in fnames:
        f_name, f_ext = os.path.splitext(fname)
        filename = os.path.join(path, fname)

        if (f_ext != '.jpg' and f_ext != '.JPEG'): continue

        print('img ', idx)
        print('filename: ', filename)
        img = read_image(filename, format='BGR')
        df_ins = VS.run_on_image(img, idx)

        if prog == 4:
            detect.auto_label(img, fname, df_ins)

        idx += 1

    print('test done')
def realsense(opt, conn):
    import pyrealsense2 as rs

    FRAME_WIDTH = 1280
    FRAME_HEIGHT = 720

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
        conn.send(MSG_CAM_READY)

    # load detecting model
    VS = detect.Visualization(m_path)

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

            fname = 'orgdepth_' + str(idx) + '.jpg'
            out_2 = os.path.join(d_path, fname)
            cv2.imwrite(out_2, depth_img)

            if opt == 3:
                img = color_img
                df_ins = VS.run_on_image(img, idx)
                if len(df_ins) > 0:
                    for i in range(len(df_ins)):
                        [xp, yp] = np.array(df_ins.loc[i, ['X', 'Y']], dtype=int)
                        dist = aligned_depth_frames.get_distance(xp, yp)
                        depth_point = rs.rs2_deproject_pixel_to_point(color_intrin, [xp, yp], dist*depth_scale)
                        [x3d, y3d, z3d] = rs.rs2_transform_point_to_point(depth_to_color_extrin, depth_point)
                        # [x3d, y3d, z3d] = [x3d*1000, y3d*1000, z3d*1000]
                        df_ins.loc[i, ['x3d', 'y3d', 'z3d']] = [x3d, y3d, z3d]
                    conn.send(MSG_DETECTED)
                    conn.send(df_ins)
                else:
                    conn.send(MSG_NOTHING)
            idx += 1

    print('Program Stop')
    pipeline.stop()
    if conn:
        conn.close()

