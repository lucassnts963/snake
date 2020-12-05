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
            self.show_score()
            
            self.machine_playing()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if (event.key == pygame.K_DOWN and 
                        self.snake.direction != self.snake.accepted_directions['up']):
                        self.snake.change_direction(self.snake.accepted_directions['down'])
                    if (event.key == pygame.K_UP and
                        self.snake.direction != self.snake.accepted_directions['down']):
                        self.snake.change_direction(self.snake.accepted_directions['up'])
                    if (event.key == pygame.K_RIGHT and
                        self.snake.direction != self.snake.accepted_directions['left']):
                        self.snake.change_direction(self.snake.accepted_directions['right'])
                    if (event.key == pygame.K_LEFT and 
                        self.snake.direction != self.snake.accepted_directions['right']):
                        self.snake.change_direction(self.snake.accepted_directions['left'])
                    
            clock.tick(15)
    
            pygame.display.flip()
            pygame.display.update()
    
    def show_score(self):
        font = pygame.font.Font('freesansbold.ttf', 18)
        score_font = font.render('Score: %s' % (self.snake.score), True, config.colors['white'])
        score_rect = score_font.get_rect()
        score_rect.topleft = (config.screen_size[0] - 120, 10)
        self.screen.blit(score_font, score_rect)
        
    def machine_playing(self):
        pass

game = Game()

game.main()