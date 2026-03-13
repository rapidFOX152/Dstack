import json
import base64
import io
import cv2
import numpy as np
from PIL import Image

def generate_tile_definition(json_file, output_image_name):
    # 1. Load the data from your friend's file
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # 2. Decode the Base64 image
    b64_str = data['data_uri'].split(',')[1]
    image_bytes = base64.b64decode(b64_str)
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    img.save(f"assets/images/tiles/{output_image_name}") # Save to your game folder

    # 3. Find the shape (Contour)
    # Convert to numpy for OpenCV
    opencv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGRA)
    gray = cv2.cvtColor(opencv_img, cv2.COLOR_BGR2GRAY)
    
    # Thresholding: Assuming background is transparent or white
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("Mama, I couldn't find a shape in that image!")
        return

    # 4. Generate a Convex Hull (Simplified physics shape)
    main_contour = max(contours, key=cv2.contourArea)
    hull = cv2.convexHull(main_contour)
    
    # Simplify the hull so Pymunk doesn't lag (aim for ~8-12 points)
    epsilon = 0.01 * cv2.arcLength(hull, True)
    simplified_hull = cv2.approxPolyDP(hull, epsilon, True)
    
    # Format vertices for Pymunk (centering them)
    w, h = img.size
    center = (w/2, h/2)
    vertices = []
    for pt in simplified_hull:
        x, y = pt[0]
        vertices.append([float(x - center[0]), float(y - center[1])])

    # 5. Output the JSON block for your tiles.json
    tile_def = {
        "image_file": output_image_name,
        "pivot": [center[0], center[1]],
        "convex_parts": [vertices],
        "outer_contour": vertices # Using the same for the red outline
    }
    
    print("\n--- COPY THIS INTO YOUR tiles.json ---\n")
    print(json.dumps(tile_def, indent=4))
    print("\n--------------------------------------")

# Run it
generate_tile_definition('image_data.json', 'trump2.png')
