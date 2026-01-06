"""
Zonify Modern UI Stylesheet

Professional, modern styling for the entire Zonify plugin.
Apply this in main_dialog.py __init__() method with self.setStyleSheet()

Author: Dragos Gontariu
License: GPL-3.0
"""

ZONIFY_STYLESHEET = """
/* ========================================
   ZONIFY MODERN UI STYLESHEET
   ======================================== */

/* === MAIN DIALOG === */
QDialog {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #FAFAFA,
        stop:1 #F5F5F5
    );
}

/* === HEADERS & TITLES === */
QLabel#titleLabel {
    color: #202124;
    font-size: 18pt;
    font-weight: bold;
    padding: 8px 0px;
}

QLabel#subtitleLabel {
    color: #5F6368;
    font-size: 11pt;
    padding: 4px 0px 12px 0px;
}

/* === TAB WIDGET === */
QTabWidget::pane {
    border: 1px solid #E0E0E0;
    background: white;
    border-radius: 6px;
    padding: 16px;  /* ← Mai mult padding interior */
    margin-top: -1px;  /* ← Seamless cu tabs */
}

QTabBar::tab {
    background: #F8F9FA;
    color: #5F6368;
    padding: 9px 18px;
    min-width: 130px;
    max-width: 180px;
    margin-right: 2px;
    border: 1px solid #E0E0E0;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
    font-size: 10pt;
}

QTabBar::tab:selected {
    background: white;
    color: #2196F3;
    border-bottom: 3px solid #2196F3;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background: #F0F0F0;
    color: #202124;
}

/* === GROUP BOXES (Cards) === */
QGroupBox {
    background-color: white;
    border: 1px solid #E0E0E0;
    border-radius: 6px;  /* ← Mai puțin rotunjit */
    margin-top: 8px;     /* ← Mai puțin spațiu */
    padding: 12px 16px 16px 16px;  /* ← Padding mai mic */
    font-weight: 600;
    font-size: 10pt;     /* ← Font mai mic */
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;    /* ← Mai compact */
    margin-left: 8px;
    color: #202124;
    background-color: white;
}

/* Compact style for Quick Map widget groups */
QWidget#quickMapWidget QGroupBox {
    padding: 8px 12px 12px 12px;  /* ← Mai compact */
    margin-top: 6px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    color: #202124;
    background-color: white;
    border-radius: 4px;
}

/* === BUTTONS === */
QPushButton {
    background-color: white;
    color: #5F6368;
    border: 1px solid #DADCE0;
    border-radius: 4px;      /* ← Mai puțin rotunjit */
    padding: 6px 12px;       /* ← Mai slim */
    font-size: 9pt;
    font-weight: 500;
    min-height: 16px;        /* ← Mai mic */
}

QPushButton:hover {
    background-color: #F8F9FA;
    border-color: #9AA0A6;
}

QPushButton:pressed {
    background-color: #F0F0F0;
}

QPushButton:disabled {
    background-color: #F5F5F5;
    color: #BDBDBD;
    border-color: #E0E0E0;
}

/* === PRIMARY BUTTON (Run) === */
QPushButton#runButton {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #4CAF50,
        stop:1 #45A049
    );
    color: white;
    border: none;
    padding: 12px 32px;
    font-size: 11pt;
    font-weight: bold;
    border-radius: 8px;
}

QPushButton#runButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #45A049,
        stop:1 #3D8B40
    );
}

QPushButton#runButton:pressed {
    background: #3D8B40;
}

/* === SECONDARY BUTTONS === */
QPushButton#closeButton {
    background-color: white;
    color: #5F6368;
    border: 1px solid #DADCE0;
    padding: 12px 24px;
    font-size: 10pt;
    border-radius: 8px;
}

QPushButton#closeButton:hover {
    background-color: #F8F9FA;
}

/* === INPUT FIELDS === */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: white;
    border: 1px solid #DADCE0;
    border-radius: 5px;  /* ← Mai puțin rotunjit */
    padding: 6px 10px;   /* ← Mai compact */
    font-size: 9pt;      /* ← Font mai mic */
    color: #202124;
    min-height: 22px;    /* ← Înălțime fixă */
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #2196F3;
    background-color: white;
}

QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #F5F5F5;
    color: #9AA0A6;
}

/* === SPIN BOX ARROWS === */
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #DADCE0;
    background: #F8F9FA;
    border-top-right-radius: 6px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background: #E3F2FD;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #5F6368;
    width: 0;
    height: 0;
}

QSpinBox::up-arrow:hover, QDoubleSpinBox::up-arrow:hover {
    border-bottom-color: #2196F3;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border-left: 1px solid #DADCE0;
    background: #F8F9FA;
    border-bottom-right-radius: 6px;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: #E3F2FD;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #5F6368;
    width: 0;
    height: 0;
}

QSpinBox::down-arrow:hover, QDoubleSpinBox::down-arrow:hover {
    border-top-color: #2196F3;
}

/* === COMBO BOXES === */
QComboBox {
    background-color: white;
    border: 1px solid #DADCE0;
    border-radius: 5px;
    padding: 6px 10px;   /* ← Mai compact */
    font-size: 9pt;      /* ← Font mai mic */
    color: #202124;
    min-height: 22px;    /* ← Înălțime fixă */
}

QComboBox QAbstractItemView::item {
    min-height: 30px;  # ← Fiecare item mai înalt
    padding: 4px;
}

/* Quick Map specific - larger color ramp preview */
QComboBox#colorRampCombo {
    min-height: 32px;
    padding: 4px 4px 4px 8px;  /* ← Padding mai mic pe dreapta */
}

QComboBox#colorRampCombo::drop-down {
    width: 24px;  /* ← Săgeata mai îngustă */
    border: none;
}

QComboBox#colorRampCombo QAbstractItemView {
    icon-size: 200px 24px;
    padding: 4px;  /* ← Padding mai mic în dropdown */
}

QComboBox#colorRampCombo QAbstractItemView::item {
    min-height: 28px;  /* ← Mai mic de la 32px */
    padding: 2px 8px;  /* ← Padding mai mic vertical */
    margin: 0px;       /* ← Fără margin */
}

QComboBox#colorRampCombo QAbstractItemView::item:selected {
    background-color: #E3F2FD;  /* ← Highlight selection */
}

QComboBox:hover {
    border-color: #9AA0A6;
}

QComboBox:focus {
    border: 2px solid #2196F3;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;      # ← Mai mare
    border-right: 5px solid transparent;     # ← Mai mare
    border-top: 7px solid #202124;           # ← Mai mare și mai întunecat
    width: 0px;
    height: 0px;
    margin-right: 8px;
}

QComboBox:hover::down-arrow {
    border-top-color: #2196F3;  # ← Blue on hover
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    selection-background-color: #E3F2FD;
    selection-color: #1976D2;
    padding: 4px;
}

/* === CHECKBOXES - MODERN DESIGN === */
QCheckBox {
    spacing: 8px;
    color: #202124;
    font-size: 10pt;
    font-weight: 500;
    padding: 4px;
    cursor: help;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #9E9E9E;
    border-radius: 4px;
    background-color: white;
}

/* Hover effect - glow */
QCheckBox:hover {
    background-color: rgba(33, 150, 243, 0.05);
    border-radius: 6px;
}

QCheckBox::indicator:hover {
    border-color: #4CAF50;
    border-width: 2px;
    background-color: rgba(76, 175, 80, 0.08);
}

/* Checked state - gradient */
QCheckBox::indicator:checked {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #4CAF50,
        stop:1 #45A049
    );
    border: 2px solid #4CAF50;
}

QCheckBox::indicator:checked:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #45A049,
        stop:1 #3D8B40
    );
    border-color: #3D8B40;
}

/* Disabled state */
QCheckBox::indicator:disabled {
    border-color: #E0E0E0;
    background-color: #F5F5F5;
}

QCheckBox:disabled {
    color: #BDBDBD;
}

/* === RADIO BUTTONS === */
QRadioButton {
    spacing: 8px;
    color: #5F6368;
    font-size: 10pt;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #DADCE0;
    border-radius: 9px;
    background: white;
}

QRadioButton::indicator:hover {
    border-color: #2196F3;
}

QRadioButton::indicator:checked {
    background-color: white;
    border: 5px solid #2196F3;  /* ← Border gros colorat */
}

QRadioButton::indicator:checked:hover {
    border-color: #1976D2;
}

QRadioButton::indicator:checked:hover {
    background-color: #1976D2;
    border: 3px solid #0D47A1;
}

/* === SLIDERS === */
QSlider::groove:horizontal {
    height: 6px;
    background: #E0E0E0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #2196F3;
    border: 2px solid white;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #1976D2;
}

/* === PROGRESS BARS === */
QProgressBar {
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    text-align: center;
    background-color: #F5F5F5;
    height: 24px;
    font-size: 9pt;
    color: #5F6368;
}

QProgressBar::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #4CAF50,
        stop:1 #66BB6A
    );
    border-radius: 5px;
}

/* === SCROLL AREAS === */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background: #F5F5F5;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #BDBDBD;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #9E9E9E;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #F5F5F5;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background: #BDBDBD;
    border-radius: 6px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #9E9E9E;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* === LIST WIDGETS === */
QListWidget {
    background-color: white;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 4px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
}

QListWidget::item:hover {
    background-color: #F5F5F5;
}

QListWidget::item:selected {
    background-color: #E3F2FD;
    color: #1976D2;
}

/* === TABLE WIDGETS === */
QTableWidget {
    background-color: white;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    gridline-color: #F0F0F0;
}

QTableWidget::item {
    padding: 6px;
}

QTableWidget::item:selected {
    background-color: #E3F2FD;
    color: #1976D2;
}

QHeaderView::section {
    background-color: #F8F9FA;
    color: #5F6368;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #E0E0E0;
    font-weight: 600;
}

/* === TOOLTIPS === */
QToolTip {
    background-color: #2C2C2C;
    color: #FFFFFF;
    border: 2px solid #4CAF50;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 10pt;
    font-weight: 500;
}

/* === LABELS === */
QLabel {
    color: #5F6368;
    font-size: 9pt;
}

QLabel[class="warning"] {
    color: #F57C00;
    font-style: italic;
}

QLabel[class="error"] {
    color: #D32F2F;
    font-weight: 600;
}

QLabel[class="success"] {
    color: #388E3C;
    font-weight: 600;
}

/* === SPECIAL WIDGETS === */
/* Tool Button (for collapsible sections) */
QToolButton {
    border: none;
    background: transparent;
    color: #202124;
    font-weight: bold;
    font-size: 11pt;
    padding: 8px;
    text-align: left;
}

QToolButton:hover {
    background-color: #F5F5F5;
    border-radius: 4px;
}

/* === STATUS BAR STYLING === */
QLabel#statusLabel {
    color: #4CAF50;
    font-weight: 600;
    font-size: 10pt;
    padding: 4px 8px;
}

QLabel#statusLabel[status="error"] {
    color: #D32F2F;
}

QLabel#statusLabel[status="warning"] {
    color: #F57C00;
}

/* === HELP TEXT === */
QLabel[class="help-text"] {
    color: #9AA0A6;
    font-size: 9pt;
    font-style: italic;
    padding: 4px 0px;
}

/* === CARD STYLE (for grouped content) === */
QWidget[class="card"] {
    background-color: white;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 16px;
}
"""
# === STATISTICS CHECKBOXES - PILL STYLE (EXTRA COMPACT) ===
STATS_CHECKBOX_STYLE = """
QCheckBox {
    spacing: 4px;
    color: #202124;
    font-size: 8.5pt;
    font-weight: 500;
    padding: 4px 10px;
    background-color: white;
    border: 1.5px solid #E0E0E0;
    border-radius: 12px;
    min-width: 50px;
    max-height: 24px;
}

QCheckBox:hover {
    background-color: #F8F9FA;
    border-color: #4CAF50;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1.5px solid #9E9E9E;
    border-radius: 7px;
    background-color: white;
}

QCheckBox::indicator:checked {
    background-color: #4CAF50;
    border-color: #4CAF50;
}

QCheckBox:checked {
    background-color: #E8F5E9;
    border-color: #4CAF50;
    color: #2E7D32;
    font-weight: 600;
}
"""

# Warning style for Coverage % (EXTRA COMPACT)
STATS_CHECKBOX_WARNING_STYLE = """
QCheckBox {
    spacing: 4px;
    color: #202124;
    font-size: 8.5pt;
    font-weight: 500;
    padding: 4px 10px;
    background-color: #FFF3CD;
    border: 1.5px solid #FFC107;
    border-radius: 12px;
    min-width: 90px;
    max-height: 24px;
}

QCheckBox:hover {
    background-color: #FFE082;
    border-color: #FF9800;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1.5px solid #F57C00;
    border-radius: 7px;
    background-color: white;
}

QCheckBox::indicator:checked {
    background-color: #FF9800;
    border-color: #FF9800;
}

QCheckBox:checked {
    background-color: #FFE082;
    border-color: #F57C00;
    color: #E65100;
    font-weight: 600;
}
"""