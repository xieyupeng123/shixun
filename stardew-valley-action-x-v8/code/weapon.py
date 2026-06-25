import pygame
from support import get_path


class Weapon(pygame.sprite.Sprite):
    """Weapon sprite — loads real weapon graphics."""
    def __init__(self, player, groups, weapon_name='sword'):
        super().__init__(groups)
        self.sprite_type = 'weapon'
        direction = player.status.split('_')[0]

        # Load real weapon graphic
        path = get_path(f'../graphics/weapons/{weapon_name}/{direction}.png')
        self.image = pygame.image.load(path).convert_alpha()

        # Placement around player
        if direction == 'right':
            self.rect = self.image.get_rect(
                midleft=player.rect.midright + pygame.math.Vector2(0, 16))
        elif direction == 'left':
            self.rect = self.image.get_rect(
                midright=player.rect.midleft + pygame.math.Vector2(0, 16))
        elif direction == 'down':
            self.rect = self.image.get_rect(
                midtop=player.rect.midbottom + pygame.math.Vector2(-10, 0))
        else:
            self.rect = self.image.get_rect(
                midbottom=player.rect.midtop + pygame.math.Vector2(-10, 0))
