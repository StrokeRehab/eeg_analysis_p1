#include <dlib/opencv.h>
#include <opencv2/opencv.hpp>
#include <dlib/image_processing/frontal_face_detector.h>
#include <dlib/image_processing/render_face_detections.h>
#include <dlib/image_processing.h>
#include <dlib/gui_widgets.h>
#include "httplib.h"
#include "TcpSocket.h"

#include <string>
#include <sstream>
#include <thread>
#include <algorithm>

#define FACE_DOWNSAMPLE_RATIO 4
#define SKIP_FRAMES 2

#define FACE_RADIUS 270

#define OPENCV_PIXELS_MAP_TO_PAN 40
#define OPENCV_PIXELS_MAP_TO_TILT 60

#define PAN_ERROR 3
#define TILT_ERROR 1

#define START_PAN 90
#define START_TILT 25

#define MIN_ANGLE 0
#define MAX_ANGLE 180

#define BASE_STATION_AGX_IP "10.18.96.109"
#define GIZMO_COMMANDER_PORT "26784"

int current_tilt = START_TILT;
int current_pan = START_PAN;
bool connectToCommander = true;

using namespace std; // Eventually remove this!

enum FaceDirection {
    FORWARD,
    LEFT,
    RIGHT,
    UP,
    DOWN,
    NONE
};

static const char *DirectionStrings[] = {"Forward", "Left", "Right", "Up", "Down", "None"};

/**
 * ServoAngle - Enumeration representing servo rotation angles.
 *
 * Defines two possible values, PAN and TILT, to represent rotation angles for servo motors.
 */
enum ServoAngle {
    PAN, // Horizontal rotation angle
    TILT // Vertical rotation angle
};

/**
 * GetDirectionString - Retrieves a string representation of a direction based on an integer value.
 *
 * @param val An integer value representing a direction (e.g., an index).
 * @return A pointer to a C-string representing the direction.
 */
const char *GetDirectionString(int val) { return DirectionStrings[val]; }

/**
 * get_3d_model_points - Retrieves 3D model points for facial feature landmarks.
 *
 * @return A vector of 3D model points representing facial feature landmarks. Used for facial pose estimation.
 */
std::vector<cv::Point3d> get_3d_model_points() {
    std::vector<cv::Point3d> modelPoints;

    modelPoints.push_back(cv::Point3d(0.0f, 0.0f, 0.0f)); // The first must be (0,0,0) while using POSIT
    modelPoints.push_back(cv::Point3d(0.0f, -330.0f, -65.0f));
    modelPoints.push_back(cv::Point3d(-225.0f, 170.0f, -135.0f));
    modelPoints.push_back(cv::Point3d(225.0f, 170.0f, -135.0f));
    modelPoints.push_back(cv::Point3d(-150.0f, -150.0f, -125.0f));
    modelPoints.push_back(cv::Point3d(150.0f, -150.0f, -125.0f));

    return modelPoints;
}

/**
 * get_2d_image_points - Extracts 2D image points from a dlib face landmark detection result.
 *
 * Given a dlib object representing facial landmarks, it extracts and 
 * returns a vector of 2D image points corresponding to specific facial features.
 *
 * @param d A dlib full_object_detection object containing facial landmark points.
 * @return A vector of 2D image points representing key facial features.
 */
std::vector<cv::Point2d> get_2d_image_points(dlib::full_object_detection &d) {
    std::vector<cv::Point2d> image_points;
    image_points.push_back(cv::Point2d(d.part(30).x(), d.part(30).y())); // Nose tip
    image_points.push_back(cv::Point2d(d.part(8).x(), d.part(8).y()));   // Chin
    image_points.push_back(cv::Point2d(d.part(36).x(), d.part(36).y())); // Left eye left corner
    image_points.push_back(cv::Point2d(d.part(45).x(), d.part(45).y())); // Right eye right corner
    image_points.push_back(cv::Point2d(d.part(48).x(), d.part(48).y())); // Left Mouth corner
    image_points.push_back(cv::Point2d(d.part(54).x(), d.part(54).y())); // Right mouth corner
    return image_points;
}

/**
 * get_camera_matrix - Computes the camera matrix for a given focal length and image center.
 *
 * Calculates and returns the camera matrix based on the provided focal length & image center coordinates. 
 * The camera matrix is a 3x3 matrix used in computer vision to represent the intrinsic parameters of a camera.
 *
 * @param focal_length The focal length of the camera lens.
 * @param center The image center coordinates (x, y).
 * @return A 3x3 camera matrix representing the camera's intrinsic parameters.
 */
cv::Mat get_camera_matrix(float focal_length, cv::Point2d center) {
    cv::Mat camera_matrix = (cv::Mat_<double>(3, 3) << focal_length, 0, center.x, 0, focal_length, center.y, 0, 0, 1);
    return camera_matrix;
}

/**
 * DisplayVersion - Displays the OpenCV library version.
 *
 * Prints the OpenVC library version info in the format "OpenCV version: major_version.minor_version.revision_num".
 */
void DisplayVersion() {
    std::cout << "OpenCV version: "
              << cv::getVersionMajor() << "." << cv::getVersionMinor() << "." << cv::getVersionRevision()
              << std::endl;
}

/**
 * ParseCLI - Parses command-line arguments to determine the input source and settings.
 *
 * The command-line arguments `argc` and `argv` are used to determine whether to use a server or default to camera input.
 * Depending, it constructs and returns a string representing the desired input source or video processing pipeline settings.
 *
 * @param argc The number of command-line arguments.
 * @param argv An array of character pointers containing the command-line arguments.
 * @return A string representing the input source or video processing pipeline settings.
 */
string ParseCLI(int argc, char **argv) {
    bool useIP = false;

    std::stringstream ss;

    // Determine input
    if (argc < 2) {
        std::cout << "No arguments, will default to camera!" << std::endl;
        useIP = false;

    } else if (3 == argc) {
        if (strncmp("-ip", argv[1], 3) == 0) {
            std::cout << "server input specified" << std::endl;
            useIP = true;

        } else if (strncmp("-c", argv[1], 2) == 0) {
            std::cout << "camera input specified" << std::endl;
            useIP = false;

        } else if (strncmp("-d", argv[1], 2) == 0) {
            std::cout << "Debug mode activated. TCP client to GizmoCommander will not be initiated." << std::endl;
            connectToCommander = false;
	    }

    } else if (3 < argc) {
        std::cout << "Too many arguments, will default to camera!" << std::endl;
    }

    // Determine the stringstream (ss)
    if (useIP) {
        ss << "http://" << argv[2] << "/";

    } else {
        ss << "nvarguscamerasrc !  video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=21/1 ! nvvidconv flip-method=2 ! video/x-raw, width=1280, height=720, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink";
    }

    std::cout << "Reading input from: " << (useIP ? "a server" : "the camera") << ". Settings: " << ss.str() << std::endl;

    return ss.str();
}
/**
 * SetAngleRotation - Adjusts the rotation of a servo motor based on the desired angle and distance.
 *
 * Adjusts the rotation of a servo motor based on the desired angle and the corresponding distance value. 
 * The function takes into account the angle type (PAN or TILT) and applies appropriate scaling/error checks.
 *
 * @param distance The distance representing the rotation to be applied.
 * @param angle The type of angle to adjust (PAN or TILT).
 */
void SetAngleRotation(int distance, ServoAngle angle) {
    float rotation = distance;

    if (ServoAngle::PAN == angle) {
        rotation /= OPENCV_PIXELS_MAP_TO_PAN;

        if (abs(rotation) < PAN_ERROR) {
            return; // Return if the rotation is within tolerance.
        }

        current_pan += rotation;

    } else if (ServoAngle::TILT == angle) {
        rotation /= OPENCV_PIXELS_MAP_TO_TILT;

        if (abs(rotation) < TILT_ERROR) {
            return; // Return if the rotation is within tolerance.
        }

        current_tilt -= rotation;

    } else {
        std::cout << "Unknown angle: " << angle << "!" << std::endl;
    }
}

/**
 * do_http_get - Send an HTTP GET request to adjust camera's pan/tilt angles.
 *
 * Adjusts the pan-tilt angles of a camera by sending an HTTP GET request to the host and port. 
 * It first sets the pan and tilt angles using the provided values (x and y), 
 * clamps them within the valid range (0 to 180 degrees),
 * then constructs an HTTP request URI (uniform resource ID) with the adjusted angles. 
 *
 * @param host The hostname or IP address of the target HTTP server.
 * @param port The port number to use for the HTTP connection.
 * @param x The desired pan angle to set.
 * @param y The desired tilt angle to set.
 */
void do_http_get(std::string host, int port, int x, int y) {
    SetAngleRotation(x, ServoAngle::PAN);
    SetAngleRotation(y, ServoAngle::TILT);

    // Ensure pan/tilt are within valid range.
    std::clamp(current_pan, 0, 180);
    std::clamp(current_tilt, 0, 180);

    int pan = current_pan;
    int tilt = current_tilt;

    std::cout << "PAN: " << pan << " TILT: " << tilt << std::endl;

    // Create an HTTP client and construct the URI for the camera adjustment.
    httplib::Client cli(host, port);
    std::stringstream uri;
    uri << "/aim_camera?pan=" << pan << "&tilt=" << tilt;

    if (auto res = cli.Get(uri.str())) { // Send HTTP GET request.
        if (res->status == 200)  {
            std::cout << res->body << std::endl; // Display HTTP request body.
        }

    } else { // Display HTTP errors if any.
        auto err = res.error();
        std::cout << "HTTP error: " << httplib::to_string(err) << std::endl;
    }
}

/**
 * openCam - Tries 
*/

/**
 * main - Entry point for the facial landmark detection and camera control program.
 *
 * The main function that initializes the application. 
 * 1- Displays the OpenCV library version
 * 2- Establishes a TCP connection to a commander (if enabled)
 * 3- Opens the camera for capturing video, and then continuously processes frames
 * 4- Detects facial landmarks and determines the direction of the face relative to the camera.
 * 5- Adjusts camera angles by using HTTP requests. 
 *
 * @param argc The number of command-line arguments.
 * @param argv An array of character pointers containing the command-line arguments.
 * @return An integer status code (0 for success, non-zero for failure).
 */
int main(int argc, char **argv) {
    DisplayVersion(); // Display OpenCV library version.

    TcpSocket* gizmoCommandSocket = nullptr; // Initialize a pointer to a TCP socket for commander communication.

    try {
        if (connectToCommander) { // If enabled, create a TCP socket for commander communication.
            gizmoCommandSocket = new TcpSocket(GIZMO_COMMANDER_PORT, BASE_STATION_AGX_IP);
        }

        cv::VideoCapture cap; // Open and configure the camera.
        cap.open(ParseCLI(argc, argv));

        if (!cap.isOpened()) { // Check if the camera is successfully opened.
            cerr << "Unable to connect to the camera" << endl;
            return 1;
        }

        // Initialize variables for frame rate calculation.
        double fps = 30.0; // Placeholder. Actual value calculated after 100 frames.
        cv::Mat im;

        // Get the first frame and allocate memory.
        cap >> im;
        cv::Mat im_small, im_display;
        cv::resize(im, im_small, cv::Size(), 1.0 / FACE_DOWNSAMPLE_RATIO, 1.0 / FACE_DOWNSAMPLE_RATIO);
        cv::resize(im, im_display, cv::Size(), 0.5, 0.5);
        cv::Size size = im.size();

        // Load face detection and pose estimation models.
        dlib::frontal_face_detector detector = dlib::get_frontal_face_detector();
        dlib::shape_predictor pose_model;
        dlib::deserialize("shape_predictor_68_face_landmarks.dat") >> pose_model; // Try 5 face landmarks as well.

        int count = 0;
        std::vector<dlib::rectangle> faces;

        // Grab and process frames until the main window is closed by the user.
        double t = (double)cv::getTickCount();
        while (1) {
            // Initialize frame time measurement if count is 0.
            if (count == 0) {
                t = cv::getTickCount();
            }

            // Capture a frame from the camera.
            cap >> im;

            // Resize the image for face detection.
            cv::resize(im, im_small, cv::Size(), 1.0 / FACE_DOWNSAMPLE_RATIO, 1.0 / FACE_DOWNSAMPLE_RATIO);

            // Change to dlib's image format. No memory is copied.
            dlib::cv_image<dlib::bgr_pixel> cimg_small(im_small);
            dlib::cv_image<dlib::bgr_pixel> cimg(im);

            // Detect faces periodically.
            if (count % SKIP_FRAMES == 0) {
                faces = detector(cimg_small);
            }

            // Pose estimation and camera control for each detected face.
            std::vector<cv::Point3d> model_points = get_3d_model_points();
            std::vector<dlib::full_object_detection> shapes;

            for (unsigned long i = 0; i < faces.size(); ++i) {
                // Extract face rectangle.
                dlib::rectangle r(
                    (long)(faces[i].left() * FACE_DOWNSAMPLE_RATIO),
                    (long)(faces[i].top() * FACE_DOWNSAMPLE_RATIO),
                    (long)(faces[i].right() * FACE_DOWNSAMPLE_RATIO),
                    (long)(faces[i].bottom() * FACE_DOWNSAMPLE_RATIO));

                // Get facial landmarks.
                dlib::full_object_detection shape = pose_model(cimg, r);
                shapes.push_back(shape);
                std::vector<cv::Point2d> image_points = get_2d_image_points(shape);

                // Calculate camera parameters and angles.
                double focal_length = im.cols;
                cv::Mat camera_matrix = get_camera_matrix(focal_length, cv::Point2d(im.cols / 2, im.rows / 2));
                cv::Mat rotation_vector;
                cv::Mat rotation_matrix;
                cv::Mat translation_vector;
                cv::Mat dist_coeffs = cv::Mat::zeros(4, 1, cv::DataType<double>::type);
                cv::solvePnP(model_points, image_points, camera_matrix, dist_coeffs, rotation_vector, translation_vector);

                // Project nose endpoint to 2D and draw line.
                std::vector<cv::Point3d> nose_end_point3D;
                std::vector<cv::Point2d> nose_end_point2D;
                nose_end_point3D.push_back(cv::Point3d(0, 0, 1000.0));
                cv::projectPoints(nose_end_point3D, rotation_vector, translation_vector, camera_matrix, dist_coeffs, nose_end_point2D);
                cv::line(im, image_points[0], nose_end_point2D[0], cv::Scalar(255, 0, 255), 10);

                // Calculate distance from the center.
                double dist = cv::norm(image_points[0] - nose_end_point2D[0]);

                // Calculate middle point.
                CvPoint middle;
                cv::Size sz = im.size();
                middle.x = sz.width / 2;
                middle.y = sz.height / 2;
                int dist_from_middle = image_points[0].x - middle.x;

                // Send HTTP requests for camera control periodically.
                if (0 == (count % 4)) {
                    std::thread http_thread(do_http_get, "localhost", 5000, image_points[0].x - middle.x, image_points[0].y - middle.y);
                    http_thread.detach();
                }

                // Determine face direction.
                bool isFacingCamera = (dist < FACE_RADIUS);
                FaceDirection direction = NONE;

                // Update camera control.
                if (!isFacingCamera) { 
                    if (connectToCommander) { gizmoCommandSocket->send((char*)"0", 1); }

                    if (image_points[0].x > nose_end_point2D[0].x) {
                        direction = LEFT;
                    } else { direction = RIGHT; }

                } else {
                    direction = FORWARD;
                    if (connectToCommander) { gizmoCommandSocket->send((char*)"1", 1); }
                }

                // Draw direction and face radius on the image.
                cv::Scalar radiusColor = (isFacingCamera) ? cv::Scalar(0, 255, 0) : cv::Scalar(0, 0, 250);
                cv::putText(im, cv::format("Facing %s", GetDirectionString(direction)), cv::Point(50, size.height - 50), cv::FONT_HERSHEY_SIMPLEX, 1.5, cv::Scalar(0, 0, 255), 5);
                cv::circle(im, image_points[0], FACE_RADIUS, radiusColor, 3);
            }

            // Resize the image for display and show it.
            im_display = im;
            cv::resize(im, im_display, cv::Size(), 0.5, 0.5);
            cv::imshow("Fast Facial Landmark Detector", im_display);

            // Check for user key press events.
            if (cv::waitKey(5) >= 0) {
                break;
            }

            // Update frame count and calculate frame rate.
            count++;
            if (count == 100) {
                t = ((double)cv::getTickCount() - t) / cv::getTickFrequency();
                fps = 100.0 / t;
                count = 0;
            }
        }

    } catch (dlib::serialization_error &e) { // Model file serialization exception.
        cout << "You need dlib's default face landmarking model file to run this example." << endl;
        cout << "You can get it from the following URL: " << endl;
        cout << "   http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2" << endl;
        cout << endl << e.what() << endl;

    } catch (exception &e) { // General exceptions.
        cout << e.what() << endl;
    }

    return 0;
}
