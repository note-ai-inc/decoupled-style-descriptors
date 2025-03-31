import cv2
import numpy as np
import os
import json
from datetime import datetime
import argparse

class HandwritingCapture:
    def __init__(self, width=800, height=300):
        self.width = width
        self.height = height
        self.window_name = 'Handwriting Capture'
        self.current_stroke = []
        self.strokes = []
        self.drawing = False
        self.last_point = None
        self.threshold = 30  # Distance threshold for new stroke
        
        # Create output directory for raw strokes
        self.raw_strokes_dir = 'data/raw_strokes'
        os.makedirs(self.raw_strokes_dir, exist_ok=True)
        
        # Initialize the window
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        # Create a white background
        self.image = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255
        self.display_image = self.image.copy()
    
    def mouse_callback(self, event, x, y, flags, param):
        # Handle drawing
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.current_stroke = [(x, y, 0)]  # pen_state = 0 for stroke points
            self.last_point = (x, y)
            
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            # Calculate distance from last point
            dist = np.sqrt((x - self.last_point[0])**2 + (y - self.last_point[1])**2)
            
            # If distance is too large, start a new stroke
            if dist > self.threshold:
                if self.current_stroke:
                    # Add pen up point at the end of current stroke
                    self.current_stroke.append((self.current_stroke[-1][0], self.current_stroke[-1][1], 1))
                    self.strokes.append(self.current_stroke)
                self.current_stroke = [(x, y, 0)]  # pen_state = 0 for new stroke
                self.last_point = (x, y)
            else:
                self.current_stroke.append((x, y, 0))  # pen_state = 0 for stroke points
                self.last_point = (x, y)
            
            # Update display
            self.display_image = self.image.copy()
            self.draw_strokes(self.display_image)
            cv2.imshow(self.window_name, self.display_image)
            
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            if self.current_stroke:
                # Add pen up point at the end of current stroke
                self.current_stroke.append((self.current_stroke[-1][0], self.current_stroke[-1][1], 1))
                self.strokes.append(self.current_stroke)
                self.current_stroke = []
            self.last_point = None
            
            # Update display
            self.display_image = self.image.copy()
            self.draw_strokes(self.display_image)
            cv2.imshow(self.window_name, self.display_image)
    
    def draw_strokes(self, img):
        # Draw completed strokes
        for stroke in self.strokes:
            if len(stroke) > 1:
                for i in range(len(stroke) - 1):
                    # Only draw lines between points where pen is down (pen_state = 0)
                    if stroke[i][2] == 0 and stroke[i+1][2] == 0:
                        cv2.line(img, 
                                (stroke[i][0], stroke[i][1]),
                                (stroke[i + 1][0], stroke[i + 1][1]), 
                                (0, 0, 0), 2)
        
        # Draw current stroke
        if len(self.current_stroke) > 1:
            for i in range(len(self.current_stroke) - 1):
                # Only draw lines between points where pen is down (pen_state = 0)
                if self.current_stroke[i][2] == 0 and self.current_stroke[i+1][2] == 0:
                    cv2.line(img,
                            (self.current_stroke[i][0], self.current_stroke[i][1]),
                            (self.current_stroke[i + 1][0], self.current_stroke[i + 1][1]),
                            (0, 0, 0), 2)
    
    def save_strokes(self, text):
        """Save the captured strokes and text to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sample_{len(os.listdir(self.raw_strokes_dir))}.json"
        filepath = os.path.join(self.raw_strokes_dir, filename)
        
        data = {
            'text': text,
            'timestamp': timestamp,
            'strokes': self.strokes,
        }
        
        # Calculate the total number of points across all strokes
        total_points = sum(len(stroke) for stroke in self.strokes)
        
        # Initialize the character mapping array
        # Each row represents a point, each column represents a character
        character_mapping = np.zeros((total_points, len(text)))
        
        point_index = 0
        current_char_index = 0
        
        for stroke in self.strokes:
            for i, point in enumerate(stroke):
                # For each point in the stroke
                x, y, pen_state = point
                
                # Map this point to the current character
                if current_char_index < len(text):
                    character_mapping[point_index, current_char_index] = 1
                
                # If pen is up (pen_state = 1), move to the next character
                if (text[current_char_index] == ' ' or pen_state == 1) and i > 0 and current_char_index < len(text):
                    current_char_index += 1
                
                point_index += 1
        
        # Add the character mapping to the data
        data['character_labels'] = character_mapping.tolist()

        with open(filepath, 'w') as f:
            json.dump(data, f)
        
        print(f"Saved strokes and text to {filepath}")
        return filepath
    
    def clear_canvas(self):
        """Clear the canvas and reset strokes."""
        self.strokes = []
        self.current_stroke = []
        self.display_image = self.image.copy()
        self.draw_strokes(self.display_image)
        cv2.imshow(self.window_name, self.display_image)
    
    def capture(self):
        """Capture handwriting with text input."""
        print("\nEnter text to write:")
        text = input()
        
        print("\nDraw your handwriting on the canvas.")
        print("Press 's' to save.")
        print("Press 'c' to clear and start over.")
        print("Press 'n' to continue to next sample.")
        print("Press 'q' to quit.")
        
        while True:
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):  # Quit
                break
            elif key == ord('c'):  # Clear
                self.clear_canvas()
                print("\nEnter text to write:")
                text = input()
            elif key == ord('s'):  # Save
                if text and self.strokes:
                    self.save_strokes(text)
                    self.clear_canvas()
                    print("\nEnter text to write:")
                    text = input()
            elif key == ord('n'):  # Next sample
                if text and self.strokes:
                    self.save_strokes(text)
                self.clear_canvas()
                break
            
            # Update display
            self.display_image = self.image.copy()
            self.draw_strokes(self.display_image)
            cv2.imshow(self.window_name, self.display_image)
        
        cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description='Capture handwriting samples')
    parser.add_argument('--width', type=int, default=800, help='Width of the capture window')
    parser.add_argument('--height', type=int, default=300, help='Height of the capture window')
    parser.add_argument('--threshold', type=int, default=30, help='Distance threshold for new stroke')
    
    args = parser.parse_args()
    
    capture = HandwritingCapture(width=args.width, height=args.height)
    capture.threshold = args.threshold
    
    while True:
        capture.capture()
        
        # Ask if user wants to capture more
        response = input("\nCapture another sample? (y/n): ")
        if response.lower() != 'y':
            break
    
    print("\nAll samples captured. Use convert_handwriting.py to convert to npy format.")

if __name__ == "__main__":
    main() 