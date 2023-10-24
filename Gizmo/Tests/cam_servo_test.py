#!/usr/bin/python3.6

"""
Gizmo's camera servo tests.
Run main logic to randomly change servo horizontal and vertical movement,
and print their values.
"""

import atexit
import sys
import time
import random
import traceback
from adafruit_servokit import ServoKit

wait_time = 3
error_wait_time = 1

MIN_ANGLE = 0
MAX_ANGLE = 180

PAN_INDEX = 0         # ServoKit idx for servo in charge of horizontal movement.
TILT_INDEX = 1        # ServoKit idx for servo in charge of vertical movement.
ERROR_WAIT_TIME = 0.3 # Second(s) to wait after an exception or error is hit before continuing.
PROMPT_GENERAL_EXC = False # If true, when unaccounted (general) exception is first hit, halt and prompt user to continue.

INIT_SUCCESFFUL = False

def init_servo_kit(max_attempts=5):
    global INIT_SUCCESFFUL 
    attempt_count = 0
    not_initialized = True

    while not INIT_SUCCESFFUL and (attempt_count <= max_attempts):
        attempt_count += 1

        try:
            print(f"\nAttempt {attempt_count}/{max_attempts} to initialize servo kit and configure actuation range.")

            kit = ServoKit(channels=16)
            print("Initialized ServoKit.")

            kit.servo[0].actuation_range = MAX_ANGLE
            kit.servo[1].actuation_range = MAX_ANGLE
            print(f"Configured actuation range to {MAX_ANGLE}.")

            INIT_SUCCESFFUL = True
        
        except Exception as err:
            INIT_SUCCESFFUL = False

            if attempt_count == max_attempts: 
                print(f"\n{traceback.format_exc()}\n")
                print(str(err))
                print(f"\nException type: {type(err).__name__}")
                print("Failed to initialize servo kit. Aborting.\n")
                sys.exit(1)
            
            else: 
                print(f"Failed to initialize servo kit. Exception type: {type(err).__name__}")
                print(f"Retrying in {error_wait_time} second(s)...\n")
                time.sleep(error_wait_time)

    return kit

kit = init_servo_kit()

@atexit.register
def cleanup_gpio():
    """
    This method is registered with atexit to execute when the program exits.
    """
    global INIT_SUCCESFFUL

    if INIT_SUCCESFFUL:
        reset_servos()

def reset_servos():
    print("\nResetting servo angles...")
    move_pan(0)
    move_tilt(0)

def print_new_line(line_count):
    """
    Print new lines in terminal. Used for clearing.
    """
    for i in range(line_count):
        print()

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
        #traceback_mssg = traceback.format_exc()
        #print(f"\nTraceback:\n {traceback_mssg}\n")
        
        print(f"Encountered error printing servo angles. Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}\n")


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
    print(f"Setting pan to {angle}.")

    try:
        kit.servo[PAN_INDEX].angle = angle
    except Exception as e:
        print(e)

def move_tilt(angle):
    angle = verify_angle(angle)
    print(f"Setting tilt to {angle}.")

    try:
        kit.servo[TILT_INDEX].angle = angle
    except Exception as e:
        print(e)

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

