import json

from PySide6.QtCharts import (
    QChart, QBarSet, QValueAxis,
    QChartView, QBarSeries, QBarCategoryAxis
)
from PySide6.QtCore import Qt, QThread, QEvent
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QLabel, QPushButton, QComboBox,
    QHBoxLayout, QVBoxLayout, QFrame, QTextEdit
)

from frontend.panels.hwTests.base_window import BaseTestWindow


class SingleFileStorageTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Single File Storage Test",
            subtitle="Read / write benchmark with hash verification",
            parent=parent
        )

        self.setStyleSheet("""
        QPushButton:disabled {
            border: 2px solid #a33;
            color: #777;
            background-color: #1a1a1a;
        }
        """)

        self.setMinimumSize(900, 520)

        # ================= ROOT =================
        root = QHBoxLayout()
        root.setSpacing(16)

        # ==================================================
        # LEFT: CONTROLS
        # ==================================================
        left = QVBoxLayout()
        left.setSpacing(10)

        lbl_device = QLabel("Storage device / path")
        lbl_device.setStyleSheet("font-weight: bold;")

        self.cmb_device = QComboBox()
        self.cmb_device.setFixedHeight(28)

        self.btn_refresh = QPushButton("Refresh devices")
        self.btn_start = QPushButton("Start test")
        self.btn_refresh.setFixedHeight(26)
        self.btn_start.setFixedHeight(32)

        results = QFrame()
        results.setFrameShape(QFrame.StyledPanel)
        res_layout = QVBoxLayout(results)

        lbl_results = QLabel("Test results")
        lbl_results.setStyleSheet("font-weight: bold;")

        self.lbl_write = QLabel("Write speed: — MB/s")
        self.lbl_read = QLabel("Read speed: — MB/s")
        self.lbl_hash = QLabel("Hash match: —")

        for lbl in (self.lbl_write, self.lbl_read, self.lbl_hash):
            lbl.setStyleSheet("color: #ccc;")

        res_layout.addWidget(lbl_results)
        res_layout.addWidget(self.lbl_write)
        res_layout.addWidget(self.lbl_read)
        res_layout.addWidget(self.lbl_hash)

        left.addWidget(lbl_device)
        left.addWidget(self.cmb_device)
        left.addWidget(self.btn_refresh)
        left.addSpacing(6)
        left.addWidget(self.btn_start)
        left.addSpacing(12)
        left.addWidget(results)
        left.addStretch(1)

        # ==================================================
        # RIGHT: STATUS + CHART
        # ==================================================
        right = QVBoxLayout()
        right.setSpacing(10)

        lbl_status = QLabel("Test status")
        lbl_status.setStyleSheet("font-weight: bold;")

        self.txt_status = QTextEdit()
        self.txt_status.setReadOnly(True)
        self.txt_status.setStyleSheet("""
            QTextEdit {
                background-color: #121212;
                color: #cccccc;
                border: 1px solid #333;
            }
        """)

        # ================= CHART =================
        self.chart = QChart()
        self.chart.setTitle("Storage performance (MB/s)")
        self.chart.setTitleBrush(Qt.white)
        self.chart.legend().setVisible(True)
        self.chart.legend().setLabelColor(Qt.white)
        self.chart.setBackgroundVisible(False)

        self.series = QBarSeries()

        self.bar_write = QBarSet("Write")
        self.bar_read = QBarSet("Read")

        self.bar_write.setColor(QColor("#3aa675"))
        self.bar_read.setColor(QColor("#a35a5a"))

        self.series.append(self.bar_write)
        self.series.append(self.bar_read)

        self.chart.addSeries(self.series)

        # --- AXES ---
        self.axis_x = QBarCategoryAxis()
        self.axis_x.append(["Speed"])
        self.axis_x.setLabelsColor(Qt.white)

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("MB/s")
        self.axis_y.setLabelsColor(Qt.white)
        self.axis_y.setTitleBrush(Qt.white)
        self.axis_y.setMin(0)

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)

        self.chart_view = QChartView(self.chart)
        self.axis_y.setMax(1)

        right.addWidget(lbl_status)
        right.addWidget(self.txt_status, 1)
        right.addWidget(self.chart_view, 2)

        # ================= FINAL =================
        root.addLayout(left, 1)
        root.addLayout(right, 2)
        self.layout().addLayout(root)

        # ================= SIGNALS =================
        self.btn_refresh.clicked.connect(self.refresh_devices)
        self.btn_start.clicked.connect(self.start_test)

        self.refresh_devices()

    # ==================================================
    # LOGIC
    # ==================================================

    def refresh_devices(self):
        self.cmb_device.clear()
        for path in self.backend.list_storage_devices():
            self.cmb_device.addItem(path)

    def start_test(self):
        path = self.cmb_device.currentText()
        if not path:
            return

        self.btn_start.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.txt_status.clear()

        self.axis_y.setMax(1)

        #Clear values of series
        self.bar_write.remove(0, self.bar_write.count())
        self.bar_read.remove(0, self.bar_read.count())

        self.thread = QThread(self)
        self.worker = self.backend.create_single_file_storage_test(path)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.status.connect(self.txt_status.append)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)

        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_finished(self, data: dict):
        self._final_result = data

        res = data["result"]
        write = res["write_speed_MBps"]
        read = res["read_speed_MBps"]

        self.lbl_write.setText(f"Write speed: {write} MB/s")
        self.lbl_read.setText(f"Read speed: {read} MB/s")
        self.lbl_hash.setText(f"Hash match: {'YES' if res['hash_match'] else 'NO'}")

        self.bar_write.append(write)
        self.bar_read.append(read)
        self.axis_y.setMax(max(write, read) * 1.2)

        self.save_results(data)

        self.txt_status.append("Test finished")
        self.btn_start.setEnabled(True)
        self.btn_refresh.setEnabled(True)

        self.worker = None
        self.thread = None

    def save_results(self, data: dict):
        path = self.backend.get_journal_path_device(
            test_name=data["test_name"],
            device=data["device"]
        )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self.txt_status.append(f"Saved results to {path.name}")


    def on_error(self, msg: str):
        self.txt_status.append(f"ERROR: {msg}")
        self.btn_start.setEnabled(True)
        self.btn_refresh.setEnabled(True)

    def event(self, e):
        if e.type() == QEvent.Close:
            if self.thread:
                self.thread.quit()
                self.thread.wait()
            e.accept()
            return True
        return super().event(e)
