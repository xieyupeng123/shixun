"""
游戏全局配置文件 (Game Global Configuration)

本模块是游戏的核心配置中心，定义了所有可调参数，包括：
- 窗口与渲染参数（分辨率、帧率、图块大小）
- UI界面尺寸与颜色主题
- 武器数据（伤害、冷却时间、贴图路径）
- 魔法数据（强度、消耗、贴图与音效路径）
- 怪物数据（生命值、经验、伤害、攻击方式、移动速度等）
- 无敌模式参数（持续时间、冷却时间、代价倍率）
- 玩家基础属性与升级成本
- Boss阶段系统（阶段颜色、属性倍率）

所有路径均通过 support.get_path() 转换，确保跨平台兼容。
"""

from support import get_path  # 导入路径工具函数，用于转换相对路径为绝对路径

# ── 游戏基础设置 (Game Setup) ──────────────────────────────────────────────

WIDTH = 1280         # 窗口宽度（像素）
HEIGHT = 720         # 窗口高度（像素）
FPS = 60             # 目标帧率（帧/秒）
TILESIZE = 64        # 地图单格图块大小（像素），影响地图绘制与碰撞检测精度

# 各实体类型的命中框偏移量（像素），用于微调碰撞检测区域
# 负值表示命中框比精灵图小，使碰撞判定更宽松
HITBOX_OFFSET = {
    'player': -26,    # 玩家：命中框比贴图小26px
    'object': -40,    # 物体（箱子等）：命中框比贴图小40px
    'grass': -10,     # 草丛：命中框比贴图小10px
    'invisible': 0    # 不可见碰撞体：命中和贴图一致
}

# ── UI界面尺寸 (UI Dimensions) ─────────────────────────────────────────────

BAR_HEIGHT = 20               # 血量/能量条的高度（像素）
HEALTH_BAR_WIDTH = 200        # 血条宽度（像素）
ENERGY_BAR_WIDTH = 140        # 能量条宽度（像素）
ITEM_BOX_SIZE = 80            # 物品槽位图标的尺寸（像素，宽高均为该值）
UI_FONT = get_path('../font/joystix.ttf')   # UI文字使用的字体文件路径（Joystix像素风格字体）
UI_FONT_SIZE = 18             # UI文字字号

# ── 通用颜色 (General Colors) ──────────────────────────────────────────────
# 使用十六进制颜色字符串，格式为 '#RRGGBB'

WATER_COLOR = '#71ddee'           # 水体颜色（浅蓝）
UI_BG_COLOR = '#222222'           # UI面板背景色（深灰）
UI_BORDER_COLOR = '#111111'       # UI面板边框色（黑色）
TEXT_COLOR = '#EEEEEE'            # 普通文字颜色（浅灰/白）

# ── UI专用颜色 (UI Colors) ─────────────────────────────────────────────────

HEALTH_COLOR = 'red'              # 血条颜色（红色，使用pygame预定义颜色名）
ENERGY_COLOR = 'blue'             # 能量条颜色（蓝色）
UI_BORDER_COLOR_ACTIVE = 'gold'   # 选中/激活状态的UI边框色（金色）

# ── 升级菜单颜色 (Upgrade Menu Colors) ─────────────────────────────────────

TEXT_COLOR_SELECTED = '#111111'     # 菜单中选中项的文本颜色（黑色）
BAR_COLOR = '#EEEEEE'               # 未选中状态下的属性条颜色（浅灰）
BAR_COLOR_SELECTED = '#111111'      # 选中状态下的属性条颜色（黑色）
UPGRADE_BG_COLOR_SELECTED = '#EEEEEE'  # 选中项的背景颜色（浅灰）

# ── 武器数据 (Weapon Data) ─────────────────────────────────────────────────

# 各武器贴图路径（通过 get_path 转换为绝对路径）
sword_path = get_path('../graphics/weapons/sword/full.png')    # 剑
lance_path = get_path('../graphics/weapons/lance/full.png')    # 长矛
axe_path = get_path('../graphics/weapons/axe/full.png')        # 斧头
rapier_path = get_path('../graphics/weapons/rapier/full.png')  # 刺剑
sai_path = get_path('../graphics/weapons/sai/full.png')        # 叉

# 武器数据字典，key为武器名称，value为属性字典：
#   - cooldown: 攻击冷却时间（毫秒），值越小攻击频率越高
#   - damage:   基础伤害值
#   - graphic:  武器贴图的绝对路径
weapon_data = {
    'sword':  {'cooldown': 100, 'damage': 15, 'graphic': sword_path},   # 剑：均衡型
    'lance':  {'cooldown': 400, 'damage': 30, 'graphic': lance_path},   # 长矛：高伤低速
    'axe':    {'cooldown': 300, 'damage': 20, 'graphic': axe_path},     # 斧头：中伤中速
    'rapier': {'cooldown': 50,  'damage': 8,  'graphic': rapier_path},  # 刺剑：低伤极速
    'sai':    {'cooldown': 80,  'damage': 10, 'graphic': sai_path}      # 叉：低伤快速
}

# ── 魔法数据 (Magic Data) ──────────────────────────────────────────────────

# 魔法贴图路径
flame_path = get_path('../graphics/particles/flame/fire.png')  # 火焰魔法贴图
heal_path = get_path('../graphics/particles/heal/heal.png')    # 治疗魔法贴图

# 魔法音效路径
flame_sound_path = get_path('../audio/flame.wav')   # 火焰释放音效
heal_sound_path = get_path('../audio/heal.wav')     # 治疗释放音效

# 魔法数据字典，key为魔法名称，value为属性字典：
#   - strength:    魔法强度/效果值（火焰为伤害，治疗为回复量）
#   - cost:        施法消耗的能量值
#   - graphic:     魔法特效贴图路径
#   - spell_sound: 施法音效文件路径
magic_data = {
    'flame': {'strength': 10, 'cost': 20, 'graphic': flame_path, 'spell_sound': flame_sound_path},
    # 火焰魔法：伤害10，消耗20能量
    'heal':  {'strength': 50, 'cost': 10, 'graphic': heal_path, 'spell_sound': heal_sound_path},
    # 治疗魔法：回复50生命，消耗10能量
}

# ── 敌人/怪物数据 (Enemy / Monster Data) ───────────────────────────────────

# 攻击音效路径
slash_sound_path   = get_path('../audio/attack/slash.wav')      # 斩击音效
claw_sound_path    = get_path('../audio/attack/claw.wav')       # 爪击音效
fireball_sound_path = get_path('../audio/attack/fireball.wav')  # 火球/雷电音效

# 怪物数据字典，key为怪物名称，value为属性字典：
#   - health:        生命值
#   - exp:           击败后获得的经验值
#   - damage:        攻击力
#   - attack_type:   攻击类型（影响动画/特效表现）
#   - attack_sound:  攻击音效路径
#   - speed:         移动速度（像素/秒）
#   - resistance:    抗性/击退抵抗值
#   - attack_radius:  攻击判定半径（像素），进入此范围即发动攻击
#   - notice_radius:  警戒半径（像素），进入此范围开始追踪玩家
monster_data = {
    'squid':   {'health': 50,   'exp': 100, 'damage': 15, 'attack_type': 'slash',
                'attack_sound': slash_sound_path, 'speed': 150, 'resistance': 3,
                'attack_radius': 80, 'notice_radius': 360},
    # 鱿鱼怪：低血量，中速，远程警戒范围大
    'raccoon': {'health': 300,  'exp': 500, 'damage': 40, 'attack_type': 'claw',
                'attack_sound': claw_sound_path, 'speed': 100, 'resistance': 3,
                'attack_radius': 120, 'notice_radius': 400},
    # 浣熊怪：高血量高伤害，低速，攻守范围均大
    'spirit':  {'health': 40,   'exp': 110, 'damage': 8,  'attack_type': 'thunder',
                'attack_sound': fireball_sound_path, 'speed': 200, 'resistance': 3,
                'attack_radius': 60, 'notice_radius': 350},
    # 幽灵怪：极低血量，高速，远程攻击
    'bamboo':  {'health': 35,   'exp': 120, 'damage': 5,  'attack_type': 'leaf_attack',
                'attack_sound': slash_sound_path, 'speed': 150, 'resistance': 3,
                'attack_radius': 50, 'notice_radius': 300}
    # 竹子怪：最低血量最低伤害，经验不错
}

# ── 无敌模式参数 (Invincible Mode) ─────────────────────────────────────────

INVINCIBLE_SPEED_MULT = 2       # 无敌期间移动速度倍率（2倍速）
INVINCIBLE_ATTACK_MULT = 2      # 无敌期间攻击伤害倍率（2倍伤害）
INVINCIBLE_DURATION = 30000     # 无敌状态持续时间，30秒后自动到期（单位：毫秒）
INVINCIBLE_COOLDOWN = 300000   # 无敌模式冷却时间，5分钟后才能再次激活（单位：毫秒）
INVINCIBLE_COST_HEALTH = 0.5    # 无敌到期后的生命代价：扣除当前生命的50%
INVINCIBLE_COST_ENERGY = 1.0    # 无敌到期后的能量代价：扣除全部能量（100%）

# ── 玩家基础属性与升级消耗 (Player Base Stats & Upgrade Costs) ────────────
# 这是所有属性升级的单一数据源（Single Source of Truth），
# 确保升级系统与初始状态保持一致

PLAYER_BASE_STATS = {
    'health': 200,    # 基础生命值
    'energy': 100,    # 基础能量值
    'attack': 15,     # 基础攻击力
    'magic': 5,       # 基础魔法强度
    'speed': 300      # 基础移动速度（像素/秒）
}

PLAYER_BASE_COSTS = {
    'health': 100,    # 升级生命所需金币
    'energy': 100,    # 升级能量所需金币
    'attack': 100,    # 升级攻击所需金币
    'magic': 100,     # 升级魔法所需金币
    'speed': 100      # 升级速度所需金币
}

# ── Boss阶段系统 (Boss Phase System) ───────────────────────────────────────
# Boss生命值降低到特定阈值时进入不同阶段，获得颜色变化和属性加成

BOSS_PHASE_DATA = {
    1: {'color': None,              'stat_mult': 1.0},   # 阶段1：普通状态，无颜色变化，属性不变
    2: {'color': (255, 120, 120),   'stat_mult': 2.0},   # 阶段2：浅红色，全属性翻倍
    3: {'color': (180, 80, 220),    'stat_mult': 4.0},   # 阶段3：紫色，全属性变为4倍
}
