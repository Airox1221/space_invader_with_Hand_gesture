import cv2
import mediapipe as mp
import time

class HandTracker:

    def __init__(self):
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FPS,10)
        if not self.cap.isOpened():
            print("Error: Camera not opened")
            return

        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hand = self.mp_hands.Hands(static_image_mode=False, max_num_hands=1,
                                        min_detection_confidence=0.5,
                                        min_tracking_confidence=0.5,
                                        model_complexity=1)
        self.mp_draw = mp.solutions.drawing_utils

        # Time variables for FPS calculation
        self.c_time = 0
        self.pre_time = 0
        self.delay_time = 21 # if 50 set it will give 1000/20 fps
        # Finger position and image dimensions
        self.pos = [0, 0]  # Store finger position (X, Y)
        self.img_dim = []
        self.active_flag = False

    def process_frame(self, img):
        # Flip the image horizontally for a natural selfie view
        img = cv2.resize(img, ( 144, 144))
        img = cv2.flip(img, 1)

        # Check if the image is captured correctly
        if img is None:
            #print("Error: No image captured from camera")
            return img, [0, 0]

        try:
            # Convert BGR image to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except cv2.error as e:
            print(f"Error converting to RGB: {e}")
            return img, [0, 0]

        # Process the image and detect hand landmarks
        result = self.hand.process(img_rgb)
        px, py = 0, 0

        # If hand landmarks are detected
        if result.multi_hand_landmarks:
            list_lm = []
            for frames in result.multi_hand_landmarks:

                for id, lm in enumerate(frames.landmark):
                    h, w, c = img.shape
                    #print(img.shape)
                    list_lm.append(lm.y)
                    self.img_dim = [h, w]
                    px, py = int(lm.x * w), int(lm.y * h)

                    # Draw hand landmarks on the image
                    #self.mp_draw.draw_landmarks(img, frames, self.mp_hands.HAND_CONNECTIONS)

                    # Track the index finger tip (landmark id 9)
                    if id == 9:
                        self.pos = [px, py]# Update finger position
                    if len(list_lm) >= 13:
                        if list_lm[9] > list_lm[12]:
                            self.active_flag = True
                        else :
                            self.active_flag = False
                    else:
                        self.active_flag =False
        else:
            # Reset position if no hand is detected
            self.pos = [0, 0]
            self.active_flag = False
        cv2.waitKey(self.delay_time)
        # Calculate FPS
        #self.c_time = time.time()
        #fps = 1 / (self.c_time - self.pre_time)
        #self.pre_time = self.c_time

        # Display FPS on the image
        #cv2.putText(img, f"FPS: {int(fps)}", (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 2)

        return img, self.pos

    def cleanup(self):
        # Release the camera and close any OpenCV windows
        self.cap.release()
        cv2.destroyAllWindows()



