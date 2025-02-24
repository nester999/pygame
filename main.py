import pygame
import sys
import math
from os import path

# Initialize Pygame
pygame.init()

# Initialize game controllers
pygame.joystick.init()
joysticks = []
for i in range(pygame.joystick.get_count()):
    joystick = pygame.joystick.Joystick(i)
    joystick.init()
    joysticks.append(joystick)
    print(f"Found gamepad: {joystick.get_name()}")

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
PURPLE = (147, 0, 211)
MAGENTA = (255, 0, 255)
DARK_PURPLE = (64, 0, 92)
LIGHT_BLUE = (100, 200, 255)
DARK_BLUE = (0, 100, 200)
YELLOW = (255, 255, 0)

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simple Platformer")

# Clock for controlling the frame rate
clock = pygame.time.Clock()

# Player settings
player_size = 50
player_x = SCREEN_WIDTH // 2
player_y = SCREEN_HEIGHT - player_size
player_speed = 5
player_jump = 10
player_velocity_y = 0
gravity = 0.5
max_jumps = 2  # New: Maximum number of jumps
jumps_remaining = max_jumps  # New: Track remaining jumps
player_direction = "right"  # Track which way robot is facing
walk_cycle = 0  # For bouncing animation
WALK_CYCLE_SPEED = 0.2  # How fast the walk cycle moves

# Jump tracking
was_space_pressed = False  # New: Track space key state

# Platform settings
platforms = [
    pygame.Rect(100, 500, 200, 20),
    pygame.Rect(400, 400, 200, 20),
    pygame.Rect(200, 300, 200, 20),
]

# Movement settings
DASH_SPEED = 15
DASH_DURATION = 15
DOUBLE_TAP_TIME = 200  # milliseconds
last_left_tap = 0
last_right_tap = 0
is_dashing = False
dash_direction = None
dash_time_remaining = 0

def load_robot_images():
    img_dir = path.join(path.dirname(__file__), 'assets')
    images = {}
    try:
        # Add debug prints
        print(f"Looking for robot images in: {img_dir}")
        
        idle_right = pygame.image.load(path.join(img_dir, 'robot_idle_right.png'))
        print("Loaded idle_right successfully")
        idle_left = pygame.image.load(path.join(img_dir, 'robot_idle_left.png'))
        print("Loaded idle_left successfully")
        
        images['idle_right'] = idle_right.convert_alpha()
        images['idle_left'] = idle_left.convert_alpha()
        
        # Scale images to match player size
        images['idle_right'] = pygame.transform.scale(images['idle_right'], (player_size, player_size))
        images['idle_left'] = pygame.transform.scale(images['idle_left'], (player_size, player_size))
        return images
    except pygame.error as e:
        print(f"Couldn't load robot images: {e}")
        return None

def load_background():
    img_dir = path.join(path.dirname(__file__), 'assets')
    try:
        print(f"Looking for background image in: {img_dir}")
        bg_image = pygame.image.load(path.join(img_dir, 'background.png')).convert()
        print("Loaded background successfully")
        return pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except pygame.error as e:
        print(f"Couldn't load background image: {e}")
        return None

def draw_background():
    if background_image is None:
        # Fallback to original background
        screen.fill(BLACK)
        pygame.draw.circle(screen, MAGENTA, (SCREEN_WIDTH//2, SCREEN_HEIGHT + 50), 200)
        
        for i in range(0, SCREEN_WIDTH, 50):
            start_pos = (i, SCREEN_HEIGHT//2)
            end_pos = (SCREEN_WIDTH//2 + (i - SCREEN_WIDTH//2) * 2, SCREEN_HEIGHT)
            pygame.draw.line(screen, PURPLE, start_pos, end_pos, 1)
        
        hill_colors = [DARK_PURPLE, PURPLE, MAGENTA]
        for i, color in enumerate(hill_colors):
            points = []
            for x in range(0, SCREEN_WIDTH + 50, 50):
                y = SCREEN_HEIGHT - 100 - i * 50 + math.sin(x/100 + i) * 30
                points.append((x, y))
            points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
            points.append((0, SCREEN_HEIGHT))
            pygame.draw.polygon(screen, color, points)
    else:
        screen.blit(background_image, (0, 0))

def draw_robot(screen, x, y, size, walk_cycle, direction):
    if robot_images is None:
        # Fallback to shape drawing
        # Add bounce to y position based on walk cycle
        bounce_offset = abs(math.sin(walk_cycle)) * 5
        y = y - bounce_offset
        
        # Body (slightly smaller than the collision box)
        body_size = int(size * 0.8)
        body_x = x + (size - body_size) // 2
        body_y = y + (size - body_size) // 2
        
        # Main body (metallic blue square)
        pygame.draw.rect(screen, DARK_BLUE, (body_x, body_y, body_size, body_size))
        
        # Head (light blue)
        head_size = int(size * 0.5)
        head_x = x + (size - head_size) // 2
        head_y = y + size * 0.1
        pygame.draw.rect(screen, LIGHT_BLUE, (head_x, head_y, head_size, head_size))
        
        # Eyes (yellow circles)
        eye_radius = int(size * 0.1)
        if direction == "left":
            left_eye_x = head_x + head_size * 0.2  # Eyes shifted left
            right_eye_x = head_x + head_size * 0.6
        else:
            left_eye_x = head_x + head_size * 0.4  # Eyes shifted right
            right_eye_x = head_x + head_size * 0.8
        
        eye_y = head_y + head_size * 0.4
        pygame.draw.circle(screen, YELLOW, (int(left_eye_x), int(eye_y)), eye_radius)
        pygame.draw.circle(screen, YELLOW, (int(right_eye_x), int(eye_y)), eye_radius)
        
        # Antenna (now with tilt based on movement)
        antenna_base_x = x + size // 2
        antenna_base_y = head_y
        antenna_top_y = y
        
        # Tilt antenna based on direction and movement
        if direction == "left":
            antenna_tilt = -10 + math.sin(walk_cycle) * 5
        else:
            antenna_tilt = 10 + math.sin(walk_cycle) * 5
        
        antenna_top_x = antenna_base_x + math.sin(math.radians(antenna_tilt)) * 20
        pygame.draw.line(screen, LIGHT_BLUE, 
                        (antenna_base_x, antenna_base_y),
                        (antenna_top_x, antenna_top_y), 3)
        pygame.draw.circle(screen, YELLOW, (int(antenna_top_x), antenna_top_y), 4)
    else:
        # Use idle images when standing still
        image = robot_images['idle_left'] if direction == 'left' else robot_images['idle_right']
        screen.blit(image, (x, y))

def load_platform_image():
    img_dir = path.join(path.dirname(__file__), 'assets')
    try:
        print(f"Looking for platform image in: {img_dir}")
        platform_img = pygame.image.load(path.join(img_dir, 'platform.png')).convert_alpha()
        print("Loaded platform image successfully")
        # Scale image to match platform size (200x20)
        return pygame.transform.scale(platform_img, (200, 20))
    except pygame.error as e:
        print(f"Couldn't load platform image: {e}")
        return None

# Initialize robot images
robot_images = load_robot_images()

# Add after other image initializations
platform_image = load_platform_image()

# Add after other image initializations
background_image = load_background()

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Create player rect once
    player_rect = pygame.Rect(player_x, player_y, player_size, player_size)
    
    # Key presses and gamepad input
    keys = pygame.key.get_pressed()
    moving = False
    current_time = pygame.time.get_ticks()
    
    # Handle dashing
    if dash_time_remaining > 0:
        # Continue ongoing dash
        if dash_direction == "left":
            player_x -= DASH_SPEED
        else:
            player_x += DASH_SPEED
        dash_time_remaining -= 1
        moving = True
    else:
        # Get gamepad input for movement (if any gamepad is connected)
        gamepad_x = 0
        if joysticks:
            gamepad_x = joysticks[0].get_axis(0)  # Left stick X axis
            # Add a small deadzone to prevent drift
            if abs(gamepad_x) < 0.2:
                gamepad_x = 0
        
        # Combine keyboard and gamepad input
        if keys[pygame.K_LEFT] or gamepad_x < -0.2:
            if not was_left_pressed:  # Key/stick just pressed
                if current_time - last_left_tap < DOUBLE_TAP_TIME:
                    # Start dash
                    dash_direction = "left"
                    dash_time_remaining = DASH_DURATION
                last_left_tap = current_time
            if not dash_time_remaining:  # Normal movement if not dashing
                player_x -= player_speed
            player_direction = "left"
            moving = True
            was_left_pressed = True
        else:
            was_left_pressed = False

        if keys[pygame.K_RIGHT] or gamepad_x > 0.2:
            if not was_right_pressed:  # Key/stick just pressed
                if current_time - last_right_tap < DOUBLE_TAP_TIME:
                    # Start dash
                    dash_direction = "right"
                    dash_time_remaining = DASH_DURATION
                last_right_tap = current_time
            if not dash_time_remaining:  # Normal movement if not dashing
                player_x += player_speed
            player_direction = "right"
            moving = True
            was_right_pressed = True
        else:
            was_right_pressed = False

    # Update jump controls to include gamepad button
    button_pressed = False
    if joysticks:
        button_pressed = joysticks[0].get_button(0)  # First button (usually B1/A)
    
    if keys[pygame.K_SPACE] or button_pressed:
        # Only jump if the key/button was just pressed (not held)
        if not was_space_pressed and jumps_remaining > 0:
            player_velocity_y = -player_jump
            jumps_remaining -= 1
        was_space_pressed = True
    else:
        was_space_pressed = False

    # Apply gravity
    player_velocity_y += gravity
    player_y += player_velocity_y

    # Update player rect position
    player_rect = pygame.Rect(player_x, player_y, player_size, player_size)

    # Check for collisions and jumping
    can_jump = False
    
    # Ground collision
    if player_y >= SCREEN_HEIGHT - player_size:
        player_y = SCREEN_HEIGHT - player_size
        player_velocity_y = 0
        jumps_remaining = max_jumps  # Reset jumps when hitting ground
        can_jump = True

    # Platform collisions
    for platform in platforms:
        if player_rect.colliderect(platform):
            if player_velocity_y > 0:  # Falling
                player_y = platform.top - player_size
                player_velocity_y = 0
                jumps_remaining = max_jumps  # Reset jumps when landing on platform
                can_jump = True
                break

    # Update walk cycle
    if moving:
        walk_cycle += WALK_CYCLE_SPEED
    else:
        walk_cycle = 0

    # Draw background
    draw_background()
    
    # Draw the platforms
    for platform in platforms:
        if platform_image is None:
            pygame.draw.rect(screen, WHITE, platform)
        else:
            screen.blit(platform_image, platform)
    
    # Draw the robot
    draw_robot(screen, player_x, player_y, player_size, walk_cycle, player_direction)

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)
