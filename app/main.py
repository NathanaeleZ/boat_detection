
import asyncio
from datetime import datetime

from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from ultralytics import YOLO

from app.utils import *

from starlette.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND,HTTP_303_SEE_OTHER

clients= []
num_boat=0
SCALE = 10
predict_counter=1
MODEL_PATH="runs/obb/model/best.pt"
list_point=list()

app = FastAPI()

app.mount("/runs/obb", StaticFiles(directory="runs/obb"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/",response_class=HTMLResponse)
async def index(request: Request):
    contents=""
    try:
        f=open("log.txt", "r", encoding="utf-8")
    except:
        print("Nofile")
    else:
        with f:
            lines=f.readlines()
            ptr=0
            for line in lines:
                if ptr< len(lines)-20:
                    ptr+=1
                else:
                    contents+=line

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

    
    global list_point
    if result.obb.conf.numel(): # If detection
        global num_boat
        try:
            f=open("log.txt", "r", encoding="utf-8") #Read last lines
        except FileNotFoundError:
            last_line="No detection"
        else:
            with f:
                lines=f.readlines()
                last_line=lines[-1].strip() if lines else "No detection"
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
                print(conf)
                # Au moment d'enregistrer comparer les bateaux avec calcul mathématique et si 2 identique on leur affecte le même id
                #(width,height)=(detection.xywhr.tolist()[0][:2][2],detection.xywhr.tolist()[0][:2][3])
                
                new_entry={ # Enregistrer dans le tableau toutes les infos du bateau (coordonnées, id, temsp , taille, theta , autres si possible)
                    "location":boat_point,
                    "time":d,
                    "size":(width,height),
                    "angle":theta,
                    "conf":conf
                }
                list_point.append(new_entry)

        if "No detection" in last_line and boat_point!=(0.0,0.0): # If last detection was empty
            dst=distance.euclidean(boat_point, platform_point)*SCALE
            num_boat+=1
            text="<"+str(d)+"> "+"Boat#"+str(num_boat)+" just appeared, Distance : "+str("%.0f" % (dst))+" m\n"

        elif boat_point!=(0.0,0.0): # If last detection was the same boat
            dst=distance.euclidean(boat_point, platform_point)*SCALE
            if platform_point!=(0.0,0.0):
                if is_point_in_cone(list_point[-2]["location"],boat_point,platform_point,15):
                    speedd=speed(list_point[-2],list_point[-1],SCALE)
                    text="<"+str(d)+"> "+"Boat#"+str(num_boat)+" IS HEADING TOWARDS the platform,\n Speed :"+str("%.0f" %speedd)+" km/h"", Distance : "+str("%.0f" % dst)+" m, Expected time: "+expected_time(speedd,dst)+"\n"
                else:
                    text="<"+str(d)+"> "+"Boat#"+str(num_boat)+" is not heading towards the platform,\n Speed :"+str("%.0f" %speed(list_point[-2],list_point[-1],SCALE))+" km/h"", Distance : "+str("%.0f" % dst)+" m\n"
            await draw_line(list_point,predict_counter)

        else: # Platform but no boat
            text="<"+str(d)+"> "+"No detection"+"\n"
            list_point=list()

    else: #If no detection
        text="<"+str(d)+"> "+"No detection"+"\n"
        list_point=list()

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