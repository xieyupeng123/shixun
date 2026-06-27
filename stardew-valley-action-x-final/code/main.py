import warnings
import os
import pygame
import sys
import time
import math
from random import randint
from settings import WIDTH, HEIGHT, FPS, WATER_COLOR
from support import get_path
from music_state import MusicState
from level import Level
from sound_manager import SoundManager

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

# Suppress warnings
warnings.simplefilter('ignore', UserWarning)

# UI Constants
START_BG_COLOR = (20, 20, 40)
DEATH_BG_COLOR = (40, 0, 0)
TITLE_COLOR = (255, 215, 0)
SUBTITLE_COLOR = (200, 200, 200)
MENU_COLOR = (255, 255, 255)
DEATH_TITLE_COLOR = (255, 0, 0)
PARTICLE_COLOR = (100, 150, 255)
DEATH_PARTICLE_BASE_COLOR = (100, 0, 0)

TITLE_FONT_SIZE = 72
SUBTITLE_FONT_SIZE = 36
MENU_FONT_SIZE = 48
STATS_FONT_SIZE = 36

TITLE_Y_OFFSET = HEIGHT // 4
SUBTITLE_Y_OFFSET = TITLE_Y_OFFSET + 80
START_MENU_Y_OFFSET = HEIGHT // 2 + 110
QUIT_MENU_Y_OFFSET = HEIGHT // 2 + 180
DEATH_MENU_Y_OFFSET = HEIGHT // 2 + 80
DEATH_QUIT_Y_OFFSET = HEIGHT // 2 + 140

PARTICLE_COUNT_START = 20
PARTICLE_COUNT_DEATH = 30  # Reduced for performance


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Stardew Valley Action X')
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        # Game states
        self.game_state = 'start'  # 'start', 'game', 'death', 'victory'

        # Fonts (pre-loaded for performance)
        self.font_title = pygame.font.Font(None, TITLE_FONT_SIZE)
        self.font_subtitle = pygame.font.Font(None, SUBTITLE_FONT_SIZE)
        self.font_menu = pygame.font.Font(None, MENU_FONT_SIZE)
        self.font_stats = pygame.font.Font(None, STATS_FONT_SIZE)
        self.font_dialog_title = pygame.font.Font(None, 48)
        self.font_dialog_option = pygame.font.Font(None, 36)
        self.font_dialog_hint = pygame.font.Font(None, 28)

        # Audio — centralised via SoundManager
        self.audio = SoundManager()
        self.start_music = self.audio.load('game_bgm.ogg', volume=0.3)
        self.menu_move_sound = self.audio.load('sword.wav', volume=0.5)
        self.menu_select_sound = self.audio.load('sword.wav', volume=0.5)
        self.death_sound = self.audio.load('death.wav', volume=0.6)

        self.audio.play_music('game_bgm.ogg')

        # Start screen background
        try:
            bg_raw = pygame.image.load(get_path('../graphics/start_bg.png')).convert()
            self.start_bg = pygame.transform.scale(bg_raw, (WIDTH, HEIGHT))
        except Exception:
            self.start_bg = None

        # Particle animation data
        self.death_particles = []
        self._init_death_particles()

        # Menu state
        self.selected_menu_option = 0  # 0 = Start, 1 = Quit

        # Level system setup
        self.current_map_id = 'default'
        self.player = None
        self.show_save_dialog = False
        self.save_dialog_result = None
        save_path = 'savegame.json'
        if os.path.exists(save_path):
            self.show_save_dialog = True
            self.save_dialog_result = None
        self.level = Level(self.current_map_id, player=None, loaded_data=None)
        self.player = self.level.player

    def _restart_game(self):
        """Full restart: reset all state, recreate level, restart music."""
        from resource_manager import ResourceManager
        ResourceManager.instance().stop_all_sounds()
        pygame.mixer.music.stop()
        MusicState.reset()
        self.player = None
        self.level = Level(self.current_map_id, player=None, loaded_data=None)
        self.player = self.level.player
        self.game_state = 'game'
        pygame.mixer.music.load(get_path('../audio/game_bgm.ogg'))
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)

    def _init_death_particles(self):
        """Initialize death screen particles with random properties"""
        self.death_particles = []
        for _ in range(PARTICLE_COUNT_DEATH):
            particle = {
                'x': randint(0, WIDTH),
                'y': randint(0, HEIGHT),
                'size': randint(1, 4),
                'speed_x': randint(-2, 2),
                'speed_y': randint(-2, 2),
                'color': (randint(100, 255), 0, 0)
            }
            self.death_particles.append(particle)

    def _update_and_draw_death_particles(self):
        """Update and draw animated death particles"""
        for particle in self.death_particles:
            # Update position
            particle['x'] += particle['speed_x']
            particle['y'] += particle['speed_y']

            # Wrap around screen edges
            if particle['x'] < 0:
                particle['x'] = WIDTH
            elif particle['x'] > WIDTH:
                particle['x'] = 0
            if particle['y'] < 0:
                particle['y'] = HEIGHT
            elif particle['y'] > HEIGHT:
                particle['y'] = 0

            # Draw particle
            pygame.draw.circle(self.screen, particle['color'],
                             (int(particle['x']), int(particle['y'])), particle['size'])

    def _render_highlighted_text(self, text, font, color, highlight_color, center_pos, selected=False):
        """Render text with optional highlight effect"""
        if selected:
            # Create pulsing highlight effect
            pulse = (pygame.time.get_ticks() // 100) % 2
            if pulse:
                # Draw highlight background
                rendered_text = font.render(text, True, highlight_color)
                highlight_rect = rendered_text.get_rect(center=center_pos)
                highlight_surface = pygame.Surface((highlight_rect.width + 20, highlight_rect.height + 10))
                highlight_surface.fill((50, 50, 50))
                highlight_surface.set_alpha(100)
                self.screen.blit(highlight_surface, highlight_rect.move(-10, -5))
            else:
                rendered_text = font.render(text, True, color)
        else:
            rendered_text = font.render(text, True, color)

        text_rect = rendered_text.get_rect(center=center_pos)
        self.screen.blit(rendered_text, text_rect)

    def show_start_screen(self):
        # Background
        if self.start_bg:
            self.screen.blit(self.start_bg, (0, 0))
        else:
            self.screen.fill(START_BG_COLOR)

        # Play start music
        if self.start_music and not pygame.mixer.get_busy():
            self.start_music.play(-1)

        # Animated Title
        current_time = pygame.time.get_ticks()
        title_y_offset = 10 * math.sin(current_time * 0.005)
        title_text = self.font_title.render("Stardew Valley Action X", True, TITLE_COLOR)
        title_rect = title_text.get_rect(center=(WIDTH // 2, TITLE_Y_OFFSET + title_y_offset))
        self.screen.blit(title_text, title_rect)

        # Menu options with highlight
        self._render_highlighted_text("Start Game", self.font_menu, MENU_COLOR, TITLE_COLOR,
                                    (WIDTH // 2, START_MENU_Y_OFFSET), self.selected_menu_option == 0)
        self._render_highlighted_text("Quit Game", self.font_menu, MENU_COLOR, TITLE_COLOR,
                                    (WIDTH // 2, QUIT_MENU_Y_OFFSET), self.selected_menu_option == 1)

        # Decorative elements - floating particles
        for i in range(PARTICLE_COUNT_START):
            x = (current_time // 30 + i * 60) % WIDTH
            y = (HEIGHT - 150 - (current_time // 20 + i * 30) % (HEIGHT // 2)) % HEIGHT
            size = 2 + (i % 2)
            pygame.draw.circle(self.screen, PARTICLE_COLOR, (x, y), size)

    def show_death_screen(self):
        # Dark red background
        self.screen.fill(DEATH_BG_COLOR)

        # Death title
        death_text = self.font_title.render("You Died", True, DEATH_TITLE_COLOR)
        death_rect = death_text.get_rect(center=(WIDTH // 2, TITLE_Y_OFFSET))
        self.screen.blit(death_text, death_rect)

        # Stats display
        exp = self.player.exp if self.player else 0
        exp_text = self.font_stats.render(f"Experience Gained: {exp}", True, MENU_COLOR)
        exp_rect = exp_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(exp_text, exp_rect)

        # Restart options
        restart_text = self.font_menu.render("Press R to Restart", True, MENU_COLOR)
        quit_text = self.font_menu.render("Press ESC to Quit", True, MENU_COLOR)

        restart_rect = restart_text.get_rect(center=(WIDTH // 2, DEATH_MENU_Y_OFFSET))
        quit_rect = quit_text.get_rect(center=(WIDTH // 2, DEATH_QUIT_Y_OFFSET))

        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(quit_text, quit_rect)

        # Animated death particles
        self._update_and_draw_death_particles()

    def show_victory_screen(self):
        self.screen.fill((10, 10, 30))
        current_time = pygame.time.get_ticks()

        # Animated title
        title_y_offset = 8 * (pygame.time.get_ticks() % 2000) / 2000.0
        victory_text = self.font_title.render("YOU WIN!", True, (255, 215, 0))
        victory_rect = victory_text.get_rect(center=(WIDTH // 2, HEIGHT // 3 + title_y_offset))
        self.screen.blit(victory_text, victory_rect)

        # Subtitle
        sub_text = self.font_subtitle.render("The Boss has been defeated!", True, (200, 200, 255))
        sub_rect = sub_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(sub_text, sub_rect)

        # Stats
        exp = self.player.exp if self.player else 0
        exp_text = self.font_stats.render(f"Final Experience: {exp}", True, (255, 255, 255))
        exp_rect = exp_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
        self.screen.blit(exp_text, exp_rect)

        # Menu options
        restart_text = self.font_menu.render("Press R to Play Again", True, (255, 255, 255))
        quit_text = self.font_menu.render("Press ESC to Quit", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 140))
        quit_rect = quit_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 200))
        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(quit_text, quit_rect)

        # Floating golden particles
        for i in range(30):
            x = (current_time // 15 + i * 57) % WIDTH
            y = (HEIGHT - ((current_time // 12 + i * 37) % HEIGHT))
            pygame.draw.circle(self.screen, (255, 215, 0), (x, int(y)), 2 + (i % 3))

    def run(self):
        from save_manager import save_game, load_game
        last_time = time.time()
        while True:
            dt = time.time() - last_time
            last_time = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.game_state == 'start':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if self.menu_select_sound:
                                self.menu_select_sound.play()
                            if self.selected_menu_option == 0:  # Start Game
                                if self.start_music:
                                    self.start_music.stop()
                                self.game_state = 'game'
                            elif self.selected_menu_option == 1:  # Quit Game
                                pygame.quit()
                                sys.exit()
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                        elif event.key == pygame.K_UP:
                            if self.menu_move_sound:
                                self.menu_move_sound.play()
                            self.selected_menu_option = (self.selected_menu_option - 1) % 2
                        elif event.key == pygame.K_DOWN:
                            if self.menu_move_sound:
                                self.menu_move_sound.play()
                            self.selected_menu_option = (self.selected_menu_option + 1) % 2

                elif self.game_state == 'death':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self._restart_game()
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()

                elif self.game_state == 'victory':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self._restart_game()
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()

                elif self.show_save_dialog:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_c:
                            self.save_dialog_result = 'c'
                        elif event.key == pygame.K_n:
                            self.save_dialog_result = 'n'

                else:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_b:
                            self.level.toggle_menu()
                        if event.key == pygame.K_m:
                            self.level.toggle_map()
                        # Save game when paused and P is pressed
                        if event.key == pygame.K_p and getattr(self.level, 'game_paused', False):
                            save_game(self.level.get_savable_state())
                    # Mouse wheel to switch weapon
                    if event.type == pygame.MOUSEWHEEL:
                        if self.player and not getattr(self.level, 'game_paused', False):
                            self.player.cycle_weapon(event.y)

            if self.game_state == 'start':
                self.show_start_screen()
                pygame.display.update()
                self.clock.tick(FPS)
                continue

            elif self.game_state == 'death':
                self.show_death_screen()
                pygame.display.update()
                self.clock.tick(FPS)
                continue

            elif self.game_state == 'victory':
                self.show_victory_screen()
                pygame.display.update()
                self.clock.tick(FPS)
                continue

            # Handle save dialog logic
            if self.show_save_dialog:
                self.screen.fill(WATER_COLOR)
                # Draw a rounded rectangle background for the dialog
                dialog_width, dialog_height = 600, 220
                dialog_x = (self.screen.get_width() - dialog_width) // 2
                dialog_y = (self.screen.get_height() - dialog_height) // 2
                dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
                # Shadow (alpha not supported on display surface, use semi-transparent fill)
                shadow_rect = dialog_rect.move(6, 6)
                shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect(), border_radius=24)
                self.screen.blit(shadow_surf, shadow_rect)
                # Main box
                pygame.draw.rect(self.screen, (30, 30, 40), dialog_rect, border_radius=24)
                pygame.draw.rect(self.screen, (255, 215, 0), dialog_rect, 4, border_radius=24)

                # Title
                text1 = self.font_dialog_title.render("Save file detected!", True, (255,255,255))
                self.screen.blit(text1, (dialog_x + (dialog_width - text1.get_width())//2, dialog_y + 30))

                # Instructions
                text2 = self.font_dialog_option.render("Press C to Continue or N for New Game", True, (255,255,0))
                self.screen.blit(text2, (dialog_x + (dialog_width - text2.get_width())//2, dialog_y + 100))

                # Button hints
                c_hint = self.font_dialog_hint.render("[C] Continue", True, (180,255,180))
                n_hint = self.font_dialog_hint.render("[N] New Game", True, (255,180,180))
                self.screen.blit(c_hint, (dialog_x + 80, dialog_y + 160))
                self.screen.blit(n_hint, (dialog_x + dialog_width - n_hint.get_width() - 80, dialog_y + 160))

                pygame.display.update()
                if self.save_dialog_result:
                    if self.save_dialog_result == 'c':
                        loaded_data = load_game('savegame.json')
                        if loaded_data and 'player' in loaded_data:
                            self.player.from_dict(loaded_data['player'])
                    # 'n' = new game: keep existing level as-is
                    self.show_save_dialog = False
                self.clock.tick(FPS)
                continue

            self.screen.fill(WATER_COLOR)
            self.level.run(dt)

            # Check for player death
            if self.player and self.player.health <= 0 and self.game_state != 'death':
                self.game_state = 'death'
                from resource_manager import ResourceManager
                ResourceManager.instance().stop_all_sounds()
                pygame.mixer.music.stop()
                if self.death_sound:
                    self.death_sound.play()

            # Check for victory
            if self.game_state == 'game' and getattr(self.level, '_trigger_victory', False):
                self.game_state = 'victory'
                from resource_manager import ResourceManager
                ResourceManager.instance().stop_all_sounds()
                pygame.mixer.music.stop()

            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == '__main__':
    game = Game()
    game.run()
