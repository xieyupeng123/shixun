import pygame
from support import import_folder
from random import choice


class AnimationPlayer:
    def __init__(self):
        self.frames = {
            'flame': import_folder('../graphics/particles/flame/frames'),
            'aura': import_folder('../graphics/particles/aura'),
            'heal': import_folder('../graphics/particles/heal/frames'),
            'claw': import_folder('../graphics/particles/claw'),
            'slash': import_folder('../graphics/particles/slash'),
            'sparkle': import_folder('../graphics/particles/sparkle'),
            'leaf_attack': import_folder('../graphics/particles/leaf_attack'),
            'thunder': import_folder('../graphics/particles/thunder'),
            'squid': import_folder('../graphics/particles/smoke_orange'),
            'raccoon': import_folder('../graphics/particles/raccoon'),
            'spirit': import_folder('../graphics/particles/nova'),
            'bamboo': import_folder('../graphics/particles/bamboo'),
            'leaf': (
                import_folder('../graphics/particles/leaf1'),
                import_folder('../graphics/particles/leaf2'),
                import_folder('../graphics/particles/leaf3'),
                import_folder('../graphics/particles/leaf4'),
                import_folder('../graphics/particles/leaf5'),
                import_folder('../graphics/particles/leaf6'),
            ),
        }

    def create_grass_particles(self, pos, groups):
        ParticleEffect(pos, choice(self.frames['leaf']), groups)

    def create_particles(self, animation_type, pos, groups):
        if animation_type in self.frames:
            ParticleEffect(pos, self.frames[animation_type], groups)

    def create_exp_particles(self, pos, target_pos, groups, amount=5):
        from random import uniform
        for _ in range(amount):
            offset = pygame.math.Vector2(uniform(-10, 10), uniform(-10, 10))
            spawn = (pos[0] + offset.x, pos[1] + offset.y)
            MovingParticleEffect(spawn, self.frames['sparkle'], groups,
                                 target_pos=target_pos, speed=200)


class ParticleEffect(pygame.sprite.Sprite):
    def __init__(self, pos, animation_frames, groups):
        super().__init__(groups)
        self.frame_index = 0
        self.animation_speed = 15
        self.frames = animation_frames
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)

    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.frames):
            self.kill()
        else:
            self.image = self.frames[int(self.frame_index)]

    def update(self, dt):
        self.animate(dt)


class MovingParticleEffect(ParticleEffect):
    """Particle that flies toward a target (EXP orbs)."""
    def __init__(self, pos, frames, groups, target_pos=(0, 0), speed=200):
        super().__init__(pos, frames, groups)
        self.target_pos = pygame.math.Vector2(target_pos)
        self.pos_vec = pygame.math.Vector2(pos)
        self.speed = speed
        self.lifetime = 1.5
        self.elapsed = 0

    def update(self, dt):
        direction = self.target_pos - self.pos_vec
        dist = direction.length()
        if dist > 0:
            move = min(self.speed * dt, dist)
            self.pos_vec += direction.normalize() * move
            self.rect.center = (round(self.pos_vec.x), round(self.pos_vec.y))
        self.elapsed += dt
        self.animate(dt)
        if dist < 16 or self.elapsed > self.lifetime:
            self.kill()


class FloatingText(pygame.sprite.Sprite):
    """Rising text that fades out."""
    def __init__(self, text, pos, groups, color=(255, 255, 100), duration=1.2):
        super().__init__(groups)
        self.font = pygame.font.Font(None, 22)
        self.color = color
        self.image = self.font.render(text, False, color)
        self.rect = self.image.get_rect(center=pos)
        self.start_y = pos[1]
        self.duration = duration
        self.elapsed = 0

    def update(self, dt):
        self.elapsed += dt
        progress = min(self.elapsed / self.duration, 1.0)
        self.rect.center = (self.rect.centerx,
                            self.start_y - 30 * progress)
        self.image.set_alpha(int(255 * (1 - progress)))
        if self.elapsed >= self.duration:
            self.kill()
