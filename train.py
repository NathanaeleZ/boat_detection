from pathlib import Path
import mlflow
from ultralytics import YOLO, settings


# Update a setting
settings.update({"mlflow": True})

# Reset settings to default values
settings.reset()

EPOCHS=4
MODEL_PATH="yolo11m-obb.pt"
#MODEL_PATH="runs/obb/train2/weights/best.pt"
CONFIG_PATH="datasets/data.yaml"


mlflow.set_tracking_uri('http://127.0.0.1:5000')
mlflow.set_experiment('Ship detection')



with mlflow.start_run() as run:
    mlflow.log_param("epochs",EPOCHS)
    mlflow.log_param("model_path",MODEL_PATH)
    mlflow.log_param("config_path",CONFIG_PATH)

    model = YOLO(MODEL_PATH)

    #for param in model.model.parameters():
    #      param.requires_grad=False
    #for param in model.model.model[-1].parameters():
    #      param.requires_grad=True
        
    train_results = model.train(
        data=CONFIG_PATH,
        epochs=EPOCHS,
        imgsz=768,
        batch=16,
        save=True,
        device=0,
        #lr0=0.0001 #learning rate
    )

    metrics=train_results.metrics
    for metric, value in metrics.items():
            mlflow.log_metric(metric,value)

    output_path= Path("model/platform_detectionv0.pt")
    mlflow.log_artifact(str(output_path))
    mlflow.end_run()

