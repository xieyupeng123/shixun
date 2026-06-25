import pygame


class Weapon(pygame.sprite.Sprite):
    """Weapon sprite that appears during player attack."""
    def __init__(self, player, groups):
        super().__init__(groups)
        self.sprite_type = 'weapon'
        direction = player.status.split('_')[0]

        # Create weapon graphic based on direction
        if direction in ('up', 'down'):
            w, h = 10, 36
        else:
            w, h = 36, 10
        self.image = pygame.Surface((w, h))
        self.image.fill((220, 220, 240))
        self.image.set_colorkey((0, 0, 0))

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
        else:  # up
            self.rect = self.image.get_rect(
                midbottom=player.rect.midtop + pygame.math.Vector2(-10, 0))
