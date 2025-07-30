from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton,
    QButtonGroup, QWidget, QToolButton, QSpinBox
)
from PyQt5.QtCore import Qt


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


class SideBar3D(QFrame):
    def __init__(self, parent=None):
        super(SideBar3D, self).__init__(parent)

        self.setObjectName("leftBar")
        self.setFixedWidth(200)
        self.setStyleSheet("background-color: #F9FAFB;")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(12)

        self.spinboxes = {}  # Guarda spinboxes por sección
        self.axis_buttons = []  # Guarda (botón, sección, tipo)
        self.global_button_group = QButtonGroup()
        self.global_button_group.setExclusive(True)
        self.button_ids = {}

        button_id_counter = 0

        for section in ["Original", "Enhanced", "Difference"]:
            inline_btn = self._create_menu_button("Inline")
            crossline_btn = self._create_menu_button("Crossline")
            zslice_btn = self._create_menu_button("Z-Slice")
            iline_spin = self._create_spinbox()
            xline_spin = self._create_spinbox()

            self.global_button_group.addButton(inline_btn, button_id_counter)
            self.button_ids[inline_btn] = (section, "inline")
            button_id_counter += 1

            self.global_button_group.addButton(crossline_btn, button_id_counter)
            self.button_ids[crossline_btn] = (section, "crossline")
            button_id_counter += 1

            self.global_button_group.addButton(zslice_btn, button_id_counter)
            self.button_ids[zslice_btn] = (section, "zslice")
            button_id_counter += 1

            if section == "Original":
                inline_btn.setChecked(True)

            self.spinboxes[section] = (iline_spin, xline_spin)

            self.axis_buttons.append((inline_btn, section, "inline"))
            self.axis_buttons.append((crossline_btn, section, "crossline"))
            self.axis_buttons.append((zslice_btn, section, "zslice"))

            section_widget = CollapsibleSection(section, [
                inline_btn, iline_spin, crossline_btn, xline_spin, zslice_btn
            ])
            section_widget.setVisible(section == "Original")
            setattr(self, f"section_{section.lower()}", section_widget)
            layout.addWidget(section_widget)

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

    def _create_spinbox(self):
        spin = QSpinBox()
        spin.setMinimum(0)
        spin.setMaximum(0)
        spin.setSingleStep(1)
        spin.setStyleSheet("""
            QSpinBox {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
                padding: 4px;
                font-size: 13px;
            }
        """)
        return spin

    def set_ixline_limits(self, iline_min, iline_max, xline_min, xline_max):
        for iline_spin, xline_spin in self.spinboxes.values():
            iline_spin.setRange(iline_min, iline_max)
            xline_spin.setRange(xline_min, xline_max)

    def show_enhanced_and_difference(self):
        self.section_enhanced.setVisible(True)
        self.section_difference.setVisible(True)

    def get_active_section(self):
        checked_btn = self.global_button_group.checkedButton()
        if checked_btn:
            section, axis = self.button_ids[checked_btn]
            spinbox = self.spinboxes[section][0] if axis == "inline" else self.spinboxes[section][1]
            return section, axis, spinbox.value()
        return None, None, None

    def connect_spinboxes(self, callback):
        for iline_spin, xline_spin in self.spinboxes.values():
            iline_spin.valueChanged.connect(callback)
            xline_spin.valueChanged.connect(callback)

    def connect_axis_buttons(self, callback):
        for button, section, axis in self.axis_buttons:
            def handler(checked=False, s=section, a=axis):
                spinbox = self.spinboxes[s][0] if a == "inline" else self.spinboxes[s][1]
                callback(s, a, spinbox.value())
            button.clicked.connect(handler)
