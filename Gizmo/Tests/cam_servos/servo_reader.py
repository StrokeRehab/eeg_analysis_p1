#!/usr/bin/python3.6

"""
Servo Monitoring Script

This Python script initializes and controls two servo motors using the Adafruit ServoKit library.
It's used to continuously prints servo angles.
Exceptions are handled wihtout terminating, and logged with ExceptionLogger for troubleshooting.

Date: 2023
"""

import sys
import time
import traceback
from adafruit_servokit import ServoKit

from exception_logger import ExceptionLogger 

PAN_INDEX = 0         # ServoKit idx for servo in charge of horizontal movement.
TILT_INDEX = 1        # ServoKit idx for servo in charge of vertical movement.
ERROR_WAIT_TIME = 0.3 # Second(s) to wait after an exception or error is hit before continuing.
PROMPT_GENERAL_EXC = False # If true, when unaccounted (general) exception is first hit, halt and prompt user to continue.

kit = None

# Variables used for ExceptionLogs, 
# which generates a file report for every exception encountered while printing servo angles.
exception_logger = ExceptionLogger(script_name="servo_reader", ERROR_WAIT_TIME=ERROR_WAIT_TIME)

def print_new_line(line_count):
    """
    Print new lines in terminal. Used for clearing.
    """
    for i in range(line_count):
        print()

def yes_no_prompt(prompt):
    """
    Prompts user for 'yes'/'no'. Additionally accepts 'y'/'n'. Cap INsensitive.
    Returns:
        int: 1 if user enters 'yes', or 0 if user enters 'no'.
    """
    response = -1

    while response < 0:
        user_input = str(input(f"{prompt}  (Y/N): "))

        if user_input.lower() == "yes" or user_input.lower() == "y":
            response = 1
        elif user_input.lower() == "no" or user_input.lower() == "n":
            response = 0
        
        else:
            print("Response can only be 'yes'/'no' or 'y'/'n'. (Cap Insensitive).\n")
    
    return response

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
                exception_logger.log_exception(exc=e, file_notes="Occured within init_servo_kit()", enable_print=True)
                init_success = False
            
            if attempt_count % 10 == 0:
                print(f"{attempt_count}th attempt to initialize ServoKit object.\n")

    except KeyboardInterrupt:
        init_success = False
        print("\nUser manually interrupted ServoKit init.")
        exception_logger.write_reports()
    
    if init_success:
        print("Successfully initialized ServoKit object.")
        init_servo_config()
    else:
        print("Failed to initialize ServoKit object. Terminating.")
        sys.exit(1)



def init_servo_config():
    """
    This method sets up initial configurations for the servos.
    It is called in the init_servo_kit method.
    """
    global kit

    if kit is None:
        init_servo_kit()

    kit.servo[0].actuation_range = 180
    kit.servo[1].actuation_range = 180


def print_servo_angles(print_pause=0.7):
    """
    Continuously continues printing servo angles 
    until some exceptions (including keyboard interruption (Ctrl+C)) cause to abort.
    """
    print()

    if kit is None:
        init_servo_kit()

    try: # Outer try block allows exception reports to be written to files before exiting print loop.
        print("Preparing to print...\n")
        note = "Occured within print_servo_angles()."

        i = 0
        while True: 
            try:  # Inner-loop try block allows prints to continue despite errors.                
                # Print servo angle values
                i += 1
                time.sleep(print_pause) # seconds
                
                pan_angle = kit.servo[PAN_INDEX].angle 
                tilt_angle = kit.servo[TILT_INDEX].angle

                print(f"{i}) Servo angles:")
                print(f"Pan  (servo[{PAN_INDEX}]) angle: {pan_angle}")
                print(f"Tilt (servo[{TILT_INDEX}]) angle: {tilt_angle}")

                if i % 20 == 0:
                    print("\n(Enter Ctrl+C to gracefully terminate printing loop)")
                print()
            
            except IOError as io_e:
                exception_logger.log_exception(exc=io_e, file_notes=note, enable_print=True)
            
            except OSError as os_e:
                exception_logger.log_exception(exc=os_e, file_notes=note, enable_print=True)

            except Exception as e: # Deal with unaccounted exceptions with more caution
                exception_logger.log_exception(exc=e, enable_print=True, traceback_mssg=traceback_mssg, file_notes=f"General exception. {note}", delay_on_exception=False)

                if PROMPT_GENERAL_EXC and not exception_logger.contains_exception(e):
                    traceback_mssg = traceback.format_exc()
                    print(f"\nTraceback:\n {traceback_mssg}\n") # Print traceback info to aid user choice

                    print(f"\nException type:    {type(e).__name__}")
                    print(f"\nException message: {str(e)}")

                    # Because exception is unnacounted, have user confirm continuation.
                    keep_printing = yes_no_prompt("Unaccounted general exception. Continue printing servo angles?")   
                    
                    if keep_printing > 0:      
                        print(f"Waiting {ERROR_WAIT_TIME} seconds before continuing...\n")
                        time.sleep(ERROR_WAIT_TIME)

                    else:
                        print("Aborting.\n")
                        break                
    
    except KeyboardInterrupt:
        print("\nUser manually interrupted servo angle printing.\n")
    
    finally:
        print("Gracefully interrupted print_servo_angles().")
        exception_logger.write_reports()

if __name__ == "__main__":
    print_new_line(6) 
    print_servo_angles()
