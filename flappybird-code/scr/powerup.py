import pygame

class PowerUp:
    def __init__(self, x, y, type="speed", resource_manager=None):
        self.x = x
        self.y = y
        self.type = type
        self.speed = 3
        if resource_manager:
            self.image = resource_manager.load_image("../assets/images/0.png").convert_alpha()
        else:
            self.image = pygame.image.load("../assets/images/0.png").convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.x -= self.speed
        self.rect.center = (self.x, self.y)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def off_screen(self):
        return self.x + self.image.get_width() < 0