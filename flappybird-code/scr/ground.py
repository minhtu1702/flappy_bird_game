import pygame

class Ground:
    def __init__(self, y, width, height=100, speed=3):
        self.y = y
        self.width = width
        self.height = height
        self.x = 0
        self.speed = speed

        self.image = pygame.image.load("../assets/images/base.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

    def update(self):
        # hiệu ứng mặt đất di chuyển
        self.x -= self.speed
        if self.x <= -self.width:
            self.x = 0

    def draw(self, screen):
        # vẽ 2 lần để tạo hiệu ứng cuộn liên tục
        screen.blit(self.image, (self.x, self.y))
        screen.blit(self.image, (self.x + self.width, self.y))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
