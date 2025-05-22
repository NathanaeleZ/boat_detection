from datetime import datetime
from app.utils import *

def test_1():
    assert is_point_in_cone((0,0),(1,0),(1000,1),180)==True , "Point should be inside the cone"
    assert is_point_in_cone((0,0),(1,0),(2,1),15)==False , "Point shouldn't be inside the cone"

def test_2():
    t1,t2=datetime.fromisoformat('2025-11-04T00:05:00'),datetime.fromisoformat('2025-11-04T00:06:00')
    x1,x2={"location":(0,0), "time":t1},{"location":(0,100), "time":t2}
    assert int(speed(x1,x2,10))==int(60.0) , "Should be 60 km/h"

def test_3():
    assert expected_time(10,10000)=="01:00:00" , "Should be 1H:0M:0S"

