import argparse
import json

from config.GlobalVariables import *
import math
import torch
from scipy import stats
import numpy as np
from PIL import Image, ImageDraw
import os
import pickle

# copied and modified from helper.py
def reformat_raw_data(raw_data, pred_start):
    if pred_start == 1:
        tmp = np.concatenate([[[0, 500, 0]], raw_data], 0)
        tmp = tmp[1:] - tmp[:-1]
        tmp[1:, 2] = raw_data[:-1, 2]
        tmp = np.concatenate([[[0, 0, 0]], tmp], 0)
    else:
        tmp = np.concatenate([raw_data[0:1], raw_data])
        tmp = tmp[1:] - tmp[:-1]
        tmp[0,2] = 0
        tmp[1:,2] = raw_data[:-1, 2]
        tmp = np.concatenate([[[0, 0, 0]], tmp * np.array([1, 1, 1])], 0) # scale delta encoded value by 10

    return tmp[:-1], tmp[1:]

def process_dataset(data_dir, writer_id, sentence_id, sentence_text, raw_points, character_labels, preprocess_dir, pred_start=1):
    print(f"Processing dataset for writer_id: {writer_id}, sentence_id: {sentence_id}")
    sentence_raw_points = raw_points
    sentence_raw_points[:, 0] -= sentence_raw_points[0, 0]
    sentence_stroke_in, sentence_stroke_out = reformat_raw_data(sentence_raw_points, pred_start=pred_start)

    split_char_ids = [i for i, c in enumerate(sentence_text) if c == ' ']

    sentence_char = [CHARACTERS.find(c) for c in sentence_text]
    # Create sentence_level_char array with same length as raw_points
    # Each element contains the index of the corresponding character in CHARACTERS
    sentence_level_char = np.zeros(len(raw_points), dtype=int)
    
    # Iterate through character labels to assign character indices
    for i in range(len(character_labels)):
        # Find which character this point belongs to
        char_idx = np.argmax(character_labels[i])
        if char_idx < len(sentence_char):
            # Assign the character index from CHARACTERS
            sentence_level_char[i] = sentence_char[char_idx]


    sentence_term = []
    cid = 0
    for i in range(len(character_labels) - 1):
        if character_labels[i + 1, cid] != 1:
            if np.argmax(character_labels[i + 1]) >= cid:
                cid += 1
                sentence_term.append(1)
            else:
                sentence_term.append(0)
        else:
            sentence_term.append(0)
    sentence_term.append(1)
    sentence_term = np.asarray(sentence_term)

    assert (len(sentence_term) == len(character_labels))

    word_level_raw_stroke = []
    word_level_stroke_in = []
    word_level_stroke_out = []
    word_level_char = []
    word_level_term = []

    segment_level_raw_stroke = []
    segment_level_stroke_in = []
    segment_level_stroke_out = []
    segment_level_char = []
    segment_level_term = []

    character_level_raw_stroke = []
    character_level_stroke_in = []
    character_level_stroke_out = []
    character_level_char = []
    character_level_term = []

    word_start_id = 0
    char_start_id = 0
    point_start_id = 0

    for i, c in enumerate(sentence_text):
        if c != ' ':
            character_raw_points = raw_points[character_labels[:, i] > 0]
            if character_raw_points.shape[0] == 0:
                print(f"Warning: No points found for character {c} at index {i}")
                continue
            character_level_raw_stroke.append(character_raw_points)
            character_stroke_in, character_stroke_out = reformat_raw_data(character_raw_points, pred_start=pred_start)
            character_level_stroke_in.append(character_stroke_in)
            character_level_stroke_out.append(character_stroke_out)
            term = np.zeros([len(character_raw_points)])
            term[-1] = 1
            character_level_term.append(term)
            # Create character_char array with the same length as character_raw_points
            # Each element contains the index of the character in CHARACTERS
            character_char = np.ones(len(character_raw_points), dtype=int) * CHARACTERS.find(c)
            character_level_char.append(character_char)
            # point_start_id += len(character_raw_points)
            # char_start_id += 1
            print(f"char {c} index {i} total {len(raw_points)} charpoints {len(character_raw_points)} term: {term.shape} character_char: {character_char.shape}")

        if i in split_char_ids:
            word = sentence_text[word_start_id:i]

            word_labels = np.zeros(len(character_labels))
            for j in range(word_start_id, i):
                word_labels += character_labels[:, j]

            print(f"word_labels for {word}: {word_labels}")
            word_raw_points = raw_points[word_labels > 0]
            word_term = np.zeros(len(word_raw_points))
            
            # word_term = sentence_term[word_labels > 0]
            word_term[:-1] = 1
        
            word_level_raw_stroke.append(np.asarray(word_raw_points))
            word_stroke_in, word_stroke_out = reformat_raw_data(word_raw_points, pred_start=pred_start)
            word_level_stroke_in.append(word_stroke_in)
            word_level_stroke_out.append(word_stroke_out)
            word_level_term.append(word_term)
            # Create word_char array with character indices for each point in word_raw_points
            word_char = np.zeros(len(word_raw_points), dtype=int)
            char_index = 0
            for j in range(len(word_term)):
                if(char_idx>len(word)):
                    print(f"Warning: char_idx {char_idx} is greater than word {word} j: {j} word_term: {word_term.shape}")
                    break
                char_index_value = CHARACTERS.find(word[char_index])
                word_char[j] = char_index_value
                if word_term[j] == 1:  # If this is the end of a character
                    char_index += 1

            word_level_char.append(word_char)
            word_start_id=i+1

            print(f"word_char for {word}: {word_char.shape} word_term: {word_term.shape} word_raw_points: {len(word_raw_points)}")

            segment_level_raw_stroke.append(character_level_raw_stroke)
            segment_level_stroke_in.append(character_level_stroke_in)
            segment_level_stroke_out.append(character_level_stroke_out)
            segment_level_char.append(character_level_char)
            segment_level_term.append(character_level_term)
            character_level_raw_stroke = []
            character_level_stroke_in = []
            character_level_stroke_out = []
            character_level_char = []
            character_level_term = []

    word = sentence_text[word_start_id:]
    word_labels = np.zeros(len(character_labels))
    for j in range(word_start_id, len(sentence_text)):
        word_labels += character_labels[:, j]
    word_raw_points = raw_points[word_labels > 0]
    if word_raw_points.shape[0] == 0:
        print(f"Warning: No points found for word {word} at index {word_start_id} sentence {sentence_text} word_labels {word_labels}")
    word_raw_points[:, 0] -= word_raw_points[0, 0]
    word_term = sentence_term[word_labels > 0]
    word_term[0] = 0
    word_level_raw_stroke.append(word_raw_points)
    word_stroke_in, word_stroke_out = reformat_raw_data(word_raw_points, pred_start=pred_start)
    word_level_stroke_in.append(word_stroke_in)
    word_level_stroke_out.append(word_stroke_out)
    word_level_term.append(word_term)
    word_level_char.append([CHARACTERS.find(c) for c in word])
    segment_level_raw_stroke.append(character_level_raw_stroke)
    segment_level_stroke_in.append(character_level_stroke_in)
    segment_level_stroke_out.append(character_level_stroke_out)
    segment_level_char.append(character_level_char)
    segment_level_term.append(character_level_term)

    if not os.path.exists(f'{data_dir}/{preprocess_dir}/{writer_id}'):
        os.mkdir(f'{data_dir}/{preprocess_dir}/{writer_id}')

    with open(f'{data_dir}/{preprocess_dir}/{writer_id}/{sentence_id}.npy', 'wb') as f:
        # Save as .npy file instead of using pickle
        # Create the array with all data
        data_array = np.array([
            sentence_raw_points,
            sentence_stroke_in, 
            sentence_stroke_out, 
            sentence_term,
            sentence_level_char,
            word_level_raw_stroke, 
            word_level_stroke_in,
            word_level_stroke_out,
            word_level_term,
            word_level_char,
            segment_level_raw_stroke,
            segment_level_stroke_in, 
            segment_level_stroke_out, 
            segment_level_term, 
            segment_level_char, 
            {}
        ], dtype=object)
        
        # Save using numpy's save function to preserve array structure
        np.save(f, data_array, allow_pickle=True)

def gaussian_2d(x1, x2, mu1, mu2, s1, s2, rho):
    norm1 = x1 - mu1
    norm2 = x2 - mu2
    s1s2 = s1 * s2
    z = (norm1 / s1) ** 2 + (norm2 / s2) ** 2 - 2 * rho * norm1 * norm2 / s1s2
    numerator = torch.exp(-z / (2 * (1 - rho ** 2)))
    denominator = 2 * math.pi * s1s2 * torch.sqrt(1 - rho ** 2)
    gaussian = numerator / denominator
    return gaussian


def get_minimax(stroke_results):
    minimas = []
    maximas = []
    for stroke in stroke_results:
        for i, [x, y] in enumerate(stroke):
            if i == 0:
                prev_x, prev_y = x, y
            if i == len(stroke) - 1:
                if prev_y <= y:
                    maximas.append([x, y])
                if prev_y >= y:
                    minimas.append([x, y])
                break
            else:
                next_x, next_y = stroke[i + 1]
                if prev_y <= y and y >= next_y:
                    maximas.append([x, y])
                if prev_y >= y and y <= next_y:
                    minimas.append([x, y])

    minimas = np.asarray(minimas)
    maximas = np.asarray(maximas)
    return minimas, maximas


def get_slope(minimas, maximas):
    minima_slope, minima_intercept, _, _, _ = stats.linregress(minimas[:, 0], minimas[:, 1])
    maxima_slope, maxima_intercept, _, _, _ = stats.linregress(maximas[:, 0], maximas[:, 1])
    min_se = []
    max_se = []
    for [x, y] in minimas:
        min_ny = minima_slope * x + minima_intercept
        min_se.append(abs(min_ny - y))
    for [x, y] in maximas:
        max_ny = maxima_slope * x + maxima_intercept
        max_se.append(abs(max_ny - y))
    min_se, max_se = np.asarray(min_se), np.asarray(max_se)
    new_minimas = minimas[min_se < np.mean(min_se)]
    new_maximas = maximas[max_se < np.mean(max_se)]
    if len(new_minimas) > 5:
        minima_slope, minima_intercept, _, _, _ = stats.linregress(new_minimas[:, 0], new_minimas[:, 1])
    if len(new_maximas) > 5:
        maxima_slope, maxima_intercept, _, _, _ = stats.linregress(new_maximas[:, 0], new_maximas[:, 1])

    return minima_slope, minima_intercept, maxima_slope, maxima_intercept


def draw_commands(commands):
    im = Image.fromarray(np.zeros([160, 750]))
    dr = ImageDraw.Draw(im)

    px, py = 50, 100
    for i, [dx, dy, t] in enumerate(commands):
        x = px + dx * 5
        y = py + dy * 5
        if t == 0:
            dr.line((px, py, x, y), 255, 1)
        px, py = x, y

    return im


def draw_points(raw_points, character_labels):
    [w, h, _] = np.max(raw_points, 0)
    im = Image.new("RGB", [int(w) + 100, int(h) + 100])
    dr = ImageDraw.Draw(im)

    colors = np.random.randint(0, 255, (len(character_labels[0]), 3))

    for i, [x, y, t] in enumerate(raw_points):
        if i > 0:
            if pt == 0:
                dr.line((px, py, x, y), tuple(colors[np.argmax(character_labels[i])]), 3)
        px, py, pt = x, y, t

    return im

# End of copied and modified from helper.py
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
    character_labels = np.asarray(data['character_labels'])  # Convert to numpy array
    preprocess_dir = 'writers'
    data_dir = './data'
    
    # Convert strokes to numpy array
    points = []
    for stroke in strokes:
        points.extend([[float(x), float(y), float(p)] for x, y, p in stroke])
    points = np.asarray(points)  # Convert list to numpy array
    
    process_dataset(data_dir, writer_id, sample_id, text, points, character_labels, preprocess_dir, 0)
    

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
    print(f"Using pred_start={args.pred_start}")
    
    # Process each JSON file
    # Check if there are any JSON files in the directory
    print(f"Processing {args.input_dir}")
    json_files = sorted([f for f in os.listdir(args.input_dir) if f.endswith('.json')])
    if not json_files:
        print(f"No JSON files found in {args.input_dir}")
    else:
        for i, json_file in enumerate(json_files):
            json_path = os.path.join(args.input_dir, json_file)
            print(f"Processing {json_file}...")
            
            # Process file and save in expected format
            process_json_file(json_path, writer_id=args.writer_id, sample_id=i, resample=args.resample)
    print("Processing complete!")

if __name__ == '__main__':
    main() 