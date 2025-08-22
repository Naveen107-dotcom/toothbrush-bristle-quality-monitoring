import sys
import cv2
import numpy as np
import serial
import time
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import QTimer

# ===== Arduino Serial Setup =====
arduino = serial.Serial('COM10', 9600)  # Change COM port if needed
time.sleep(2)

# ===== Parameters =====
ROI_X, ROI_Y = 100, 50
ROI_WIDTH, ROI_HEIGHT = 300, 200
CANNY_LOW = 60
CANNY_HIGH = 150
CONTOUR_MIN_LENGTH = 50
ZIGZAG_THRESHOLD = 3

# ===== Camera Setup =====
cap = cv2.VideoCapture(0)

class BrushChecker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brush Zig-Zag Detector")

        # Video displays
        self.frame_label = QLabel()
        self.roi_label = QLabel()
        self.edges_label = QLabel()

        # Pass/Fail indicator
        self.status_label = QLabel("Waiting...")
        self.status_label.setStyleSheet("font-size: 20px; color: gray; font-weight: bold;")

        # Buttons
        self.refresh_btn = QPushButton("Refresh")
        self.quit_btn = QPushButton("Quit")

        self.refresh_btn.clicked.connect(self.refresh_detection)
        self.quit_btn.clicked.connect(self.close_app)

        # Layouts
        video_layout = QHBoxLayout()
        video_layout.addWidget(self.frame_label)
        video_layout.addWidget(self.roi_label)
        video_layout.addWidget(self.edges_label)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.quit_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(video_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        # Timer for real-time update
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def refresh_detection(self):
        self.status_label.setText("Waiting...")
        self.status_label.setStyleSheet("font-size: 20px; color: gray; font-weight: bold;")

    def close_app(self):
        cap.release()
        arduino.close()
        cv2.destroyAllWindows()
        self.close()

    def update_frame(self):
        ret, frame = cap.read()
        if not ret:
            return

        # Draw ROI rectangle
        cv2.rectangle(frame, (ROI_X, ROI_Y), (ROI_X + ROI_WIDTH, ROI_Y + ROI_HEIGHT), (0, 255, 0), 2)

        # Crop ROI
        roi = frame[ROI_Y:ROI_Y + ROI_HEIGHT, ROI_X:ROI_X + ROI_WIDTH]

        # Gray + blur
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny
        edges = cv2.Canny(blurred, CANNY_LOW, CANNY_HIGH)

        # Contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Count zigzag edges
        zigzag_count = 0
        for cnt in contours:
            if cv2.arcLength(cnt, True) > CONTOUR_MIN_LENGTH:
                approx = cv2.approxPolyDP(cnt, 2, True)
                if len(approx) > 6:
                    zigzag_count += 1
                cv2.drawContours(roi, [cnt], -1, (255, 0, 0), 1)

        # Pass/Fail logic
        if zigzag_count >= ZIGZAG_THRESHOLD:
            result_text = "PASS"
            self.status_label.setStyleSheet("font-size: 20px; color: green; font-weight: bold;")
            arduino.write(b'P')
        else:
            result_text = "FAIL"
            self.status_label.setStyleSheet("font-size: 20px; color: red; font-weight: bold;")
            arduino.write(b'F')

        self.status_label.setText(f"{result_text} | ZigZag Count: {zigzag_count}")

        # Convert frames for Qt display
        self.frame_label.setPixmap(self.convert_cv_qt(frame))
        self.roi_label.setPixmap(self.convert_cv_qt(roi))
        self.edges_label.setPixmap(self.convert_cv_qt(cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)))

    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        return QPixmap.fromImage(QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = BrushChecker()
    win.show()
    sys.exit(app.exec_())
