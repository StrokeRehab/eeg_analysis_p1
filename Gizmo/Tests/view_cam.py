#!/usr/bin/python3.6

import cv2
import time
import traceback

def basic_cam_test(valid_wait_time=0.1, invalid_wait_time=0.4, dispW=1280, dispH=960, flip=2):
    try: 
        print(f"\ncv2 Version: {cv2.__version__}\n")

        #camSet = 'nvarguscamerasrc !  video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=21/1 ! nvvidconv flip-method=2 ! video/x-raw, width=480, height=680, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
        camSet = 'nvarguscamerasrc !  video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=21/1 ! nvvidconv flip-method=2 ! video/x-raw, width=1280, height=720, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
        cam = cv2.VideoCapture(camSet)

        invalid_frame_count = 0
        while True:
            ret, frame = cam.read()

            if not ret:
                print(f"\nret: {ret}")

            if frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
                cv2.imshow('piCam', frame)
                time.sleep(valid_wait_time)

            else:
                invalid_frame_count +=1

                if frame is None:
                    print(f"[Invalid count: {invalid_frame_count}]  Empty frame. ")
                else:
                    print(f"[Invalid count: {invalid_frame_count}].   Frame height = {frame.shape[0]}, Frame width = {frame.shape[1]}.")

                time.sleep(invalid_wait_time)

            if cv2.waitKey(1)==ord('q'):
                print("\nUser ended process with 'q'.")
                break
    
    except KeyboardInterrupt:
        print("\nUser manually interrupted process.")
    
    except Exception as e:
        print("\nbasic_cam_test error:")
        print(f"{traceback.format_exc()}\n")
        print(f"Exception type:\n {type(e).__name__}\n")
        print(f"Exception message:\n {str(e)}\n")
    
    finally:
        print("Releasing camera and destroying windows...\n")
        cam.release
        cv2.destroyAllWindows()


if __name__ == "__main__":
    basic_cam_test()
