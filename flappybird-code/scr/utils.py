import pygame

class Loader:
    @staticmethod
    def load_image(path):
        return pygame.image.load(path)

    @staticmethod
    def load_sound(path):
        return pygame.mixer.Sound(path)
