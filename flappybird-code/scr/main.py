import pygame
import os
from game import Game
from utils import ResourceManager, FileManager


class GameApp:
    def __init__(self, size=(400, 600)):
        os.chdir(os.path.dirname(__file__))
        pygame.init()
        self.screen = pygame.display.set_mode(size)
        pygame.display.set_caption("Flappy Bird Day")
        self.clock = pygame.time.Clock()
        self.resource_manager = ResourceManager()
        self.file_manager = FileManager()
        self.game = Game(self.screen, resource_manager=self.resource_manager, file_manager=self.file_manager)

    def run(self):
        running = True
        while running:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.game.handle_event(event)

            self.game.update()
            self.game.draw()
            pygame.display.flip()

        pygame.quit()


def main():
    app = GameApp()
    app.run()


if __name__ == "__main__":
    main()
