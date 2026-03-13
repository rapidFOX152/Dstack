import pygame
import pymunk
import pymunk.pygame_util
from svgpathtools import svg2paths

# --- 1. SVG PARSING ---
def get_vertices_from_svg(filename, n_points=12):
    """ Converts SVG path to a list of (x, y) tuples for Pymunk """
    paths, _ = svg2paths(filename)
    path = paths[0] # Takes the first trace from Inkscape
    
    vertices = []
    for i in range(n_points):
        # Sample points along the SVG curve
        p = path.point(i / n_points)
        vertices.append((p.real, p.imag))
    
    # Center the vertices (Important: Pymunk shapes rotate around 0,0)
    avg_x = sum(v[0] for v in vertices) / n_points
    avg_y = sum(v[1] for v in vertices) / n_points
    return [(v[0] - avg_x, v[1] - avg_y) for v in vertices]

# --- 2. PYGAME & PYMUNK SETUP ---
pygame.init()
screen = pygame.display.set_mode((600, 600))
space = pymunk.Space()
space.gravity = (0, 900) # Earth-like gravity
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Create a floor so things can stack
floor_body = space.static_body
floor_shape = pymunk.Segment(floor_body, (0, 550), (600, 550), 5)
floor_shape.friction = 1.0
space.add(floor_shape)

# Load your Inkscape trace data
# Tip: Keep n_points low (8-14) for better stacking stability
MY_VERTICES = get_vertices_from_svg("your_trace.svg", n_points=12)

def spawn_tile(pos):
    mass = 1
    # Calculate moment of inertia based on your custom shape
    moment = pymunk.moment_for_poly(mass, MY_VERTICES)
    body = pymunk.Body(mass, moment)
    body.position = pos
    
    # Create a Convex Hull for stability
    shape = pymunk.Poly(body, MY_VERTICES)
    shape.friction = 0.8  # High friction stops sliding
    shape.elasticity = 0.2 # Low bounce
    space.add(body, shape)

# --- 3. MAIN LOOP ---
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            spawn_tile(event.pos)

    screen.fill((255, 255, 255))
    space.step(1/60.0) # Step the physics
    space.debug_draw(draw_options) # Shows the collision wireframes
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
