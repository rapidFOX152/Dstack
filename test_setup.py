import pygame
import pymunk
import json
import os

print("=" * 50)
print("DStacks - Diagnostic Test")
print("=" * 50)

# Test 1: Pygame initialization
print("\n[1] Testing Pygame...")
try:
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    print("    ✓ Pygame initialized")
except Exception as e:
    print(f"    ✗ Pygame failed: {e}")
    exit(1)

# Test 2: Pymunk initialization
print("\n[2] Testing Pymunk...")
try:
    space = pymunk.Space()
    space.gravity = (0, -900)
    body = pymunk.Body(1, 1)
    body.position = (100, 100)
    shape = pymunk.Poly.create_box(body, (50, 50))
    space.add(body, shape)
    space.step(1/60)
    print("    ✓ Pymunk working")
except Exception as e:
    print(f"    ✗ Pymunk failed: {e}")
    exit(1)

# Test 3: Check tile data
print("\n[3] Checking tile data...")
if os.path.exists("assets/data/tiles.json"):
    try:
        with open("assets/data/tiles.json", "r") as f:
            tiles = json.load(f)
        print(f"    ✓ Found {len(tiles)} tiles")
        if tiles:
            print(f"    Sample: {tiles[0]}")
    except Exception as e:
        print(f"    ✗ JSON error: {e}")
else:
    print("    ✗ tiles.json not found!")
    print("    Run: python process_images.py")

# Test 4: Check images
print("\n[4] Checking images...")
if os.path.exists("assets/images/tiles"):
    images = [f for f in os.listdir("assets/images/tiles") if f.endswith('.png')]
    print(f"    ✓ Found {len(images)} PNG files")
    for img in images[:3]:
        print(f"      - {img}")
else:
    print("    ✗ assets/images/tiles folder not found!")

print("\n" + "=" * 50)
print("Diagnostic complete!")
print("=" * 50)

pygame.quit()
