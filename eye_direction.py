import cv2
import dlib
import numpy as np
import os
from datetime import datetime
from scipy.spatial import distance as dist
import time

# Load pre-trained models
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("C:/Program Files/Python312/Main Project/Interface/OCULISE/shape_predictor_68_face_landmarks.dat")  # Download from dlib's website
down_correction=''

# Eye indices based on the facial landmark points
(left_eye_start, left_eye_end) = (36, 41)
(right_eye_start, right_eye_end) = (42, 47)

#for long-short blink
blink_counter = 0

ear_values=[]

def eye_aspect_ratio(eye):
    # Compute the euclidean distances between the vertical eye landmarks
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    
    # Compute the euclidean distance between the horizontal eye landmarks
    C = dist.euclidean(eye[0], eye[3])
    
    # Compute the eye aspect ratio
    ear = (A + B) / (2.0 * C)
    return ear

def detect_face_landmarks(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:
        landmarks = predictor(gray, face)
        landmarks_np = np.zeros((68, 2), dtype=int)
        
        for i in range(0, 68):
            landmarks_np[i] = (landmarks.part(i).x, landmarks.part(i).y)
        
        return face, landmarks_np
    return None, None

def extract_eye_regions(landmarks):
    left_eye = landmarks[36:42]  # Left eye landmarks
    right_eye = landmarks[42:48] # Right eye landmarks

    left_eye_rect = cv2.boundingRect(np.array(left_eye))
    right_eye_rect = cv2.boundingRect(np.array(right_eye))

    return left_eye_rect, right_eye_rect

def detect_pupil(eye_region, threshold_value):
    if eye_region.any():
        gray_eye = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)
        _, binary_eye = cv2.threshold(gray_eye, threshold_value, 255, cv2.THRESH_BINARY_INV)
        
        contours, _ = cv2.findContours(binary_eye, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            moments = cv2.moments(largest_contour)
            if moments['m00'] != 0:
                cx = int(moments['m10'] / moments['m00'])
                cy = int(moments['m01'] / moments['m00'])
                return (cx, cy)
        return None
    else:
        print("no eye region")
def calculate_ratios(eye_center, pupil_position, eye_width, eye_height):
    HR = (pupil_position[0] - eye_center[0]) / (eye_width / 2)
    VR = (pupil_position[1] - eye_center[1]) / (eye_height / 2)
    return HR, VR

# Threshold values to indicate eye closure
EYE_AR_THRESH = 0.21  # Adjust this based on testing for accurate results

# Countdown before capturing frames
def countdown_timer(cap, frame, seconds=3):
    for i in range(seconds, 0, -1):
        ret, frame = cap.read()
        if not ret:
            break
        cv2.putText(frame, f"Starting in {i}...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Frame", frame)
        cv2.waitKey(1000)

def save_frame_to_device(frame):
    # Create a folder to save images if it doesn't exist
    save_dir = 'saved_frames'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Generate a unique filename based on current date and time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"frame_{timestamp}.png"
    
    # Save the frame
    save_path = os.path.join(save_dir, filename)
    cv2.imwrite(save_path, frame)
    print(f"Frame saved at {save_path}")

def detect_eye_direction(frame):
    
    # Change orientation of frame
    frame = cv2.rotate(frame, cv2.ROTATE_180)
    #save_frame_to_device(frame)
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces in the grayscale frame
    faces = detector(gray, 0)
    print(f"Detected {len(faces)} face(s).")
    
    for face in faces:
        # Get the facial landmarks
        shape = predictor(gray, face)
        shape = np.array([(shape.part(i).x, shape.part(i).y) for i in range(68)])  # Convert landmarks to a NumPy array
        #print("Facial landmarks detected.")

        # Extract the left and right eye coordinates
        left_eye = shape[left_eye_start:left_eye_end + 1]
        right_eye = shape[right_eye_start:right_eye_end + 1]

        # Calculate the eye aspect ratio for both eyes
        left_eye_ear = eye_aspect_ratio(left_eye)
        right_eye_ear = eye_aspect_ratio(right_eye)

        # Average the eye aspect ratio
        ear = (left_eye_ear + right_eye_ear) / 2.0
        face, landmarks = detect_face_landmarks(frame)
        # Check if the eye aspect ratio is below the threshold, which indicates closed eyes
        if ear < EYE_AR_THRESH:
            #cv2.putText(frame, "Down", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return "Down"
        elif face is not None:
            #print("Processing for open eyes...")

            left_eye_rect, right_eye_rect = extract_eye_regions(landmarks)
            
            left_eye_region = frame[left_eye_rect[1]:left_eye_rect[1] + left_eye_rect[3], left_eye_rect[0]:left_eye_rect[0] + left_eye_rect[2]]
            right_eye_region = frame[right_eye_rect[1]:right_eye_rect[1] + right_eye_rect[3], right_eye_rect[0]:right_eye_rect[0] + right_eye_rect[2]]
            
            left_pupil = detect_pupil(left_eye_region, threshold_value=70)
            right_pupil = detect_pupil(right_eye_region, threshold_value=70)
            
            if left_pupil and right_pupil:
                left_eye_center = (left_eye_rect[2] // 2, left_eye_rect[3] // 2)
                right_eye_center = (right_eye_rect[2] // 2, right_eye_rect[3] // 2)
                
                left_HR, left_VR = calculate_ratios(left_eye_center, left_pupil, left_eye_rect[2], left_eye_rect[3])
                right_HR, right_VR = calculate_ratios(right_eye_center, right_pupil, right_eye_rect[2], right_eye_rect[3])
                
                HR = (left_HR + right_HR) / 2
                VR = (left_VR + right_VR) / 2
                
                # Swap the labels for "Right" and "Left"
                if HR < -0.3:
                    return "Left"  # Originally "Looking Left"
                    print("Right")
                elif HR > 0.3:
                    return "Right"  # Originally "Looking Right"
                    print("Left")
                elif VR < -0.3:
                    return "Up"
                    print("Up")
                elif VR > 0.3:
                    return "Down"
                    print("Down")
                else:
                    return "Center"
                    print("Center")

    print("No face or eye direction detected.")
    return None

def detect_blink(frame, update_label):
    """
    Detects blinks in the provided frame based on Eye Aspect Ratio (EAR).
    :param frame: The frame from the camera feed.
    :return: Blink status (Short Blink, Long Blink, or None).
    """
    EAR_BLINK_THRESHOLD = 0.22

    # Time durations for short and long blinks (in seconds)
    SHORT_BLINK_MIN_DURATION = 2  # Minimum duration for a short blink
    SHORT_BLINK_MAX_DURATION = 3.5  # Maximum duration for a short blink
    LONG_BLINK_MIN_DURATION = 4  # Minimum Long blink threshold
    LONG_BLINK_MAX_DURATION = 6

    # Blink counters and timers
    blink_start_time = None
    total_short_blinks = 0
    total_long_blinks = 0

    blink_consecutive_count = 0  # Tracks consecutive frames below threshold
    SHORT_BLINK_FRAME_COUNT = 3  # Minimum frames for a short blink
    LONG_BLINK_FRAME_COUNT = 5

    LEFT_EYE = list(range(36, 42))
    RIGHT_EYE = list(range(42, 48))


    # Change orientation of frame (reuse logic from detect_eye_direction)
    frame = cv2.rotate(frame, cv2.ROTATE_180)

    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces in the grayscale frame
    faces = detector(gray, 0)
    print(f" blink Detected {len(faces)} face(s).")

    if len(faces) != 1:
        # Update the label in `CameraWidget`
        if len(faces) == 0:
            update_label("No face detected")
            blink_consecutive_count = 0
            ear_values.clear()
        else:
            update_label("Too many faces")
    else:
        update_label('Face Detected')
    
    for face in faces:
        # Get the facial landmarks
        landmarks = predictor(gray, face)
        shape = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in range(68)])  # Convert landmarks to a NumPy array

        # Extract the left and right eye coordinates
        left_eye = shape[LEFT_EYE]
        right_eye = shape[RIGHT_EYE]

        # Calculate the eye aspect ratio for both eyes
        left_eye_ear = eye_aspect_ratio(left_eye)
        right_eye_ear = eye_aspect_ratio(right_eye)

        
        # Average the eye aspect ratio
        ear = (left_eye_ear + right_eye_ear) / 2.0
        print(f"ear: {ear} ")
        ear_values.append(ear)

        for ear in ear_values:  # Loop through calculated EAR values
            if ear <= EAR_BLINK_THRESHOLD:  # EAR is below the threshold
                blink_consecutive_count += 1  # Increment consecutive count
                
                if blink_consecutive_count > 1:
                    update_label(str(blink_consecutive_count))

            else:  # EAR is above the threshold (blink has ended)
                if blink_consecutive_count >= SHORT_BLINK_FRAME_COUNT:
                    if blink_consecutive_count < LONG_BLINK_FRAME_COUNT:
                        print("Short Blink Detected!")
                        ear_values.clear()
                        total_short_blinks += 1
                        return "Short Blink"
                    elif blink_consecutive_count >= LONG_BLINK_FRAME_COUNT:
                        print("Long Blink Detected!")
                        ear_values.clear()
                        total_long_blinks += 1
                        return "Long Blink"

                # Reset the count after classify
                blink_consecutive_count = 0
        print(blink_consecutive_count)
            
    return None