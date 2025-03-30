import numpy as np

def analyze_npy_file(file_path):
    """Analyze the structure of an NPY file containing handwriting data."""
    print(f"\nAnalyzing {file_path}")
    
    # Load the data
    data = np.load(file_path, allow_pickle=True)
    print(f"Data structure length: {len(data)}")
    
    # Analyze each element
    for i, element in enumerate(data):
        print(f"\nElement {i}:")
        if isinstance(element, np.ndarray):
            print(f"Type: numpy array")
            print(f"Shape: {element.shape}")
            if len(element.shape) > 1 and element.shape[1] == 3:  # If it's stroke data
                print(f"Pen states: {np.unique(element[:, 2])}")
                print(f"First 5 points: {element[:5]}")
            elif len(element.shape) == 1:  # If it's a 1D array
                print(f"Values: {element[:5]}")
        elif isinstance(element, list):
            print(f"Type: list")
            print(f"Length: {len(element)}")
            if len(element) > 0:
                if isinstance(element[0], np.ndarray):
                    print(f"First element shape: {element[0].shape}")
                else:
                    print(f"First element type: {type(element[0])}")
        else:
            print(f"Type: {type(element)}")

if __name__ == "__main__":
    # Analyze training data
    analyze_npy_file('data/writers/1/0.npy')
    
    # Analyze our converted data
    analyze_npy_file('data/writers/200/0.npy') 