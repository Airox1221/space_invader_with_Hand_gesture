import pygame 
from laser import Laser
from gesture import HandTracker
import possition_controler
import time
import cv2

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, constraint, speed):
        super().__init__()
        self.image = pygame.image.load('../graphics/player.png').convert_alpha()
        self.rect = self.image.get_rect(midbottom=pos)
        self.speed = speed
        self.max_x_constraint = constraint
        self.ready = True
        self.laser_time = 0
        self.laser_cooldown = 600
        self.lasers = pygame.sprite.Group()
        self.prev_pos = 0

        # Audio
        self.laser_sound = pygame.mixer.Sound('../audio/laser.wav')
        self.laser_sound.set_volume(0.5)

        # Hand Tracker Initialization (once, not per frame)
        self.hand_tracker = HandTracker()
        self.poss = possition_controler.Poss_Fix(height=600, width=600)

    def get_input(self):
        dist = self.rect.x  # Store the player's current X position
        keys = False
        #keys = pygame.key.get_pressed()

        # Capture the frame from the camera
        success, img = self.hand_tracker.cap.read()
        if not success or img is None:
            print("Error: Blank screen or no image captured")
            return

        # Process the hand-tracking frame
        img, list_of_pos = self.hand_tracker.process_frame(img)

        # FPS calculation (optional, for debugging)
        self.hand_tracker.c_time = time.time()
        self.hand_tracker.pre_time = self.hand_tracker.c_time

        # If a hand is detected, move the player based on the index finger's position
        if list_of_pos[0] != 0:
            dist = self.poss.set_pos(self.hand_tracker.img_dim[0], self.hand_tracker.img_dim[1], list_of_pos[0])

        if dist != 0:
            if self.prev_pos == 0:
                # If there's no previous position, set it directly
                self.rect.x = dist
                self.prev_pos = dist
            else:
                difference = abs(self.prev_pos - dist)
                # Smooth out sudden position changes (greater than 10 units)
                if difference > 15  and difference < 60:
                    step = 20 if dist > self.prev_pos else -20  # Determine the direction of movement
                    for i in range(self.prev_pos, dist, step):
                        self.rect.x = i
                        # Here, you might need to add a small delay to see the smooth movement in real time
                        pygame.time.delay(20)  # Optional: Add delay if the movement happens too fast

                    self.rect.x = dist  # Set the final position to the target distance
                    self.prev_pos = dist
                elif difference > 60  and difference < 120:
                    step = 20 if dist > self.prev_pos else -20
                    rang = 5
                    for i in range(rang):
                        self.rect.x += step
                        pygame.time.delay(20)
                    self.prev_pos = self.prev_pos+(step*rang)
                elif difference >100:
                    print("huge leep")
                else:
                    # If the difference is small, set the position directly
                    self.rect.x = dist
                    self.prev_pos = dist
            # Update previous position



        # Check for laser shooting (Space key press)
        if (keys and self.ready) or (self.hand_tracker.active_flag and self.ready):  # use this to work for space keys[pygame.K_SPACE]
            self.shoot_laser()
            self.ready = False
            self.laser_time = pygame.time.get_ticks()
            self.laser_sound.play()

    def recharge(self):
        # Recharge laser cooldown
        if not self.ready:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_time >= self.laser_cooldown:
                self.ready = True

    def constraint(self):
        # Ensure the player doesn't move out of bounds
        if self.rect.left <= 0:
            self.rect.left = 0
        if self.rect.right >= self.max_x_constraint:
            self.rect.right = self.max_x_constraint

    def shoot_laser(self):
        # Add a laser to the group
        self.lasers.add(Laser(self.rect.center, -8, self.rect.bottom))

    def update(self):
        self.get_input()
        self.constraint()
        self.recharge()
        self.lasers.update()

    def cleanup(self):
        # Cleanup the hand tracker (only call this when the game ends)
        self.hand_tracker.cleanup()
