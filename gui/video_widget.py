"""VideoWidget — a QLabel that paints OpenCV frames emitted from CameraWorker."""
from __future__ import annotations

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy


class VideoWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("videoCanvas")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(560, 420)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setText("Camera initializing...")

    def update_frame(self, bgr_frame: np.ndarray) -> None:
        h, w, ch = bgr_frame.shape
        rgb = bgr_frame[:, :, ::-1].copy()
        image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(image).scaled(
            self.width(), self.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(pixmap)
