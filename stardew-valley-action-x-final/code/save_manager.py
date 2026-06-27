import json
import os
import tempfile

def save_game(data, filepath='savegame.json'):
    """Save the game state to a JSON file atomically.

    Writes to a temp file first, then renames — prevents corrupt saves
    if the process is interrupted mid-write.
    """
    try:
        dir_name = os.path.dirname(filepath) or '.'
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f, indent=4)
            os.replace(tmp_path, filepath)
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except Exception as e:
        print(f'[ERROR] Failed to save game: {e}')

def load_game(filepath='savegame.json'):
    """Load the game state from a JSON file. Returns None if not found or error."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception:
        return None
