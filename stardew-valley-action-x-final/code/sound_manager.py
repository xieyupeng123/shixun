"""
Centralised sound loading with consistent error handling.
"""
import pygame
from support import get_path


class SoundManager:
    """Loads and caches sounds. Returns None on failure (never crashes)."""

    def __init__(self, volume=0.5):
        self._cache = {}
        self._default_volume = volume

    def load(self, name, volume=None):
        """Load a sound by filename (e.g. 'game_bgm.ogg', 'sword.wav').
        Returns pygame.mixer.Sound or None."""
        if name in self._cache:
            return self._cache[name]
        try:
            path = get_path(f'../audio/{name}')
            snd = pygame.mixer.Sound(path)
            snd.set_volume(volume if volume is not None else self._default_volume)
            self._cache[name] = snd
            return snd
        except (pygame.error, FileNotFoundError):
            return None

    def play_music(self, name, loops=-1, volume=0.3):
        """Start looping background music. Falls back gracefully."""
        try:
            path = get_path(f'../audio/{name}')
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops)
        except pygame.error:
            pass
