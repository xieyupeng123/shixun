# Stardew Valley Action X — 更新日志

## V10 Final（2026-06-26）— 当前版本

**代码量**：2828行 / 20个Python源文件

### 新增功能

#### 🛡️ 无敌模式（空格键切换）
- 按空格键切换无敌/正常模式
- 开启后：移动速度×2，攻击伤害×2
- 视觉反馈：金色半透明覆盖层（RGBA 255,200,0,80）
- 顶部居中显示 "INVINCIBLE" 金色文字+边框
- 免疫所有敌人伤害
- 独立BGM（invincible.ogg循环播放）
- 防连触检测：松开空格后才能再次切换

#### 🔊 完整音效系统
- **sound_manager.py**：集中管理音频加载+缓存+降级处理
- **music_state.py**：BGM状态管理（0=普通/1=Boss）
- 玩家攻击音效：sword.wav
- 敌人受击音效：hit.wav
- 敌人死亡音效：death.wav
- 魔法释放音效：flame.wav / heal.wav
- 怪物攻击音效：slash.wav / claw.wav / fireball.wav
- 无敌模式音效：invincible.ogg（循环）
- 背景音乐：game_bgm.ogg（普通）/ boss_bgm.ogg（Boss区域）

#### 🎵 BGM区域切换
- 进入Boss notice_radius时永久切换到Boss BGM
- 无敌模式下只设状态不立即播放
- 退出无敌时根据当前状态恢复对应BGM

#### 🎯 武器/魔法UI覆盖
- 左下角80×80武器图标框，显示当前装备武器
- 右侧80×80魔法图标框，显示当前装备魔法
- 切换时金色边框高亮（200ms冷却）

#### ⚔️ 真实伤害计算
- `get_full_weapon_damage()` = 攻击力 + 武器伤害（无敌×2）
- `get_full_magic_damage()` = 魔法值 + 法术强度（无敌×2）
- 火焰粒子现在造成魔法伤害

### 操作说明

| 按键 | 功能 |
|------|------|
| WASD / 方向键 | 移动 |
| 鼠标左键 | 攻击 |
| 鼠标右键 | 释放魔法 |
| Q键 / 鼠标滚轮 | 切换武器（5种） |
| E键 | 切换魔法（治疗/火焰） |
| 空格 | 切换无敌模式 |
| B键 | 打开升级菜单（暂停） |
| M键 | 世界地图 |
| P键 | 暂停时存档 |
| 回车 | 开始游戏 |
| R键 | 死亡/胜利后重开 |
| ESC | 退出 |

---

## V9 — 架构重构 + Boss三阶段 + 世界地图（2026-06-25）

**代码量**：1997行 / 20个Python源文件

### 架构重构
- 从Level提取3个专职Manager：
  - **CombatManager**：武器创建/销毁、魔法释放、攻击碰撞、草地破坏
  - **BossManager**：Boss生成、三阶段晋升、胜利检测
  - **MapRenderer**：全屏世界地图覆盖渲染
- Level通过组合模式集成三个Manager
- 保留兼容性属性（@property代理）

### 新增功能
- **Boss三阶段系统**：
  - 阶段1（Normal）：×1属性，无色
  - 阶段2（Enraged）：×2属性，淡红色(255,120,120)
  - 阶段3（Final）：×4属性，紫色(180,80,220)
  - 击杀3次触发胜利
- **世界地图**（M键）：
  - 半透明黑色覆盖
  - 障碍网格（灰色=障碍，浅绿=可通行）
  - 敌人红点（普通小圆，Boss大红叉+脉冲+BOSS标签）
  - 玩家绿点（脉冲+YOU标签）
  - 底部坐标 + Boss击杀进度
  - 右下角图例
  - 金色边框

---

## V8 — Boss战 + 暂停存档 + 魔法 + 升级面板（2026-06-25）

**代码量**：1665行 / 20个Python源文件

### 新增功能
- **Boss系统**：浣熊Boss 300HP，2阶段变身（66%/33%血量阈值）
- **魔法系统**：
  - 火焰术：5方向粒子喷射，10威力，20能量消耗
  - 治疗术：光环粒子，50回复，10能量消耗
  - 右键/Ctrl释放，E键切换
- **升级面板**：
  - B键暂停，半透明覆盖
  - 五维属性：health/energy/attack/magic/speed
  - 左右键选择，上键升级，下键降级
  - 经验消耗递增（+50/级）
- **暂停存档**：
  - M键暂停 + "PAUSED"标题
  - P键保存（玩家+地图状态）
  - 启动检测savegame.json → C继续/N新游戏/ESC退出
- **能量系统**：蓝色能量条，每秒自动恢复5点

---

## V5 — 真实怪物精灵 + 完整粒子特效（2026-06-25）

**代码量**：1268行 / 18个Python源文件

### 新增功能
- **真实怪物精灵**：4种怪物（squid/raccoon/spirit/bamboo）各含idle/move/attack动画
- **12种粒子特效**：
  - 攻击：claw/slash/sparkle/leaf_attack/thunder
  - 死亡：smoke_orange
  - 魔法：flame/aura/heal
  - 环境：leaf1-leaf6（含镜像）
- **存档系统完整实现**：
  - 玩家序列化（位置/HP/经验/武器/属性）
  - 地图状态跟踪（已击败敌人、已破坏草地）
  - JSON原子写入

---

## V4 — 终版优化（2026-06-25）

**代码量**：1192行 / 18个Python源文件

### 新增功能
- **5种武器**：sword/lance/axe/rapier/sai，各有真实精灵+独立伤害/冷却
- **A*寻路**：敌人追踪从线性 → A*智能绕障碍（500ms重算）
- **鼠标左键攻击**：与空格键并存
- **Q键切换武器**：循环切换5种武器，200ms冷却
- **鼠标滚轮切换武器**
- **动画主菜单**：标题正弦浮动 + 蓝色浮动粒子 + 武器列表
- **胜利界面**：全灭敌人后金色粒子 + 经验统计

### 架构变化
- 新增constants.py、map_manager.py、pathfinding_utils.py、resource_manager.py

---

## V3 — 完整架构 + 敌人AI（2026-06-25）

**代码量**：890行 / 14个Python源文件

### 新增功能
- **敌人AI**：史莱姆精灵，idle→chase→attack三态状态机
- **HP系统**：玩家血量、受伤闪烁效果
- **无敌帧**：受伤后500ms无敌
- **击退效果**：被攻击后位移
- **死亡/重生**：R键重开
- **HUD**：血条（红色）+ 经验值数字
- **受击粒子**：hit特效
- **草地破坏动画**：碎片粒子

### 架构变化
- 从7文件扩展到14文件
- 新增enemy.py、weapon.py、combat.py、ui.py、particles.py、items.py、save_manager.py

---

## V2 — 加入开始页面与基础攻击（2026-06-24）

**代码量**：475行 / 7个Python源文件

### 新增功能
- **主菜单界面**：深色背景 + 金色标题 + 操作提示
- **空格键攻击**：程序化生成武器精灵，400ms冷却
- **草地破坏**：武器碰撞检测
- **游戏状态机**：start / game 两种状态

---

## V1 — 初版（2026-06-24）

**代码量**：343行 / 7个Python源文件

### 基础功能
- 1280×720 Pygame窗口
- 玩家8方向精灵动画（行走/待机）
- WASD/方向键移动 + AABB碰撞检测
- 4层CSV瓦片地图
- Y轴深度排序摄像机跟随
- Delta Time帧动画系统

---

## 技术栈

- **语言**：Python 3.12
- **框架**：Pygame 2.6
- **分辨率**：1280×720
- **帧率**：60FPS（Delta Time驱动）
- **地图格式**：CSV（4层）
- **存档格式**：JSON（原子写入）
- **寻路算法**：A*（曼哈顿距离启发式）
- **碰撞检测**：分轴AABB
- **渲染**：Y轴深度排序

## 项目结构

```
stardew-valley-action-x-final/
├── code/                    # 20个Python源文件（2828行）
│   ├── main.py              # 游戏入口，全局状态机（421行）
│   ├── level.py             # Level协调者 + CombatManager + BossManager + MapRenderer（460行）
│   ├── player.py            # Player类（键盘输入驱动）（361行）
│   ├── settings.py          # 配置数据（武器/怪物/魔法/Boss）（91行）
│   ├── enemy.py             # Enemy类（AI状态机驱动）（256行）
│   ├── map_manager.py       # MapManager（CSV地图加载/水域检测/寻路网格）（233行）
│   ├── ui.py                # UI（血条/能量条/武器图标/Boss血条/无敌标记）（185行）
│   ├── particles.py         # AnimationPlayer + ParticleEffect + FloatingText（167行）
│   ├── upgrade.py           # Upgrade升级菜单（五维属性升降级）（158行）
│   ├── entity.py            # Entity基类（移动/碰撞/动画）（83行）
│   ├── pathfinding_utils.py # A*寻路 + 网格构建 + 坐标转换（78行）
│   ├── resource_manager.py  # ResourceManager单例（图片/音效/字体缓存）（61行）
│   ├── magic.py             # MagicPlayer（治疗/火焰）（59行）
│   ├── support.py           # get_path / import_csv_layout / import_folder（41行）
│   ├── sound_manager.py     # SoundManager（音频加载/降级处理）（37行）
│   ├── save_manager.py      # JSON原子写入存档（36行）
│   ├── constants.py         # 常量（实体编码/图层名/精灵类型）（30行）
│   ├── weapon.py            # Weapon精灵（短暂存在/朝向放置）（28行）
│   ├── music_state.py       # MusicState（BGM状态管理）（26行）
│   └── tile.py              # Tile瓦片精灵（17行）
├── data/map/                # CSV地图数据（4个文件）
├── graphics/                # PNG图片资源（257个文件）
├── audio/                   # 音频资源（11个文件）
└── font/                    # 字体文件
```

## 许可证

MIT License
