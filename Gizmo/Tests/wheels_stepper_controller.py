# coding=utf8

# https://github.com/nBestauros/ESP32StepperController/blob/main/i2ctest.py
# https://github.com/MaryamM4/SRP/blob/main/stepper-controller/simultaneous_stepper.py
# https://github.com/MaryamM4/SRP/blob/main/stepper-controller/server.py

# Style: https://www.python.org/doc/essays/styleguide/

# To be used by:
# https://github.com/the-innovative-bun/stroke-rehab/blob/GizmoCommander/GizmoCommander/gizmoCommander.py

import time
from smbus2 import SMBus # Used for communicating with devices over I2C (SMBus) Protocol
import Jetson.GPIO as GPIO
import random
import atexit # Used for registering cleanup function when program exits

class GizmoDriver: 
    """
    A class for controlling two stepper motors interfaced to the Jetson Nano via an Adafruit ESP32-S2 Feather.

    Attributes:
        interrupt_pin (int):  
        last_execution_time (int):
        last_interrupt_time (int): 

        FOLLOWER_ADDRESS (hex):
        FORWARD, BACKWARD, TURN_FORWARD, TURN_BACKWARD (hex): 
            Variable representation of hex instructions for I2C communication, for controlling direction. 
        
    """

    FOLLOWER_ADDRESS = 0x23 # I2C Address

    FORWARD = 0x01
    BACKWARD = 0x00 # FLIPPED IN ARDUINO CODE.
    TURN_FORWARD = 0x02
    TURN_BACKWARD = 0x03

    def __init__(self, interrupt_pin):
        """
        Initialize GizmoDriver instance.

        Args:
            interrupt_pin (int): Pin used for interrupt handling
        """

        self.interrupt_pin = interrupt_pin

        self.setup_GPIO()
        
        # Set initial time values
        init_time = self.get_current_time_micros()
        self.last_execution_time = init_time
        self.last_interrupt_time = init_time

        self.enable_interrupts()

    def get_current_time_micros(self):
        """
        Returns:
            int: Current time in microseconds.
        """
        return int(time.time() * 1000000)
    
    def setup_GPIO(self):
        GPIO.setmode(GPIO.BOARD) # Change to BCM, better practice
        GPIO.setup(self.interrupt_pin, GPIO.IN)
    
    @atexit.register
    def cleanup_gpio():
        """
        This method is registered with atexit to cleanup GPIO when the program exits.
        """
        GPIO.cleanup()

    def enable_interrupts(self):
        """
        Enable GPIO interrupt detection on the interrupt pin.

        This function sets up an interrupt callback function to trigger when
        the specified GPIO interrupt pin goes high (RISING edge).
        """
        GPIO.add_event_detect(self.interrupt_pin, GPIO.RISING, callback=self.pin_change_callback) # safety manuever interrupt whenever interrupt_pin goes high

    def pin_change_callback(self):
        self.disable_interrupts()

        try:
            current_time = self.get_current_time_micros()

            if current_time - self.last_execution_time < 3000000:
                self.enable_interrupts()
                return
            
            print("Interrupted")

            self.last_execution_time = current_time
            self.last_interrupt_time = current_time
            
            bus = SMBus(1)
            num = random.randint(1,2)

            # Bytes values used as response for emergency interrupt 
            emergency_data_1 = [0x03] # TURN_BACKWARD
            emergency_data_1 += self.convert_to_hex_bytes(6000)
            emergency_data_1.append(self.convert_to_signed_hex_byte(-70))

            emergency_data_2 = [0x03] # TURN_BACKWARD
            emergency_data_2 += self.convert_to_hex_bytes(6000)
            emergency_data_2.append(self.convert_to_signed_hex_byte(70))

            if num == 1:
                emergency_data = emergency_data_1

            elif num == 2:
                emergency_data = emergency_data_2

            for i in range(len(emergency_data)):
                bus.write_byte(self.FOLLOWER_ADDRESS, emergency_data[i])
                print("Sent: ", emergency_data[i])
        
        except Exception as e:
            print(f"{e}")
            return
        
        finally:
            bus.close()
            self.enable_interrupts()
            return

    def disable_interrupts(self):
        """
        Disable GPIO interrupt.
        """
        GPIO.remove_event_detect(self.interrupt_pin)

    def convert_to_hex_bytes(self, number):
        """
        Convert an integer to a list of little-endian hex bytes.
        Used to convert a given distance into a list of hex instructions (for I2C movement commands).

        Args:
            number (int): The number to be converted.

        Returns:
            list (size of 4): A list of little-endian hex bytes representing the number.
        """

        if number < 0 or number > 0xFFFFFFFF:
            raise ValueError("Number is out of range: [0, 0xFFFFFFFF]")
        
        hex_string = hex(number)[2:].zfill(8)
        hex_bytes = [int(hex_string[i:i+2], 16) for i in range (6, -1, -2)] # store in little endian.

        return hex_bytes

    def convert_to_signed_hex_byte(self, number):
        """
        Convert a signed integer to a hex byte.
        Used to convert an angle to hex instructions (for I2C movement commands).

        Args:
            number (int): The signed integer to be converted.

        Returns:
            int: A hex byte representing the signed integer.
        """

        if number < -90 or number > 90:
            raise ValueError("Number is out of range: [-90, 90]")

        signed_byte = number & 0xFF

        return signed_byte


    def convert_to_I2C_instruction(self, distance, direction, angle=0):
        """
        This method "interfaces" the program with I2C communication be converting to 
        a list of hex commands of the following format:
        [type, dist, dist, dist, dist, angle]

        Angle is ignored in forward and backward cases, but it should still be sent. 

        Args:
            distance (int): dist
            direction (hex): Determines 'type'. Must be this object's FORWARD, BACKWARD, TURN_FORWARD, or TURN_BACKWARD hex commands.
            angle (int): The angle for the the robot to turn. Only applicable for TURN_ directions.
        """
        i2c_intructions = [direction]
        i2c_intructions += self.convert_to_hex_bytes(distance)
        i2c_intructions.append(self.convert_to_signed_hex_byte(angle))

        return i2c_intructions
    
    def _send_to_bus(self, data):
        """
        Sends byte of data at a time to the I2C address from list of instructions.

        Args:
            data (list of hex): Format should be [type, dist, dist, dist, dist, angle].
        """
        self.last_execution_time = self.get_current_time_micros()

        try:
            self.disable_interrupts()

            bus = SMBus(1)

            for i in range(len(data)):
                bus.write_byte(self.FOLLOWER_ADDRESS, data[i])
        
        except Exception as e:
            print(f"{e}")

        finally:
            bus.close()
            self.enable_interrupts()


    def move(self, distance, direction, angle=0):
        """
        Move the robot the specified distance, direction and angle:

        Args:
            distance (int): Steps
            direction (hex): This should be this object's FORWARD, BACKWARD, TURN_FORWARD, or TURN_BACKWARD hex commands.
            angle (int): The angle for the the robot to turn. Only applicable for TURN_ directions.
        """
        print("Moving.")
        bus_instr = self.convert_to_I2C_instruction(distance, direction, angle)
        self._send_to_bus(bus_instr)



if __name__ == "__main__":
    move_distnce = 3500
    pause_time = 0.3

    gizmo_driver = GizmoDriver(interrupt_pin=29)

    gizmo_driver.move(distance=move_distnce, direction=gizmo_driver.FORWARD)
    time.sleep(pause_time)
    gizmo_driver.move(distance=move_distnce, direction=gizmo_driver.BACKWARD)





