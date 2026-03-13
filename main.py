import pygame
import sys
import pymunk
import math
import random
import json
import os
import numpy as np
from scipy.spatial import ConvexHull

pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Bar
BAR_WIDTH = 600
BAR_VISUAL_HEIGHT = 8
BAR_PHYSICS_HEIGHT = 25
BAR_Y = 500

# Physics
GRAVITY = -700
COLLISION_MARGIN = 0.5
SETTLE_DURATION = 240
VELOCITY_THRESHOLD = 0.5
STILL_FRAMES_REQUIRED = 30
SETTLE_READY_DELAY = 10
DENSITY = 0.3
DAMPING = 0.2
SOLVER_ITERATIONS = 40
LOSS_TOLERANCE = 5

# Movement
ANGLE_STEP = math.radians(10)
MOVE_STEP = 8
TARGET_TILE_SIZE = 162

# Colors
P1_COLOR_MAIN = (231, 76, 60)
P1_COLOR_LIGHT = (236, 112, 99)
P1_COLOR_DARK = (192, 57, 43)
P1_TINT = (231, 76, 60, 40)

P2_COLOR_MAIN = (52, 152, 219)
P2_COLOR_LIGHT = (93, 173, 226)
P2_COLOR_DARK = (41, 128, 185)
P2_TINT = (52, 152, 219, 40)

NEUTRAL_COLOR = (139, 69, 19)
BACKGROUND_TOP = (220, 220, 240)
BACKGROUND_BOTTOM = (180, 180, 200)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("DStacks")
clock = pygame.time.Clock()

# Sound (optional)
sounds = {}
sound_enabled = True
try:
    sounds['drop'] = pygame.mixer.Sound("assets/sounds/drop.wav")
    sounds['game_over'] = pygame.mixer.Sound("assets/sounds/game_over.wav")
    pygame.mixer.music.load("assets/sounds/background_music.ogg")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
except:
    print("Sound files missing – continuing without sound.")

# Load tile definitions
tile_defs = []
fallback_polygons = True

try:
    with open("assets/data/tiles.json", "r") as f:
        tile_data = json.load(f)
    print(f"Tiles in JSON: {len(tile_data)}")
    for item in tile_data:
        img_path = os.path.join("assets/images/tiles", item["image_file"])
        if os.path.exists(img_path):
            img_orig = pygame.image.load(img_path).convert_alpha()
            orig_w, orig_h = img_orig.get_size()
            print(f"Loaded image: {img_path} -> size {orig_w}x{orig_h}")
            scale = min(TARGET_TILE_SIZE / orig_w, TARGET_TILE_SIZE / orig_h, 1.0)
            if scale < 1.0:
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                img = pygame.transform.smoothscale(img_orig, (new_w, new_h))
            else:
                img = img_orig
                scale = 1.0
                new_w, new_h = orig_w, orig_h
            
            if "center_of_mass" in item:
                com = [item["center_of_mass"][0] * scale, item["center_of_mass"][1] * scale]
            else:
                com = [item["pivot"][0] * scale, item["pivot"][1] * scale]
            
            convex_parts = []
            for part in item["convex_parts"]:
                scaled_part = [[x * scale, y * scale] for x, y in part]
                convex_parts.append(scaled_part)
            
            outer_contour = None
            if "outer_contour" in item:
                outer_contour = [[v[0] * scale, v[1] * scale] for v in item["outer_contour"]]
            
            area = item.get("area", None)
            if area is not None:
                area *= (scale * scale)
            
            tile_defs.append({
                "surface": img,
                "convex_parts": convex_parts,
                "com": com,
                "area": area,
                "outer_contour": outer_contour,
                "image_size": (new_w, new_h)
            })
        else:
            print(f"Warning: {img_path} not found, skipping.")
    if tile_defs:
        fallback_polygons = False
        print(f"Loaded {len(tile_defs)} tile images.")
        for i, td in enumerate(tile_defs):
            print(f"Tile {i}: image size={td['image_size']}, convex parts={len(td['convex_parts'])}")
except Exception as e:
    print(f"Tile data error: {e}. Using random polygons.")

def random_convex_polygon(center=(0,0), avg_radius=45, num_vertices=8):
    angles = sorted(random.uniform(0, 2*math.pi) for _ in range(num_vertices))
    points = []
    for ang in angles:
        r = avg_radius * random.uniform(0.7, 1.3)
        x = center[0] + r * math.cos(ang)
        y = center[1] + r * math.sin(ang)
        points.append((x, y))
    hull = ConvexHull(points)
    hull_points = [points[i] for i in hull.vertices]
    return hull_points

# Pymunk space
space = pymunk.Space()
space.gravity = (0, GRAVITY)
space.collision_slop = 0.2
space.iterations = SOLVER_ITERATIONS

# Bar
bar_body = pymunk.Body(body_type=pymunk.Body.STATIC)
bar_center_x = SCREEN_WIDTH // 2
bar_top_y = SCREEN_HEIGHT - BAR_Y
bar_center_y = bar_top_y - BAR_PHYSICS_HEIGHT / 2
bar_body.position = (bar_center_x, bar_center_y)
bar_shape = pymunk.Poly.create_box(bar_body, (BAR_WIDTH, BAR_PHYSICS_HEIGHT))
bar_shape.friction = 1.0
bar_shape.elasticity = 0.05
bar_shape.collision_margin = COLLISION_MARGIN
space.add(bar_body, bar_shape)

def to_pygame(p):
    if hasattr(p, 'x'):
        return int(p.x), int(SCREEN_HEIGHT - p.y)
    else:
        return int(p[0]), int(SCREEN_HEIGHT - p[1])

def draw_gradient_rect(surface, color_top, color_bottom, rect):
    height = rect.height
    for y in range(rect.top, rect.bottom):
        ratio = (y - rect.top) / height
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (rect.left, y), (rect.right, y))

def draw_rounded_rect(surface, color, rect, radius, border=0, border_color=None):
    x, y, w, h = rect
    if radius > min(w, h) // 2:
        radius = min(w, h) // 2
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, color, (0, 0, w, h), border_radius=radius)
    if border > 0 and border_color:
        pygame.draw.rect(s, border_color, (0, 0, w, h), border, border_radius=radius)
    surface.blit(s, (x, y))

# Keep track of which bodies we've already printed for (to avoid spam)
printed_bodies = set()

def draw_objects():
    """Draw all physics objects (tiles) – either images or colored polygons."""
    for shape in space.shapes:
        if shape == bar_shape:
            continue
        if isinstance(shape, pymunk.Poly):
            body = shape.body
            if hasattr(body, 'tile_data'):
                # Draw image tile
                img = body.tile_data['surface']
                com = body.tile_data.get('com', [img.get_width()/2, img.get_height()/2])
                angle = body.angle
                body_pos = to_pygame(body.position)
                angle_deg = math.degrees(angle)
                rotated = pygame.transform.rotate(img, -angle_deg)
                
                # Find COM position on rotated image
                img_w, img_h = img.get_size()
                img_center = (img_w / 2, img_h / 2)
                vec_to_com_x = com[0] - img_center[0]
                vec_to_com_y = com[1] - img_center[1]
                rotated_vec_x = vec_to_com_x * math.cos(angle) - vec_to_com_y * math.sin(angle)
                rotated_vec_y = vec_to_com_x * math.sin(angle) + vec_to_com_y * math.cos(angle)
                com_on_rotated_x = img_center[0] + rotated_vec_x
                com_on_rotated_y = img_center[1] + rotated_vec_y
                draw_x = body_pos[0] - com_on_rotated_x
                draw_y = body_pos[1] - com_on_rotated_y
                screen.blit(rotated, (draw_x, draw_y))
                
                # Debug: print first time we draw this tile
                if id(body) not in printed_bodies:
                    printed_bodies.add(id(body))
                    print(f"Drawing image for tile: {body.tile_data.get('image_file', 'unknown')}")
                
                # DEBUG: Draw convex parts in green
                for part in body.tile_data['convex_parts']:
                    # Transform vertices to world
                    world_verts = []
                    for vx, vy in part:
                        rx = vx * math.cos(angle) - vy * math.sin(angle)
                        ry = vx * math.sin(angle) + vy * math.cos(angle)
                        wx = body.position.x + rx
                        wy = body.position.y + ry
                        world_verts.append(to_pygame((wx, wy)))
                    if len(world_verts) >= 3:
                        pygame.draw.polygon(screen, (0,255,0), world_verts, 2)  # green outline
            else:
                # Fallback: draw colored polygon
                vertices = [body.local_to_world(v) for v in shape.get_vertices()]
                screen_verts = [to_pygame(v) for v in vertices]
                if len(screen_verts) >= 3:
                    if hasattr(body, 'player'):
                        color = P1_COLOR_MAIN if body.player == 1 else P2_COLOR_MAIN
                    else:
                        color = (180, 180, 180)
                    pygame.draw.polygon(screen, color, screen_verts)
                    pygame.draw.polygon(screen, (0, 0, 0), screen_verts, 2)

def draw_physics_outlines():
    """Draw RED outer contour - LOCKED to same transformation as image"""
    for body in space.bodies:
        if body.body_type == pymunk.Body.DYNAMIC and hasattr(body, 'tile_data'):
            tile_data = body.tile_data
            if 'outer_contour' in tile_data and tile_data['outer_contour']:
                world_verts = []
                for vx, vy in tile_data['outer_contour']:
                    rotated_x = vx * math.cos(body.angle) - vy * math.sin(body.angle)
                    rotated_y = vx * math.sin(body.angle) + vy * math.cos(body.angle)
                    world_x = body.position.x + rotated_x
                    world_y = body.position.y + rotated_y
                    world_verts.append((world_x, world_y))
                screen_verts = [to_pygame(v) for v in world_verts]
                if len(screen_verts) >= 3:
                    pygame.draw.polygon(screen, (255, 0, 0), screen_verts, 2)
                    for vx, vy in screen_verts:
                        pygame.draw.circle(screen, (0, 255, 0), (int(vx), int(vy)), 2)

def draw_preview(surface, preview_data, x, y, angle, player):
    if 'surface' in preview_data:
        img = preview_data['surface']
        com = preview_data.get('com', [img.get_width()/2, img.get_height()/2])
        angle_deg = math.degrees(angle)
        rotated = pygame.transform.rotate(img, -angle_deg)
        
        img_w, img_h = img.get_size()
        img_center = (img_w / 2, img_h / 2)
        vec_to_com_x = com[0] - img_center[0]
        vec_to_com_y = com[1] - img_center[1]
        rotated_vec_x = vec_to_com_x * math.cos(angle) - vec_to_com_y * math.sin(angle)
        rotated_vec_y = vec_to_com_x * math.sin(angle) + vec_to_com_y * math.cos(angle)
        com_on_rotated_x = img_center[0] + rotated_vec_x
        com_on_rotated_y = img_center[1] + rotated_vec_y
        
        draw_x = x - com_on_rotated_x
        draw_y = y - com_on_rotated_y
        surface.blit(rotated, (draw_x, draw_y))
    else:
        vertices = preview_data['vertices']
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        rotated = []
        for vx, vy in vertices:
            rx = vx * cos_a - vy * sin_a
            ry = vx * sin_a + vy * cos_a
            sx = x + rx
            sy = y - ry
            rotated.append((sx, sy))
        if len(rotated) >= 3:
            color = P1_COLOR_MAIN + (180,) if player == 1 else P2_COLOR_MAIN + (180,)
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(s, color, rotated)
            surface.blit(s, (0, 0))
            pygame.draw.polygon(surface, (0, 0, 0), rotated, 2)

def check_loss(player):
    for body in space.bodies:
        if body.body_type == pymunk.Body.DYNAMIC and hasattr(body, 'player') and body.player == player:
            for shape in body.shapes:
                if isinstance(shape, pymunk.Poly):
                    vertices = [body.local_to_world(v) for v in shape.get_vertices()]
                    screen_verts = [to_pygame(v) for v in vertices]
                    if screen_verts:
                        lowest = max(v[1] for v in screen_verts)
                        if lowest > BAR_Y + LOSS_TOLERANCE:
                            return True
    return False

def all_bodies_still():
    for body in space.bodies:
        if body.body_type == pymunk.Body.DYNAMIC:
            if body.velocity.length > VELOCITY_THRESHOLD:
                return False
    return True

def draw_background(player):
    draw_gradient_rect(screen, BACKGROUND_TOP, BACKGROUND_BOTTOM,
                       pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
    tint = P1_TINT if player == 1 else P2_TINT
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill(tint)
    screen.blit(overlay, (0, 0))

# Game state
current_player = 1
game_over = False
winner = None
transition_active = False
transition_timer = 0
next_player = 1
preview_active = True
preview_data = None
preview_x = SCREEN_WIDTH // 2
preview_y = 50
preview_angle = 0.0
dragging = False
settling = False
settle_frames = 0
still_counter = 0
settle_ready_counter = 0
key_left = False
key_right = False
key_shift = False

button_font = pygame.font.Font(None, 42)
try:
    button_font = pygame.font.Font("assets/fonts/Roboto-Bold.ttf", 36)
except:
    pass

buttons = {
    'rotate': pygame.Rect(250, 540, 120, 50),
    'drop': pygame.Rect(430, 540, 120, 50)
}
button_labels = {
    'rotate': '↻ ROTATE',
    'drop': 'DROP'
}
hover_button = None

if tile_defs:
    chosen = random.choice(tile_defs)
    preview_data = {
        'surface': chosen['surface'],
        'convex_parts': chosen['convex_parts'],
        'area': chosen.get('area'),
        'com': chosen.get('com'),
        'outer_contour': chosen.get('outer_contour')
    }
else:
    preview_data = {'vertices': random_convex_polygon()}

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    hover_button = None
    for name, rect in buttons.items():
        if rect.collidepoint(mouse_pos):
            hover_button = name
            break

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            sound_enabled = not sound_enabled
            if sound_enabled:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.pause()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and game_over:
                space.remove(*space.bodies, *space.shapes)
                space.add(bar_body, bar_shape)
                current_player = 1
                game_over = False
                winner = None
                transition_active = False
                preview_active = True
                if tile_defs:
                    chosen = random.choice(tile_defs)
                    preview_data = {
                        'surface': chosen['surface'],
                        'convex_parts': chosen['convex_parts'],
                        'area': chosen.get('area'),
                        'com': chosen.get('com'),
                        'outer_contour': chosen.get('outer_contour')
                    }
                else:
                    preview_data = {'vertices': random_convex_polygon()}
                preview_x = SCREEN_WIDTH // 2
                preview_angle = 0.0
                settling = False
                dragging = False
                continue

            if not game_over and preview_active and not settling and not transition_active:
                if event.key == pygame.K_LEFT:
                    key_left = True
                elif event.key == pygame.K_RIGHT:
                    key_right = True
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    key_shift = True
                elif event.key == pygame.K_SPACE:
                    pos = (preview_x, SCREEN_HEIGHT - preview_y)
                    if 'convex_parts' in preview_data:
                        convex_parts = preview_data['convex_parts']
                        if preview_data.get('area'):
                            mass = max(0.1, preview_data['area'] * DENSITY)
                        else:
                            total_area = 0
                            for part in convex_parts:
                                xs = [p[0] for p in part]
                                ys = [p[1] for p in part]
                                area = 0.5 * abs(sum(xs[i]*ys[(i+1)%len(part)] - xs[(i+1)%len(part)]*ys[i] for i in range(len(part))))
                                total_area += area
                            mass = max(0.1, total_area * DENSITY)
                        all_verts = []
                        for part in convex_parts:
                            all_verts.extend(part)
                        if all_verts:
                            moment = pymunk.moment_for_poly(mass, all_verts)
                        else:
                            moment = float('inf')
                        body = pymunk.Body(mass, moment)
                        body.position = pos
                        body.angle = preview_angle
                        body.linear_damping = DAMPING
                        body.angular_damping = DAMPING
                        body.player = current_player
                        body.tile_data = preview_data
                        shapes = []
                        for part in convex_parts:
                            shape = pymunk.Poly(body, part)
                            shape.friction = 1.0
                            shape.elasticity = 0.05
                            shape.collision_margin = COLLISION_MARGIN
                            shapes.append(shape)
                        space.add(body, *shapes)
                    else:
                        vertices = preview_data['vertices']
                        mass = 1.0
                        moment = pymunk.moment_for_poly(mass, vertices)
                        body = pymunk.Body(mass, moment)
                        body.position = pos
                        body.angle = preview_angle
                        body.linear_damping = DAMPING
                        body.angular_damping = DAMPING
                        body.player = current_player
                        shape = pymunk.Poly(body, vertices)
                        shape.friction = 1.0
                        shape.elasticity = 0.05
                        shape.collision_margin = COLLISION_MARGIN
                        space.add(body, shape)
                    
                    if sound_enabled and 'drop' in sounds:
                        sounds['drop'].play()
                    preview_active = False
                    settling = True
                    settle_frames = 0
                    still_counter = 0
                    settle_ready_counter = 0

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                key_left = False
            elif event.key == pygame.K_RIGHT:
                key_right = False
            elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                key_shift = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if settling or transition_active or game_over:
                continue
            button_clicked = False
            for name, rect in buttons.items():
                if rect.collidepoint(event.pos):
                    button_clicked = True
                    if name == 'rotate':
                        preview_angle += ANGLE_STEP
                    elif name == 'drop':
                        pos = (preview_x, SCREEN_HEIGHT - preview_y)
                        if 'convex_parts' in preview_data:
                            convex_parts = preview_data['convex_parts']
                            if preview_data.get('area'):
                                mass = max(0.1, preview_data['area'] * DENSITY)
                            else:
                                total_area = 0
                                for part in convex_parts:
                                    xs = [p[0] for p in part]
                                    ys = [p[1] for p in part]
                                    area = 0.5 * abs(sum(xs[i]*ys[(i+1)%len(part)] - xs[(i+1)%len(part)]*ys[i] for i in range(len(part))))
                                    total_area += area
                                mass = max(0.1, total_area * DENSITY)
                            all_verts = []
                            for part in convex_parts:
                                all_verts.extend(part)
                            if all_verts:
                                moment = pymunk.moment_for_poly(mass, all_verts)
                            else:
                                moment = float('inf')
                            body = pymunk.Body(mass, moment)
                            body.position = pos
                            body.angle = preview_angle
                            body.linear_damping = DAMPING
                            body.angular_damping = DAMPING
                            body.player = current_player
                            body.tile_data = preview_data
                            shapes = []
                            for part in convex_parts:
                                shape = pymunk.Poly(body, part)
                                shape.friction = 1.0
                                shape.elasticity = 0.05
                                shape.collision_margin = COLLISION_MARGIN
                                shapes.append(shape)
                            space.add(body, *shapes)
                        else:
                            vertices = preview_data['vertices']
                            mass = 1.0
                            moment = pymunk.moment_for_poly(mass, vertices)
                            body = pymunk.Body(mass, moment)
                            body.position = pos
                            body.angle = preview_angle
                            body.linear_damping = DAMPING
                            body.angular_damping = DAMPING
                            body.player = current_player
                            shape = pymunk.Poly(body, vertices)
                            shape.friction = 1.0
                            shape.elasticity = 0.05
                            shape.collision_margin = COLLISION_MARGIN
                            space.add(body, shape)
                        if sound_enabled and 'drop' in sounds:
                            sounds['drop'].play()
                        preview_active = False
                        settling = True
                        settle_frames = 0
                        still_counter = 0
                        settle_ready_counter = 0
                    break
            if not button_clicked and preview_active and not settling:
                dragging = True
                preview_x = event.pos[0]

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            dragging = False

        if event.type == pygame.MOUSEMOTION:
            if dragging and preview_active and not settling and not transition_active and not game_over:
                preview_x = event.pos[0]

    if not game_over and preview_active and not settling and not transition_active:
        if key_left:
            preview_x -= MOVE_STEP
        if key_right:
            preview_x += MOVE_STEP
        if key_shift:
            preview_angle += ANGLE_STEP

    preview_x = max(20, min(SCREEN_WIDTH - 20, preview_x))

    for _ in range(8):
        space.step(1 / FPS / 8)

    if settling:
        settle_frames += 1
        if all_bodies_still():
            still_counter += 1
        else:
            still_counter = 0
            settle_ready_counter = 0

        if still_counter >= STILL_FRAMES_REQUIRED:
            settle_ready_counter += 1
            if settle_ready_counter >= SETTLE_READY_DELAY:
                settling = False
                if check_loss(current_player):
                    game_over = True
                    winner = 3 - current_player
                    if sound_enabled and 'game_over' in sounds:
                        sounds['game_over'].play()
                else:
                    transition_active = True
                    transition_timer = 60
                    next_player = 2 if current_player == 1 else 1
        elif settle_frames >= SETTLE_DURATION:
            settling = False
            if check_loss(current_player):
                game_over = True
                winner = 3 - current_player
                if sound_enabled and 'game_over' in sounds:
                    sounds['game_over'].play()
            else:
                transition_active = True
                transition_timer = 60
                next_player = 2 if current_player == 1 else 1

    if transition_active:
        transition_timer -= 1
        if transition_timer <= 0:
            transition_active = False
            current_player = next_player
            preview_active = True
            if tile_defs:
                chosen = random.choice(tile_defs)
                preview_data = {
                    'surface': chosen['surface'],
                    'convex_parts': chosen['convex_parts'],
                    'area': chosen.get('area'),
                    'com': chosen.get('com'),
                    'outer_contour': chosen.get('outer_contour')
                }
            else:
                preview_data = {'vertices': random_convex_polygon()}
            preview_x = SCREEN_WIDTH // 2
            preview_angle = 0.0
            dragging = False
            key_left = key_right = key_shift = False

    # Drawing
    if game_over:
        draw_background(winner)
    elif transition_active:
        draw_background(next_player)
    else:
        draw_background(current_player)

    bar_rect = pygame.Rect(0, 0, BAR_WIDTH, BAR_VISUAL_HEIGHT)
    bar_rect.topleft = (SCREEN_WIDTH // 2 - BAR_WIDTH // 2, BAR_Y)
    pygame.draw.rect(screen, NEUTRAL_COLOR, bar_rect, border_radius=5)
    pygame.draw.rect(screen, (0, 0, 0), bar_rect, 2, border_radius=5)

    # DEBUG: Draw bar physics shape in red
    bar_verts = [bar_body.local_to_world(v) for v in bar_shape.get_vertices()]
    bar_screen_verts = [to_pygame(v) for v in bar_verts]
    if len(bar_screen_verts) >= 3:
        pygame.draw.polygon(screen, (255,0,0), bar_screen_verts, 2)

    draw_objects()
    draw_physics_outlines()

    active_player = next_player if transition_active else current_player
    for name, rect in buttons.items():
        if active_player == 1:
            base_color = P1_COLOR_MAIN
            light_color = P1_COLOR_LIGHT
            dark_color = P1_COLOR_DARK
        else:
            base_color = P2_COLOR_MAIN
            light_color = P2_COLOR_LIGHT
            dark_color = P2_COLOR_DARK

        if hover_button == name and not game_over and not settling and not transition_active:
            fill_color = light_color
            border_color = dark_color
        else:
            fill_color = base_color
            border_color = dark_color

        draw_rounded_rect(screen, fill_color, rect, 12, border=2, border_color=border_color)

        text = button_font.render(button_labels[name], True, (255,255,255))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    if preview_active and not settling and not transition_active and not game_over:
        draw_preview(screen, preview_data, preview_x, preview_y, preview_angle, current_player)

    if transition_active:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        font = pygame.font.Font(None, 72)
        player_color_name = "Red" if next_player == 1 else "Blue"
        text = font.render(f"{player_color_name}'s Turn", True, (255,255,255))
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
        screen.blit(text, text_rect)

        font_small = pygame.font.Font(None, 48)
        subtext = font_small.render("Get Ready...", True, (220,220,220))
        sub_rect = subtext.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
        screen.blit(subtext, sub_rect)

    if game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        font = pygame.font.Font(None, 72)
        winner_color_name = "Red" if winner == 1 else "Blue"
        text = font.render(f"{winner_color_name} Wins!", True, (255,255,255))
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
        screen.blit(text, text_rect)

        font_small = pygame.font.Font(None, 48)
        restart_text = font_small.render("Press ENTER to restart", True, (220,220,220))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
        screen.blit(restart_text, restart_rect)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
