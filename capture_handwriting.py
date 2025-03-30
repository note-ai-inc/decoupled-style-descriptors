import cv2
import numpy as np
from PIL import Image
import argparse
from convert_handwriting import HandwritingConverter

class HandwritingCanvas:
    def __init__(self, width=800, height=400):
        self.width = width
        self.height = height
        self.canvas = np.ones((height, width), dtype=np.uint8) * 255  # White background
        self.drawing = False
        self.last_point = None
        self.points = []
        self.pen_states = []
        
        # Create window and set mouse callback
        cv2.namedWindow('Handwriting Canvas')
        cv2.setMouseCallback('Handwriting Canvas', self.mouse_callback)
        
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.last_point = (x, y)
            self.points.append((float(x), float(y)))
            self.pen_states.append(True)  # Pen down
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                # Draw line from last point to current point
                cv2.line(self.canvas, self.last_point, (x, y), 0, 2)
                self.last_point = (x, y)
                self.points.append((float(x), float(y)))
                self.pen_states.append(True)  # Pen down
                
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.last_point = None
            # Add pen up point
            if self.points:
                self.points.append(self.points[-1])
                self.pen_states.append(False)
    
    def run(self):
        print("Draw your handwriting on the canvas.")
        print("Press 's' to save and exit.")
        print("Press 'c' to clear the canvas.")
        
        while True:
            # Show the canvas
            cv2.imshow('Handwriting Canvas', self.canvas)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('s'):  # Save and exit
                break
            elif key == ord('c'):  # Clear canvas
                self.canvas = np.ones((self.height, self.width), dtype=np.uint8) * 255
                self.points = []
                self.pen_states = []
        
        cv2.destroyAllWindows()
        return self.points, self.pen_states

def main():
    parser = argparse.ArgumentParser(description='Capture handwriting from canvas')
    parser.add_argument('--text', type=str, required=True, help='The text being written')
    parser.add_argument('--writer_id', type=int, required=True, help='ID for the writer')
    parser.add_argument('--sample_id', type=int, default=0, help='ID for the sample (default: 0)')
    parser.add_argument('--width', type=int, default=800, help='Canvas width (default: 800)')
    parser.add_argument('--height', type=int, default=400, help='Canvas height (default: 400)')
    
    args = parser.parse_args()
    
    # Create and run the canvas
    canvas = HandwritingCanvas(args.width, args.height)
    points, pen_states = canvas.run()
    
    if points:
        # Convert the captured data
        converter = HandwritingConverter()
        converter.process_handwriting_data(points, pen_states, args.text, args.writer_id, args.sample_id)
        print(f"Saved handwriting data for text: {args.text}")
    else:
        print("No handwriting data captured.")

if __name__ == '__main__':
    main() 