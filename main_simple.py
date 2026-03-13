import pygame
import pymunk
import math
import random
import json
import os
import sys

# Initialize
pygame.init()
SCREEN = pygame.display.set_mode((800, 600))
CLOCK = pygame.time.Clock()
FONT = pygame.font.Font(None, 48)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (231, 76, 60)
BLUE = (52, 152, 219)
GRAY = (150, 150, 150)

# Physics
GRAVITY = -900
DAMPING = 0.5

# Load tiles
TILES = []
try:
    with open("assets/data/tiles.json", "r") as f:
        tile_data = json.load(f)
    
    for item in tile_data[:5]:  # Load first 5 tiles
        img_path = os.path.join("assets/images/tiles", item["image_file"])
        if os.path.exists(img_path):
            img = pygame.image.load(img_path).convert_alpha()
            img = pygame.transform.smoothscale(img, (100, 100))
            TILES.append({
                "image": img,
                "bbox": (80, 80),  # Simplified bbox
                "area": item.get("area", 1000)
            })
    print(f"Loaded {len(TILES)} tiles")
except Exception as e:
    print(f"Tile load error: {e}")
    # Create fallback
    for i in range(3):
        surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.rect(surf, (random.randint(100,255), random.randint(100,255), random.randint(100,255)), 
                        (10, 10, 80, 80))
        TILES.append({"image": surf, "bbox": (80, 80), "area": 1000})

# Physics space
space = pymunk.Space()
space.gravity = (0, GRAVITY)
space.damping = DAMPING

# Bar (static)
bar_body = pymunk.Body(body_type=pymunk.Body.STATIC)
bar_body.position = (400, 500)
bar_shape = pymunk.Poly.create_box(bar_body, (400, 20))
bar_shape.friction = 1.0
space.add(bar_body, bar_shape)

# Game state
current_player = 1
preview_tile = random.choice(TILES) if TILES else None
preview_x = 400
preview_y = 100
preview_angle = 0
dropped_bodies = []
game_over = False
settling = False
settle_count = 0

def create_body(x, y, tile, player):
    w, h = tile["bbox"]
    mass = max(1, tile["area"] * 0.0001)
    moment = pymunk.moment_for_box(mass, (w, h))
    
    body = pymunk.Body(mass, moment)
    body.position = (x, 600 - y)  # Flip Y for pymunk
    body.angle = preview_angle
    body.linear_damping = DAMPING
    body.angular_damping = DAMPING
    body.player = player
    body.tile = tile
    
    shape = pymunk.Poly.create_box(body, (w, h))
    shape.friction = 1.0
    shape.elasticity = 0.1
    
    space.add(body, shape)
    return body

def draw_tile(body):
    img = body.tile["image"]
    pos = int(body.position.x), int(600 - body.position.y)
    angle = math.degrees(body.angle)
    rotated = pygame.transform.rotate(img, -angle)
    rect = rotated.get_rect(center=pos)
    SCREEN.blit(rotated, rect.topleft)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and preview_tile and not settling and not game_over:
                body = create_body(preview_x, preview_y, preview_tile, current_player)
                dropped_bodies.append(body)
                settling = True
                settle_count = 0
            
            if event.key == pygame.K_r and game_over:
                # Reset
                for b in dropped_bodies:
                    space.remove(b, *b.shapes)
                dropped_bodies = []
                current_player = 1
                game_over = False
                settling = False
                preview_tile = random.choice(TILES)
                preview_x = 400
                preview_angle = 0
            
            if event.key == pygame.K_LSHIFT:
                preview_angle += math.radians(15)
    
    # Movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        preview_x -= 5
    if keys[pygame.K_RIGHT]:
        preview_x += 5
    preview_x = max(50, min(750, preview_x))
    
    # Physics
    space.step(1/60)
    
    # Settle check
    if settling:
        still = all(b.velocity.length < 0.5 for b in dropped_bodies)
        if still:
            settle_count += 1
            if settle_count > 30:
                settling = False
                # Check loss (simplified)
                for b in dropped_bodies:
                    if b.player == current_player and (600 - b.position.y) > 520:
                        game_over = True
                        break
                if not game_over:
                    current_player = 2 if current_player == 1 else 1
                    preview_tile = random.choice(TILES)
                    preview_x = 400
                    preview_angle = 0
        else:
            settle_count = 0
    
    # Draw
    SCREEN.fill(WHITE)
    
    # Bar
    pygame.draw.rect(SCREEN, GRAY, (200, 100, 400, 20))
    
    # Dropped tiles
    for body in dropped_bodies:
        draw_tile(body)
    
    # Preview
    if preview_tile and not settling:
        img = preview_tile["image"]
        rotated = pygame.transform.rotate(img, -math.degrees(preview_angle))
        rect = rotated.get_rect(center=(preview_x, preview_y))
        SCREEN.blit(rotated, rect.topleft)
    
    # UI
    color = RED if current_player == 1 else BLUE
    pygame.draw.circle(SCREEN, color, (50, 50), 20)
    
    if game_over:
        text = FONT.render("GAME OVER - Press R", True, BLACK)
        SCREEN.blit(text, (200, 300))
    
    pygame.display.flip()
    CLOCK.tick(60)

pygame.quit()
sys.exit()
