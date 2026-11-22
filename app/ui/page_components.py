"""Shared card, tab, and completion widgets for the desktop pages."""
from PyQt5.QtCore import QEasingCurve, QRectF, QSize, Qt, QVariantAnimation
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QPen
from PyQt5.QtWidgets import QFrame, QLabel, QTabBar, QVBoxLayout, QWidget


def page_layout(page):
    layout = QVBoxLayout(page)
    layout.setContentsMargins(20, 16, 20, 16)
    layout.setSpacing(14)
    return layout


def section_card(title=None):
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(8)
    if title:
        label = QLabel(title)
        label.setObjectName("card_title")
        layout.addWidget(label)
    return frame, layout


class SectionTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setExpanding(False)
        self.setElideMode(Qt.ElideNone)
        self.setUsesScrollButtons(True)
        self.setAttribute(Qt.WA_Hover)

    def label(self, index):
        return self.tabText(index).replace("&&", "&")

    def tabSizeHint(self, index):
        metrics = self.fontMetrics()
        return QSize(metrics.horizontalAdvance(self.label(index)) + 28, metrics.height() + 16)

    def minimumTabSizeHint(self, index):
        return self.tabSizeHint(index)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        hovered = self.tabAt(self.mapFromGlobal(self.cursor().pos())) if self.underMouse() else -1
        for index in range(self.count()):
            rect = self.tabRect(index).adjusted(1, 0, -3, -1)
            selected = index == self.currentIndex()
            if selected or index == hovered:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor("#5546D7" if selected else "#EAE8FF"))
                painter.drawRoundedRect(QRectF(rect), 9, 9)
            color = "#FFFFFF" if selected else "#445271"
            if not self.isTabEnabled(index):
                color = "#8790A3"
            painter.setPen(QColor(color))
            painter.drawText(rect, Qt.AlignCenter | Qt.TextSingleLine, self.label(index))
            if selected and self.hasFocus():
                painter.setPen(QPen(QColor("#D8D2FF"), 1, Qt.DotLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(QRectF(rect.adjusted(3, 3, -3, -3)), 7, 7)


def configure_tabs(tabs):
    tabs.setObjectName("section_tabs")
    tabs.setTabBar(SectionTabBar(tabs))
    tabs.setDocumentMode(True)


class CompletionRing(QWidget):
    def __init__(self, size=96, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAccessibleName("Topic completion")
        self._value = 0.0
        self._target = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(450)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.valueChanged.connect(self._show_value)

    def set_value(self, percent):
        percent = max(0, min(100, percent))
        if percent == self._target:
            return
        self._target = percent
        self.setAccessibleDescription(f"{percent:g}% complete")
        self._animation.stop()
        self._animation.setStartValue(self._value)
        self._animation.setEndValue(float(percent))
        self._animation.start()

    def _show_value(self, value):
        self._value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        arc = QRectF(self.rect()).adjusted(7, 7, -7, -7)
        painter.setPen(QPen(QColor("#EEF0FA"), 10))
        painter.drawEllipse(arc)
        if self._value > 0:
            gradient = QLinearGradient(arc.topLeft(), arc.bottomRight())
            gradient.setColorAt(0, QColor("#5546D7"))
            gradient.setColorAt(1, QColor("#25B9D4"))
            pen = QPen()
            pen.setBrush(gradient)
            pen.setWidth(10)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawArc(arc, 90 * 16, -round(self._value * 360 * 16 / 100))
        painter.setPen(QColor("#101A35"))
        font = painter.font()
        font.setPointSize(17)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self._value:.0f}%")
