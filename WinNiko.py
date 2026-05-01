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
        self.resize(100, 100)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)

        self.frames = {
            'idle': self._load_png_frames('idle', 4),
            'walk': self._load_png_frames('walk', 1),
        }

        self.drag_movie = self._try_load_gif('drag')
        if self.drag_movie is None:
            self.frames['drag'] = self._load_png_frames('drag', 1)

        self.current_state = 'idle'
        self.current_frame_index = 0

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.next_frame)
        self.anim_timer.start(80)

        self.walk_timer = QTimer(self)
        self.walk_timer.timeout.connect(self.update_walking)
        self.walk_timer.start(50)

        self.target_pos = None
        self.speed = 3
        self.screen_rect = QApplication.primaryScreen().availableGeometry()

        self.dragging = False
        self.drag_offset = QPoint()

        self.update_image()
        self.pick_new_target()

    def _load_png_frames(self, state_name, count):
        frames = []
        for i in range(1, count + 1):
            path = f"images/{state_name}/{state_name}_{i}.png"
            pix = QPixmap(path)
            if pix.isNull():
                print(f"Warning: failed to load {path}")
                pix = QPixmap(100, 100)
                pix.fill(Qt.transparent)
            frames.append(pix)
        return frames

    def _try_load_gif(self, state_name):
        path = f"images/{state_name}/{state_name}.gif"
        if not os.path.exists(path):
            return None
        movie = QMovie(path)
        if not movie.isValid():
            print(f"Warning: invalid GIF: {path}")
            return None
        movie.frameChanged.connect(self._on_gif_frame_changed)
        return movie

    def _on_gif_frame_changed(self, _frame_number):
        if self.current_state == 'drag' and self.drag_movie:
            pix = self.drag_movie.currentPixmap()
            self.label.setPixmap(pix)
            self.label.resize(pix.size())
            self.resize(pix.size())

    def update_image(self):
        if self.current_state == 'drag' and self.drag_movie:
            return
        pix = self.frames[self.current_state][self.current_frame_index]
        self.label.setPixmap(pix)
        self.resize(pix.size())
        self.label.resize(pix.size())

    def next_frame(self):
        if self.current_state == 'drag' and self.drag_movie:
            return
        frames = self.frames[self.current_state]
        self.current_frame_index = (self.current_frame_index + 1) % len(frames)
        self.update_image()

    def set_state(self, state):
        if state == self.current_state:
            return

        if self.current_state == 'drag' and self.drag_movie:
            self.drag_movie.stop()

        self.current_state = state
        self.current_frame_index = 0

        if state == 'drag' and self.drag_movie:
            self.drag_movie.start()
            pix = self.drag_movie.currentPixmap()
            self.label.setPixmap(pix)
            self.label.resize(pix.size())
            self.resize(pix.size())
        else:
            self.update_image()

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
            self.pick_new_target()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    niko = NikoWindow()
    niko.show()
    sys.exit(app.exec_())
