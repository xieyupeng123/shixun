import pygame
import sys
import time
import math
import os
from random import randint
from settings import WIDTH, HEIGHT, FPS, WATER_COLOR, weapon_data
from level import Level
from upgrade import Upgrade
from save_manager import load_game, save_game


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Stardew Valley Action X')
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.game_state = 'start'
        self.level = None
        self.upgrade = None

        self.font_title = pygame.font.Font(None, 72)
        self.font_menu = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)

        # save dialog
        self.show_save_dialog = os.path.exists('savegame.json')
        if self.show_save_dialog:
            self.game_state = 'dialog'

        # start screen decorations
        self.start_particles = self._init_particles(25)

    def _init_particles(self, count):
        return [{'x': randint(0, WIDTH), 'y': randint(0, HEIGHT),
                 'size': randint(2, 5), 'spd_x': randint(-1, 1),
                 'spd_y': randint(-2, -1),
                 'color': (randint(100, 200), randint(150, 220), 255)}
                for _ in range(count)]

    def _update_particles(self, particles):
        for p in particles:
            p['x'] += p['spd_x']
            p['y'] += p['spd_y']
            if p['y'] < -10:
                p['y'] = HEIGHT + 10
                p['x'] = randint(0, WIDTH)
            pygame.draw.circle(self.screen, p['color'],
                               (int(p['x']), int(p['y'])), p['size'])

    def show_save_dialog_screen(self):
        self.screen.fill((30, 30, 60))
        w, h = 560, 180
        dx, dy = (WIDTH - w) // 2, (HEIGHT - h) // 2
        r = pygame.Rect(dx, dy, w, h)
        pygame.draw.rect(self.screen, (30, 30, 50), r, border_radius=14)
        pygame.draw.rect(self.screen, (255, 215, 0), r, 3, border_radius=14)

        t = self.font_menu.render('Save file detected!', True, (255, 255, 255))
        self.screen.blit(t, t.get_rect(center=(WIDTH // 2, dy + 45)))

        t2 = self.font_small.render(
            'C = Continue    N = New Game    ESC = Quit',
            True, (255, 255, 100))
        self.screen.blit(t2, t2.get_rect(center=(WIDTH // 2, dy + 110)))

    def show_start_screen(self):
        self.screen.fill((20, 20, 40))
        t = pygame.time.get_ticks()
        y_off = 10 * math.sin(t * 0.005)

        title = self.font_title.render(
            'Stardew Valley Action X', True, (255, 215, 0))
        r = title.get_rect(center=(WIDTH // 2, HEIGHT // 4 + y_off))
        self.screen.blit(title, r)

        wx = WIDTH // 2 - 150
        for i, name in enumerate(weapon_data.keys()):
            txt = self.font_small.render(name, True, (200, 200, 200))
            r = txt.get_rect(center=(wx + i * 75, HEIGHT // 2 - 20))
            self.screen.blit(txt, r)

        prompt = self.font_menu.render(
            'Press ENTER to Start', True, (255, 255, 255))
        r = prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
        self.screen.blit(prompt, r)

        ctrl = self.font_small.render(
            'LMB/SPACE:Atk  |  RMB/Ctrl:Magic  |  Q/Wheel:Wpn  |  E:Magic  |  B:Upg  |  M:Pause',
            True, (150, 150, 150))
        r = ctrl.get_rect(center=(WIDTH // 2, HEIGHT - 70))
        self.screen.blit(ctrl, r)
        ctrl2 = self.font_small.render(
            'ESC: Quit', True, (120, 120, 120))
        r = ctrl2.get_rect(center=(WIDTH // 2, HEIGHT - 40))
        self.screen.blit(ctrl2, r)

        self._update_particles(self.start_particles)

    def show_pause_screen(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        t = self.font_title.render('PAUSED', True, (255, 255, 255))
        r = t.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        self.screen.blit(t, r)

        t2 = self.font_small.render(
            'M: Resume  |  P: Save Game  |  ESC: Quit',
            True, (200, 200, 200))
        r = t2.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(t2, r)

    def show_death_screen(self):
        self.screen.fill((40, 0, 0))
        t = self.font_title.render('You Died', True, (255, 50, 50))
        self.screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 3)))
        exp = self.font_menu.render(
            f'EXP: {self.level.player.exp}', True, (255, 255, 255))
        self.screen.blit(exp, exp.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        rs = self.font_menu.render('Press R to Restart', True, (255, 255, 255))
        self.screen.blit(rs, rs.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80)))

    def show_victory_screen(self):
        self.screen.fill((0, 20, 0))
        c = pygame.time.get_ticks()
        title = self.font_title.render('Victory!', True, (255, 215, 0))
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 3)))
        exp = self.font_menu.render(
            f'Total EXP: {self.level.player.exp}', True, (255, 255, 255))
        self.screen.blit(exp, exp.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        rs = self.font_menu.render('Press R to Restart', True, (255, 255, 255))
        self.screen.blit(rs, rs.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))
        for i in range(15):
            x = (c // 30 + i * 85) % WIDTH
            y = (c // 20 + i * 45) % HEIGHT
            pygame.draw.circle(self.screen, (255, 215, 0), (x, y), 2 + i % 3)

    def _start_new_game(self):
        self.level = Level()
        self.upgrade = Upgrade(self.level.player)
        self.game_state = 'game'

    def _continue_game(self):
        data = load_game('savegame.json')
        self.level = Level(loaded_data=data)
        self.upgrade = Upgrade(self.level.player)
        self.game_state = 'game'

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

                    # dialog state
                    if self.game_state == 'dialog':
                        if event.key == pygame.K_c:
                            self._continue_game()
                        elif event.key == pygame.K_n:
                            self._start_new_game()

                    # start state
                    elif self.game_state == 'start':
                        if event.key == pygame.K_RETURN:
                            self._start_new_game()

                    # death / victory
                    elif self.game_state in ('death', 'victory'):
                        if event.key == pygame.K_r:
                            self._start_new_game()

                    # pause
                    elif self.game_state == 'pause':
                        if event.key == pygame.K_m:
                            self.game_state = 'game'
                        elif event.key == pygame.K_p:
                            save_game(self.level.get_savable_state())

                    # upgrade
                    elif self.game_state == 'upgrade':
                        if event.key == pygame.K_b:
                            self.game_state = 'game'

                    # game
                    elif self.game_state == 'game':
                        if event.key == pygame.K_b:
                            self.game_state = 'upgrade'
                        elif event.key == pygame.K_m:
                            self.game_state = 'pause'

                if event.type == pygame.MOUSEWHEEL:
                    if self.game_state in ('game', 'upgrade') and self.level:
                        self.level.player.cycle_weapon(event.y)

            if self.game_state == 'dialog':
                self.show_save_dialog_screen()
            elif self.game_state == 'start':
                self.show_start_screen()
            elif self.game_state == 'pause':
                self.show_pause_screen()
            elif self.game_state == 'death':
                self.show_death_screen()
            elif self.game_state == 'victory':
                self.show_victory_screen()
            elif self.game_state == 'upgrade':
                self.screen.fill((20, 20, 40))
                self.upgrade.display()
            else:
                self.screen.fill(WATER_COLOR)
                self.level.run(dt)
                if self.level.player.health <= 0:
                    self.game_state = 'death'
                elif self.level.all_enemies_dead():
                    self.game_state = 'victory'

            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == '__main__':
    game = Game()
    game.run()
