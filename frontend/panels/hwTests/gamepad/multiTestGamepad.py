# frontend/panels/hwTests/gamepad/multiTestGamepad.py

import math

from PySide6.QtCore import Qt, QThread, QEvent
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QFrame, QStyle, QPushButton,
)

from frontend.panels.hwTests.base_window import BaseTestWindow
from frontend.panels.hwTests.gamepad.elements.AnalogButtonBar import AnalogButtonBar
from frontend.panels.hwTests.gamepad.elements.AxisBar import AxisBar
from frontend.panels.hwTests.gamepad.elements.StickWidget import StickWidget
from frontend.panels.hwTests.gamepad.gamepad_visual import GamepadVisual


class GamepadMultiTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Gamepad Multitest (X-Input)",
            subtitle="Buttons, sticks, circular error (WARNING! Only first gamepad gets tested!)",
            parent=parent
        )

        self.setFixedSize(1200, 750)
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        self._thread: QThread | None = None
        self._worker = None

        # Base layout from BaseTestWindow
        self.base_layout = self.layout()

        # ================= ROOT =================
        root = QHBoxLayout()
        root.setSpacing(16)

        # ==========================================================
        # LEFT PANEL
        # ==========================================================

        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)

        # ================= BUTTONS =================
        left_layout.addWidget(QLabel("Buttons"))

        button_container = QWidget()
        button_grid = QGridLayout(button_container)
        button_grid.setSpacing(10)
        button_grid.setContentsMargins(0, 0, 0, 0)

        self.button_bars = {}

        button_names = [
            "A", "B", "X", "Y",
            "LB", "RB", "LT", "RT",
            "BACK", "START", "LS", "RS",
            "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT",
        ]

        for i, name in enumerate(button_names):
            bar = AnalogButtonBar(name, height=22)
            self.button_bars[name] = bar
            button_grid.addWidget(bar, i // 2, i % 2)

        left_layout.addWidget(button_container)

        # ================= SEPARATOR =================
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color:#333;")
        left_layout.addWidget(sep)

        # ================= ANALOG STICKS =================
        analog_container = QWidget()
        analog_grid = QGridLayout(analog_container)
        analog_grid.setSpacing(16)

        # Headers
        analog_grid.addWidget(QLabel("Left Stick"), 0, 0, Qt.AlignCenter)
        analog_grid.addWidget(QLabel("Right Stick"), 0, 1, Qt.AlignCenter)

        # Stick visuals
        self.left_stick = StickWidget("L-Stick", show_values=False)
        self.right_stick = StickWidget("R-Stick", show_values=False)

        analog_grid.addWidget(self.left_stick, 1, 0, Qt.AlignCenter)
        analog_grid.addWidget(self.right_stick, 1, 1, Qt.AlignCenter)

        # Axis bars
        self.left_lx = AxisBar("LX", width=180)
        self.left_ly = AxisBar("LY", width=180)
        self.right_rx = AxisBar("RX", width=180)
        self.right_ry = AxisBar("RY", width=180)

        analog_grid.addWidget(self.left_lx, 2, 0)
        analog_grid.addWidget(self.right_rx, 2, 1)
        analog_grid.addWidget(self.left_ly, 3, 0)
        analog_grid.addWidget(self.right_ry, 3, 1)

        left_layout.addWidget(analog_container)
        left_layout.addStretch(1)

        left_container = QWidget()
        left_container.setLayout(left_layout)

        # ==========================================================
        # RIGHT PANEL
        # ==========================================================

        right_layout = QVBoxLayout()
        right_layout.setSpacing(12)

        self.gamepad_visual = GamepadVisual()
        right_layout.addWidget(self.gamepad_visual)
        right_layout.addStretch(1)

        right_container = QWidget()
        right_container.setLayout(right_layout)

        # ================= STATS PANEL =================

        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.StyledPanel)
        stats_frame.setFixedHeight(270)
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setSpacing(3)

        stats_title = QLabel("Stick Quality")
        stats_title.setStyleSheet("font-weight: bold;")

        self.lbl_left_error = QLabel("Left stick circular error: —")
        self.lbl_left_max = QLabel("Left stick max radius: —")

        self.lbl_right_error = QLabel("Right stick circular error: —")
        self.lbl_right_max = QLabel("Right stick max radius: —")

        for lbl in (
                self.lbl_left_error,
                self.lbl_left_max,
                self.lbl_right_error,
                self.lbl_right_max,
        ):
            lbl.setStyleSheet("color: #cccccc;")

        stats_layout.addWidget(stats_title)
        stats_layout.addWidget(self.lbl_left_error)
        stats_layout.addWidget(self.lbl_left_max)
        stats_layout.addSpacing(6)
        stats_layout.addWidget(self.lbl_right_error)
        stats_layout.addWidget(self.lbl_right_max)

        right_layout.addWidget(stats_frame)

        self.btn_save = QPushButton("Save results")
        self.btn_save.setFixedHeight(18)

        self.btn_reset = QPushButton("Reset results")
        self.btn_reset.setFixedHeight(18)

        self.btn_save.clicked.connect(lambda: self.on_save_clicked())
        self.btn_reset.clicked.connect(lambda: self.on_reset_clicked())

        right_layout.addWidget(self.btn_save)
        right_layout.addWidget(self.btn_reset)

        # ================= FINAL =================
        root.addWidget(left_container, 1)
        root.addWidget(right_container, 1)

        self.base_layout.addLayout(root)

        self.start_test()



        # ==========================================================
        # DEMO TIMER (REMOVE WHEN BACKEND WIRED)
        # ==========================================================

        # self._t = 0.0
        # self.startTimer(16)

    # ==========================================================
    # DEMO UPDATE (REMOVE LATER)
    # ==========================================================

    def start_test(self):
        self._thread = QThread(self)
        self._worker = self.backend.create_gamepad_test()

        self._worker.moveToThread(self._thread)

        # ---- signals ----
        self._thread.started.connect(self._worker.run)
        self._worker.live.connect(self.on_live_update)
        self._worker.stats.connect(self.on_stats_update)
        #self._worker.finished.connect(self.on_test_finished)
        #self._worker.error.connect(self.on_test_error)

        # ---- cleanup ----
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def on_live_update(self, state: dict):
        # ================= BUTTONS =================
        for name, value in state["buttons"].items():
            bar = self.button_bars.get(name)
            if bar:
                bar.set_value(value)

            self.gamepad_visual.set_button(name, value)

        # ================= TRIGGERS =================
        for trg, val in state["triggers"].items():
            bar = self.button_bars.get(trg)
            if bar:
                bar.set_value(val)
            self.gamepad_visual.set_trigger(trg, val)

        # ================= STICKS =================
        lx, ly = state["sticks"]["L"]
        rx, ry = state["sticks"]["R"]

        self.left_stick.set_value(lx, ly)
        self.right_stick.set_value(rx, ry)

        self.left_lx.set_value(lx)
        self.left_ly.set_value(ly)
        self.right_rx.set_value(rx)
        self.right_ry.set_value(ry)

        self.gamepad_visual.set_stick("L", lx, ly)
        self.gamepad_visual.set_stick("R", rx, ry)

    def on_stats_update(self, stats):
        left = stats["left_stick"]
        right = stats["right_stick"]

        if left:
            self.lbl_left_error.setText(
                f"Left stick circular error: {left['circular_error']}"
            )
            self.lbl_left_max.setText(
                f"Left stick max radius: {left['max_radius']}"
            )

        if right:
            self.lbl_right_error.setText(
                f"Right stick circular error: {right['circular_error']}"
            )
            self.lbl_right_max.setText(
                f"Right stick max radius: {right['max_radius']}"
            )

    def on_reset_clicked(self):
        if self._worker:
            self._worker.reset_stats()

        for bar in self.button_bars.values():
            bar.reset()

        self.left_stick.reset()
        self.right_stick.reset()

        self.left_lx.reset()
        self.left_ly.reset()
        self.right_rx.reset()
        self.right_ry.reset()

        self.gamepad_visual.reset()

        self.lbl_left_error.setText("Left stick circular error: —")
        self.lbl_left_max.setText("Left stick max radius: —")
        self.lbl_right_error.setText("Right stick circular error: —")
        self.lbl_right_max.setText("Right stick max radius: —")

    def on_save_clicked(self):
        if not self._worker:
            return

        result = self._worker._build_result()

        path = self.backend.get_journal_path(
            "GamepadMultiTest",
            result["device"].get("vid", 0),
            result["device"].get("pid", 0),
        )

        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    # def timerEvent(self, event):
    #     self._t += 0.05
    #
    #     x = math.sin(self._t)
    #     y = math.cos(self._t)
    #
    #     # Stick visuals
    #     self.left_stick.set_value(x, y)
    #     self.right_stick.set_value(-y, x)
    #
    #     # Axis bars
    #     self.left_lx.set_value(x)
    #     self.left_ly.set_value(y)
    #     self.right_rx.set_value(-y)
    #     self.right_ry.set_value(x)
    #
    #     # Buttons (demo pulse)
    #     self.button_bars["A"].set_value(abs(x))
    #     self.button_bars["RT"].set_value(abs(y))

    def event(self, e):

        if e.type() == QEvent.Close:
            if self._worker:
                self._worker.stop()

            if self._thread:
                self._thread.quit()
                self._thread.wait(500)
            e.accept()
        return super().event(e)
