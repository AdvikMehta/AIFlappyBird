import pygame
import neat
import os
import random
pygame.font.init()

# const variables
WIN_WIDTH = 500
WIN_HEIGHT = 800

GEN = 0

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bg.png")))

STAT_FONT = pygame.font.SysFont('comicsans', 50)

# bird class
class Bird:
    IMGS = BIRD_IMGS
    MAX_ROT = 25
    ROT_VEL = 20
    ANIM_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tickCount = 0
        self.vel = 0
        self.height = self.y
        self.imgCount = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5  # to jump up
        self.tickCount = 0  # when we last jumped
        self.height = self.y  # height before jump started

    def move(self):
        self.tickCount += 1  # how many times we moved since the last jump

        d = self.vel * self.tickCount + 1.5*self.tickCount**2  # D = ut + (1/2a)t^2
        # as tickCount increases (1, 2, 3..), d decreases (as we reach max height)

        d = 16 if d >= 16 else d
        d -= 2 if d < 0 else 0  # d -= 0 and not d = 0

        self.y = self.y + d

        if d < 0 or self.y < self.height + 50:  # were still jumping
            if self.tilt < self.MAX_ROT:
                self.tilt = self.MAX_ROT
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL  # nose-diving when moving faster and faster

    def draw(self, screen):
        self.imgCount += 1  # next frame

        if self.imgCount < self.ANIM_TIME:
            self.img = self.IMGS[0]
        elif self.imgCount < self.ANIM_TIME*2:
            self.img = self.IMGS[1]
        elif self.imgCount < self.ANIM_TIME*3:
            self.img = self.IMGS[2]
        elif self.imgCount < self.ANIM_TIME*4:
            self.img = self.IMGS[1]
        elif self.imgCount == self.ANIM_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.imgCount = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]  # not flapping when free-falling
            self.imgCount = self.ANIM_TIME*2

        # image rotation
        rotatedImg = pygame.transform.rotate(self.img, self.tilt)
        newRect = rotatedImg.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        screen.blit(rotatedImg, newRect.topleft)

    def getMask(self):
        return pygame.mask.from_surface(self.img)

# bird class
class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        self.passed = False
        self.setHeight()

    def setHeight(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, screen):
        screen.blit(self.PIPE_TOP, (self.x, self.top))
        screen.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        birdMask = bird.getMask()
        topMask = pygame.mask.from_surface(self.PIPE_TOP)
        bottomMask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        topOffset = (self.x - bird.x, self.top - round(bird.y))
        bottomOffset = (self.x - bird.x, self.bottom - round(bird.y))

        tPoint = birdMask.overlap(topMask, topOffset)  # returns None if doesn't collide
        bPoint = birdMask.overlap(bottomMask, bottomOffset)  # returns None if doesn't collide

        if tPoint or bPoint:
            return True
        return False

# base class
class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG
    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x1 = self.x1 + self.WIDTH

    def draw(self, screen):
        screen.blit(self.IMG, (self.x1, self.y))
        screen.blit(self.IMG, (self.x2, self.y))

def drawWindow(screen, birds, pipes, base, score, gen):
    screen.blit(BG_IMG, (0,0))
    for pipe in pipes:
        pipe.draw(screen)
    text = STAT_FONT.render("Score: " + str(score), True, (255,255,255))
    screen.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    text = STAT_FONT.render("Gen: " + str(gen), True, (255, 255, 255))
    screen.blit(text, (10, 10))
    base.draw(screen)
    for bird in birds:
        bird.draw(screen)
    pygame.display.update()

def checkPipes(pipes, birds, ge, nets):
    addPipe = False
    rem = []
    for pipe in pipes:
        for x, bird in enumerate(birds):
            if pipe.collide(bird):  # collided
                ge[x].fitness -= 1
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)
            if not pipe.passed and pipe.x < bird.x:  # passed
                pipe.passed = True
                addPipe = True
        if pipe.x + pipe.PIPE_TOP.get_width() < 0:  # off-screen
            rem.append(pipe)
        pipe.move()
    return addPipe, rem

def removePipes(pipes, rem):
    for pipe in rem:
        pipes.remove(pipe)

def addPipes(addPipe, pipes, ge):
    if addPipe:
        for g in ge:
            g.fitness += 5
        pipes.append(Pipe(600))  # new pipe
        return 1
    return 0

def main(genomes, config):  # all fitness functions should have these 2 parameters
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []

    for _,g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    pipes = [Pipe(600)]
    base = Base(730)
    score = 0
    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    running = True
    while running:
        clock.tick(30)

        # event listening
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                quit()

        pipeInd = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipeInd = 1
        else:
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipeInd].height), abs(bird.y - pipes[pipeInd].bottom)))
            if output[0] > 0.5:  # output is a list
                bird.jump()

        # pipe mechanics
        addPipe, rem = checkPipes(pipes, birds, ge, nets)
        score += addPipes(addPipe, pipes, ge)
        removePipes(pipes, rem)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        drawWindow(screen, birds, pipes, base, score, GEN)


def run(configPath):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                configPath)
    p = neat.Population(config)

    # printing statistics
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # save the object below using pickler to not train the birds everyrime
    _ = p.run(main, 50)  # 50 = generations, call main 50 times


if __name__ == '__main__':
    localDir = os.path.dirname(__file__)
    config_path = os.path.join(localDir, "config-feedforward.txt")
    run(config_path)
