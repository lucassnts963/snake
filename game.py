import pygame, sys

from config import Configuration
from snake import Snake
from food import Food

config = Configuration()

#Controller the time
clock = pygame.time.Clock()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(config.screen_size)
        self.snake  = Snake(self)
        self.food   = Food(self)
        print('__init__()')
        
        
    def main(self):
        pygame.display.set_caption('Snake')
        
        while 1:
            self.screen.fill(config.colors['black'])
            self.snake.update()
            self.food.draw()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_DOWN:
                        self.snake.change_direction(self.snake.accepted_directions['down'])
                    if event.key == pygame.K_UP:
                        self.snake.change_direction(self.snake.accepted_directions['up'])
                    if event.key == pygame.K_RIGHT:
                        self.snake.change_direction(self.snake.accepted_directions['right'])
                    if event.key == pygame.K_LEFT:
                        self.snake.change_direction(self.snake.accepted_directions['left'])
                    
            clock.tick(15)
    
            pygame.display.flip()
            pygame.display.update()
            