import glob
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import time

from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QLabel, QApplication, QMenu, QFileDialog, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPixmap, QTransform

from bubble import BubbleWidget
from phrases import (
    get_phrases, get_time_phrase, get_interaction_phrase,
    detect_type, current_time_state, HOME_LINES, SLEEP_ZZZ
)

SIZE_PRESETS = {"小": 60, "中": 100, "大": 150}
POS_DIR      = os.path.join(tempfile.gettempdir(), "desktop_pet_pos")


class PetWidget(QWidget):
    IDLE      = "idle"
    WALKING   = "walking"
    DRAGGING  = "dragging"
    RETURNING = "returning"
    SLEEPING  = "sleeping"
    GREETING  = "greeting"

    def __init__(self, image_file="pet.png", screen_index=0,
                 pet_type=None, pet_size=100, pet_name="", spawn_x=-1):
        super().__init__()
        self._image_file    = image_file
        self._screen_index  = screen_index
        self._pet_type      = pet_type or detect_type(image_file)
        self._pet_size      = pet_size
        self._pet_name      = pet_name or os.path.splitext(os.path.basename(image_file))[0]
        self._spawn_x       = spawn_x
        self._phrases       = get_phrases(self._pet_type)

        self.state          = self.IDLE
        self.direction      = 1
        self._drag_offset   = QPoint()
        self._drag_moved    = False
        self._vy            = 0.0
        self._falling       = False
        self._bob_phase     = 0.0
        self._walk_phase    = 0.0
        self._base_pixmap   = None

        # 时间感知
        self._time_state        = current_time_state()
        self._last_time_check   = datetime.now()
        self._greeted_today     = False

        # 宠物互动
        self._last_interaction  = 0.0   # timestamp
        self._interaction_cd    = 30.0  # 30 秒冷却

        self._setup_window()
        self._setup_image()
        self._setup_bubble()
        self._setup_timers()
        self._setup_pos_file()
        self._apply_time_state(startup=True)

    # ── screen helpers ────────────────────────────────────────────────────────

    def _get_screen(self):
        screens = QApplication.screens()
        return screens[min(self._screen_index, len(screens) - 1)]

    def _screen_geo(self):
        return self._get_screen().availableGeometry()

    def _ground_y(self):
        return self._screen_geo().bottom() - self._pet_size

    def _current_screen(self):
        center = self.pos() + QPoint(self._pet_size // 2, self._pet_size // 2)
        return QApplication.screenAt(center) or self._get_screen()

    def _current_ground(self):
        return self._current_screen().availableGeometry().bottom() - self._pet_size

    def _is_on_assigned_screen(self):
        return self._screen_geo().contains(
            self.pos() + QPoint(self._pet_size // 2, self._pet_size // 2)
        )

    # ── setup ─────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self._pet_size, self._pet_size)
        geo = self._screen_geo()
        start_x = self._spawn_x if self._spawn_x >= 0 else geo.center().x() - self._pet_size // 2
        start_x = max(geo.left(), min(start_x, geo.right() - self._pet_size))
        self.move(start_x, geo.bottom() - self._pet_size)

    def _setup_image(self):
        self._label = QLabel(self)
        self._label.setFixedSize(self._pet_size, self._pet_size)
        self._label.setAlignment(Qt.AlignCenter)
        self._load_base_pixmap()
        self._label.setPixmap(self._base_pixmap)

    def _load_base_pixmap(self):
        self._base_pixmap = QPixmap(self._image_file).scaled(
            self._pet_size, self._pet_size,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

    def _setup_bubble(self):
        self._bubble = BubbleWidget()

    def _setup_timers(self):
        # 主循环 60fps
        self._tick = QTimer(self)
        self._tick.timeout.connect(self._update)
        self._tick.start(16)

        # 随机行为
        self._behavior = QTimer(self)
        self._behavior.timeout.connect(self._random_behavior)
        self._behavior.start(random.randint(2000, 5000))

        # 时间检测（每分钟）
        self._time_timer = QTimer(self)
        self._time_timer.timeout.connect(self._check_time)
        self._time_timer.start(60_000)

        # 写自己位置（每 500ms）
        self._pos_write_timer = QTimer(self)
        self._pos_write_timer.timeout.connect(self._write_pos)
        self._pos_write_timer.start(500)

        # 扫描其他宠物（每 2s）
        self._scan_timer = QTimer(self)
        self._scan_timer.timeout.connect(self._check_nearby_pets)
        self._scan_timer.start(2000)

    def _setup_pos_file(self):
        os.makedirs(POS_DIR, exist_ok=True)
        self._pos_file = os.path.join(POS_DIR, f"pet_{os.getpid()}.json")

    # ── 时间感知 ──────────────────────────────────────────────────────────────

    def _apply_time_state(self, startup=False):
        new_state = current_time_state()
        old_state = self._time_state
        self._time_state = new_state

        if new_state == "sleeping":
            self.state = self.SLEEPING
            self._behavior.stop()
        else:
            if old_state == "sleeping" and not startup:
                # 刚睡醒
                self.state = self.IDLE
                self._behavior.start(random.randint(2000, 5000))
                phrase = get_time_phrase(self._pet_type, "wakeup")
                if phrase:
                    self._bubble.show_message(
                        phrase, self.mapToGlobal(QPoint(self._pet_size // 2, 0))
                    )
            elif new_state == "morning" and not self._greeted_today:
                self._greeted_today = True
                phrase = get_time_phrase(self._pet_type, "morning")
                if phrase:
                    QTimer.singleShot(2000, lambda: self._bubble.show_message(
                        phrase, self.mapToGlobal(QPoint(self._pet_size // 2, 0))
                    ))
            elif new_state == "evening" and startup is False:
                phrase = get_time_phrase(self._pet_type, "evening")
                if phrase:
                    self._bubble.show_message(
                        phrase, self.mapToGlobal(QPoint(self._pet_size // 2, 0))
                    )

            if self.state == self.SLEEPING:
                self.state = self.IDLE
            if not self._behavior.isActive():
                self._behavior.start(random.randint(2000, 5000))

        # 凌晨过后重置早晨问候标志
        if datetime.now().hour == 0:
            self._greeted_today = False

    def _check_time(self):
        self._apply_time_state(startup=False)

    # ── 宠物互动 ──────────────────────────────────────────────────────────────

    def _write_pos(self):
        try:
            data = {
                "pid":    os.getpid(),
                "x":      self.x(),
                "y":      self.y(),
                "screen": self._screen_index,
                "type":   self._pet_type,
                "size":   self._pet_size,
                "ts":     time.time(),
            }
            with open(self._pos_file, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _check_nearby_pets(self):
        if self.state in (self.DRAGGING, self.RETURNING, self.SLEEPING):
            return
        if time.time() - self._last_interaction < self._interaction_cd:
            return

        try:
            for path in glob.glob(os.path.join(POS_DIR, "pet_*.json")):
                if f"pet_{os.getpid()}.json" in path:
                    continue
                with open(path) as f:
                    other = json.load(f)

                # 跳过失活进程（超过 2 秒没更新）
                if time.time() - other.get("ts", 0) > 2.0:
                    continue
                # 必须同一屏幕
                if other.get("screen") != self._screen_index:
                    continue
                # 距离判断
                dx = abs(other["x"] - self.x())
                if dx < 160:
                    self._do_greet(other)
                    break
        except Exception:
            pass

    def _do_greet(self, other: dict):
        self._last_interaction = time.time()

        # 面向对方
        self.direction = 1 if other["x"] > self.x() else -1
        self.state     = self.GREETING

        phrase = get_interaction_phrase(self._pet_type, other.get("type", "generic"))
        self._bubble.show_message(
            phrase, self.mapToGlobal(QPoint(self._pet_size // 2, 0))
        )

        # 3 秒后恢复 IDLE
        QTimer.singleShot(3000, self._end_greeting)

    def _end_greeting(self):
        if self.state == self.GREETING:
            self.state      = self.IDLE
            self._bob_phase = 0.0

    # ── per-frame update ──────────────────────────────────────────────────────

    def _update(self):
        if self._falling:
            self._do_gravity()
        elif self.state == self.SLEEPING:
            self._do_sleep()
        elif self.state == self.RETURNING:
            self._do_return()
        elif self.state == self.GREETING:
            self._do_greeting_idle()
        elif self.state == self.IDLE:
            self._do_idle_bob()
        elif self.state == self.WALKING:
            self._do_walk()
        self._sync_bubble()

    # ── movement / animation states ───────────────────────────────────────────

    def _do_idle_bob(self):
        self._bob_phase += 0.06
        self.move(self.x(), self._ground_y() + int(math.sin(self._bob_phase) * 3))
        scale = 1.0 + 0.012 * math.sin(self._bob_phase * 0.7)
        sz    = int(self._pet_size * scale)
        self._label.setPixmap(
            self._base_pixmap.scaled(sz, sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def _do_walk(self):
        self._walk_phase += 0.18
        geo = self._screen_geo()
        x   = self.x() + 2 * self.direction
        hit = False
        if x <= geo.left():
            x = geo.left(); self.direction = 1; hit = True
        elif x >= geo.right() - self._pet_size:
            x = geo.right() - self._pet_size; self.direction = -1; hit = True
        self.move(x, self._ground_y())
        self._walk_sprite(1.0)
        if hit:
            self._walk_phase = 0.0

    def _do_return(self):
        self._walk_phase += 0.28
        geo      = self._screen_geo()
        target_x = geo.center().x() - self._pet_size // 2
        dx       = target_x - self.x()
        speed    = 5
        if abs(dx) <= speed:
            self.move(target_x, self._current_ground())
            self.state      = self.IDLE
            self._bob_phase = 0.0
            self._bubble.show_message(
                random.choice(HOME_LINES),
                self.mapToGlobal(QPoint(self._pet_size // 2, 0))
            )
            return
        self.direction = 1 if dx > 0 else -1
        self.move(self.x() + speed * self.direction, self._current_ground())
        self._walk_sprite(1.4)

    def _do_sleep(self):
        """侧躺睡觉动画"""
        self._bob_phase += 0.02   # 非常慢的呼吸
        self.move(self.x(), self._ground_y() + int(math.sin(self._bob_phase) * 1))

        # 图片旋转 90° 模拟侧躺
        t = QTransform().rotate(90)
        pix = self._base_pixmap.transformed(t, Qt.SmoothTransformation).scaled(
            self._pet_size, self._pet_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self._label.setPixmap(pix)

        # 偶尔显示 Zzz
        if random.random() < 0.003:
            self._bubble.show_message(
                random.choice(SLEEP_ZZZ),
                self.mapToGlobal(QPoint(self._pet_size // 2, 0))
            )

    def _do_greeting_idle(self):
        """打招呼时静止面向对方"""
        self.move(self.x(), self._ground_y())
        pix = self._base_pixmap
        if self.direction == -1:
            pix = pix.transformed(QTransform().scale(-1, 1))
        self._label.setPixmap(pix)

    def _do_gravity(self):
        ground   = self._current_ground()
        self._vy = min(self._vy + 1.5, 30)
        new_y    = int(self.y() + self._vy)
        if new_y >= ground:
            new_y         = ground
            self._vy      = 0.0
            self._falling = False
            if not self._is_on_assigned_screen():
                self.state = self.RETURNING
            else:
                self.state      = self.IDLE
                self._bob_phase = 0.0
        self.move(self.x(), new_y)

    def _walk_sprite(self, speed_factor=1.0):
        pix = self._base_pixmap
        if self.direction == -1:
            pix = pix.transformed(QTransform().scale(-1, 1))
        t = QTransform()
        t.shear(0.09 * speed_factor * math.sin(self._walk_phase) * self.direction, 0)
        self._label.setPixmap(pix.transformed(t, Qt.SmoothTransformation))

    # ── behavior ──────────────────────────────────────────────────────────────

    def _random_behavior(self):
        if self.state in (self.DRAGGING, self.RETURNING,
                          self.SLEEPING, self.GREETING) or self._falling:
            return
        if random.random() < 0.55:
            self.state       = self.WALKING
            self.direction   = random.choice([-1, 1])
            self._walk_phase = 0.0
        else:
            self.state      = self.IDLE
            self._bob_phase = 0.0
        self._behavior.setInterval(random.randint(2000, 6000))

    # ── mouse ─────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 点击唤醒睡觉中的宠物
            if self.state == self.SLEEPING:
                self.state      = self.IDLE
                self._bob_phase = 0.0
                phrase = get_time_phrase(self._pet_type, "wakeup")
                if phrase:
                    self._bubble.show_message(
                        phrase, self.mapToGlobal(QPoint(self._pet_size // 2, 0))
                    )
                if not self._behavior.isActive():
                    self._behavior.start(random.randint(2000, 5000))
                return
            self._drag_offset = event.pos()
            self._drag_moved  = False
            self._falling     = False
            self._vy          = 0.0
            self.state        = self.IDLE

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._drag_moved = True
            self.state       = self.DRAGGING
            self.move(self.mapToGlobal(event.pos()) - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.state == self.DRAGGING:
                self.state    = self.IDLE
                self._falling = True
            elif not self._drag_moved and self.state != self.SLEEPING:
                self._show_bubble()

    # ── bubble ────────────────────────────────────────────────────────────────

    def _sync_bubble(self):
        if not self._bubble.isVisible():
            return
        ct = self.mapToGlobal(QPoint(self._pet_size // 2, 0))
        bw, bh = self._bubble.width(), self._bubble.height()
        sg = self._get_screen().geometry()
        x  = max(sg.left(), min(ct.x() - bw // 2, sg.right() - bw))
        y  = max(sg.top(), ct.y() - bh - 4)
        self._bubble.move(x, y)

    def _show_bubble(self):
        self._bubble.show_message(
            random.choice(self._phrases),
            self.mapToGlobal(QPoint(self._pet_size // 2, 0))
        )

    # ── right-click menu ──────────────────────────────────────────────────────

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #2C2C2E; color: #F2F2F7;
                border: 1px solid #3A3A3C; border-radius: 10px;
                padding: 4px; font-family: "Microsoft YaHei"; font-size: 13px;
            }
            QMenu::item { padding: 7px 20px; border-radius: 6px; }
            QMenu::item:selected { background: #0A84FF; color: white; }
            QMenu::item:disabled { color: #636366; }
            QMenu::separator { height: 1px; background: #3A3A3C; margin: 4px 10px; }
        """)

        # 宠物名字标题
        title = menu.addAction(f"🐾  {self._pet_name}")
        title.setEnabled(False)
        title_font = title.font(); title_font.setBold(True); title.setFont(title_font)
        menu.addSeparator()

        screen_menu = menu.addMenu("切换屏幕")
        for i, scr in enumerate(QApplication.screens()):
            g = scr.geometry()
            a = screen_menu.addAction(f"屏幕 {i+1}  ({g.width()}×{g.height()})")
            a.setCheckable(True)
            a.setChecked(i == self._screen_index)
            a.triggered.connect(lambda _, idx=i: self._switch_screen(idx))

        size_menu = menu.addMenu("调整大小")
        for label, px in SIZE_PRESETS.items():
            a = size_menu.addAction(f"{label}  ({px}px)")
            a.setCheckable(True)
            a.setChecked(self._pet_size == px)
            a.triggered.connect(lambda _, p=px: self._resize_pet(p))

        menu.addSeparator()
        menu.addAction("添加新宠物…").triggered.connect(self._add_pet)
        menu.addSeparator()
        menu.addAction("退出此宠物").triggered.connect(self._quit_self)

        menu.exec_(event.globalPos())

    def _switch_screen(self, idx):
        self._screen_index = idx
        geo = self._screen_geo()
        self.move(geo.center().x() - self._pet_size // 2,
                  geo.bottom() - self._pet_size)
        self.state      = self.IDLE
        self._bob_phase = 0.0

    def _resize_pet(self, new_size):
        old            = self._pet_size
        self._pet_size = new_size
        self.setFixedSize(new_size, new_size)
        self._label.setFixedSize(new_size, new_size)
        self._label.move(0, 0)
        self._load_base_pixmap()
        self._label.setPixmap(self._base_pixmap)
        geo   = self._screen_geo()
        new_x = self.x() + (old - new_size) // 2
        self.move(max(geo.left(), min(new_x, geo.right() - new_size)),
                  geo.bottom() - new_size)
        self.state      = self.IDLE
        self._bob_phase = 0.0

    def _add_pet(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择宠物图片", "", "图片 (*.png *.jpg *.jpeg *.bmp)"
        )
        if not path:
            return
        screens    = QApplication.screens()
        screen_idx = 0
        if len(screens) > 1:
            names = [f"屏幕 {i+1}  ({s.geometry().width()}×{s.geometry().height()})"
                     for i, s in enumerate(screens)]
            choice, ok = QInputDialog.getItem(
                self, "选择屏幕", "把新宠物放在哪个屏幕？", names, 0, False
            )
            if not ok:
                return
            screen_idx = names.index(choice)

        type_names = ["自动识别", "猫咪 🐱", "狗狗 🐶", "其他"]
        type_map   = {"自动识别": "", "猫咪 🐱": "cat", "狗狗 🐶": "dog", "其他": "generic"}
        t_choice, ok = QInputDialog.getItem(
            self, "动物类型", "这是什么宠物？", type_names, 0, False
        )
        if not ok:
            return
        pet_type = type_map[t_choice] or detect_type(path)

        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        subprocess.Popen([sys.executable, script, path, str(screen_idx), pet_type])

    def _quit_self(self):
        try:
            os.remove(self._pos_file)
        except Exception:
            pass
        self._bubble.close()
        self.close()
        QApplication.quit()
