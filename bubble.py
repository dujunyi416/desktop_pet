from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont


class BubbleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        font = QFont("Microsoft YaHei", 10)
        self.label.setFont(font)
        self.label.setStyleSheet("color: #333333; background: transparent;")

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    PADDING = 14
    TAIL_H = 12
    RADIUS = 10

    def show_message(self, text: str, pet_top_center: QPoint):
        self.label.setText(text)
        self.label.adjustSize()

        p = self.PADDING
        w = max(self.label.width() + p * 2, 80)
        bubble_h = self.label.height() + p * 2
        total_h = bubble_h + self.TAIL_H

        self.setFixedSize(w, total_h)
        self.label.move(p, p)

        x = pet_top_center.x() - w // 2
        y = pet_top_center.y() - total_h - 4

        screen = self.screen()
        if screen:
            sg = screen.geometry()
            x = max(sg.left(), min(x, sg.right() - w))
            y = max(sg.top(), y)

        self.move(x, y)
        self.show()
        self.raise_()
        self._timer.start(3000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        bubble_h = self.height() - self.TAIL_H

        path = QPainterPath()
        path.addRoundedRect(0, 0, w, bubble_h, self.RADIUS, self.RADIUS)

        mid = w // 2
        path.moveTo(mid - 8, bubble_h)
        path.lineTo(mid, self.height())
        path.lineTo(mid + 8, bubble_h)
        path.closeSubpath()

        painter.fillPath(path, QColor(255, 255, 255, 230))
        painter.setPen(QColor(180, 180, 180, 200))
        painter.drawPath(path)
