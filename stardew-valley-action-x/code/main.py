import pygame
import sys
import time
from settings import WIDTH, HEIGHT, FPS, WATER_COLOR
from level import Level


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Stardew Valley Action X')
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        # game state
        self.game_state = 'start'
        self.level = None

        # fonts
        self.font_title = pygame.font.Font(None, 72)
        self.font_prompt = pygame.font.Font(None, 36)

    def show_start_screen(self):
        self.screen.fill((20, 20, 40))

        # Title
        title_text = self.font_title.render(
            'Stardew Valley Action X', True, (255, 215, 0))
        title_rect = title_text.get_rect(
            center=(WIDTH // 2, HEIGHT // 3))
        self.screen.blit(title_text, title_rect)

        # Start prompt
        prompt_text = self.font_prompt.render(
            'Press ENTER to Start', True, (255, 255, 255))
        prompt_rect = prompt_text.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 + 60))
        self.screen.blit(prompt_text, prompt_rect)

        # Controls hint
        hint_text = self.font_prompt.render(
            'WASD: Move  |  SPACE: Attack  |  ESC: Quit', True, (150, 150, 150))
        hint_rect = hint_text.get_rect(
            center=(WIDTH // 2, HEIGHT - 50))
        self.screen.blit(hint_text, hint_rect)

    def run(self):
        last_time = time.time()
        while True:
            dt = time.time() - last_time
            last_time = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if self.game_state == 'start':
                        if event.key == pygame.K_RETURN:
                            self.game_state = 'game'
                            self.level = Level()

            if self.game_state == 'start':
                self.show_start_screen()
            else:
                self.screen.fill(WATER_COLOR)
                self.level.run(dt)

            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == '__main__':
    game = Game()
    game.run()
