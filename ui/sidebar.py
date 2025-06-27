from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton, QLabel,
    QButtonGroup, QWidget, QToolButton, QSizePolicy
)
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon


class CollapsibleSection(QWidget):
    def __init__(self, title, buttons):
        super().__init__()
        self.toggle_button = QToolButton()
        self.toggle_button.setText(title)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.DownArrow)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.setStyleSheet("""
            QToolButton {
                font-weight: 600;
                font-size: 14px;
                color: #1E1E1E;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: #FFFFFF;
                text-align: left;
            }
            QToolButton:checked {
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }
        """)
        self.toggle_button.clicked.connect(self._toggle_content)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(6, 6, 6, 6)
        self.content_layout.setSpacing(6)

        for btn in buttons:
            self.content_layout.addWidget(btn)

        self.content_widget.setLayout(self.content_layout)
        self.content_widget.setStyleSheet("""
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-top: none;
            border-bottom-left-radius: 8px;
            border-bottom-right-radius: 8px;
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_widget)
        self.setLayout(layout)

    def _toggle_content(self):
        visible = self.toggle_button.isChecked()
        self.content_widget.setVisible(visible)
        self.toggle_button.setArrowType(Qt.DownArrow if visible else Qt.RightArrow)


class SideBar(QFrame):
    def __init__(self, parent=None):
        super(SideBar, self).__init__(parent)
        self.setObjectName("leftBar")
        self.setFixedWidth(200)
        self.setStyleSheet("background-color: #F9FAFB;")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(12)

        # --- Data ---
        self.view_original_btn = self._create_menu_button("Original")
        self.view_enhanced_btn = self._create_menu_button("Enhanced")

        self.view_group = QButtonGroup()
        self.view_group.setExclusive(True)
        self.view_group.addButton(self.view_original_btn, 0)
        self.view_group.addButton(self.view_enhanced_btn, 1)

        self.data_section = CollapsibleSection("Data", [
            self.view_original_btn, self.view_enhanced_btn
        ])
        self.data_section.setVisible(False)
        layout.addWidget(self.data_section)

        # --- Section ---
        self.inline_btn = self._create_menu_button("Inline")
        self.crossline_btn = self._create_menu_button("Crossline")

        self.ic_group = QButtonGroup()
        self.ic_group.setExclusive(True)
        self.ic_group.addButton(self.inline_btn, 0)
        self.ic_group.addButton(self.crossline_btn, 1)

        self.section_section = CollapsibleSection("Section", [
            self.inline_btn, self.crossline_btn
        ])
        self.section_section.setVisible(False)
        layout.addWidget(self.section_section)

        layout.addStretch()
        self.setLayout(layout)

    def _create_menu_button(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setMinimumHeight(36)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: none;
                padding: 6px 12px;
                text-align: left;
                color: #1E1E1E;
                font-size: 13px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
            }
            QPushButton:checked {
                background-color: #04BFAD;
                color: white;
            }
        """)
        return btn

    def show_3d_options(self):
        self.section_section.setVisible(True)

    def hide_3d_options(self):
        self.section_section.setVisible(False)

    def show_view_buttons(self):
        self.data_section.setVisible(True)
        self.data_section.toggle_button.setChecked(True)
        self.data_section._toggle_content()

    def hide_view_buttons(self):
        self.data_section.setVisible(False)
