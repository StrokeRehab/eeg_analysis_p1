#!/usr/bin/python3.6

from adafruit_servokit import ServoKit

pan_index = 0
tilt_index = 1

min_angle = 0
max_angle = 180

myKit = ServoKit(channels=16)

def verify_angle(angle):
    if angle < min_angle:
        print(f"Angle {angle} is too low. Use {min_angle} instead.")
        angle = min_angle
    
    elif angle > max_angle:
        print(f"Angle {angle} is too high. Use {max_angle} instead.")
        angle =  max_angle
    
    return angle

def move_pan(angle):
    angle = verify_angle(angle)
    print(f"Setting pan (servo[{pan_index}]) angle to {angle}.")
    myKit.servo[pan_index].angle = angle

def move_tilt(angle):
    angle = verify_angle(angle)
    print(f"Setting tilt (servo[{tilt_index}]) angle to {angle}.")
    myKit.servo[tilt_index].angle = angle


if __name__ == '__main__':
    move_tilt(45)
    move_pan(45)
    print()


