from __future__ import annotations

import time
from typing import TYPE_CHECKING

from PyQt5.QtCore import QRect, QTimer
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QWidget

if TYPE_CHECKING:
    from village.gui.gui import Gui


class BehaviorWindow(QWidget):
    def __init__(self, gui: Gui) -> None:
        super().__init__()
        self.gui = gui
        self.x_displacement: int = gui.primary_width
        self.window_width: int = gui.secondary_width
        self.window_height: int = gui.secondary_height
        rect = QRect(self.x_displacement, 0, self.window_width, self.window_height)
        self.setGeometry(rect)
        self.setFixedSize(self.window_width, self.window_height)
        self.setWindowTitle("Village2")
        self.setStyleSheet("background-color: black")

        # Animación
        self.stimulus_visible = True
        self.animation_running = False
        self.circle_diameter = 50  # Diámetro inicial del círculo
        self.diameter_increment = 2  # Incremento por cuadro

        # Configurar el QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.animate
        )  # Llama a la animación cada vez que expira
        self.timer.start(16)  # 16 ms para aproximadamente 60 FPS (1000 ms / 60)

        self.timings: list[float] = []
        self.deltas: list[int] = []
        self.counter = 0

        self.show()

    def closeEvent(self, event) -> None:
        event.ignore()

    def toggle_animation(self) -> None:
        self.animation_running = not self.animation_running

    def animate(self) -> None:
        """Actualiza el estado de la animación y repinta."""
        if self.animation_running and self.stimulus_visible:
            # Modificar el diámetro del círculo
            self.circle_diameter += self.diameter_increment

            # Rebotar entre 50 y 200 píxeles de diámetro
            if self.circle_diameter >= 200 or self.circle_diameter <= 50:
                self.diameter_increment *= -1  # Cambia la dirección del crecimiento

            # Actualiza la ventana para repintar
            self.update()

    def paintEvent(self, event) -> None:
        self.counter += 1
        if self.counter > 3:
            current_time = time.time()
            if self.timings:
                delta = int((current_time - self.timings[-1]) * 1000)
                self.deltas.append(delta)
                # print(str(delta) + " ms")
                # print(sum(self.deltas) / len(self.deltas))
            self.timings.append(current_time)
        painter = QPainter(self)
        if self.stimulus_visible:
            # Determinar el centro del círculo
            center_x = (self.window_width - self.circle_diameter) // 2
            center_y = (self.window_height - self.circle_diameter) // 2
            rect = QRect(center_x, center_y, self.circle_diameter, self.circle_diameter)

            # Dibujar el círculo
            painter.setBrush(QColor("white"))
            painter.setPen(QColor("white"))
            painter.drawEllipse(rect)


# class BehaviorWindow(QOpenGLWidget):
#     def __init__(self, gui: Gui) -> None:
#         super().__init__()
#         self.gui = gui
#         self.x_displacement: int = gui.primary_width
#         self.window_width: int = gui.secondary_width
#         self.window_height: int = gui.secondary_height

#         self.setGeometry(
#             self.x_displacement, 0, self.window_width, self.window_height
#             )
#         self.setFixedSize(self.window_width, self.window_height)
#         self.setWindowTitle("Village2")

#         # self.context().setShareContext(shared_context)

#         self.animation_running = False
#         self.circle_diameter = 50.0
#         self.diameter_increment = 2.0

#         self.frameSwapped.connect(self.on_frame_swapped)

#         self.show()

#     def closeEvent(self, event) -> None:
#         event.ignore()

#     def toggle_animation(self) -> None:
#         self.animation_running = not self.animation_running

#     @pyqtSlot()
#     def on_frame_swapped(self) -> None:
#         if self.animation_running:
#             self.circle_diameter += self.diameter_increment

#             if self.circle_diameter >= 200 or self.circle_diameter <= 50:
#                 self.diameter_increment *= -1

#             self.update()

#     def initializeGL(self) -> None:
#         glClearColor(0.0, 0.0, 0.0, 1.0)

#     def paintGL(self) -> None:
#         glClear(GL_COLOR_BUFFER_BIT)

#         center_x = (self.window_width - self.circle_diameter) / 2.0
#         center_y = (self.window_height - self.circle_diameter) / 2.0

#         glColor3f(1.0, 1.0, 1.0)
#         glBegin(GL_QUADS)
#         glVertex2f(center_x, center_y)
#         glVertex2f(center_x + self.circle_diameter, center_y)
#         glVertex2f(center_x + self.circle_diameter, center_y + self.circle_diameter)
#         glVertex2f(center_x, center_y + self.circle_diameter)
#         glEnd()

#     def resizeGL(self, width, height) -> None:
#         self.window_width = width
#         self.window_height = height

#         glMatrixMode(GL_PROJECTION)
#         glLoadIdentity()
#         glOrtho(0, self.window_width, self.window_height, 0, -1, 1)
#         glMatrixMode(GL_MODELVIEW)
#         glLoadIdentity()
