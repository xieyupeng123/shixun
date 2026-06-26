import pygame
import sys
import time
import math
import os
from random import randint
from settings import WIDTH, HEIGHT, FPS, WATER_COLOR
from support import get_path
from level import Level
from save_manager import save_game, load_game
from sound_manager import SoundManager
from resource_manager import ResourceManager
from music_state import MusicState


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Stardew Valley Action X')
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.game_state = 'start'
        self.current_map_id = 'default'
        self.player = None

        # Audio
        self.audio = SoundManager()
        self.death_sound = self.audio.load('death.wav', volume=0.6)
        self.audio.play_music('game_bgm.ogg')

        self.font_title = pygame.font.Font(None, 72)
        self.font_subtitle = pygame.font.Font(None, 36)
        self.font_menu = pygame.font.Font(None, 48)
        self.font_stats = pygame.font.Font(None, 36)

        self.selected_menu_option = 0
        try:
            bg_raw = pygame.image.load(
                get_path('../graphics/start_bg.png')).convert()
            self.start_bg = pygame.transform.scale(bg_raw, (WIDTH, HEIGHT))
        except Exception:
            self.start_bg = None

        self.death_particles = self._init_death_particles()

        self.show_save_dialog = os.path.exists('savegame.json')
        self.save_dialog_result = None

        self.level = Level(self.current_map_id, player=None, loaded_data=None)
        self.player = self.level.player

    def _init_death_particles(self):
        return [{'x': randint(0, WIDTH), 'y': randint(0, HEIGHT),
                 'size': randint(1, 4), 'spd_x': randint(-2, 2),
                 'spd_y': randint(-2, 2),
                 'color': (randint(100, 255), 0, 0)} for _ in range(30)]

    def _update_death_particles(self):
        for p in self.death_particles:
            p['x'] += p['spd_x']; p['y'] += p['spd_y']
            if p['x'] < 0: p['x'] = WIDTH
            if p['x'] > WIDTH: p['x'] = 0
            if p['y'] < 0: p['y'] = HEIGHT
            if p['y'] > HEIGHT: p['y'] = 0
            pygame.draw.circle(self.screen, p['color'],
                               (int(p['x']), int(p['y'])), p['size'])

    def _render_highlight(self, text, font, color, h_color, center, selected):
        if selected:
            pulse = (pygame.time.get_ticks() // 100) % 2
            if pulse:
                surf = font.render(text, True, h_color)
                r = surf.get_rect(center=center)
                bg = pygame.Surface((r.width + 20, r.height + 10))
                bg.fill((50, 50, 50)); bg.set_alpha(100)
                self.screen.blit(bg, r.move(-10, -5))
            else:
                surf = font.render(text, True, color)
        else:
            surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def show_start_screen(self):
        if self.start_bg:
            self.screen.blit(self.start_bg, (0, 0))
        else:
            self.screen.fill((20, 20, 40))
        t = pygame.time.get_ticks()
        y_off = 10 * math.sin(t * 0.005)
        title = self.font_title.render(
            'Stardew Valley Action X', True, (255, 215, 0))
        self.screen.blit(title, title.get_rect(
            center=(WIDTH // 2, HEIGHT // 4 + y_off)))
        self._render_highlight('Start Game', self.font_menu,
                               (255, 255, 255), (255, 215, 0),
                               (WIDTH // 2, HEIGHT // 2 + 110),
                               self.selected_menu_option == 0)
        self._render_highlight('Quit Game', self.font_menu,
                               (255, 255, 255), (255, 215, 0),
                               (WIDTH // 2, HEIGHT // 2 + 180),
                               self.selected_menu_option == 1)
        # Controls hint
        hint = pygame.font.Font(None, 28).render(
            'LMB: Attack | RMB: Magic | SPACE: Invincible | Q/E: Switch | B: Upgrade | M: Map',
            True, (150, 150, 150))
        self.screen.blit(hint, hint.get_rect(
            center=(WIDTH // 2, HEIGHT - 50)))

        for i in range(15):
            x = (t // 30 + i * 60) % WIDTH
            y = (HEIGHT - 150 - (t // 20 + i * 30) % (HEIGHT // 2)) % HEIGHT
            pygame.draw.circle(self.screen, (100, 150, 255), (x, y), 2 + i % 2)

    def show_death_screen(self):
        self.screen.fill((40, 0, 0))
        t = self.font_title.render('You Died', True, (255, 50, 50))
        self.screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 4)))
        exp = self.player.exp if self.player else 0
        et = self.font_stats.render(
            f'Experience Gained: {exp}', True, (255, 255, 255))
        self.screen.blit(et, et.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        rs = self.font_menu.render('Press R to Restart', True, (255, 255, 255))
        self.screen.blit(rs, rs.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80)))
        qt = self.font_menu.render('Press ESC to Quit', True, (255, 255, 255))
        self.screen.blit(qt, qt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 140)))
        self._update_death_particles()

    def show_victory_screen(self):
        self.screen.fill((10, 10, 30))
        t = pygame.time.get_ticks()
        y_off = 8 * (t % 2000) / 2000.0
        vt = self.font_title.render('YOU WIN!', True, (255, 215, 0))
        self.screen.blit(vt, vt.get_rect(center=(WIDTH // 2, HEIGHT // 3 + y_off)))
        st = self.font_subtitle.render(
            'The Boss has been defeated!', True, (200, 200, 255))
        self.screen.blit(st, st.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        exp = self.player.exp if self.player else 0
        et = self.font_stats.render(
            f'Final Experience: {exp}', True, (255, 255, 255))
        self.screen.blit(et, et.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))
        rs = self.font_menu.render('Press R to Play Again', True, (255, 255, 255))
        self.screen.blit(rs, rs.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 140)))
        for i in range(30):
            x = (t // 15 + i * 57) % WIDTH
            y = HEIGHT - ((t // 12 + i * 37) % HEIGHT)
            pygame.draw.circle(self.screen, (255, 215, 0), (x, int(y)), 2 + i % 3)

    def _restart_game(self):
        ResourceManager.instance().stop_all_sounds()
        pygame.mixer.music.stop()
        MusicState.reset()
        self.player = None
        self.level = Level(self.current_map_id, player=None, loaded_data=None)
        self.player = self.level.player
        self.game_state = 'game'
        self.audio.play_music('game_bgm.ogg')

    def run(self):
        last_time = time.time()
        while True:
            dt = time.time() - last_time
            last_time = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if self.game_state == 'start':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if self.selected_menu_option == 0:
                                self.game_state = 'game'
                            else:
                                pygame.quit(); sys.exit()
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit(); sys.exit()
                        elif event.key == pygame.K_UP:
                            self.selected_menu_option = (self.selected_menu_option - 1) % 2
                        elif event.key == pygame.K_DOWN:
                            self.selected_menu_option = (self.selected_menu_option + 1) % 2

                elif self.game_state == 'death':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r: self._restart_game()
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit(); sys.exit()

                elif self.game_state == 'victory':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r: self._restart_game()
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit(); sys.exit()

                elif self.show_save_dialog:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_c: self.save_dialog_result = 'c'
                        elif event.key == pygame.K_n: self.save_dialog_result = 'n'

                else:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_b: self.level.toggle_menu()
                        if event.key == pygame.K_m: self.level.toggle_map()
                        if event.key == pygame.K_p and self.level.game_paused:
                            save_game(self.level.get_savable_state())
                    if event.type == pygame.MOUSEWHEEL:
                        if self.player and not self.level.game_paused:
                            self.player.cycle_weapon(event.y)

            if self.game_state == 'start':
                self.show_start_screen(); pygame.display.update()
                self.clock.tick(FPS); continue
            elif self.game_state == 'death':
                self.show_death_screen(); pygame.display.update()
                self.clock.tick(FPS); continue
            elif self.game_state == 'victory':
                self.show_victory_screen(); pygame.display.update()
                self.clock.tick(FPS); continue

            if self.show_save_dialog:
                self._draw_save_dialog()
                if self.save_dialog_result:
                    if self.save_dialog_result == 'c':
                        data = load_game('savegame.json')
                        if data and 'player' in data:
                            self.player.from_dict(data['player'])
                    self.show_save_dialog = False
                self.clock.tick(FPS); continue

            self.screen.fill(WATER_COLOR)
            self.level.run(dt)

            if self.player and self.player.health <= 0 and \
               self.game_state != 'death':
                self.game_state = 'death'
                ResourceManager.instance().stop_all_sounds()
                pygame.mixer.music.stop()
                if self.death_sound: self.death_sound.play()

            if self.game_state == 'game' and \
               getattr(self.level.boss, '_trigger_victory', False):
                self.game_state = 'victory'
                ResourceManager.instance().stop_all_sounds()
                pygame.mixer.music.stop()

            pygame.display.update()
            self.clock.tick(FPS)

    def _draw_save_dialog(self):
        self.screen.fill(WATER_COLOR)
        dw, dh = 600, 220
        dx, dy = (WIDTH - dw) // 2, (HEIGHT - dh) // 2
        r = pygame.Rect(dx, dy, dw, dh)
        shadow = pygame.Surface((dw, dh), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 80), shadow.get_rect(), border_radius=24)
        self.screen.blit(shadow, (dx + 6, dy + 6))
        pygame.draw.rect(self.screen, (30, 30, 40), r, border_radius=24)
        pygame.draw.rect(self.screen, (255, 215, 0), r, 4, border_radius=24)
        ft = pygame.font.Font(None, 48)
        fo = pygame.font.Font(None, 36)
        fh = pygame.font.Font(None, 28)
        t1 = ft.render('Save file detected!', True, (255, 255, 255))
        self.screen.blit(t1, (dx + (dw - t1.get_width()) // 2, dy + 30))
        t2 = fo.render('Press C to Continue or N for New Game', True, (255, 255, 0))
        self.screen.blit(t2, (dx + (dw - t2.get_width()) // 2, dy + 100))
        c = fh.render('[C] Continue', True, (180, 255, 180))
        n = fh.render('[N] New Game', True, (255, 180, 180))
        self.screen.blit(c, (dx + 80, dy + 160))
        self.screen.blit(n, (dx + dw - n.get_width() - 80, dy + 160))
        pygame.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()
