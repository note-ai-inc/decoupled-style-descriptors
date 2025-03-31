import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

def draw_strokes(stroke_data, output_path, width=750, height=160):
    """
    Draw handwriting strokes from stroke data.
    
    Args:
        stroke_data: numpy array or list containing stroke data with shape (N, 3)
        output_path: path to save the output image
        width: width of the output image
        height: height of the output image
        level: visualization level ('s': sentence, 'w': word, 'c': char)
    """
    # Convert list to numpy array if needed
    if isinstance(stroke_data, list):
        stroke_data = np.array(stroke_data)
    
    # Debug information
    print(f"\nStroke data shape: {stroke_data.shape}")
    print(f"X range: {np.min(stroke_data[:, 0])} to {np.max(stroke_data[:, 0])}")
    print(f"Y range: {np.min(stroke_data[:, 1])} to {np.max(stroke_data[:, 1])}")
    print(f"Pen states: {np.unique(stroke_data[:, 2])}")
    
    # Create a new image with white background
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Scale coordinates to fit the image
    x_coords = stroke_data[:, 0]
    y_coords = stroke_data[:, 1]
    pen_states = stroke_data[:, 2]
    
    # Add padding
    padding = 40
    
    # Scale coordinates to fit the image while maintaining aspect ratio
    x_min, x_max = np.min(x_coords), np.max(x_coords)
    y_min, y_max = np.min(y_coords), np.max(y_coords)
    
    # Calculate scale factors
    x_scale = (width - 2*padding) / (x_max - x_min)
    y_scale = (height - 2*padding) / (y_max - y_min)
    scale = min(x_scale, y_scale)  # Use the smaller scale to maintain aspect ratio
    
    # Calculate centering offsets
    x_center_offset = (width - (x_max - x_min) * scale) / 2
    y_center_offset = (height - (y_max - y_min) * scale) / 2
    
    # Scale and center the coordinates
    x_coords = (x_coords - x_min) * scale + x_center_offset
    y_coords = (y_coords - y_min) * scale + y_center_offset
    
    # Organize points into strokes based on pen state transitions
    strokes = []
    current_stroke = []
    
    for i in range(len(stroke_data)):
        x, y = x_coords[i], y_coords[i]
        pen_state = pen_states[i]
        
        if pen_state == 1:  # Start of a new stroke
            if current_stroke:  # Add the previous stroke if it exists
                strokes.append(current_stroke)
            current_stroke = [(x, y)]  # Start a new stroke with this point
        else:  # Continue current stroke
            if current_stroke:  # Only add to stroke if we have a current stroke
                # Check if this point is too far from the last point (likely a new word)
                last_x, last_y = current_stroke[-1]
                distance = np.sqrt((x - last_x)**2 + (y - last_y)**2)
                if distance > 30:  # Increased threshold for better word separation
                    strokes.append(current_stroke)
                    current_stroke = [(x, y)]
                else:
                    current_stroke.append((x, y))
            else:  # Start a new stroke if we don't have one
                current_stroke = [(x, y)]
    
    if current_stroke:  # Add the last stroke
        strokes.append(current_stroke)
    
    # Draw each stroke
    for stroke in strokes:
        if len(stroke) > 1:
            # Draw the stroke with varying thickness
            draw.line(stroke, fill='black', width=3)  # Increased line width
        # Draw dots at the start and end of each stroke
        for point in [stroke[0], stroke[-1]]:
            x, y = point
            dot_radius = 2  # Increased dot radius
            draw.ellipse([(x-dot_radius, y-dot_radius), (x+dot_radius, y+dot_radius)], fill='black')
    
    
    # Save the image
    img.save(output_path)
    print(f"Saved visualization to {output_path}")

def visualize_handwriting(npy_path, output_path, level='s'):
    """
    Load handwriting data from .npy file and visualize it.
    
    Args:
        npy_path: path to the .npy file
        output_path: path to save the output image
        level: visualization level ('s': sentence, 'w': word, 'c': char)
    """
    # Load the data
    data = np.load(npy_path, allow_pickle=True)
    
    # Extract stroke data (first element contains sentence-level raw stroke data)
    if(level == 's'):
        stroke_data = data[0]
    elif(level == 'w'):
        stroke_data = data[5][0]
    elif(level == 'c'):
        # Flatten the 2D array of segment-level strokes
        segment_strokes = data[10][0][0:3]
        stroke_data = np.vstack(segment_strokes)
        print(f"char Stroke data: {stroke_data}")
    
    # Draw the strokes
    draw_strokes(stroke_data, output_path)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize handwriting strokes from .npy files')
    parser.add_argument('--input', type=str, required=True, help='Path to the .npy file')
    parser.add_argument('--output', type=str, required=True, help='Path to save the output image')
    parser.add_argument('--level', type=str, default='s', choices=['s', 'w', 'c'],
                      help='Visualization level (s: sentence, w: word, c: char)')
    
    args = parser.parse_args()
    
    visualize_handwriting(args.input, args.output, level=args.level) 