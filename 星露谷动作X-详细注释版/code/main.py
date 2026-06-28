import warnings
import os
import pygame
import sys
import time
import math
from random import randint
from settings import WIDTH, HEIGHT, FPS, WATER_COLOR
from support import get_path
from music_state import MusicState
from level import Level
from sound_manager import SoundManager

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

# Suppress warnings
warnings.simplefilter('ignore', UserWarning)

# ============================================================
# UI 常量定义 — 控制开始画面、死亡画面、胜利画面的颜色与粒子效果
# ============================================================
START_BG_COLOR = (20, 20, 40)
DEATH_BG_COLOR = (40, 0, 0)
TITLE_COLOR = (255, 215, 0)
SUBTITLE_COLOR = (200, 200, 200)
MENU_COLOR = (255, 255, 255)
DEATH_TITLE_COLOR = (255, 0, 0)
PARTICLE_COLOR = (100, 150, 255)
DEATH_PARTICLE_BASE_COLOR = (100, 0, 0)

# ——— 字体尺寸 —
TITLE_FONT_SIZE = 72          # 标题字体大小
SUBTITLE_FONT_SIZE = 36       # 副标题字体大小
MENU_FONT_SIZE = 48           # 菜单选项字体大小
STATS_FONT_SIZE = 36          # 统计数据字体大小

# ——— 屏幕坐标偏移量 —
TITLE_Y_OFFSET = HEIGHT // 4            # 标题垂直位置（屏幕上方1/4处）
SUBTITLE_Y_OFFSET = TITLE_Y_OFFSET + 80 # 副标题垂直位置（标题下方80像素）
START_MENU_Y_OFFSET = HEIGHT // 2 + 110 # 开始菜单"Start"选项垂直位置
QUIT_MENU_Y_OFFSET = HEIGHT // 2 + 180  # 开始菜单"Quit"选项垂直位置
DEATH_MENU_Y_OFFSET = HEIGHT // 2 + 80  # 死亡画面"Restart"选项垂直位置
DEATH_QUIT_Y_OFFSET = HEIGHT // 2 + 140 # 死亡画面"Quit"选项垂直位置

# ——— 粒子效果数量 —
PARTICLE_COUNT_START = 20  # 开始画面漂浮粒子数
PARTICLE_COUNT_DEATH = 30   # 死亡画面粒子数（为性能考虑适当减少）


class Game:
    """
    游戏主类 — 全局入口与状态机。

    管理四个游戏状态：
      - 'start'      : 开始菜单
      - 'game'       : 实际游戏运行
      - 'death'      : 玩家死亡画面
      - 'victory'    : 胜利画面
    以及一个弹窗状态 show_save_dialog（覆盖在 game 之上，不独立成状态）。

    职责包括：
      - 初始化 Pygame 窗口、音频、字体
      - 主循环事件派发与状态切换
      - 粒子动画、菜单高亮等非游戏渲染
    """

    def __init__(self):
        """
        初始化游戏：
          - 创建 Pygame 窗口与时钟
          - 预加载字体（避免每帧重复创建）
          - 通过 SoundManager 加载音效/BGM
          - 加载开始画面背景图
          - 初始化粒子系统与菜单状态
          - 创建 Level 实例并持有玩家引用
          - 检测存档文件，若有则弹出加载/新建存档对话框
        """
        pygame.init()
        pygame.display.set_caption('Stardew Valley Action X')
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        # Game states
        self.game_state = 'start'  # 'start'（开始画面）, 'game'（游戏运行）, 'death'（死亡）, 'victory'（胜利）

        # Fonts (pre-loaded for performance)
        self.font_title = pygame.font.Font(None, TITLE_FONT_SIZE)       # 大标题字体
        self.font_subtitle = pygame.font.Font(None, SUBTITLE_FONT_SIZE) # 副标题字体
        self.font_menu = pygame.font.Font(None, MENU_FONT_SIZE)         # 菜单选项字体
        self.font_stats = pygame.font.Font(None, STATS_FONT_SIZE)       # 统计数据显示字体
        self.font_dialog_title = pygame.font.Font(None, 48)             # 存档对话框标题字体
        self.font_dialog_option = pygame.font.Font(None, 36)            # 存档对话框选项字体
        self.font_dialog_hint = pygame.font.Font(None, 28)              # 存档对话框提示字体

        # Audio — centralised via SoundManager
        self.audio = SoundManager()                                     # 音频管理器单例
        self.start_music = self.audio.load('game_bgm.ogg', volume=0.3)  # 主菜单背景音乐
        self.menu_move_sound = self.audio.load('sword.wav', volume=0.5) # 菜单上下移动音效
        self.menu_select_sound = self.audio.load('sword.wav', volume=0.5)# 菜单确认音效
        self.death_sound = self.audio.load('death.wav', volume=0.6)     # 死亡音效

        self.audio.play_music('game_bgm.ogg')

        # Start screen background
        try:
            bg_raw = pygame.image.load(get_path('../graphics/start_bg.png')).convert()
            self.start_bg = pygame.transform.scale(bg_raw, (WIDTH, HEIGHT))
        except Exception:
            self.start_bg = None  # 背景图片不存在时使用纯色背景

        # Particle animation data
        self.death_particles = []
        self._init_death_particles()

        # Menu state
        self.selected_menu_option = 0  # 0 = Start（开始游戏）, 1 = Quit（退出游戏）

        # Level system setup
        self.current_map_id = 'default'        # 当前地图ID
        self.player = None                     # 玩家对象引用，由Level创建后赋值
        self.show_save_dialog = False          # 是否显示存档对话框
        self.save_dialog_result = None         # 存档对话框用户选择结果：'c'（继续）/ 'n'（新游戏）
        save_path = 'savegame.json'
        if os.path.exists(save_path):
            self.show_save_dialog = True
            self.save_dialog_result = None
        self.level = Level(self.current_map_id, player=None, loaded_data=None)
        self.player = self.level.player

    def _restart_game(self):
        """
        完全重启游戏流程，在死亡或胜利后按 R 键调用。

        执行顺序：
          1. 停止所有正在播放的音效（ResourceManager 管理的一次性音效）
          2. 停止背景音乐（pygame.mixer.music）
          3. 重置 MusicState（音乐状态跟踪器，避免音频状态残留）
          4. 销毁旧 Level，创建全新的 Level 实例（含新地图、新玩家、新敌人）
          5. 重新获得玩家引用
          6. 设置游戏状态为 'game' 进入游戏循环
          7. 重新加载并循环播放 BGM
        """
        from resource_manager import ResourceManager
        ResourceManager.instance().stop_all_sounds()
        pygame.mixer.music.stop()
        MusicState.reset()
        self.player = None
        self.level = Level(self.current_map_id, player=None, loaded_data=None)
        self.player = self.level.player
        self.game_state = 'game'
        pygame.mixer.music.load(get_path('../audio/game_bgm.ogg'))
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)

    def _init_death_particles(self):
        """
        初始化死亡画面的浮动粒子效果。

        生成 PARTICLE_COUNT_DEATH（30）个粒子，每个粒子包含：
          - x, y          : 随机初始位置（全屏范围）
          - size          : 粒子半径（1~4 像素）
          - speed_x/y     : 水平和垂直速度（-2 ~ 2，飘动效果）
          - color         : RGB 颜色，R 分量随机（100~255），G/B=0（红色系）
        """
        self.death_particles = []
        for _ in range(PARTICLE_COUNT_DEATH):
            particle = {
                'x': randint(0, WIDTH),
                'y': randint(0, HEIGHT),
                'size': randint(1, 4),
                'speed_x': randint(-2, 2),
                'speed_y': randint(-2, 2),
                'color': (randint(100, 255), 0, 0)
            }
            self.death_particles.append(particle)

    def _update_and_draw_death_particles(self):
        """
        更新并绘制死亡画面的红色浮动粒子。

        每帧对每个粒子执行：
          1. 按 speed_x/speed_y 更新位置
          2. 超出屏幕边缘时从相对侧重新进入（环绕效果）
          3. 在当前位置画一个实心圆
        """
        for particle in self.death_particles:
            # Update position
            particle['x'] += particle['speed_x']
            particle['y'] += particle['speed_y']

            # Wrap around screen edges
            if particle['x'] < 0:
                particle['x'] = WIDTH
            elif particle['x'] > WIDTH:
                particle['x'] = 0
            if particle['y'] < 0:
                particle['y'] = HEIGHT
            elif particle['y'] > HEIGHT:
                particle['y'] = 0

            # Draw particle
            pygame.draw.circle(self.screen, particle['color'],
                             (int(particle['x']), int(particle['y'])), particle['size'])

    def _render_highlighted_text(self, text, font, color, highlight_color, center_pos, selected=False):
        """
        渲染带选中高亮效果的菜单文字。

        参数：
          text           : 要渲染的文本
          font           : 使用的 Pygame Font 对象
          color          : 未选中时的文字颜色（RGB 元组）
          highlight_color: 选中时的高亮颜色
          center_pos     : 文字居中位置 (x, y)
          selected       : 是否为当前选中的菜单项

        高亮效果：
          - 每隔 100ms 闪烁一次（利用 get_ticks() 取整判断奇偶）
          - 高亮时在文字背后绘制半透明灰色背景块（制造选中感）
        """
        if selected:
            # Create pulsing highlight effect
            pulse = (pygame.time.get_ticks() // 100) % 2
            if pulse:
                # Draw highlight background
                rendered_text = font.render(text, True, highlight_color)
                highlight_rect = rendered_text.get_rect(center=center_pos)
                highlight_surface = pygame.Surface((highlight_rect.width + 20, highlight_rect.height + 10))
                highlight_surface.fill((50, 50, 50))
                highlight_surface.set_alpha(100)
                self.screen.blit(highlight_surface, highlight_rect.move(-10, -5))
            else:
                rendered_text = font.render(text, True, color)
        else:
            rendered_text = font.render(text, True, color)

        text_rect = rendered_text.get_rect(center=center_pos)
        self.screen.blit(rendered_text, text_rect)

    def show_start_screen(self):
        """
        渲染开始菜单画面。

        包含元素：
          1. 背景图片（若存在）或纯色填充
          2. 背景音乐播放（仅在音乐播放器空闲时启动）
          3. 动画标题 — Y 轴以正弦波上下浮动（频率 0.005，振幅 10 像素）
          4. "Start Game" / "Quit Game" 两个菜单选项，支持高亮选中
          5. 蓝色浮动粒子装饰（沿对角线方向规律飘动，营造星空感）
        """
        # 背景
        if self.start_bg:
            self.screen.blit(self.start_bg, (0, 0))
        else:
            self.screen.fill(START_BG_COLOR)

        # Play start music
        if self.start_music and not pygame.mixer.get_busy():
            self.start_music.play(-1)

        # Animated Title
        current_time = pygame.time.get_ticks()
        title_y_offset = 10 * math.sin(current_time * 0.005)
        title_text = self.font_title.render("Stardew Valley Action X", True, TITLE_COLOR)
        title_rect = title_text.get_rect(center=(WIDTH // 2, TITLE_Y_OFFSET + title_y_offset))
        self.screen.blit(title_text, title_rect)

        # Menu options with highlight
        self._render_highlighted_text("Start Game", self.font_menu, MENU_COLOR, TITLE_COLOR,
                                    (WIDTH // 2, START_MENU_Y_OFFSET), self.selected_menu_option == 0)
        self._render_highlighted_text("Quit Game", self.font_menu, MENU_COLOR, TITLE_COLOR,
                                    (WIDTH // 2, QUIT_MENU_Y_OFFSET), self.selected_menu_option == 1)

        # Decorative elements - floating particles
        for i in range(PARTICLE_COUNT_START):
            x = (current_time // 30 + i * 60) % WIDTH
            y = (HEIGHT - 150 - (current_time // 20 + i * 30) % (HEIGHT // 2)) % HEIGHT
            size = 2 + (i % 2)
            pygame.draw.circle(self.screen, PARTICLE_COLOR, (x, y), size)

    def show_death_screen(self):
        """
        渲染死亡画面。

        画面布局（从上到下）：
          1. 暗红色纯色背景（DEATH_BG_COLOR）
          2. 红色大标题 "You Died"
          3. 本次游戏获得的总经验值显示
          4. 操作提示："Press R to Restart" / "Press ESC to Quit"
          5. 红色浮动粒子动画（使用 _update_and_draw_death_particles）
        """
        # 暗红色背景
        self.screen.fill(DEATH_BG_COLOR)

        # Death title
        death_text = self.font_title.render("You Died", True, DEATH_TITLE_COLOR)
        death_rect = death_text.get_rect(center=(WIDTH // 2, TITLE_Y_OFFSET))
        self.screen.blit(death_text, death_rect)

        # Stats display
        exp = self.player.exp if self.player else 0
        exp_text = self.font_stats.render(f"Experience Gained: {exp}", True, MENU_COLOR)
        exp_rect = exp_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(exp_text, exp_rect)

        # Restart options
        restart_text = self.font_menu.render("Press R to Restart", True, MENU_COLOR)
        quit_text = self.font_menu.render("Press ESC to Quit", True, MENU_COLOR)

        restart_rect = restart_text.get_rect(center=(WIDTH // 2, DEATH_MENU_Y_OFFSET))
        quit_rect = quit_text.get_rect(center=(WIDTH // 2, DEATH_QUIT_Y_OFFSET))

        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(quit_text, quit_rect)

        # Animated death particles
        self._update_and_draw_death_particles()

    def show_victory_screen(self):
        """
        渲染胜利画面（Boss 被击败后显示）。

        画面布局：
          1. 深蓝色背景
          2. "YOU WIN!" 金色标题（Y 轴匀速上下摆动）
          3. 副标题 "The Boss has been defeated!"
          4. 最终经验值显示
          5. 操作提示："Press R to Play Again" / "Press ESC to Quit"
          6. 金色漂浮粒子装饰（对角线规律运动，庆祝效果）
        """
        self.screen.fill((10, 10, 30))
        current_time = pygame.time.get_ticks()

        # 动画标题 — Y 轴在两秒周期内匀速上下移动
        title_y_offset = 8 * (pygame.time.get_ticks() % 2000) / 2000.0
        victory_text = self.font_title.render("YOU WIN!", True, (255, 215, 0))
        victory_rect = victory_text.get_rect(center=(WIDTH // 2, HEIGHT // 3 + title_y_offset))
        self.screen.blit(victory_text, victory_rect)

        # Subtitle
        sub_text = self.font_subtitle.render("The Boss has been defeated!", True, (200, 200, 255))
        sub_rect = sub_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(sub_text, sub_rect)

        # Stats
        exp = self.player.exp if self.player else 0
        exp_text = self.font_stats.render(f"Final Experience: {exp}", True, (255, 255, 255))
        exp_rect = exp_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
        self.screen.blit(exp_text, exp_rect)

        # Menu options
        restart_text = self.font_menu.render("Press R to Play Again", True, (255, 255, 255))
        quit_text = self.font_menu.render("Press ESC to Quit", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 140))
        quit_rect = quit_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 200))
        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(quit_text, quit_rect)

        # Floating golden particles
        for i in range(30):
            x = (current_time // 15 + i * 57) % WIDTH
            y = (HEIGHT - ((current_time // 12 + i * 37) % HEIGHT))
            pygame.draw.circle(self.screen, (255, 215, 0), (x, int(y)), 2 + (i % 3))

    def run(self):
        """
        游戏主循环 — 全局状态机调度器。

        状态流转图：
          ┌─────────┐   Enter键选中Start   ┌──────────┐
          │  start  │ ──────────────────► │   game   │
          └─────────┘                     └────┬─────┘
                                               │
                                  health <= 0  │  _trigger_victory
                                     ┌────────┴────────┐
                                     ▼                 ▼
                                 ┌──────┐         ┌─────────┐
                                 │death │         │ victory │
                                 └──┬───┘         └────┬────┘
                                    │  R键              │  R键
                                    └──► _restart_game()◄──┘
                                                │
                                          ┌──────▼──────┐
                                          │    game     │
                                          └─────────────┘

        除上述四个状态外，还有 save_dialog 弹窗：
          - 在进入 'game' 状态之前，若检测到 savegame.json 存在，则弹出对话框
          - 按 C 键加载存档继续 / 按 N 键开始新游戏
        """
        from save_manager import save_game, load_game
        last_time = time.time()
        while True:
            dt = time.time() - last_time
            last_time = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.game_state == 'start':
                    # 开始画面事件处理：
                    #   Enter   → 选中 "Start Game" 则切至 'game'，选中 "Quit Game" 则退出
                    #   Escape  → 直接退出游戏
                    #   Up/Down → 切换菜单选项（上/下循环）
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if self.menu_select_sound:
                                self.menu_select_sound.play()
                            if self.selected_menu_option == 0:  # Start Game
                                if self.start_music:
                                    self.start_music.stop()
                                self.game_state = 'game'
                            elif self.selected_menu_option == 1:  # Quit Game
                                pygame.quit()
                                sys.exit()
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                        elif event.key == pygame.K_UP:
                            if self.menu_move_sound:
                                self.menu_move_sound.play()
                            self.selected_menu_option = (self.selected_menu_option - 1) % 2
                        elif event.key == pygame.K_DOWN:
                            if self.menu_move_sound:
                                self.menu_move_sound.play()
                            self.selected_menu_option = (self.selected_menu_option + 1) % 2

                elif self.game_state == 'death':
                    # 死亡画面事件处理：
                    #   R     → 调用 _restart_game() 完全重启
                    #   ESC   → 退出游戏
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self._restart_game()
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()

                elif self.game_state == 'victory':
                    # 胜利画面事件处理：与死亡画面相同
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self._restart_game()
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()

                elif self.show_save_dialog:
                    # 存档对话框事件处理：
                    #   C → 加载已有存档继续游戏
                    #   N → 开始新游戏（忽略存档）
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_c:
                            self.save_dialog_result = 'c'
                        elif event.key == pygame.K_n:
                            self.save_dialog_result = 'n'

                else:
                    # 游戏运行中事件处理：
                    #   B       → 打开/关闭升级菜单（toggle_menu）
                    #   M       → 打开/关闭大地图（toggle_map）
                    #   P       → 游戏暂停时保存存档
                    #   鼠标滚轮 → 切换武器（不暂停时）
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_b:
                            self.level.toggle_menu()
                        if event.key == pygame.K_m:
                            self.level.toggle_map()
                        # Save game when paused and P is pressed
                        if event.key == pygame.K_p and getattr(self.level, 'game_paused', False):
                            save_game(self.level.get_savable_state())
                    # Mouse wheel to switch weapon
                    if event.type == pygame.MOUSEWHEEL:
                        if self.player and not getattr(self.level, 'game_paused', False):
                            self.player.cycle_weapon(event.y)

            if self.game_state == 'start':
                self.show_start_screen()
                pygame.display.update()
                self.clock.tick(FPS)
                continue

            elif self.game_state == 'death':
                self.show_death_screen()
                pygame.display.update()
                self.clock.tick(FPS)
                continue

            elif self.game_state == 'victory':
                self.show_victory_screen()
                pygame.display.update()
                self.clock.tick(FPS)
                continue

            # ============================================================
            # 存档对话框渲染与逻辑
            # ============================================================
            # 渲染过程：
            #   1. 用 WATER_COLOR 填充背景
            #   2. 绘制圆角对话框主体（带阴影效果）
            #   3. 标题："Save file detected!"
            #   4. 提示："Press C to Continue or N for New Game"
            #   5. 按钮提示文字
            # ============================================================
            if self.show_save_dialog:
                self.screen.fill(WATER_COLOR)
                # Draw a rounded rectangle background for the dialog
                dialog_width, dialog_height = 600, 220
                dialog_x = (self.screen.get_width() - dialog_width) // 2
                dialog_y = (self.screen.get_height() - dialog_height) // 2
                dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
                # Shadow (alpha not supported on display surface, use semi-transparent fill)
                shadow_rect = dialog_rect.move(6, 6)
                shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect(), border_radius=24)
                self.screen.blit(shadow_surf, shadow_rect)
                # Main box
                pygame.draw.rect(self.screen, (30, 30, 40), dialog_rect, border_radius=24)
                pygame.draw.rect(self.screen, (255, 215, 0), dialog_rect, 4, border_radius=24)

                # Title
                text1 = self.font_dialog_title.render("Save file detected!", True, (255,255,255))
                self.screen.blit(text1, (dialog_x + (dialog_width - text1.get_width())//2, dialog_y + 30))

                # Instructions
                text2 = self.font_dialog_option.render("Press C to Continue or N for New Game", True, (255,255,0))
                self.screen.blit(text2, (dialog_x + (dialog_width - text2.get_width())//2, dialog_y + 100))

                # Button hints
                c_hint = self.font_dialog_hint.render("[C] Continue", True, (180,255,180))
                n_hint = self.font_dialog_hint.render("[N] New Game", True, (255,180,180))
                self.screen.blit(c_hint, (dialog_x + 80, dialog_y + 160))
                self.screen.blit(n_hint, (dialog_x + dialog_width - n_hint.get_width() - 80, dialog_y + 160))

                pygame.display.update()
                if self.save_dialog_result:
                    if self.save_dialog_result == 'c':
                        loaded_data = load_game('savegame.json')
                        if loaded_data and 'player' in loaded_data:
                            self.player.from_dict(loaded_data['player'])
                    # 'n' = new game: keep existing level as-is
                    self.show_save_dialog = False
                self.clock.tick(FPS)
                continue

            self.screen.fill(WATER_COLOR)
            self.level.run(dt)

            # ——— 检测玩家死亡 ———
            # 条件：玩家存在 && 血量 <= 0 && 尚未处于死亡状态
            # 触发后：停止所有音效和BGM，播放死亡音效，状态切至 'death'
            if self.player and self.player.health <= 0 and self.game_state != 'death':
                self.game_state = 'death'
                from resource_manager import ResourceManager
                ResourceManager.instance().stop_all_sounds()
                pygame.mixer.music.stop()
                if self.death_sound:
                    self.death_sound.play()

            # ——— 检测 Boss 是否被击败（胜利条件） ———
            # 条件：游戏状态为 'game' && Level 的 _trigger_victory 标记为 True
            # 触发后：停止所有音效和BGM，状态切至 'victory'
            if self.game_state == 'game' and getattr(self.level, '_trigger_victory', False):
                self.game_state = 'victory'
                from resource_manager import ResourceManager
                ResourceManager.instance().stop_all_sounds()
                pygame.mixer.music.stop()

            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == '__main__':
    game = Game()
    game.run()
