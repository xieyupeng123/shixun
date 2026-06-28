"""
entity —— 游戏实体基类模块

本模块定义了 Entity 基类，是所有游戏实体（玩家、敌人）的公共父类。
提供以下核心功能：
  - 移动与碰撞检测（水平和垂直方向分离）
  - 动画帧推进和切换
  - 正弦波闪烁效果工具方法

Entity 继承自 pygame.sprite.Sprite，可被直接加入精灵组统一管理。
"""

import pygame
from math import sin


class Entity(pygame.sprite.Sprite):
    """Entity —— 所有游戏实体的基类（玩家和敌人共用）

    封装了精灵对象在 2D 平铺世界中的基础行为：
      移动、碰撞响应、动画帧推进、冷却追踪。
    子类通过重写特定方法来自定义行为和外观。

    继承自 pygame.sprite.Sprite，因此可以加入到任何精灵组中。
    """

    def __init__(self, groups, pos):
        """初始化实体对象

        参数:
            groups (list[pygame.sprite.Group]): 该实体需要加入的精灵组列表，
                例如 all_sprites、obstacle_sprites 等
            pos (tuple[int, int]): 实体的初始坐标 (x, y)，以像素为单位
        """
        super().__init__(groups)
        # 当前动画帧在 animations 列表中的索引，用于逐帧切换精灵图
        self.frame_index = 0
        # 动画播放速度系数，值越大切换帧越快（与 dt 相乘作为帧增量）
        self.animation_speed = 4
        # 移动方向向量，取值范围 [-1, 1]；归一化后保证各个方向移动速度一致
        self.direction = pygame.math.Vector2()

    # ── Movement & Collision ──────────────────────────────────────────

    def move(self, speed, pos, dt):
        """执行实体的移动逻辑，包含水平和垂直两个方向的分步处理

        流程:
          1. 更新 pos 为外部传入的位置对象
          2. 当方向向量非零时归一化，保证对角线移动速度与正交方向一致
          3. 水平分量移动 -> 更新碰撞箱 -> 碰撞检测与修正
          4. 垂直分量移动 -> 更新碰撞箱 -> 碰撞检测与修正
          5. 将 pos 与 rect/hitbox 同步，确保渲染位置与物理位置一致

        参数:
            speed (float): 移动速度，单位 像素/秒
            pos (pygame.math.Vector2): 实体位置（中心点坐标），会被原地修改
            dt (float): 上一帧到当前帧的时间间隔（秒），用于帧率无关的移动

        使用:
            pos 是 Vector2 引用，外部传入后在方法内部直接修改其 x/y，
            调用方（通常是 Entity 子类）可以读取更新后的值。
        """
        self.pos = pos

        # 如果方向向量有长度（即玩家按了方向键），将其归一化为单位向量
        # 防止对角线移动时速度叠加导致移动更快（斜向归一化）
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        # ── 水平移动（先处理 X 轴） ──
        # 水平位移 = 方向分量 x 速度 x 时间步长
        self.pos.x += self.direction.x * speed * dt
        # 将 hitbox 的 centerx 对齐到 pos.x（四舍五入取整像素）
        self.hitbox.centerx = round(self.pos.x)
        # 用 hitbox 的位置同步更新 rect，保证渲染位置与物理碰撞箱一致
        self.rect.centerx = self.hitbox.centerx
        # 水平碰撞检测与修正（推送实体离开障碍物）
        self.collision('horizontal')

        # ── 垂直移动（再处理 Y 轴） ──
        self.pos.y += self.direction.y * speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision('vertical')

    def collision(self, direction):
        """碰撞检测与位置修正 —— 将实体从障碍物中"推"出来

        遍历 obstacle_sprites 组中的所有精灵，检查 hitbox 是否与本实体重叠。
        如果重叠，根据移动方向将本实体的 hitbox 紧贴在障碍物边缘，
        并将 pos 和 rect 同步到修正后的位置。

        水平和垂直方向分开处理的好处：
          - 避免一个方向的碰撞修正影响另一个方向的移动
          - 允许实体贴着墙壁滑动（例如水平撞墙时垂直方向仍可移动）

        参数:
            direction (str): 碰撞检测方向，'horizontal' 或 'vertical'
                - 'horizontal': 修正 X 轴位置（左/右推离）
                - 'vertical': 修正 Y 轴位置（上/下推离）
        """
        for sprite in self.obstacle_sprites.sprites():
            # 只有带 hitbox 属性的精灵才参与碰撞（排除不含物理碰撞箱的装饰层）
            if hasattr(sprite, 'hitbox'):
                if sprite.hitbox.colliderect(self.hitbox):
                    if direction == 'horizontal':
                        # 向右移动时撞墙：将本实体右侧紧贴障碍物左侧
                        if self.direction.x > 0:
                            self.hitbox.right = sprite.hitbox.left
                        # 向左移动时撞墙：将本实体左侧紧贴障碍物右侧
                        if self.direction.x < 0:
                            self.hitbox.left = sprite.hitbox.right
                        # 同步 rect 和 pos 到修正后的位置
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx

                    if direction == 'vertical':
                        # 向上移动时撞墙：将本实体顶部紧贴障碍物底部
                        if self.direction.y < 0:
                            self.hitbox.top = sprite.hitbox.bottom
                        # 向下移动时撞墙：将本实体底部紧贴障碍物顶部
                        if self.direction.y > 0:
                            self.hitbox.bottom = sprite.hitbox.top
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery

    # ── Animation ─────────────────────────────────────────────────────

    def animate(self, dt):
        """推进实体的动画帧并更新当前渲染图像

        根据当前状态（self.status，如 'down'、'up_attack'）从
        self.animations 字典中取出对应的帧列表，以 animation_speed * dt
        为步长递增帧索引，循环播放。

        子类应调用 super().animate(dt) 后再添加自己的修改：
          - 玩家类：重新定位 rect、受伤闪烁、无敌金色覆盖层
          - 敌人类：根据移动方向设置状态、受伤闪烁

        参数:
            dt (float): 帧时间间隔（秒），用于帧率无关的动画推进
        """
        # 根据当前状态获取对应的动画帧列表
        animation = self.animations[self.status]
        # 累加帧索引（浮点累加，取整时切换图片，实现平滑慢速动画）
        self.frame_index += self.animation_speed * dt
        # 如果帧索引超出列表范围，回到开头（循环播放）
        if self.frame_index >= len(animation):
            self.frame_index = 0
        # 取整后获取当前帧对应的 Surface 图像
        self.image = animation[int(self.frame_index)]

    # ── Utility ───────────────────────────────────────────────────────

    def wave_value(self):
        """基于正弦波返回 255 或 0 —— 用于受击闪烁效果

        利用 pygame.time.get_ticks() / 40 作为正弦函数的输入，
        40 是频率调节因子，值越小闪烁越快。大约每 0.25 秒完成一个亮灭周期。
        返回 255（可见）或 0（透明），与 set_alpha() 配合产生闪烁视觉效果。

        用在：
          - 玩家受击后短暂无敌期间的闪烁
          - 敌人被击中后的闪烁反馈

        返回:
            int: 255（正弦值 >= 0 时，可见）或 0（正弦值 < 0 时，透明）
        """
        value = sin(pygame.time.get_ticks() / 40)
        if value >= 0:
            return 255
        return 0
