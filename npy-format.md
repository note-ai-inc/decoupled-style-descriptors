# Handwriting Data Format (.npy)

This document describes the format of the .npy files used in the handwriting synthesis model.

## Overview

Each .npy file contains a numpy array with 16 elements, representing different levels of handwriting data. The data is structured hierarchically at sentence, word, and segment levels.

## Data Structure

The numpy array contains the following elements in order:

1. `sentence_level_raw_stroke`: Raw stroke data for the entire sentence
   - Shape: (N, 3) where N is the number of points
   - Each point contains (x, y, pen_state)
   - pen_state: 1.0 for pen down, 0.0 for pen up

2. `sentence_level_stroke_in`: Input stroke data for the sentence
   - Shape: (N, 3)
   - Same format as raw_stroke

3. `sentence_level_stroke_out`: Output stroke data for the sentence
   - Shape: (N, 3)
   - Same format as raw_stroke

4. `sentence_level_term`: Term data for the sentence
   - Shape: (N,)
   - Binary values: 1.0 for character boundaries, 0.0 otherwise

5. `sentence_level_char`: Character indices for the sentence
   - Shape: (N,)
   - Integer indices mapping to characters
   - Character mapping:
     - 0: space
     - 1-26: a-z
     - 27-68: special characters and numbers
     - 69: newline

6. `word_level_raw_stroke`: Raw stroke data for each word
   - Shape: [(N1, 3), (N2, 3), ...]
   - List of stroke data for each word

7. `word_level_stroke_in`: Input stroke data for each word
   - Shape: [(N1, 3), (N2, 3), ...]
   - Same format as raw_stroke

8. `word_level_stroke_out`: Output stroke data for each word
   - Shape: [(N1, 3), (N2, 3), ...]
   - Same format as raw_stroke

9. `word_level_term`: Term data for each word
   - Shape: [(N1,), (N2,), ...]
   - Binary values for character boundaries

10. `word_level_char`: Character indices for each word
    - Shape: [(N1,), (N2,), ...]
    - Integer indices mapping to characters

11. `segment_level_raw_stroke`: Raw stroke data for each segment
    - Shape: [[(N1, 3), (N2, 3)], [(N3, 3), (N4, 3)], ...]
    - Nested list of stroke data for each segment of each word

12. `segment_level_stroke_in`: Input stroke data for each segment
    - Shape: [[(N1, 3), (N2, 3)], [(N3, 3), (N4, 3)], ...]
    - Same format as raw_stroke

13. `segment_level_stroke_out`: Output stroke data for each segment
    - Shape: [[(N1, 3), (N2, 3)], [(N3, 3), (N4, 3)], ...]
    - Same format as raw_stroke

14. `segment_level_term`: Term data for each segment
    - Shape: [[(N1,), (N2,)], [(N3,), (N4,)], ...]
    - Binary values for character boundaries

15. `segment_level_char`: Character indices for each segment
    - Shape: [[(N1,), (N2,)], [(N3,), (N4,)], ...]
    - Integer indices mapping to characters

16. `metadata`: Dictionary containing additional information
    - Currently empty but can be extended for future use

## Example

```python
data = np.array([
    stroke_data,                    # sentence_level_raw_stroke
    stroke_data,                    # sentence_level_stroke_in
    stroke_data,                    # sentence_level_stroke_out
    term_data,                      # sentence_level_term
    char_data,                      # sentence_level_char
    [stroke_data],                  # word_level_raw_stroke
    [stroke_data],                  # word_level_stroke_in
    [stroke_data],                  # word_level_stroke_out
    [term_data],                    # word_level_term
    [char_data],                    # word_level_char
    [[stroke_data]],                # segment_level_raw_stroke
    [[stroke_data]],                # segment_level_stroke_in
    [[stroke_data]],                # segment_level_stroke_out
    [[term_data]],                  # segment_level_term
    [[char_data]],                  # segment_level_char
    {}                              # metadata
], dtype=object)
```

## Notes

- All coordinates are normalized to fit within a specific range
- The pen_state value (0.0 or 1.0) indicates whether the pen is up or down
- Character indices are mapped to a predefined vocabulary
- The data structure supports hierarchical processing at sentence, word, and segment levels
- The model uses this hierarchical structure to learn and generate handwriting at different levels of detail 