import os
from convert_handwriting import HandwritingConverter

def main():
    input_dir = 'data/raw_strokes'
    output_dir = 'data/writers'
    writer_id = 200
    
    # Create converter
    converter = HandwritingConverter(output_dir=output_dir)
    
    # Process each sample file
    for i in range(10):
        json_path = os.path.join(input_dir, f'sample_{i}.json')
        if os.path.exists(json_path):
            print(f"Processing {json_path}...")
            converter.process_json_strokes(json_path, writer_id, i)

if __name__ == '__main__':
    main() 