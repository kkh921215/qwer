# import some common libraries
import os
import numpy as np
import pandas as pd
import cv2
pd.set_option('mode.chained_assignment',  None)

# import some common detectron2 utilities
import detectron2
from detectron2.utils.logger import setup_logger
setup_logger()

from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog

import torch, torchvision

from PIL import Image
from ultralytics import YOLO

# 작업 경로
WORK_DIR = ''
VAR_MODEL_DIR = WORK_DIR + 'output' # 모델이 저장된 경로
VAR_TEST_DIR = WORK_DIR + 'test' # 테스트 이미지 경로
VAR_RES_DIR = WORK_DIR + 'result' # 실행 결과를 저장할 경로
VAR_TRAIN_DIR = WORK_DIR + 'train' # 실행 결과를 저장할 경로
VAR_LABEL_DIR = WORK_DIR + 'label' # 라벨링 결과를 저장할 경로
VAR_SNAP_DIR = WORK_DIR + 'data'

s_path = VAR_TEST_DIR
m_path = VAR_MODEL_DIR
r_path = VAR_RES_DIR
t_path = VAR_RES_DIR
l_path = VAR_LABEL_DIR
d_path = VAR_SNAP_DIR

# 인식 세팅값
VAR_LAYER_CNT = 101
VAR_PER_BATCH = 12

class dtron2():
  def __init__(self, config): # 모델 가중치 불러오기
    VAR_THRESH = config['thresh']

    # 라벨링된 클래스 입력
    class_name = config['class_name']
    VAR_NUM_CLASSES = len(class_name)

    # 데이터 카탈로그
    self.metadata = MetadataCatalog.get("mdata_").set(thing_classes=class_name)

    cfg = get_cfg()
    
    device = torch.device('cuda')
    if config['device'] == 'cpu':
      cfg.MODEL.DEVICE='cpu'
    # elif config['device'] == 'gpu':
    #   cfg.MODEL.DEVICE='cuda'
    cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_101_FPN_3x.yaml"))

    cfg.SOLVER.IMS_PER_BATCH = VAR_PER_BATCH
    cfg.SOLVER.BASE_LR = 0.00025  # pick a good LR
    cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128  # faster, and good enough for this toy dataset (default: 512)
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = VAR_NUM_CLASSES 

    cfg.MODEL.WEIGHTS = os.path.join(m_path, "model_final.pth")
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = VAR_THRESH  # set a custom testing threshold

    cfg.freeze()

    self.predictor = DefaultPredictor(cfg) # 예측 함수

  def run_on_image(self, img, idx): # 컬러 이미지에 예측 실행
    vis_output = None
    df_data = pd.DataFrame(columns=['X', 'Y', 'dist'])

    predictions = self.predictor(img)
    image = img[:, :, ::-1]
    h, w, c = img.shape

    print('detecting start')
    v = Visualizer(image, self.metadata, scale=1)

    if "instances" in predictions:
      instances = predictions["instances"].to("cpu")
      v_output = v.draw_instance_predictions(predictions=predictions["instances"].to("cpu"))
      num_instances = len(instances)

      if num_instances > 0:
        # 인식된 객체의 위치 정보 처리
        print('detected: ', num_instances)
        boxes1 = instances.pred_boxes.tensor.numpy()
        for i in range(num_instances):
          box = boxes1[i]
          center_x = (box[0] + box[2]) / 2
          center_y = (box[1] + box[3]) / 2
          xy_pos = np.array([center_x, center_y])
          center = np.array([w/2, h/2])
          c_dist = np.linalg.norm(xy_pos - center)
          df_data.loc[i] = [center_x, center_y, c_dist]
        dist_min = df_data['dist'].idxmin()

        os.makedirs(r_path, exist_ok=True)
        fname = 'img_' + str(idx) + '.jpg'
        out_filename = os.path.join(r_path, fname)
        v_output.save(out_filename)

      else:
        print('detected: nothing')
        df_data = None
        dist_min = 0

      return df_data, dist_min
    
class yolov8:
  def __init__(self, config) -> None:
    self.thresh = config['thresh']
    self.vert = config['crop']['vertical']
    self.hori = config['crop']['horizontal']
    self.imgsz = config['imgsz']
    
    model_path = os.path.join(m_path, "best.pt")
    self.model = YOLO(model_path)
  
  def run_on_image(self, img, idx):
    image = Image.fromarray(img[..., ::-1])
    
    visout = None
    df_data = pd.DataFrame(columns=['X', 'Y', 'x1', 'y1', 'x2', 'y2', 'dist'])

    # 현재 이미지 크기 얻기
    width, height = image.size
    
    resized_image = image.resize((640, 640))
    
    source = resized_image
    h, w, c = img.shape
    results = self.model.predict(source, imgsz=640, conf=self.thresh)
    result = results[0]
    
    num_instances = len(result.boxes.data)
    if num_instances > 0:
      names = result.names
      boxes = result.boxes.data
      visout = result.plot()
        
      for i, box in enumerate(boxes):
        x1, y1, x2, y2, conf, cnt = box
        if names[int(cnt)] == 'Planted_in': continue # planted in 스킵
        org_x1, org_y1 = self.convert_coordinates(x1, y1, 640, 640, 1280, 720)
        org_x2, org_y2 = self.convert_coordinates(x2, y2, 640, 640, 1280, 720)
        center_x = (org_x1 + org_x2) / 2
        center_y = (org_y1 + org_y2) / 2
        xy_pos = np.array([center_x, center_y])
        center = np.array([w/2, h/2])
        c_dist = np.linalg.norm(xy_pos - center)
        df_data.loc[i] = [center_x, center_y, x1, y1, x2, y2, c_dist]

      if len(df_data) < 2: # 감지된 spot이 2개 미만인 경우 에러 처리
        print('detecting error')
        df_data = None
        dist_min = 0
        next_dist = 0
        return df_data, dist_min, next_dist


        
      dist_min = df_data['dist'].idxmin()
      sorted_index = df_data.sort_values('dist').index
      print(sorted_index)
      r1 = df_data['y1'][sorted_index[0]]
      r2 = df_data['y1'][sorted_index[1]]
      print(r1,r2)
      print(df_data['x1'][sorted_index[0]],df_data['x1'][sorted_index[1]])
      next_dist = int(abs((r1 - r2)/10))-5
      
      os.makedirs(r_path, exist_ok=True)
      fname = 'img_' + str(idx) + '.jpg'
      out_filename = os.path.join(r_path, fname)
      cv2.imwrite(out_filename, visout)
      
    else:
      print('detected: nothing')
      df_data = None
      dist_min = 0
      next_dist = 0

    return df_data, dist_min, next_dist
  
  def convert_coordinates(self, x, y, original_width, original_height, new_width, new_height):
    x_ratio = new_width / original_width
    y_ratio = new_height / original_height

    new_x = x * x_ratio
    new_y = y * y_ratio

    return new_x, new_y