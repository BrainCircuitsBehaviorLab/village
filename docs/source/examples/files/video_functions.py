# Visual stimulus generators for this project.
#
# Each draw_X_generator(...) is a factory: it takes the stimulus parameters
# and returns a draw() closure, meant to be passed to
# screen.load_draw_function(draw_fn=...). Qt then calls that draw() on every
# frame while screen.start_drawing() is active (see direct_functions.py,
# function8-15). draw() itself is responsible for checking
# screen.elapsed_time < duration and deciding whether to paint anything --
# nothing clears or disables it automatically once the duration is over, it
# just stops drawing the stimulus (leaving the background color) until a new
# draw function is loaded.
#
# Every draw() also fills the whole viewport with screen.background_color
# first, since Qt does not clear the widget between paints on its own -- skip
# that and the previous frame's stimulus would stay on screen underneath.

import math

from PyQt5.QtCore import QPointF, QRect, Qt
from PyQt5.QtGui import QColor, QPainter, QPolygonF

from village.devices.screen import screen
from village.devices.sound_device import sound_device


def draw_circle_generator(duration, x_pos, y_pos, diameter, color):

    def draw():
        with QPainter(screen) as painter:
            # no transparency and no antialiasing (drawing is faster)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.setRenderHint(QPainter.Antialiasing, False)

            # clean the screen with background color
            painter.fillRect(painter.viewport(), screen.background_color)

            # use the parameters to draw the circle for the specified duration
            if screen.elapsed_time < duration:
                painter.setPen(Qt.NoPen)
                painter.setBrush(color)
                painter.drawEllipse(QRect(x_pos, y_pos, diameter, diameter))

    return draw


def draw_rectangle_generator(duration, x_pos, y_pos, width, height, color):

    def draw():
        with QPainter(screen) as painter:
            # no transparency and no antialiasing (drawing is faster)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.setRenderHint(QPainter.Antialiasing, False)

            # clean the screen with background color
            painter.fillRect(painter.viewport(), screen.background_color)

            # use the parameters to draw the rectangle for the specified duration
            if screen.elapsed_time < duration:
                painter.setPen(Qt.NoPen)
                painter.setBrush(color)
                painter.drawRect(x_pos, y_pos, width, height)

    return draw


def draw_rectangles_generator(rects, colors, durations):
    """Draws several independent rectangles at once, e.g. a touchscreen menu.

    rects, colors and durations are same-length lists (one entry per
    rectangle): rects[i] is (x_pos, y_pos, width, height), colors[i] its
    QColor, durations[i] how many seconds it stays visible (independently
    of the others -- one can disappear before another does).
    """

    def draw():
        with QPainter(screen) as painter:
            # no transparency and no antialiasing (drawing is faster)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.setRenderHint(QPainter.Antialiasing, False)

            # clean the screen with background color
            painter.fillRect(painter.viewport(), screen.background_color)

            painter.setPen(Qt.NoPen)
            for (x_pos, y_pos, width, height), color, duration in zip(
                rects, colors, durations, strict=True
            ):
                if screen.elapsed_time < duration:
                    painter.setBrush(color)
                    painter.drawRect(x_pos, y_pos, width, height)

    return draw


def draw_moving_circle_generator(duration, diameter, color):

    def draw():
        with QPainter(screen) as painter:
            # no transparency and no antialiasing (drawing is faster)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.setRenderHint(QPainter.Antialiasing, False)

            # clean the screen with background color
            painter.fillRect(painter.viewport(), screen.background_color)

            # use the parameters to draw the circle for the specified duration
            if screen.elapsed_time < duration:
                # oscillates left-right around x=0 with a 1-second period and
                # a 100px amplitude; y is fixed at 0 (top of the screen)
                x_pos = int(100 * math.sin(screen.elapsed_time * 2 * math.pi))
                painter.setPen(QColor("red"))
                painter.setBrush(color)
                painter.drawEllipse(QRect(x_pos, 0, diameter, diameter))

    return draw


def draw_triangle_generator(duration, color):
    def draw():
        with QPainter(screen) as painter:
            # no transparency and no antialiasing (drawing is faster)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.setRenderHint(QPainter.Antialiasing, False)

            # clean the screen with background color
            painter.fillRect(painter.viewport(), screen.background_color)

            # use the parameters to draw the triangle for the specified duration
            if screen.elapsed_time < duration:
                # get screen size
                width = painter.viewport().width()
                height = painter.viewport().height()

                # border and fill
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(color))

                # draw the triangle
                points = QPolygonF(
                    [
                        QPointF(width / 2, height / 2 - 100),
                        QPointF(width / 2 - 100, height / 2 + 100),
                        QPointF(width / 2 + 100, height / 2 + 100),
                    ]
                )
                painter.drawPolygon(points)

    return draw


def draw_image_generator(duration, x_pos, y_pos):
    # draws whatever is currently loaded in screen.image -- call
    # screen.load_image(file=...) with the desired file before this stimulus
    # is actually drawn (screen.image stays None, and nothing is painted,
    # until load_image has been called at least once)
    def draw():
        with QPainter(screen) as painter:
            # no transparency and no antialiasing (drawing is faster)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.setRenderHint(QPainter.Antialiasing, False)

            # clean the screen with the background color
            painter.fillRect(painter.viewport(), screen.background_color)

            # use the parameters to draw the image for the specified duration
            if screen.elapsed_time < duration:
                painter.drawPixmap(x_pos, y_pos, screen.image)

    return draw


def draw_image_with_alpha_generator(duration, x_pos, y_pos):
    def draw():
        with QPainter(screen) as painter:
            # in this case we use transparency as the image is a png with alpha channel
            # CompositionMode_SourceOver instead of CompositionMode_Source
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setRenderHint(QPainter.Antialiasing, False)

            # clean the screen with the background color
            painter.fillRect(painter.viewport(), screen.background_color)

            # use the parameters to draw the image for the specified duration
            if screen.elapsed_time < duration:
                painter.drawPixmap(x_pos, y_pos, screen.image)

    return draw


def draw_video_generator(duration):
    # draws whatever video is currently playing via screen.load_video(...),
    # frame by frame. Once elapsed_time passes duration it stops any audio
    # that came with the video (loaded by load_video's own audio extraction),
    # so the video's sound ends together with its picture.
    def draw():
        with QPainter(screen) as painter:
            # no transparency and no antialiasing (drawing is faster)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.setRenderHint(QPainter.Antialiasing, False)

            # clean the screen with the background color
            painter.fillRect(painter.viewport(), screen.background_color)

            # draw the video for the specified duration
            if screen.elapsed_time < duration:
                # get the last frame from the video source
                frame = screen.get_video_frame()
                # draw the last frame from the video source
                if frame is not None:
                    painter.drawImage(0, 0, frame)
            else:
                sound_device.stop()

    return draw
