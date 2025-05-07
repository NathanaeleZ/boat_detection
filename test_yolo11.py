import math
from ultralytics import YOLO
import numpy as np
import torch

# Load a model
model = YOLO("yolo11m-obb.pt")  # load an official model

# Predict with the model
results = model(source=["images/boat0.jpg"],imgsz=768,conf=0.25,save=True)  # predict on an image
result=results[0]
print("YOOOOOO")
print(result.obb.conf.numel())
print("YOOOOOO")
for result in results:
    xywhr = result.obb.xywhr  # center-x, center-y, width, height, angle (radians)
    xyxyxyxy = result.obb.xyxyxyxy  # polygon format with 4-points
    print(xywhr.tolist()[0][:2])
    for polygon in xyxyxyxy:
        p0,p1,p2,p3= polygon.view(4,2)
        vec1=p1-p0
        vec2=p2-p1
        long=vec2 if torch.norm(vec1) < torch.norm(vec2) else vec1
        theta=math.atan2(long[1],long[0])
    #names = [result.names[cls.item()] for cls in result.obb.cls.int()]  # class name of each box
    #confs = result.obb.conf  # confidence score of each box
    degree= (np.degrees(theta) + 180 ) % 360
    print(degree)