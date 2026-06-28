# -*- coding: utf-8 -*-
"""
magic.py — 魔法系统（MagicPlayer）

定义 MagicPlayer 类，管理玩家两种魔法的释放逻辑：
    1. heal（治疗魔法）：消耗能量恢复生命值，播放治疗粒子特效
    2. flame（火焰魔法）：消耗能量朝面朝方向发射火焰弹，播放火焰粒子特效
"""

import pygame
from settings import magic_data, TILESIZE
from random import randint
from resource_manager import ResourceManager


class MagicPlayer:
    """
    魔法系统类，负责处理玩家施法的完整流程。

    功能：
        - 能量消耗检查与扣除
        - 治疗魔法：恢复生命值 + 光环/治疗粒子特效
        - 火焰魔法：根据玩家面朝方向生成火焰弹粒子序列 + 随机扩散
        - 音效播放（通过 ResourceManager 缓存加载）

    与 AnimationPlayer 协作，委托其创建对应的粒子视觉效果。
    魔法属性（强度、消耗等）从 settings.magic_data 配置表中读取。
    """

    def __init__(self, animation_player):
        """
        初始化魔法系统。

        参数:
            animation_player (AnimationPlayer): 粒子动画播放器，用于创建魔法释放时的视觉特效
        """
        self.animation_player = animation_player
        # 通过 ResourceManager 加载魔法音效（带缓存）
        res = ResourceManager.instance()
        self.sounds = {
            'heal': res.get_sound(magic_data['heal']['spell_sound'], volume=0.5),   # 治疗魔法音效
            'flame': res.get_sound(magic_data['flame']['spell_sound'], volume=0.4),  # 火焰魔法音效
        }

    def heal(self, player, strength, cost, groups):
        """
        释放治疗魔法。

        执行流程：
            1. 检查玩家能量是否足够
            2. 扣除能量，恢复生命值（不超过最大生命值上限）
            3. 播放治疗音效
            4. 委托 AnimationPlayer 创建 aura（光环）和 heal（治疗）粒子特效

        参数:
            player (Player): 玩家对象，需具备 energy、health、stats['health'] 属性
            strength (int): 治疗量，从 magic_data['heal']['strength'] 读取
            cost (int): 能量消耗量，从 magic_data['heal']['cost'] 读取
            groups (list[pygame.sprite.Group]): 粒子特效要加入的精灵组列表
        """
        if player.energy >= cost:
            self.sounds['heal'].play()           # 播放治疗音效
            player.health += strength            # 恢复生命值
            player.energy -= cost                # 扣除能量
            # 限制生命值不超过最大生命值上限
            if player.health >= player.stats['health']:
                player.health = player.stats['health']
            # 在玩家位置创建光环粒子特效
            self.animation_player.create_particles('aura',
                                                   player.rect.center, groups)
            # 在玩家位置上方 20 像素处创建治疗粒子特效
            self.animation_player.create_particles('heal',
                                                   player.rect.center + pygame.math.Vector2(0, -20), groups)

    def flame(self, player, cost, groups):
        """
        释放火焰魔法。

        执行流程：
            1. 检查玩家能量是否足够
            2. 扣除能量
            3. 根据玩家面朝方向（up/down/left/right）确定火焰弹发射方向
            4. 沿方向生成 5 个火焰弹粒子，每个间隔一个 TILESIZE 距离
            5. 每个火焰弹添加随机偏移（±TILESIZE/3），产生散射效果
            6. 委托 AnimationPlayer 创建 flame 粒子特效

        参数:
            player (Player): 玩家对象，需具备 energy、status 属性
            cost (int): 能量消耗量，从 magic_data['flame']['cost'] 读取
            groups (list[pygame.sprite.Group]): 粒子特效要加入的精灵组列表
        """
        if player.energy >= cost:
            player.energy -= cost                # 扣除能量
            self.sounds['flame'].play()          # 播放火焰音效

            # 从玩家状态中解析面朝方向（去除 '_idle'、'_attack' 等后缀）
            status = player.status.split('_')[0]
            if status == 'up':
                direction = pygame.math.Vector2(0, -1)    # 朝上（屏幕坐标 y 轴向下）
            elif status == 'down':
                direction = pygame.math.Vector2(0, 1)     # 朝下
            elif status == 'right':
                direction = pygame.math.Vector2(1, 0)     # 朝右
            else:
                direction = pygame.math.Vector2(-1, 0)    # 朝左（默认）

            # 沿面朝方向生成 5 个火焰弹粒子（i=1 到 5）
            for i in range(1, 6):
                if direction.x:  # 水平方向（左/右）
                    # 水平偏移 = 方向 × i × TILESIZE，垂直方向随机抖动 ±TILESIZE/3
                    offset_x = (direction.x * i) * TILESIZE
                    x = player.rect.centerx + offset_x + \
                        randint(-TILESIZE//3, TILESIZE//3)
                    y = player.rect.centery + \
                        randint(-TILESIZE//3, TILESIZE//3)
                    self.animation_player.create_particles(
                        'flame', (x, y), groups)
                else:  # 垂直方向（上/下）
                    # 垂直偏移 = 方向 × i × TILESIZE，水平方向随机抖动 ±TILESIZE/3
                    offset_y = (direction.y * i) * TILESIZE
                    x = player.rect.centerx + \
                        randint(-TILESIZE//3, TILESIZE//3)
                    y = player.rect.centery + offset_y + \
                        randint(-TILESIZE//3, TILESIZE//3)
                    self.animation_player.create_particles(
                        'flame', (x, y), groups)
