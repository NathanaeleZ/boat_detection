import openpyxl
from datetime import datetime

from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from ultralytics import YOLO

from app.utils import *


clients= []
boat_counter=[0]
SCALE = 10
predict_counter=1
MODEL_PATH="runs/obb/model/best.pt"
boat_list=list()

app = FastAPI()

app.mount("/runs/obb", StaticFiles(directory="runs/obb"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/",response_class=HTMLResponse)
async def index(request: Request):
    contents=""

    global predict_counter
    if predict_counter==1:
        image_path = Path("/runs/obb/predict/photo.jpg")
    else:
        image_path = Path("/runs/obb/predict"+str(predict_counter)+"/photo.jpg")
    
    
    return templates.TemplateResponse("index.html", {"request": request, 
              "image_name": image_path,
              "text": contents,
              "now": datetime.now().replace(microsecond=0)
            }
        )

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = file.file.read()

        with open("photo.jpg", 'wb') as f:
            f.write(contents)


    except HTTPException as e:
        # Re-lève l’exception telle quelle
        raise e


    except Exception as e:
        # Erreur inconnue
        raise HTTPException(status_code=500, detail="Internal server error.")


    finally:
        file.file.close()
    
    # Load a model
    model = YOLO(MODEL_PATH)  # load an official model
    # Predict with the model
    results = model(source="photo.jpg",imgsz=768,conf=0.25,save=True)  # predict on an image

    global predict_counter
    predict_counter+=1

    d=datetime.now().replace(microsecond=0)

    #Analyse detection
    result=results[0]    

    
    global boat_list
    if result.obb.conf.numel(): # If detection
        global boat_counter
        boat_point=(0.0,0.0)
        platform_point=(0.0,0.0)

        for detection in result.obb:
            if detection.cls.item()==15.0:
                platform_point=(detection.xywhr.tolist()[0][0],detection.xywhr.tolist()[0][1])
            else:
                boat_point=(detection.xywhr.tolist()[0][:2][0],detection.xywhr.tolist()[0][:2][1])
                theta=detection.xywhr.tolist()[0][-1]
                (width,height)=(detection.xywhr.tolist()[0][2],detection.xywhr.tolist()[0][3])
                conf=detection.conf.item()

                boat_counter=boat_management(boat_list,boat_point,(width,height),theta,conf,boat_counter)

                new_entry={
                    "id":boat_counter,
                    "location":boat_point,
                    "time":d,
                    "size":(width,height),
                    "angle":theta,
                    "conf":conf,
                    "predict_number":predict_counter,
                    "speed":speed,
                    "towards_platform":towards_platform
                }
                boat_list.append(new_entry)
        
        current_boat_list=[]
        for boat in boat_list["predict_number"]==predict_counter:
            current_boat_list.append(boat["id"])
        predict_list.append(predict_counter,current_boat_list)

        if "No detection" in last_line and boat_point!=(0.0,0.0): # If last detection was empty
            dst=distance.euclidean(boat_point, platform_point)*SCALE
            text="<"+str(d)+"> "+"Boat#"+str(boat_counter)+" just appeared, Distance : "+str("%.0f" % (dst))+" m\n"

        elif boat_point!=(0.0,0.0): # If last detection was the same boat
            dst=distance.euclidean(boat_point, platform_point)*SCALE
            if platform_point!=(0.0,0.0):
                if is_point_in_cone(boat_list[-2]["location"],boat_point,platform_point,15):
                    speedd=speed(boat_list[-2],boat_list[-1],SCALE)
                    text="<"+str(d)+"> "+"Boat#"+str(boat_counter)+" IS HEADING TOWARDS the platform,\n Speed :"+str("%.0f" %speedd)+" km/h"", Distance : "+str("%.0f" % dst)+" m, Expected time: "+expected_time(speedd,dst)+"\n"
                else:
                    text="<"+str(d)+"> "+"Boat#"+str(boat_counter)+" is not heading towards the platform,\n Speed :"+str("%.0f" %speed(boat_list[-2],boat_list[-1],SCALE))+" km/h"", Distance : "+str("%.0f" % dst)+" m\n"
            await draw_line(boat_list,predict_counter)

        else: # Platform but no boat
            text="<"+str(d)+"> "+"No detection"+"\n"
            boat_list=list()

    else: #If no detection
        text="<"+str(d)+"> "+"No detection"+"\n"
        boat_list=list()

    with open("log.txt", "a+", encoding="utf-8") as f:
        f.write(text)

    for client in clients:
        try:
            await client.send_text("reload")
        except:
            pass
    return {"message":"done"}

@app.websocket("/ws")
async def web_socket_endpoint(websocket : WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        clients.remove(websocket)