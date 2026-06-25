import pygame

UI_BG = '#222222'
UI_BORDER = '#111111'
HP_COLOR = '#ff4444'
ENERGY_COLOR = '#4488ff'
EXP_COLOR = '#44aaff'


class UI:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 24)

        self.hp_bar_rect = pygame.Rect(10, 10, 200, 16)
        self.energy_bar_rect = pygame.Rect(10, 30, 140, 16)
        self.exp_x = self.display_surface.get_size()[0] - 20
        self.exp_y = self.display_surface.get_size()[1] - 20

    def show_bar(self, current, maximum, rect, color):
        pygame.draw.rect(self.display_surface, UI_BG, rect)
        if maximum > 0:
            ratio = current / maximum
            filled = rect.copy()
            filled.width = rect.width * ratio
            pygame.draw.rect(self.display_surface, color, filled)
        pygame.draw.rect(self.display_surface, UI_BORDER, rect, 2)

    def show_exp(self, exp):
        text = self.font.render(f'EXP: {int(exp)}', False, (255, 255, 255))
        rect = text.get_rect(bottomright=(self.exp_x, self.exp_y))
        pygame.draw.rect(self.display_surface, UI_BG, rect.inflate(16, 10))
        self.display_surface.blit(text, rect)
        pygame.draw.rect(self.display_surface, UI_BORDER, rect.inflate(16, 10), 2)

    def display(self, player):
        self.show_bar(player.health, player.max_health,
                      self.hp_bar_rect, HP_COLOR)
        self.show_bar(player.energy, player.max_energy,
                      self.energy_bar_rect, ENERGY_COLOR)
        self.show_exp(player.exp)
