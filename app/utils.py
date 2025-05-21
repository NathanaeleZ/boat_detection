import time
import numpy as np
import cv2
from scipy.spatial import distance

def is_point_in_cone(center_point,direction_point,platform_point,angle_cone): # Parameter in euclidian coordinate
    center_point=np.array(center_point)
    direction_point=np.array(direction_point)
    platform_point=np.array(platform_point)

    vector_to_platform = platform_point - center_point

    direction_vector=direction_point-center_point

    vector_to_platform_normalized= vector_to_platform/np.linalg.norm(vector_to_platform)
    direction_vector_normalized=direction_vector/np.linalg.norm(direction_vector)

    dot_product = np.dot(direction_vector_normalized,vector_to_platform_normalized)

    angle= np.acos(dot_product)
    return angle_cone >= np.rad2deg(angle)

def speed(x1,x2,scale): # x1,x2 = "location":boat_point, "time":d , Scale = int  
    point1=x1["location"]
    point2=x2["location"]
    dst=distance.euclidean(point1, point2)*scale

    tstart=x1["time"]
    tend=x2["time"]
    delta = tend - tstart
    seconds = int(delta.total_seconds())

    return (dst/seconds)*3.6 # return km/h speed

def expected_time(speed,distance): 
    speed=speed/3.6 # to m/s
    distance=distance
    expected_time=distance/speed
    print(time.strftime('%H:%M:%S', time.gmtime(expected_time)))
    return time.strftime('%H:%M:%S', time.gmtime(expected_time))

def draw_line(points): # points = List of point = "location":boat_point, "time":d
    # Load the image
    image = cv2.imread("runs/obb/predict/photo.jpg")
    # Define the color (BGR format) and thickness of the line
    color = (0, 255, 0) 
    thickness = 2

    tamp=points[0]["location"]
    # Draw the line on the image
    for point in points[1:]:
        cv2.line(image, (int(tamp[0]), int(tamp[1])), (int(point["location"][0]), int(point["location"][1])), color, thickness)
        tamp=point["location"]
    # Save the modified image
    cv2.imwrite('runs/obb/predict/photo.jpg', image)