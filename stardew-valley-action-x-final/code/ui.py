import pygame
from settings import UI_FONT, UI_FONT_SIZE, HEALTH_BAR_WIDTH, BAR_HEIGHT, ENERGY_BAR_WIDTH, weapon_data, magic_data, UI_BG_COLOR, UI_BORDER_COLOR, TEXT_COLOR, UI_BORDER_COLOR_ACTIVE, HEALTH_COLOR, ENERGY_COLOR, ITEM_BOX_SIZE, monster_data, BOSS_PHASE_DATA
from resource_manager import ResourceManager


class UI:
    def __init__(self):
        res = ResourceManager.instance()

        # general
        self.display_surface = pygame.display.get_surface()
        self.font = res.get_font(UI_FONT, UI_FONT_SIZE)

        # bar setup
        self.health_bar_rect = pygame.Rect(
            10, 10, HEALTH_BAR_WIDTH, BAR_HEIGHT)
        self.energy_bar_rect = pygame.Rect(
            10, 34, ENERGY_BAR_WIDTH, BAR_HEIGHT)

        # convert weapon dictionary (cached via ResourceManager)
        self.weapon_graphics = []
        for weapon in weapon_data.values():
            path = weapon['graphic']
            weapon_surf = res.get_image(path)
            self.weapon_graphics.append(weapon_surf)

        # convert magic dictionary (cached via ResourceManager)
        self.magic_graphics = []
        for magic in magic_data.values():
            path = magic['graphic']
            magic_surf = res.get_image(path)
            self.magic_graphics.append(magic_surf)

    def show_bar(self, current, max_amount, bg_rect, color):
        # draw bg
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_rect)

        # converting stat to pixel
        ratio = current / max(max_amount, 1)
        current_width = bg_rect.width * ratio
        current_rect = bg_rect.copy()
        current_rect.width = current_width

        # drawing the bar
        pygame.draw.rect(self.display_surface, color, current_rect)
        pygame.draw.rect(self.display_surface,
                         UI_BORDER_COLOR, bg_rect, 3)

    def show_exp(self, exp):
        text_surf = self.font.render(str(int(exp)), False, TEXT_COLOR)
        x = self.display_surface.get_size()[0] - 20
        y = self.display_surface.get_size()[1] - 20
        text_rect = text_surf.get_rect(bottomright=(x, y))

        pygame.draw.rect(self.display_surface, UI_BG_COLOR,
                         text_rect.inflate(20, 20))
        self.display_surface.blit(text_surf, text_rect)
        pygame.draw.rect(self.display_surface, UI_BORDER_COLOR,
                         text_rect.inflate(20, 20), 3)

    def selection_box(self, left, top, has_switched):
        bg_rect = pygame.Rect(left, top, ITEM_BOX_SIZE, ITEM_BOX_SIZE)
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_rect)

        if has_switched:
            pygame.draw.rect(self.display_surface,
                             UI_BORDER_COLOR_ACTIVE, bg_rect, 3)
        else:
            pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, bg_rect, 3)
        return bg_rect

    def weapon_overlay(self, weapon_index, has_switched):
        bg_rect = self.selection_box(10, 630, has_switched)
        weapon_surf = self.weapon_graphics[weapon_index]
        weapon_rect = weapon_surf.get_rect(center=bg_rect.center)

        self.display_surface.blit(weapon_surf, weapon_rect)

    def magic_overlay(self, magic_index, has_switched):
        bg_rect = self.selection_box(80, 635, has_switched)
        magic_surf = self.magic_graphics[magic_index]
        magic_rect = magic_surf.get_rect(center=bg_rect.center)

        self.display_surface.blit(magic_surf, magic_rect)

    def show_invincible_status(self, player):
        """Display INVINCIBLE indicator at top center when active."""
        if not player.invincible:
            return
        inv_font = ResourceManager.instance().get_font(UI_FONT, 28)
        text = "INVINCIBLE"
        text_surf = inv_font.render(text, False, (255, 215, 0))
        text_rect = text_surf.get_rect(midtop=(self.display_surface.get_size()[0] // 2, 10))
        bg_rect = text_rect.inflate(30, 10)
        pygame.draw.rect(self.display_surface, (0, 0, 0, 180), bg_rect)
        pygame.draw.rect(self.display_surface, (255, 215, 0), bg_rect, 2)
        self.display_surface.blit(text_surf, text_rect)

    def show_boss_status(self, boss_kills):
        """Display boss phase progress at top-right."""
        if boss_kills <= 0:
            return
        boss_font = ResourceManager.instance().get_font(UI_FONT, 22)
        phase_colors = {1: (255, 255, 255), 2: (180, 80, 220), 3: (255, 40, 40)}
        color = phase_colors.get(boss_kills + 1, (255, 255, 255))
        text = f"BOSS {boss_kills}/3"
        text_surf = boss_font.render(text, False, color)
        x = self.display_surface.get_size()[0] - text_surf.get_width() - 20
        text_rect = text_surf.get_rect(topleft=(x, 12))
        bg_rect = text_rect.inflate(20, 10)
        pygame.draw.rect(self.display_surface, (0, 0, 0, 180), bg_rect)
        pygame.draw.rect(self.display_surface, color, bg_rect, 2)
        self.display_surface.blit(text_surf, text_rect)

    def show_boss_phase_hud(self, boss_sprite):
        """Display current boss phase at top-center if boss is alive."""
        if not boss_sprite or not boss_sprite.alive():
            return
        phase = getattr(boss_sprite, 'boss_phase', 1)
        phase_names = {1: 'Phase 1 - Normal', 2: 'Phase 2 - Enraged', 3: 'Phase 3 - Final'}
        phase_colors = {1: (255, 255, 255), 2: (255, 150, 150), 3: (200, 100, 255)}
        hud_font = ResourceManager.instance().get_font(UI_FONT, 22)
        text = f"BOSS: {phase_names.get(phase, '?')}"
        text_surf = hud_font.render(text, False, phase_colors.get(phase, (255, 255, 255)))
        text_rect = text_surf.get_rect(midtop=(self.display_surface.get_size()[0] // 2, 40))
        bg_rect = text_rect.inflate(20, 6)
        pygame.draw.rect(self.display_surface, (0, 0, 0, 180), bg_rect)
        self.display_surface.blit(text_surf, text_rect)

    def show_boss_health_bar(self, boss_sprite):
        """Display boss health bar below the phase text if boss is alive."""
        if not boss_sprite or not boss_sprite.alive():
            return
        phase = getattr(boss_sprite, 'boss_phase', 1)
        max_hp = int(monster_data['raccoon']['health'] * BOSS_PHASE_DATA[phase]['stat_mult'])
        current_hp = max(0, boss_sprite.health)
        sw = self.display_surface.get_size()[0]

        # Bar dimensions
        bar_w = 300
        bar_h = 18
        bar_x = (sw - bar_w) // 2
        bar_y = 70

        # Background
        pygame.draw.rect(self.display_surface, (0, 0, 0, 180),
                         pygame.Rect(bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4))

        # Health fill
        ratio = current_hp / max_hp if max_hp > 0 else 0
        fill_w = int(bar_w * ratio)
        phase_bar_colors = {1: (200, 50, 50), 2: (255, 120, 120), 3: (180, 80, 220)}
        bar_color = phase_bar_colors.get(phase, (200, 50, 50))
        pygame.draw.rect(self.display_surface, bar_color,
                         pygame.Rect(bar_x, bar_y, fill_w, bar_h))

        # Border
        pygame.draw.rect(self.display_surface, (255, 255, 255),
                         pygame.Rect(bar_x, bar_y, bar_w, bar_h), 2)

        # HP text
        hp_font = ResourceManager.instance().get_font(UI_FONT, 16)
        hp_text = f"{current_hp} / {max_hp}"
        hp_surf = hp_font.render(hp_text, False, (255, 255, 255))
        hp_rect = hp_surf.get_rect(center=(sw // 2, bar_y + bar_h // 2))
        self.display_surface.blit(hp_surf, hp_rect)

    def display(self, player, boss_kills=0, boss_sprite=None):
        self.show_bar(
            player.health, player.stats['health'], self.health_bar_rect, HEALTH_COLOR)
        self.show_bar(
            player.energy, player.stats['energy'], self.energy_bar_rect, ENERGY_COLOR)

        self.show_exp(player.exp)

        self.weapon_overlay(player.weapon_index, not player.can_switch_weapon)
        self.magic_overlay(player.magic_index, not player.can_switch_magic)

        # Invincible state indicator
        self.show_invincible_status(player)

        # Boss indicators
        self.show_boss_status(boss_kills)
        self.show_boss_phase_hud(boss_sprite)
        self.show_boss_health_bar(boss_sprite)
