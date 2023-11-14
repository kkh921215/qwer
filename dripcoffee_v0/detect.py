import torch, torchvision
import detectron2
from detectron2.utils.logger import setup_logger
setup_logger()

# import some common libraries
import os
import numpy as np
import pickle
import time
import cv2
import pandas as pd
pd.set_option('mode.chained_assignment',  None)

# import some common detectron2 utilities
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog

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

# 인식 세팅값
VAR_LAYER_CNT = 101
VAR_PER_BATCH = 12


class Visualization():
  def __init__(self, path): # 모델 가중치 불러오기
    # 라벨링된 클래스 입력
    # self.class_name = class_name
    # VAR_NUM_CLASSES = len(self.class_name)

    # 데이터 카탈로그
    self.metadata = MetadataCatalog.get("mdata_").set(thing_classes=self.class_name)
    self.cfg = get_cfg()
    self.cfg.MODEL.DEVICE='cpu'
    self.cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_101_FPN_3x.yaml"))

    self.cfg.SOLVER.IMS_PER_BATCH = VAR_PER_BATCH
    self.cfg.SOLVER.BASE_LR = 0.00025  # pick a good LR
    self.cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128  # faster, and good enough for this toy dataset (default: 512)
    # self.cfg.MODEL.ROI_HEADS.NUM_CLASSES = VAR_NUM_CLASSES 
    model="model_final.pth"
    self.cfg.MODEL.WEIGHTS = os.path.join(path, model)
    self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.9  # set a custom testing threshold

    self.cfg.freeze()

    self.predictor = DefaultPredictor(self.cfg) # 예측 함수

  def run_on_image(self, img, idx): # 컬러 이미지에 예측 실행
    vis_output = None
    df_ins = pd.DataFrame()

    predictions = self.predictor(img)
    image = img[:, :, ::-1]
    h, w, c = img.shape

    print('detecting start')
    v = Visualizer(image, self.metadata, scale=1)

    if "instances" in predictions:
      instances = predictions["instances"].to("cpu")
      v_output = v.draw_instance_predictions(predictions=instances)
      num_instances = len(instances)

      if num_instances > 0:
        print('detected: ', num_instances)
        class_num = instances.pred_classes.numpy()
        boxes = instances.pred_boxes.tensor.numpy()
        # masks = np.where(instances.pred_masks.numpy(), 1, 0)

        # x,y pos 및 박스 정보 저장
        for i in range(num_instances):
          # mask = np.fromstring(masks[i], dtype=int).reshape(h, w)
          # cordy, cordx = np.where(mask == 1)
          # p_mask = pickle.dumps(mask)

          df_ins.loc[i, 'class'] = self.class_name[class_num[i]]
          df_ins.loc[i, 'X'] = (boxes[i][0] + boxes[i][2]) / 2
          df_ins.loc[i, 'Y'] = (boxes[i][1] + boxes[i][3]) / 2
          # df_ins.loc[i, ['x1', 'y1', 'x2', 'y2']] = boxes[i]
          # df_ins.loc[i, 'mask'] = p_mask
          # df_ins.loc[i, 'size'] = abs((boxes[i][0] - boxes[i][2])*(boxes[i][1] - boxes[i][3]))

        os.makedirs(r_path, exist_ok=True)
        fname = 'img_' + str(idx)  + '.jpg'
        out_filename = os.path.join(r_path, fname)
        v_output.save(out_filename)
        return df_ins

      else:
        print('detected: nothing') 
        return df_ins
