from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt5.QtWidgets import QWidget


class StudyChart(QWidget):
    def __init__(self, *, heatmap=False):
        super().__init__()
        self.heatmap = heatmap
        self.values = []
        self.days_in_month = 31
        self.first_weekday = 0
        self.setMinimumHeight(225)

    def set_data(self, values, days_in_month, first_weekday=0):
        self.values = values
        self.days_in_month = days_in_month
        self.first_weekday = first_weekday
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#ffffff"))
        painter.drawRoundedRect(QRectF(self.rect()), 12, 12)

        if self.heatmap:
            self.draw_heatmap(painter)
            return

        left, top = 38, 13
        bottom = self.height() - 32
        width = self.width() - left - 16
        day_width = width / self.days_in_month
        step = max(1, (max(self.values, default=0) + 3) // 4)
        scale = (bottom - top) / (step * 4)

        for tick in range(5):
            value = tick * step
            y = bottom - value * scale
            painter.setPen(QColor("#e0e5f0"))
            painter.drawLine(QPointF(left, y), QPointF(left + width, y))
            painter.setPen(QColor("#475569"))
            painter.drawText(QRectF(0, y - 8, left - 6, 16), Qt.AlignRight | Qt.AlignVCenter, str(value))

        for day in (1, 5, 10, 15, 20, 25, self.days_in_month):
            x = left + (day - 0.5) * day_width
            painter.drawText(QRectF(x - 12, bottom + 5, 24, 18), Qt.AlignCenter, str(day))

        points = [
            QPointF(left + (index + 0.5) * day_width, bottom - value * scale)
            for index, value in enumerate(self.values)
        ]
        color = QColor("#087e85")
        painter.setBrush(color)
        if points:
            painter.setPen(QPen(color, 2))
            painter.drawPolyline(QPolygonF(points))
            painter.setPen(Qt.NoPen)
            for point in points:
                painter.drawEllipse(point, 2.5, 2.5)

    def draw_heatmap(self, painter):
        weekdays = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
        colors = ("#eef0f6", "#e0dcff", "#bbb1fa", "#7867df", "#4836a9")
        cell_width = (self.width() - 24) / len(weekdays)
        cell_height = (self.height() - 54) / 6
        for column, weekday in enumerate(weekdays):
            painter.setPen(QColor("#475569"))
            painter.drawText(QRectF(12 + column * cell_width, 5, cell_width, 20),
                             Qt.AlignCenter, weekday)

        for day in range(1, self.days_in_month + 1):
            row, column = divmod(self.first_weekday + day - 1, len(weekdays))
            cell = QRectF(14 + column * cell_width, 27 + row * cell_height,
                          cell_width - 4, cell_height - 3)
            streak = self.values[day - 1] if day <= len(self.values) else None
            if streak is None:
                painter.setBrush(QColor("#ffffff"))
                painter.setPen(QColor("#e0e5f0"))
            else:
                level = min(streak, 4)
                painter.setBrush(QColor(colors[level]))
                painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(cell, 4, 4)
            text_color = "#ffffff" if streak is not None and streak >= 3 else "#475569"
            painter.setPen(QColor(text_color))
            painter.drawText(cell, Qt.AlignCenter, str(day))

        legend_y = self.height() - 24
        painter.setPen(QColor("#475569"))
        painter.drawText(QRectF(12, legend_y, 112, 18), Qt.AlignVCenter, "Streak length (days)")
        for index, color in enumerate(colors):
            cell = QRectF(128 + index * 31, legend_y, 28, 18)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(cell, 3, 3)
            painter.setPen(QColor("#ffffff" if index >= 3 else "#475569"))
            painter.drawText(cell, Qt.AlignCenter, "4+" if index == 4 else str(index))
