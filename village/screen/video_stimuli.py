# import time

# import cv2
# from PyQt5.QtGui import QImage, QPixmap


# class VideoPlayer:
#     def __init__(self) -> None:
#         self.cap = None
#         self.path = None
#         self.fps = 30
#         self.frame_interval = 1 / 30
#         self.last_frame_time = None
#         self.frame_index = 0
#         self.frame_count = 0
#         self.playing = False
#         self.current_pixmap = None

#     def load_video(self, path: str) -> bool:
#         self.release()
#         self.cap = cv2.VideoCapture(path)
#         try:
#             if not self.cap.isOpened():
#                 print(f"Failed to open video: {path}")
#                 return False

#             self.path = path
#             self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
#             self.frame_interval = 1 / self.fps
#             self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
#             self.frame_index = 0
#             self.last_frame_time = None
#             self.current_pixmap = None
#             return True
#         except Exception:
#             return False

#     def play_video(self):
#         self.playing = True
#         self.last_frame_time = time.time()

#     def pause_resume_video(self):
#         self.playing = not self.playing
#         if self.playing:
#             self.last_frame_time = time.time()

#     def stop_video(self):
#         self.playing = False
#         self.frame_index = 0
#         self.current_pixmap = None
#         self.last_frame_time = None
#         self.release()

#     def release(self):
#         if self.cap is not None:
#             self.cap.release()
#         self.cap = None

#     def get_next_pixmap(self) -> QPixmap | None:
#         if not self.cap or not self.playing:
#             return self.current_pixmap

#         current_time = time.time()
#         if self.last_frame_time is None:
#             self.last_frame_time = current_time

#         elapsed = current_time - self.last_frame_time

#         if elapsed < self.frame_interval:
#             return self.current_pixmap  # No toca actualizar aún

#         # Avanzar los frames necesarios (por si hubo pequeño retraso)
#         frames_to_advance = int(elapsed / self.frame_interval)
#         self.frame_index += frames_to_advance
#         self.last_frame_time += frames_to_advance * self.frame_interval

#         if self.frame_index >= self.frame_count:
#             self.playing = False
#             return self.current_pixmap

#         self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
#         ret, frame = self.cap.read()
#         if not ret or frame is None:
#             self.playing = False
#             return self.current_pixmap

#         # Convertir a QPixmap
#         frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         h, w, ch = frame_rgb.shape
#         bytes_per_line = ch * w
#         image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
#         pixmap = QPixmap.fromImage(image)

#         self.current_pixmap = pixmap
#         return pixmap
