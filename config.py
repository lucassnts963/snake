#Colors
black = (  0,   0,   0)
white = (255, 255, 255)
red   = (255,   0,   0)
green = (  0, 255,   0)
blue  = (  0,   0, 255)

class Configuration:
    def __init__(self):
        self.screen_size = [500, 500]
        self.size_rect = self.screen_size[0]/50
        self.colors = {'black': black, 'white': white, 'red': red, 'green': green, 'blue': blue}