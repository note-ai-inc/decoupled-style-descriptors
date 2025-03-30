import torch
import numpy as np
import os
import svgwrite
from PIL import Image, ImageDraw
from SynthesisNetwork import SynthesisNetwork
from DataLoader import DataLoader
import convenience

def generate_handwriting(writer_id, target_text, output_path="output"):
    """
    Generate handwriting for target text using a specified writer style.
    This version fixes tensor dimension issues.
    
    Args:
        writer_id (int): ID of the writer style to use (0-169)
        target_text (str): The text to generate handwriting for
        output_path (str): Path to save the output files
    """
    # Create output directory if needed
    os.makedirs(output_path, exist_ok=True)
    
    # Define output filenames
    base_filename = f"{writer_id}_{target_text.replace(' ', '_')}"
    svg_path = os.path.join(output_path, f"{base_filename}.svg")
    png_path = os.path.join(output_path, f"{base_filename}.png")
    strokes_path = os.path.join(output_path, f"{base_filename}_strokes.txt")
    
    # Force CPU usage for consistency
    device = 'cpu'
    
    # Initialize model
    print(f"Generating handwriting for '{target_text}' using writer style {writer_id}")
    print("Loading model...")
    net = SynthesisNetwork(weight_dim=256, num_layers=3).to(device)
    
    # Load model weights
    try:
        state_dict = torch.load('./model/250000.pt', map_location=torch.device('cpu'))
        if "model_state_dict" in state_dict:
            net.load_state_dict(state_dict["model_state_dict"])
        else:
            net.load_state_dict(state_dict)
        print("Model loaded successfully")
    except Exception as e:
        print(f"Error loading model: {e}")
        return None
    
    # Load data from the writer
    dl = DataLoader(num_writer=1, num_samples=1, divider=3.0, datadir='./data/writers')
    loaded_data = dl.next_batch(TYPE='TRAIN', uid=writer_id, tids=list(range(10)))  # Use samples 0 to 9
    # print("Loaded Data : ", loaded_data)
    # print("Loadded Data Shape : ", len(loaded_data))
    # Extract the writer's style
    mean_global_W = convenience.get_mean_global_W(net, loaded_data, device)
    
    # Use the draw_words_svg function from convenience.py
    print(f"Generating handwriting for text: '{target_text}'")
    words = target_text.split()
    
    # Create word style vectors and character matrices for each word
    word_Ws = []
    word_Cs = []
    
    for word in words:
        print(f"Processing word: '{word}'")
        writer_Ws, writer_Cs = convenience.get_DSD(net, word, [mean_global_W], [loaded_data], device)
        word_Ws.append(writer_Ws.cpu())
        word_Cs.append(writer_Cs.cpu())
    
    # Use the original function from convenience.py to draw the SVG
    svg = convenience.draw_words_svg(words, word_Ws, word_Cs, [1.0], net)
    
    # Save SVG
    svg.saveas(svg_path)
    print(f"Saved SVG to {svg_path}")
    
    # Extract command points from the SVG for visualization and strokes file
    all_commands = []
    for path in svg.elements:
        if isinstance(path, svgwrite.path.Path):
            # Extract path data
            d = path['d']
            points = []
            pen_down = True
            
            # Parse SVG path commands
            parts = d.split()
            current_x, current_y = 0, 0
            
            for i, part in enumerate(parts):
                if part == 'M':
                    # Move to (pen up, then down for next segment)
                    x, y = float(parts[i+1]), float(parts[i+2])
                    points.append([x, y, 1])  # Pen up
                    current_x, current_y = x, y
                    pen_down = True
                elif part == 'L':
                    # Line to (pen down)
                    x, y = float(parts[i+1]), float(parts[i+2])
                    points.append([x, y, 0])  # Pen down
                    current_x, current_y = x, y
            
            all_commands.extend(points)
    
    # Save strokes data
    with open(strokes_path, 'w') as f:
        for x, y, t in all_commands:
            f.write(f"{x},{y},{t}\n")
    print(f"Saved stroke data to {strokes_path}")
    
    # Create a PNG visualization
    try:
        # Create image and drawing context
        img_width, img_height = 800, 200
        img = Image.new("RGB", (img_width, img_height), color="black")
        draw = ImageDraw.Draw(img)
        
        # Draw strokes
        prev_x, prev_y = None, None
        for x, y, t in all_commands:
            if t == 0 and prev_x is not None:  # Pen down and we have a previous point
                draw.line((prev_x, prev_y, x, y), fill="white", width=2)
            
            prev_x, prev_y = x, y
        
        # Save the image
        img.save(png_path)
        print(f"Saved PNG to {png_path}")
        
        # Show the image
        img.show()
    except Exception as e:
        print(f"Error creating PNG: {e}")
    
    return {
        "all_commands": all_commands,
        "svg_path": svg_path,
        "png_path": png_path,
        "strokes_path": strokes_path
    }

# If the script is run directly
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate handwriting')
    parser.add_argument('--writer_id', type=int, default=80, help='Writer ID (0-169)')
    parser.add_argument('--text', type=str, required=True, help='Text to generate')
    parser.add_argument('--output', type=str, default='output', help='Output directory')
    parser.add_argument('--svg', action='store_true', help='Generate SVG (already done by default)')
    parser.add_argument('--png', action='store_true', help='Generate PNG (already done by default)')
    
    args = parser.parse_args()
    
    result = generate_handwriting(
        writer_id=args.writer_id,
        target_text=args.text,
        output_path=args.output
    )