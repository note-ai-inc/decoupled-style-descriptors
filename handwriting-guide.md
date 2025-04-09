# Handwriting Data Conversion and Text Generation Guide

This guide provides step-by-step instructions for converting handwriting images to data and generating text outputs using the handwriting synthesis model.

## Prerequisites

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Prepare your handwriting samples:
   - Create clear, high-quality images of your handwriting
   - Save them as PNG files
   - Create a text file containing the corresponding text for each image

## Step 1: Prepare Input Files

1. Capture handwriting data using `capture_multiple`:
```bash
python3 capture_multiple.py
```
   - This will save data in a specific format that can be converted using `convert_handwritingv1.py` under data/raw_samples
   - When writing characters, ensure each character is written with exactly one stroke
   - We don't have a good way to capture character-level data with multiple strokes
   - Follow the on-screen instructions to write each character

2. Run `python convert_handwritingv1.py --input data/raw_samples --writer_id your_id`, this will convert your sample data to npy files and Place your handwriting images in the writer/your_id


## Step 2: Convert Handwriting Images to Data

1. Clear previous results (if any):
```bash
rm -rf data/writers/200/* results/*
```

2. Convert all handwriting samples:
```
    python3 convert_handwritingv1.py \
        --input data/raw_samples \
        --writer_id 200 \
```

## Step 3: Generate Text Outputs

### Generate a Single Image

To generate text in your handwriting style:
```bash
python3 interpolation.py \
    --interpolate writer \
    --output image \
    --writer_ids 200 80 \
    --target_word "Your text here" \
    --blend_weights 1.0 0.0
```

Parameters:
- `--interpolate writer`: Use writer style interpolation
- `--output image`: Generate a single image
- `--writer_ids 200 80`: Use your style (200) and another style (80)
- `--target_word`: The text you want to generate
- `--blend_weights 1.0 0.0`: Use only your style (no blending)

### Generate a Video Interpolation

To create a video showing the transition between styles:
```bash
python3 interpolation.py \
    --interpolate writer \
    --output video \
    --writer_ids 200 80 \
    --target_word "Your text here"
```

This will:
- Generate frames showing the transition
- Combine frames into a video
- Save as `results/your_text_blend_video.mov`

## Output Files

1. Data files:
   - Location: `data/writers/200/`
   - Format: `.npy` files (see npy-format.md for details)
   - One file per sample (0.npy through 9.npy)

2. Generated images:
   - Location: `results/`
   - Format: PNG files
   - Naming: `blend_200+80.png` for single images
   - Naming: `your_text_blend_video.mov` for videos

## Tips for Better Results

1. Provide diverse samples:
   - Include different lengths of text
   - Use various characters and words
   - Include different writing styles (cursive, print, etc.)

2. Image quality:
   - Ensure good lighting
   - Use high contrast (black on white)
   - Avoid shadows or noise
   - Keep the background clean

3. Text content:
   - Match text exactly with what's in the images
   - Include punctuation and spaces
   - Use consistent formatting

4. Number of samples:
   - More samples generally yield better results
   - Aim for at least 5-10 samples
   - Include samples with the characters you want to generate

## Troubleshooting

1. If generation quality is poor:
   - Add more handwriting samples
   - Ensure text matches exactly
   - Check image quality
   - Try different blend weights

2. If conversion fails:
   - Check image format (must be PNG)
   - Verify text file format
   - Ensure proper file permissions
   - Check for sufficient disk space

3. If video generation fails:
   - Check FFmpeg installation
   - Verify frame generation
   - Ensure sufficient disk space
   - Check file permissions 