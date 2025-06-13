import pygame
import random
import sys
import os

# Initialize pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.5
JUMP_STRENGTH = -12
SCROLL_THRESH = 200
SCROLL_SPEED = 4

# Colors
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)
ORANGE = (255, 165, 0)

# Create the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Angel Cat Cloud Jumper")
clock = pygame.time.Clock()

# Load images
def load_image(name, scale=1):
    try:
        image = pygame.image.load(name).convert_alpha()
        width = image.get_width()
        height = image.get_height()
        return pygame.transform.scale(image, (int(width * scale), int(height * scale)))
    except pygame.error:
        # If image loading fails, create a placeholder
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        if "cat" in name:
            pygame.draw.rect(surf, ORANGE, (0, 0, 50, 30))
            pygame.draw.polygon(surf, WHITE, [(10, 5), (25, 0), (40, 5)])  # Wings
        elif "cloud" in name:
            pygame.draw.ellipse(surf, WHITE, (0, 0, 50, 30))
        elif "yarn" in name:
            pygame.draw.circle(surf, (255, 0, 0), (25, 25), 15)
        elif "treat" in name:
            pygame.draw.rect(surf, (139, 69, 19), (10, 20, 30, 20))
        return surf

# Try to load images, or use placeholders if files don't exist
try:
    cat_img = load_image("cat.png", 0.2)
    cloud_img = load_image("cloud.png", 0.3)
    yarn_img = load_image("yarn.png", 0.15)
    treat_bowl_img = load_image("treat_bowl.png", 0.25)
    bg_img = load_image("sky_bg.png", 1)
except:
    # Create placeholder images
    cat_img = load_image("cat.png")
    cloud_img = load_image("cloud.png")
    yarn_img = load_image("yarn.png")
    treat_bowl_img = load_image("treat_bowl.png")
    bg_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg_img.fill(SKY_BLUE)

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = cat_img
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True
        self.score = 0

    def update(self, platforms):
        dx = 0
        dy = 0
        
        # Get key presses
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            dx = -5
            self.direction = -1
        if key[pygame.K_RIGHT]:
            dx = 5
            self.direction = 1
        if key[pygame.K_SPACE] and not self.jumped and not self.in_air:
            self.vel_y = JUMP_STRENGTH
            self.jumped = True
            self.in_air = True
        if not key[pygame.K_SPACE]:
            self.jumped = False
            
        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y
        
        # Check for collisions with platforms
        self.in_air = True
        for platform in platforms:
            # Check for collision in x direction
            if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height):
                dx = 0
                
            # Check for collision in y direction
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                # Check if below platform (jumping)
                if self.vel_y < 0:
                    dy = platform.rect.bottom - self.rect.top
                    self.vel_y = 0
                # Check if above platform (falling)
                elif self.vel_y >= 0:
                    dy = platform.rect.top - self.rect.bottom
                    self.vel_y = 0
                    self.in_air = False
        
        # Update player position
        self.rect.x += dx
        self.rect.y += dy
        
        # Check if player has fallen off the screen
        if self.rect.top > SCREEN_HEIGHT:
            return True
        return False

# Platform class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width):
        super().__init__()
        self.image = pygame.transform.scale(cloud_img, (width, 30))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
    def update(self, scroll):
        self.rect.x -= scroll

# Yarn ball class (collectible)
class YarnBall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = yarn_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
    def update(self, scroll):
        self.rect.x -= scroll

# Treat bowl class (goal)
class TreatBowl(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = treat_bowl_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
    def update(self, scroll):
        self.rect.x -= scroll

# Game class
class Game:
    def __init__(self):
        self.reset_game()
        
    def reset_game(self):
        # Create sprite groups
        self.platforms = pygame.sprite.Group()
        self.yarn_balls = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        self.treat_bowl = None
        
        # Create player
        self.player = Player(100, 300)
        self.all_sprites.add(self.player)
        
        # Create initial platforms
        self.create_platforms()
        
        # Game variables
        self.scroll = 0
        self.bg_scroll = 0
        self.level_complete = False
        self.game_over = False
        self.score = 0
        
    def create_platforms(self):
        # Starting platform
        platform = Platform(0, 500, 200)
        self.platforms.add(platform)
        self.all_sprites.add(platform)
        
        # Generate random platforms
        self.last_x = 200
        for i in range(15):
            width = random.randint(80, 150)
            x = self.last_x + random.randint(100, 200)
            y = random.randint(400, 550)
            platform = Platform(x, y, width)
            self.platforms.add(platform)
            self.all_sprites.add(platform)
            
            # Add yarn balls on some platforms
            if random.random() > 0.5:
                yarn = YarnBall(x + width // 2, y - 30)
                self.yarn_balls.add(yarn)
                self.all_sprites.add(yarn)
                
            self.last_x = x + width
        
        # Add treat bowl at the end
        self.treat_bowl = TreatBowl(self.last_x + 100, 450)
        self.all_sprites.add(self.treat_bowl)
    
    def draw_text(self, text, size, x, y, color=WHITE):
        font = pygame.font.SysFont('Arial', size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        screen.blit(text_surface, text_rect)
    
    def run(self):
        running = True
        while running:
            clock.tick(FPS)
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if (event.key == pygame.K_RETURN or event.key == pygame.K_SPACE) and (self.game_over or self.level_complete):
                        self.reset_game()
            
            if not self.game_over and not self.level_complete:
                # Update scroll based on player position
                if self.player.rect.right > SCREEN_WIDTH - SCROLL_THRESH and self.bg_scroll < (self.last_x + 500):
                    self.scroll = SCROLL_SPEED
                else:
                    self.scroll = 0
                
                # Update background scroll
                self.bg_scroll += self.scroll
                
                # Draw scrolling background
                for i in range(4):
                    screen.blit(bg_img, ((i * bg_img.get_width()) - self.bg_scroll * 0.5, 0))
                
                # Update all sprites
                self.platforms.update(self.scroll)
                
                # Check for yarn ball collection
                yarn_hits = pygame.sprite.spritecollide(self.player, self.yarn_balls, True)
                for yarn in yarn_hits:
                    self.score += 10
                
                # Check for treat bowl (level complete)
                if self.treat_bowl and pygame.sprite.collide_rect(self.player, self.treat_bowl):
                    self.level_complete = True
                
                # Update yarn balls and treat bowl
                self.yarn_balls.update(self.scroll)
                if self.treat_bowl:
                    self.treat_bowl.update(self.scroll)
                
                # Check if player has fallen off screen
                self.game_over = self.player.update(self.platforms)
                
                # Draw all sprites
                self.all_sprites.draw(screen)
                
                # Display score
                self.draw_text(f"Score: {self.score}", 30, 100, 50)
                
            elif self.game_over:
                screen.fill((0, 0, 0))
                self.draw_text("GAME OVER!", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
                self.draw_text(f"Final Score: {self.score}", 36, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)
                self.draw_text("Press Enter to play again", 24, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)
            
            elif self.level_complete:
                screen.fill(SKY_BLUE)
                self.draw_text("LEVEL COMPLETE!", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
                self.draw_text(f"Final Score: {self.score}", 36, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)
                self.draw_text("Press Enter to play again", 24, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()
