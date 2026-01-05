import json

from PySide6.QtCore import Qt, QThread, QEvent
from PySide6.QtWidgets import (
    QLabel, QPushButton, QComboBox,
    QHBoxLayout, QVBoxLayout, QFrame,
    QTextEdit, QTableWidget, QTableWidgetItem
)

from frontend.panels.hwTests.base_window import BaseTestWindow


class MultiFileStorageTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Multiple Files Storage Test",
            subtitle="Batch read/write benchmark with hash verification",
            parent=parent
        )

        self.setStyleSheet("""
        QPushButton:disabled {
            border: 2px solid #a33;
            color: #777;
            background-color: #1a1a1a;
        }
        """)

        self.setMinimumSize(1000, 780)

        # ================= ROOT =================
        root = QHBoxLayout()
        root.setSpacing(16)

        # ==================================================
        # LEFT
        # ==================================================
        left = QVBoxLayout()

        lbl_device = QLabel("Storage device / path")
        lbl_device.setStyleSheet("font-weight: bold;")

        self.cmb_device = QComboBox()
        self.btn_refresh = QPushButton("Refresh devices")
        self.btn_start = QPushButton("Start multi-file test")

        for b in (self.btn_refresh, self.btn_start):
            b.setFixedHeight(30)

        # ---- Summary ----
        summary = QFrame()
        summary.setFrameShape(QFrame.StyledPanel)
        sum_layout = QVBoxLayout(summary)

        lbl_summary = QLabel("Summary results")
        lbl_summary.setStyleSheet("font-weight: bold;")

        self.lbl_avg_write = QLabel("Avg write speed: — MB/s")
        self.lbl_avg_read = QLabel("Avg read speed: — MB/s")
        self.lbl_files_ok = QLabel("Files verified: — / —")

        for lbl in (self.lbl_avg_write, self.lbl_avg_read, self.lbl_files_ok):
            lbl.setStyleSheet("color: #ccc;")

        sum_layout.addWidget(lbl_summary)
        sum_layout.addWidget(self.lbl_avg_write)
        sum_layout.addWidget(self.lbl_avg_read)
        sum_layout.addWidget(self.lbl_files_ok)

        left.addWidget(lbl_device)
        left.addWidget(self.cmb_device)
        left.addWidget(self.btn_refresh)
        left.addSpacing(8)
        left.addWidget(self.btn_start)
        left.addSpacing(12)
        left.addWidget(summary)
        left.addStretch(1)

        # ==================================================
        # RIGHT
        # ==================================================
        right = QVBoxLayout()

        lbl_status = QLabel("Test status")
        lbl_status.setStyleSheet("font-weight: bold;")

        self.txt_status = QTextEdit()
        self.txt_status.setReadOnly(True)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "File", "Write MB/s", "Read MB/s", "Hash OK"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        right.addWidget(lbl_status)
        right.addWidget(self.txt_status, 1)
        right.addWidget(QLabel("Per-file results"))
        right.addWidget(self.table, 3)

        root.addLayout(left, 1)
        root.addLayout(right, 3)
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
        self.table.setRowCount(0)

        self.thread = QThread(self)
        self.worker = self.backend.create_multi_file_storage_test(path)
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

        summary = data["summary"]
        files = data["files"]

        self.lbl_avg_write.setText(f"Avg write speed: {summary['avg_write_MBps']} MB/s")
        self.lbl_avg_read.setText(f"Avg read speed: {summary['avg_read_MBps']} MB/s")
        self.lbl_files_ok.setText(
            f"Files verified: {summary['files_ok']} / {summary['files_total']}"
        )

        for r in files:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r["file"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(r["write_MBps"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(r["read_MBps"])))
            self.table.setItem(row, 3, QTableWidgetItem("YES" if r["hash_match"] else "NO"))

        self.save_results(data)

        self.txt_status.append("Multi-file test finished")
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
            if self.worker:
                self.worker.stop()
            if self.thread:
                self.thread.quit()
                self.thread.wait()
            e.accept()
            return True
        return super().event(e)
