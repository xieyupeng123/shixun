import pygame
from support import get_path


class Upgrade:
    def __init__(self, player):
        self.display_surface = pygame.display.get_surface()
        self.player = player
        self.attr_names = list(player.upgrade_levels.keys())
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
            full_w = self.display_surface.get_size()[0]
            inc = full_w // self.attr_count
            left = (i * inc) + (inc - self.width) // 2
            top = self.display_surface.get_size()[1] * 0.1
            self.items.append(UpgradeItem(
                left, top, self.width, self.height, i, self.font))

    def input(self):
        keys = pygame.key.get_pressed()
        if not self.can_move:
            return
        if keys[pygame.K_RIGHT] and self.selection_index < self.attr_count - 1:
            self.selection_index += 1
            self.can_move = False
            self.selection_time = pygame.time.get_ticks()
        elif keys[pygame.K_LEFT] and self.selection_index >= 1:
            self.selection_index -= 1
            self.can_move = False
            self.selection_time = pygame.time.get_ticks()
        if keys[pygame.K_UP]:
            self.can_move = False
            self.selection_time = pygame.time.get_ticks()
            self.items[self.selection_index].upgrade(self.player)
        if keys[pygame.K_DOWN]:
            self.can_move = False
            self.selection_time = pygame.time.get_ticks()
            self.items[self.selection_index].downgrade(self.player)

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
            cost = self.player.upgrade_cost(name)
            item.draw(self.display_surface, self.selection_index,
                      name, value, max_val, cost)

    def _get_value(self, idx):
        return [self.player.max_health, self.player.max_energy,
                self.player.attack_damage, 10, int(self.player.speed)][idx]

    def _get_max(self, idx):
        return [600, 300, 40, 30, 720][idx]


class UpgradeItem:
    def __init__(self, left, top, w, h, index, font):
        self.rect = pygame.Rect(left, top, w, h)
        self.index = index
        self.font = font

    def upgrade(self, player):
        names = list(player.upgrade_levels.keys())
        name = names[self.index]
        cost = player.upgrade_cost(name)
        if player.exp >= cost:
            player.exp -= cost
            player.upgrade_levels[name] += 1
            self._apply(player, name, 1)

    def downgrade(self, player):
        names = list(player.upgrade_levels.keys())
        name = names[self.index]
        if player.upgrade_levels[name] <= 0:
            return
        cost = player.upgrade_cost(name)
        player.exp += int(cost / 1.4)
        player.upgrade_levels[name] -= 1
        self._apply(player, name, -1)

    def _apply(self, player, name, direction):
        factor = 1.2 if direction > 0 else 1 / 1.2
        if name == 'health':
            player.max_health = max(50, int(player.max_health * factor))
            player.health = player.max_health
        elif name == 'energy':
            player.max_energy = max(20, int(player.max_energy * factor))
            player.energy = player.max_energy
        elif name == 'attack':
            player.attack_damage = max(
                5, int(player.attack_damage * factor))
        elif name == 'speed':
            player.speed = max(50, int(player.speed * factor))

    def draw(self, surface, sel_idx, name, value, max_val, cost):
        selected = self.index == sel_idx
        bg = (60, 60, 60) if selected else (30, 30, 30)
        pygame.draw.rect(surface, bg, self.rect)
        pygame.draw.rect(surface, (80, 80, 80), self.rect, 3)

        # Name
        ns = self.font.render(name, False,
                              (255, 255, 255) if selected else (180, 180, 180))
        surface.blit(ns, ns.get_rect(
            midtop=self.rect.midtop + pygame.math.Vector2(0, 15)))

        # Bar
        bar_top = self.rect.midtop[1] + 60
        bar_bot = self.rect.midbottom[1] - 50
        bar_h = bar_bot - bar_top
        ratio = min(value / max(max_val, 1), 1.0)
        fill_h = int(bar_h * ratio)
        bx = self.rect.centerx - 15
        pygame.draw.line(surface, (200, 200, 200),
                         (bx + 15, bar_top), (bx + 15, bar_bot), 5)
        pygame.draw.rect(surface, (255, 215, 0) if selected else (150, 150, 150),
                         (bx, bar_bot - fill_h, 30, fill_h))

        # Value
        vs = self.font.render(str(value), False, (255, 255, 255))
        surface.blit(vs, vs.get_rect(center=(bx + 15, bar_top - 12)))

        # Cost
        cs = self.font.render(f'{cost} XP', False,
                              (255, 255, 100) if selected else (180, 180, 100))
        surface.blit(cs, cs.get_rect(
            midbottom=self.rect.midbottom - pygame.math.Vector2(0, 20)))
