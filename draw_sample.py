import numpy as np
import json
from PIL import Image, ImageDraw
import argparse

def draw_sample_strokes(strokes, output_path, width=750, height=160):
    """
    Draw handwriting strokes directly from sample data.
    
    Args:
        strokes: list of stroke points
        output_path: path to save the output image
        width: width of the output image
        height: height of the output image
    """
    # Create a new image with white background
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Extract all points for scaling
    all_points = []
    for stroke in strokes:
        all_points.extend(stroke)
    all_points = np.array(all_points)
    
    # Debug information
    print(f"\nNumber of strokes: {len(strokes)}")
    print(f"Total points: {len(all_points)}")
    print(f"X range: {np.min(all_points[:, 0])} to {np.max(all_points[:, 0])}")
    print(f"Y range: {np.min(all_points[:, 1])} to {np.max(all_points[:, 1])}")
    
    # Add padding
    padding = 40
    
    # Scale coordinates to fit the image while maintaining aspect ratio
    x_min, x_max = np.min(all_points[:, 0]), np.max(all_points[:, 0])
    y_min, y_max = np.min(all_points[:, 1]), np.max(all_points[:, 1])
    
    # Calculate scale factors
    x_scale = (width - 2*padding) / (x_max - x_min)
    y_scale = (height - 2*padding) / (y_max - y_min)
    scale = min(x_scale, y_scale)  # Use the smaller scale to maintain aspect ratio
    
    # Calculate centering offsets
    x_center_offset = (width - (x_max - x_min) * scale) / 2
    y_center_offset = (height - (y_max - y_min) * scale) / 2
    
    # Draw each stroke
    for stroke in strokes:
        if len(stroke) > 1:
            # Scale and center the points
            scaled_points = []
            for x, y in stroke:
                scaled_x = (x - x_min) * scale + x_center_offset
                scaled_y = (y - y_min) * scale + y_center_offset
                scaled_points.append((scaled_x, scaled_y))
            
            # Draw the stroke
            draw.line(scaled_points, fill='black', width=2)
            
            # Draw dots at the start and end of each stroke
            for point in [scaled_points[0], scaled_points[-1]]:
                x, y = point
                dot_radius = 1
                draw.ellipse([(x-dot_radius, y-dot_radius), (x+dot_radius, y+dot_radius)], fill='black')
    
    # Save the image
    img.save(output_path)
    print(f"Saved visualization to {output_path}")

def visualize_sample(json_path, output_path):
    """
    Load sample data from JSON file and visualize it.
    
    Args:
        json_path: path to the JSON file
        output_path: path to save the output image
    """
    # Load the data
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Extract strokes and text
    strokes = data.get('strokes', [])
    text = data.get('text', '')
    
    if not strokes:
        raise ValueError(f"No stroke data found in {json_path}")
    
    print(f"Text: {text}")
    
    # Draw the strokes
    draw_sample_strokes(strokes, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Visualize handwriting strokes from sample JSON files')
    parser.add_argument('--input', type=str, required=True, help='Path to the JSON file')
    parser.add_argument('--output', type=str, required=True, help='Path to save the output image')
    
    args = parser.parse_args()
    
    visualize_sample(args.input, args.output) 