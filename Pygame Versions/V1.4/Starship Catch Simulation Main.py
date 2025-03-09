import pygame
import random
import os
from time import time, sleep
import configparser
import asyncio
from enum import Enum

# --- Config Parser Setup ---
Config = configparser.ConfigParser()
Config.read("Starship Catch Py CONFIG.ini")

# --- Pygame Setup ---
pygame.init() # Initialize Pygame modules

pygame.mixer.init() # Initialize mixer for playing sound

screen_x, screen_y = 800, 700 # Setup game window dimensions
screen = pygame.display.set_mode((screen_x, screen_y)) # Create the display surface (window)
pygame.display.set_caption("Starship Catch Simulator") # Set the title of the game window
bg_color = {"R": 135, "G": 206, "B": 235} # Define the background color (light blue)

clock = pygame.time.Clock()

class Difficulty(Enum):
    """Stores difficulty level"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

# Load all game images
starship_img = pygame.image.load(Config.get("IMAGES", "starship_img"))
starship_firing_img = pygame.image.load(Config.get("IMAGES", "starship_firing_img"))
explosion = pygame.image.load(Config.get("IMAGES", "explosion"))
mechazilla_img = pygame.image.load(Config.get("IMAGES", "mechazilla"))
satellite_img = pygame.image.load(Config.get("IMAGES", "satallite"))

# Load audio files
explosion_sound = Config.get("AUDIO", "explosion_sound")
engine_sound = Config.get("AUDIO", "engine_sound")

# --- Declare Variables ---
starship_y = screen_y/2-100

descent_rate = float(Config.get("STARTING VALUES", "descent_rate")) # How fast the ship is descending

# Minimum rate at which the ship could descend. Stores descsnt rate of different difficulty levels as a dictionary
min_descent_rate_dict = {Difficulty.EASY: float(Config.get("PARAMETERS", "min_descent_rate_easy")), 
                        Difficulty.MEDIUM: float(Config.get("PARAMETERS", "min_descent_rate_medium")),
                        Difficulty.HARD: float(Config.get("PARAMETERS", "min_descent_rate_hard"))}

# Maximum rate at which the ship could descend. Stores descent rate of different difficulty levels as a dictionary
max_descent_rate_dict = {Difficulty.EASY: float(Config.get("PARAMETERS", "max_descent_rate_easy")),
                         Difficulty.MEDIUM: float(Config.get("PARAMETERS", "max_descent_rate_medium")),
                         Difficulty.HARD: float(Config.get("PARAMETERS", "max_descent_rate_hard"))}

starting_alt = int(Config.get("STARTING VALUES", "starting_alt")) # The altitude where the game is initialized
alt = starting_alt

ship_movement_alt = int(Config.get("PARAMETERS", "ship_movement_alt")) # Altitude where the ship starts to move instead of surroundings
tower_base_coor = int(Config.get("PARAMETERS", "tower_base_coor")) # Y coordinates of tower base when alt = 0 D = 145
tower_x_coor = int(Config.get("PARAMETERS", "tower_x_coor")) # X coordinate of Mechazilla
catch_height = int(Config.get("PARAMETERS", "catch_height")) # Altitude of chopsticks
ground_alt = int(Config.get("PARAMETERS", "ground_alt"))

catch_x_min = int(Config.get("PARAMETERS", "catch_x_min"))
catch_x_max = int(Config.get("PARAMETERS", "catch_x_max"))

# Maximum descent rate onto Chopsticks for a successful catch
catch_max_descent_rate_dict = {Difficulty.EASY: float(Config.get("PARAMETERS", "catch_max_descent_rate_easy")),
                               Difficulty.MEDIUM: float(Config.get("PARAMETERS", "catch_max_descent_rate_medium")),
                               Difficulty.HARD: float(Config.get("PARAMETERS", "catch_max_descent_rate_hard"))}

# Min and max X coordinates of the tower to detect collisions with the tower
tower_x_min = int(Config.get("PARAMETERS", "tower_x_min"))
tower_x_max = int(Config.get("PARAMETERS", "tower_x_max"))

belly_flop_acc = float(Config.get("PARAMETERS", "belly_flop_acc"))
belly_flop_max_descent_rate = float(Config.get("PARAMETERS", "belly_flop_max_descent_rate"))
engine_thrust_min = float(Config.get("PARAMETERS", "engine_thrust_min"))
engine_thrust_max = float(Config.get("PARAMETERS", "engine_thrust_max"))
min_propellant_usage = float(Config.get("PARAMETERS", "min_propellant_usage"))
max_propellant_usage = float(Config.get("PARAMETERS", "max_propellant_usage"))

update_interval = 1/int(Config.get("PARAMETERS", "update_frequency"))

class Starship:

    def __init__(self, image):
        self.img = image
        self.x = 0
        self.y = 0
        self.rotation = 0
        self.belly_flop_executed = False
        self.firing = False
        self.propellant = 100
    
    def set_rotation(self, angle):
        self.rotation = angle
    
    def belly_flop(self):
        """Belly flops if not yet executed."""
        if not self.belly_flop_executed:
            # Belly flop hasn't been executed -> manuvere allowed
            self.set_rotation(0)
            self.belly_flop_executed = True
    
    def fire_engine(self, thrust, propellant_usage):
        """Err... Fires engine"""
        global descent_rate

        if self.propellant > 0:
            # Propellant hasn't been used up... yet
            self.propellant -= propellant_usage
            self.img = starship_firing_img # Set image to image of starship firing engines
            descent_rate -= thrust # Slow descent rate
            self.firing = True
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.load(engine_sound)
                pygame.mixer.music.play()
        else:
            # Propellant used up
            self.img = starship_img # Set image to image of starship not firing engines
            self.firing = False
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
    
    def stop_firing_engine(self):
        """Err... Stop firing engines"""
        self.img = starship_img # Set image to image of starship not firing engines
        self.firing = False
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
    
    def explode(self):
        self.img = explosion
        screen.blit(self.img, (self.x, self.y-60))
        pygame.mixer.music.load(explosion_sound)
        pygame.mixer.music.play()

    def setpos(self, x, y):
        self.x = x
        self.y = y
    
    def blit(self):
        """Render starship onto screen."""
        self.img_modified = pygame.transform.rotate(self.img, self.rotation)
        screen.blit(self.img_modified, (self.x, self.y))
    
    def reset(self, image):
        self.img = image
        self.x = 0
        self.y = 0
        self.rotation = 0
        self.belly_flop_executed = False
        self.firing = False
        self.propellant = 100

class AltitudeBar:
    def __init__(self, x_offset, y_offset, width, height):
        self.x_origin = screen_x-x_offset-width # X axis of top left of ractangle
        self.y_origin = screen_y-y_offset # Y axis of top left of ractangle
        self.width = width
        #pygame.draw.rect(screen, (0,100,200), pygame.Rect(self.x_origin, self.y_origin-height, self.width, height))

    def draw_indicator(self, height):
        pygame.draw.rect(screen, (0,100,200), pygame.Rect(self.x_origin, self.y_origin-height, self.width, height))

class FuelBar():
    def __init__(self, x_offset, y_offset, width, height):
        self.x_origin = x_offset # X axis of top left of ractangle
        self.y_origin = y_offset # Y axis of top left of ractangle
        self.height = height
        #pygame.draw.rect(screen, (120,0,200), pygame.Rect(self.x_origin, self.y_origin, width, self.height))

    def draw_indicator(self, width):
        pygame.draw.rect(screen, (120,0,200), pygame.Rect(self.x_origin, self.y_origin, width, self.height))

class Mechazilla:
    def __init__(self, img, x):#, height_offset):
        self.img = img
        self.x = x
        #self.height_offset = height_offset # Offset at which tower leg is at alt = 0
    
    def blit(self, alt):
        screen.blit(self.img, (self.x, alt+tower_base_coor))

class Banner:
    def __init__(self, size: int, color: tuple):
        self.font = pygame.font.SysFont(None, size)
        self.color = color

    def render_text(self, text, x, y):
        """Renders text onto screen"""
        text_img = self.font.render(text, True, self.color)
        screen.blit(text_img, (x, y))
        #rect = img.get_rect()
        #pygame.draw.rect(img, (255, 255, 255), rect, 1)

class Button:
    def __init__(self, text: str, x_origin: int, y_origin: int, width: int, height: int, text_color: tuple, box_color: tuple):
        font = pygame.font.SysFont(None, height)
        self.text_img = font.render(text, True, text_color)
        self.x_origin = x_origin
        self.y_origin = y_origin
        self.width = width
        self.height = height
        self.box_color = box_color
    
    def render_button(self, screen, pygame):
        """Renders button onto screen"""
        mouse_hovering = self.mouse_hover() # Get if mouse is hovering over button
        if mouse_hovering:
            # Mouser hovering over button
            pygame.draw.rect(screen, (max(self.box_color[0]-50, 0), max(self.box_color[1]-50, 0), max(self.box_color[2]-50, 0)), pygame.Rect(self.x_origin, self.y_origin, self.width, self.height))
        else:
            # Mouse isn't hovering over button
            pygame.draw.rect(screen, self.box_color, [self.x_origin, self.y_origin, self.width, self.height])
        screen.blit(self.text_img , (self.x_origin, self.y_origin)) # Render text onto rectangle
    
    def mouse_hover(self):
        """Helper function for mouse_click() and render_button(). Returns True if mouse is hovering over button"""
        mouse_pos = pygame.mouse.get_pos()
        return self.x_origin < mouse_pos[0] < self.x_origin+self.width and self.y_origin < mouse_pos[1] < self.y_origin+self.height

    def mouse_click(self):
        """Returns True if mouse has clicked this button"""
        mouse_hovering = self.mouse_hover()
        mouse_down = 0 # Starts from zero and only increments by on if mouse button is down
        if mouse_hovering:
            # Mouse is hovering over button
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_down += 1
            return True if mouse_down>0 else False
        else:
            # Mouse isn't overing over button
            return False

class ScreenState(Enum):
    """Stores which screen program should be showing"""
    LEVELSCREEN = 1
    GAMESCREEN = 2

# --- Create Characters ---
starship = Starship(starship_img)
starship.setpos(random.randint(0, screen_x-150), starship_y)
starship.set_rotation(-75)

alt_bar = AltitudeBar(20, 20, 35, 400)

mechazilla = Mechazilla(mechazilla_img, tower_x_coor)

fuel_bar = FuelBar(50, 10, 100, 30)

home_banner = Banner(70, (0,0,0))

frequency_banner = Banner(20, (128, 128, 128)) # Frequency of frames in game session
banner = Banner(50, (0,0,0)) # Header banner after flight ends
banner_subtitle = Banner(25, (0,0,0)) # Sub-header banner after flight ends
banner_restart = Banner(25, (255, 0, 0)) # Tells user to press Q to restart
sinkrate_warning = Banner(30, (255, 0, 0))
descent_rate_banner = Banner(30, (0,0,0))

# --- Homescreen Buttons ---
easy_button = Button("Easy", screen_x/4-50, screen_y/2, 100, 50, (0, 0, 0), (0, 255, 0))
medium_button = Button("Medium", screen_x/4*2-50, screen_y/2, 150, 50, (0, 0, 0), (255, 165, 0))
hard_button = Button("Hard", screen_x/4*3-50, screen_y/2, 125, 50, (0, 0, 0), (255, 0, 0))

def kill_me():
    global running
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # Check for window close event
            running = False  # Set flag to exit loop

def reset_vars():
    """Resets run-time vars so program could run again"""
    global starship, descent_rate, starting_alt, alt, starship_img, start_time, screen_state

    starship.reset(starship_img)
    starship.setpos(random.randint(0, screen_x-150), starship_y)
    starship.set_rotation(-75)
    descent_rate = float(Config.get("STARTING VALUES", "descent_rate")) # How fast the ship is descending
    alt = starting_alt # The altitude where the game is initialized
    start_time = time()
    screen_state = ScreenState.LEVELSCREEN

start_time = time()
prev_update_time = time() # Stores when game session has previously been updated. Makes game run at a consistent speed.
time_since_banner_update = time() # Stores when the frequency banner has last been updated
running = True

screen_state = ScreenState.LEVELSCREEN
difficulty_level = Difficulty.EASY

while running:
    # Event handling
    kill_me()
    
    time_since_update = time() - prev_update_time # Check if it's time to update game session

    if screen_state == ScreenState.LEVELSCREEN:
        screen.fill((bg_color["R"], bg_color["G"], bg_color["B"]))
        home_banner.render_text("Starship Catch Sim", screen_x/4, screen_y/3)

        easy_button.render_button(screen, pygame)
        medium_button.render_button(screen, pygame)
        hard_button.render_button(screen, pygame)

        level = 0 # Initialize level
        level += int(easy_button.mouse_click())*1
        level += int(medium_button.mouse_click())*2
        level += int(hard_button.mouse_click())*3
        print(level)

        # Determine difficulty level
        if level == 1:
            difficulty_level = Difficulty.EASY
            print("EASY")
        elif level == 2:
            difficulty_level = Difficulty.MEDIUM
            print("MEDIUM")
        elif level == 3:
            difficulty_level = Difficulty.HARD
            print("HARD")

        if level>0:
            # Change to game screen when button is pressed
            screen_state = ScreenState.GAMESCREEN

            # Set up variables for this session
            min_descent_rate = min_descent_rate_dict[difficulty_level]
            max_descent_rate = max_descent_rate_dict[difficulty_level]
            catch_max_descent_rate = catch_max_descent_rate_dict[difficulty_level]

    elif screen_state == ScreenState.GAMESCREEN and time_since_update > update_interval:
        prev_update_time = time()
        #print(1/time_since_update)

        keys = pygame.key.get_pressed()
        if not starship.belly_flop_executed:
            # Belly flop hasn't been executed
            if keys[pygame.K_LEFT]:
                # Left arrow pressed
                print("key left")
                starship.setpos(starship.x-0.25, starship.y) # Move starship to the left
                starship.set_rotation(-65)
            elif keys[pygame.K_RIGHT]:
                # Right arrow pressed
                print("key right")
                starship.setpos(starship.x+0.25, starship.y) # Move starship to the right
                starship.set_rotation(-85)
            else:
                # Neither left nor right arrow pressed
                starship.set_rotation(-75) # Reset rotation

            if keys[pygame.K_UP]:
                # Up arrow pressed
                descent_rate -= 0.0001
            elif keys[pygame.K_DOWN]:
                # Down arrow pressed
                descent_rate += 0.0001
            descent_rate = max(min(max_descent_rate, descent_rate), min_descent_rate) # Constrain descent rate
            #print(descent_rate)

            if keys[pygame.K_SPACE]:
                # Space bar pressed
                print('belly flop')
                starship.belly_flop()
        else:
            # Belly flopped
            if keys[pygame.K_SPACE]:
                # Belly flop executed -> fire engines
                starship.fire_engine(engine_thrust_max if keys[pygame.K_LSHIFT] else engine_thrust_min, max_propellant_usage if keys[pygame.K_LSHIFT] else min_propellant_usage)
            else:
                # Space bar not pressed
                starship.stop_firing_engine()
            if keys[pygame.K_LEFT]:
                # Left arrow pressed and firing engine
                # Moves faster if right shift key pressed
                starship.set_rotation(10 if keys[pygame.K_RSHIFT] else 5)
                starship.setpos(starship.x-(0.25 if keys[pygame.K_RSHIFT] else 0.05), starship.y)
            elif keys[pygame.K_RIGHT]:
                # Right arrow pressed and firing engine
                # Moves faster if right shift key pressed
                starship.set_rotation(-10 if keys[pygame.K_RSHIFT] else -5)
                starship.setpos(starship.x+(0.25 if keys[pygame.K_RSHIFT] else 0.05), starship.y)
            else:
                # Neither left nor right arrow pressed
                starship.set_rotation(0) # Reset rotation
        
        if starship.belly_flop_executed:
            # Belly flop has been done
            descent_rate += belly_flop_acc
            descent_rate = min(descent_rate, belly_flop_max_descent_rate) # Constrain descent rate
        
        #print(f"descent rate:       {descent_rate}, alt:        {alt}, starship X:      {starship.x}, propellant:       {starship.propellant}")
        
        if alt<ship_movement_alt:
            starship.setpos(starship.x, starship_y+(ship_movement_alt-alt))
        else:            
            starship.setpos(starship.x, starship_y)

        screen.fill((round(bg_color["R"]*(1-alt/starting_alt)), round(bg_color["G"]*(1-alt/starting_alt)), round(bg_color["B"]*(1-alt/starting_alt)))) # Create backgound

        starship.setpos(max(min(starship.x, screen_x-(50 if starship.belly_flop_executed else 150)), 0), starship.y) # Constrain X axis coordinates
        starship.blit()
        
        alt_bar.draw_indicator(alt/starting_alt*(screen_y-40))

        mechazilla.blit(alt if alt>=ship_movement_alt else ship_movement_alt)

        if time()-time_since_banner_update > 0.5:
            # Update frame-rate on frequency banner between intervals of 0.5s
            frequency_banner_val = 1/time_since_update
            time_since_banner_update = time() # Update time since banner has been updated
            print(f"Banner Update: {frequency_banner_val}")
        
        frequency_banner.render_text(f"Frame-Rate: {(frequency_banner_val):.0f}", 10, 150)

        alt -= descent_rate

        # --- Catch Logic ---
        if catch_height-5<alt <= catch_height:
            # Ship reached chopstick level
            if catch_x_max>=starship.x>=catch_x_min and 0 < descent_rate < catch_max_descent_rate and starship.belly_flop_executed:
                # Ship in chopsticks and is slow enough
                print("Mechazilla has caught the ship.")
                restart = False # Stores whether game has been restarted
                banner.render_text(f"SHIP CAUGHT!", screen_x/2, screen_y/2-50)
                banner_subtitle.render_text(f"{starship.propellant:.0f}% Propellant Left. Time Taken: {(time()-start_time):.1f} Seconds", screen_x/2-80, screen_y/2)
                banner_restart.render_text("Press Q to Restart Game", 10, 10)
                pygame.display.flip()
                clock.tick()
                pygame.mixer.music.fadeout(3)
                while running and not restart:
                    kill_me()
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_q]:
                        reset_vars()
                        restart = True

            elif catch_x_max>starship.x>catch_x_min and descent_rate>catch_max_descent_rate and starship.belly_flop_executed:
                # Max descent rate exceeded
                print("AWW SNAP!")
                restart = False # Stores whether game has been restarted
                starship.explode()
                banner.render_text("AWW SNAP!", screen_x/2-280, screen_y/2-50)
                banner_subtitle.render_text("You Landed Too Hard.", screen_x/2-265, screen_y/2)
                banner_restart.render_text("Press Q to Restart Game", 10, 10)
                pygame.display.flip()
                clock.tick()
                while running and not restart:
                    kill_me()
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_q]:
                        reset_vars()
                        restart = True

            elif catch_x_max>starship.x>catch_x_min-10 and not starship.belly_flop_executed:
                # Ship crashed into tower due to not doing belly flop
                exclamation = random.choice(["DANG!", "DARN IT!"])
                banner_restart.render_text("Press Q to Restart Game", 10, 10)
                restart = False # Stores whether game has been restarted
                starship.explode()
                banner.render_text(exclamation, screen_x/2, screen_y/2)
                pygame.display.flip()
                clock.tick()
                while running and not restart:
                    kill_me()
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_q]:
                        reset_vars()
                        restart = True
            
            elif tower_x_max>starship.x>tower_x_min:
                # Ship crashed into tower
                restart = False # Stores whether game has been restarted
                starship.explode()
                banner.render_text(random.choice(["DANG!", "DARN IT!"]), screen_x/2, screen_y/2)
                banner_restart.render_text("Press Q to Restart Game", 10, 10)
                pygame.display.flip()
                clock.tick()
                while running and not restart:
                    kill_me()
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_q]:
                        reset_vars()
                        restart = True

        # --- Has Ship Crashed into Ground? ---
        if alt <= ground_alt:
            # Ship reached ground
            print("BOOOOM")
    #        while running:
            restart = False # Stores whether game has been restarted
            banner.render_text(random.choice(["BOOOOOM!", "NOOOOO!!!"]), screen_x/2, screen_y/2)
            banner_restart.render_text("Press Q to Restart Game", 10, 10)
            starship.explode()
            pygame.display.flip()
            clock.tick()
            while running and not restart:
                kill_me()
                keys = pygame.key.get_pressed()
                if keys[pygame.K_q]:
                    reset_vars()
                    restart = True


        fuel_bar.draw_indicator(starship.propellant/100*200)

        descent_rate_banner.render_text(f"Descent Rate: {descent_rate:.2f}", 10, 50)
        # Sink-rate warning
        if descent_rate>catch_max_descent_rate:
            sinkrate_warning.render_text("SINK-RATE!", 10, 70)

    # Update Screen and Clock
    pygame.display.flip()
    clock.tick()
    #print("LOOP")
