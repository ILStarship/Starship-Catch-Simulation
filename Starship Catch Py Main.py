import turtle
import random
import CONFIG

# Setup background
screen_x, screen_y = 600, 700
screen = turtle.Screen()
screen.setup(screen_x, screen_y)
screen.bgcolor('light blue')

# Setup vars and parameters
#global vertical_speed
vertical_speed = 5
v_speed_max = 10
v_speed_min = 2

# Parameters for belly-flop and after belly-flop
verticle_max_descent_rate = 30 # Max descent rate after belly-flop
gravity_acceleration = 2
engine_acceleration = 4

# Satallite descent rate
satallite_descent_rate = 10

alt = 100
landing_alt = 100
propellant = 100 # Keeps track of how much propellant is remaining
propellant_usage_rate = 1
mechazilla_position = -400 # Screen Y-coordinates of mechazilla when alt == 0

# Min and max X-coordinates for a catch
catch_min = -50
catch_max = -5
catch_vertical_speed_max = 20

# Min and max X-coordinates for ship to crash into tower
tower_min = 15 
tower_max = 75

flight_ended = False # Stores whether flight has terminated (crashed into tower/ground, caught)

# Define function to create satallite
def create_sat():
  satallite = turtle.Turtle()
  screen.addshape('satallite_small_nobg.png')
  satallite.shape('satallite_small_nobg.png')
  satallite.speed(0) # Set speed so tht turtle instantaneously moves
  satallite.penup()
  return satallite

# Setup character
starship = turtle.Turtle()
screen.addshape('starshipStage2SideSmall.png')
starship.shape('starshipStage2SideSmall.png')
starship.penup()
starship.speed(0)
starship.setpos(0, 100)
starship.setheading(15)

# Setup Catch Tower
mechazilla = turtle.Turtle()
screen.addshape('Mechazilla_Mod.png')
mechazilla.shape('Mechazilla_Mod.png')
mechazilla.speed(0)
mechazilla.setheading(90)
mechazilla.penup()
mechazilla.setpos(0, 0)
#mechazilla.hideturtle()

# Setup debris
satallites = []
for row_num in range(random.randint(1, 3)):
  satallites.append(create_sat()) # Create a satallite and append to list
  satallites[row_num].goto(random.randint(screen_x/-2, screen_x/2), screen_x/2-random.randint(-10, 30)) # Move satallite to random coordinate
  
  

# --------- Keyboard actions ---------
def char_right():
#  starship.setheading(350)
  starship.setx(starship.xcor()+5) # Edit speed here
  print("X pos: " + str(starship.xcor()))
#  starship.setheading(0)
def char_left():
#  starship.setheading(10)
  starship.setx(starship.xcor()-5) # Edit speed here
  print("X pos: " + str(starship.xcor()))
#  starship.setheading(0)

# --------- Flight ---------
def reduce_v_speed():
  global vertical_speed
  if vertical_speed>v_speed_min:
    vertical_speed -= 0.5

def increase_v_speed():
  global vertical_speed
  if vertical_speed<v_speed_max:
    vertical_speed += 0.5

def belly_flop(): # Belly flop manuvere
  global vertical_speed
  if starship.heading() != 90:
    starship.setheading(90)
  elif starship.heading() == 90:
    starship.shape("StarshipStage2FiringMod.png")
    screen.addshape("StarshipStage2FiringMod.png")
    print('firing')
    vertical_speed -= engine_acceleration
'''def engine_off():
  screen.addshape('starshipStage2SideSmall.png')
  starship.shape('starshipStage2SideSmall.png')'''
    
  

screen.onkey(char_right, 'Right')
screen.onkey(char_left, 'Left')
screen.onkey(reduce_v_speed, 'Up')
screen.onkey(increase_v_speed, 'Down')
screen.onkey(belly_flop, 'Space')
#screen.onkeyrelease(engine_off, 'Space')
screen.listen()

# --------- Score ---------
score = 0 # Stores score

score_display = turtle.Turtle() # Create turtle object which shows score
score_display.hideturtle()
score_display.penup()
score_display.goto(screen_x/-2+20, screen_y/2-30)
score_display.write('Score: {}'.format(score), align='', font=('Ariel', 24, 'normal'))

def update_score():
  global score
  score -= 1
  score_display.clear()
  score_display.write('Score: {}'.format(score), align='', font=('Ariel', 24, 'normal'))

while True:
  print('Descent rate: ' + str(vertical_speed))
  print('Alt: ' + str(alt))
  print('Score: ' + str(score))
  
# ================================================================================
#                      Re-entry Portion
# ================================================================================
  
  # Make satallites fall
  sat_index = 0 # Stores index or satallite which loop is checking for deletion from list when it hits end of screen
  for satallite in satallites:
    satallite.sety(satallite.ycor()- (satallite_descent_rate-vertical_speed)) # Make satallite fall
    if satallite.ycor() < -(screen_x)/2: # Satallite hit end of screen
      satallite.goto(random.randint(screen_x/-2, screen_x/2), screen_x/2-random.randint(-10, 30))
      satallites.pop(sat_index)
      satallites.append(create_sat())
      satallites[len(satallites)-1].goto(random.randint(screen_x/-2, screen_x/2), screen_x/2-random.randint(-10, 30)) # Move latest satallite to random coordinate
    sat_index += 1
    
  # Check if satallite has collided with player
  for satallite in satallites:
    if satallite.distance(starship) < 50:
      update_score()

  # If alt is at landing alt, stop making satallites fall
  if alt < 500:
    for i in satallites: # Clear all satallites
    # TO DO: Make satallite move off screen
      satallites.pop()
      
  # ================================================================================
  #                         Belly Flop
  # ================================================================================
  
  if starship.heading() == 90:
    # Belly flop executed
    if vertical_speed < verticle_max_descent_rate and flight_ended==False:
      vertical_speed += gravity_acceleration
  
  # ================================================================================
  #                         End of: Belly Flop
  # ================================================================================
  
  # ================================================================================
  #                         Move Mechazilla
  # ================================================================================
  
  mechazilla.setpos(0, mechazilla_position-alt)
    
  
  # --------- Catch Logic ---------
  if alt <= -450:
    # Starship at level of chopsticks
    if catch_max>=starship.xcor()>=catch_min:
      # Starship is within chopsticks
      if vertical_speed <= catch_vertical_speed_max:
        # Ship is slow enough to be caught
        print('ship caught')
        flight_ended = True
      else:
        print("Chopsticks: Aww SNAP!")
        flight_ended = True
    
    elif tower_max>=starship.xcor()>=tower_min:
      # Starship has crashed into tower
      print("crashed into tower")
      flight_ended = True

  # --------- Change altitude ---------
  if alt > -1000 and flight_ended == False:
    # Starship in air
    alt -= vertical_speed
  elif flight_ended == False: # Flight hasn't ended but alt isn't higher than ground ie, ship has reached ground
                              # -> Ship has crashed into ground
    print("Ship crashed into ground")
