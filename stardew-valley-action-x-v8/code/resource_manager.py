"""Singleton cache for images, sounds, and fonts."""
import pygame
import os


class ResourceManager:
    _instance = None

    def __init__(self):
        self._images = {}
        self._sounds = {}
        self._folders = {}

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_image(self, path):
        if path not in self._images:
            self._images[path] = pygame.image.load(path).convert_alpha()
        return self._images[path]

    def get_folder_images(self, path):
        if path not in self._folders:
            images = []
            for f in sorted(os.listdir(path)):
                full = os.path.join(path, f)
                if os.path.isfile(full):
                    images.append(self.get_image(full))
            self._folders[path] = images
        return self._folders[path]

    def clear(self):
        self._images.clear()
        self._sounds.clear()
        self._folders.clear()
