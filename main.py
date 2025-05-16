import time
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

from scipy.spatial import distance

num_boat=0

SCALE = 10

MODEL_PATH="runs/obb/train9/weights/best.pt"

list_point=list()

app = FastAPI()

app.mount("/runs/obb/predict", StaticFiles(directory="runs/obb/predict"), name="static")

templates = Jinja2Templates(directory="templates")

def is_point_in_cone(center_point,direction_point,platform_point,angle_cone):
    center_point=np.array(center_point)
    direction_point=np.array(direction_point)
    platform_point=np.array(platform_point)

    vector_to_platform = platform_point - center_point

    direction_vector=direction_point-center_point

    vector_to_platform_normalized= vector_to_platform/np.linalg.norm(vector_to_platform)
    direction_vector_normalized=direction_vector/np.linalg.norm(direction_vector)

    dot_product = np.dot(direction_vector_normalized,vector_to_platform_normalized)

    angle= np.acos(dot_product)
    print("YOOOOOOOOOOOOOOOOOOOOO")
    print(np.rad2deg(angle))
    return angle_cone >= np.rad2deg(angle)

def orientation(x1,y1,x2,y2):

    radians = math.atan2((y1 - y2), (x1 - x2))
    compassReading = radians * (180 / math.pi)
    if compassReading<0:
        compassReading=-compassReading
    return compassReading

def speed():
    point1=list_point[-2]["location"]
    point2=list_point[-1]["location"]
    dst=distance.euclidean(point1, point2)*SCALE

    tstart=list_point[-2]["time"]
    tend=list_point[-1]["time"]
    delta = tend - tstart
    seconds = int(delta.total_seconds())

    return (dst/seconds)*3.6

def expected_time(speed,distance):
    speed=speed/3.6
    print(distance,speed)
    expected_time=distance/speed
    return time.strftime('%H:%M:%S', time.gmtime(expected_time))
def draw_line():
    # Load the image
    image = cv2.imread("runs/obb/predict/photo.jpg")


    # Define the color (BGR format) and thickness of the line
    color = (0, 255, 0) 
    thickness = 2

    tamp=list_point[0]["location"]
    # Draw the line on the image
    for point in list_point[1:]:
        cv2.line(image, (int(tamp[0]), int(tamp[1])), (int(point["location"][0]), int(point["location"][1])), color, thickness)
        tamp=point["location"]

    # Save the modified image
    cv2.imwrite('runs/obb/predict/photo.jpg', image)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    content=""
    with open("log.txt", "r", encoding="utf-8") as f:
        lines=f.readlines()
    ptr=0
    for line in lines:
        if ptr< len(lines)-20:
            ptr+=1
        else:
            content+=line

    image_path = Path("photo.jpg")
    if not image_path.is_file():
        return {"error": "Image not found on the server"}
    
    return templates.TemplateResponse("index.html", 
            {
              "request": request, 
              "image_name": image_path,
              "text": content,
              "now": datetime.now().replace(microsecond=0)
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

    d=datetime.now().replace(microsecond=0)

    #Analyse detection
    result=results[0]    

    global list_point
    if result.obb.conf.numel(): # If detection
        global num_boat
        with open("log.txt", "r", encoding="utf-8") as f: #Read last lines
            lines=f.readlines()
            last_line=lines[-1].strip() if lines else "No detection"
        boat_point=(0.0,0.0)
        platefor_point=(0.0,0.0)
        for detection in result.obb:
            if detection.cls.item()==15.0:
                platform_point=(detection.xywhr.tolist()[0][:2][0],detection.xywhr.tolist()[0][:2][1])
                print(platform_point)
            else:
                boat_point=(detection.xywhr.tolist()[0][:2][0],detection.xywhr.tolist()[0][:2][1])
                new_entry={
                    "location":boat_point,
                    "time":d
                }
                list_point.append(new_entry)

        if "No detection" in last_line and boat_point!=(0.0,0.0): # If last detection was empty
            dst=distance.euclidean(boat_point, platform_point)*SCALE
            num_boat+=1
            text="<"+str(d)+"> "+"Boat#"+str(num_boat)+" just appeared at :"+str("%.0f" % boat_point[0])+" , "+str("%.0f" % boat_point[1])+", Distance : "+str("%.0f" % (dst))+" m\n"

        elif boat_point!=(0.0,0.0): # If last detection was the same boat
            dst=distance.euclidean(boat_point, platform_point)*SCALE
            if platform_point!=(0.0,0.0):
                if is_point_in_cone(list_point[-2]["location"],boat_point,platform_point,15):
                    speedd=speed()
                    text="<"+str(d)+"> "+"Boat#"+str(num_boat)+" detected and IS HEADING TOWARDS the platform, Speed :"+str("%.0f" %speedd)+" km/h"", Distance : "+str("%.0f" % dst)+" m, Expected time: "+expected_time(speedd,dst)+"\n"
                else:
                    text="<"+str(d)+"> "+"Boat#"+str(num_boat)+" detected and is not heading towards the platform, Speed :"+str("%.0f" %speed())+" km/h"", Distance : "+str("%.0f" % dst)+" m\n"
            draw_line()

        else: # Platform but no boat
            text="<"+str(d)+"> "+"No detection"+"\n"
            list_point=list()

    else: #If no detection
        text="<"+str(d)+"> "+"No detection"+"\n"
        list_point=list()

    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(text)

    return {"message": f"Successfully uploaded {file.filename}"}