import sys
import random
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QPixmap, QMovie


class NikoWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Настройки окна: без рамки, поверх всех окон, прозрачный фон
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool  # Скрыть из панели задач
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Размер окна под размер спрайта (задаётся позже по первому кадру)
        self.resize(100, 100)

        # Метка для отображения спрайта
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)

        # Загрузка кадров для разных состояний
        self.frames = {
            'idle': self.load_frames('idle', 4),      # Кадры покачивания
            'walk': self.load_frames('walk', 1),      # Кадры ходьбы
            'drag': self.load_frames('drag', 1)       # Кадры перетаскивания
        }
        self.current_state = 'idle'
        self.current_frame_index = 0

        # Таймер анимации
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.next_frame)
        self.anim_timer.start(80)  # 80 мс между кадрами

        # Таймер для автоматической ходьбы (если не перетаскивают)
        self.walk_timer = QTimer(self)
        self.walk_timer.timeout.connect(self.update_walking)
        self.walk_timer.start(50)  # частота обновления позиции

        # Параметры движения
        self.target_pos = None          # целевая точка на экране
        self.speed = 3                   # скорость перемещения
        self.screen_rect = QApplication.primaryScreen().availableGeometry()

        # Перетаскивание
        self.dragging = False
        self.drag_offset = QPoint()

        # Показываем первый кадр
        self.update_image()

        # Начать движение (идти случайно)
        self.pick_new_target()

    def load_frames(self, state_name, count):
        """Загружает кадры из файлов state_name_1.png, state_name_2.png и т.д."""
        frames = []
        for i in range(1, count + 1):
            path = f"images/{state_name}/{state_name}_{i}.png"
            pix = QPixmap(path)
            if pix.isNull():
                print(f"Предупреждение: не удалось загрузить {path}")
                # Создаём заглушку
                pix = QPixmap(100, 100)
                pix.fill(Qt.transparent)
            frames.append(pix)
        return frames

    def update_image(self):
        """Обновляет картинку в label на основе текущего кадра."""
        pix = self.frames[self.current_state][self.current_frame_index]
        self.label.setPixmap(pix)
        # Подгоняем размер окна под размер картинки (только если не перетаскиваем)
        if not self.dragging:
            self.resize(pix.size())
            self.label.resize(pix.size())

    def next_frame(self):
        """Переключает на следующий кадр в текущем состоянии."""
        frames = self.frames[self.current_state]
        self.current_frame_index = (self.current_frame_index + 1) % len(frames)
        self.update_image()

    def set_state(self, state):
        """Меняет состояние (idle/walk/drag) и сбрасывает индекс кадра."""
        if state != self.current_state:
            self.current_state = state
            self.current_frame_index = 0
            self.update_image()

    # --- Логика самостоятельной ходьбы ---
    def pick_new_target(self):
        """Выбирает новую случайную цель на экране."""
        margin = 50  # отступ от краёв
        x = random.randint(margin, self.screen_rect.width() - margin)
        y = random.randint(margin, self.screen_rect.height() - margin)
        self.target_pos = QPoint(x, y)

    def update_walking(self):
        """Обновление позиции при автоматической ходьбе (вызывается по таймеру)."""
        if self.dragging or self.current_state == 'drag':
            return  # не двигаем, если перетаскиваем

        if not self.target_pos:
            return

        current = self.pos()
        delta_x = self.target_pos.x() - current.x()
        delta_y = self.target_pos.y() - current.y()
        distance = (delta_x ** 2 + delta_y ** 2) ** 0.5

        if distance < self.speed:
            # Достигли цели
            self.move(self.target_pos)
            self.pick_new_target()
            self.set_state('idle')  # на месте покачивается
        else:
            # Двигаемся к цели
            step_x = self.speed * delta_x / distance
            step_y = self.speed * delta_y / distance
            new_x = current.x() + step_x
            new_y = current.y() + step_y
            self.move(int(new_x), int(new_y))
            self.set_state('walk')

    # --- Обработка перетаскивания мышкой ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_offset = event.pos()  # позиция клика внутри окна
            self.set_state('drag')
            # Останавливаем автоматическую ходьбу во время перетаскивания
            self.target_pos = None

    def mouseMoveEvent(self, event):
        if self.dragging:
            # Перемещаем окно
            self.move(event.globalPos() - self.drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            self.set_state('idle')
            # Возобновляем ходьбу
            self.pick_new_target()

    # Для возможности выхода по ESC (опционально)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Создаём и показываем окно
    niko = NikoWindow()
    niko.show()

    sys.exit(app.exec_())