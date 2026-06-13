"""
俄罗斯方块 — 使用 Python + Pygame

  游戏规则：
    - 标准 10×20 网格，7 种经典方块（I O T L J S Z）
    - 方块从顶部下落，玩家可移动 + 旋转 + 硬降
    - 满行自动消除并计分，速度随等级递增
    - 方块无法生成时游戏结束

  运行方式：
    1. 安装依赖：pip install pygame
    2. 启动游戏：python tetris.py

  操作按键：
    ← →       左/右移动当前方块
    ↓         加速下落（软降）
    ↑ 或 X    顺时针旋转 90°
    Z         逆时针旋转 90°
    空格      硬降（直接落到底部并锁定）
    C         暂存当前方块 / 取出已暂存方块（每块限用一次）
    长按 R    游戏进行中长按 1 秒重新开局
    R（结束） 游戏结束后按 R 重新开始
    ESC       退出游戏

"""


import pygame    # Pygame游戏开发库
import random    # random随机

#  游戏常量 — 棋盘尺寸和颜色

# --- 棋盘尺寸 ---
COLS = 10            # 列数（宽度方向）
ROWS = 20            # 行数（高度方向）
CELL = 30            # 每个小格子的边长（像素），格子和方块都基于这个大小绘制

WIDTH  = COLS * CELL + 200   # 窗口总宽度 = 500 像素
HEIGHT = ROWS * CELL          # 窗口总高度 = 600 像素

# 颜色定义（RGB 三元组，每个值 0~255
# RGB 表示 Red / Green / Blue 三种光的强度，数值越大越亮
BLACK   = (0, 0, 0)           # 纯黑 — 空白格子、背景
GRAY    = (40, 40, 40)        # 深灰 — 网格线
WHITE   = (200, 200, 200)     # 浅灰白 — 文字
CYAN    = (30, 160, 160)      # 青色    — I 形（长条）
YELLOW  = (180, 180, 20)      # 黄色    — O 形（方块）
PURPLE  = (120, 20, 160)      # 紫色    — T 形
BLUE    = (30, 60, 180)       # 蓝色    — J 形
ORANGE  = (200, 120, 0)       # 橙色    — L 形
GREEN   = (30, 170, 50)       # 绿色    — S 形
RED     = (190, 40, 40)       # 红色    — Z 形

# 每种方块由 4 个旋转状态组成，每个旋转状态是 4 个格子的坐标列表
# 坐标以 4×4 的小网格为参考系，(x, y) 中 x 是列号、y 是行号
# 4 个旋转状态按 0° → 90° → 180° → 270° 顺时针排列
# 在一个 4×4 的"局部坐标"定义，旋转时只需换一套坐标
# 实际绘制时，把局部坐标加上方块在棋盘上的 (x, y) 偏移量
# 即使是对称方块，在180°时也不是完全一样，因为重心，所以下落位置发生变化

SHAPES = {
    # 长条
    # 0横 90竖 180横 270竖
    'I': {
        'shape': [
            [(0,1),(1,1),(2,1),(3,1)],   # 旋转状态 0：横向平躺
            [(2,0),(2,1),(2,2),(2,3)],   # 旋转状态 1：右竖直站立
            [(0,2),(1,2),(2,2),(3,2)],   # 旋转状态 2：横向平躺（镜面）
            [(1,0),(1,1),(1,2),(1,3)],   # 旋转状态 3：左竖直站立
        ],
        'color': CYAN,
    },

    # 方块
    # 旋转不变
    'O': {
        'shape': [
            [(0,0),(1,0),(0,1),(1,1)],   # 所有状态相同
            [(0,0),(1,0),(0,1),(1,1)],
            [(0,0),(1,0),(0,1),(1,1)],
            [(0,0),(1,0),(0,1),(1,1)],
        ],
        'color': YELLOW,
    },

    # T形
    'T': {
        'shape': [
            [(1,0),(0,1),(1,1),(2,1)],   # 0°:朝上
            [(1,0),(1,1),(2,1),(1,2)],   # 90°:朝右
            [(0,1),(1,1),(2,1),(1,2)],   # 180°:朝下 "⊤" 形
            [(1,0),(0,1),(1,1),(1,2)],   # 270°:朝左
        ],
        'color': PURPLE,
    },

    # L形
    'L': {
        'shape': [
            [(2,0),(0,1),(1,1),(2,1)],   # 0°: 突起在右上
            [(1,0),(1,1),(1,2),(2,2)],   # 90°: L 右下
            [(0,1),(1,1),(2,1),(0,2)],   # 180°: 左下
            [(0,0),(1,0),(1,1),(1,2)],   # 270°: 左上
        ],
        'color': ORANGE,
    },

    # J形
    # L 形镜面翻转
    'J': {
        'shape': [
            [(0,0),(0,1),(1,1),(2,1)],   # 0°
            [(1,0),(2,0),(1,1),(1,2)],   # 90°
            [(0,1),(1,1),(2,1),(2,2)],   # 180°
            [(1,0),(1,1),(0,2),(1,2)],   # 270°:J
        ],
        'color': BLUE,
    },

    # S形
    # 先右后左
    'S': {
        'shape': [
            [(1,0),(2,0),(0,1),(1,1)],   # 0°: 横 S
            [(1,0),(1,1),(2,1),(2,2)],   # 90°: 竖 S
            [(1,1),(2,1),(0,2),(1,2)],   # 180°: 横 S（镜面）
            [(0,0),(0,1),(1,1),(1,2)],   # 270°: 竖 S（镜面）
        ],
        'color': GREEN,
    },

    # Z形
    # S形镜面
    'Z': {
        'shape': [
            [(0,0),(1,0),(1,1),(2,1)],   # 0°: 横 Z
            [(2,0),(1,1),(2,1),(1,2)],   # 90°: 竖 Z
            [(0,1),(1,1),(1,2),(2,2)],   # 180°: 横 Z（镜面）
            [(1,0),(0,1),(1,1),(0,2)],   # 270°: 竖 Z（镜面）
        ],
        'color': RED,
    },
}

class Tetris:

    def __init__(self):
        pygame.init()
        pygame.key.stop_text_input()

        # 创建游戏窗口，尺寸为 WIDTH×HEIGHT 像素
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        # 设置窗口标题栏文字
        pygame.display.set_caption("俄罗斯方块 — Tetris")

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("simsun", 24, bold=True)
        self.font_small = pygame.font.SysFont("simsun", 18)
        # 初始化所有游戏状态
        self.reset()

    # 重置reset，将所有游戏状态恢复到初始值
    # 游戏首次启动时调用一次，之后每次重新开始游戏时也调用

    def reset(self):
        """重置游戏状态 清空棋盘、分数归零、速度初始化、发新牌"""

        # ── 在重置前保存 AI 模式状态，以免自动重开时关闭 AI ──
        was_ai = getattr(self, 'ai_mode', False)

        # 如果格子为空，存储 BLACK(0,0,0)
        # 如果格子被方块占据，存储该方块的颜色
        # grid[0]是顶部
        self.grid = [[BLACK for _ in range(COLS)] for _ in range(ROWS)]

        self.score = 0              # 当前得分
        self.lines_cleared = 0      # 累计消除的行数
        self.level = 1              # 当前等级（每消 10 行升 1 级）
        self.game_over = False      # 游戏是否结束的标记
        self.fall_time = 0          # 累计下落计时器（毫秒），超过 fall_speed 就下落一格
        self.fall_speed = 500       # 下落间隔（毫秒），初始 0.5 秒下落一格

        # 随机选两个方块名：current 是正在控制的那一个，next 是预览区显示的
        self.current_name = random.choice(list(SHAPES.keys()))  # 当前方块名
        self.next_name    = random.choice(list(SHAPES.keys()))  # 下一个方块名
        self.rotation = 0  # 当前旋转状态，取值 0 / 1 / 2 / 3，对应 0° / 90° / 180° / 270°
        self.x = COLS // 2 - 2  # 方块左上角在棋盘上的列坐标（水平居中）
        self.y = 0               # 方块左上角在棋盘上的行坐标（从顶部开始）

        # 暂存Hold
        # hold_name 记录暂存的方块名，None 表示暂存区为空。
        # hold_used 是否已经使用过暂存
        self.hold_name = None
        self.hold_used = False

        # ───── 键盘轮询状态 — 用来实现可靠的按键检测 ─────
        # 需要追踪的所有按键列表（排除 ESC，因为 ESC 在事件循环里处理）
        # 存储的方式为 {按键: False/True} 的字典，因为 hash 查表比 list 遍历快
        self._track_keys = [
            pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN,
            pygame.K_UP, pygame.K_x, pygame.K_z,
            pygame.K_SPACE, pygame.K_c, pygame.K_r, pygame.K_a,
            pygame.K_ESCAPE,
        ]
        # _key_prev：上一帧每个键的按下状态，和当前帧对比就知道"刚刚按下"还是"一直按住"
        self._key_prev = {k: False for k in self._track_keys}

        # ───── DAS（延迟自动移位）系统 ─────
        # DAS = Delayed Auto Shift，即"按住方向键时，先等一小会儿，
        # 然后自动连续移动"。几乎所有俄罗斯方块都用这个机制。
        # _das_time[k] 记录方向键 k 最近一次"触发移动"的时间（毫秒）
        # _das_fired[k] 标记该键是否已经度过首次延迟，进入连续重复阶段
        self._das_time = {}
        self._das_fired = {}
        self._das_delay = 170      # 首次延迟：按住 170ms 后才开始连续移动
        self._das_interval = 50    # 连续间隔：进入连续阶段后每 50ms 移动一次

        # ───── R 键长按重开（游戏进行中） ─────
        # 游戏中按住 R 键满 1 秒 → 直接重新开局。
        # _r_press_time 记录 R 键开始按下的时间戳（毫秒），0 表示当前未按住
        # _r_restarted 防止同一次按住过程中重复触发 reset()
        self._r_press_time = 0
        self._r_restarted = False

        # AI
        self.ai_mode = False
        self._ai_planned = False
        self._ai_target_rotation = 0
        self._ai_target_x = 0
        self._ai_step_delay = 0   # AI 每步操作之间的冷却计时器（ms）

        # 恢复 AI 模式（避免 reset 关闭正在运行的 AI）
        self.ai_mode = was_ai

        # 退出标记（ESC 触发，由 run() 循环读取）
        self._quit = False

        # 生成第一个可操作的方块
        self.spawn_piece()

    # 方块生成spawn_piece
    def spawn_piece(self):
        """将预览方块提升为当前方块，并随机生成新的预览方块"""

        # 把"下一个方块"变为"当前方块"
        self.current_name = self.next_name
        # 从 7 种方块中随机选一个作为新的"下一个方块"
        self.next_name = random.choice(list(SHAPES.keys()))
        # 新方块总是从旋转状态 0 开始，放在顶部中央
        self.rotation = 0
        self.x = COLS // 2 - 2   # 计算水平中心位置：10 / 2 - 2 = 3（方块 4×4 框的左上角）
        self.y = 0               # 第 0 行开始下落

        # 如果新生方块在出生位置就已经和其他方块重叠，游戏结束
        if self.collides(self.get_current_blocks(), self.x, self.y):
            self.game_over = True

    def get_current_blocks(self):
        """返回当前方块在 4×4 局部坐标系中的 4 个格子坐标"""
        return SHAPES[self.current_name]['shape'][self.rotation]

    # 碰撞检测collides
    def collides(self, blocks, px, py):
        """检查方块在(px, py)位置是否与边界或已有方块碰撞"""
        for bx, by in blocks:       # 遍历方块的 4 个格子
            gx = px + bx            # 格子在实际棋盘上的列坐标
            gy = py + by            # 格子在实际棋盘上的行坐标

            if gx < 0 or gx >= COLS or gy >= ROWS:
                return True # 超出边界，有碰撞

            if gy >= 0 and self.grid[gy][gx] != BLACK:
                return True # 目标位置已被已定格的方块占据，有碰撞

        return False # 没有任何冲突，可以移动/旋转

    # 锁定方块lock_piece
    def lock_piece(self):
        """将当前方块写入棋盘，消除满行，重置暂存标记，生成新方块"""

        # 获取当前方块的 4 个局部坐标 + 颜色
        blocks = self.get_current_blocks()
        color = SHAPES[self.current_name]['color']

        # 逐格写入棋盘：把 grid 对应位置的颜色改为方块颜色
        for bx, by in blocks:
            gx = self.x + bx
            gy = self.y + by

            if 0 <= gy < ROWS and 0 <= gx < COLS:
                self.grid[gy][gx] = color

        # 消除所有满行
        self.clear_lines()

        # 允许再次使用暂存功能
        self.hold_used = False

        # 生成下一个要操作的方块
        self.spawn_piece()

    # clear_lines
    def clear_lines(self):
        """消除所有满行，计算得分，更新等级和下落速度"""

        # 找出所有满的行号
        full_rows = []
        for r in range(ROWS):
            if all(self.grid[r][c] != BLACK for c in range(COLS)):
                full_rows.append(r)

        if not full_rows:
            return

        for r in sorted(full_rows, reverse=True):
            del self.grid[r]

        for _ in full_rows:
            self.grid.insert(0, [BLACK for _ in range(COLS)])

        #   1 = 100
        #   2 = 300
        #   3 = 500
        #   4 = 800
        n = len(full_rows)
        points = {1: 100, 2: 300, 3: 500, 4: 800}[n]
        self.score += points
        self.lines_cleared += n

        # 升级
        self.level = self.lines_cleared // 10 + 1

        # 下落速度
        self.fall_speed = max(50, 500 - (self.level - 1) * 40)

    # 移动方块move
    # dx=-1左移，dy=1下移。
    def move(self, dx, dy):
        """尝试将方块位移 (dx, dy)，返回是否成功"""
        if not self.collides(self.get_current_blocks(), self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            return True
        return False   # 移动失败撞墙/落地/撞到方块）

    # 旋转方块rotate
    def rotate(self, direction=1):
        """direction=1 顺时针，direction=-1 逆时针"""

        # 计算新的旋转状态：加 direction 后对 4 取余
        new_rotation = (self.rotation + direction) % 4
        new_blocks = SHAPES[self.current_name]['shape'][new_rotation]

        # 原地旋转
        if not self.collides(new_blocks, self.x, self.y):
            self.rotation = new_rotation
            return

        for offset in (1, -1, 2, -2):
            if not self.collides(new_blocks, self.x + offset, self.y):
                self.x += offset       # 水平偏移
                self.rotation = new_rotation  # 应用新旋转
                return

    # 暂存方块hold_piece
    def hold_piece(self):
        """暂存 / 切换方块 — 每次方块落定前限用一次"""
        # 如果这一轮已经用过暂存，跳过
        if self.hold_used:
            return

        if self.hold_name is None:

            self.hold_name = self.current_name

            self.spawn_piece()
        else:

            self.hold_name, self.current_name = self.current_name, self.hold_name
            self.rotation = 0
            self.x = COLS // 2 - 2
            self.y = 0

        self.hold_used = True

    # 硬降drop_hard
    def drop_hard(self):

        while self.move(0, 1):
            pass
        self.lock_piece()

    # 虚影get_ghost_y
    def get_ghost_y(self):
        """返回当前方块硬降落点的 y 坐标（供虚影绘制使用）"""
        ghost_y = self.y
        blocks = self.get_current_blocks()
        # 只要下一行不碰撞，就继续下移
        while not self.collides(blocks, self.x, ghost_y + 1):
            ghost_y += 1
        return ghost_y

    def handle_input(self):
        """每帧调用一次 — 读取键盘状态并转换为游戏操作"""

        # 获取当前这一帧所有按键的物理状态（列表，按下为 True）
        keys = pygame.key.get_pressed()
        # 获取当前时间（毫秒），用于 DAS 计时和 R 键长按计时
        now = pygame.time.get_ticks()

        # ───── ESC 退出 — 任何时候都生效 ─────
        if keys[pygame.K_ESCAPE] and not self._key_prev[pygame.K_ESCAPE]:
            self._quit = True
            return

        # ───── 游戏结束时的输入处理 ─────
        # 游戏结束后只响应两件事：按 R 重开、更新按键状态记录
        if self.game_over:
            # 刚按下 R 键（不是一直按住） → 重新开始
            if keys[pygame.K_r] and not self._key_prev[pygame.K_r]:
                self.reset()
                self._key_prev = {k: keys[k] for k in self._track_keys}
                return
            # 更新按键记录后直接返回，不处理任何游戏内操作
            self._key_prev = {k: keys[k] for k in self._track_keys}
            return

        # ───── AI 模式切换（A 键）— 放在 AI 拦截之前 ─────
        if keys[pygame.K_a] and not self._key_prev[pygame.K_a]:
            self.ai_mode = not self.ai_mode
            self._ai_planned = False

        # ───── AI 模式下跳过所有玩家操作 ─────
        if self.ai_mode:
            self._key_prev = {k: keys[k] for k in self._track_keys}
            return

        # ───── R 键长按重开（游戏进行中） ─────
        # 按住 R 键：计时，满 1000ms 触发 reset
        if keys[pygame.K_r]:
            if self._r_press_time == 0:
                # R 键刚被按下，记录开始时间
                self._r_press_time = now
                self._r_restarted = False   # 重置"已完成重开"标记
            elif not self._r_restarted and now - self._r_press_time >= 1000:
                # 按住超过 1 秒且尚未触发过 → 重开
                self.reset()
                self._r_press_time = 0      # 计时器归零
                self._r_restarted = True     # 标记已完成，防止重复触发
                self._key_prev = {k: keys[k] for k in self._track_keys}
                return
        else:
            # R 键松开了，计时器归零
            self._r_press_time = 0

        # ───── 方向键移动 — DAS 三阶段状态机 ─────
        # 移动键映射：pygame 键常量 → (dx, dy) 位移量
        move_keys = {
            pygame.K_LEFT:  (-1, 0),   # 左箭头：x 减 1（向左移一格）
            pygame.K_RIGHT: (1, 0),    # 右箭头：x 加 1（向右移一格）
            pygame.K_DOWN:  (0, 1),    # 下箭头：y 加 1（向下加速）
        }

        for k, (dx, dy) in move_keys.items():
            if keys[k]:   # 该键当前被按住
                if not self._key_prev[k]:
                    # 【阶段 1 — 首次按下】
                    # 上一帧没按、这一帧按了 → 立即移动一格
                    self.move(dx, dy)
                    self._das_time[k] = now     # 记录首次移动的时间
                    self._das_fired[k] = False  # 尚未进入连续重复阶段
                elif not self._das_fired[k]:
                    # 【阶段 2 — 延迟等待】
                    # 一直按住但还没进入重复阶段 → 检查是否满了延迟阈值
                    if now - self._das_time[k] >= self._das_delay:
                        # 满了 170ms，触发一次移动并进入连续重复阶段
                        self.move(dx, dy)
                        self._das_time[k] = now   # 重置计时起点
                        self._das_fired[k] = True # 进入连续重复阶段
                else:
                    # 【阶段 3 — 连续重复】
                    # 已经进入连续重复阶段 → 每隔 interval 毫秒移动一次
                    if now - self._das_time[k] >= self._das_interval:
                        self.move(dx, dy)
                        self._das_time[k] = now   # 重置计时起点

        # ───── 单次触发操作 ─────
        # 这些操作只在"按下的那一瞬间"触发一次，持续按住不会重复触发。
        # 实现方式：检查"当前是否按住"且"上一帧没有按住"。
        #
        # 顺时针旋转（↑ 或 X）
        # K_UP 或 K_x 中任意一个刚被按下就触发
        if (keys[pygame.K_UP] or keys[pygame.K_x]) and \
           not (self._key_prev[pygame.K_UP] or self._key_prev[pygame.K_x]):
            self.rotate(1)          # direction=1 → 顺时针
        # 逆时针旋转（Z）
        if keys[pygame.K_z] and not self._key_prev[pygame.K_z]:
            self.rotate(-1)         # direction=-1 → 逆时针
        # 硬降（空格）
        if keys[pygame.K_SPACE] and not self._key_prev[pygame.K_SPACE]:
            self.drop_hard()
        # 暂存/切换（C）
        if keys[pygame.K_c] and not self._key_prev[pygame.K_c]:
            self.hold_piece()

        # ───── 保存本轮按键状态 ─────
        # 这一帧的状态保存为 _key_prev，供下一帧做"刚按下"判断
        self._key_prev = {k: keys[k] for k in self._track_keys}



    # 模拟落底 _ai_simulate_drop
    def _ai_simulate_drop(self, piece_name, rotation, px):
        """模拟落底：将方块以指定旋转 + x 坐标落底，返回落定后的棋盘副本和消行数"""
        # 深拷贝
        grid = [row[:] for row in self.grid]

        blocks = SHAPES[piece_name]['shape'][rotation]
        color = SHAPES[piece_name]['color']

        py = 0
        while True:
            collision = False
            for bx, by in blocks:
                gx, gy = px + bx, py + 1 + by
                if gx < 0 or gx >= COLS or gy >= ROWS:
                    collision = True
                    break
                if gy >= 0 and grid[gy][gx] != BLACK:
                    collision = True
                    break
            if collision:
                break
            py += 1

        for bx, by in blocks:
            gx, gy = px + bx, py + by
            if 0 <= gy < ROWS and 0 <= gx < COLS:
                grid[gy][gx] = color

        cleared = 0
        for r in range(ROWS - 1, -1, -1):
            if all(grid[r][c] != BLACK for c in range(COLS)):
                del grid[r]
                cleared += 1
        for _ in range(cleared):
            grid.insert(0, [BLACK for _ in range(COLS)])
        return grid, cleared

    # 评价函数_ai_evaluate
    def _ai_evaluate(self, grid, cleared):
        """评价函数：对落定后的棋盘打分（越高越好）"""

        # 列高
        heights = []
        for c in range(COLS):
            h = 0
            for r in range(ROWS):
                if grid[r][c] != BLACK:
                    h = ROWS - r
                    break
            heights.append(h)

        # 空洞
        holes = 0
        for c in range(COLS):
            above = False
            for r in range(ROWS):
                if grid[r][c] != BLACK:
                    above = True
                elif above:
                    holes += 1

        # 行内跳变
        row_trans = 0
        for r in range(ROWS):
            for c in range(COLS - 1):
                if (grid[r][c] != BLACK) != (grid[r][c + 1] != BLACK):
                    row_trans += 1

        # 列内跳变
        col_trans = 0
        for c in range(COLS):
            for r in range(ROWS - 1):
                if (grid[r][c] != BLACK) != (grid[r + 1][c] != BLACK):
                    col_trans += 1

        # 井深
        well = 0
        for c in range(COLS):
            left  = heights[c - 1] if c > 0 else ROWS
            right = heights[c + 1] if c < COLS - 1 else ROWS
            if heights[c] < left and heights[c] < right:
                well += min(left, right) - heights[c]

        # 聚合高度
        agg_height = sum(heights)

        # 加权求和
        score = 0
        score -= 45 * agg_height     # 聚合高度惩罚：越低越好
        if cleared == 1:
            score += 3400     # 消1行奖励
        elif cleared == 2:
            score += 12000    # 消2
        elif cleared == 3:
            score += 20000    # 消3
        elif cleared == 4:
            score += 34000    # 消4
        score -= 32 * row_trans      # 行跳变惩罚
        score -= 93 * col_trans      # 列跳变惩罚
        score -= 79 * holes          # 空洞惩罚
        score -= 34 * well           # 井深惩罚
        return score

    # 决策
    def _ai_find_best(self):
        """枚举所有旋转×水平位置，对每种可能落底后评分，返回(最佳rot, 最佳x, 最佳分)"""
        best_score = -float('inf')
        best_rot, best_x = 0, 0
        piece = self.current_name

        # 外层遍历旋转
        for rot in range(4):
            blocks = SHAPES[piece]['shape'][rot]

            min_x = min(bx for bx, by in blocks)    # 方块内最左边格子的 x
            max_x = max(bx for bx, by in blocks)    # 方块内最右边格子的 x

            # 内层遍历x
            for px in range(-min_x, COLS - max_x):
                overlap = False
                for bx, by in blocks:
                    gx, gy = px + bx, by
                    if 0 <= gy < ROWS and 0 <= gx < COLS:
                        if self.grid[gy][gx] != BLACK:
                            overlap = True
                            break
                if overlap:
                    continue

                sim_grid, cleared = self._ai_simulate_drop(piece, rot, px)
                score = self._ai_evaluate(sim_grid, cleared)

                if score > best_score:
                    best_score = score
                    best_rot = rot
                    best_x = px

        return best_rot, best_x, best_score

    # ── 更新 update ───────────────────────────────────────────────
    # 每帧调用一次，负责自动下落逻辑。
    # dt 是两帧之间的时间差（毫秒），由 clock.tick(60) 返回。

    def update(self, dt):
        """每帧更新 — 处理自动下落 / AI 决策"""
        # 游戏结束时不更新（AI 模式自动重开）
        if self.game_over:
            if self.ai_mode:
                self.fall_time += dt
                if self.fall_time >= 800:  # 0.8 秒后自动重开
                    self.fall_time = 0
                    self.reset()
            return

        # ───── AI 模式 ─────
        if self.ai_mode:
            # 每步操作之间加入 80ms 冷却，让 AI 动作肉眼可观察
            self._ai_step_delay += dt

            # 第一步：对当前方块做规划（只做一次）
            if not self._ai_planned:
                rot, tx, score = self._ai_find_best()
                self._ai_target_rotation = rot
                self._ai_target_x = tx
                self._ai_planned = True

            # 第二步：逐帧执行 — 先旋转到位，再移动到目标 x，最后硬降
            if self._ai_step_delay >= 80:
                self._ai_step_delay = 0
                if self.rotation != self._ai_target_rotation:
                    # 还没转到目标角度，逐帧旋转
                    self.rotate(1)
                elif self.x != self._ai_target_x:
                    # 旋转到位了，逐帧水平移动到目标列
                    dx = 1 if self._ai_target_x > self.x else -1
                    self.move(dx, 0)
                else:
                    # 一切都就位 → 硬降到底
                    self.drop_hard()
                    self._ai_planned = False
            return

        # ───── 玩家模式 — 正常自动下落 ─────
        # 累加下落计时器。当累计时间超过 fall_speed，方块自动下移一格。
        self.fall_time += dt
        if self.fall_time >= self.fall_speed:
            self.fall_time = 0   # 计时器归零，开始下一轮计时
            # 尝试下移一格，如果失败（撞到东西）→ 锁定方块
            if not self.move(0, 1):
                self.lock_piece()

    # ── 绘制单个格子 draw_cell ───────────────────────────────────
    # 在 pygame 窗口上画一个有立体感的方块格子。
    # 参数 offset_x/offset_y 允许在非棋盘位置绘制（如右侧面板的预览区）。
    #
    # 立体感怎么来的？
    #   → 用当前颜色填满矩形，然后在左/上边画一条稍亮的线（模拟光照），
    #     在右/下边画一条稍暗的线（模拟阴影）。这就是简单的"2.5D 效果"。

    def draw_cell(self, x, y, color, offset_x=0, offset_y=0):
        """在屏幕坐标 (x, y) 处画一个带立体感的格子"""

        # 计算格子在屏幕上的像素坐标（相对于棋盘或面板左上角）
        px = (x + offset_x) * CELL
        py = (y + offset_y) * CELL
        rect = pygame.Rect(px, py, CELL, CELL)   # pygame 的矩形对象

        # 填充方块底色
        pygame.draw.rect(self.screen, color, rect)

        # 计算高光色（比原色亮 60）和阴影色（比原色暗 60）
        # min(255, c+60) 保证不超出 RGB 上限 255
        # max(0, c-60)   保证不低于下限 0
        lighter = tuple(min(255, c + 60) for c in color)
        darker  = tuple(max(0, c - 60) for c in color)

        # 在格子上边和左边画亮线 → 模拟光源从左上角打下来
        pygame.draw.line(self.screen, lighter, rect.topleft, rect.topright, 2)
        pygame.draw.line(self.screen, lighter, rect.topleft, rect.bottomleft, 2)

        # 在格子下边和右边画暗线 → 模拟右下角的阴影
        pygame.draw.line(self.screen, darker, rect.bottomleft, rect.bottomright, 2)
        pygame.draw.line(self.screen, darker, rect.topright, rect.bottomright, 2)

    # ═══════════════════════════════════════════════════════════════
    #  ██  绘制整个画面  draw  ██
    # ═══════════════════════════════════════════════════════════════
    # 每一帧都会重新绘制整个画面。绘制顺序决定了"谁在上面"：
    #   1. 黑色背景
    #   2. 灰色网格线
    #   3. 已锁定的方块（棋盘内容）
    #   4. 虚影（半透明落底预览）
    #   5. 当前方块（实体，盖在虚影上面）
    #   6. 右侧信息面板（分数、等级、预览、操作提示）
    #   7. 游戏结束遮罩（半透明黑色 + 文字）
    #   8. flip() — 把画好的内容一次性显示到屏幕上

    def draw(self):
        """每一帧重绘整个画面"""

        # 用黑色填充整个窗口（相当于"擦黑板"）
        self.screen.fill(BLACK)

        # ───── 第 1 层：网格线 ─────
        # 在游戏区画出 10×20 的灰色格子框架
        for r in range(ROWS):
            for c in range(COLS):
                # 每个格子画一个空心矩形（线宽 1 像素）
                rect = pygame.Rect(c * CELL, r * CELL, CELL, CELL)
                pygame.draw.rect(self.screen, GRAY, rect, 1)

        # ───── 第 2 层：已锁定的方块 ─────
        # 遍历整个棋盘 grid，把不是黑色的格子画出来
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] != BLACK:
                    self.draw_cell(c, r, self.grid[r][c])

        # ───── 第 3 层：当前操作的方块（+ 虚影） ─────
        if not self.game_over:
            blocks = self.get_current_blocks()
            color = SHAPES[self.current_name]['color']

            # --- 3a：虚影（落底预览） ---
            # 虚影显示在当前方块的正下方落点位置
            ghost_y = self.get_ghost_y()
            if ghost_y != self.y:   # 只有还能下落时才画虚影（等于 self.y 说明已经在底部）
                for bx, by in blocks:
                    gx = self.x + bx
                    gy = ghost_y + by
                    if gy >= 0:   # 只画棋盘内的格子
                        px = gx * CELL
                        py = gy * CELL
                        rect = pygame.Rect(px, py, CELL, CELL)

                        # 虚影效果：半透明暗色填充 + 原色边框
                        # 创建一个带 alpha 通道的 Surface（可以半透明）
                        ghost_fill = tuple(max(0, c - 100) for c in color)
                        ghost_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                        # 填充颜色，alpha=80 表示约 31% 不透明度（很透）
                        ghost_surf.fill((*ghost_fill, 80))
                        self.screen.blit(ghost_surf, (px, py))
                        # 画 2px 粗的原色边框，让虚影即使很透也能被看见
                        pygame.draw.rect(self.screen, color, rect, 2)

            # --- 3b：实体方块（画在虚影上面） ---
            for bx, by in blocks:
                gx = self.x + bx
                gy = self.y + by
                if gy >= 0:   # 屏幕上方还没进入棋盘的格子不画
                    self.draw_cell(gx, gy, color)

        # ───── 第 4 层：右侧信息面板 ─────
        # 面板在游戏区右边，从 column 10 再往右 15 像素开始
        panel_x = COLS * CELL + 15

        # 分数显示
        t1 = self.font_small.render("分数", True, WHITE)
        self.screen.blit(t1, (panel_x, 15))
        t2 = self.font.render(str(self.score), True, WHITE)
        self.screen.blit(t2, (panel_x, 36))

        # 等级显示
        t3 = self.font_small.render("等级", True, WHITE)
        self.screen.blit(t3, (panel_x, 70))
        t4 = self.font.render(str(self.level), True, WHITE)
        self.screen.blit(t4, (panel_x, 91))

        # 消除行数显示
        t5 = self.font_small.render("行数", True, WHITE)
        self.screen.blit(t5, (panel_x, 125))
        t6 = self.font.render(str(self.lines_cleared), True, WHITE)
        self.screen.blit(t6, (panel_x, 146))

        # "下一个"方块预览
        t7 = self.font_small.render("下一个", True, WHITE)
        self.screen.blit(t7, (panel_x, 180))
        preview_blocks = SHAPES[self.next_name]['shape'][0]
        preview_color  = SHAPES[self.next_name]['color']
        for bx, by in preview_blocks:
            px = panel_x + bx * CELL
            py = 205 + by * CELL
            rect = pygame.Rect(px, py, CELL, CELL)
            pygame.draw.rect(self.screen, preview_color, rect)
            lighter = tuple(min(255, c + 60) for c in preview_color)
            darker  = tuple(max(0, c - 60) for c in preview_color)
            pygame.draw.line(self.screen, lighter, rect.topleft, rect.topright, 2)
            pygame.draw.line(self.screen, lighter, rect.topleft, rect.bottomleft, 2)
            pygame.draw.line(self.screen, darker,  rect.bottomleft, rect.bottomright, 2)
            pygame.draw.line(self.screen, darker,  rect.topright, rect.bottomright, 2)

        # "储存"方块预览（Hold 区）
        t8 = self.font_small.render("储存", True, WHITE)
        self.screen.blit(t8, (panel_x, 290))
        if self.hold_name is not None:
            hold_blocks = SHAPES[self.hold_name]['shape'][0]
            hold_color  = SHAPES[self.hold_name]['color']
            for bx, by in hold_blocks:
                px = panel_x + bx * CELL
                py = 315 + by * CELL
                rect = pygame.Rect(px, py, CELL, CELL)
                pygame.draw.rect(self.screen, hold_color, rect)
                lighter = tuple(min(255, c + 60) for c in hold_color)
                darker  = tuple(max(0, c - 60) for c in hold_color)
                pygame.draw.line(self.screen, lighter, rect.topleft, rect.topright, 2)
                pygame.draw.line(self.screen, lighter, rect.topleft, rect.bottomleft, 2)
                pygame.draw.line(self.screen, darker,  rect.bottomleft, rect.bottomright, 2)
                pygame.draw.line(self.screen, darker,  rect.topright, rect.bottomright, 2)

        # AI 模式指示器
        if self.ai_mode:
            ai_text = self.font_small.render("AI 自动", True, (255, 200, 50))
            self.screen.blit(ai_text, (panel_x, 395))
        else:
            ai_hint = self.font_small.render("按 A = AI 代打", True, (120, 120, 120))
            self.screen.blit(ai_hint, (panel_x, 395))

        # 操作提示文字
        tips = [
            "← → 移动",
            "↑ / X 顺转",
            "Z     逆转",
            "↓     加速",
            "空格   硬降",
            "C     暂存",
            "A     AI",
            "ESC    退出",
        ]
        ty = 425
        for tip in tips:
            t = self.font_small.render(tip, True, WHITE)
            self.screen.blit(t, (panel_x, ty))
            ty += 20

        # ───── 第 5 层：游戏结束遮罩 + 文字 ─────
        if self.game_over:
            # 创建和窗口一样大的半透明黑色遮罩
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)   # alpha 决定透明度（0=完全透明，255=完全不透明）
            overlay.fill(BLACK)      # 纯黑色
            self.screen.blit(overlay, (0, 0))   # 贴到整个窗口上

            # 显示"游戏结束"（红色大字）
            go_text = self.font.render("游戏结束", True, RED)
            # get_rect(center=...) 让文字在指定中心点居中
            go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
            self.screen.blit(go_text, go_rect)

            # 显示"按 R 重新开始"（白色小字）
            restart_text = self.font_small.render("按 R 重新开始", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 25))
            self.screen.blit(restart_text, restart_rect)

        # ───── 显示到屏幕 ─────
        # flip() 把这一帧画的所有内容一次性呈现到显示器上。
        # 如果不调 flip，画的内容不会出现在屏幕上。
        pygame.display.flip()

    # ═══════════════════════════════════════════════════════════════
    #  ██  主循环  run  ██
    # ═══════════════════════════════════════════════════════════════
    # 这是游戏的"心跳"——一个无限循环，直到玩家关闭窗口或按 ESC。
    # 每一轮循环（即每一帧）按顺序做四件事：
    #   1. 控制帧率（clock.tick）
    #   2. 处理系统事件（目前只关心"关闭窗口"）
    #   3. 处理玩家输入（handle_input）
    #   4. 更新游戏状态（update）
    #   5. 渲染画面（draw）
    #
    # 这个循环结构是几乎所有游戏的基础，称为 Game Loop（游戏循环）。

    def run(self):
        """启动游戏主循环"""

        # running 是循环条件，设为 False 就能退出循环
        running = True

        while running and not self._quit:   # 每一轮 = 1 帧 ≈ 16.67ms（60 FPS）
            # clock.tick(60) 做了两件事：
            #   ① 等待，确保自上次调用以来刚好过了 1/60 秒
            #   ② 返回实际经过的毫秒数 dt，用于速度计算
            # 60 表示目标帧率 = 60 帧/秒
            dt = self.clock.tick(60)

            # ── 处理事件（只关心关闭窗口） ──
            # 其他所有输入都由 handle_input 的轮询方式处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:   # 用户点了窗口右上角的 ×
                    running = False             # 退出循环

            # ── 处理输入 ──
            # 通过 key.get_pressed() 轮询键盘状态，
            # 不依赖 pygame 的 KEYDOWN 事件，避免 IME 拦截
            self.handle_input()

            # ── 更新游戏逻辑 ──
            # 自动下落、碰撞检测、消行判定等
            self.update(dt)

            # ── 绘制画面 ──
            # 把所有变化反映到屏幕上
            self.draw()

        # 退出循环后，关闭 pygame 窗口并释放资源
        pygame.quit()

if __name__ == "__main__":
    # 创建一个 Tetris 对象并立即调用 run() 启动游戏循环
    Tetris().run()
