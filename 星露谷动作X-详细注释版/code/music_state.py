"""
Music state manager — 控制当前播放哪首背景音乐 (BGM)。

【设计意图】
这是一个轻量级的状态管理器，用于在游戏内不同场景间切换背景音乐。
由于游戏主循环和事件系统可能同时读取/写入音乐状态（例如角色进入Boss区域时
触发状态切换，而渲染线程同时读取当前状态以决定播放哪首BGM），
本类将所有访问统一为类方法，避免多路径写入导致的竞态条件（race condition）。

状态定义：
    State 0 = 普通 BGM（探索、对话、日常场景）
    State 1 = Boss BGM（战斗场景）
"""


class MusicState:
    """音乐状态管理类（类级单例模式，所有实例共享同一份 _state）。"""

    _state = 0  # 类变量：当前音乐状态，默认 0（普通 BGM）

    @classmethod
    def get(cls):
        """读取当前音乐状态（线程安全，返回 0 或 1）。

        返回值：
            int: 0 表示普通 BGM，1 表示 Boss BGM。
        """
        return cls._state

    @classmethod
    def set(cls, value):
        """写入音乐状态。只接受 0 和 1，其他值抛出 ValueError。

        参数：
            value (int): 目标状态，必须为 0 或 1。

        异常：
            ValueError: 当传入非 0/1 的值时抛出。
        """
        if value not in (0, 1):
            raise ValueError(f"Invalid music state: {value}")
        cls._state = value

    @classmethod
    def reset(cls):
        """重置为初始状态（游戏重启时调用，确保音乐状态不会从上一局残留）。"""
        cls._state = 0
