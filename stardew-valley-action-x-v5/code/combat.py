"""Combat calculations — damage, knockback, resistances."""


def calculate_damage(attacker_damage, target_resistance=0):
    """Calculate final damage after resistance."""
    return max(1, attacker_damage - target_resistance)


def knockback_vector(attacker_pos, target_pos, force=20):
    """Return knockback direction vector from attacker to target."""
    import pygame
    vec = pygame.math.Vector2(target_pos) - pygame.math.Vector2(attacker_pos)
    if vec.length() > 0:
        vec = vec.normalize() * force
    return vec


def is_critical(base_chance=0.1):
    """Roll for critical hit. Returns True if crit."""
    import random
    return random.random() < base_chance
