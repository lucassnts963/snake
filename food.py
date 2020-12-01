import pygame

import random as rd

from config import Configuration

config = Configuration()

#Object that represent the food
class Food:
    def __init__(self, game):
        x = rd.randint(0,config.screen_size[0]/config.size_rect-1) * config.size_rect
        y = rd.randint(0,config.screen_size[0]/config.size_rect-1) * config.size_rect
        self.position = (x,y)
        self.game = game
    
    #Method to draw the food at the screen    
    def draw(self):
        apple = pygame.Surface((config.size_rect, config.size_rect))
        apple.fill(config.colors['red'])
        self.game.screen.blit(apple, self.position)
        