import numpy as np
import os
import json
from PIL import Image
import cv2
from typing import List, Tuple, Dict, Any
import argparse
from config.GlobalVariables import CHARACTERS

class HandwritingConverter:
    def __init__(self, output_dir: str = './data/writers'):
        self.output_dir = output_dir
        self.divider = 5.0  # Normalization factor for coordinates
        
    def create_writer_directory(self, writer_id: int) -> str:
        """Create directory for a writer if it doesn't exist."""
        writer_dir = os.path.join(self.output_dir, str(writer_id))
        os.makedirs(writer_dir, exist_ok=True)
        return writer_dir

    def normalize_coordinates(self, points: List[Tuple[float, float]]) -> np.ndarray:
        """Normalize coordinates to fit within a 5x5 box while maintaining aspect ratio."""
        if not points:
            return np.array([])
        
        # Convert points to numpy array
        points_array = np.array(points)
        
        # Find min and max coordinates
        min_coords = points_array.min(axis=0)
        max_coords = points_array.max(axis=0)
        
        # Calculate scale factors while maintaining aspect ratio
        scale_x = self.divider / (max_coords[0] - min_coords[0])
        scale_y = self.divider / (max_coords[1] - min_coords[1])
        scale = min(scale_x, scale_y)  # Use the smaller scale to maintain aspect ratio
        
        # Normalize coordinates
        normalized = (points_array - min_coords) * scale
        
        return normalized

    def create_stroke_data(self, points: np.ndarray, pen_states: List[bool]) -> np.ndarray:
        """Convert points and pen states into stroke data format."""
        stroke_data = np.zeros((len(points), 3))
        stroke_data[:, :2] = points
        # Convert pen states to 0 (pen up) or 1 (pen down)
        stroke_data[:, 2] = np.array([1.0 if state else 0.0 for state in pen_states])
        return stroke_data

    def process_handwriting_data(self,
                               points: List[Tuple[float, float]],
                               pen_states: List[int],
                               text: str,
                               writer_id: int,
                               sample_id: int = 0) -> None:
        """Process handwriting data and save to NPY file."""
        # Create writer directory
        writer_dir = self.create_writer_directory(writer_id)
        
        # Normalize coordinates
        normalized_points = self.normalize_coordinates(points)
        
        # Create stroke data
        stroke_data = np.column_stack((points, pen_states))
        # Ensure stroke_data_in and stroke_data_out have the same length as stroke_data
        if len(normalized_points) > 0:
            # For stroke_data_in, duplicate the first point
            stroke_data_in = np.column_stack((normalized_points, pen_states))
            
            # For stroke_data_out, duplicate the last point
            last_point = normalized_points[-1]
            last_pen = pen_states[-1]
            out_points = np.vstack([normalized_points[1:], last_point])
            out_pens = np.array(pen_states[1:] + [last_pen])
            stroke_data_out = np.column_stack((out_points, out_pens))
        else:
            stroke_data_in = stroke_data.copy()
            stroke_data_out = stroke_data.copy()
        
        # Convert text to character indices using GlobalVariables.CHARACTERS
        text_chars = list(text.lower())
        char_indices = [CHARACTERS.index(c) if c in CHARACTERS else CHARACTERS.index(' ') for c in text_chars]
        
        # Create term data (all ones)
        term_data = np.ones(len(points))
        
        # Create character data with term markers
        char_data = []
        points_per_char = len(points) // len(text_chars)
        for char_idx in char_indices:
            char_data.extend([char_idx] * points_per_char)
        # Pad if necessary
        while len(char_data) < len(points):
            char_data.append(char_indices[-1])
        
        # Convert char_data to numpy array
        char_data = np.array(char_data, dtype=np.int64)
        
        # Create the data structure according to the format
        data = np.array([
            stroke_data,  # sentence_level_raw_stroke
            stroke_data_in,  # sentence_level_stroke_in
            stroke_data_out,  # sentence_level_stroke_out
            term_data,    # sentence_level_term
            char_data,    # sentence_level_char
            
            [stroke_data],  # word_level_raw_stroke
            [stroke_data_in],  # word_level_stroke_in
            [stroke_data_out],  # word_level_stroke_out
            [term_data],    # word_level_term
            [char_data],    # word_level_char
            
            [[stroke_data]],  # segment_level_raw_stroke
            [[stroke_data_in]],  # segment_level_stroke_in
            [[stroke_data_out]],  # segment_level_stroke_out
            [[term_data]],    # segment_level_term
            [[char_data]],    # segment_level_char
            
            {}  # metadata
        ], dtype=object)
        
        # Save to NPY file
        output_path = os.path.join(writer_dir, f"{sample_id}.npy")
        np.save(output_path, data, allow_pickle=True)
        
        print(f"Saved stroke data to {output_path}")
        print(f"Shape: {stroke_data.shape}")
        print(f"Text: {text}")

    def process_image(self, 
                     image_path: str,
                     text: str,
                     writer_id: int,
                     sample_id: int = 0) -> None:
        """Process handwriting from an image file."""
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Threshold the image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours with more points
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        if not contours:
            raise ValueError("No handwriting found in the image")
        
        # Sort contours by x-coordinate to handle multiple characters
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])
        
        # Extract points and pen states
        points = []
        pen_states = []
        
        # Process each contour
        for i, contour in enumerate(contours):
            # Add pen up point at the start of each new character (except the first one)
            if i > 0:
                # Add a pen up point at the last position of previous character
                points.append(points[-1])
                pen_states.append(False)  # Pen up
                # Add a pen up point at the first position of current character
                x, y = contour[0][0]
                points.append((float(x), float(y)))
                pen_states.append(False)  # Pen up
            
            # Add first point of each contour
            x, y = contour[0][0]
            points.append((float(x), float(y)))
            pen_states.append(True)  # Pen down for first point
            
            # Process remaining points in the contour
            for j in range(1, len(contour)):
                x, y = contour[j][0]
                prev_x, prev_y = contour[j-1][0]
                
                # Calculate distance from previous point
                dist = np.sqrt((x - prev_x)**2 + (y - prev_y)**2)
                
                # If distance is very large, consider it a pen up event
                if dist > 30:  # Threshold for pen up
                    # Add pen up point at previous location
                    points.append((float(prev_x), float(prev_y)))
                    pen_states.append(False)  # Pen up
                    
                    # Add pen down point at new location
                    points.append((float(x), float(y)))
                    pen_states.append(True)  # Pen down
                else:
                    # Regular point
                    points.append((float(x), float(y)))
                    pen_states.append(True)  # Pen down
            
            # Add pen up point at the end of each contour
            points.append(points[-1])
            pen_states.append(False)  # Pen up
        
        # Process the data
        self.process_handwriting_data(points, pen_states, text, writer_id, sample_id)

    def process_json_strokes(self,
                           json_path: str,
                           writer_id: int,
                           sample_id: int = 0) -> None:
        """Process handwriting from a JSON file containing stroke data."""
        try:
            # Read the JSON file
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Extract strokes and text
            strokes = data.get('strokes', [])
            text = data.get('text', '')
            
            if not strokes:
                raise ValueError(f"No stroke data found in {json_path}")
            
            if not text:
                print(f"Warning: No text found in {json_path}, using empty string")
            
            # Convert strokes to points and pen states
            points = []
            pen_states = []
            
            # Process each stroke
            for stroke in strokes:
                if not stroke:
                    continue
                
                # Process all points in the stroke, including pen states
                for point in stroke:
                    x, y, pen_state = point
                    points.append((float(x), float(y)))
                    pen_states.append(pen_state)  # Use pen state directly from data
            
            if not points:
                raise ValueError(f"No valid points found in {json_path}")
            
            # Process the data
            if(len(points) > 0 and len(text)> 0):
                self.process_handwriting_data(points, pen_states, text, writer_id, sample_id)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file {json_path}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing {json_path}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Convert handwriting data to the model format')
    parser.add_argument('--input', type=str, required=True, help='Path to the input file (image or JSON)')
    parser.add_argument('--text', type=str, help='Text content of the handwriting (required for image input)')
    parser.add_argument('--writer_id', type=int, required=True, help='ID of the writer')
    parser.add_argument('--sample_id', type=int, default=0, help='ID of the sample (default: 0)')
    parser.add_argument('--output_dir', type=str, default='./data/writers', help='Output directory (default: ./data/writers)')
    
    args = parser.parse_args()
    
    converter = HandwritingConverter(output_dir=args.output_dir)
    
    # Check if input is JSON or image
    if args.input.endswith('.json'):
        if args.text:
            print("Warning: Text argument will be ignored for JSON input")
        converter.process_json_strokes(args.input, args.writer_id, args.sample_id)
    else:
        if not args.text:
            raise ValueError("Text argument is required for image input")
        converter.process_image(args.input, args.text, args.writer_id, args.sample_id)

if __name__ == '__main__':
    main() 