# BOAT DETECTION VIA SATELLITE IMAGES


After you launch the docker image, you can try this command in python to test.

f = open("Path/to/image.png", 'rb')
files = {"file": (f.name, f, "multipart/form-data")}
requests.post(url="http://127.0.0.1:80/upload", files=files)

See the result at http://127.0.0.1:80