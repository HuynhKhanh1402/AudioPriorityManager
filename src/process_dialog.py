"""
Process selection dialog with audio detection
"""
import sys
from typing import Optional, List
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                            QGroupBox, QSplitter, QFrame, QScrollArea, QWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QFont, QPolygon
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint

from .process_manager import ProcessManager, ProcessInfo

class AudioIcon(QLabel):
    """Custom audio icon widget"""
    def __init__(self, has_audio: bool = False, audio_level: float = 0.0):
        super().__init__()
        self.has_audio = has_audio
        self.audio_level = audio_level
        self.setFixedSize(24, 24)
        self.update_icon()
    
    def set_audio_info(self, has_audio: bool, audio_level: float = 0.0):
        self.has_audio = has_audio
        self.audio_level = audio_level
        self.update_icon()
    
    def update_icon(self):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.has_audio:
            # Draw speaker icon with volume level
            color = QColor("#4CAF50") if self.audio_level > 0.01 else QColor("#2196F3")
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Speaker base
            painter.drawRect(2, 8, 6, 8)
            # Speaker cone
            polygon = QPolygon([
                QPoint(8, 6), QPoint(14, 2), QPoint(14, 22), QPoint(8, 18)
            ])
            painter.drawPolygon(polygon)
            
            # Volume waves if audio is active
            if self.audio_level > 0.01:
                painter.setPen(color)
                painter.drawArc(16, 6, 6, 4, 0, 180*16)
                if self.audio_level > 0.05:
                    painter.drawArc(18, 4, 6, 8, 0, 180*16)
                if self.audio_level > 0.1:
                    painter.drawArc(20, 2, 6, 12, 0, 180*16)
        else:
            # Draw generic application icon
            painter.setBrush(QBrush(QColor("#757575")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(4, 4, 16, 16)
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawRect(6, 6, 12, 12)
        
        painter.end()
        self.setPixmap(pixmap)

class ProcessListItem(QFrame):
    """Custom list item for process selection"""
    clicked = pyqtSignal(str)
    
    def __init__(self, process_info: ProcessInfo):
        super().__init__()
        self.process_info = process_info
        self.selected = False
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Audio icon
        self.audio_icon = AudioIcon(self.process_info.has_audio, self.process_info.audio_level)
        layout.addWidget(self.audio_icon)
        
        # Process info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Main layout for name and description
        name_desc_layout = QVBoxLayout()
        name_desc_layout.setSpacing(1)
        
        # Process name (bold if has audio)
        name_label = QLabel(self.process_info.name)
        name_font = name_label.font()
        name_font.setBold(True)
        name_font.setPointSize(10)
        name_label.setFont(name_font)
        
        if self.process_info.has_audio:
            name_label.setStyleSheet("color: #4CAF50;")
        else:
            name_label.setStyleSheet("color: #FFFFFF;")
        
        name_desc_layout.addWidget(name_label)
        
        # Description/Title if available (more prominent)
        if self.process_info.description:
            desc_label = QLabel(self.process_info.description)
            desc_font = desc_label.font()
            desc_font.setPointSize(9)
            desc_label.setFont(desc_font)
            desc_label.setStyleSheet("color: #BBBBBB; font-style: italic;")
            desc_label.setWordWrap(True)
            name_desc_layout.addWidget(desc_label)
        
        info_layout.addLayout(name_desc_layout)
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Audio level indicator if has audio
        if self.process_info.has_audio:
            level_label = QLabel(f"{int(self.process_info.audio_level * 100)}%")
            level_label.setStyleSheet("color: #4CAF50; font-size: 10px;")
            layout.addWidget(level_label)
        
        self.setStyleSheet("""
            ProcessListItem {
                border: 1px solid transparent;
                border-radius: 4px;
                background-color: #2a2a2a;
                margin: 1px;
            }
            ProcessListItem:hover {
                border-color: #3daee9;
                background-color: #3a3a3a;
            }
            ProcessListItem QLabel {
                border: none;
                background-color: transparent;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.process_info.exe_name)
        super().mousePressEvent(event)
    
    def set_selected(self, selected: bool):
        self.selected = selected
        if selected:
            self.setStyleSheet("""
                ProcessListItem {
                    border: 2px solid #3daee9;
                    border-radius: 4px;
                    background-color: #4a4a4a;
                    margin: 1px;
                }
                ProcessListItem QLabel {
                    border: none;
                    background-color: transparent;
                }
            """)
        else:
            self.setStyleSheet("""
                ProcessListItem {
                    border: 1px solid transparent;
                    border-radius: 4px;
                    background-color: #2a2a2a;
                    margin: 1px;
                }
                ProcessListItem:hover {
                    border-color: #3daee9;
                    background-color: #3a3a3a;
                }
                ProcessListItem QLabel {
                    border: none;
                    background-color: transparent;
                }
            """)

class ProcessSelectionDialog(QDialog):
    """Dialog for selecting a process"""
    
    def __init__(self, parent=None, current_process: str = ""):
        super().__init__(parent)
        self.process_manager = ProcessManager()
        self.selected_process = current_process
        self.process_items = {}
        
        self.setWindowTitle("Select Priority Process")
        self.setModal(True)
        self.resize(600, 500)
        self.setStyleSheet(self._get_dark_theme())
        
        self.setup_ui()
        self.refresh_processes()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_processes)
        self.refresh_timer.start(2000)  # Refresh every 2 seconds
    
    def _get_dark_theme(self) -> str:
        return """
        QDialog {
            background-color: #1e1e1e;
            color: #ffffff;
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
        QLineEdit {
            border: 2px solid #555555;
            border-radius: 4px;
            padding: 5px;
            background-color: #404040;
            color: #ffffff;
        }
        QLineEdit:focus {
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
        QScrollArea {
            border: 2px solid #555555;
            border-radius: 4px;
            background-color: #404040;
        }
        """
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Select Priority Process")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #3daee9; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # Search box
        search_group = QGroupBox("Search")
        search_layout = QVBoxLayout(search_group)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search processes by name or description...")
        self.search_edit.textChanged.connect(self.filter_processes)
        search_layout.addWidget(self.search_edit)
        
        layout.addWidget(search_group)
        
        # Splitter for two columns
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Audio processes group
        audio_group = QGroupBox("🔊 Processes with Audio")
        audio_layout = QVBoxLayout(audio_group)
        
        self.audio_scroll = QScrollArea()
        self.audio_widget = QWidget()
        self.audio_list_layout = QVBoxLayout(self.audio_widget)
        self.audio_list_layout.addStretch()
        self.audio_scroll.setWidget(self.audio_widget)
        self.audio_scroll.setWidgetResizable(True)
        self.audio_scroll.setMinimumHeight(200)
        
        audio_layout.addWidget(self.audio_scroll)
        splitter.addWidget(audio_group)
        
        # All processes group  
        all_group = QGroupBox("📱 All Processes")
        all_layout = QVBoxLayout(all_group)
        
        self.all_scroll = QScrollArea()
        self.all_widget = QWidget()
        self.all_list_layout = QVBoxLayout(self.all_widget)
        self.all_list_layout.addStretch()
        self.all_scroll.setWidget(self.all_widget)
        self.all_scroll.setWidgetResizable(True)
        
        all_layout.addWidget(self.all_scroll)
        splitter.addWidget(all_group)
        
        layout.addWidget(splitter)
        
        # Manual input
        manual_group = QGroupBox("✏️ Manual Input")
        manual_layout = QHBoxLayout(manual_group)
        
        manual_layout.addWidget(QLabel("Process name:"))
        self.manual_edit = QLineEdit()
        self.manual_edit.setPlaceholderText("e.g., vlc.exe")
        self.manual_edit.setText(self.selected_process)
        self.manual_edit.textChanged.connect(self.on_manual_input)
        manual_layout.addWidget(self.manual_edit)
        
        layout.addWidget(manual_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.clicked.connect(self.refresh_processes)
        button_layout.addWidget(refresh_button)
        
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)
        
        layout.addWidget(QFrame())  # Spacer
        layout.addLayout(button_layout)
    
    def refresh_processes(self):
        """Refresh the process list"""
        processes = self.process_manager.get_running_processes()
        
        # Clear existing items
        self.clear_layouts()
        self.process_items.clear()
        
        # Separate audio and non-audio processes
        audio_processes = [p for p in processes if p.has_audio]
        other_processes = [p for p in processes if not p.has_audio]
        
        # Add audio processes
        for process in audio_processes:
            item = ProcessListItem(process)
            item.clicked.connect(self.on_process_selected)
            self.audio_list_layout.insertWidget(self.audio_list_layout.count() - 1, item)
            self.process_items[process.exe_name] = item
        
        # Add other processes (show more processes, not just common ones)
        common_processes = self.process_manager.get_common_audio_processes()
        displayed_count = 0
        max_display = 50  # Limit to prevent too many items
        
        for process in other_processes:
            if displayed_count >= max_display:
                break
                
            # Show if it's a common audio process, currently selected, or has recognizable name
            should_show = (
                process.exe_name in common_processes or 
                process.exe_name == self.selected_process.lower() or
                any(keyword in process.exe_name for keyword in [
                    'chrome', 'firefox', 'edge', 'opera', 'browser',
                    'discord', 'teams', 'zoom', 'skype', 'telegram',
                    'steam', 'epic', 'game', 'launcher',
                    'vlc', 'media', 'player', 'music', 'audio',
                    'obs', 'stream', 'record',
                    'notepad', 'code', 'studio', 'editor'
                ])
            )
            
            if should_show:
                item = ProcessListItem(process)
                item.clicked.connect(self.on_process_selected)
                self.all_list_layout.insertWidget(self.all_list_layout.count() - 1, item)
                self.process_items[process.exe_name] = item
                displayed_count += 1
        
        # Update selection
        if self.selected_process:
            self.update_selection()
    
    def clear_layouts(self):
        """Clear all process items from layouts"""
        # Clear audio layout
        while self.audio_list_layout.count() > 1:  # Keep the stretch
            item = self.audio_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear all layout
        while self.all_list_layout.count() > 1:  # Keep the stretch
            item = self.all_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def on_process_selected(self, process_name: str):
        """Handle process selection"""
        self.selected_process = process_name
        self.manual_edit.setText(process_name)
        self.update_selection()
    
    def on_manual_input(self, text: str):
        """Handle manual input"""
        self.selected_process = text
        self.update_selection()
    
    def update_selection(self):
        """Update visual selection"""
        for process_name, item in self.process_items.items():
            item.set_selected(process_name == self.selected_process.lower())
    
    def filter_processes(self, text: str):
        """Filter processes based on search text"""
        text = text.lower()
        for process_name, item in self.process_items.items():
            # Search in process name, exe name, and description
            should_show = (
                text in process_name or 
                text in item.process_info.name.lower() or
                (item.process_info.description and text in item.process_info.description.lower())
            )
            item.setVisible(should_show)
    
    def get_selected_process(self) -> str:
        """Get the selected process name"""
        return self.selected_process.strip()
    
    def closeEvent(self, event):
        """Handle dialog close"""
        self.refresh_timer.stop()
        super().closeEvent(event)
