import numpy as np
import os
from PIL import Image, ImageDraw
import argparse

def load_style_samples(writer_id, num_samples=10):
    """Load style samples from NPY files."""
    samples = []
    for i in range(num_samples):
        npy_path = f'data/writers/{writer_id}/{i}.npy'
        if os.path.exists(npy_path):
            data = np.load(npy_path, allow_pickle=True)
            stroke_data = data[0]  # Get sentence_level_raw_stroke
            samples.append(stroke_data)
    return samples

def normalize_coordinates(points, divider=5.0):
    """Normalize coordinates to fit within a 5x5 box while maintaining aspect ratio."""
    if len(points) == 0:
        return np.array([])
    
    # Convert points to numpy array if needed
    points_array = np.array(points)
    
    # Find min and max coordinates
    min_coords = points_array.min(axis=0)
    max_coords = points_array.max(axis=0)
    
    # Calculate scale factors while maintaining aspect ratio
    scale_x = divider / (max_coords[0] - min_coords[0])
    scale_y = divider / (max_coords[1] - min_coords[1])
    scale = min(scale_x, scale_y)  # Use the smaller scale to maintain aspect ratio
    
    # Normalize coordinates
    normalized = (points_array - min_coords) * scale
    
    return normalized

def generate_stroke(text, style_samples, output_path, width=750, height=160):
    """Generate handwriting for the given text using style samples."""
    # Create a new image with white background
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Add padding
    padding = 40
    
    # Process each character
    x_offset = padding
    all_points = None
    all_pen_states = None
    
    for char in text:
        # Find a sample that contains this character
        char_stroke = None
        for sample in style_samples:
            # Extract points and pen states
            points = sample[:, :2]
            pen_states = sample[:, 2]
            
            # Normalize the points
            normalized_points = normalize_coordinates(points)
            
            # Add to our collection
            if all_points is None:
                all_points = normalized_points
                all_pen_states = pen_states
            else:
                # Add a small gap between characters
                x_offset += 0.5
                normalized_points[:, 0] += x_offset
                all_points = np.vstack([all_points, normalized_points])
                all_pen_states = np.concatenate([all_pen_states, pen_states])
            
            x_offset = np.max(all_points[:, 0]) + 0.5
    
    if all_points is None:
        raise ValueError("No valid points found in style samples")
    
    # Scale coordinates to fit the image
    x_min, x_max = np.min(all_points[:, 0]), np.max(all_points[:, 0])
    y_min, y_max = np.min(all_points[:, 1]), np.max(all_points[:, 1])
    
    # Calculate scale factors
    x_scale = (width - 2*padding) / (x_max - x_min)
    y_scale = (height - 2*padding) / (y_max - y_min)
    scale = min(x_scale, y_scale)
    
    # Calculate centering offsets
    x_center_offset = (width - (x_max - x_min) * scale) / 2
    y_center_offset = (height - (y_max - y_min) * scale) / 2
    
    # Scale and center the points
    scaled_points = []
    current_stroke = []
    
    for i in range(len(all_points)):
        x, y = all_points[i]
        pen_state = all_pen_states[i]
        
        # Scale and center the point
        scaled_x = (x - x_min) * scale + x_center_offset
        scaled_y = (y - y_min) * scale + y_center_offset
        
        if pen_state == 0:  # Pen up
            if current_stroke:
                scaled_points.append(current_stroke)
                current_stroke = []
        else:  # Pen down
            current_stroke.append((scaled_x, scaled_y))
    
    if current_stroke:
        scaled_points.append(current_stroke)
    
    # Draw the strokes
    for stroke in scaled_points:
        if len(stroke) > 1:
            # Draw the stroke
            draw.line(stroke, fill='black', width=2)
            
            # Draw dots at the start and end of each stroke
            for point in [stroke[0], stroke[-1]]:
                x, y = point
                dot_radius = 1
                draw.ellipse([(x-dot_radius, y-dot_radius), (x+dot_radius, y+dot_radius)], fill='black')
    
    # Save the image
    img.save(output_path)
    print(f"Generated text: {text}")
    print(f"Saved visualization to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate handwriting text using style samples')
    parser.add_argument('--text', type=str, required=True, help='Text to generate')
    parser.add_argument('--writer_id', type=int, default=200, help='ID of the writer to use for style')
    parser.add_argument('--output', type=str, required=True, help='Path to save the output image')
    
    args = parser.parse_args()
    
    # Load style samples
    style_samples = load_style_samples(args.writer_id)
    
    # Generate the text
    generate_stroke(args.text, style_samples, args.output)

if __name__ == '__main__':
    main() 