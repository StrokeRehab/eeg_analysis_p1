#!/usr/bin/python3.6

"""
Gizmo's camera servo tests.
Run main logic to randomly change servo horizontal and vertical movement, 
and print their values. 
"""

import sys
import time
import random
import traceback
from adafruit_servokit import ServoKit

wait_time = 0.5

MIN_ANGLE = 0
MAX_ANGLE = 180

PAN_INDEX = 0         # ServoKit idx for servo in charge of horizontal movement.
TILT_INDEX = 1        # ServoKit idx for servo in charge of vertical movement.
ERROR_WAIT_TIME = 0.3 # Second(s) to wait after an exception or error is hit before continuing.
PROMPT_GENERAL_EXC = False # If true, when unaccounted (general) exception is first hit, halt and prompt user to continue.

print_error_count = 0
pan_error_count = 0
tilt_error_count = 0

kit = None


def print_new_line(line_count):
    """
    Print new lines in terminal. Used for clearing.
    """
    for i in range(line_count):
        print()

def init_servo_kit():
    """
    Loops through attempts to initialize ServoKit object, while logging failed attempts.
    Handy ServoKit resource: https://cdn-learn.adafruit.com/downloads/pdf/adafruit-16-channel-servo-driver-with-raspberry-pi.pdf

    If initialization succesful, calls init_servo_config() to handle initial servo configurations.
    Otherwise terminates script.
    """
    global kit

    print("Initializing ServoKit object...")

    init_success = False
    try:
        attempt_count = 0
        while not init_success:
            attempt_count +=1 

            try:
                kit = ServoKit(channels=16) 
                time.sleep(0.05)
                init_success = True

            except Exception as e:
                init_success = False
            
            if attempt_count % 10 == 0:
                print(f"{attempt_count}th attempt to initialize ServoKit object.\n")

            else: 
                print("Failed to initialize ServoKit object. Terminating.")
                sys.exit(1)

    except KeyboardInterrupt:
        init_success = False
        print("\nUser manually interrupted ServoKit init.")
    
    print("Successfully initialized ServoKit object.")
    init_servo_config()

def init_servo_config():
    """
    This method sets up initial configurations for the servos.
    It is called in the init_servo_kit method.
    """
    global kit

    if kit is None:
        init_servo_kit()

    kit.servo[0].actuation_range = MAX_ANGLE
    kit.servo[1].actuation_range = MAX_ANGLE

def print_angles():
    """
    Prints pan and tilt angles.
    """
    try:
        pan_angle = kit.servo[PAN_INDEX].angle 
        tilt_angle = kit.servo[TILT_INDEX].angle

        print(f"Pan  angle: {pan_angle}")
        print(f"Tilt angle: {tilt_angle}\n")
    
    except Exception as e:
        print_error_count += 1
        traceback_mssg = traceback.format_exc()

        #print(f"\nTraceback:\n {traceback_mssg}\n") 
        print(f"\nException type:    {type(e).__name__}")
        print(f"\nException message: {str(e)}")
        print(f"Encountered error printing servo angles ({print_error_count}).\n")


def verify_angle(angle):
    if angle < MIN_ANGLE:
        print(f"Angle {angle} is too low. Use {MIN_ANGLE} instead.")
        angle = MIN_ANGLE
    
    elif angle > MAX_ANGLE:
        print(f"Angle {angle} is too high. Use {MAX_ANGLE} instead.")
        angle =  MAX_ANGLE
    
    return angle

def move_pan(angle):
    angle = verify_angle(angle)
    print(f"Setting pan (servo[{PAN_INDEX}]) angle to {angle}.")
    kit.servo[PAN_INDEX].angle = angle

def move_tilt(angle):
    angle = verify_angle(angle)
    print(f"Setting tilt (servo[{TILT_INDEX}]) angle to {angle}.")
    kit.servo[TILT_INDEX].angle = angle


def move_randomly():
    pan = random.randint(MIN_ANGLE, MAX_ANGLE)
    tilt = random.randint(MIN_ANGLE, MAX_ANGLE)

    move_pan(pan)
    move_tilt(tilt)


if __name__ == "__main__":
    print_new_line(2) # Terminal readability 

    # First test boundaries.
    move_pan(MAX_ANGLE)
    move_tilt(MAX_ANGLE)
    print_angles()
    time.sleep(wait_time)

    move_pan(MIN_ANGLE)
    move_tilt(MIN_ANGLE)
    print_angles()
    time.sleep(wait_time)

    while True:
        move_randomly()
        print_angles()
        time.sleep(wait_time)

    


    
