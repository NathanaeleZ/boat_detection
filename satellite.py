import requests
import sys

if len(sys.argv)<2:
    f = open("images_satellite/heading/platform.png", 'rb')
else:
    val=sys.argv[1]
    f = open("images_satellite/heading/boat"+val+".jpg", 'rb')
files = {"file": (f.name, f, "multipart/form-data")}
requests.post(url="http://127.0.0.1:8000/upload", files=files)