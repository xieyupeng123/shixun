"""
Centralised sound loading with consistent error handling.
集中式音效加载模块，提供统一的异常处理策略。

【设计意图】
音频文件（.ogg / .wav 等）可能在开发过程中缺失、路径变更或格式不兼容，
直接加载失败会导致游戏崩溃。本模块采用 **防御式编程** 策略，所有加载操作
都包裹在 try/except 中，加载失败时返回 None 或静默忽略，确保音频问题
不会阻塞游戏正常运行。

【降级策略】
- 音效 (load):    文件缺失或损坏 → 返回 None，调用方自行决定是否播放
- 背景音乐 (play_music): 文件缺失或损坏 → 静默跳过，不抛出任何异常
"""
import pygame
from support import get_path


class SoundManager:
    """音效加载器。缓存已加载的音效，加载失败时返回 None（永不崩溃）。

    核心原则：音频是游戏的"锦上添花"而非"必需品"，任何音频加载失败都不应
    影响游戏主流程的运行。本类通过 try/except 捕获 pygame.error 和文件
    不存在异常，确保游戏在缺失音频文件时仍可正常启动和运行。
    """

    def __init__(self, volume=0.5):
        """初始化音效管理器。

        参数：
            volume (float): 所有音效的全局默认音量，范围 0.0~1.0，默认 0.5。

        内部属性：
            self._cache         (dict):   音效缓存，以文件名（str）为键，pygame.mixer.Sound 为值
            self._default_volume (float): 当 load() 未指定 volume 时使用的默认音量
        """
        self._cache = {}
        self._default_volume = volume

    def load(self, name, volume=None):
        """按文件名加载并缓存一个音效（例如 'game_bgm.ogg'、'sword.wav'）。

        加载流程：
            1. 检查 name 是否已在缓存中，若命中则直接返回（避免重复 I/O）
            2. 通过 get_path() 拼接为 '../audio/{name}' 的绝对路径
            3. 创建 pygame.mixer.Sound 对象并设置音量
            4. 存入缓存字典后返回
            5. 若文件不存在或格式错误，捕获异常并返回 None

        降级处理：
            当音频文件缺失或 pygame.mixer 无法解码时，返回 None 而不是抛出异常。
            调用方应检查返回值是否为 None，再决定是否调用 play()。

        参数：
            name   (str):   音频文件名（如 'sword.wav'、'game_bgm.ogg'），路径相对于 audio/ 目录
            volume (float): 该音效的独立音量（可选）。若为 None 则使用 self._default_volume

        返回值：
            pygame.mixer.Sound | None: 成功时返回 Sound 对象，失败时返回 None
        """
        if name in self._cache:
            return self._cache[name]
        try:
            path = get_path(f'../audio/{name}')
            snd = pygame.mixer.Sound(path)
            snd.set_volume(volume if volume is not None else self._default_volume)
            self._cache[name] = snd
            return snd
        except (pygame.error, FileNotFoundError):
            return None

    def play_music(self, name, loops=-1, volume=0.3):
        """启动循环播放的背景音乐。文件缺失时静默忽略（无任何反馈）。

        与 load() 不同，此方法直接播放音乐而不缓存 Sound 对象，
        因为它使用 pygame.mixer.music 模块（专用于长音频流，不占用音效通道）。

        降级处理：
            如果音频文件缺失或无法加载，捕获 pygame.error 并以 pass 静默处理，
            不打印任何错误信息，不中断游戏流程。这是刻意设计的"静默降级"策略。

        参数：
            name   (str):   音频文件名（如 'field_bgm.ogg'），路径相对于 audio/ 目录
            loops  (int):   循环次数。-1 表示无限循环，0 表示不循环，>0 表示循环指定次数
            volume (float): 背景音乐音量，范围 0.0~1.0，默认 0.3
        """
        try:
            path = get_path(f'../audio/{name}')
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops)
        except pygame.error:
            pass
