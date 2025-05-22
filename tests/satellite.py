from time import sleep
import requests

INTERVAL_TIME=5

def satellite():
    for _ in range(20):
        try:
            r=requests.get("http://app:80")
            if r.status_code==200:
                print("connection established")
                break
        except requests.exceptions.ConnectionError:
            print("Waiting for the API")
        sleep(1)
    else:
        print("API not reachable timeout")
        exit(1)
            
    while True:
        f = open("images_satellite/platform.png", 'rb')
        files = {"file": (f.name, f, "multipart/form-data")}
        requests.post(url="http://app:80/upload", files=files)
        sleep(INTERVAL_TIME)
        for i in range(0,9):
            print("POOOOST")
            f = open("images_satellite/boat"+str(i)+".jpg", 'rb')
            files = {"file": (f.name, f, "multipart/form-data")}
            requests.post(url="http://app:80/upload", files=files)
            sleep(INTERVAL_TIME)
        

satellite()