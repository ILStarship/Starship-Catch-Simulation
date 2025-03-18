import pygame
import random
from time import time, sleep
import configparser
from enum import Enum
import PseudoMarkUp_FileParser
from tkinter import messagebox
import json

# --- Config Parser Setup ---
Config = configparser.ConfigParser()
Config.read("StarshipCatchPy_CONFIG.ini")

# --- Pygame Setup ---
pygame.init() # Initialize Pygame modules

pygame.mixer.init() # Initialize mixer for playing sound

screen_x, screen_y = 800, 700 # Setup game window dimensions
screen = pygame.display.set_mode((screen_x, screen_y)) # Create the display surface (window)
pygame.display.set_caption("Starship Catch Simulator") # Set the title of the game window
bg_color = (135, 206, 235) # Define the background color (light blue)

running = True

clock = pygame.time.Clock()

starship_y = screen_y/2-100 # Y position of ship on screen before it starts to move

class Difficulty(Enum):
    """Stores difficulty level"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

# --- Load all game images ---
try:
    starship_img = pygame.image.load(Config.get("IMAGES", "starship_img"))
    starship_firing_img = pygame.image.load(Config.get("IMAGES", "starship_firing_img"))
    explosion = pygame.image.load(Config.get("IMAGES", "explosion"))
    mechazilla_img = pygame.image.load(Config.get("IMAGES", "mechazilla"))
    satellite_img = pygame.image.load(Config.get("IMAGES", "satallite"))
    home_img = pygame.image.load(Config.get("IMAGES", "home_img"))
    info_bg = pygame.image.load(Config.get("IMAGES", "info_screen_img"))

except Exception as e:
    # An error has occured during import
    print(f"An Error During Imgae Importing Has Occured. Error MSG: {e}")
    messagebox.showinfo('ERROR', f'Unable to import images. Try restarting program. Error: {e}')
    running = False

# --- Load audio files ---
try:
    explosion_sound = Config.get("AUDIO", "explosion_sound")
    engine_sound = Config.get("AUDIO", "engine_sound")
    wind_sound = Config.get("AUDIO", "wind_sound")

except Exception as e:
    print(f"An Error Has Occured During Import of Audio Files. Error MSG: {e}")
    messagebox.showinfo('ERROR',f'Unable to import audio. Try restarting program. Error: {e}')
    running = False

# --- Declare Variables ---
starship_y = screen_y/2-100

# --- Load starting values ---
try:
    descent_rate = float(Config.get("STARTING VALUES", "descent_rate")) # How fast the ship is descending
    starting_alt = int(Config.get("STARTING VALUES", "starting_alt")) # The altitude where the game is initialized
    alt = starting_alt

except Exception as e:
    print(f"An Error Has Occured During Import of Starting Values. Error MSG: {e}")
    messagebox.showinfo('ERROR',f'Unable to import starting values. Try restarting program. Error: {e}')
    running = False

# --- Load parameters ---
try:
    # Minimum rate at which the ship could descend. Stores descsnt rate of different difficulty levels as a dictionary
    min_descent_rate_dict = {Difficulty.EASY: float(Config.get("PARAMETERS", "min_descent_rate_easy")), 
                            Difficulty.MEDIUM: float(Config.get("PARAMETERS", "min_descent_rate_medium")),
                            Difficulty.HARD: float(Config.get("PARAMETERS", "min_descent_rate_hard"))}

    # Maximum rate at which the ship could descend. Stores descent rate of different difficulty levels as a dictionary
    max_descent_rate_dict = {Difficulty.EASY: float(Config.get("PARAMETERS", "max_descent_rate_easy")),
                            Difficulty.MEDIUM: float(Config.get("PARAMETERS", "max_descent_rate_medium")),
                            Difficulty.HARD: float(Config.get("PARAMETERS", "max_descent_rate_hard"))}

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

    landing_flip_acc = float(Config.get("PARAMETERS", "landing_flip_acc"))
    landing_flip_max_descent_rate = float(Config.get("PARAMETERS", "landing_flip_max_descent_rate"))
    engine_thrust_min = float(Config.get("PARAMETERS", "engine_thrust_min"))
    engine_thrust_max = float(Config.get("PARAMETERS", "engine_thrust_max"))
    min_propellant_usage = float(Config.get("PARAMETERS", "min_propellant_usage"))
    max_propellant_usage = float(Config.get("PARAMETERS", "max_propellant_usage"))

    update_interval = 1/int(Config.get("PARAMETERS", "update_frequency"))

except Exception as e:
    print(f"An Error Has Occured During Import of Parameters. Error MSG: {e}")
    messagebox.showinfo('ERROR',f'Unable to import parameters. Try restarting program. Error: {e}')
    running = False

    # =========================================================================================
    #                               Process Intro File
    # =========================================================================================
if running:
    # Only continue setup if getting config values were successful

    MarkUp_file_parser = PseudoMarkUp_FileParser.PseudoMarkUpParser(-2600, 0)
    MarkUp_file_parser.convert_file("Instructions.txt")
    MarkUp_file_parser.print_attributes()

    class Starship:

        def __init__(self, image):
            self.img = image
            self.x = 0
            self.y = 0
            self.rotation = 0
            self.landing_flip_executed = False
            self.firing = False
            self.propellant = 100
        
        def set_rotation(self, angle):
            self.rotation = angle
        
        def landing_flip(self):
            """Belly flops if not yet executed."""
            if not self.landing_flip_executed:
                # Belly flop hasn't been executed -> manuvere allowed
                self.set_rotation(0)
                self.landing_flip_executed = True
        
        def fire_engine(self, thrust, propellant_usage):
            """Err... Fires engine"""
            global descent_rate

            if self.propellant > 0:
                # Propellant hasn't been used up... yet
                self.propellant -= propellant_usage
                self.img = starship_firing_img # Set image to image of starship firing engines
                descent_rate -= thrust # Slow descent rate
                self.firing = True
                if audio_player.get_audio() != engine_sound:
                    # audio_player isn't playing audio
                    audio_player.play_audio(engine_sound)
            else:
                # Propellant used up
                self.img = starship_img # Set image to image of starship not firing engines
                self.firing = False
                if audio_player.get_audio() == engine_sound:
                    audio_player.stop_audio()
        
        def stop_firing_engine(self):
            """Err... Stop firing engines"""
            self.img = starship_img # Set image to image of starship not firing engines
            self.firing = False
            if audio_player.get_audio() == engine_sound:
                audio_player.stop_audio()
        
        def explode(self):
            """Makes Ship Explode"""
            audio_player.stop_audio()
            self.img = explosion
            screen.blit(self.img, (self.x, self.y-60))
            audio_player.play_audio(explosion_sound)

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
            self.landing_flip_executed = False
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
        def __init__(self, size: int, color: tuple, font: str | None = None):
            #self.font = pygame.font.SysFont(None, size)
            if font == None:
                # Use default font
                self.font = pygame.font.SysFont(None, size)
            elif ".ttf" in font:
                # Use a font file
                try:
                    self.font = pygame.font.Font(font, size)
                except FileNotFoundError as e:
                    # Font not found in system
                    print(f"[FILE NOT FOUND]: {e}")
                    self.font = pygame.font.SysFont(None, size)
            else:
                # Use a font from os
                try:
                    self.font = pygame.font.SysFont(font, size)
                except FileNotFoundError as e:
                    # Font not found in system
                    print(f"[FILE NOT FOUND]: {e}")
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
                # Mouser hovering over button -> Make button darker
                pygame.draw.rect(screen, (max(self.box_color[0]-50, 0), max(self.box_color[1]-50, 0), max(self.box_color[2]-50, 0)), pygame.Rect(self.x_origin, self.y_origin, self.width, self.height))
            else:
                # Mouse isn't hovering over button
                pygame.draw.rect(screen, self.box_color, [self.x_origin, self.y_origin, self.width, self.height])
            screen.blit(self.text_img , (self.x_origin+5, self.y_origin+8)) # Render text onto rectangle
        
        def mouse_hover(self):
            """Helper function for mouse_click() and render_button(). Returns True if mouse is hovering over button"""
            mouse_pos = pygame.mouse.get_pos()
            return self.x_origin < mouse_pos[0] < self.x_origin+self.width and self.y_origin < mouse_pos[1] < self.y_origin+self.height

        def mouse_click(self):
            """Returns True if mouse has clicked this button"""
            mouse_down = pygame.mouse.get_pressed()
            if mouse_down[0]:
                # Mouse left-clicked
                return self.mouse_hover() # If mouse_hover() returns True, button clicked! :>
                                            # Else mouse_hover() returns False, button isn't clicked... :<
            else:
                # Mouse isn't left-clicked
                return False

    class AudioPlayer:
        def  __init__(self):
            self._current_audio = None

        def play_audio(self, file_name, volume=1):
            """Plays audio using pygame.mixer.music."""
            try:
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.load(file_name)
                pygame.mixer.music.play()

                self._current_audio = file_name
            except FileNotFoundError as e:
                print(f"Audio file not found! {e}")

        def stop_audio(self):
            """Stops audio."""
            self._current_audio = None
            pygame.mixer.music.stop()
        
        def get_audio(self):
            """Returns what audio pygame.mixer.music is playing. Returns None if pygame.mixer.music isn't playing anything"""
            if not pygame.mixer.music.get_busy():
                # mixer.music isn't playing anything
                self._current_audio = None

            return self._current_audio
        
        def set_volume(self, volume):
            pygame.mixer.music.set_volume(volume)

    audio_player = AudioPlayer()

    class ScreenState(Enum):
        """Stores which screen program should be showing"""
        LEVELSCREEN = 1
        INFOSCREEN = 2 # Manual
        GAMESCREEN = 3

    # --- Create Characters ---
    starship = Starship(starship_img)
    starship.setpos(random.randint(0, screen_x-150), starship_y)
    starship.set_rotation(-75)

    alt_bar = AltitudeBar(40, 30, 35, 400)

    mechazilla = Mechazilla(mechazilla_img, tower_x_coor)

    fuel_bar = FuelBar(150, 39, 100, 30)

    home_banner = Banner(32, (0,0,0), "Spacex.ttf")

    frequency_banner = Banner(20, (128, 128, 128)) # Frequency of frames in game session
    banner = Banner(50, (0,0,0)) # Header banner after flight ends
    banner_subtitle = Banner(25, (0,0,0)) # Sub-header banner after flight ends
    banner_record = Banner(25, (0,0,0)) # Tells user whether they broke their record
    banner_restart = Banner(25, (255, 0, 0), "Agency FB") # Tells user to press Q to restart
    sinkrate_warning = Banner(30, (255, 0, 0), "Agency FB")
    descent_rate_banner = Banner(30, (128, 128, 128), "Agency FB")

    altitude_banner = Banner(30, (128, 128, 128), "Agency FB") # Writes "ALTITUDE"
    propellant_banner = Banner(30, (128, 128, 128), "Agency FB") # Writes "PROPELLANT"

    # --- Homescreen Buttons ---
    easy_button = Button("Easy", screen_x/4-50, screen_y/1.3, 90, 50, (0, 0, 0), (0, 255, 0))
    medium_button = Button("Medium", screen_x/4*2-75, screen_y/1.3, 140, 50, (0, 0, 0), (255, 165, 0))
    hard_button = Button("Hard", screen_x/4*3-50, screen_y/1.3, 90, 50, (0, 0, 0), (255, 0, 0))
    
    info_button = Button("How to Play?", screen_x-150, 10, 135, 30, (0,0,0), (128, 128, 128))

    delete_best_button = Button("Reset Best Score", 100, 10, 175, 30, (255, 0,0), (128, 128, 128))
    get_best_button = Button("What is my Best score?", 100, 50, 243, 30, (0,0,0), (128, 128, 128))

    # --- Infoscreen Buttons ---
    back_button = Button("<Back", 5, 5, 70, 30, (0,0,0), (128, 128, 128))

    def kill_me():
        global running
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Check for window close event
                running = False  # Set flag to exit loop

    def setup_vars():
        """Resets run-time vars so program could run again"""
        global starship, descent_rate, starting_alt, alt, starship_img, start_time, screen_state

        starship.reset(starship_img)
        starship.setpos(random.randint(0, screen_x-150), starship_y)
        starship.set_rotation(-75)
        descent_rate = float(Config.get("STARTING VALUES", "descent_rate")) # How fast the ship is descending
        alt = starting_alt # The altitude where the game is initialized
        start_time = time()

        # Reset colors of banners
        altitude_banner.color = (128, 128, 128)
        propellant_banner.color = (128, 128, 128)
        descent_rate_banner.color = (128, 128, 128)
    
    def update_best_json(time_taken, propellant_used):
        try:
            with open("Best.json", 'w') as best_file: # Open file with overwriting mode
                best_file.write(json.dumps({"best_time": time_taken, "min_propellant_usage": propellant_used}))
        except FileNotFoundError as e:
            print("Best.json Couldn't be Found!")
            messagebox.showerror(title="File Not Found", message="Unable to open Best.json")

    prev_update_time = time() # Stores when game session has previously been updated. Makes game run at a consistent speed.
    time_since_banner_update = time() # Stores when the frequency banner has last been updated

    screen_state = ScreenState.LEVELSCREEN
    difficulty_level = Difficulty.EASY

while running:
    # Event handling
    kill_me()
    
    time_since_update = time() - prev_update_time # Check if it's time to update game session

    # ==========================================================================================
    #                                   LEVEL SCREEN
    # ==========================================================================================
    if screen_state == ScreenState.LEVELSCREEN:
        #screen.fill(bg_color)
        screen.blit(home_img, (-200, 0))
        home_banner.render_text("STARSHIP CATCH SIMULATOR", screen_x/12-55, screen_y/8)

        # Render buttons onto screen
        easy_button.render_button(screen, pygame)
        medium_button.render_button(screen, pygame)
        hard_button.render_button(screen, pygame)

        info_button.render_button(screen, pygame)

        delete_best_button.render_button(screen, pygame)
        get_best_button.render_button(screen, pygame)

        # Gets whether button is pressed
        level = 0 # Initialize level
        level += int(easy_button.mouse_click())*1
        level += int(medium_button.mouse_click())*2
        level += int(hard_button.mouse_click())*3

        if info_button.mouse_click():
            # INFO button clicked
            screen_state = ScreenState.INFOSCREEN
        
        if delete_best_button.mouse_click():
            # User wants to delete stats
            delete_stats = messagebox.askokcancel(title="WARNING", message="Are you sure you want to reset your best score?", icon=messagebox.WARNING)
            if delete_stats:
                # Confirmed
                update_best_json(None, None)
        
        if get_best_button.mouse_click():
            try:
                with open("Best.json") as best_file:
                    best_json = json.load(best_file)
                    time_taken = best_json["best_time"]
                    propellant_used = best_json["min_propellant_usage"]
                    if time_taken != None and propellant_used != None:
                        # Stats available
                        messagebox.showinfo("Best Score", f"Time Taken: {time_taken:.0f} Seconds, Propellant Left: {100-propellant_used:.0f}%")
                    else:
                        # Stats aren't available
                        messagebox.showinfo("Best Score", "Best Score is not Available.")

            except FileNotFoundError as e:
                print("Best.json Couldn't be Found!")
                messagebox.showerror(title="File Not Found", message="Unable to open Best.json")

        #print(level)

        audio_player.stop_audio() # Bugfix for Wind_sound.mp3 still playing after game session ended

        # Determine difficulty level
        match level:
            case 1:
                difficulty_level = Difficulty.EASY
                print("[EASY]")
            case 2:
                difficulty_level = Difficulty.MEDIUM
                print("[MEDIUM]")
            case 3:
                difficulty_level = Difficulty.HARD
                print("[HARD]")

        if level>0:
            # Change to game screen when button is pressed
            screen_state = ScreenState.GAMESCREEN

            # Set up variables for this session
            start_time = time()
            min_descent_rate = min_descent_rate_dict[difficulty_level]
            max_descent_rate = max_descent_rate_dict[difficulty_level]
            catch_max_descent_rate = catch_max_descent_rate_dict[difficulty_level]
            setup_vars()
    
    # ==========================================================================================
    #                                     INFO SCREEN
    # ==========================================================================================
    elif screen_state == ScreenState.INFOSCREEN:
        #screen.fill(bg_color)
        screen.blit(info_bg, (0, -100)) # Render background

        scroll_offset = 0
        for event in pygame.event.get():
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset = event.y*15
        MarkUp_file_parser.display_content(screen, scroll_offset) # Display instructions

        back_button.render_button(screen, pygame) # Render back button

        if back_button.mouse_click():
            # Back button clicked
            MarkUp_file_parser.total_scroll_offset = 0 # Reset scrolled amount
            screen_state = ScreenState.LEVELSCREEN # Return to level screen

    # ==========================================================================================
    #                                      GAME SCREEN
    # ==========================================================================================
    elif screen_state == ScreenState.GAMESCREEN and time_since_update > update_interval:
        prev_update_time = time()
        #print(1/time_since_update)

        keys = pygame.key.get_pressed()
        if not starship.landing_flip_executed:
            # Belly flop hasn't been executed
            if keys[pygame.K_LEFT]:
                # Left arrow pressed
                starship.setpos(starship.x-0.25, starship.y) # Move starship to the left
                starship.set_rotation(-65)
            elif keys[pygame.K_RIGHT]:
                # Right arrow pressed
                starship.setpos(starship.x+0.25, starship.y) # Move starship to the right
                starship.set_rotation(-85)
            else:
                # Neither left nor right arrow pressed
                starship.set_rotation(-75) # Reset rotation

            if keys[pygame.K_UP]:
                # Up arrow pressed
                descent_rate -= 0.0002
            elif keys[pygame.K_DOWN]:
                # Down arrow pressed
                descent_rate += 0.0002
            descent_rate = max(min(max_descent_rate, descent_rate), min_descent_rate) # Constrain descent rate

            if keys[pygame.K_SPACE]:
                # Space bar pressed
                print('[BELLY FLOP]')
                starship.landing_flip()
        else:
            # Landing flip executed
            if keys[pygame.K_SPACE]:
                # Belly flop executed -> fire engines
                starship.fire_engine(engine_thrust_max if keys[pygame.K_LSHIFT] else engine_thrust_min, max_propellant_usage if keys[pygame.K_LSHIFT] else min_propellant_usage)

            else:
                # Space bar not pressed
                starship.stop_firing_engine()

            # Check for left and right arrow presses. Only moves when engines are firing
            if keys[pygame.K_LEFT] and starship.firing:
                # Left arrow pressed and firing engine
                # Moves faster if right shift key pressed
                starship.set_rotation(10 if keys[pygame.K_RSHIFT] else 5)
                starship.setpos(starship.x-(0.25 if keys[pygame.K_RSHIFT] else 0.05), starship.y)
            elif keys[pygame.K_RIGHT] and starship.firing:
                # Right arrow pressed and firing engine
                # Moves faster if right shift key pressed
                starship.set_rotation(-10 if keys[pygame.K_RSHIFT] else -5)
                starship.setpos(starship.x+(0.25 if keys[pygame.K_RSHIFT] else 0.05), starship.y)
            else:
                # Neither left nor right arrow pressed
                starship.set_rotation(0) # Reset rotation
        
        if starship.landing_flip_executed:
            # Belly flop has been done
            descent_rate += landing_flip_acc
            descent_rate = min(descent_rate, landing_flip_max_descent_rate) # Constrain descent rate
        
        #print(f"descent rate:       {descent_rate}, alt:        {alt}, starship X:      {starship.x}, propellant:       {starship.propellant}")
        
        if alt<ship_movement_alt:
            starship.setpos(starship.x, starship_y+(ship_movement_alt-alt))
        else:            
            starship.setpos(starship.x, starship_y)

        screen.fill((round(bg_color[0]*(1-alt/starting_alt)), round(bg_color[1]*(1-alt/starting_alt)), round(bg_color[2]*(1-alt/starting_alt)))) # Create backgound

        starship.setpos(max(min(starship.x, screen_x-(50 if starship.landing_flip_executed else 150)), 0), starship.y) # Constrain X axis coordinates
        starship.blit()
        
        alt_bar.draw_indicator(alt/starting_alt*(screen_y-40))

        mechazilla.blit(alt if alt>=ship_movement_alt else ship_movement_alt)

        alt -= descent_rate

        # --- Catch Logic ---
        if catch_height-5<alt <= catch_height:
            # Ship reached chopstick level
            if catch_x_max>=starship.x>=catch_x_min and 0 < descent_rate < catch_max_descent_rate and starship.landing_flip_executed:
                '''Ship in chopsticks and is slow enough'''
                print("Mechazilla has caught the ship.")
                restart = False # Stores whether game has been restarted

                # --- Is this the best attempt? ---
                time_taken = time()-start_time # Time taken
                propellant_used = 100-starship.propellant # Propellant used

                try:
                    with open("Best.json") as best_file: # Open Best.json to get best session
                        best = json.load(best_file)
                        print(f"Best time: {best["best_time"]}, Min Prop Usage: {best["min_propellant_usage"]}")
                        print(f"Current time: {time_taken}, Current prop usage: {propellant_used}")

                        if best["best_time"] != None and best["min_propellant_usage"] != None:
                            # Best values have been set

                            if propellant_used+time_taken < best["min_propellant_usage"]+best["best_time"]:
                                # Current attempt has taken less propellant and time -> Record broken! :>
                                print("Record Broken")
                                banner_record.render_text(f"You Beat Your Best Score! Previous Score: {(100-best["min_propellant_usage"]):.0f}% Propellant Left, {best["best_time"]:.0f} Seconds Taken", screen_x/4-150, screen_y/2+30)
                                update_best_json(time_taken, propellant_used) # Update Best.json
                            else:
                                # Taken longer and/or used more fuel
                                print("Could you break your record at your next attempt?")
                                banner_record.render_text(f"Could you beat your best score at your next attempt? To Beat: {(100-best["min_propellant_usage"]):.0f}% Propellant Left, {best["best_time"]:.0f} Seconds", 5, screen_y/2+30)

                        else:
                            # Best values haven't been set yet
                            print("No values in Best.json")
                            print("Overiting null values in Best.json")
                            update_best_json(time_taken, propellant_used) # Update current stats to Best.json
                            print("Overwrite completed")


                except FileNotFoundError as e:
                    print("Best.json Couldn't be Found!")
                    messagebox.showerror(title="File Not Found", message="Unable to open Best.json")

                banner.render_text(f"SHIP CAUGHT!", screen_x/2, screen_y/2-50)
                banner_subtitle.render_text(f"{starship.propellant:.0f}% Propellant Left. Time Taken: {time_taken:.0f} Seconds", screen_x/2-80, screen_y/2)
                banner_restart.render_text("Press Q to Restart Game", 10, 10)

                pygame.display.flip()
                clock.tick()
                audio_player.stop_audio()
                while running and not restart:
                    kill_me()
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_q]:
                        # User wants to go to menu
                        screen_state = ScreenState.LEVELSCREEN
                        restart = True

            elif catch_x_max>starship.x>catch_x_min and descent_rate>catch_max_descent_rate and starship.landing_flip_executed:
                '''Max descent rate exceeded'''
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
                        # User wants to go to menu
                        screen_state = ScreenState.LEVELSCREEN
                        restart = True

            elif catch_x_max>starship.x>catch_x_min-10 and not starship.landing_flip_executed:
                '''Ship crashed into tower due to not doing belly flop'''
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
                        # User wants to go to menu
                        screen_state = ScreenState.LEVELSCREEN
                        restart = True
            
            elif tower_x_max>starship.x>tower_x_min:
                '''Ship crashed into tower'''
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
                        # User wants to go to menu
                        screen_state = ScreenState.LEVELSCREEN
                        restart = True

        # --- Has Ship Crashed into Ground? ---
        if alt <= ground_alt:
            '''Ship has crashed into the ground'''
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
                    # User wants to go to menu
                    screen_state = ScreenState.LEVELSCREEN
                    restart = True

        if alt < starting_alt/3*2:
            altitude_banner.color = (0, 0, 0)
            propellant_banner.color = (0, 0, 0)
            descent_rate_banner.color = (0, 0, 0)

        altitude_banner.render_text(f"ALTITUDE: {alt/100:.0f} KM", screen_x-165, screen_y-35)

        propellant_banner.render_text("PROPELLANT", 10, 40)
    
        back_button.render_button(screen, pygame) # Render back button

        if back_button.mouse_click():
            # Back buton pressed
            screen_state = ScreenState.LEVELSCREEN # Return to level screen

        if time()-time_since_banner_update > 0.5:
            # Update frame-rate on frequency banner between intervals of 0.5s
            frequency_banner_val = 1/time_since_update
            time_since_banner_update = time() # Update time since banner has been updated
            print(f"Banner Update: {frequency_banner_val}")
        
        # Set frequency_banner to red if refresh rate is too low
        frequency_banner.color = (200, 0, 0) if (frequency_banner_val)<int(Config.get("PARAMETERS", "update_frequency"))-200 else (128, 128, 128)
        frequency_banner.render_text(f"Refresh-Rate: {(frequency_banner_val):.0f}Hz", 10, 170)

        fuel_bar.draw_indicator(starship.propellant/100*200)

        descent_rate_banner.render_text(f"Descent Rate: {descent_rate:.2f}", 10, 80)
        # Sink-rate warning
        if descent_rate>catch_max_descent_rate and starship.landing_flip_executed:
            sinkrate_warning.render_text(f"SINK-RATE! MAX: {catch_max_descent_rate}", 10, 130)
        
        if audio_player.get_audio() == None:
            # Audio player isn't playing anything
            audio_player.play_audio(wind_sound) # Play wind sounds

        if audio_player.get_audio() == wind_sound and starship.landing_flip_executed:
            # Adjust wind sound volume only after landing flip has been executed
            audio_player.set_volume(abs(descent_rate/max_descent_rate))
            print(abs(descent_rate/max_descent_rate))

    # Update Screen and Clock
    pygame.display.flip()
    clock.tick()
