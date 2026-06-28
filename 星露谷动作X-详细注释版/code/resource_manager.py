"""
Centralized resource loading with caching.
集中式资源加载模块，自带缓存机制。

【设计意图】
避免重复的磁盘 I/O。游戏中大量使用图片、音效和字体资源，如果每次使用都从
磁盘读取，会显著拖慢帧率。本模块采用 **单例模式** + **字典缓存** 的方式，
确保同一资源在内存中只保留一份副本，后续访问直接从缓存返回。

【缓存策略】
- 图片 (images):   以文件路径为键，pygame.Surface 为值
- 音效 (sounds):   以文件路径为键，pygame.mixer.Sound 为值
- 字体 (fonts):    以 (路径, 字号) 元组为键，pygame.font.Font 为值
- 文件夹图片集:    以 ('folder', 路径) 特殊元组为键，避免与单张图片冲突
"""
import pygame
from support import get_path


class ResourceManager:
    """全局资源缓存管理器（单例模式）。

    通过 ResourceManager.instance() 获取全局唯一实例，保证整个游戏生命周期中
    所有资源只加载一次，不产生重复内存开销。

    单例设计说明：
        使用类变量 _singleton 持有唯一实例，instance() 类方法负责懒加载
        （lazy initialization）—— 首次调用时创建实例，后续调用直接返回已有实例。
    """

    _singleton = None  # 类变量：持有全局唯一实例，初始为 None

    @classmethod
    def instance(cls):
        """获取 ResourceManager 全局唯一实例（懒加载单例）。

        首次调用时创建实例并存入 _singleton，后续调用直接返回缓存中的实例。

        返回值：
            ResourceManager: 全局唯一的资源管理器实例。
        """
        if cls._singleton is None:
            cls._singleton = cls()
        return cls._singleton

    def __init__(self):
        """初始化三个私有缓存字典，分别存储图片、音效和字体资源。"""
        self._images = {}    # 图片缓存:  路径 (str)        -> pygame.Surface
        self._sounds = {}    # 音效缓存:  路径 (str)        -> pygame.mixer.Sound
        self._fonts = {}     # 字体缓存:  (路径, 字号) 元组 -> pygame.font.Font

    def get_image(self, path):
        """加载并缓存一张图片。路径相对于 code/ 目录（例如 '../graphics/test/player.png'）。

        缓存逻辑：
            1. 检查 path 是否已在 self._images 中
            2. 若未缓存，通过 get_path() 解析为绝对路径，用 pygame.image.load() 加载
            3. 调用 convert_alpha() 转换为硬件加速表面，保留透明通道
            4. 存入缓存字典后返回

        参数：
            path (str): 图片文件路径（相对于 code/ 目录）。

        返回值：
            pygame.Surface: 已加载并缓存的图片表面。
        """
        if path not in self._images:
            full_path = get_path(path)
            self._images[path] = pygame.image.load(full_path).convert_alpha()
        return self._images[path]

    def get_sound(self, path, volume=0.5):
        """加载并缓存一个音效。返回 pygame.mixer.Sound 对象。

        缓存逻辑：
            1. 检查 path 是否已在 self._sounds 中
            2. 若未缓存，通过 get_path() 解析绝对路径，创建 Sound 对象
            3. 设置默认音量（通过 volume 参数控制，默认 0.5）
            4. 存入缓存字典后返回

        参数：
            path   (str):  音效文件路径（相对于 code/ 目录）。
            volume (float): 默认音量，范围 0.0~1.0，默认 0.5。

        返回值：
            pygame.mixer.Sound: 已加载并设置音量的音效对象。
        """
        if path not in self._sounds:
            full_path = get_path(path)
            snd = pygame.mixer.Sound(full_path)
            snd.set_volume(volume)
            self._sounds[path] = snd
        return self._sounds[path]

    def get_font(self, path, size):
        """加载并缓存一个字体。返回 pygame.font.Font 对象。

        缓存逻辑：
            1. 以 (path, size) 元组为键，检查是否已在 self._fonts 中
            2. 若未缓存，通过 get_path() 解析绝对路径
            3. 若 path 为 None，则使用 pygame 默认字体
            4. 创建 Font 对象后存入缓存字典

        参数：
            path (str):  字体文件路径。如果为 None，则使用系统默认字体。
            size (int):  字体大小（像素）。

        返回值：
            pygame.font.Font: 已加载并缓存的字体对象。
        """
        key = (path, size)
        if key not in self._fonts:
            full_path = get_path(path) if path else None
            self._fonts[key] = pygame.font.Font(full_path, size)
        return self._fonts[key]

    def get_folder_images(self, path):
        """加载指定文件夹内的所有图片（按文件名排序）。返回 pygame.Surface 列表。

        缓存逻辑：
            - 使用 ('folder', path) 特殊元组作为缓存键，与 get_image() 的单张图片缓存隔离
            - 首次调用时从 support.import_folder() 批量导入
            - 后续调用直接返回已排序的 Surface 列表

        参数：
            path (str): 图片文件夹路径（相对于 code/ 目录）。

        返回值：
            list[pygame.Surface]: 文件夹内所有图片按文件名排序后的表面列表。
        """
        cache_key = ('folder', path)
        if cache_key not in self._images:
            from support import import_folder
            self._images[cache_key] = import_folder(path)
        return self._images[cache_key]

    def stop_all_sounds(self):
        """停止所有已缓存的音效对象。游戏重启时调用，确保上一局的音效不会残留。

        遍历 self._sounds 字典中的所有 Sound 对象，逐个调用其 stop() 方法，
        相当于静默清理音频状态，避免新旧音效混叠。
        """
        for snd in self._sounds.values():
            snd.stop()
