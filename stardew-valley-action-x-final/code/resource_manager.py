"""
Centralized resource loading with caching.
Prevents redundant disk I/O for images, sounds, and fonts.
"""
import pygame
from support import get_path


class ResourceManager:
    """Singleton resource cache. Use ResourceManager.instance() to get the global instance."""

    _singleton = None

    @classmethod
    def instance(cls):
        if cls._singleton is None:
            cls._singleton = cls()
        return cls._singleton

    def __init__(self):
        self._images = {}    # path -> Surface
        self._sounds = {}    # path -> Sound
        self._fonts = {}     # (path, size) -> Font

    def get_image(self, path):
        """Load and cache an image. `path` is relative to code/ (e.g. '../graphics/test/player.png')."""
        if path not in self._images:
            full_path = get_path(path)
            self._images[path] = pygame.image.load(full_path).convert_alpha()
        return self._images[path]

    def get_sound(self, path, volume=0.5):
        """Load and cache a sound. Returns pygame.mixer.Sound."""
        if path not in self._sounds:
            full_path = get_path(path)
            snd = pygame.mixer.Sound(full_path)
            snd.set_volume(volume)
            self._sounds[path] = snd
        return self._sounds[path]

    def get_font(self, path, size):
        """Load and cache a font. Returns pygame.font.Font."""
        key = (path, size)
        if key not in self._fonts:
            full_path = get_path(path) if path else None
            self._fonts[key] = pygame.font.Font(full_path, size)
        return self._fonts[key]

    def get_folder_images(self, path):
        """Load all images in a folder (sorted by filename). Returns list of Surfaces.
        Results are cached per folder path."""
        cache_key = ('folder', path)
        if cache_key not in self._images:
            from support import import_folder
            self._images[cache_key] = import_folder(path)
        return self._images[cache_key]

    def stop_all_sounds(self):
        """Stop all cached Sound objects. Use on game restart to silence leftovers."""
        for snd in self._sounds.values():
            snd.stop()
