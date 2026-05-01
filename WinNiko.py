import sys
import os
import random
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPixmap, QMovie


class NikoWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.fixed_size = 100
        self.setFixedSize(self.fixed_size, self.fixed_size)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(self.fixed_size, self.fixed_size)

        # Загружаем медиа для каждого состояния
        self.media = {
            'idle': self._load_media('idle'),
            'walk': self._load_media('walk'),
            'drag': self._load_media('drag'),
        }

        self.current_state = 'idle'
        self.current_frame_index = 0

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_display)
        self.anim_timer.start(80)

        self.walk_timer = QTimer(self)
        self.walk_timer.timeout.connect(self.update_walking)
        self.walk_timer.start(50)

        self.idle_wait_timer = QTimer(self)
        self.idle_wait_timer.timeout.connect(self.finish_idle_wait)
        self.idle_wait_timer.setSingleShot(True)

        self.target_pos = None
        self.speed = 3
        self.screen_rect = QApplication.primaryScreen().availableGeometry()

        self.dragging = False
        self.drag_offset = QPoint()

        self.update_display()
        self.pick_new_target()

    def _load_media(self, state_name):
        """Загружает медиа для состояния. GIF в приоритете."""
        gif_path = f"{state_name}.gif"
        static_path = f"{state_name}.png"
        
        if os.path.exists(gif_path):
            movie = QMovie(gif_path)
            if movie.isValid():
                movie.frameChanged.connect(self._on_media_changed)
                return {'type': 'gif', 'data': movie}
            else:
                print(f"Warning: invalid GIF: {gif_path}")
        
        if os.path.exists(static_path):
            pix = QPixmap(static_path)
            if not pix.isNull():
                return {'type': 'pixmap', 'data': pix}
            else:
                print(f"Warning: failed to load {static_path}")
        
        pix = QPixmap(self.fixed_size, self.fixed_size)
        pix.fill(Qt.transparent)
        return {'type': 'pixmap', 'data': pix}

    def _on_media_changed(self, _frame_number):
        """Callback для обновления GIF кадров"""
        self.update_display()

    def update_display(self):
        """Отображает текущее медиа"""
        media = self.media[self.current_state]
        
        if media['type'] == 'gif':
            pix = media['data'].currentPixmap()
        else:
            pix = media['data']
        
        # Масштабируем чтобы полностью заполнить 100x100
        scaled_pix = pix.scaled(self.fixed_size, self.fixed_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled_pix)

    def set_state(self, state):
        if state == self.current_state:
            return

        # Останавливаем старый GIF если был
        if self.media[self.current_state]['type'] == 'gif':
            self.media[self.current_state]['data'].stop()

        self.current_state = state

        # Запускаем новый GIF если нужен
        if self.media[state]['type'] == 'gif':
            self.media[state]['data'].start()
        
        self.update_display()

    def pick_new_target(self):
        margin = 50
        x = random.randint(margin, self.screen_rect.width() - margin)
        y = random.randint(margin, self.screen_rect.height() - margin)
        self.target_pos = QPoint(x, y)

    def update_walking(self):
        if self.dragging or self.current_state == 'drag':
            return
        if not self.target_pos:
            return

        current = self.pos()
        delta_x = self.target_pos.x() - current.x()
        delta_y = self.target_pos.y() - current.y()
        distance = (delta_x ** 2 + delta_y ** 2) ** 0.5

        if distance < self.speed:
            self.move(self.target_pos)
            self.pick_new_target()
            self.set_state('idle')
        else:
            step_x = self.speed * delta_x / distance
            step_y = self.speed * delta_y / distance
            self.move(int(current.x() + step_x), int(current.y() + step_y))
            self.set_state('walk')

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_offset = event.pos()
            self.target_pos = None
            self.set_state('drag')

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            self.set_state('idle')
            self.idle_wait_timer.start(2000)  # Ждем 2 секунды перед тем как продолжить

    def finish_idle_wait(self):
        """Вызывается после ожидания 2 секунды"""
        self.pick_new_target()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    niko = NikoWindow()
    niko.show()
    sys.exit(app.exec_())
