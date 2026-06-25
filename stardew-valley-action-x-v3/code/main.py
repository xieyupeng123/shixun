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

        # game state: start / game / death
        self.game_state = 'start'
        self.level = None

        # fonts
        self.font_title = pygame.font.Font(None, 72)
        self.font_menu = pygame.font.Font(None, 36)

    def show_start_screen(self):
        self.screen.fill((20, 20, 40))

        title = self.font_title.render(
            'Stardew Valley Action X', True, (255, 215, 0))
        r = title.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        self.screen.blit(title, r)

        prompt = self.font_menu.render(
            'Press ENTER to Start', True, (255, 255, 255))
        r = prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
        self.screen.blit(prompt, r)

        hint = self.font_menu.render(
            'WASD: Move  |  SPACE: Attack  |  ESC: Quit', True, (150, 150, 150))
        r = hint.get_rect(center=(WIDTH // 2, HEIGHT - 50))
        self.screen.blit(hint, r)

    def show_death_screen(self):
        self.screen.fill((30, 0, 0))

        title = self.font_title.render('You Died', True, (255, 50, 50))
        r = title.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        self.screen.blit(title, r)

        exp_text = self.font_menu.render(
            f'EXP: {self.level.player.exp}', True, (255, 255, 255))
        r = exp_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(exp_text, r)

        restart = self.font_menu.render(
            'Press R to Restart', True, (255, 255, 255))
        r = restart.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
        self.screen.blit(restart, r)

        quit_msg = self.font_menu.render(
            'Press ESC to Quit', True, (150, 150, 150))
        r = quit_msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 130))
        self.screen.blit(quit_msg, r)

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

                    elif self.game_state == 'death':
                        if event.key == pygame.K_r:
                            self.game_state = 'game'
                            self.level = Level()

            if self.game_state == 'start':
                self.show_start_screen()
            elif self.game_state == 'death':
                self.show_death_screen()
            else:
                self.screen.fill(WATER_COLOR)
                self.level.run(dt)
                if self.level.player.health <= 0:
                    self.game_state = 'death'

            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == '__main__':
    game = Game()
    game.run()
