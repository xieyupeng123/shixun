import pygame


class ParticleEffect(pygame.sprite.Sprite):
    """Base particle — a small animated visual effect."""
    def __init__(self, pos, color, groups, lifetime=0.5, size=6):
        super().__init__(groups)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect(center=pos)
        self.lifetime = lifetime
        self.elapsed = 0
        self.pos = pygame.math.Vector2(pos)

    def update(self, dt):
        self.elapsed += dt
        alpha = int(255 * (1 - self.elapsed / self.lifetime))
        self.image.set_alpha(max(0, alpha))
        if self.elapsed >= self.lifetime:
            self.kill()


def spawn_hit_particles(pos, groups, count=5):
    """Spawn small particles at pos (for hit feedback)."""
    from random import randint
    for _ in range(count):
        color = (randint(200, 255), randint(100, 180), randint(0, 80))
        p = ParticleEffect(
            (pos[0] + randint(-10, 10), pos[1] + randint(-10, 10)),
            color, groups, lifetime=0.3, size=randint(3, 6))
        p.pos += pygame.math.Vector2(randint(-30, 30), randint(-30, 30)) * 0.5
