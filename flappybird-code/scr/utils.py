import pygame
import os


class ResourceManager:
    def __init__(self, base_path=os.path.join('..', 'assets')):
        self.base_path = base_path

    def image_path(self, relative_path):
        return os.path.join(self.base_path, 'images', os.path.basename(relative_path)) if not os.path.isdir(relative_path) else relative_path

    def sound_path(self, relative_path):
        return os.path.join(self.base_path, 'sound', os.path.basename(relative_path))

    def load_image(self, path):
        full = path
        # allow passing either a path relative to assets/images or a full path
        if not os.path.isabs(path) and not os.path.isdir(path):
            full = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images', os.path.basename(path))
            full = os.path.normpath(full)
        return pygame.image.load(full)

    def load_sound(self, path):
        full = path
        if not os.path.isabs(path):
            full = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sound', os.path.basename(path))
            full = os.path.normpath(full)
        return pygame.mixer.Sound(full)


class FileManager:
    def __init__(self, data_dir=os.path.dirname(__file__)):
        self.data_dir = data_dir

    def read_high_score(self, filename='highscore.txt'):
        path = os.path.join(self.data_dir, filename)
        try:
            with open(path, 'r') as f:
                return int(f.read())
        except Exception:
            return 0

    def write_high_score(self, value, filename='highscore.txt'):
        path = os.path.join(self.data_dir, filename)
        with open(path, 'w') as f:
            f.write(str(value))

    def read_achievements(self, filename='achievements.txt'):
        path = os.path.join(self.data_dir, filename)
        try:
            with open(path, 'r') as f:
                return set(line.strip() for line in f)
        except Exception:
            return set()

    def write_achievements(self, achievements, filename='achievements.txt'):
        path = os.path.join(self.data_dir, filename)
        with open(path, 'w') as f:
            for a in achievements:
                f.write(a + '\n')
