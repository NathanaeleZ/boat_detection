from pathlib import Path
import mlflow
from ultralytics import YOLO

EPOCHS=100
MODEL_PATH="yolo11m-obb.pt"
CONFIG_PATH="data.yaml"



mlflow.set_experiment('Ship detection')

with mlflow.start_run() as run:
    mlflow.log_param("epochs",EPOCHS)
    mlflow.log_param("model_path",MODEL_PATH)
    mlflow.log_param("config_path",CONFIG_PATH)

    model = YOLO(MODEL_PATH)
    train_results = model.train(
        data=CONFIG_PATH,
        epochs=EPOCHS,
        imgsz=768,
        batch=32,
        save=True,
    )

    metrics=train_results.metrics
    for metric, value in metrics.items():
            mlflow.log_metric(metric,value)

    output_path= Path("model/best.pt")
    mlflow.log_artifact(str(output_path))
    mlflow.end_run()

