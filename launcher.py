import json, os, random, subprocess, sys

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QScrollArea, QFrame, QFileDialog, QInputDialog
)
from PyQt5.QtCore  import Qt, pyqtSignal, QPoint, QRectF
from PyQt5.QtGui   import (
    QPixmap, QFont, QColor, QPainter, QPainterPath, QPen
)

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "pets.json")
PYTHON      = sys.executable

TYPE_LIST = ["🐶  狗狗", "🐱  猫咪", "❓  其他"]
TYPE_KEYS = ["dog", "cat", "generic"]
SIZE_LIST = ["小  60", "中  100", "大  150", "✏  自定义"]
SIZE_VALS = [60, 100, 150, -1]

BG   = "#1C1C1E"
CARD = "#2C2C2E"
SEP  = "#3A3A3C"
TEXT = "#F2F2F7"
SUB  = "#8E8E93"
BLUE = "#0A84FF"
RED  = "#FF453A"

COMBO_S = f"""
QComboBox {{
    background:{SEP}; color:{TEXT}; border:none;
    border-radius:6px; padding:3px 8px; font-size:11px; min-width:75px;
}}
QComboBox::drop-down {{ border:none; width:14px; }}
QComboBox QAbstractItemView {{
    background:{CARD}; color:{TEXT}; border:1px solid {SEP};
    selection-background-color:{BLUE}; selection-color:white; outline:none;
}}
"""

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"pets": []}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ── 照片开关（点击切换启用） ───────────────────────────────────────────────────

class PhotoToggle(QLabel):
    toggled = pyqtSignal(bool)

    def __init__(self, path: str, size=56):
        super().__init__()
        self._on   = True
        self._sz   = size
        self._r    = size // 5
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("点击启用 / 禁用")
        if os.path.exists(path):
            self._pix = QPixmap(path).scaled(
                size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
        else:
            self._pix = QPixmap(size, size); self._pix.fill(QColor(SEP))

    def set_state(self, v: bool):
        self._on = v; self.update()

    def mousePressEvent(self, _):
        self._on = not self._on
        self.update(); self.toggled.emit(self._on)

    def paintEvent(self, _):
        sz, r = self._sz, self._r
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 圆角裁剪区域
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, sz, sz), r, r)
        p.setClipPath(clip)

        # 绘制图片（灰暗表示禁用）
        p.setOpacity(1.0 if self._on else 0.25)
        p.drawPixmap(0, 0, self._pix)

        p.setOpacity(1.0)
        p.setClipping(False)

        # 启用时绘制蓝色边框
        if self._on:
            p.setPen(QPen(QColor(BLUE), 2.5))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(1.25, 1.25, sz - 2.5, sz - 2.5), r, r)

        # 右下角勾选圆
        if self._on:
            cx, cy, cr = sz - 11, sz - 11, 9
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(BLUE))
            p.drawEllipse(QRectF(cx - cr, cy - cr, cr * 2, cr * 2))
            p.setPen(QPen(QColor("white"), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawLine(cx - 4, cy, cx - 1, cy + 3)
            p.drawLine(cx - 1, cy + 3, cx + 4, cy - 3)

        p.end()


# ── 数量步进器 ────────────────────────────────────────────────────────────────

class CountStepper(QWidget):
    def __init__(self, value=1):
        super().__init__()
        self._v = max(1, value)
        h = QHBoxLayout(self); h.setContentsMargins(0,0,0,0); h.setSpacing(0)
        s = f"""QPushButton{{background:{SEP};color:{TEXT};border:none;
                font-size:14px;font-weight:bold;min-width:26px;min-height:26px;}}
               QPushButton:hover{{background:{BLUE};color:white;}}"""
        self._m = QPushButton("−"); self._m.setStyleSheet(s+"QPushButton{border-radius:6px 0 0 6px;}")
        self._l = QLabel(str(self._v))
        self._l.setFixedWidth(30); self._l.setAlignment(Qt.AlignCenter)
        self._l.setStyleSheet(f"background:{CARD};color:{TEXT};font-weight:bold;font-size:12px;"
                               f"border-top:1px solid {SEP};border-bottom:1px solid {SEP};")
        self._p = QPushButton("＋"); self._p.setStyleSheet(s+"QPushButton{border-radius:0 6px 6px 0;}")
        self._m.clicked.connect(self._dec); self._p.clicked.connect(self._inc)
        h.addWidget(self._m); h.addWidget(self._l); h.addWidget(self._p)

    def _dec(self):
        if self._v > 1: self._v -= 1; self._l.setText(str(self._v))
    def _inc(self):
        if self._v < 9: self._v += 1; self._l.setText(str(self._v))

    @property
    def value(self): return self._v


# ── 宠物卡片 ──────────────────────────────────────────────────────────────────

class PetCard(QFrame):
    sig_delete  = pyqtSignal(object)
    sig_changed = pyqtSignal()

    def __init__(self, data: dict):
        super().__init__()
        self._data = data
        self._custom_size = None
        self._build()

    def _build(self):
        self.setFixedHeight(88)
        self.setStyleSheet(f"""
            PetCard {{
                background:{CARD}; border-radius:12px; border:1px solid {SEP};
            }}
        """)
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 0, 14, 0); row.setSpacing(12)

        img = self._data.get("image", "")
        if not os.path.isabs(img): img = os.path.join(BASE_DIR, img)
        self.photo = PhotoToggle(img, 58)
        self.photo.set_state(self._data.get("enabled", True))
        self.photo.toggled.connect(self._on_toggle)
        row.addWidget(self.photo)

        col = QVBoxLayout(); col.setSpacing(6); col.setContentsMargins(0, 12, 0, 12)

        self.name_edit = QLineEdit(self._data.get("name", "未命名"))
        self.name_edit.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.name_edit.setStyleSheet(f"""
            QLineEdit{{border:none;border-bottom:1px solid {SEP};
                background:transparent;color:{TEXT};padding-bottom:2px;}}
            QLineEdit:focus{{border-bottom:1.5px solid {BLUE};}}
        """)
        col.addWidget(self.name_edit)

        sub = QHBoxLayout(); sub.setSpacing(6)
        self.type_cb = QComboBox(); self.type_cb.addItems(TYPE_LIST)
        self.type_cb.setStyleSheet(COMBO_S)
        t = self._data.get("type","generic")
        self.type_cb.setCurrentIndex(TYPE_KEYS.index(t) if t in TYPE_KEYS else 2)
        sub.addWidget(self.type_cb)

        screens = QApplication.screens()
        self.screen_cb = QComboBox(); self.screen_cb.setStyleSheet(COMBO_S)
        for i,s in enumerate(screens):
            g = s.geometry(); self.screen_cb.addItem(f"屏幕{i+1}  {g.width()}×{g.height()}")
        self.screen_cb.setCurrentIndex(min(self._data.get("screen",0), len(screens)-1))
        sub.addWidget(self.screen_cb)

        self.size_cb = QComboBox(); self.size_cb.addItems(SIZE_LIST)
        self.size_cb.setStyleSheet(COMBO_S)
        sz = self._data.get("size", 100)
        if sz in [60,100,150]: self.size_cb.setCurrentIndex([60,100,150].index(sz))
        else: self.size_cb.setCurrentIndex(3); self._custom_size = sz
        self.size_cb.currentIndexChanged.connect(self._on_size)
        sub.addWidget(self.size_cb)
        sub.addStretch()
        col.addLayout(sub)
        row.addLayout(col, 1)

        right = QVBoxLayout(); right.setContentsMargins(0,16,0,16); right.setSpacing(4)
        self.stepper = CountStepper(self._data.get("count", 1))
        right.addWidget(self.stepper)
        lbl = QLabel("数量"); lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color:{SUB};font-size:10px;")
        right.addWidget(lbl)
        row.addLayout(right)

        d = QPushButton("✕"); d.setFixedSize(26,26); d.setCursor(Qt.PointingHandCursor)
        d.setStyleSheet(f"""QPushButton{{color:{SUB};border:none;font-size:12px;
            border-radius:13px;background:transparent;}}
            QPushButton:hover{{background:#3D1A1A;color:{RED};}}""")
        d.clicked.connect(lambda: self.sig_delete.emit(self))
        row.addWidget(d, 0, Qt.AlignTop)
        self._update_dim()

    def _on_toggle(self, v):
        self._update_dim(); self.sig_changed.emit()

    def _update_dim(self):
        on = self.photo._on
        for w in (self.name_edit, self.type_cb, self.screen_cb, self.size_cb, self.stepper):
            w.setEnabled(on)

    def _on_size(self, idx):
        if idx == 3:
            val, ok = QInputDialog.getInt(self,"自定义大小","像素大小(40-300)：",
                                          self._custom_size or 100, 40, 300, 10)
            if ok: self._custom_size = val
            else:
                sz = self._data.get("size",100)
                self.size_cb.blockSignals(True)
                self.size_cb.setCurrentIndex([60,100,150].index(sz) if sz in [60,100,150] else 1)
                self.size_cb.blockSignals(False)

    def collect(self):
        idx  = self.size_cb.currentIndex()
        size = SIZE_VALS[idx] if idx < 3 else (self._custom_size or 100)
        return {
            "name":    self.name_edit.text().strip() or "未命名",
            "image":   self._data.get("image",""),
            "screen":  self.screen_cb.currentIndex(),
            "type":    TYPE_KEYS[self.type_cb.currentIndex()],
            "size":    size, "count": self.stepper.value,
            "enabled": self.photo._on,
        }


# ── 主窗口（圆角无边框） ──────────────────────────────────────────────────────

class LauncherWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._cards: list[PetCard] = []
        self._cfg = load_config()
        self._drag_pos = None
        self._build()
        self._load_pets()

    def _build(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setFixedWidth(520)
        self.setStyleSheet(f"""
            LauncherWindow {{
                background:{BG}; border-radius:14px; border:1px solid {SEP};
            }}
            QWidget   {{ background:{BG}; color:{TEXT}; font-family:"Microsoft YaHei"; }}
            QScrollBar:vertical{{width:4px;background:transparent;}}
            QScrollBar::handle:vertical{{background:{SUB};border-radius:2px;min-height:24px;}}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 20)
        root.setSpacing(0)

        # 标题栏（可拖拽）
        tb = QWidget(); tb.setFixedHeight(50)
        tb.setStyleSheet(f"background:{CARD};border-radius:16px 16px 0 0;border-bottom:1px solid {SEP};")
        tbr = QHBoxLayout(tb); tbr.setContentsMargins(18, 0, 14, 0); tbr.setSpacing(10)

        ic = QLabel("🐾"); ic.setFont(QFont("Segoe UI Emoji", 17)); ic.setFixedWidth(32)
        tbr.addWidget(ic)
        tl = QLabel("桌面宠物管理器")
        tl.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        tl.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        tbr.addWidget(tl, 1)

        for color, action in [(RED, self.close), ("#FF9F0A", self.showMinimized), ("#30D158", None)]:
            btn = QPushButton(); btn.setFixedSize(13, 13)
            btn.setStyleSheet(f"QPushButton{{background:{color};border:none;border-radius:6px;}}"
                              f"QPushButton:hover{{opacity:0.8;}}")
            btn.setCursor(Qt.PointingHandCursor)
            if action: btn.clicked.connect(action)
            tbr.addWidget(btn)

        tb.mousePressEvent   = self._tb_press
        tb.mouseMoveEvent    = self._tb_move
        tb.mouseReleaseEvent = self._tb_release
        root.addWidget(tb)

        inner = QVBoxLayout()
        inner.setContentsMargins(20, 14, 20, 0); inner.setSpacing(0)

        self._stat = QLabel()
        self._stat.setStyleSheet(f"color:{SUB};font-size:12px;")
        inner.addWidget(self._stat)
        inner.addSpacing(12)

        self._list_w = QWidget(); self._list_w.setStyleSheet("background:transparent;")
        self._list_l = QVBoxLayout(self._list_w)
        self._list_l.setSpacing(8); self._list_l.setContentsMargins(0,0,2,0)
        self._list_l.addStretch()

        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setWidget(self._list_w)
        sc.setFrameShape(QFrame.NoFrame); sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sc.setStyleSheet("background:transparent;border:none;")
        inner.addWidget(sc, 1)
        inner.addSpacing(16)

        br = QHBoxLayout(); br.setSpacing(10)
        add = QPushButton("＋  添加宠物"); add.setFixedHeight(38); add.setCursor(Qt.PointingHandCursor)
        add.setStyleSheet(f"""QPushButton{{background:transparent;color:{BLUE};
            border:1.5px solid {BLUE};border-radius:10px;font-size:13px;padding:0 16px;}}
            QPushButton:hover{{background:rgba(10,132,255,0.12);}}""")
        add.clicked.connect(self._add_pet); br.addWidget(add); br.addStretch()

        self._go = QPushButton("启动选中宠物  →"); self._go.setFixedHeight(42)
        self._go.setCursor(Qt.PointingHandCursor)
        self._go.setStyleSheet(f"""QPushButton{{background:{BLUE};color:white;border:none;
            border-radius:12px;font-size:14px;font-weight:bold;padding:0 24px;}}
            QPushButton:hover{{background:#3A9EFF;}}
            QPushButton:pressed{{background:#006EDB;}}""")
        self._go.clicked.connect(self._launch); br.addWidget(self._go)
        inner.addLayout(br)
        root.addLayout(inner)
        self._refresh_height()

    # ── 拖拽 ─────────────────────────────────────────────────────────────────

    def _tb_press(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()
    def _tb_move(self, e):
        if e.buttons() & Qt.LeftButton and self._drag_pos:
            self.move(e.globalPos() - self._drag_pos)
    def _tb_release(self, _): self._drag_pos = None

    # ── 卡片管理 ──────────────────────────────────────────────────────────────

    def _load_pets(self):
        for p in self._cfg.get("pets", []): self._insert(p)

    def _insert(self, data):
        c = PetCard(data)
        c.sig_delete.connect(self._del); c.sig_changed.connect(self._refresh_stat)
        self._list_l.insertWidget(self._list_l.count()-1, c)
        self._cards.append(c); self._refresh_height(); self._refresh_stat()

    def _del(self, c):
        self._list_l.removeWidget(c); c.deleteLater()
        self._cards.remove(c); self._refresh_height(); self._refresh_stat()

    def _refresh_height(self):
        h = 200 + min(max(len(self._cards),1), 5) * 98
        self.setFixedHeight(h)

    def _refresh_stat(self):
        total = len(self._cards)
        sel   = sum(1 for c in self._cards if c.photo._on)
        cnt   = sum(c.stepper.value for c in self._cards if c.photo._on)
        self._stat.setText(f"共 {total} 只  ·  已选 {sel} 只  ·  将启动 {cnt} 个")
        # 有宠物被选中时恢复启动按钮文字
        if cnt > 0:
            self._go.setText("启动选中宠物  →")

    # ── 动作 ─────────────────────────────────────────────────────────────────

    def _add_pet(self):
        path, _ = QFileDialog.getOpenFileName(
            self,"选择宠物图片",BASE_DIR,"图片 (*.png *.jpg *.jpeg *.bmp)")
        if not path: return
        try:    rel = os.path.relpath(path, BASE_DIR)
        except: rel = path
        from phrases import detect_type
        self._insert({"name": os.path.splitext(os.path.basename(path))[0],
                      "image": rel, "screen": 0, "type": detect_type(path),
                      "size": 100, "count": 1, "enabled": True})

    def _launch(self):
        self._cfg["pets"] = [c.collect() for c in self._cards]
        save_config(self._cfg)
        launched = 0
        screens = QApplication.screens()
        for pet in self._cfg["pets"]:
            if not pet.get("enabled"): continue
            img = pet["image"]
            if not os.path.isabs(img): img = os.path.join(BASE_DIR, img)
            if not os.path.exists(img): continue

            scr_idx = pet.get("screen", 0)
            scr     = screens[min(scr_idx, len(screens)-1)]
            geo     = scr.availableGeometry()
            size    = pet.get("size", 100)
            count   = pet.get("count", 1)

            # 随机分布出生点，均匀分散在屏幕底部
            margin  = size
            usable  = max(geo.width() - margin * 2, 1)
            step    = usable // max(count, 1)

            for i in range(count):
                # 在各自区间内随机偏移，避免堆叠
                base_x = geo.left() + margin + i * step
                rand_x = base_x + random.randint(0, max(step - size, 0))
                rand_x = max(geo.left(), min(rand_x, geo.right() - size))
                subprocess.Popen([
                    PYTHON, os.path.join(BASE_DIR, "main.py"),
                    img, str(scr_idx),
                    pet.get("type","generic"),
                    str(size),
                    pet.get("name",""),
                    str(rand_x),      # spawn_x
                ])
                launched += 1

        if launched: self.hide()
        else: self._go.setText("⚠  没有可启动的宠物")

    def closeEvent(self, event):
        self._cfg["pets"] = [c.collect() for c in self._cards]
        save_config(self._cfg); event.accept()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    win = LauncherWindow()
    # 居中显示在主屏幕
    screen = app.primaryScreen().availableGeometry()
    win.move(
        screen.center().x() - win.width() // 2,
        screen.center().y() - win.height() // 2,
    )
    win.show()
    win.raise_()
    win.activateWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
