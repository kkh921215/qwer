"""
Saves a series of snapshots with the current camera as snapshot_<width>_<height>_<nnn>.jpg
Arguments:
    --f <output folder>     default: current folder
    --n <file name>         default: snapshot
    --w <width px>          default: none
    --h <height px>         default: none
Buttons:
    q           - quit
    space bar   - save the snapshot
    
  
"""

import cv2
import argparse
import os
import pyrealsense2 as rs
import numpy as np
import time



pipeline = rs.pipeline()

config = rs.config()
dev = rs.device()
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)

profile = pipeline.start(config)
depth_frame = None
color_intrin = None
depth_intrin = None
depth_to_color_extrin = None

depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()


align_to = rs.stream.color
align = rs.align(align_to)


def save_snaps(width=1280, height=720, name="snapshot", folder="data"):

    if width > 0 and height > 0:
        print("Setting the custom Width and Height")
        
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
            # ----------- CREATE THE FOLDER -----------------
            folder = os.path.dirname(folder)
            try:
                os.stat(folder)
            except:
                os.mkdir(folder)
    except:
        pass

    nSnap   = 0
    w       = 1280
    h       = 720

    fileName    = "%s/%s_%d_%d_" %(folder, name, w, h)

    while True:
        frames = pipeline.wait_for_frames()

        aligned_frames = align.process(frames)

        aligned_depth_frame = aligned_frames.get_depth_frame() ### use
        color_frame = aligned_frames.get_color_frame() 

        if not aligned_depth_frame or not color_frame: continue

        color_intrin = color_frame.profile.as_video_stream_profile().intrinsics
        depth_intrin = aligned_depth_frame.profile.as_video_stream_profile().intrinsics
        depth_to_color_extrin = aligned_depth_frame.profile.get_extrinsics_to(color_frame.profile)
        depth_frame = aligned_depth_frame.get_data()

        ### Main Image
        depth_image = np.asanyarray(depth_frame)
        color_image = np.asanyarray(color_frame.get_data())

        cv2.imshow('camera', color_image)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord(' '):
            print("Saving image ", nSnap)
            cv2.imwrite("%s%d.jpg"%(fileName, nSnap), color_image)
            cv2.imwrite("%s%d_depth.png"%(fileName, nSnap), depth_image)
            nSnap += 1

    pipeline.stop()
    cv2.destroyAllWindows()




def main():
    # ---- DEFAULT VALUES ---
    SAVE_FOLDER = "data"
    FILE_NAME = "snapshot"
    FRAME_WIDTH = 1280
    FRAME_HEIGHT = 720

    # ----------- PARSE THE INPUTS -----------------
    parser = argparse.ArgumentParser(
        description="Saves snapshot from the camera. \n q to quit \n spacebar to save the snapshot")
    parser.add_argument("--folder", default=SAVE_FOLDER, help="Path to the save folder (default: current)")
    parser.add_argument("--name", default=FILE_NAME, help="Picture file name (default: snapshot)")
    parser.add_argument("--dwidth", default=FRAME_WIDTH, type=int, help="<width> px (default the camera output)")
    parser.add_argument("--dheight", default=FRAME_HEIGHT, type=int, help="<height> px (default the camera output)")
    args = parser.parse_args()

    SAVE_FOLDER = args.folder
    FILE_NAME = args.name
    FRAME_WIDTH = args.dwidth
    FRAME_HEIGHT = args.dheight


    save_snaps(width=args.dwidth, height=args.dheight, name=args.name, folder=args.folder)

    print("Files saved")

if __name__ == "__main__":
    main()
