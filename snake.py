import pygame

from config import Configuration

UP    = 1
DOWN  = 2
LEFT  = 3
RIGHT = 4

config = Configuration()

class Snake:
    
    def __init__(self, game):
        self.body = [(0,0),(10,0),(20,0)]
        self.game = game
        self.accepted_directions = {'up': UP, 'down': DOWN, 'left': LEFT, 'right': RIGHT}
        self.direction = RIGHT
        self.score = 0
    
    def draw(self):
        skin = pygame.Surface((config.size_rect, config.size_rect))
        skin.fill(config.colors['white'])
        for pos in self.body:
            self.game.screen.blit(skin,pos)
    
    def update(self):
        step = config.size_rect
        if self.direction == UP:
            pos = (self.body[0][0], self.body[0][1]-step)
            self.body[0] = pos
        if self.direction == DOWN:
            pos = (self.body[0][0], self.body[0][1]+step)
            self.body[0] = pos
        if self.direction == RIGHT:
            pos = (self.body[0][0]+step, self.body[0][1])
            self.body[0] = pos
        if self.direction == LEFT:
            pos = (self.body[0][0]-step, self.body[0][1])
            self.body[0] = pos
        
        self.get_collision()
        
        for i in range(len(self.body)-1, 0, -1):
            self.body[i] = self.body[i-1]
            
        self.eat(self.game.food)
        self.draw()
    
    def restart(self):
        self.body = [(0,0),(10,0),(20,0)]
        self.direction = RIGHT
        self.game.food.__init__(self.game)
        self.score = 0
    
    def change_direction(self, direction):
        self.direction = direction
    
    def eat(self, food):
        if self.body[0] == food.position:
            self.body.append((food.position))
            self.game.food.__init__(self.game)
            self.score += 1
            
    def get_collision(self):    
        if self.body[0][0] >= config.screen_size[0]:
            self.restart()
        if self.body[0][0] < 0:
            self.restart()
        if self.body[0][1] >= config.screen_size[1]:
            self.restart()
        if self.body[0][1] < 0:
            self.restart()
        for i in range(1, len(self.body) - 1):
            if self.body[0][0] == self.body[i][0] and self.body[0][1] == self.body[i][1]:
                self.restart()
                break
            
    def get_collision_tail(self, pos):
        for i in range(1, len(self.body)-1):
            print(len(self.body)-1)
            if pos == self.body[i]:
                self.restart()