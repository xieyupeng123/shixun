import pygame
from support import get_path


class Upgrade:
    def __init__(self, player):
        self.display_surface = pygame.display.get_surface()
        self.player = player
        self.attr_names = ['health', 'energy', 'attack', 'magic', 'speed']
        self.attr_count = len(self.attr_names)
        self.font = pygame.font.Font(get_path('../font/joystix.ttf'), 16)

        self.width = self.display_surface.get_size()[0] // (self.attr_count + 1)
        self.height = self.display_surface.get_size()[1] * 0.8
        self.items = []
        self._create_items()

        self.selection_index = 0
        self.selection_time = None
        self.can_move = True

    def _create_items(self):
        self.items = []
        for i in range(self.attr_count):
            left = (i * (self.display_surface.get_size()[0] // self.attr_count)
                    + (self.display_surface.get_size()[0] // self.attr_count - self.width) // 2)
            top = self.display_surface.get_size()[1] * 0.1
            self.items.append(
                UpgradeItem(left, top, self.width, self.height, i, self.font))

    def input(self):
        keys = pygame.key.get_pressed()
        if self.can_move:
            if keys[pygame.K_RIGHT] and self.selection_index < self.attr_count - 1:
                self.selection_index += 1
                self.can_move = False
                self.selection_time = pygame.time.get_ticks()
            elif keys[pygame.K_LEFT] and self.selection_index >= 1:
                self.selection_index -= 1
                self.can_move = False
                self.selection_time = pygame.time.get_ticks()
            if keys[pygame.K_SPACE]:
                self.can_move = False
                self.selection_time = pygame.time.get_ticks()
                self.items[self.selection_index].upgrade(self.player)

    def _cooldown(self):
        if not self.can_move and self.selection_time:
            if pygame.time.get_ticks() - self.selection_time >= 300:
                self.can_move = True

    def display(self):
        self.input()
        self._cooldown()
        for idx, item in enumerate(self.items):
            name = self.attr_names[idx]
            value = self._get_value(idx)
            max_val = self._get_max(idx)
            cost = self._get_cost(idx)
            item.draw(self.display_surface, self.selection_index,
                      name, value, max_val, cost)

    def _get_value(self, idx):
        return [self.player.max_health, self.player.max_energy,
                self.player.attack_damage, 10, int(self.player.speed)][idx]

    def _get_max(self, idx):
        return [600, 300, 40, 30, 720][idx]

    def _get_cost(self, idx):
        base = [100, 100, 80, 120, 60]
        level = [self.player.upgrade_levels[n] for n in self.attr_names]
        return base[idx] + level[idx] * 50


class UpgradeItem:
    def __init__(self, left, top, w, h, index, font):
        self.rect = pygame.Rect(left, top, w, h)
        self.index = index
        self.font = font

    def upgrade(self, player):
        names = ['health', 'energy', 'attack', 'magic', 'speed']
        name = names[self.index]
        cost = player.upgrade_cost(name)
        if player.exp >= cost:
            player.exp -= cost
            player.upgrade_levels[name] += 1
            if name == 'health':
                player.max_health = int(player.max_health * 1.2)
                player.health = player.max_health
            elif name == 'energy':
                player.max_energy = int(player.max_energy * 1.2)
                player.energy = player.max_energy
            elif name == 'attack':
                player.attack_damage = int(player.attack_damage * 1.2)
            elif name == 'speed':
                player.speed = int(player.speed * 1.15)

    def draw(self, surface, sel_idx, name, value, max_val, cost):
        selected = self.index == sel_idx
        bg = (60, 60, 60) if selected else (30, 30, 30)
        pygame.draw.rect(surface, bg, self.rect)
        pygame.draw.rect(surface, (80, 80, 80), self.rect, 3)

        # name
        name_surf = self.font.render(name, False,
                                     (255, 255, 255) if selected else (180, 180, 180))
        nr = name_surf.get_rect(
            midtop=self.rect.midtop + pygame.math.Vector2(0, 15))
        surface.blit(name_surf, nr)

        # bar
        bar_top = self.rect.midtop[1] + 60
        bar_bot = self.rect.midbottom[1] - 50
        bar_h = bar_bot - bar_top
        ratio = min(value / max(max_val, 1), 1.0)
        bar_fill_h = int(bar_h * ratio)
        bar_x = self.rect.centerx - 15
        pygame.draw.line(surface, (200, 200, 200),
                         (bar_x + 15, bar_top), (bar_x + 15, bar_bot), 5)
        pygame.draw.rect(surface, (255, 215, 0) if selected else (150, 150, 150),
                         (bar_x, bar_bot - bar_fill_h, 30, bar_fill_h))

        # value
        val_surf = self.font.render(f'{value}', False, (255, 255, 255))
        vr = val_surf.get_rect(
            center=(bar_x + 15, bar_top - 12))
        surface.blit(val_surf, vr)

        # cost
        cost_surf = self.font.render(f'{cost} XP', False,
                                     (255, 255, 100) if selected else (180, 180, 100))
        cr = cost_surf.get_rect(
            midbottom=self.rect.midbottom - pygame.math.Vector2(0, 20))
        surface.blit(cost_surf, cr)
