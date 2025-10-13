# mypy: ignore-errors
import sys

from picamera2 import Picamera2
from picamera2.previews.qt import QPicamera2  # SIN GL
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt


class LensPositionApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera 0 (900×600) — Lens/Sharpness/Contrast Controls")
        self.resize(1200, 720)

        self.picam2 = None
        self.preview = None
        self._last_metadata = {}

        self._lens_min = 0.0
        self._lens_max = 10.0
        self._sharp_min = 0.0
        self._sharp_max = 16.0
        self._cont_min = 0.0
        self._cont_max = 32.0

        # ---------- UI ----------
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)

        main = QtWidgets.QHBoxLayout(central)

        left = QtWidgets.QVBoxLayout()
        main.addLayout(left, stretch=1)

        self.preview_container = QtWidgets.QWidget(self)
        self.preview_layout = QtWidgets.QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        left.addWidget(self.preview_container)

        grid = QtWidgets.QGridLayout()
        left.addLayout(grid)

        # LensPosition
        grid.addWidget(QtWidgets.QLabel("LensPosition:"), 0, 0)
        self.spin_lens = QtWidgets.QDoubleSpinBox(self)
        self.spin_lens.setDecimals(3)
        self.spin_lens.setRange(0.0, 10.0)
        self.spin_lens.setSingleStep(0.05)
        self.spin_lens.setEnabled(False)
        grid.addWidget(self.spin_lens, 0, 1)

        self.lbl_lens_current = QtWidgets.QLabel("current: —", self)
        grid.addWidget(self.lbl_lens_current, 0, 2)

        # Sharpness
        grid.addWidget(QtWidgets.QLabel("Sharpness:"), 1, 0)
        self.spin_sharp = QtWidgets.QDoubleSpinBox(self)
        self.spin_sharp.setDecimals(2)
        self.spin_sharp.setRange(0.0, 16.0)
        self.spin_sharp.setSingleStep(0.1)
        self.spin_sharp.setEnabled(False)
        grid.addWidget(self.spin_sharp, 1, 1)

        self.lbl_sharp_current = QtWidgets.QLabel("current: —", self)
        grid.addWidget(self.lbl_sharp_current, 1, 2)

        # Contrast
        grid.addWidget(QtWidgets.QLabel("Contrast:"), 2, 0)
        self.spin_contrast = QtWidgets.QDoubleSpinBox(self)
        self.spin_contrast.setDecimals(2)
        self.spin_contrast.setRange(0.0, 32.0)
        self.spin_contrast.setSingleStep(0.1)
        self.spin_contrast.setEnabled(False)
        grid.addWidget(self.spin_contrast, 2, 1)

        self.lbl_contrast_current = QtWidgets.QLabel("current: —", self)
        grid.addWidget(self.lbl_contrast_current, 2, 2)

        grid.setColumnStretch(3, 1)

        right = QtWidgets.QVBoxLayout()
        main.addLayout(right, stretch=1)

        right.addWidget(QtWidgets.QLabel("All camera controls (live):"))
        self.txt_controls = QtWidgets.QTextEdit(self)
        self.txt_controls.setReadOnly(True)
        right.addWidget(self.txt_controls, stretch=1)

        self.timer_ui = QtCore.QTimer(self)
        self.timer_ui.setInterval(250)
        self.timer_ui.timeout.connect(self._refresh_ui_from_metadata)

        self.spin_lens.valueChanged.connect(self._apply_lens_position)
        self.spin_sharp.valueChanged.connect(self._apply_sharpness)
        self.spin_contrast.valueChanged.connect(self._apply_contrast)

        QtCore.QTimer.singleShot(0, self._start_camera)

    def _start_camera(self):
        self._stop_camera()

        self.picam2 = Picamera2(camera_num=0)

        try:
            self.preview = QPicamera2(self.picam2, width=900, height=600)
        except TypeError:
            self.preview = QPicamera2(self.picam2, 900, 600)

        self.preview.setMinimumSize(900, 600)
        self.preview.setMaximumSize(900, 600)
        self.preview_layout.addWidget(
            self.preview, alignment=Qt.AlignLeft | Qt.AlignTop
        )

        cfg = self.picam2.create_video_configuration(
            main={"size": (900, 600), "format": "RGB888"}, buffer_count=2
        )
        self.picam2.configure(cfg)

        try:
            fps = 30
            us = int(1e6 / fps)
            self.picam2.set_controls({"FrameDurationLimits": (us, us)})
        except Exception:
            pass

        def on_request(req):
            try:
                md = req.get_metadata()
                if isinstance(md, dict):
                    self._last_metadata = md
            finally:
                pass

        try:
            self.picam2.post_callback = on_request
        except Exception:
            self.picam2.request_callback = on_request

        self.picam2.start()
        try:
            self.preview.start()
        except Exception:
            pass

        self._init_controls_from_camera()

        self.timer_ui.start()

    def _stop_camera(self):
        self.timer_ui.stop()
        try:
            if self.picam2 is not None:
                try:
                    self.picam2.post_callback = None
                except Exception:
                    pass
                try:
                    self.picam2.request_callback = None
                except Exception:
                    pass
                self.picam2.stop()
                self.picam2.close()
        except Exception:
            pass
        self.picam2 = None
        self._last_metadata = {}

        if self.preview is not None:
            self.preview.setParent(None)
        self.preview = None

    def _init_controls_from_camera(self):
        if self.picam2 is None:
            for w in (self.spin_lens, self.spin_sharp, self.spin_contrast):
                w.setEnabled(False)
            return

        cc = self.picam2.camera_controls

        # LensPosition
        lp = cc.get("LensPosition", None)
        if lp and len(lp) >= 2:
            self._lens_min = float(lp[0])
            self._lens_max = float(lp[1])
            self.spin_lens.setRange(self._lens_min, self._lens_max)
            step = max((self._lens_max - self._lens_min) / 200.0, 0.01)
            self.spin_lens.setSingleStep(step)

        # Sharpness
        sh = cc.get("Sharpness", None)
        if sh and len(sh) >= 2:
            self._sharp_min = float(sh[0])
            self._sharp_max = float(sh[1])
            self.spin_sharp.setRange(self._sharp_min, self._sharp_max)
        self.spin_sharp.setSingleStep(0.1)

        # Contrast
        ct = cc.get("Contrast", None)
        if ct and len(ct) >= 2:
            self._cont_min = float(ct[0])
            self._cont_max = float(ct[1])
            self.spin_contrast.setRange(self._cont_min, self._cont_max)
        self.spin_contrast.setSingleStep(0.1)

        md = self._last_metadata

        def initial(name, fallback_range, default_from_cc):
            cur = md.get(name, None)
            if cur is not None:
                return float(cur)
            if default_from_cc is not None:
                return float(default_from_cc)
            lo, hi = fallback_range
            return (lo + hi) / 2.0

        lens_def = lp[2] if (lp and len(lp) > 2) else None
        sharp_def = sh[2] if (sh and len(sh) > 2) else None
        cont_def = ct[2] if (ct and len(ct) > 2) else None

        v_lens = initial("LensPosition", (self._lens_min, self._lens_max), lens_def)
        v_sharp = initial("Sharpness", (self._sharp_min, self._sharp_max), sharp_def)
        v_cont = initial("Contrast", (self._cont_min, self._cont_max), cont_def)

        self.spin_lens.blockSignals(True)
        self.spin_lens.setValue(v_lens)
        self.spin_lens.blockSignals(False)
        self.spin_sharp.blockSignals(True)
        self.spin_sharp.setValue(v_sharp)
        self.spin_sharp.blockSignals(False)
        self.spin_contrast.blockSignals(True)
        self.spin_contrast.setValue(v_cont)
        self.spin_contrast.blockSignals(False)

        self.spin_lens.setEnabled(True)
        self.spin_sharp.setEnabled(True)
        self.spin_contrast.setEnabled(True)

    def _apply_lens_position(self, value: float):
        if self.picam2 is None:
            return
        try:
            self.picam2.set_controls({"LensPosition": float(value)})
        except Exception:
            try:
                self.picam2.set_controls({"AfMode": 2})
                self.picam2.set_controls({"LensPosition": float(value)})
            except Exception:
                pass

    def _apply_sharpness(self, value: float):
        if self.picam2 is None:
            return
        try:
            self.picam2.set_controls({"Sharpness": float(value)})
        except Exception:
            pass

    def _apply_contrast(self, value: float):
        if self.picam2 is None:
            return
        try:
            self.picam2.set_controls({"Contrast": float(value)})
        except Exception:
            pass

    def _refresh_ui_from_metadata(self):
        md = self._last_metadata or {}

        # Labels current
        cur_lens = md.get("LensPosition", None)
        self.lbl_lens_current.setText(
            f"current: {float(cur_lens):.3f}" if cur_lens is not None else "current: —"
        )

        cur_sharp = md.get("Sharpness", None)
        self.lbl_sharp_current.setText(
            f"current: {float(cur_sharp):.2f}"
            if cur_sharp is not None
            else "current: —"
        )

        cur_cont = md.get("Contrast", None)
        self.lbl_contrast_current.setText(
            f"current: {float(cur_cont):.2f}" if cur_cont is not None else "current: —"
        )

        def sync(spin, val, tol):
            if val is None:
                return
            v = float(val)
            if abs(spin.value() - v) > tol:
                spin.blockSignals(True)
                spin.setValue(v)
                spin.blockSignals(False)

        sync(self.spin_lens, cur_lens, max(self.spin_lens.singleStep() / 2.0, 0.005))
        sync(self.spin_sharp, cur_sharp, max(self.spin_sharp.singleStep() / 2.0, 0.01))
        sync(
            self.spin_contrast,
            cur_cont,
            max(self.spin_contrast.singleStep() / 2.0, 0.01),
        )

        txt = self._format_all_controls_text(md)
        self.txt_controls.setPlainText(txt)

    def _format_all_controls_text(self, metadata: dict) -> str:
        if self.picam2 is None:
            return ""
        try:
            cc = self.picam2.camera_controls
            names = sorted(cc.keys())
        except Exception:
            names = []

        lines = ["Camera index: 0", ""]
        for name in names:
            cur = metadata.get(name, None)
            if cur is None:
                cur_str = "—"
            elif isinstance(cur, float):
                cur_str = f"{cur:.4f}"
            elif isinstance(cur, (list, tuple)):
                cur_str = "(" + ", ".join(str(x) for x in cur) + ")"
            else:
                cur_str = str(cur)

            lines.append(f"{name:<22} {cur_str}")
        return "\n".join(lines)

    def closeEvent(self, event):
        self._stop_camera()
        super().closeEvent(event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = LensPositionApp()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
