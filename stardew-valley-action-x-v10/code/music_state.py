"""
Music state manager — controls which BGM is active.
State 0 = normal BGM, State 1 = boss BGM.
All access goes through get()/set()/reset() to prevent race conditions.
"""


class MusicState:
    _state = 0

    @classmethod
    def get(cls):
        """Read current music state (0 or 1)."""
        return cls._state

    @classmethod
    def set(cls, value):
        """Write music state. Only 0 and 1 are valid."""
        if value not in (0, 1):
            raise ValueError(f"Invalid music state: {value}")
        cls._state = value

    @classmethod
    def reset(cls):
        """Reset to initial state (called on game restart)."""
        cls._state = 0
