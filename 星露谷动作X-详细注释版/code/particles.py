# -*- coding: utf-8 -*-
"""
particles.py — 粒子系统与动画播放器

定义以下核心类：
    - AnimationPlayer：粒子播放器，管理所有粒子类型的帧资源，提供创建各类粒子的接口
    - ParticleEffect：基础粒子特效精灵，播放完动画帧后自动销毁
    - MovingParticleEffect：可移动粒子特效（继承 ParticleEffect），追踪目标位置移动
    - FloatingText：浮动文字精灵，在指定位置显示文本并自动上升淡出

支持的粒子类型包括：
    魔法类：flame（火焰）、aura（光环）、heal（治疗）
    攻击类：claw（爪击）、slash（斩击）、sparkle（闪光）、leaf_attack（叶攻击）、thunder（雷电）
    死亡类：squid（章鱼）、raccoon（浣熊）、spirit（精灵）、bamboo（竹子）
    叶子类：leaf（多种叶片及镜像变体）
"""

import pygame
from support import get_path, import_folder
from random import choice


class AnimationPlayer:
    """
    粒子动画播放器，是粒子系统的统一入口。

    职责：
        - 在初始化时从磁盘加载所有粒子类型的帧序列
        - 提供 create_particles()、create_exp_particles()、create_grass_particles() 等接口
        - 提供 create_floating_text() 用于显示飘浮文字（如经验值提示）

    每种粒子类型对应 frames 字典中的一个键，值为多帧图像列表。
    'leaf' 类型特殊，是一个包含多组叶片帧及其镜像变体的元组。
    """

    def __init__(self):
        """
        初始化所有粒子类型的帧序列。

        从 ../graphics/particles/ 目录下按子文件夹加载图像序列。
        所有类型按功能分组：
            - magic（魔法特效）：flame、aura、heal
            - attacks（攻击特效）：claw、slash、sparkle、leaf_attack、thunder
            - monster deaths（怪物死亡特效）：squid、raccoon、spirit、bamboo
            - leaf（叶片粒子，特殊处理）：6 种叶片 + 6 种镜像变体
        """
        self.frames = {
            # ── 魔法粒子 ──────────────────────────────────────────────
            'flame': import_folder('../graphics/particles/flame/frames'),   # 火焰魔法弹
            'aura': import_folder('../graphics/particles/aura'),            # 治疗光环
            'heal': import_folder('../graphics/particles/heal/frames'),     # 治疗光柱/光点

            # ── 攻击粒子 ──────────────────────────────────────────────
            'claw': import_folder('../graphics/particles/claw'),            # 爪击特效
            'slash': import_folder('../graphics/particles/slash'),          # 斩击特效
            'sparkle': import_folder('../graphics/particles/sparkle'),      # 闪光/星点（也用作经验球）
            'leaf_attack': import_folder('../graphics/particles/leaf_attack'),  # 叶片攻击
            'thunder': import_folder('../graphics/particles/thunder'),      # 雷电特效

            # ── 怪物死亡粒子 ──────────────────────────────────────────
            'squid': import_folder('../graphics/particles/smoke_orange'),    # 章鱼/乌贼死亡（橙色烟雾）
            'raccoon': import_folder('../graphics/particles/raccoon'),       # 浣熊死亡
            'spirit': import_folder('../graphics/particles/nova'),           # 精灵死亡（新星爆发）
            'bamboo': import_folder('../graphics/particles/bamboo'),         # 竹子怪物死亡

            # ── 叶片粒子（草丛交互特效） ──────────────────────────────
            'leaf': (
                import_folder('../graphics/particles/leaf1'),   # 叶片类型 1
                import_folder('../graphics/particles/leaf2'),   # 叶片类型 2
                import_folder('../graphics/particles/leaf3'),   # 叶片类型 3
                import_folder('../graphics/particles/leaf4'),   # 叶片类型 4
                import_folder('../graphics/particles/leaf5'),   # 叶片类型 5
                import_folder('../graphics/particles/leaf6'),   # 叶片类型 6
                # 以上 6 种叶片的水平镜像变体（增加视觉多样性）
                self.reflect_images(import_folder('../graphics/particles/leaf1')),
                self.reflect_images(import_folder('../graphics/particles/leaf2')),
                self.reflect_images(import_folder('../graphics/particles/leaf3')),
                self.reflect_images(import_folder('../graphics/particles/leaf4')),
                self.reflect_images(import_folder('../graphics/particles/leaf5')),
                self.reflect_images(import_folder('../graphics/particles/leaf6')),
            ),
        }

    def create_grass_particles(self, pos, groups):
        """
        创建草丛交互粒子（玩家走过草地时飘落的叶片）。

        从 'leaf' 组中随机选择一种叶片类型及其动画帧序列。

        参数:
            pos (tuple): 粒子生成位置的像素坐标 (x, y)
            groups (list[pygame.sprite.Group]): 粒子要加入的精灵组列表
        """
        grass_animation_frames = choice(self.frames['leaf'])
        ParticleEffect(pos, grass_animation_frames, groups)

    def create_particles(self, animation_type, pos, groups):
        """
        通用的粒子创建接口，根据类型创建对应的粒子特效。

        参数:
            animation_type (str): 粒子类型标识，对应 self.frames 字典中的键
                                  （如 'flame'、'heal'、'claw' 等）
            pos (tuple): 粒子生成位置的像素坐标 (x, y)
            groups (list[pygame.sprite.Group]): 粒子要加入的精灵组列表
        """
        animation_frames = self.frames.get(animation_type)
        if not animation_frames:
            return  # 找不到对应的帧序列则静默跳过
        ParticleEffect(pos, animation_frames, groups)

    def reflect_images(self, frames):
        """
        将帧序列中的所有图像水平翻转（生成镜像变体）。

        用于叶片粒子的视觉多样性。

        参数:
            frames (list[pygame.Surface]): 原始帧序列

        返回:
            list[pygame.Surface]: 水平翻转后的帧序列
        """
        new_frames = []
        for frame in frames:
            flipped_frame = pygame.transform.flip(frame, True, False)
            new_frames.append(flipped_frame)
        return new_frames

    def create_floating_text(self, text, pos, groups, color=(255, 255, 0), font_size=18, duration=1.2, rise_distance=30):
        """
        在指定位置创建飘浮文字（如经验值提示 "+50 XP"）。

        文字自动向上飘升并逐渐淡出，达到持续时间后自动销毁。

        参数:
            text (str): 要显示的文本内容
            pos (tuple): 初始位置的像素坐标 (x, y)
            groups (list[pygame.sprite.Group]): 文字要加入的精灵组列表
            color (tuple): RGB 颜色值，默认黄色 (255, 255, 0)
            font_size (int): 字号大小，默认 18
            duration (float): 文字存续时间（秒），默认 1.2 秒
            rise_distance (int): 文字上升总距离（像素），默认 30 像素
        """
        FloatingText(text, pos, groups, color, font_size, duration, rise_distance)

    def create_exp_particles(self, pos, target_pos, groups, amount=5, speed=250, exp_amount=None):
        """
        创建经验球粒子，从死亡位置飞向玩家位置。

        使用 MovingParticleEffect 实现粒子的追踪移动。
        可选的 exp_amount 参数会在死亡位置额外显示一条 "+XX XP" 飘浮文字。

        参数:
            pos (tuple): 经验球生成位置（怪物死亡位置）(x, y)
            target_pos (tuple): 目标位置（玩家当前位置）(x, y)
            groups (list[pygame.sprite.Group]): 粒子要加入的精灵组列表
            amount (int): 生成的经验球数量，默认 5 个
            speed (int): 经验球飞行速度（像素/秒），默认 250
            exp_amount (int, optional): 如果提供，在死亡位置显示 "+XX XP" 飘浮文字
        """
        from random import uniform
        orb_frames = self.frames.get('sparkle', [])
        if not orb_frames:
            # 没有 sparkle 帧时静默跳过（避免空帧序列错误）
            return
        for _ in range(amount):
            # 每个经验球在生成位置添加微小随机偏移，产生扩散效果
            offset = pygame.math.Vector2(uniform(-10, 10), uniform(-10, 10))
            spawn_pos = (pos[0] + offset.x, pos[1] + offset.y)
            MovingParticleEffect(
                spawn_pos,
                orb_frames,
                groups,
                target_pos=target_pos,
                speed=speed,
                sprite_type='exp_orb',  # 精灵类型标识为经验球
            )
        # 如果提供了经验值量，在死亡位置显示飘浮文字
        if exp_amount is not None:
            self.create_floating_text(f"+{exp_amount} XP", pos, groups)


class FloatingText(pygame.sprite.Sprite):
    """
    飘浮文字精灵，用于显示临时的文字提示（如经验值增加、伤害数字等）。

    行为：
        - 创建后在 duration 秒内逐渐上升
        - 同时逐渐淡出（alpha 从 255 降到 0）
        - 持续时间结束后自动从所有精灵组中移除
    """

    def __init__(self, text, pos, groups, color=(255, 255, 0), font_size=18, duration=1.2, rise_distance=30):
        """
        初始化飘浮文字。

        参数:
            text (str): 显示的文本内容
            pos (tuple): 初始位置的像素坐标 (x, y)
            groups (list[pygame.sprite.Group]): 要加入的精灵组
            color (tuple): RGB 颜色值，默认黄色 (255, 255, 0)
            font_size (int): 字号，默认 18
            duration (float): 持续时间（秒），默认 1.2 秒
            rise_distance (int): 上升总距离（像素），默认 30 像素
        """
        super().__init__(groups)
        from resource_manager import ResourceManager
        self.font = ResourceManager.instance().get_font('../font/joystix.ttf', font_size)
        self.text = text
        self.color = color
        self.image = self.font.render(self.text, True, self.color)
        self.rect = self.image.get_rect(center=pos)
        self.start_pos = pygame.math.Vector2(pos)  # 初始位置，用于计算上升偏移
        self.duration = duration                     # 文字存续总时长（秒）
        self.elapsed = 0                             # 已经过的时间（秒）
        self.rise_distance = rise_distance           # 总上升距离（像素）
        self.alpha = 255                             # 当前透明度

    def update(self, dt):
        """
        每帧更新：向上移动 + 淡出效果。

        参数:
            dt (float): 帧时间差（秒），用于帧率无关的动画
        """
        self.elapsed += dt
        # 计算动画进度率（0.0 ~ 1.0），clamp 防止超调
        progress = min(self.elapsed / self.duration, 1.0)
        # 垂直偏移：从起始位置向上移动（y 轴负方向）
        offset_y = -self.rise_distance * progress
        self.rect.center = (self.start_pos.x, self.start_pos.y + offset_y)
        # 淡出效果：alpha 从 255 线性降至 0
        self.alpha = int(255 * (1 - progress))
        self.image.set_alpha(self.alpha)
        # 达到持续时间后自动销毁
        if self.elapsed >= self.duration:
            self.kill()


class ParticleEffect(pygame.sprite.Sprite):
    """
    基础粒子特效精灵。

    行为：
        - 在指定位置播放一组动画帧序列
        - 以固定速度（animation_speed=15 帧/秒）逐帧播放
        - 所有帧播放完毕后自动从所有精灵组中移除
        - 不会移动，适合爆炸特效、魔法光环等静态位置播放的动画
    """

    def __init__(self, pos, animation_frames, groups, sprite_type='magic'):
        """
        初始化粒子特效。

        参数:
            pos (tuple): 粒子中心位置的像素坐标 (x, y)
            animation_frames (list[pygame.Surface]): 动画帧序列（图像列表）
            groups (list[pygame.sprite.Group]): 要加入的精灵组列表
            sprite_type (str): 精灵类型标识，默认 'magic'，用于碰撞分类或渲染排序
        """
        super().__init__(groups)
        self.sprite_type = sprite_type
        self.frame_index = 0               # 当前帧索引
        self.animation_speed = 15          # 播放速度（帧/秒）
        self.frames = animation_frames     # 所有帧列表
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)

    def animate(self, dt):
        """
        逐帧播放动画。

        根据帧时间 dt 推进帧索引，当索引超过帧列表长度时自动销毁。
        使用 int() 取整来获取当前帧图像，实现帧率无关的播放速度。

        参数:
            dt (float): 帧时间差（秒）
        """
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.frames):
            self.kill()  # 动画播放完毕，销毁自身
        else:
            self.image = self.frames[int(self.frame_index)]

    def update(self, dt):
        """
        每帧更新：推进动画。

        参数:
            dt (float): 帧时间差（秒）
        """
        self.animate(dt)


class MovingParticleEffect(ParticleEffect):
    """
    可移动的粒子特效（继承 ParticleEffect）。

    在基础粒子的基础上增加了追踪目标位置移动的功能。
    用于经验球粒子：从怪物死亡位置飞向玩家位置。

    扩展行为：
        - 每帧朝 target_pos 方向移动
        - 到达目标附近（<16 像素）或超过最大存活时间时自动销毁
        - 继承父类的动画播放功能
    """

    def __init__(self, pos, animation_frames, groups, target_pos, speed=250, sprite_type='exp_orb', max_lifetime=1.5):
        """
        初始化可移动粒子特效。

        参数:
            pos (tuple): 初始位置的像素坐标 (x, y)
            animation_frames (list[pygame.Surface]): 动画帧序列
            groups (list[pygame.sprite.Group]): 要加入的精灵组列表
            target_pos (tuple): 目标位置的像素坐标 (x, y)，粒子将朝此位置移动
            speed (int): 飞行速度（像素/秒），默认 250
            sprite_type (str): 精灵类型标识，默认 'exp_orb'
            max_lifetime (float): 最大存活时间（秒），超过后自动销毁，默认 1.5 秒
        """
        super().__init__(pos, animation_frames, groups, sprite_type)
        self.target_pos = pygame.math.Vector2(target_pos)  # 目标位置
        self.pos = pygame.math.Vector2(pos)                 # 当前位置（浮点数精度）
        self.speed = speed                                   # 飞行速度（像素/秒）
        self.max_lifetime = max_lifetime                     # 最大存活时间（秒）
        self.lifetime = 0                                    # 已存活时间（秒）

    def update(self, dt):
        """
        每帧更新：移动 + 动画 + 生命周期检查。

        移动逻辑：
            1. 计算从当前位置指向目标位置的向量
            2. 归一化后乘以速度 × dt，得到本帧移动距离
            3. 如果本帧移动距离超过到目标的剩余距离，直接瞬移到目标
            4. 更新精灵位置

        销毁条件（任一满足）：
            1. 与目标距离 < 16 像素（认为已到达）
            2. 存活时间超过 max_lifetime（1.5 秒）

        参数:
            dt (float): 帧时间差（秒）
        """
        # ── 朝目标位置移动 ──────────────────────────────────────────
        direction = self.target_pos - self.pos
        distance = direction.length()
        if distance > 0:
            direction = direction.normalize()
            # 本帧移动距离 = min(速度 × dt, 剩余距离) —— 避免 overshoot
            move_dist = min(self.speed * dt, distance)
            self.pos += direction * move_dist
            self.rect.center = (round(self.pos.x), round(self.pos.y))

        # ── 播放动画帧（继承自 ParticleEffect） ─────────────────────
        self.animate(dt)

        # ── 生命周期更新 ────────────────────────────────────────────
        self.lifetime += dt
        if distance < 16 or self.lifetime > self.max_lifetime:
            self.kill()  # 到达目标或超时后销毁
