import numpy as np

CHARACTERS = ' !"#$%&\'()*+,-./0123456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ[]abcdefghijklmnopqrstuvwxyz'

def get_char_from_idx(idx):
    """Convert character index back to character."""
    if 0 <= idx < len(CHARACTERS):
        return CHARACTERS[idx]
    return '?'

def preprocess_data(char_data, term_data, datadir='./data/writers'):
    """Preprocess data according to DataLoader's rules."""
    # Remove trailing points where term != 1.0
    while True:
        if len(term_data) == 0:
            break
        if term_data[-1] != 1.0:
            char_data = char_data[:-1]
            term_data = term_data[:-1]
        else:
            break
    
    # Handle different data directories
    if datadir in ['./data/DW_writers', './data/VALID_DW_writers']:
        char_data = char_data[1:]
        term_data = term_data[1:]
    
    return char_data, term_data

def extract_text_from_npy(file_path):
    """Extract text from an NPY file containing handwriting data."""
    print(f"\nAnalyzing {file_path}")
    
    # Load the data
    data = np.load(file_path, allow_pickle=True)
    
    # Print data structure
    print("\nData structure:")
    for i in range(len(data)):
        if isinstance(data[i], np.ndarray):
            print(f"Element {i}: numpy array with shape {data[i].shape}")
        elif isinstance(data[i], list):
            print(f"Element {i}: list with length {len(data[i])}")
            if len(data[i]) > 0:
                first_item = data[i][0]
                if isinstance(first_item, np.ndarray):
                    print(f"  First item is numpy array with shape {first_item.shape}")
                elif isinstance(first_item, list):
                    print(f"  First item is list with length {len(first_item)}")
        else:
            print(f"Element {i}: {type(data[i])}")
    
    # Get sentence level data
    sentence_level_char = data[4]  # character indices
    sentence_level_term = data[3]  # term array
    
    # Print raw data
    print("\nRaw data:")
    print("Term array (first 20):", sentence_level_term[:20])
    print("Character array (first 20):", sentence_level_char[:20])
    
    # Find positions where term == 1
    term_positions = np.where(sentence_level_term == 1)[0]
    print("\nPositions where term == 1:", term_positions[:20])
    
    # Get characters at those positions
    chars = sentence_level_char[term_positions]
    print("Characters at term positions:", chars[:20])
    
    # Convert to text
    text = ''.join(get_char_from_idx(idx) for idx in chars)
    print("\nExtracted text:", text)

if __name__ == "__main__":
    print("Analyzing training data:")
    for i in range(2):  # Just look at first 2 training samples
        extract_text_from_npy(f'data/writers/1/{i}.npy')
    
    print("\nAnalyzing converted data:")
    extract_text_from_npy('data/writers/200/0.npy') 