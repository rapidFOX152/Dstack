import os
import json
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import ConvexHull
import re

def tokenize_svg_path(d):
    """Tokenize SVG path into commands and numbers."""
    pattern = re.compile(r'([MLHVCSQTAZ]|[mlhvcsqtaz])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)')
    tokens = []
    for match in pattern.finditer(d):
        if match.group(1):
            tokens.append(match.group(1))
        else:
            tokens.append(float(match.group(2)))
    return tokens

def cubic_bezier_point(p0, p1, p2, p3, t):
    """Evaluate a cubic Bezier curve at parameter t."""
    return (1-t)**3 * np.array(p0) + 3*(1-t)**2*t * np.array(p1) + 3*(1-t)*t**2 * np.array(p2) + t**3 * np.array(p3)

def sample_bezier(p0, p1, p2, p3, num_samples=10):
    """Generate points along a cubic Bezier curve."""
    points = []
    for i in range(1, num_samples+1):
        t = i / num_samples
        points.append(cubic_bezier_point(p0, p1, p2, p3, t).tolist())
    return points

def parse_svg_path(d):
    """
    Convert SVG path to list of (x,y) coordinates.
    Handles M, L, C, and Z commands. For C, samples the curve.
    """
    tokens = tokenize_svg_path(d)
    coords = []
    i = 0
    current_pos = None
    while i < len(tokens):
        token = tokens[i]
        if isinstance(token, str):
            cmd = token.upper()
            i += 1
            if cmd == 'M':
                # Absolute move
                if i+1 < len(tokens) and isinstance(tokens[i], (int, float)) and isinstance(tokens[i+1], (int, float)):
                    x, y = tokens[i], tokens[i+1]
                    coords.append((x, y))
                    current_pos = (x, y)
                    i += 2
                else:
                    break
            elif cmd == 'L':
                # Absolute line
                while i+1 < len(tokens) and isinstance(tokens[i], (int, float)) and isinstance(tokens[i+1], (int, float)):
                    x, y = tokens[i], tokens[i+1]
                    coords.append((x, y))
                    current_pos = (x, y)
                    i += 2
            elif cmd == 'C':
                # Absolute cubic Bezier
                if current_pos is None:
                    break
                pts = []
                while len(pts) < 6 and i < len(tokens) and isinstance(tokens[i], (int, float)):
                    pts.append(tokens[i])
                    i += 1
                if len(pts) == 6:
                    p1 = (pts[0], pts[1])
                    p2 = (pts[2], pts[3])
                    p3 = (pts[4], pts[5])
                    curve_points = sample_bezier(current_pos, p1, p2, p3)
                    coords.extend(curve_points)
                    current_pos = p3
                else:
                    break
            elif cmd == 'Z':
                break
            else:
                print(f"Warning: unsupported command {cmd} – ignoring rest")
                break
        else:
            break
    return coords

def convex_hull_from_points(points):
    hull = ConvexHull(points)
    return [points[i] for i in hull.vertices]

input_folder = "assets/images/tiles"
output_json = "assets/data/tiles.json"

tiles = []
for filename in os.listdir(input_folder):
    if not filename.endswith('.svg'):
        continue
    name = filename[:-4]
    png_file = f"{name}.png"
    png_path = os.path.join(input_folder, png_file)
    if not os.path.exists(png_path):
        print(f"Warning: {png_file} not found for SVG {filename}, skipping")
        continue
    svg_path = os.path.join(input_folder, filename)
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        path_elem = root.find('.//{http://www.w3.org/2000/svg}path')
        if path_elem is None:
            print(f"No path found in {filename}")
            continue
        d = path_elem.get('d')
        points = parse_svg_path(d)
        if len(points) < 3:
            print(f"Not enough points in {filename} (got {len(points)})")
            continue

        # Debug prints
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        print(f"\nFile: {filename}")
        print(f"  Number of points: {len(points)}")
        print(f"  X range: {min(xs):.1f} to {max(xs):.1f}")
        print(f"  Y range: {min(ys):.1f} to {max(ys):.1f}")

        hull_points = convex_hull_from_points(points)
        hull_xs = [p[0] for p in hull_points]
        hull_ys = [p[1] for p in hull_points]
        print(f"  Hull points: {len(hull_points)}")
        print(f"  Hull X range: {min(hull_xs):.1f} to {max(hull_xs):.1f}")
        print(f"  Hull Y range: {min(hull_ys):.1f} to {max(hull_ys):.1f}")

        centroid = np.mean(hull_points, axis=0).tolist()
        print(f"  Centroid (pivot): {centroid}")

        local_verts = [[p[0] - centroid[0], p[1] - centroid[1]] for p in hull_points]
        tiles.append({
            "image_file": png_file,
            "pivot": centroid,
            "convex_parts": [local_verts],
            "area": 0.0
        })
        print(f"  Processed {filename} -> {png_file}\n")
    except Exception as e:
        print(f"Error processing {filename}: {e}")

with open(output_json, 'w') as f:
    json.dump(tiles, f, indent=2)

print(f"Saved {len(tiles)} tiles to {output_json}")
