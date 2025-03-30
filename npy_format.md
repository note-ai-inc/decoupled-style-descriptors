# NPY File Format for Handwriting Data

This document describes the format of the NPY files used to store handwriting data.

## File Structure

Each NPY file contains a numpy array with the following structure:

```python
data = np.array([
    stroke_data,  # sentence_level_raw_stroke: numpy array of shape (N, 3)
    stroke_data,  # sentence_level_stroke_in: same as raw_stroke
    stroke_data,  # sentence_level_stroke_out: same as raw_stroke
    term_data,    # sentence_level_term: numpy array of shape (N,)
    char_data,    # sentence_level_char: numpy array of shape (N,)
    
    [stroke_data],  # word_level_raw_stroke: list containing stroke_data
    [stroke_data],  # word_level_stroke_in: same as raw_stroke
    [stroke_data],  # word_level_stroke_out: same as raw_stroke
    [term_data],    # word_level_term: list containing term_data
    [char_data],    # word_level_char: list containing char_data
    
    [[stroke_data]],  # segment_level_raw_stroke: nested list containing stroke_data
    [[stroke_data]],  # segment_level_stroke_in: same as raw_stroke
    [[stroke_data]],  # segment_level_stroke_out: same as raw_stroke
    [[term_data]],    # segment_level_term: nested list containing term_data
    [[char_data]],    # segment_level_char: nested list containing char_data
    
    {}  # metadata: empty dictionary
], dtype=object)
```

## Data Components

### Stroke Data (stroke_data)
- Shape: (N, 3) where N is the number of points
- Each row contains [x, y, pen_state]
- x, y: normalized coordinates (typically scaled to fit in a 5x5 box)
- pen_state: 1.0 for pen down, 0.0 for pen up

### Term Data (term_data)
- Shape: (N,) where N is the number of points
- Contains 1.0 for all points
- Used to mark the end of terms

### Character Data (char_data)
- Shape: (N,) where N is the number of points
- Contains character indices for each point
- Character indices are mapped as follows:
  - Space: 0
  - Lowercase letters a-z: 1-26
  - Punctuation marks: 27-58
  - Numbers 0-9: 59-68
  - Newline: 69

## Coordinate Normalization

Coordinates are normalized to fit within a 5x5 box while maintaining aspect ratio:
1. Find min and max coordinates
2. Calculate scale factors for x and y
3. Use the smaller scale to maintain aspect ratio
4. Apply scaling to all coordinates

## Pen State Handling

Pen states are determined by:
1. Pen down (1.0) at the start of each stroke
2. Pen up (0.0) when:
   - Distance between consecutive points is large (> 30 pixels)
   - At the end of each stroke
   - Between characters

## File Organization

Files are organized in the following structure:
```
data/
  writers/
    {writer_id}/
      {sample_id}.npy
```

Where:
- writer_id: unique identifier for each writer
- sample_id: unique identifier for each handwriting sample 