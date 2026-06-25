import pygame
from settings import BOSS_PHASE_COLORS, BOSS_PHASE_NAMES

UI_BG = '#222222'
UI_BORDER = '#111111'
HP_COLOR = '#ff4444'
ENERGY_COLOR = '#4488ff'


class UI:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 24)
        self.boss_font = pygame.font.Font(None, 20)

        self.hp_bar_rect = pygame.Rect(10, 10, 200, 16)
        self.energy_bar_rect = pygame.Rect(10, 30, 140, 16)
        self.exp_x = self.display_surface.get_size()[0] - 20
        self.exp_y = self.display_surface.get_size()[1] - 20

    def show_bar(self, current, maximum, rect, color):
        pygame.draw.rect(self.display_surface, UI_BG, rect)
        if maximum > 0:
            ratio = max(current, 0) / maximum
            filled = rect.copy()
            filled.width = rect.width * ratio
            pygame.draw.rect(self.display_surface, color, filled)
        pygame.draw.rect(self.display_surface, UI_BORDER, rect, 2)

    def show_exp(self, exp):
        text = self.font.render(f'EXP: {int(exp)}', False, (255, 255, 255))
        rect = text.get_rect(bottomright=(self.exp_x, self.exp_y))
        pygame.draw.rect(self.display_surface, UI_BG, rect.inflate(16, 10))
        self.display_surface.blit(text, rect)
        pygame.draw.rect(self.display_surface, UI_BORDER,
                         rect.inflate(16, 10), 2)

    def show_boss_hud(self, boss_kills, boss_sprite):
        """Boss health bar + phase at top center."""
        if not boss_sprite or not boss_sprite.alive():
            return
        w = self.display_surface.get_size()[0]
        phase = boss_sprite._current_phase
        color = BOSS_PHASE_COLORS[min(phase, 2)]
        name = BOSS_PHASE_NAMES[min(phase, 2)]

        # Phase label
        pt = self.boss_font.render(
            f'Boss Phase {phase+1}: {name}', False, color)
        self.display_surface.blit(
            pt, pt.get_rect(center=(w // 2, 20)))

        # Boss HP bar
        bw, bh = 300, 14
        br = pygame.Rect((w - bw) // 2, 38, bw, bh)
        pygame.draw.rect(self.display_surface, UI_BG, br)
        ratio = max(boss_sprite.health, 0) / boss_sprite.max_health
        fill = br.copy()
        fill.width = int(bw * ratio)
        pygame.draw.rect(self.display_surface, color, fill)
        pygame.draw.rect(self.display_surface, UI_BORDER, br, 2)

        # HP text
        ht = self.boss_font.render(
            f'{int(boss_sprite.health)}/{boss_sprite.max_health}',
            False, (255, 255, 255))
        self.display_surface.blit(ht, ht.get_rect(center=(w // 2, 58)))

        # Boss kill counter
        kt = self.boss_font.render(
            f'BOSS {boss_kills}/3', False, color)
        self.display_surface.blit(
            kt, kt.get_rect(topright=(w - 10, 10)))

    def display(self, player, boss_kills=0, boss_sprite=None):
        self.show_bar(player.health, player.max_health,
                      self.hp_bar_rect, HP_COLOR)
        self.show_bar(player.energy, player.max_energy,
                      self.energy_bar_rect, ENERGY_COLOR)
        self.show_exp(player.exp)
        if boss_sprite and boss_sprite.alive():
            self.show_boss_hud(boss_kills, boss_sprite)
