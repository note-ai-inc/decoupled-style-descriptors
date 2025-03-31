import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import xml.etree.ElementTree as ET
from xml.dom import minidom
import numpy as np
import time
from datetime import datetime

class HandwritingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Handwriting Data Collection")
        self.root.geometry("1200x800")
        
        # Set writer ID
        self.writer_id_input = simpledialog.askstring("Writer ID", "Enter your writer ID (2-3 chars, e.g. 'a01'):", 
                                                initialvalue="a01")
        if not self.writer_id_input:
            # Default ID format like "a01"
            self.writer_id_input = "w" + datetime.now().strftime("%d")
        
        # Normalize writer ID to maintain format
        if len(self.writer_id_input) > 3:
            self.writer_id_input = self.writer_id_input[:3]
        elif len(self.writer_id_input) < 3:
            self.writer_id_input = self.writer_id_input.ljust(3, '0')
        
        # Create a numeric writer ID for the XML (original requires an integer)
        self.numeric_writer_id = self.convert_to_numeric_id(self.writer_id_input)
            
        # Initialize variables
        self.strokes = []  # List to store all strokes
        self.current_stroke = []  # Current stroke being drawn
        self.is_drawing = False
        self.stroke_timestamps = []  # To store timestamp data for each stroke
        self.current_timestamps = []  # Timestamps for current stroke
        self.stroke_color = "black"  # Default stroke color
        
        # Track line-by-line input
        self.line_entries = []  # Store text entries for each line
        self.line_strokes = []  # Store strokes for each line
        self.line_timestamps = []  # Store timestamps for each line
        self.current_line_index = 0  # Track which line is currently being drawn
        
        # Create main frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create top control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Text input for full transcription
        ttk.Label(control_frame, text="Full Transcription:").pack(side=tk.LEFT, padx=5)
        self.full_text_entry = scrolledtext.ScrolledText(control_frame, width=50, height=5, wrap=tk.WORD)
        self.full_text_entry.pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(control_frame, text="Parse Lines", command=self.parse_lines).pack(side=tk.LEFT, padx=5)
        
        # Line-by-line frame
        self.lines_frame = ttk.LabelFrame(main_frame, text="Lines")
        self.lines_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Current line indicator
        self.current_line_frame = ttk.Frame(self.lines_frame)
        self.current_line_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(self.current_line_frame, text="Current Line:").pack(side=tk.LEFT, padx=5)
        self.current_line_var = tk.StringVar(value="No lines added yet")
        self.current_line_label = ttk.Label(self.current_line_frame, textvariable=self.current_line_var, font=("Arial", 12, "bold"))
        self.current_line_label.pack(side=tk.LEFT, padx=5)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.lines_frame)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(nav_frame, text="Previous Line", command=self.previous_line).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Next Line", command=self.next_line).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Save Current Line", command=self.save_current_line).pack(side=tk.LEFT, padx=5)
        
        # Control panel for options
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Writing style selection
        ttk.Label(options_frame, text="Style:").pack(side=tk.LEFT, padx=5)
        self.style_combo = ttk.Combobox(options_frame, values=["u", "w", "x", "z"], width=5)
        self.style_combo.current(0)
        self.style_combo.pack(side=tk.LEFT, padx=5)
        
        # Color selection
        ttk.Label(options_frame, text="Color:").pack(side=tk.LEFT, padx=5)
        self.color_combo = ttk.Combobox(options_frame, values=["black", "blue", "red", "green"], width=10)
        self.color_combo.current(0)
        self.color_combo.pack(side=tk.LEFT, padx=5)
        self.color_combo.bind("<<ComboboxSelected>>", self.change_color)
        
        # Canvas size settings
        ttk.Label(options_frame, text="Canvas Size:").pack(side=tk.LEFT, padx=5)
        self.canvas_size_combo = ttk.Combobox(options_frame, values=["Small (600x400)", "Medium (800x600)", "Large (1000x800)"], width=15)
        self.canvas_size_combo.current(0)
        self.canvas_size_combo.pack(side=tk.LEFT, padx=5)
        self.canvas_size_combo.bind("<<ComboboxSelected>>", self.change_canvas_size)
        
        # Buttons
        ttk.Button(options_frame, text="Clear Line", command=self.clear_canvas).pack(side=tk.LEFT, padx=5)
        ttk.Button(options_frame, text="Save All Lines", command=self.save_all_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(options_frame, text="Exit", command=root.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Create canvas frame with scrollbars
        self.canvas_frame = ttk.LabelFrame(main_frame, text="Draw Here")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollbars
        h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create canvas - SMALLER SIZE to avoid large offsets
        self.canvas_width = 600
        self.canvas_height = 400
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", width=self.canvas_width, height=self.canvas_height,
                               xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)
        self.canvas.config(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        
        # Bind mouse events to canvas
        self.canvas.bind("<Button-1>", self.start_stroke)
        self.canvas.bind("<B1-Motion>", self.continue_stroke)
        self.canvas.bind("<ButtonRelease-1>", self.end_stroke)
        
        # Output directory setup
        self.setup_directories()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set(f"Writer ID: {self.writer_id_input} (Numeric: {self.numeric_writer_id}) | Style: {self.style_combo.get()} | Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create info panel on the right
        info_frame = ttk.LabelFrame(main_frame, text="Information")
        info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        info_text = (
            "Instructions:\n\n"
            "1. Paste or type the full text in the top box\n"
            "2. Click 'Parse Lines' to split into separate lines\n"
            "3. Navigate between lines and write each one\n"
            "4. Save each line after writing\n"
            "5. When finished with all lines, click 'Save All Lines'\n\n"
            "IMPORTANT: Keep your strokes small\n"
            "and centered to pass validation!\n\n"
            f"Your writer ID ({self.writer_id_input}) has been\n"
            f"converted to numeric ID ({self.numeric_writer_id})\n"
            "for compatibility with the dataset format.\n\n"
            "Each line will have its own strokes file.\n"
            "Files are saved in:\n"
            "- ascii: text transcriptions\n"
            "- lineStrokes: individual stroke data\n"
            "- original: combined metadata by style"
        )
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, wraplength=250).pack(padx=10, pady=10)

    def convert_to_numeric_id(self, writer_id):
        """Convert alphanumeric writer ID to numeric only for XML compatibility"""
        # Simple conversion: just use a number between 1-100
        try:
            # First try to parse as integer
            return int(writer_id)
        except ValueError:
            # If it contains letters, use a simple conversion:
            # Calculate numeric value (first char as base 36 value)
            if writer_id[0].isalpha():
                # Maps 'a' to 1, 'b' to 2, etc.
                numeric_val = ord(writer_id[0].lower()) - ord('a') + 1
            else:
                numeric_val = int(writer_id[0])
                
            # Add remaining digits if they exist and are numeric
            for i in range(1, len(writer_id)):
                if writer_id[i].isdigit():
                    numeric_val = numeric_val * 10 + int(writer_id[i])
                    
            return max(1, min(100, numeric_val))  # Clamp between 1-100

    def parse_lines(self):
        """Parse the full text into individual lines"""
        full_text = self.full_text_entry.get("1.0", tk.END).strip()
        if not full_text:
            messagebox.showerror("Error", "Please enter the text to parse!")
            return
            
        # Split by newlines and filter out empty lines
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        if not lines:
            messagebox.showerror("Error", "No valid lines found in the text!")
            return
            
        # Store the lines
        self.line_entries = lines
        
        # Initialize line data structures
        self.line_strokes = [[] for _ in range(len(lines))]
        self.line_timestamps = [[] for _ in range(len(lines))]
        
        # Set current line to first line
        self.current_line_index = 0
        self.update_current_line_display()
        
        # Clear canvas for first line
        self.clear_canvas()
        
        messagebox.showinfo("Success", f"Parsed {len(lines)} lines. Start drawing the first line.")

    def update_current_line_display(self):
        """Update the display to show the current line"""
        if not self.line_entries:
            self.current_line_var.set("No lines added yet")
            return
            
        line_num = self.current_line_index + 1
        total_lines = len(self.line_entries)
        current_line = self.line_entries[self.current_line_index]
        
        self.current_line_var.set(f"Line {line_num}/{total_lines}: {current_line}")
        
        # Update status bar
        self.status_var.set(f"Writer ID: {self.writer_id_input} | Line {line_num}/{total_lines} | Style: {self.style_combo.get()}")

    def previous_line(self):
        """Go to the previous line"""
        if not self.line_entries:
            messagebox.showinfo("Info", "No lines to navigate!")
            return
            
        # Save current strokes for this line
        self.save_current_line_data()
        
        # Move to previous line
        if self.current_line_index > 0:
            self.current_line_index -= 1
            self.update_current_line_display()
            self.load_line_data()
        else:
            messagebox.showinfo("Info", "Already at the first line!")

    def next_line(self):
        """Go to the next line"""
        if not self.line_entries:
            messagebox.showinfo("Info", "No lines to navigate!")
            return
            
        # Save current strokes for this line
        self.save_current_line_data()
        
        # Move to next line
        if self.current_line_index < len(self.line_entries) - 1:
            self.current_line_index += 1
            self.update_current_line_display()
            self.load_line_data()
        else:
            messagebox.showinfo("Info", "Already at the last line!")

    def save_current_line_data(self):
        """Save stroke data for the current line internally"""
        if not self.line_entries:
            return
            
        # Store current strokes and timestamps
        self.line_strokes[self.current_line_index] = self.strokes.copy()
        self.line_timestamps[self.current_line_index] = self.stroke_timestamps.copy()

    def load_line_data(self):
        """Load stroke data for the current line"""
        if not self.line_entries:
            return
            
        # Clear canvas
        self.canvas.delete("stroke")
        
        # Load previously saved strokes for this line
        self.strokes = self.line_strokes[self.current_line_index].copy()
        self.stroke_timestamps = self.line_timestamps[self.current_line_index].copy()
        
        # Redraw strokes
        for stroke, timestamp in zip(self.strokes, self.stroke_timestamps):
            color = timestamp['color']
            for i in range(1, len(stroke)):
                x1, y1 = stroke[i-1]
                x2, y2 = stroke[i]
                self.canvas.create_line(x1, y1, x2, y2, 
                                      width=2, fill=color, 
                                      capstyle=tk.ROUND, smooth=tk.TRUE,
                                      tags="stroke")

    def save_current_line(self):
        """Save the current line's stroke data"""
        if not self.line_entries:
            messagebox.showerror("Error", "No lines to save!")
            return
            
        if not self.strokes:
            messagebox.showerror("Error", "No handwriting data for this line!")
            return
            
        # Save current line data internally
        self.save_current_line_data()
        
        messagebox.showinfo("Success", f"Line {self.current_line_index + 1} saved!")

    def change_canvas_size(self, event):
        """Change the canvas size based on selection"""
        size_str = self.canvas_size_combo.get()
        if "Small" in size_str:
            self.canvas_width, self.canvas_height = 600, 400
        elif "Medium" in size_str:
            self.canvas_width, self.canvas_height = 800, 600
        elif "Large" in size_str:
            self.canvas_width, self.canvas_height = 1000, 800
        
        # Update canvas size
        self.canvas.config(width=self.canvas_width, height=self.canvas_height)
        self.canvas.config(scrollregion=(0, 0, self.canvas_width, self.canvas_height))

    def setup_directories(self):
        """Create the necessary directory structure for saving data"""
        writer_dir = self.writer_id_input
        
        # Create base directories
        self.base_dir = os.path.join("data", "rawCustom")
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Create specific directories
        self.dirs = {
            "ascii": os.path.join(self.base_dir, "ascii", writer_dir),
            "lineStrokes": os.path.join(self.base_dir, "lineStrokes", writer_dir),
            "original": os.path.join(self.base_dir, "original", writer_dir)
        }
        
        for d in self.dirs.values():
            os.makedirs(d, exist_ok=True)
        
        # Create sample counter
        self.sample_counter = 0
        while True:
            sample_dir = f"{writer_dir}-{self.sample_counter:03d}"
            ascii_sample_path = os.path.join(self.base_dir, "ascii", writer_dir, sample_dir)
            if not os.path.exists(ascii_sample_path):
                break
            self.sample_counter += 1

    def change_color(self, event):
        """Change the stroke color"""
        self.stroke_color = self.color_combo.get()
        self.status_var.set(f"Writer ID: {self.writer_id_input} | Style: {self.style_combo.get()} | Color: {self.stroke_color}")

    def start_stroke(self, event):
        """Start a new stroke"""
        self.is_drawing = True
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.current_stroke = [(x, y)]
        self.current_timestamps = [time.time()]
        self.prev_x, self.prev_y = x, y

    def continue_stroke(self, event):
        """Continue drawing the current stroke"""
        if self.is_drawing:
            x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            self.canvas.create_line(self.prev_x, self.prev_y, x, y, 
                                   width=2, fill=self.stroke_color, 
                                   capstyle=tk.ROUND, smooth=tk.TRUE,
                                   tags="stroke")
            self.current_stroke.append((x, y))
            self.current_timestamps.append(time.time())
            self.prev_x, self.prev_y = x, y

    def end_stroke(self, event):
        """End the current stroke"""
        if self.is_drawing:
            self.is_drawing = False
            if len(self.current_stroke) > 1:  # Only add stroke if it has more than one point
                self.strokes.append(self.current_stroke)
                self.stroke_timestamps.append({
                    'color': self.stroke_color,
                    'start_time': self.current_timestamps[0],
                    'end_time': self.current_timestamps[-1],
                    'points': self.current_timestamps
                })
                
                # Update status with line info if available
                if self.line_entries:
                    line_num = self.current_line_index + 1
                    total_lines = len(self.line_entries)
                    self.status_var.set(f"Writer ID: {self.writer_id_input} | Line {line_num}/{total_lines} | Strokes: {len(self.strokes)}")
                else:
                    self.status_var.set(f"Writer ID: {self.writer_id_input} | Style: {self.style_combo.get()} | Strokes: {len(self.strokes)}")

    def clear_canvas(self):
        """Clear the canvas and all strokes for the current line"""
        self.canvas.delete("stroke")
        self.strokes = []
        self.stroke_timestamps = []
        
        # Update status
        if self.line_entries:
            line_num = self.current_line_index + 1
            total_lines = len(self.line_entries)
            self.status_var.set(f"Writer ID: {self.writer_id_input} | Line {line_num}/{total_lines} | Canvas cleared")
        else:
            self.status_var.set(f"Writer ID: {self.writer_id_input} | Style: {self.style_combo.get()} | Canvas cleared")

    def save_all_data(self):
        """Save all lines of handwriting data in the required format"""
        if not self.line_entries:
            messagebox.showerror("Error", "No lines to save!")
            return
            
        # Save current line data first
        self.save_current_line_data()
        
        # Check if all lines have strokes
        empty_lines = [i for i, strokes in enumerate(self.line_strokes) if not strokes]
        if empty_lines:
            result = messagebox.askyesno("Warning", 
                f"Lines {[i+1 for i in empty_lines]} have no handwriting data. Continue anyway?")
            if not result:
                return
        
        # Get the style letter
        style_letter = self.style_combo.get()
        
        # Create sample ID
        writer_dir = self.writer_id_input
        sample_id = f"{writer_dir}-{self.sample_counter:03d}"
        sample_dir = sample_id
        
        try:
            # Create all the needed subdirectories
            ascii_sample_dir = os.path.join(self.dirs["ascii"], sample_dir)
            os.makedirs(ascii_sample_dir, exist_ok=True)
            
            line_strokes_sample_dir = os.path.join(self.dirs["lineStrokes"], sample_dir)
            os.makedirs(line_strokes_sample_dir, exist_ok=True)
            
            original_sample_dir = os.path.join(self.dirs["original"], sample_dir)
            os.makedirs(original_sample_dir, exist_ok=True)
            
            # Save ASCII transcription with full text
            full_text = "\n".join(self.line_entries)
            self.save_ascii(sample_id, full_text, style_letter, ascii_sample_dir)
            
            # Save each line's strokes separately
            all_normalized_strokes = []
            for i, (line_strokes, line_timestamps) in enumerate(zip(self.line_strokes, self.line_timestamps)):
                if not line_strokes:
                    continue  # Skip empty lines
                
                # Normalize strokes for this line
                normalized_strokes = self.normalize_strokes(line_strokes)
                all_normalized_strokes.extend(normalized_strokes)
                
                # Check if normalized strokes pass validation criteria
                max_norm = self.check_stroke_norms(normalized_strokes)
                if max_norm > 60:
                    messagebox.showwarning("Warning", 
                        f"Line {i+1} has stroke offsets (max: {max_norm:.2f}) larger than the validation threshold (60).\n"
                        "This may cause validation issues. Consider redrawing with smaller strokes.")
                
                # Save line stroke XML with sequence number
                line_file_id = f"{sample_id}{style_letter}-{i+1:02d}"
                self.save_stroke_xml(line_file_id, style_letter, normalized_strokes, line_timestamps, line_strokes_sample_dir)
            
            # Save combined original XML for all lines with the style letter
            self.save_original_xml(sample_id, style_letter, all_normalized_strokes, original_sample_dir)
            
            # Increment counter for next sample
            self.sample_counter += 1
            
            messagebox.showinfo("Success", f"All lines saved successfully as sample {sample_id} with style '{style_letter}'")
            
            # Reset for a new set of lines
            self.line_entries = []
            self.line_strokes = []
            self.line_timestamps = []
            self.current_line_index = 0
            self.full_text_entry.delete("1.0", tk.END)
            self.clear_canvas()
            self.current_line_var.set("No lines added yet")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")

    def normalize_strokes(self, strokes_to_normalize=None):
        """Normalize strokes to fit within acceptable ranges for validation"""
        # Use provided strokes or current strokes
        strokes_to_process = strokes_to_normalize if strokes_to_normalize is not None else self.strokes
        
        if not strokes_to_process:
            return []
            
        # Clone strokes
        normalized_strokes = []
        
        # Find min/max values
        all_points = [point for stroke in strokes_to_process for point in stroke]
        x_vals = [p[0] for p in all_points]
        y_vals = [p[1] for p in all_points]
        
        min_x, max_x = min(x_vals), max(x_vals)
        min_y, max_y = min(y_vals), max(y_vals)
        
        # Calculate center and scale
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Normalize to have a max range of 50 (to stay below the 60 validation threshold)
        x_range = max(1, max_x - min_x)  # Avoid division by zero
        y_range = max(1, max_y - min_y)
        scale = min(40 / x_range, 40 / y_range)
        
        # Create normalized strokes
        for stroke in strokes_to_process:
            new_stroke = []
            for x, y in stroke:
                # Center then scale
                new_x = (x - center_x) * scale + 250  # Center in a 500x500 space
                new_y = (y - center_y) * scale + 250
                new_stroke.append((new_x, new_y))
            normalized_strokes.append(new_stroke)
        
        return normalized_strokes
        
    def check_stroke_norms(self, normalized_strokes):
        """Calculate maximum stroke offset norm to check against validation"""
        all_offsets = []
        
        for stroke in normalized_strokes:
            for i in range(1, len(stroke)):
                offset_x = stroke[i][0] - stroke[i-1][0]
                offset_y = stroke[i][1] - stroke[i-1][1]
                all_offsets.append((offset_x, offset_y))
        
        if not all_offsets:
            return 0
            
        # Calculate norms of offsets
        norms = [np.sqrt(x*x + y*y) for x, y in all_offsets]
        return max(norms)

    def save_stroke_xml(self, file_id, style_letter, normalized_strokes=None, timestamps=None, save_dir=None):
        """Save stroke data as XML in WhiteboardCaptureSession format"""
        # Use normalized strokes and timestamps if provided
        strokes_to_save = normalized_strokes if normalized_strokes is not None else self.normalize_strokes()
        timestamps_to_save = timestamps if timestamps is not None else self.stroke_timestamps
        
        if len(strokes_to_save) != len(timestamps_to_save):
            # If timestamps are not matching, create dummy timestamps
            timestamps_to_save = []
            start_time = time.time()
            for _ in strokes_to_save:
                end_time = start_time + 1.0
                timestamps_to_save.append({
                    'color': 'black',
                    'start_time': start_time,
                    'end_time': end_time,
                    'points': [start_time + 0.1 * i for i in range(10)]
                })
                start_time = end_time + 0.5
        
        # Create line stroke file path
        line_stroke_path = os.path.join(save_dir, f"{file_id}.xml")
        
        # Create XML structure similar to the WhiteboardCaptureSession format
        root = ET.Element("WhiteboardCaptureSession")
        
        # Add whiteboard description - match format from example
        desc = ET.SubElement(root, "WhiteboardDescription")
        ET.SubElement(desc, "SensorLocation", corner="top_left")
        ET.SubElement(desc, "DiagonallyOppositeCoords", x="512", y="376")
        ET.SubElement(desc, "VerticallyOppositeCoords", x="96", y="376")
        ET.SubElement(desc, "HorizontallyOppositeCoords", x="512", y="78")
        
        # Add strokes
        stroke_set = ET.SubElement(root, "StrokeSet")
        
        for i, (stroke, timestamp) in enumerate(zip(strokes_to_save, timestamps_to_save)):
            # Format times to match the sample format (truncate to 2 decimal places)
            start_time = f"{timestamp['start_time']:.2f}"
            end_time = f"{timestamp['end_time']:.2f}"
            
            stroke_elem = ET.SubElement(stroke_set, "Stroke", 
                                        colour=timestamp['color'],
                                        start_time=start_time, 
                                        end_time=end_time)
            
            for j, (x, y) in enumerate(stroke):
                # Get point time or use interpolated time if points don't match
                if j < len(timestamp['points']):
                    point_time = f"{timestamp['points'][j]:.2f}"
                else:
                    # Interpolate time if points don't match
                    ratio = j / max(1, len(stroke) - 1)
                    point_time = f"{timestamp['start_time'] + ratio * (timestamp['end_time'] - timestamp['start_time']):.2f}"
                
                ET.SubElement(stroke_elem, "Point", 
                              x=str(int(x)), 
                              y=str(int(y)), 
                              time=point_time)

        # Add XML declaration and proper encoding to match the format
        with open(line_stroke_path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
            f.write(ET.tostring(root, encoding='unicode'))
            
        print(f"Saved line stroke file: {line_stroke_path}")

    def save_ascii(self, sample_id, text, style_letter, save_dir=None):
        """Save ASCII transcription"""
        ascii_filename = f"{sample_id}{style_letter}.txt"
        
        # Use the provided save directory or default to the main ascii directory
        if save_dir:
            ascii_path = os.path.join(save_dir, ascii_filename)
        else:
            ascii_path = os.path.join(self.dirs["ascii"], sample_id, ascii_filename)
            
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(ascii_path), exist_ok=True)
        
        # Add OCR section before CSR
        with open(ascii_path, "w") as f:
            f.write("OCR:\n\n")
            f.write(text + "\n\n")
            f.write("CSR:\n\n")
            f.write(text)
            
        print(f"Saved ASCII file: {ascii_path}")

    def save_original_xml(self, sample_id, style_letter, normalized_strokes=None, save_dir=None):
        """Save original XML with metadata - combines all strokes by style"""
        # Use normalized strokes if provided
        strokes_to_save = normalized_strokes if normalized_strokes is not None else self.normalize_strokes()
        
        # Create the filename - this follows the format in the tree diagram
        # where original files are named like "strokesz.xml" based on style letter
        original_filename = f"strokes{style_letter}.xml"
        
        # Use the provided save directory or default to the main original directory
        if save_dir:
            original_path = os.path.join(save_dir, original_filename)
        else:
            original_path = os.path.join(self.dirs["original"], original_filename)
        
        # Create XML structure
        root = ET.Element("WhiteboardCaptureSession")
        
        # Add whiteboard description - match format from example with smaller values
        desc = ET.SubElement(root, "WhiteboardDescription")
        ET.SubElement(desc, "SensorLocation", corner="top_left")
        ET.SubElement(desc, "DiagonallyOppositeCoords", x="512", y="376")
        ET.SubElement(desc, "VerticallyOppositeCoords", x="96", y="376")
        ET.SubElement(desc, "HorizontallyOppositeCoords", x="512", y="78")
        
        # Add general section with NUMERIC writer ID
        general = ET.SubElement(root, "General")
        rec_info = ET.SubElement(general, "RecordingInformation")
        rec_info.set("writerID", str(self.numeric_writer_id))  # Use numeric ID, not the alphanumeric one
        
        # Add stroke set (similar to line strokes)
        stroke_set = ET.SubElement(root, "StrokeSet")
        
        # Collect all strokes from all lines for this style
        all_strokes = []
        all_timestamps = []
        
        # If we have line data, use that
        if self.line_strokes:
            for line_idx, (line_strokes, line_timestamps) in enumerate(zip(self.line_strokes, self.line_timestamps)):
                if not line_strokes:
                    continue
                
                # Normalize if not already normalized
                if normalized_strokes is None:
                    norm_strokes = self.normalize_strokes(line_strokes)
                    all_strokes.extend(norm_strokes)
                    all_timestamps.extend(line_timestamps)
                else:
                    # If normalized_strokes is provided, we've already processed the data
                    all_strokes = strokes_to_save
                    all_timestamps = self.stroke_timestamps
                    break
        else:
            # If no line data, just use current strokes
            all_strokes = strokes_to_save
            all_timestamps = self.stroke_timestamps
        
        # If timestamps don't match strokes (can happen when merging), create dummy timestamps
        if len(all_strokes) != len(all_timestamps):
            all_timestamps = []
            start_time = time.time()
            for _ in all_strokes:
                end_time = start_time + 1.0
                all_timestamps.append({
                    'color': 'black',
                    'start_time': start_time,
                    'end_time': end_time,
                    'points': [start_time + 0.1 * i for i in range(10)]
                })
                start_time = end_time + 0.5
        
        # Add all strokes to the XML
        for i, (stroke, timestamp) in enumerate(zip(all_strokes, all_timestamps)):
            # Format times to match the sample format
            start_time = f"{timestamp['start_time']:.2f}"
            end_time = f"{timestamp['end_time']:.2f}"
            
            stroke_elem = ET.SubElement(stroke_set, "Stroke", 
                                        colour=timestamp['color'],
                                        start_time=start_time, 
                                        end_time=end_time)
            
            for j, (x, y) in enumerate(stroke):
                # Get point time or use interpolated time if points don't match
                if j < len(timestamp['points']):
                    point_time = f"{timestamp['points'][j]:.2f}"
                else:
                    # Interpolate time if points don't match
                    ratio = j / max(1, len(stroke) - 1)
                    point_time = f"{timestamp['start_time'] + ratio * (timestamp['end_time'] - timestamp['start_time']):.2f}"
                
                ET.SubElement(stroke_elem, "Point", 
                              x=str(int(x)), 
                              y=str(int(y)), 
                              time=point_time)
        
        # Add XML declaration and proper encoding to match the format
        with open(original_path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
            f.write(ET.tostring(root, encoding='unicode'))
            
        print(f"Saved original XML file: {original_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = HandwritingApp(root)
    root.mainloop()