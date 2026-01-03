import pygame
import random

class Particle:
    def __init__(self, x, y, color=(255, 255, 255), size=3, lifetime=20):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.size = max(1, int(self.size * (self.lifetime / self.max_lifetime)))

    def draw(self, screen):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (self.size, self.size), self.size)
        screen.blit(surf, (self.x - self.size, self.y - self.size))

    def is_dead(self):
        return self.lifetime <= 0