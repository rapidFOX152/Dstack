import os
import json
import cv2
import numpy as np
from PIL import Image
from shapely.geometry import Polygon
import math

def simplify_contour(contour, epsilon_factor=0.003):
    perimeter = cv2.arcLength(contour, True)
    epsilon = epsilon_factor * perimeter
    return cv2.approxPolyDP(contour, epsilon, True)

def get_centroid(contour):
    M = cv2.moments(contour)
    if M["m00"] == 0:
        return 0, 0
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    return cx, cy

def process_all_images(input_folder, output_json, alpha_threshold=10):
    tiles = []
    for filename in os.listdir(input_folder):
        if not filename.lower().endswith('.png'):
            continue
        path = os.path.join(input_folder, filename)
        print(f"Processing {filename}...")
        
        img = Image.open(path).convert('RGBA')
        alpha = np.array(img)[:,:,3]
        mask = (alpha > alpha_threshold).astype(np.uint8) * 255
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            print(f"  Skipping {filename}: no contours")
            continue
        
        contour = max(contours, key=cv2.contourArea)
        cx, cy = get_centroid(contour)
        simplified = simplify_contour(contour, epsilon_factor=0.003)
        
        points = simplified.reshape(-1, 2).tolist()
        # Ensure at least 3 points
        if len(points) < 3:
            print(f"  Not enough points, skipping")
            continue
        
        # Compute convex hull to ensure convexity (for physics)
        hull = cv2.convexHull(simplified).reshape(-1, 2).tolist()
        
        # Shift vertices so centroid is at origin
        local_verts = [[p[0] - cx, p[1] - cy] for p in hull]
        
        tiles.append({
            "image_file": filename,
            "pivot": [float(cx), float(cy)],
            "convex_parts": [local_verts],
            "area": 0.0
        })
        print(f"  Processed {filename} ({len(points)} points)")
    
    with open(output_json, 'w') as f:
        json.dump(tiles, f, indent=2)
    print(f"Saved {len(tiles)} tiles to {output_json}")

if __name__ == "__main__":
    process_all_images("assets/images/tiles", "assets/data/tiles.json")
