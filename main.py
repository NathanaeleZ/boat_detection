from typing import Union

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

import math
from ultralytics import YOLO
import numpy as np
import torch

import shutil

from fastapi.templating import Jinja2Templates

from datetime import date, datetime

import cv2

import numpy as np

num_boat=0

MODEL_PATH="yolo11m-obb.pt"

list_point=list()

app = FastAPI()

app.mount("/runs/obb/predict", StaticFiles(directory="runs/obb/predict"), name="static")

templates = Jinja2Templates(directory="templates")

def draw_line():
    # Load the image
    image = cv2.imread("runs/obb/predict/photo.jpg")


    # Define the color (BGR format) and thickness of the line
    color = (0, 255, 0) 
    thickness = 2

    tamp=list_point[0]
    # Draw the line on the image
    for point in list_point[1:]:
        cv2.line(image, (int(tamp[0]), int(tamp[1])), (int(point[0]), int(point[1])), color, thickness)
        tamp=point

    # Save the modified image
    cv2.imwrite('runs/obb/predict/photo.jpg', image)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    with open("log.txt", "r", encoding="utf-8") as f:
            content=f.read()
    image_path = Path("photo.jpg")
    if not image_path.is_file():
        return {"error": "Image not found on the server"}
    
    return templates.TemplateResponse("index.html", 
            {
              "request": request, 
              "image_name": image_path,
              "text": content,
              "now": datetime.now()
            }
        )

@app.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        with open("photo.jpg", 'wb') as f:
            f.write(contents)
    except Exception:
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        file.file.close()

    try:
        shutil.rmtree("runs/obb/predict")
    except OSError as e:
        print(f"Error:{ e.strerror}")
    
    # Load a model
    model = YOLO(MODEL_PATH)  # load an official model
    # Predict with the model
    results = model(source="photo.jpg",imgsz=768,conf=0.25,save=True)  # predict on an image

    d=datetime.now()

    #Analyse detection
    result=results[0]    
    print(result.obb)    
    xywhr = result.obb.xywhr  # Tensor center-x, center-y, width, height, angle (radians)
    global list_point
    if result.obb.conf.numel(): # If detection
        global num_boat
        with open("log.txt", "r", encoding="utf-8") as f: #Read last lines
            lines=f.readlines()
            last_line=lines[-1].strip() if lines else "No detection"
        l=xywhr.tolist()[0][:2]
        point=(l[0],l[1])
        list_point.append(point)
        if "No detection" in last_line: # If last detection was empty
            num_boat+=1
            text="<"+str(d)+"> "+"Boat#"+str(num_boat)+" detected at :"+str(xywhr)+"\n"

        else: # If last detection was the same boat
            text="<"+str(d)+"> "+"Boat#"+str(num_boat)+" detected at :"+str(xywhr)+"\n"
            draw_line()

    else: #If no detection
        text="<"+str(d)+"> "+"No detection"+"\n"
        list_point=list()

    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(text)

    return {"message": f"Successfully uploaded {file.filename}"}