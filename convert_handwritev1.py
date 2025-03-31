import os
import argparse
import json
import numpy as np
import pickle
from helper import process_dataset

def create_writer_directory(writer_id):
    """Create directory for a writer if it doesn't exist."""
    dir_path = f'./data/raw_strokes/{writer_id}'
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path

def process_json_file(json_path, writer_id, sample_id, resample):
    """Process a JSON file and save it in the format expected by preprocess_dataset."""
    # Read JSON file
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Extract data
    text = data['text']
    strokes = data['strokes']
    character_labels = data['character_labels']
    preprocess_dir = 'writers'
    data_dir = './data'
    
    # Convert strokes to numpy array
    points = []
    for stroke in strokes:
        points.extend([[float(x), float(y), float(p)] for x, y, p in stroke])
    points = np.asarray(points)  # Convert list to numpy array
    
    process_dataset(data_dir, writer_id, sample_id, text, points, character_labels, preprocess_dir, 1)
    

def main():
    parser = argparse.ArgumentParser(description='Convert handwriting data using helper.preprocess_dataset')
    parser.add_argument('--input_dir', type=str, default='./data/raw_strokes',
                      help='Input directory containing raw stroke data')
    parser.add_argument('--resample', type=int, default=20,
                      help='Number of points to resample each stroke to')
    parser.add_argument('--pred_start', type=int, default=1,
                      help='Prediction start flag (0 or 1)')
    parser.add_argument('--writer_id', type=int, default=1,
                      help='Writer ID')
    
    args = parser.parse_args()
    
    # Check if input directory exists
    if not os.path.exists(args.input_dir):
        raise ValueError(f"Input directory {args.input_dir} does not exist")
    
    print(f"Processing handwriting data from {args.input_dir}")
    print(f"Resampling to {args.resample} points per stroke")
    print(f"Using pred_start={args.pred_start}")
    
    # Process each JSON file
    json_files = [f for f in os.listdir(args.input_dir) if f.endswith('.json')]
    for i, json_file in enumerate(json_files):
        json_path = os.path.join(args.input_dir, json_file)
        print(f"Processing {json_file}...")
        
        # Process file and save in expected format
        output_path = process_json_file(json_path, writer_id=args.writer_id, sample_id=i, resample=args.resample)
        print(f"Saved to {output_path}")
    
    print("Processing complete!")

if __name__ == '__main__':
    main() 