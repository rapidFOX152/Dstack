import os
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, Point
import math

def simplify_contour(contour, epsilon_factor=0.003):
    """Lower epsilon = more vertices = better curve capture"""
    perimeter = cv2.arcLength(contour, True)
    epsilon = epsilon_factor * perimeter
    return cv2.approxPolyDP(contour, epsilon, True)

def get_centroid(contour):
    M = cv2.moments(contour)
    if M["m00"] == 0:
        return 0, 0
    cx = M["m10"] / M["m00"]
    cy = M["m01"] / M["m00"]
    return cx, cy

def get_polygon_center_of_mass(vertices):
    poly = Polygon(vertices)
    if poly.is_empty:
        return 0, 0
    centroid = poly.centroid
    return centroid.x, centroid.y

def is_convex(polygon):
    return polygon.convex_hull.equals(polygon)

def split_at_concave_vertex(polygon):
    coords = list(polygon.exterior.coords)[:-1]
    n = len(coords)
    
    for i in range(n):
        a = Point(coords[(i-1) % n])
        b = Point(coords[i])
        c = Point(coords[(i+1) % n])
        
        v1 = (a.x - b.x, a.y - b.y)
        v2 = (c.x - b.x, c.y - b.y)
        cross = v1[0]*v2[1] - v1[1]*v2[0]
        
        if cross > 0:
            for j in range(n):
                if j in [i, (i-1) % n, (i+1) % n]:
                    continue
                
                d = Point(coords[j])
                mid = Point((b.x + d.x)/2, (b.y + d.y)/2)
                
                if polygon.contains(mid):
                    if i < j:
                        poly1_coords = coords[i:j+1] + [coords[i]]
                        poly2_coords = coords[j:] + coords[:i+1] + [coords[j]]
                    else:
                        poly1_coords = coords[i:] + coords[:j+1] + [coords[i]]
                        poly2_coords = coords[j:i+1] + [coords[j]]
                    
                    poly1 = Polygon(poly1_coords)
                    poly2 = Polygon(poly2_coords)
                    
                    if poly1.is_valid and poly2.is_valid:
                        return [poly1, poly2]
    return []

def decompose_concave_polygon(polygon, max_depth=10):
    if polygon.is_empty or len(polygon.exterior.coords) < 4:
        return []
    
    if is_convex(polygon):
        return [polygon]
    
    if max_depth <= 0:
        return [polygon.convex_hull]
    
    split = split_at_concave_vertex(polygon)
    if not split:
        return [polygon.convex_hull]
    
    result = []
    for p in split:
        result.extend(decompose_concave_polygon(p, max_depth - 1))
    return result

def create_outline_image(img, contour, output_path, line_width=3):
    outline_img = img.copy()
    draw = ImageDraw.Draw(outline_img)
    
    points = contour.reshape(-1, 2).tolist()
    if len(points) >= 3:
        draw.polygon(points, outline=(255, 0, 0), width=line_width)
        for px, py in points:
            draw.ellipse([px-2, py-2, px+2, py+2], fill=(0, 255, 0))
    
    outline_img.save(output_path)
    print(f"  ✓ Outline: {len(points)} vertices")

def process_images(input_folder, output_json, output_outline_folder=None):
    tiles = []
    
    if not os.path.exists(input_folder):
        print(f"Error: Folder '{input_folder}' not found!")
        return
    
    if output_outline_folder and not os.path.exists(output_outline_folder):
        os.makedirs(output_outline_folder)
    
    processed_files = set()
    
    for filename in sorted(os.listdir(input_folder)):
        if not filename.lower().endswith(('.png', '.jpg')):
            continue
        
        base_name = filename.split('.')[0]
        if base_name in processed_files:
            continue
        
        best_file = None
        for ext_priority in ['-rbg.png', '.png', '.jpg']:
            test_file = base_name + ext_priority
            test_path = os.path.join(input_folder, test_file)
            if os.path.exists(test_path):
                best_file = test_file
                break
        
        if not best_file:
            continue
        
        processed_files.add(base_name)
        path = os.path.join(input_folder, best_file)
        print(f"\nProcessing {best_file}...")
        
        try:
            img = Image.open(path).convert('RGBA')
            img_w, img_h = img.width, img.height
            
            alpha = np.array(img)[:, :, 3]
            mask = (alpha > 128).astype(np.uint8) * 255
            
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.erode(mask, kernel, iterations=1)
            mask = cv2.dilate(mask, kernel, iterations=2)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                print(f"  ✗ No contours found")
                continue
            
            contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(contour)
            
            if area < 500:
                print(f"  ✗ Too small (area={area})")
                continue
            
            simplified = simplify_contour(contour, epsilon_factor=0.003)
            
            poly = Polygon(simplified.reshape(-1, 2))
            if not poly.is_valid:
                poly = poly.buffer(0)
            
            # Calculate TRUE center of mass from polygon
            com_x, com_y = get_polygon_center_of_mass(simplified.reshape(-1, 2))
            
            convex_parts = decompose_concave_polygon(poly)
            
            # Store ALL vertices RELATIVE to COM
            parts_local = []
            for part in convex_parts:
                coords = np.array(part.exterior.coords[:-1])
                local = (coords - [com_x, com_y]).tolist()
                parts_local.append(local)
            
            # Store outer contour RELATIVE to COM
            outer_contour_local = []
            for vx, vy in simplified.reshape(-1, 2):
                outer_contour_local.append([float(vx - com_x), float(vy - com_y)])
            
            total_area = sum(part.area for part in convex_parts)
            
            x, y, w, h = cv2.boundingRect(simplified)
            
            tiles.append({
                "image_file": best_file,
                "base_name": base_name,
                "image_size": [img_w, img_h],
                "center_of_mass": [float(com_x), float(com_y)],
                "bounding_box": [float(x), float(y), float(w), float(h)],
                "convex_parts": parts_local,
                "outer_contour": outer_contour_local,
                "num_vertices": len(simplified),
                "num_convex_parts": len(convex_parts),
                "area": float(total_area)
            })
            
            print(f"  ✓ Image: {img_w}x{img_h}")
            print(f"  ✓ COM: ({com_x:.1f}, {com_y:.1f})")
            print(f"  ✓ Vertices: {len(simplified)}")
            print(f"  ✓ Convex Parts: {len(convex_parts)}")
            print(f"  ✓ Area: {total_area:.1f}")
            
            if output_outline_folder:
                outline_path = os.path.join(output_outline_folder, f"{base_name}_outline.png")
                create_outline_image(img, simplified, outline_path)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    with open(output_json, 'w') as f:
        json.dump(tiles, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Processed {len(tiles)} tiles")
    print(f"Saved to: {output_json}")
    print(f"{'='*60}")
    
    return tiles

if __name__ == "__main__":
    tiles = process_images(
        input_folder="assets/images/tiles",
        output_json="assets/data/tiles.json",
        output_outline_folder="assets/images/outlines"
    )
