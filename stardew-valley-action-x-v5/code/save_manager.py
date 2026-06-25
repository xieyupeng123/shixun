"""Save/Load game state as JSON."""
import json


def save_game(data, filepath='savegame.json'):
    """Save game state to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def load_game(filepath='savegame.json'):
    """Load game state from JSON file. Returns None if not found."""
    import os
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None
