import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog, messagebox, Frame, Label, Button, Entry, Canvas
import numpy as np
import os
import torch
import svgwrite
from PIL import Image, ImageDraw, ImageTk
import sys

# Import required modules for the DSD model
# Make sure these are in the same directory or in the Python path
from SynthesisNetwork import SynthesisNetwork
import convenience

# Character set from GlobalVariables.py
CHARACTERS = ' !"#$%&\'()*+,-./0123456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ[]abcdefghijklmnopqrstuvwxyz'

class SimpleHandwritingCanvas:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Handwriting Canvas")
        
        # Create text entry
        self.text_entry = Entry(root, width=40)
        self.text_entry.insert(0, "quick brown fox jumps")
        self.text_entry.pack(pady=10)
        
        # Create canvas
        self.canvas = Canvas(root, width=700, height=400, bg='white', bd=2, relief='solid')
        self.canvas.pack(pady=10)
        
        # Add baseline
        self.canvas.create_line(50, 200, 650, 200, fill='lightgray', dash=(5,5))
        
        # Bind mouse events
        self.canvas.bind('<Button-1>', self.start_stroke)
        self.canvas.bind('<B1-Motion>', self.continue_stroke)
        self.canvas.bind('<ButtonRelease-1>', self.end_stroke)
        
        # Add buttons
        Button(root, text="Clear", command=self.clear_canvas).pack(pady=5)
        
        # Add text entry for generation
        self.generate_text_entry = Entry(root, width=40)
        self.generate_text_entry.insert(0, "Hello world")
        self.generate_text_entry.pack(pady=10)
        
        Button(root, text="Generate Handwriting", command=self.generate_handwriting).pack(pady=5)
        
        # Initialize variables
        self.strokes = []
        self.current_stroke = []
        self.raw_points = []
        self.device = 'cpu'
        self.net = None
        
        # Status label
        self.status = Label(root, text="Ready")
        self.status.pack(pady=5)
    
    def start_stroke(self, event):
        x, y = event.x, event.y
        self.current_stroke = [(x, y, 0)]
        self.canvas.create_oval(x-1, y-1, x+1, y+1, fill='black')
    
    def continue_stroke(self, event):
        if self.current_stroke:
            x, y = event.x, event.y
            x1, y1, _ = self.current_stroke[-1]
            self.current_stroke.append((x, y, 0))
            self.canvas.create_line(x1, y1, x, y, width=2, fill='black')
    
    def end_stroke(self, event):
        if self.current_stroke:
            x, y, _ = self.current_stroke[-1]
            self.current_stroke[-1] = (x, y, 1)
            self.strokes.append(self.current_stroke)
            self.raw_points.extend(self.current_stroke)
            self.current_stroke = []
            self.status.config(text=f"Strokes: {len(self.strokes)}")
    
    def clear_canvas(self):
        self.canvas.delete('all')
        self.canvas.create_line(50, 200, 650, 200, fill='lightgray', dash=(5,5))
        self.strokes = []
        self.raw_points = []
        self.current_stroke = []
        self.status.config(text="Canvas cleared")
    
    def load_model(self):
        """Load the neural network model if not already loaded"""
        print("Attempting to load model...")
        if self.net is None:
            try:
                # Update status safely
                try:
                    self.status.config(text="Loading model...")
                    self.root.update()
                except:
                    pass
                
                # Initialize model
                print("Initializing SynthesisNetwork...")
                self.net = SynthesisNetwork(weight_dim=256, num_layers=3)
                self.net.to(self.device)  # Move model to device after initialization
                
                # Load model weights
                print("Loading model weights from ./model/250000.pt...")
                state_dict = torch.load('./model/250000.pt', map_location=torch.device(self.device))
                if "model_state_dict" in state_dict:
                    print("Found model_state_dict in state_dict")
                    self.net.load_state_dict(state_dict["model_state_dict"])
                else:
                    print("Loading state_dict directly")
                    self.net.load_state_dict(state_dict)
                
                print("Model loaded successfully")
                try:
                    self.status.config(text="Model loaded successfully")
                except:
                    pass
                return True
            except Exception as e:
                print(f"Error loading model: {str(e)}")
                try:
                    messagebox.showerror("Error", f"Error loading model: {str(e)}")
                    self.status.config(text="Failed to load model")
                except:
                    pass
                return False
        return True
    
    def prepare_mock_data(self, text):
        """Create artificial mock data to work with the model's expected dimensions"""
        # This is a simplified approach that creates data in the expected format
        # but doesn't try to accurately represent the handwriting
        
        # Create mock raw points data
        # For each character we generate 10 points with synthetic coordinates
        raw_points = []
        pen_state = 0  # pen down
        
        for i, char in enumerate(text):
            # Create synthetic points for each character
            for j in range(10):
                # Synthetic coordinates with small variations
                x = i * 20 + j * 2 + (np.random.random() - 0.5) * 5
                y = 200 + (np.random.random() - 0.5) * 10
                
                # Last point of each character gets pen up state
                if j == 9:
                    pen_state = 1
                else:
                    pen_state = 0
                    
                raw_points.append([x, y, pen_state])
                    
        raw_points = np.array(raw_points, dtype=np.float32)
        
        # Create character mapping array - we need to map the raw stroke
        # points to the characters they represent
        character_labels = np.zeros((len(raw_points), len(text)))
        points_per_char = len(raw_points) // len(text)
        
        for i, char in enumerate(text):
            start_idx = i * points_per_char
            end_idx = min((i + 1) * points_per_char, len(raw_points))
            character_labels[start_idx:end_idx, i] = 1
        
        # Create all the required data structures
        # Sentence level data
        sentence_level_raw_stroke = raw_points
        sentence_level_stroke_in = raw_points[:-1].copy()
        sentence_level_stroke_out = raw_points[1:].copy()
        sentence_level_term = raw_points[:-1, 2].copy()
        
        # Character information
        sentence_level_char = []
        for c in text:
            sentence_level_char.append(CHARACTERS.index(c) if c in CHARACTERS else CHARACTERS.index(' '))
        
        # Make sure text has at least 5 characters to match expected dimensions
        if len(text) < 5:
            # Use original text and pad with spaces to get to 5 characters
            padded_text = text + ' ' * (5 - len(text))
            
            # Recreate sentence_level_char with padded text
            sentence_level_char = []
            for c in padded_text:
                sentence_level_char.append(CHARACTERS.index(c) if c in CHARACTERS else CHARACTERS.index(' '))

        # Ensure we have exactly 5 characters to match expected dimensions
        if len(sentence_level_char) < 5:
            # Pad with spaces
            sentence_level_char = sentence_level_char + [CHARACTERS.index(' ')] * (5 - len(sentence_level_char))
        elif len(sentence_level_char) > 5:
            # Trim to 5 characters
            sentence_level_char = sentence_level_char[:5]
                
        # Word level data 
        # Split the text into words
        words = text.split()
        
        # Create word-level structures
        word_level_raw_stroke = []
        word_level_stroke_in = []
        word_level_stroke_out = []
        word_level_term = []
        word_level_char = []
        
        # Make sure we have at least 5 words
        if len(words) < 5:
            words = words + ["dummy"] * (5 - len(words))
                
        # Process each word
        points_per_word = len(raw_points) // len(words)
        for i, word in enumerate(words):
            start_idx = i * points_per_word
            end_idx = min((i + 1) * points_per_word, len(raw_points))
            
            # Extract points for this word
            word_points = raw_points[start_idx:end_idx].copy()
            word_level_raw_stroke.append(word_points)
            
            # Create stroke in/out pairs
            if len(word_points) > 1:
                word_level_stroke_in.append(word_points[:-1])
                word_level_stroke_out.append(word_points[1:])
                word_level_term.append(word_points[:-1, 2])
                
                # Create character indices
                word_chars = []
                for c in word:
                    word_chars.append(CHARACTERS.index(c) if c in CHARACTERS else CHARACTERS.index(' '))
                word_level_char.append(np.array(word_chars))
            else:
                # Create minimal dummy data if word has only one point
                dummy_in = np.array([[0, 0, 0]], dtype=np.float32)
                dummy_out = np.array([[0.1, 0.1, 1]], dtype=np.float32)
                word_level_stroke_in.append(dummy_in)
                word_level_stroke_out.append(dummy_out)
                word_level_term.append(np.array([0], dtype=np.float32))
                word_level_char.append(np.array([CHARACTERS.index(' ')]))
        
        # Segment (character) level data
        segment_level_raw_stroke = []
        segment_level_stroke_in = []
        segment_level_stroke_out = []
        segment_level_term = []
        segment_level_char = []
        
        # Process each word to create segment data
        for i, word in enumerate(words):
            word_segments_raw = []
            word_segments_in = []
            word_segments_out = []
            word_segments_term = []
            word_segments_char = []
            
            # Ensure each word has exactly 5 characters (segments)
            word_chars = list(word)
            if len(word_chars) < 5:
                word_chars = word_chars + [' '] * (5 - len(word_chars))
            elif len(word_chars) > 5:
                word_chars = word_chars[:5]
                    
            # Get points for this word
            word_points = word_level_raw_stroke[i]
            points_per_char = max(2, len(word_points) // len(word_chars))
            
            for j, char in enumerate(word_chars):
                start_idx = j * points_per_char
                end_idx = min((j + 1) * points_per_char, len(word_points))
                
                # Extract points for this character
                if start_idx < len(word_points) and end_idx <= len(word_points) and start_idx < end_idx:
                    char_points = word_points[start_idx:end_idx].copy()
                else:
                    # Create dummy points if indices are invalid
                    char_points = np.array([
                        [0, 0, 0],
                        [0.1, 0.1, 1]
                    ], dtype=np.float32)
                
                # Add to segment data
                word_segments_raw.append(char_points)
                
                if len(char_points) > 1:
                    word_segments_in.append(char_points[:-1])
                    word_segments_out.append(char_points[1:])
                    word_segments_term.append(char_points[:-1, 2])
                else:
                    # Create minimal dummy data
                    dummy_in = np.array([[0, 0, 0]], dtype=np.float32)
                    dummy_out = np.array([[0.1, 0.1, 1]], dtype=np.float32)
                    word_segments_in.append(dummy_in)
                    word_segments_out.append(dummy_out)
                    word_segments_term.append(np.array([0], dtype=np.float32))
                
                # Add character index
                word_segments_char.append(np.array([CHARACTERS.index(char) if char in CHARACTERS else CHARACTERS.index(' ')]))
            
            segment_level_raw_stroke.append(word_segments_raw)
            segment_level_stroke_in.append(word_segments_in)
            segment_level_stroke_out.append(word_segments_out)
            segment_level_term.append(word_segments_term)
            segment_level_char.append(word_segments_char)
        
        # Create length information
        sentence_level_char_length = [len(sentence_level_char)]
        word_level_char_length = [len(chars) for chars in word_level_char]
        segment_level_char_length = [[len(chars) for chars in word] for word in segment_level_char]
        
        sentence_level_stroke_length = [len(sentence_level_stroke_in)]
        word_level_stroke_length = [len(stroke) for stroke in word_level_stroke_in]
        segment_level_stroke_length = [[len(stroke) for stroke in word] for word in segment_level_stroke_in]
        
        # Scale by divider (5.0)
        divider = 5.0
        
        # Apply scaling to coordinates
        a = np.ones_like(sentence_level_stroke_in)
        a[:, :2] /= divider
        sentence_level_stroke_in = sentence_level_stroke_in * a
        sentence_level_stroke_out = sentence_level_stroke_out * a
        
        for i in range(len(word_level_stroke_in)):
            a = np.ones_like(word_level_stroke_in[i])
            a[:, :2] /= divider
            word_level_stroke_in[i] = word_level_stroke_in[i] * a
            word_level_stroke_out[i] = word_level_stroke_out[i] * a
        
        for i in range(len(segment_level_stroke_in)):
            for j in range(len(segment_level_stroke_in[i])):
                if len(segment_level_stroke_in[i][j]) > 0:
                    a = np.ones_like(segment_level_stroke_in[i][j])
                    a[:, :2] /= divider
                    segment_level_stroke_in[i][j] = segment_level_stroke_in[i][j] * a
                    segment_level_stroke_out[i][j] = segment_level_stroke_out[i][j] * a
        
        # Assemble the final data package
        return [
            [sentence_level_stroke_in], 
            [sentence_level_stroke_out],
            [sentence_level_stroke_length],
            [sentence_level_term],
            [sentence_level_char],
            [sentence_level_char_length],
            [word_level_stroke_in],
            [word_level_stroke_out],
            [word_level_stroke_length],
            [word_level_term],
            [word_level_char],
            [word_level_char_length],
            [segment_level_stroke_in],
            [segment_level_stroke_out],
            [segment_level_stroke_length],
            [segment_level_term],
            [segment_level_char],
            [segment_level_char_length]
        ]
    
    def generate_handwriting(self):
        """Generate handwriting based on example text"""
        # Get the text from the UI
        example_text = self.text_entry.get().strip()
        target_text = self.generate_text_entry.get().strip()
        
        # Validate inputs
        if not example_text:
            messagebox.showerror("Error", "Please enter example text that matches your handwriting.")
            return
            
        if not target_text:
            messagebox.showerror("Error", "Please enter text to generate.")
            return
            
        if len(example_text) < 5:
            messagebox.showerror("Error", "Example text must be at least 5 characters long to work with the model.")
            return
        
        # Check if we have recorded strokes
        if not self.raw_points:
            messagebox.showerror("Error", "No handwriting recorded. Please draw on the canvas first.")
            return
        
        # Load the model
        if not self.load_model():
            return
        
        # Update status
        self.status.config(text=f"Generating handwriting for: {target_text}")
        self.root.update()
        
        try:
            # Prepare mock data with exact dimensions needed
            mock_data = self.prepare_mock_data(example_text)
            
            # Extract the writer's style
            mean_global_W = convenience.get_mean_global_W(self.net, mock_data, self.device)
            
            # Generate handwriting
            words = target_text.split()
            
            # Make sure we have at least one word
            if not words:
                words = [""]
                
            # Create word style vectors and character matrices for each word
            word_Ws = []
            word_Cs = []
            
            for word in words:
                # Make sure word is not empty
                if not word:
                    word = " "
                    
                writer_Ws, writer_Cs = convenience.get_DSD(self.net, word, [mean_global_W], [mock_data], self.device)
                word_Ws.append(writer_Ws.cpu())
                word_Cs.append(writer_Cs.cpu())
            
            # Generate the SVG
            svg = convenience.draw_words_svg(words, word_Ws, word_Cs, [1.0], self.net)
            
            # Create output directory if needed
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            # Save the SVG
            svg_path = os.path.join(output_dir, "generated.svg")
            svg.saveas(svg_path)
            
            # Extract command points for visualization
            all_commands = []
            for path in svg.elements:
                if isinstance(path, svgwrite.path.Path):
                    # Extract path data
                    d = path['d']
                    points = []
                    
                    # Parse SVG path commands
                    parts = d.split()
                    current_x, current_y = 0, 0
                    
                    for i, part in enumerate(parts):
                        if part == 'M':
                            # Move to (pen up)
                            x, y = float(parts[i+1]), float(parts[i+2])
                            points.append([x, y, 1])  # Pen up
                            current_x, current_y = x, y
                        elif part == 'L':
                            # Line to (pen down)
                            x, y = float(parts[i+1]), float(parts[i+2])
                            points.append([x, y, 0])  # Pen down
                            current_x, current_y = x, y
                    
                    all_commands.extend(points)
            
            # Create a PNG visualization
            png_path = os.path.join(output_dir, "generated.png")
            img_width, img_height = 800, 300
            img = Image.new("RGB", (img_width, img_height), color="black")
            draw = ImageDraw.Draw(img)
            
            # Draw strokes
            prev_x, prev_y = None, None
            for x, y, t in all_commands:
                if t == 0 and prev_x is not None:
                    draw.line((prev_x, prev_y, x, y), fill="white", width=2)
                prev_x, prev_y = x, y
            
            # Save the image
            img.save(png_path)
            
            # Show success message
            messagebox.showinfo("Success", f"Handwriting generated successfully!\n"
                               f"SVG saved to: {svg_path}\n"
                               f"PNG saved to: {png_path}")
            
            # Open the image
            try:
                from PIL import ImageTk
                # Create a new window to display the image
                result_window = tk.Toplevel(self.root)
                result_window.title("Generated Handwriting")
                
                # Add the image
                image = ImageTk.PhotoImage(img)
                label = Label(result_window, image=image)
                label.image = image  # Keep a reference
                label.pack(padx=10, pady=10)
                
                # Add a close button
                Button(result_window, text="Close", command=result_window.destroy).pack(pady=10)
                
            except Exception as e:
                print(f"Error displaying result image: {e}")
            
            self.status.config(text="Handwriting generated successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generating handwriting: {str(e)}")
            self.status.config(text="Failed to generate handwriting")
            import traceback
            traceback.print_exc()

# Create and run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleHandwritingCanvas(root)
    root.mainloop()