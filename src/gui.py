import sys
import json
import os
import time
from typing import Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QSpinBox, QDoubleSpinBox, QTextEdit, QGroupBox,
                            QListWidget, QTabWidget, QCheckBox, QMessageBox,
                            QSystemTrayIcon, QMenu, QFrame, QGridLayout,
                            QSplitter, QProgressBar, QFileDialog)
from PyQt6.QtCore import QTimer, pyqtSignal, QThread, Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QPainter, QColor, QBrush

from .audio_engine import AudioDuckingEngine, AudioDuckingConfig

class ModernFrame(QFrame):
    """Modern styled frame widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #3daee9;
                border-radius: 8px;
                background-color: #2a2a2a;
                margin: 5px;
                padding: 10px;
            }
        """)

class StatusIndicator(QWidget):
    """Custom status indicator widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.active = False
    
    def set_active(self, active: bool):
        self.active = active
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circle
        color = QColor("#4CAF50") if self.active else QColor("#757575")
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 16, 16)

class AudioPriorityGUI(QMainWindow):
    status_update = pyqtSignal(str, str, dict)
    
    def __init__(self):
        super().__init__()
        self.engine: Optional[AudioDuckingEngine] = None
        self.config_file = "audio_priority_config.json"
        
        self.setWindowTitle("Audio Priority Manager")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(self._get_dark_theme())
        
        # Setup UI
        self.setup_ui()
        self.setup_tray()
        self.load_config()
        
        # Connect signals
        self.status_update.connect(self.on_status_update)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
        # Initialize duck percentage display
        self.update_duck_percentage()

    def _get_dark_theme(self) -> str:
        return """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QTabWidget::pane {
            border: 1px solid #3daee9;
            background-color: #2a2a2a;
        }
        QTabWidget::tab-bar {
            alignment: center;
        }
        QTabBar::tab {
            background-color: #404040;
            color: #ffffff;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #3daee9;
        }
        QTabBar::tab:hover {
            background-color: #505050;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #3daee9;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 10px;
            background-color: #2a2a2a;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #3daee9;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox {
            border: 2px solid #555555;
            border-radius: 4px;
            padding: 5px;
            background-color: #404040;
            color: #ffffff;
        }
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border-color: #3daee9;
        }
        QPushButton {
            background-color: #3daee9;
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #1a6b96;
        }
        QPushButton:disabled {
            background-color: #555555;
            color: #888888;
        }
        QTextEdit {
            border: 2px solid #555555;
            border-radius: 4px;
            background-color: #404040;
            color: #ffffff;
            font-family: 'Consolas', 'Monaco', monospace;
        }
        QListWidget {
            border: 2px solid #555555;
            border-radius: 4px;
            background-color: #404040;
            color: #ffffff;
            alternate-background-color: #4a4a4a;
        }
        QCheckBox {
            color: #ffffff;
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        QCheckBox::indicator:unchecked {
            border: 2px solid #555555;
            background-color: #404040;
            border-radius: 3px;
        }
        QCheckBox::indicator:checked {
            border: 2px solid #3daee9;
            background-color: #3daee9;
            border-radius: 3px;
        }
        QProgressBar {
            border: 2px solid #555555;
            border-radius: 4px;
            text-align: center;
            background-color: #404040;
        }
        QProgressBar::chunk {
            background-color: #3daee9;
            border-radius: 2px;
        }
        """

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Header with status
        header_frame = ModernFrame()
        header_layout = QHBoxLayout(header_frame)
        
        # Title and status
        title_label = QLabel("Audio Priority Manager")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_indicator = StatusIndicator()
        self.status_label = QLabel("Stopped")
        header_layout.addWidget(QLabel("Status:"))
        header_layout.addWidget(self.status_indicator)
        header_layout.addWidget(self.status_label)
        
        main_layout.addWidget(header_frame)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Setup tabs
        self.setup_config_tab()
        self.setup_advanced_tab()
        self.setup_monitor_tab()
        self.setup_log_tab()
        
        # Control buttons
        button_frame = ModernFrame()
        button_layout = QHBoxLayout(button_frame)
        
        self.start_button = QPushButton("▶ Start Ducking")
        self.start_button.clicked.connect(self.start_ducking)
        self.start_button.setShortcut("Ctrl+S")
        self.start_button.setToolTip("Start audio ducking (Ctrl+S)")
        
        self.stop_button = QPushButton("⏹ Stop Ducking")
        self.stop_button.clicked.connect(self.stop_ducking)
        self.stop_button.setEnabled(False)
        self.stop_button.setShortcut("Ctrl+T")
        self.stop_button.setToolTip("Stop audio ducking (Ctrl+T)")
        
        self.minimize_button = QPushButton("📥 Minimize to Tray")
        self.minimize_button.clicked.connect(self.hide)
        self.minimize_button.setShortcut("Ctrl+M")
        self.minimize_button.setToolTip("Hide to system tray (Ctrl+M)")
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()
        button_layout.addWidget(self.minimize_button)
        
        main_layout.addWidget(button_frame)

    def setup_config_tab(self):
        """Setup main configuration tab"""
        config_widget = QWidget()
        layout = QVBoxLayout(config_widget)
        
        # Basic settings
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QGridLayout(basic_group)
        
        # Priority process
        basic_layout.addWidget(QLabel("Priority Process:"), 0, 0)
        self.priority_edit = QLineEdit()
        self.priority_edit.setPlaceholderText("e.g., vlc.exe, spotify.exe, chrome.exe")
        self.priority_edit.setToolTip("Process name that will have audio priority (case insensitive)")
        basic_layout.addWidget(self.priority_edit, 0, 1)
        
        # Duck to volume
        basic_layout.addWidget(QLabel("Duck to Volume:"), 1, 0)
        self.duck_to_spin = QDoubleSpinBox()
        self.duck_to_spin.setRange(0.0, 1.0)
        self.duck_to_spin.setSingleStep(0.05)
        self.duck_to_spin.setValue(0.25)
        self.duck_to_spin.setDecimals(2)
        self.duck_to_spin.valueChanged.connect(self.update_duck_percentage)
        self.duck_to_spin.setToolTip("Volume level to reduce other applications to when priority audio is playing")
        basic_layout.addWidget(self.duck_to_spin, 1, 1)
        
        # Threshold
        basic_layout.addWidget(QLabel("Activity Threshold:"), 2, 0)
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.0, 1.0)
        self.threshold_spin.setSingleStep(0.01)
        self.threshold_spin.setValue(0.02)
        self.threshold_spin.setDecimals(3)
        self.threshold_spin.setToolTip("Minimum audio level to consider an application as 'active'")
        basic_layout.addWidget(self.threshold_spin, 2, 1)
        
        layout.addWidget(basic_group)
        
        # Other processes (optional)
        other_group = QGroupBox("Target Processes (Optional)")
        other_layout = QVBoxLayout(other_group)
        
        self.limit_checkbox = QCheckBox("Limit ducking to specific processes only")
        self.limit_checkbox.setToolTip("When checked, only the processes in the list below will be ducked")
        other_layout.addWidget(self.limit_checkbox)
        
        self.other_processes_list = QListWidget()
        self.other_processes_list.setMaximumHeight(100)
        self.other_processes_list.setToolTip("List of processes that will be ducked when priority audio is active")
        other_layout.addWidget(self.other_processes_list)
        
        other_button_layout = QHBoxLayout()
        self.add_process_edit = QLineEdit()
        self.add_process_edit.setPlaceholderText("Process name (e.g., chrome.exe)")
        self.add_process_edit.returnPressed.connect(self.add_other_process)  # Enter key support
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_other_process)
        add_button.setToolTip("Add process to the list")
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.remove_other_process)
        remove_button.setToolTip("Remove selected process from the list")
        
        other_button_layout.addWidget(self.add_process_edit)
        other_button_layout.addWidget(add_button)
        other_button_layout.addWidget(remove_button)
        other_layout.addWidget(QWidget())  # spacer
        other_layout.addLayout(other_button_layout)
        
        layout.addWidget(other_group)
        layout.addStretch()
        
        self.tab_widget.addTab(config_widget, "⚙ Basic Config")

    def setup_advanced_tab(self):
        """Setup advanced configuration tab"""
        advanced_widget = QWidget()
        layout = QVBoxLayout(advanced_widget)
        
        # Priority detection
        priority_group = QGroupBox("Priority Detection")
        priority_layout = QGridLayout(priority_group)
        
        priority_layout.addWidget(QLabel("Attack Threshold:"), 0, 0)
        self.attack_threshold_spin = QDoubleSpinBox()
        self.attack_threshold_spin.setRange(0.0, 1.0)
        self.attack_threshold_spin.setSingleStep(0.01)
        self.attack_threshold_spin.setValue(0.06)
        self.attack_threshold_spin.setDecimals(3)
        self.attack_threshold_spin.setToolTip("Audio level required to trigger priority detection")
        priority_layout.addWidget(self.attack_threshold_spin, 0, 1)
        
        priority_layout.addWidget(QLabel("Release Threshold:"), 1, 0)
        self.release_threshold_spin = QDoubleSpinBox()
        self.release_threshold_spin.setRange(0.0, 1.0)
        self.release_threshold_spin.setSingleStep(0.01)
        self.release_threshold_spin.setValue(0.02)
        self.release_threshold_spin.setDecimals(3)
        self.release_threshold_spin.setToolTip("Audio level below which priority detection is released")
        priority_layout.addWidget(self.release_threshold_spin, 1, 1)
        
        priority_layout.addWidget(QLabel("Attack Frames:"), 2, 0)
        self.attack_frames_spin = QSpinBox()
        self.attack_frames_spin.setRange(1, 100)
        self.attack_frames_spin.setValue(3)
        self.attack_frames_spin.setToolTip("Number of consecutive frames above attack threshold to activate")
        priority_layout.addWidget(self.attack_frames_spin, 2, 1)
        
        priority_layout.addWidget(QLabel("Release Frames:"), 3, 0)
        self.release_frames_spin = QSpinBox()
        self.release_frames_spin.setRange(1, 100)
        self.release_frames_spin.setValue(20)
        self.release_frames_spin.setToolTip("Number of consecutive frames below release threshold to deactivate")
        priority_layout.addWidget(self.release_frames_spin, 3, 1)
        
        layout.addWidget(priority_group)
        
        # Timing settings
        timing_group = QGroupBox("Timing & Performance")
        timing_layout = QGridLayout(timing_group)
        
        timing_layout.addWidget(QLabel("Min Overlap Frames:"), 0, 0)
        self.overlap_frames_spin = QSpinBox()
        self.overlap_frames_spin.setRange(1, 50)
        self.overlap_frames_spin.setValue(2)
        self.overlap_frames_spin.setToolTip("Minimum frames of audio overlap required before ducking")
        timing_layout.addWidget(self.overlap_frames_spin, 0, 1)
        
        timing_layout.addWidget(QLabel("Polling Interval (s):"), 1, 0)
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.02, 1.0)
        self.interval_spin.setSingleStep(0.01)
        self.interval_spin.setValue(0.05)
        self.interval_spin.setDecimals(3)
        self.interval_spin.setToolTip("How often to check audio levels (lower = more responsive, higher CPU)")
        timing_layout.addWidget(self.interval_spin, 1, 1)
        
        timing_layout.addWidget(QLabel("Fade Step:"), 2, 0)
        self.step_spin = QDoubleSpinBox()
        self.step_spin.setRange(0.01, 1.0)
        self.step_spin.setSingleStep(0.01)
        self.step_spin.setValue(0.08)
        self.step_spin.setDecimals(3)
        self.step_spin.setToolTip("Volume change step size (lower = smoother transitions)")
        timing_layout.addWidget(self.step_spin, 2, 1)
        
        layout.addWidget(timing_group)
        layout.addStretch()
        
        self.tab_widget.addTab(advanced_widget, "🔧 Advanced")

    def setup_monitor_tab(self):
        """Setup monitoring tab"""
        monitor_widget = QWidget()
        layout = QVBoxLayout(monitor_widget)
        
        # Real-time status
        status_group = QGroupBox("Real-time Status")
        status_layout = QGridLayout(status_group)
        
        status_layout.addWidget(QLabel("Priority Status:"), 0, 0)
        self.priority_status_label = QLabel("Inactive")
        status_layout.addWidget(self.priority_status_label, 0, 1)
        
        status_layout.addWidget(QLabel("Ducked Sessions:"), 1, 0)
        self.ducked_sessions_label = QLabel("0")
        status_layout.addWidget(self.ducked_sessions_label, 1, 1)
        
        status_layout.addWidget(QLabel("Total Sessions:"), 2, 0)
        self.total_sessions_label = QLabel("0")
        status_layout.addWidget(self.total_sessions_label, 2, 1)
        
        layout.addWidget(status_group)
        
        # Activity indicator
        activity_group = QGroupBox("Activity Levels")
        activity_layout = QVBoxLayout(activity_group)
        
        # Priority process progress
        priority_label = QLabel("Priority Process Activity:")
        activity_layout.addWidget(priority_label)
        
        self.priority_progress = QProgressBar()
        self.priority_progress.setRange(0, 100)
        self.priority_progress.setValue(0)
        self.priority_progress.setFormat("Priority Audio: %p%")
        self.priority_progress.setToolTip("Real-time audio activity level of priority process")
        activity_layout.addWidget(self.priority_progress)
        
        # Add some spacing
        activity_layout.addSpacing(10)
        
        layout.addWidget(activity_group)
        layout.addStretch()
        
        self.tab_widget.addTab(monitor_widget, "📊 Monitor")

    def setup_log_tab(self):
        """Setup log tab"""
        log_widget = QWidget()
        layout = QVBoxLayout(log_widget)
        
        # Log display
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        # Note: setMaximumBlockCount is not available in QTextEdit, using document().setMaximumBlockCount
        self.log_text.document().setMaximumBlockCount(1000)  # Limit log size
        log_layout.addWidget(self.log_text)
        
        # Log controls
        log_controls = QHBoxLayout()
        clear_log_button = QPushButton("Clear Log")
        clear_log_button.clicked.connect(self.clear_log)
        save_log_button = QPushButton("Save Log")
        save_log_button.clicked.connect(self.save_log)
        
        log_controls.addWidget(clear_log_button)
        log_controls.addWidget(save_log_button)
        log_controls.addStretch()
        
        log_layout.addLayout(log_controls)
        layout.addWidget(log_group)
        
        self.tab_widget.addTab(log_widget, "📝 Log")

    def setup_tray(self):
        """Setup system tray icon"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(self, "System Tray", 
                               "System tray is not available on this system.")
            return
        
        # Create tray icon (simple colored circle for now)
        icon_pixmap = QPixmap(32, 32)
        icon_pixmap.fill(QColor(61, 174, 233))  # Blue color
        
        self.tray_icon = QSystemTrayIcon(QIcon(icon_pixmap), self)
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        start_action = QAction("Start Ducking", self)
        start_action.triggered.connect(self.start_ducking)
        tray_menu.addAction(start_action)
        
        stop_action = QAction("Stop Ducking", self)
        stop_action.triggered.connect(self.stop_ducking)
        tray_menu.addAction(stop_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()

    def _get_priority_audio_level(self) -> float:
        """Get current audio level of priority process"""
        if not self.engine or not self.engine.running:
            return 0.0
        
        try:
            from pycaw.pycaw import AudioUtilities
            priority_name = self.priority_edit.text().strip().lower()
            if not priority_name:
                return 0.0
            
            sessions = AudioUtilities.GetAllSessions()
            max_level = 0.0
            
            for session in sessions:
                try:
                    if not session.Process:
                        continue
                    if session.Process.name().lower() == priority_name:
                        # Get audio meter
                        _, meter = self.engine._get_interfaces(session)
                        if meter:
                            level = meter.GetPeakValue()
                            if level and level > max_level:
                                max_level = level
                except Exception:
                    continue
            
            return max_level
        except Exception:
            return 0.0

    def update_duck_percentage(self):
        """Update duck to volume percentage display"""
        value = self.duck_to_spin.value()
        percentage = int(value * 100)
        self.duck_to_spin.setSuffix(f" ({percentage}%)")

    def add_other_process(self):
        """Add process to other processes list"""
        process_name = self.add_process_edit.text().strip()
        if not process_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a process name.")
            return
        
        # Check for duplicates
        for i in range(self.other_processes_list.count()):
            if self.other_processes_list.item(i).text().lower() == process_name.lower():
                QMessageBox.information(self, "Duplicate", f"'{process_name}' is already in the list.")
                return
        
        self.other_processes_list.addItem(process_name)
        self.add_process_edit.clear()
        self.log_message(f"Added '{process_name}' to target processes list")

    def remove_other_process(self):
        """Remove selected process from list"""
        current_row = self.other_processes_list.currentRow()
        if current_row >= 0:
            item = self.other_processes_list.takeItem(current_row)
            if item:
                self.log_message(f"Removed '{item.text()}' from target processes list")
        else:
            QMessageBox.information(self, "No Selection", "Please select a process to remove.")

    def start_ducking(self):
        """Start the audio ducking engine"""
        if self.engine and self.engine.running:
            return
        
        # Validate inputs
        priority_process = self.priority_edit.text().strip()
        if not priority_process:
            QMessageBox.warning(self, "Invalid Configuration", 
                              "Please specify a priority process name.")
            self.tab_widget.setCurrentIndex(0)  # Switch to config tab
            self.priority_edit.setFocus()
            return
        
        # Validate duck to volume
        if self.duck_to_spin.value() >= 1.0:
            reply = QMessageBox.question(self, "Warning", 
                                       "Duck volume is set to 100%. This won't reduce other audio.\n"
                                       "Continue anyway?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Get other processes if limited
        other_processes = None
        if self.limit_checkbox.isChecked():
            other_processes = []
            for i in range(self.other_processes_list.count()):
                other_processes.append(self.other_processes_list.item(i).text())
            
            if not other_processes:
                QMessageBox.warning(self, "Invalid Configuration", 
                                  "You've enabled 'Limit to specific processes' but no processes are listed.\n"
                                  "Either add processes to the list or disable this option.")
                self.tab_widget.setCurrentIndex(0)  # Switch to config tab
                return
        
        # Create configuration
        config = AudioDuckingConfig(
            priority_process=priority_process,
            other_processes=other_processes,
            duck_to=self.duck_to_spin.value(),
            threshold=self.threshold_spin.value(),
            priority_attack_threshold=self.attack_threshold_spin.value(),
            priority_release_threshold=self.release_threshold_spin.value(),
            attack_frames=self.attack_frames_spin.value(),
            release_frames=self.release_frames_spin.value(),
            min_overlap_frames=self.overlap_frames_spin.value(),
            interval=self.interval_spin.value(),
            step=self.step_spin.value()
        )
        
        # Create and start engine
        self.engine = AudioDuckingEngine(config, self.status_callback)
        
        if self.engine.start():
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.log_message(f"Started audio ducking engine for '{priority_process}'")
            self.save_config()  # Save current config
            
            # Show notification if available
            if self.tray_icon.isVisible():
                self.tray_icon.showMessage("Audio Priority Manager", 
                                         f"Started ducking for {priority_process}",
                                         QSystemTrayIcon.MessageIcon.Information, 3000)
        else:
            QMessageBox.warning(self, "Error", "Failed to start audio ducking engine.\n"
                                              "Please check that the priority process name is correct.")

    def stop_ducking(self):
        """Stop the audio ducking engine"""
        if self.engine:
            self.engine.stop()
            self.engine = None
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_indicator.set_active(False)
        self.status_label.setText("Stopped")
        self.log_message("Stopped audio ducking engine - all volumes restored")
        
        # Show notification if available
        if self.tray_icon.isVisible():
            self.tray_icon.showMessage("Audio Priority Manager", 
                                     "Audio ducking stopped",
                                     QSystemTrayIcon.MessageIcon.Information, 2000)

    def status_callback(self, status: str, message: str, data: dict):
        """Callback for engine status updates"""
        self.status_update.emit(status, message, data)

    def on_status_update(self, status: str, message: str, data: dict):
        """Handle status updates from engine"""
        timestamp = time.strftime("%H:%M:%S")
        
        if status == "started":
            self.status_indicator.set_active(True)
            self.status_label.setText("Running")
            self.log_message(f"🟢 {message}")
        elif status == "stopped":
            self.status_indicator.set_active(False)
            self.status_label.setText("Stopped")
            self.log_message(f"🔴 {message}")
        elif status == "priority_changed":
            if data.get('priority_active'):
                self.log_message(f"🎵 Priority audio activated")
            else:
                self.log_message(f"🔇 Priority audio deactivated")
        else:
            self.log_message(f"[{status.upper()}] {message}")

    def update_display(self):
        """Update display with current engine status"""
        if self.engine and self.engine.running:
            status = self.engine.get_status()
            
            # Update status labels
            self.priority_status_label.setText(
                "Active" if status['priority_active'] else "Inactive"
            )
            self.ducked_sessions_label.setText(str(status['ducked_sessions']))
            self.total_sessions_label.setText(str(status['total_sessions']))
            
            # Status indicator should be green when engine is running
            # regardless of priority active state
            self.status_indicator.set_active(True)
            self.status_label.setText("Running")
            
            # Update progress bar with priority activity level
            try:
                # Get real-time activity level from audio engine
                priority_level = self._get_priority_audio_level()
                self.priority_progress.setValue(int(priority_level * 100))
                
                # Update progress bar color based on activity
                if priority_level > self.threshold_spin.value():
                    self.priority_progress.setStyleSheet("""
                        QProgressBar::chunk {
                            background-color: #4CAF50;
                            border-radius: 2px;
                        }
                    """)
                else:
                    self.priority_progress.setStyleSheet("""
                        QProgressBar::chunk {
                            background-color: #757575;
                            border-radius: 2px;
                        }
                    """)
            except Exception:
                self.priority_progress.setValue(0)
        else:
            # Reset display when not running
            self.priority_status_label.setText("Stopped")
            self.ducked_sessions_label.setText("0")
            self.total_sessions_label.setText("0")
            self.priority_progress.setValue(0)
            self.status_indicator.set_active(False)
            self.status_label.setText("Stopped")

    def log_message(self, message: str):
        """Add message to log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def clear_log(self):
        """Clear the log"""
        self.log_text.clear()

    def save_log(self):
        """Save log to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "audio_priority_log.txt", "Text files (*.txt)"
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Success", f"Log saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save log: {e}")

    def save_config(self):
        """Save current configuration to file"""
        config = {
            'priority_process': self.priority_edit.text(),
            'duck_to': self.duck_to_spin.value(),
            'threshold': self.threshold_spin.value(),
            'priority_attack_threshold': self.attack_threshold_spin.value(),
            'priority_release_threshold': self.release_threshold_spin.value(),
            'attack_frames': self.attack_frames_spin.value(),
            'release_frames': self.release_frames_spin.value(),
            'min_overlap_frames': self.overlap_frames_spin.value(),
            'interval': self.interval_spin.value(),
            'step': self.step_spin.value(),
            'limit_to_specific': self.limit_checkbox.isChecked(),
            'other_processes': [
                self.other_processes_list.item(i).text() 
                for i in range(self.other_processes_list.count())
            ]
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def load_config(self):
        """Load configuration from file"""
        if not os.path.exists(self.config_file):
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Load values
            self.priority_edit.setText(config.get('priority_process', ''))
            self.duck_to_spin.setValue(config.get('duck_to', 0.25))
            self.threshold_spin.setValue(config.get('threshold', 0.02))
            self.attack_threshold_spin.setValue(config.get('priority_attack_threshold', 0.06))
            self.release_threshold_spin.setValue(config.get('priority_release_threshold', 0.02))
            self.attack_frames_spin.setValue(config.get('attack_frames', 3))
            self.release_frames_spin.setValue(config.get('release_frames', 20))
            self.overlap_frames_spin.setValue(config.get('min_overlap_frames', 2))
            self.interval_spin.setValue(config.get('interval', 0.05))
            self.step_spin.setValue(config.get('step', 0.08))
            self.limit_checkbox.setChecked(config.get('limit_to_specific', False))
            
            # Load other processes
            self.other_processes_list.clear()
            for process in config.get('other_processes', []):
                self.other_processes_list.addItem(process)
                
        except Exception as e:
            print(f"Failed to load config: {e}")

    def closeEvent(self, event):
        """Handle close event"""
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_application()

    def quit_application(self):
        """Quit the application"""
        if self.engine:
            self.engine.stop()
        self.save_config()
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running when window is closed
    
    window = AudioPriorityGUI()
    window.show()
    
    sys.exit(app.exec())
