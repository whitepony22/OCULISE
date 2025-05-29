# alphabet_detection.py

# Define the predefined combinations and their corresponding alphabets
combinations = {
    ('↑', '↓', '↑', '↑'): ('A', 'a'),
    ('↑', '↓', '↑', '↓'): ('B', 'b'),
    ('↑', '↓', '↑', '→'): ('C', 'c'),
    ('↑', '↓', '↑', '←'): ('D', 'd'),
    ('↑', '↓', '↓', '↑'): ('E', 'e'),
    ('↑', '↓', '↓', '↓'): ('F', 'f'),
    ('↑', '↓', '↓', '→'): ('G', 'g'),
    ('↑', '↓', '↓', '←'): ('H', 'h'),
    ('↑', '↓', '→', '↑'): ('I', 'i'),
    ('↑', '↓', '→', '↓'): ('J', 'j'),
    ('↑', '↓', '→', '→'): ('K', 'k'),
    ('↑', '↓', '→', '←'): ('L', 'l'),
    ('↑', '↓', '←', '↑'): ('M', 'm'),
    ('↑', '→', '↑', '↑'): ('N', 'n'),
    ('↑', '→', '↑', '↓'): ('O', 'o'),
    ('↑', '→', '↑', '→'): ('P', 'p'),
    ('↑', '→', '↑', '←'): ('Q', 'q'),
    ('↑', '→', '↓', '↑'): ('R', 'r'),
    ('↑', '→', '↓', '↓'): ('S', 's'),
    ('↑', '→', '↓', '→'): ('T', 't'),
    ('↑', '→', '↓', '←'): ('U', 'u'),
    ('↑', '→', '→', '↑'): ('V', 'v'),
    ('↑', '→', '→', '↓'): ('W', 'w'),
    ('↑', '→', '→', '→'): ('X', 'x'),
    ('↑', '→', '→', '←'): ('Y', 'y'),
    ('↑', '→', '←', '↑'): ('Z', 'z'),
    ('↓', '↑', '↑', '↑'): '0',
    ('↓', '↑', '↑', '↓'): '1',
    ('↓', '↑', '↑', '→'): '2',
    ('↓', '↑', '↑', '←'): '3',
    ('↓', '↑', '↓', '↑'): '4',
    ('↓', '↑', '↓', '↓'): '5',
    ('↓', '↑', '↓', '→'): '6',
    ('↓', '↑', '↓', '←'): '7',
    ('↓', '↑', '→', '↑'): '8',
    ('↓', '↑', '→', '↓'): '9',
    ('→', '↑', '↑', '↑'): ' ',
    ('→', '↑', '↑', '↓'): '\n',
    ('→', '↑', '↑', '→'): '.',
    ('→', '↑', '↑', '←'): ',',
    ('→', '↑', '↓', '↑'): '!',
    ('→', '↑', '↓', '↓'): '?',
    ('→', '↑', '↓', '→'): '\'',
    ('→', '↑', '↓', '←'): '\"',
}

def detect_alphabet(directions, caps):
    input_tuple = tuple(directions)
    result = combinations.get(input_tuple, "")

    # Check if the result is a tuple (letter case tuple) and apply caps logic
    if isinstance(result, tuple):
        return result[caps]  # Select lowercase (caps=0) or uppercase (caps=1)
    return result  # Return directly for numbers and symbols

def get_predictions(directions, caps):
    """Return possible predictions based on the first 2 or 3 directions."""
    possible_letters = set()  # Use a set to avoid duplicates
    
    # Iterate through the predefined combinations
    for pattern in combinations:
        # If the given directions match the start of the pattern, add the corresponding letter
        if len(pattern) >= len(directions) and pattern[:len(directions)] == tuple(directions):
            value = combinations[pattern]
            # Determine case for letters
            if isinstance(value, tuple):  # For letters (uppercase, lowercase)
                possible_letters.add(value[caps])  # Select based on caps value (0: lowercase, 1: uppercase)
            else:
                possible_letters.add(value)  # For numbers and symbols, add directly

    # Return the list of possible predictions
    return list(possible_letters)