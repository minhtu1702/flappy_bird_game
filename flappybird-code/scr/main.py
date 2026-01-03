import pygame
import os
from game import Game

def main():
    os.chdir(os.path.dirname(__file__))  # set working directory to scr/
    pygame.init()
    screen = pygame.display.set_mode((400, 600))
    pygame.display.set_caption("Flappy Bird Day")

    clock = pygame.time.Clock()
    game = Game(screen)


    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)

        game.update()
        game.draw()
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
