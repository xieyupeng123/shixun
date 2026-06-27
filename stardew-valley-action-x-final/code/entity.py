import pygame
from math import sin


class Entity(pygame.sprite.Sprite):
    """Base class for all game entities (Player, Enemy).

    Provides shared behavior for movement, collision, animation frame
    progression, and cooldown tracking. Subclasses override specific
    methods to customize behavior.
    """

    def __init__(self, groups, pos):
        super().__init__(groups)
        self.frame_index = 0
        self.animation_speed = 4
        self.direction = pygame.math.Vector2()

    # ── Movement & Collision ──────────────────────────────────────────

    def move(self, speed, pos, dt):
        self.pos = pos

        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        # horizontal movement
        self.pos.x += self.direction.x * speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('horizontal')

        # vertical movement
        self.pos.y += self.direction.y * speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision('vertical')

    def collision(self, direction):
        for sprite in self.obstacle_sprites.sprites():
            if hasattr(sprite, 'hitbox'):
                if sprite.hitbox.colliderect(self.hitbox):
                    if direction == 'horizontal':
                        if self.direction.x > 0:  # moving right
                            self.hitbox.right = sprite.hitbox.left
                        if self.direction.x < 0:  # moving left
                            self.hitbox.left = sprite.hitbox.right
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx

                    if direction == 'vertical':
                        if self.direction.y < 0:  # moving up
                            self.hitbox.top = sprite.hitbox.bottom
                        if self.direction.y > 0:  # moving down
                            self.hitbox.bottom = sprite.hitbox.top
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery

    # ── Animation ─────────────────────────────────────────────────────

    def animate(self, dt):
        """Advance animation frame index. Sets self.image to current frame.

        Subclasses should call super().animate(dt) then apply their own
        modifications (rect repositioning, tinting, alpha).
        """
        animation = self.animations[self.status]
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(animation):
            self.frame_index = 0
        self.image = animation[int(self.frame_index)]

    # ── Utility ───────────────────────────────────────────────────────

    def wave_value(self):
        """Returns 255 or 0 based on sine wave (used for flicker effect).
        Fast flicker (~0.25s cycle) so enemy remains clearly visible during
        invulnerability while still providing visual feedback.
        """
        value = sin(pygame.time.get_ticks() / 40)
        if value >= 0:
            return 255
        return 0
