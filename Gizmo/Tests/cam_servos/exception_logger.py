#!/usr/bin/python3.6

"""
Exception Logging Utility

This ExceptionLogger class logs exceptions that occur in a python script.
It creates a log file for each different exception type that is reported, 
including details such as traceback info and the number of occurences.

Date: 2023

Needed updates:
- Allow specifying path to store logs, either by prompt or as an init var.
- Better handle exceptions regarding file writing faults, rather than just printing a message and quitting.
"""

import os
import time
import traceback

class ExceptionLogger:
    folder_path = ""                 # Path where reports are stored
    reporting_script_name = ""       # Script where exceptions occurred
    exception_reports = {}           # Dictionary. Maps exception name to details
                                     # Note to add to file
    note_prepend = "This log contains info from the first occurence of exception in the most recent execution of the reporting script.\nOnly the exception occurence count was updated."

    def __init__(self, script_name, ERROR_WAIT_TIME=0.3):     
        """
        ExceptionLogger object is in charge of logging exceptions that occur in a script (each different error once).
        
        Args:
            script_name    (String): The name of the script reporting the exceptions.
            ERROR_WAIT_TIME (float): Seconds to pause after an every exception (new or not) is reported (to log_exception()).
        
        """   
        self.ERROR_WAIT_TIME = float(max(ERROR_WAIT_TIME, 0))
        self.reporting_script_name = script_name
        
        prepending_directory = os.getcwd()
        foldername = f"{script_name}_exlog"
        self.folder_path = os.path.join(prepending_directory, foldername)

        os.makedirs(self.folder_path, exist_ok=True) # exist_ok=True: Raise no error if the folder already exists.

    
    def add_exception(self, exception, exception_count=1, traceback_info="", notes=""):
        """
        Stores information on exception in object's dictionary.

        Args:
            exception (exception): The exception that occured in the reporting script.
            exception_count (int): The number of times the exception occured (if recurring).
            traceback_info (String): The traceback message.
            notes (String): Any additional notes to be included in file. Configurable. 
        """
        exception_type = type(exception).__name__
        exception_mssg = str(exception)

        self.exception_reports[exception_type] = {
            "exception_message": exception_mssg,
            "exception_count": exception_count,
            "traceback": traceback_info,
            "notes": notes
        }
    
    def contains_exception(self, exception_type):
        """
        Retuns True if dictionary already contains the exception type key (Generally type(exception).__name__).
        """
        if not isinstance(exception_type, str):
            exception_type = type(exception_type).__name__

        return bool(exception_type in self.exception_reports)
    
    def update_exception_count(self, exception_type, new_exception_count=0):
        """
        Updates exception_count only for corresponding exception key in dictionary.
        If exception not already stored, does nothing. 

        Args:
            exception_type   (String): Typically type(exception).__name__
                                       Can handle being passed an exception instead. 
            new_exception_count (int): Updated number of occurences of exception.
                                       By default set to 0, meaning to increment the existing count.
        """
        if not isinstance(exception_type, str):
            exception_type = type(exception_type).__name__

        if self.contains_exception(exception_type):
            if new_exception_count < 1:
                new_exception_count = self.exception_reports[exception_type]["exception_count"] + 1

            self.exception_reports[exception_type]["exception_count"] = new_exception_count

        else:
            warning_mssg = "exception_logger add_exception error: Cannot update exception_count for an exception that has not already been stored."
            print(f"\n{warning_mssg}\n")


    def print_to_console(self, exc):
        """
        This method prints warning messages concerning the exception that exists in ExceptionLogger's dictionary. 
        Only prints exception type, message, and number of occurences.

        Args:
            exc (exception): The exception to print.
        """
        exception_type = type(exc).__name__

        if self.contains_exception(exception_type):
            error_count = self.exception_reports[exception_type]["exception_count"]
        else:
            error_count = 0

        mssg_allignment = 20
        print(f"\nException type:    {exception_type: <{mssg_allignment}}")
        print(f"Exception message: {str(exc): <{mssg_allignment}}")
        print(f"Exception count:   {error_count: <{mssg_allignment}}")

    
    def log_exception(self, exc, traceback_mssg="", file_notes="", enable_print=False, delay_on_exception=True):
        """
        This method is to be called at the occurence of an exception (within the reporting script). 
        If the exception is not already logged, stored it's type, message, traceback, and note information. Otherwise just updates occurence count.

        Args:
            exc           (exception): The exception that occured.
            traceback_mssg   (String): The traceback message, typically traceback.format_exc().
            file_notes       (String): Notes to write to file on save.
            enable_print       (bool): Wether to print exception message to console.
            delay_on_exception (bool): Allows pausing ERROR_WAIT_TIME secs after occurence of exception (True recommended).
        """
        exception_type = type(exc).__name__

        if not traceback_mssg:
            recent_traceback_mssg = traceback.format_exc()
            traceback_mssg = f"Traceback was not provided to logger. Traceback at function is provided instead.\n{recent_traceback_mssg}"

        # Update ExeptionLogger's dictionary
        if not self.contains_exception(exception_type):
            self.add_exception(exception=exc, traceback_info=traceback_mssg, notes=file_notes)
        
        else:
            self.update_exception_count(exception_type)
        
        # Print message to console if applicable
        if enable_print:
            self.print_to_console(exc)
        
        # After an exception is reported, pause ERROR_WAIT_TIME seconds before continuing
        delay = float(self.ERROR_WAIT_TIME)

        if delay_on_exception and (delay > 0):
            print(f"Waiting {delay} seconds before continuing...\n")
            time.sleep(delay)

        elif enable_print:
            print()
    
    def write_reports(self):
        """
        This function is to be called in the finally section or after a try-exception block.
        Failing to do so means no files will be written.

        Writes file reports for each exception stored in dictionary.
        Includes exception type, message, additional notes, and traceback. 

        Returns:
            bool: Whether the file was successfully written.
        """
        successful_write = False
        print(f"Attempting to write logs to '{self.folder_path}'")

        try:
            for exception_type, value in self.exception_reports.items():
                filename = f"{self.folder_path}/{exception_type}.txt"

                with open(filename, 'w') as file:
                    mssg_allignment = 20
                    
                    file.write(f"\nException Type:    {exception_type: <{mssg_allignment}}\n")
                    file.write(f"Exception Message: {value['exception_message']: <{mssg_allignment}}\n")
                    file.write(f"{value['exception_count']} occurrence(s) in {self.reporting_script_name}\n")

                    file.write(f"\nNotes:\n{value['notes']}\n{self.note_prepend}\n")
                    file.write(f"\nTraceback:\n{value['traceback']}\n")

            successful_write = True

        except Exception as e:
            print(e)
            print("\nERROR: ExceptionLogger failed to write exception reports to files.\n")
            successful_write = False
        
        if successful_write:
            print("ExceptionLogger succesfully wrote to files.\n")
        
        return successful_write





