# BOAT DETECTION VIA SATELLITE IMAGES


After you launch the docker image, you can try this command in python to test.

f = open("Path/to/image.png", 'rb')
files = {"file": (f.name, f, "multipart/form-data")}
requests.post(url="http://127.0.0.1:80/upload", files=files)

See the result at http://127.0.0.1:80

# What the goal

Sometimes fischerman goes on the Petronas platform and make fire.
This is very dangerous
So the goal of this project is to analyse satellite images around the platform and say if boats are going towards it and identify the boats
# How it works ?

When the web app receive a POST request with an image.
The image is predict with our model.

The model was trained with YOLOv11 and enhanced to predict platform

after the detection the data is analyse and shown on the screen and the image too