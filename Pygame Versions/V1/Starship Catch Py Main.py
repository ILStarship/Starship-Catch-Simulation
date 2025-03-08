import pygame
import random
import os
from time import sleep
import configparser

# --- Config Parser Setup ---
Config = configparser.ConfigParser()
Config.read("Starship Catch Py CONFIG.INI")

# --- Pygame Setup ---
pygame.init() # Initialize Pygame modules

screen_x, screen_y = 600, 700 # Setup game window dimensions
screen = pygame.display.set_mode((screen_x, screen_y)) # Create the display surface (window)
pygame.display.set_caption("Starship Landing") # Set the title of the game window
bg_color = {"R": 135, "G": 206, "B": 235} # Define the background color (light blue)

clock = pygame.time.Clock()

# Load all game images
starship_img = pygame.image.load(Config.get("IMAGES", "starship_img"))
starship_firing_img = pygame.image.load(Config.get("IMAGES", "starship_firing_img"))
explosion = pygame.image.load(Config.get("IMAGES", "explosion"))
mechazilla_img = pygame.image.load(Config.get("IMAGES", "mechazilla"))
satellite_img = pygame.image.load(Config.get("IMAGES", "satallite"))

# --- Declare Variables ---
starship_y = screen_y/2-100

descent_rate = float(Config.get("STARTING VALUES", "descent_rate")) # How fast the ship is descending
min_descent_rate = float(Config.get("PARAMETERS", "min_descent_rate")) # Minimum rate at which the ship could descend
max_descent_rate = float(Config.get("PARAMETERS", "max_descent_rate")) # Maximum rate at which the ship could descend

starting_alt = int(Config.get("STARTING VALUES", "starting_alt")) # The altitude where the game is initialized
alt = starting_alt

ship_movement_alt = int(Config.get("PARAMETERS", "ship_movement_alt")) # Altitude where the ship starts to move instead of surroundings
tower_base_coor = int(Config.get("PARAMETERS", "tower_base_coor")) # Y coordinates of tower base when alt = 0 D = 145
tower_x = int(Config.get("PARAMETERS", "tower_x"))
catch_height = int(Config.get("PARAMETERS", "catch_height")) # Altitude of chopsticks
ground_alt = int(Config.get("PARAMETERS", "ground_alt"))

catch_x_min = int(Config.get("PARAMETERS", "catch_x_min"))
catch_x_max = int(Config.get("PARAMETERS", "catch_x_max"))
catch_max_descent_rate = float(Config.get("PARAMETERS", "catch_max_descent_rate"))

tower_min = int(Config.get("PARAMETERS", "tower_min"))
tower_max = int(Config.get("PARAMETERS", "tower_max"))

belly_flop_acc = float(Config.get("PARAMETERS", "belly_flop_acc"))
belly_flop_max_descent_rate = float(Config.get("PARAMETERS", "belly_flop_max_descent_rate"))
engine_thrust_min = float(Config.get("PARAMETERS", "engine_thrust_min"))
engine_thrust_max = float(Config.get("PARAMETERS", "engine_thrust_max"))
min_propellant_usage = float(Config.get("PARAMETERS", "min_propellant_usage"))
max_propellant_usage = float(Config.get("PARAMETERS", "max_propellant_usage"))

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
        else:
            # Propellant used up
            self.img = starship_img # Set image to image of starship not firing engines
            self.firing = False
    
    def stop_firing_engine(self):
        """Err... Stop firing engines"""
        self.img = starship_img # Set image to image of starship not firing engines
        self.firing = False
    
    def explode(self):
        self.img = explosion
        screen.blit(self.img, (self.x, self.y-60))

    def setpos(self, x, y):
        self.x = x
        self.y = y
    
    def blit(self):
        """Render starship onto screen."""
        self.img_modified = pygame.transform.rotate(self.img, self.rotation)
        screen.blit(self.img_modified, (self.x, self.y))

class AltitudeBar:
    def __init__(self, x_offset, y_offset, width, height):
        self.x_origin = screen_x-x_offset-width # X axis of top left of ractangle
        self.y_origin = screen_y-y_offset # Y axis of top left of ractangle
        self.width = width
        pygame.draw.rect(screen, (0,100,200), pygame.Rect(self.x_origin, self.y_origin-height, self.width, height))

    def draw_indicator(self, height):
        pygame.draw.rect(screen, (0,100,200), pygame.Rect(self.x_origin, self.y_origin-height, self.width, height))

class FuelBar():
    def __init__(self, x_offset, y_offset, width, height):
        self.x_origin = x_offset # X axis of top left of ractangle
        self.y_origin = y_offset # Y axis of top left of ractangle
        self.height = height
        pygame.draw.rect(screen, (120,0,200), pygame.Rect(self.x_origin, self.y_origin, width, self.height))

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
    def __init__(self, size, color):
        self.font = pygame.font.SysFont(None, size)
        self.color = color

    def render_text(self, text, x, y):
        text_img = self.font.render(text, True, self.color)
        screen.blit(text_img, (x, y))
        #rect = img.get_rect()
        #pygame.draw.rect(img, (255, 255, 255), rect, 1)

# --- Create Characters ---
starship = Starship(starship_img)
starship.setpos(random.randint(0, screen_x), starship_y)
starship.set_rotation(-75)

alt_bar = AltitudeBar(20, 20, 35, 400)

mechazilla = Mechazilla(mechazilla_img, tower_x)

fuel_bar = FuelBar(50, 10, 100, 30)

banner = Banner(50, (0,0,0))
sinkrate_warning = Banner(30, (255, 0, 0))
descent_rate_banner = Banner(30, (0,0,0))

running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # Check for window close event
            running = False  # Set flag to exit loop
    
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
    
    if starship.belly_flop_executed:
        # Belly flop has been done
        descent_rate += belly_flop_acc
        descent_rate = min(descent_rate, belly_flop_max_descent_rate) # Constrain descent rate
    
    print(f"descent rate:       {descent_rate}, alt:        {alt}, starship X:      {starship.x}, propellant:       {starship.propellant}")
    
    if alt<ship_movement_alt:
        starship.setpos(starship.x, starship_y+(ship_movement_alt-alt))
    else:            
        starship.setpos(starship.x, starship_y)

    screen.fill((round(bg_color["R"]*(1-alt/starting_alt)), round(bg_color["G"]*(1-alt/starting_alt)), round(bg_color["B"]*(1-alt/starting_alt)))) # Create backgound

    starship.blit()
    
    alt_bar.draw_indicator(alt/starting_alt*(screen_y-40))

    mechazilla.blit(alt if alt>=ship_movement_alt else ship_movement_alt)

    alt -= descent_rate

    # --- Catch Logic ---
    if alt <= 0 and alt>-5:
        # Ship reached chopstick level
        if catch_x_max>starship.x>catch_x_min and 0 < descent_rate < catch_max_descent_rate and starship.belly_flop_executed:
            # Ship in chopsticks and is slow enough
            print("SHIP CAUGHT")
            while running:
                banner.render_text("SHIP CAUGHT!", screen_x/2, screen_y/2)
                pygame.display.flip()
                clock.tick()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:  # Check for window close event
                        running = False  # Set flag to exit loop

        elif catch_x_max>starship.x>catch_x_min and descent_rate>catch_max_descent_rate and starship.belly_flop_executed:
            # Max descent rate exceeded
            print("AWW SNAP!")
            while running:
                starship.explode()
                banner.render_text("AWW SNAP! You landed too hard.", screen_x/2-280, screen_y/2)
                pygame.display.flip()
                clock.tick()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:  # Check for window close event
                        running = False  # Set flag to exit loop

        elif catch_x_max>starship.x>catch_x_min-10 and not starship.belly_flop_executed:
            # Ship crashed into tower due to not doing belly flop
            while running:
                starship.explode()
                banner.render_text("DANG!", screen_x/2, screen_y/2)
                pygame.display.flip()
                clock.tick()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:  # Check for window close event
                        running = False  # Set flag to exit loop
        
        elif tower_max>starship.x>tower_min:
            # Ship crashed into tower
            while running:
                starship.explode()
                banner.render_text("DANG!", screen_x/2, screen_y/2)
                pygame.display.flip()
                clock.tick()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:  # Check for window close event
                        running = False  # Set flag to exit loop

    # --- Has Ship Crashed into Ground? ---
    if alt <= ground_alt:
        # Ship reached ground
        print("BOOM")
        while running:
            banner.render_text("BOOOM!", screen_x/2, screen_y/2)
            starship.explode()
            pygame.display.flip()
            clock.tick()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # Check for window close event
                    running = False  # Set flag to exit loop

    fuel_bar.draw_indicator(starship.propellant/100*200)

    descent_rate_banner.render_text(f"Descent Rate: {descent_rate}", 10, 50)
    # Sink-rate warning
    if descent_rate>catch_max_descent_rate:
        sinkrate_warning.render_text("SINK-RATE!", 10, 70)

    # Update Screen and Clock
    pygame.display.flip()
    clock.tick()
