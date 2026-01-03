import pygame
import random

class Pipe:
    def __init__(self, x, gap_y, gap_height=None, speed=3):
        self.x = x
        self.gap_y = gap_y
        if gap_height is None:
            gap_height = random.randint(150, 220)
        self.gap_height = gap_height
        self.width = 52
        self.speed = speed
        self.scored = False

        # chỉ có ảnh ống dưới
        self.image_bottom = pygame.image.load("../assets/images/pipe-green.png").convert_alpha()
        self.image_bottom = pygame.transform.scale(self.image_bottom, (self.width, self.image_bottom.get_height()))

        # tạo ảnh ống trên bằng cách lật ngược ảnh dưới
        self.image_top = pygame.transform.flip(self.image_bottom, False, True)

    def update(self):
        self.x -= self.speed

    def off_screen(self):
        return self.x + self.width < 0

    def draw(self, screen):
        top_height = self.gap_y - self.gap_height // 2
        if top_height > 0:
            scaled_top = pygame.transform.scale(self.image_top, (self.width, top_height))
            top_rect = scaled_top.get_rect(midbottom=(self.x + self.width // 2, self.gap_y - self.gap_height // 2))
            screen.blit(scaled_top, top_rect)
        else:
            # if negative, don't draw or draw at 0
            top_rect = self.image_top.get_rect(midbottom=(self.x + self.width // 2, self.gap_y - self.gap_height // 2))
            screen.blit(self.image_top, top_rect)

        # vẽ ống dưới
        bottom_start = self.gap_y + self.gap_height // 2
        bottom_height = 600 - bottom_start  # assume screen height 600
        if bottom_height > 0:
            scaled_bottom = pygame.transform.scale(self.image_bottom, (self.width, bottom_height))
            bottom_rect = scaled_bottom.get_rect(midtop=(self.x + self.width // 2, bottom_start))
            screen.blit(scaled_bottom, bottom_rect)

    def collides_with(self, bird):
        bird_rect = bird.get_rect()

        # tạo rect cho ống trên và dưới
        top_rect = self.image_top.get_rect(midbottom=(self.x + self.width // 2, self.gap_y - self.gap_height // 2))
        bottom_rect = self.image_bottom.get_rect(midtop=(self.x + self.width // 2, self.gap_y + self.gap_height // 2))

        return bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect)
