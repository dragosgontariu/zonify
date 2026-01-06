"""
Zonify Main Dialog - Full Implementation

Complete main dialog with all UI controls:
- Polygon layer selection
- Multiple raster selection
- Statistics selection
- Output configuration
- Resource management
- Run button

Author: Dragos Gontariu
License: GPL-3.0
"""

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QCheckBox, QRadioButton, QLineEdit, QSpinBox,
    QComboBox, QFileDialog, QMessageBox, QTabWidget, QWidget,
    QGridLayout, QSlider, QProgressBar
)
from qgis.PyQt.QtCore import (
    Qt, 
    pyqtSignal, 
    QSettings,
    QTimer  
)
from qgis.PyQt.QtGui import QFont, QPixmap
from qgis.core import QgsProject, QgsVectorLayer, QgsMapLayerProxyModel
from qgis.gui import QgsMapLayerComboBox

from .widgets.raster_list_widget import RasterListWidget
from .widgets.score_creator_widget import ScoreCreatorWidget
from .widgets.area_classifier_widget import AreaClassifierWidget
from .widgets.area_highlighter_widget import AreaHighlighterWidget
from .widgets.rule_tagger_widget import RuleTaggerWidget
from .widgets.time_series_widget import TimeSeriesWidget            
from .widgets.quick_map_widget import QuickMapWidget
from .zonify_stylesheet import ZONIFY_STYLESHEET, STATS_CHECKBOX_STYLE, STATS_CHECKBOX_WARNING_STYLE  # ← Modern UI styling
import os
import psutil
from ..utils.logger import Logger

class ZonifyDialog(QDialog):
    """
    Main dialog window for Zonify plugin.
    
    Provides complete UI for:
    - Input selection (polygons, rasters)
    - Statistics configuration
    - Output options
    - Resource management
    - Processing control
    """
    
    # Signal emitted when processing should start
    runProcessing = pyqtSignal(dict)
    
    def __init__(self, iface, parent=None):
        """
        Constructor.
        
        Args:
            iface: QGIS interface instance
            parent: Parent widget
        """
        super(ZonifyDialog, self).__init__(parent)
        
        self.iface = iface
        self.processing_thread = None  
        
        # Initialize logger FIRST
        self.logger = Logger('ZonifyDialog')
        self.logger.info('Initializing Zonify dialog')
        
        # Set window properties
        self.setWindowTitle('Zonify - Advanced Zonal Statistics')
        
        # Apply modern stylesheet
        self.setStyleSheet(ZONIFY_STYLESHEET)
            
        # Apply global tooltip style - SIMPLIFIED (Qt compatible)
        from qgis.PyQt.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            tooltip_style = """
                QToolTip {
                    background-color: #1E1E1E;
                    color: #FFFFFF;
                    border-left: 3px solid #4CAF50;
                    border-radius: 4px;
                    padding: 6px 10px;
                    font-size: 9pt;
                    font-weight: 500;
                }
            """
            app.setStyleSheet(app.styleSheet() + tooltip_style)
        
        # Setup UI
        self._setup_ui()
        # Connect coverage warning
        self.stat_coverage.toggled.connect(self._on_coverage_toggled)
        # Connect signals
        self._connect_signals()

        # Initialize with default values
        self._load_defaults()

        
        self.setMinimumSize(850, 580)

        self.logger.info('Zonify dialog initialized successfully')

    def showEvent(self, event):
        """
        Override showEvent pentru a forța dimensiunea corectă la prima afișare.
        """
        super().showEvent(event)
        
        
        if not hasattr(self, '_initial_resize_done'):
            self._initial_resize_done = True
            
            
            QTimer.singleShot(0, lambda: self.resize(920, 620))
            QTimer.singleShot(50, lambda: self.resize(920, 620))
            
            
            QTimer.singleShot(100, self._center_dialog)

    def _center_dialog(self):
        """Centrează dialogul pe ecran, mai aproape de margine superioară."""
        from qgis.PyQt.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        
        
        x = screen.x() + (screen.width() - self.width()) // 2
        
        
        y = screen.y() + int(screen.height() * 0.02)  # 2% from top
        
        self.move(max(0, x), max(0, y))

    def _on_coverage_toggled(self, checked):
        """Show warning when coverage is enabled."""
        if checked:
            from qgis.PyQt.QtWidgets import QMessageBox
            
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle('Performance Warning')
            msg.setText('<b>Geometric Coverage is SLOW</b>')
            msg.setInformativeText(
                'Coverage calculation uses pixel-by-pixel geometric intersection, '
                'which is <b>20-50× slower</b> than other statistics.<br><br>'
                '<b>Expected processing speed:</b><br>'
                '• <b>With coverage:</b> ~10-30 polygons/second<br>'
                '• <b>Without coverage:</b> ~200-400 polygons/second<br><br>'
                '<b>Estimated time for your dataset:</b><br>'
                '• 1,000 features: ~2-5 minutes (with) vs ~5-10 seconds (without)<br>'
                '• 10,000 features: ~10-30 minutes (with) vs ~30-60 seconds (without)<br><br>'
                'Do you want to enable coverage calculation?'
            )
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            
            result = msg.exec_()
            
            if result == QMessageBox.No:
                # Uncheck if user says no (use blockSignals to avoid recursion)
                self.stat_coverage.blockSignals(True)
                self.stat_coverage.setChecked(False)
                self.stat_coverage.blockSignals(False)    
    
    def set_available_features(self, dependency_report):
        """
        Disable export options based on available packages.
        
        Args:
            dependency_report (dict): Report from DependencyChecker
        """
        available_features = dependency_report.get('available_features', {})
        
        # Disable PDF export if reportlab not available
        if 'reportlab' not in available_features:
            self.export_pdf.setEnabled(False)
            self.export_pdf.setToolTip('PDF export requires reportlab package (not installed)')
        
        # Disable HTML export if jinja2 not available
        if 'jinja2' not in available_features:
            self.export_html.setEnabled(False)
            self.export_html.setToolTip('HTML export requires jinja2 package (not installed)')
        
        # CSV is always available (uses built-in csv module)
        # JSON is always available (uses built-in json module)
        
        self.logger.info(f'Available export features: {list(available_features.keys())}')    
        
    def _setup_ui(self):
        """Setup the complete user interface."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)  # ← Margins mai mici
        main_layout.setSpacing(12)  # ← Spacing mai mic între elemente
        # === HEADER WITH LOGO ===
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        
        # Logo
        logo_label = QLabel()

        # Try to load plugin icon
        plugin_dir = os.path.dirname(os.path.dirname(__file__))
        icon_path = os.path.join(plugin_dir, 'icon.png')

        if os.path.exists(icon_path):
            logo_pixmap = QPixmap(icon_path)
            if not logo_pixmap.isNull():
                scaled_pixmap = logo_pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
            else:
                # Fallback to emoji if loading fails
                logo_label.setText('🗺️')
                logo_label.setStyleSheet('font-size: 36pt;')
        else:
            # Fallback to emoji if file doesn't exist
            logo_label.setText('🗺️')
            logo_label.setStyleSheet('font-size: 36pt;')

        header_layout.addWidget(logo_label)
        if not logo_pixmap.isNull():
            scaled_pixmap = logo_pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText('🗺️')
            logo_label.setStyleSheet('font-size: 36pt;')
        header_layout.addWidget(logo_label)
        
        # Spacing
        header_layout.addSpacing(12)
        
        # Title text
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        # Title
        title = QLabel('Zonify - Advanced Zonal Statistics')
        title.setObjectName('titleLabel')  # For styling
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title_container.addWidget(title)
        
        # Subtitle
        subtitle = QLabel('Professional batch zonal statistics processor')
        subtitle.setObjectName('subtitleLabel')  # For styling
        subtitle.setAlignment(Qt.AlignLeft)
        title_container.addWidget(subtitle)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # Tab widget for organized UI
        self.tabs = QTabWidget()
        
        # Tab 1: Input & Statistics
        self.tabs.addTab(self._create_input_tab(), '📊 Input_Statistics')
        
        # Tab 2: Output & Export
        self.tabs.addTab(self._create_output_tab(), '📁 Output_Export')
        
        # Tab 3: Performance
        self.tabs.addTab(self._create_performance_tab(), '⚡ Performance')
        
        # Tab 4: Advanced (NEW!)
        self.tabs.addTab(self._create_advanced_tab(), '🔬 Advanced')
        # Tab 5: Quick Map (NEW!)
        self.tabs.addTab(self._create_quick_map_tab(), '🗺️ Quick Map')
        main_layout.addWidget(self.tabs)
        
        # Info about Advanced tab (ABOVE buttons)
        advanced_info = QLabel(
            '<div style="text-align: center; padding: 10px; color: gray;">'
            '<i>💡 For advanced analysis (scores, classification, highlighting, tagging), '
            'use the widgets in the <b>Advanced</b> tab.</i>'
            '</div>'
        )
        advanced_info.setWordWrap(True)
        advanced_info.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(advanced_info)
        
        # Bottom buttons
        buttons_layout = QHBoxLayout()
        
        # Info label
        self.info_label = QLabel('Ready to process')
        self.info_label.setObjectName('statusLabel')  # For styling
        buttons_layout.addWidget(self.info_label)
        
        buttons_layout.addStretch()
        
        # Run button
        self.run_btn = QPushButton('⚡ Run Standard Processing')
        self.run_btn.setObjectName('runButton')  # For special styling
        self.run_btn.setMinimumWidth(180)
        self.run_btn.clicked.connect(self._on_run)
        buttons_layout.addWidget(self.run_btn)
        
        # Close button
        self.close_btn = QPushButton('Close')
        self.close_btn.setObjectName('closeButton')  # For styling
        self.close_btn.setMinimumWidth(100)
        self.close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
    
    def _create_input_tab(self):
        """Create the Input & Statistics tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # === INPUT SECTION ===
        input_group = QGroupBox('Input Data')
        input_layout = QVBoxLayout()
        
        # Polygon layer selection
        poly_layout = QHBoxLayout()
        poly_layout.addWidget(QLabel('Polygon Layer:'))
        
        self.polygon_combo = QgsMapLayerComboBox()
        self.polygon_combo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        poly_layout.addWidget(self.polygon_combo, 1)
        
        input_layout.addLayout(poly_layout)
        
        # Raster selection
        input_layout.addWidget(QLabel('Rasters:'))
        self.raster_widget = RasterListWidget()
        input_layout.addWidget(self.raster_widget)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # === STATISTICS SECTION ===
        stats_group = QGroupBox('Statistics to Calculate')
        stats_group.setStyleSheet("""
            QCheckBox {
                spacing: 6px;
                color: #202124;
                font-size: 9pt;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #9E9E9E;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #4CAF50;
                border-width: 2px;
                background-color: #E8F5E9;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 2px solid #4CAF50;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #45A049;
                border-color: #45A049;
            }
        """)
        
        stats_layout = QGridLayout()
        stats_layout.setVerticalSpacing(5)      # Spacing vertical mai mic (default e ~11)
        stats_layout.setHorizontalSpacing(10)   # Spacing orizontal
        stats_layout.setContentsMargins(8, 5, 8, 5)  # Margini mai mici
        # Basic statistics
        stats_layout.addWidget(QLabel('<b>Basic:</b>'), 0, 0)
        
        self.stat_mean = QCheckBox('Mean')
        self.stat_mean.setChecked(True)
        self.stat_mean.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_mean.setToolTip('Calculate the average value of pixels within each zone')
        stats_layout.addWidget(self.stat_mean, 0, 1)
        
        self.stat_sum = QCheckBox('Sum')
        self.stat_sum.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_sum.setToolTip('Calculate the total sum of pixel values in each zone')
        stats_layout.addWidget(self.stat_sum, 0, 2)
        
        self.stat_min = QCheckBox('Min')
        self.stat_min.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_min.setToolTip('Find the minimum pixel value in each zone')
        stats_layout.addWidget(self.stat_min, 0, 3)
        
        self.stat_max = QCheckBox('Max')
        self.stat_max.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_max.setToolTip('Find the maximum pixel value in each zone')
        stats_layout.addWidget(self.stat_max, 0, 4)
        
        self.stat_coverage = QCheckBox('Coverage % ⚠️')
        self.stat_coverage.setChecked(False)  # Nu mai e bifat implicit
        self.stat_coverage.setStyleSheet(STATS_CHECKBOX_WARNING_STYLE)
        self.stat_coverage.setToolTip(
            '<b>Geometric Coverage Calculation</b><br><br>'
            '✓ Calculates precise pixel-by-pixel intersection area<br>'
            '✓ 100% accurate geometric coverage<br><br>'
            '<b>⚠️ WARNING:</b> This is <b>20-50× slower</b> than other statistics!<br>'
            'Expected speed: ~10-30 polygons/second<br><br>'
            '<i>For large datasets (>1000 features), consider running without coverage first.</i>'
        )
        stats_layout.addWidget(self.stat_coverage, 0, 5)    

        self.stat_median = QCheckBox('Median')
        self.stat_median.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_median.setToolTip('Calculate the middle value (50th percentile) in each zone')
        stats_layout.addWidget(self.stat_median, 1, 1)
        
        self.stat_mode = QCheckBox('Majority')
        self.stat_mode.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_mode.setToolTip('Find the most frequently occurring pixel value in each zone')
        stats_layout.addWidget(self.stat_mode, 1, 2)
        
        self.stat_count = QCheckBox('Count')
        self.stat_count.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_count.setToolTip('Count the number of pixels in each zone')
        stats_layout.addWidget(self.stat_count, 1, 3)

        self.stat_minority = QCheckBox('Minority')
        self.stat_minority.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_minority.setToolTip('Find the least frequently occurring pixel value in each zone')
        stats_layout.addWidget(self.stat_minority, 1, 4)

        self.stat_variety = QCheckBox('Variety')
        self.stat_variety.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_variety.setToolTip('Count the number of unique pixel values in each zone')
        stats_layout.addWidget(self.stat_variety, 2, 1)
        
        self.stat_range = QCheckBox('Range')
        self.stat_range.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_range.setToolTip('Calculate the difference between max and min values')
        stats_layout.addWidget(self.stat_range, 1, 5)
        
        # Advanced statistics
        stats_layout.addWidget(QLabel('<b>Advanced:</b>'), 3, 0)
        
        self.stat_stddev = QCheckBox('Std Dev')
        self.stat_stddev.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_stddev.setToolTip('Calculate standard deviation - measures variability')
        stats_layout.addWidget(self.stat_stddev, 3, 1)
        
        self.stat_variance = QCheckBox('Variance')
        self.stat_variance.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_variance.setToolTip('Calculate variance - square of standard deviation')
        stats_layout.addWidget(self.stat_variance, 3, 2)
        
        self.stat_cv = QCheckBox('Coeff. of Variation')
        self.stat_cv.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_cv.setToolTip('Coefficient of Variation - std dev relative to mean (as %)')
        stats_layout.addWidget(self.stat_cv, 3, 3)
        
        # Percentiles
        stats_layout.addWidget(QLabel('<b>Percentiles:</b>'), 4, 0)
        
        self.stat_p10 = QCheckBox('P10')
        self.stat_p10.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_p10.setToolTip('Calculate the 10th percentile value')
        stats_layout.addWidget(self.stat_p10, 4, 1)
        
        self.stat_p25 = QCheckBox('P25')
        self.stat_p25.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_p25.setToolTip('Calculate the 25th percentile (Q1 - first quartile)')
        stats_layout.addWidget(self.stat_p25, 4, 2)
        
        self.stat_p50 = QCheckBox('P50 (Median)')
        self.stat_p50.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_p50.setToolTip('Calculate the 50th percentile (median)')
        stats_layout.addWidget(self.stat_p50, 4, 3)
        
        self.stat_p75 = QCheckBox('P75')
        self.stat_p75.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_p75.setToolTip('Calculate the 75th percentile (Q3 - third quartile)')
        stats_layout.addWidget(self.stat_p75, 4, 4)
        
        self.stat_p90 = QCheckBox('P90')
        self.stat_p90.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_p90.setToolTip('Calculate the 90th percentile value')
        stats_layout.addWidget(self.stat_p90, 5, 1)
        
        self.stat_p95 = QCheckBox('P95')
        self.stat_p95.setStyleSheet(STATS_CHECKBOX_STYLE)
        self.stat_p95.setToolTip('Calculate the 95th percentile value')
        stats_layout.addWidget(self.stat_p95, 5, 2)
        
        # Quick select buttons
        quick_layout = QHBoxLayout()
        
        select_basic_btn = QPushButton('Select Basic')
        select_basic_btn.clicked.connect(self._select_basic_stats)
        quick_layout.addWidget(select_basic_btn)
        
        select_all_btn = QPushButton('Select All')
        select_all_btn.clicked.connect(self._select_all_stats)
        quick_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton('Deselect All')
        deselect_all_btn.clicked.connect(self._deselect_all_stats)
        quick_layout.addWidget(deselect_all_btn)
        
        quick_layout.addStretch()
        
        stats_layout.addLayout(quick_layout, 6, 0, 1, 6)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        tab.setLayout(layout)
        return tab
    
    def _create_output_tab(self):
        """Create the Output & Export tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # === OUTPUT LAYER ===
        output_group = QGroupBox('Output Layer')
        output_layout = QVBoxLayout()
        
        # Output mode
        self.output_modify = QRadioButton('Modify original layer (add columns)')
        self.output_new = QRadioButton('Create new layer')
        self.output_new.setChecked(True)
        
        output_layout.addWidget(self.output_modify)
        output_layout.addWidget(self.output_new)
        
        # Output path (for new layer)
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel('Output path:'))
        
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText('Select output location...')
        path_layout.addWidget(self.output_path, 1)
        
        browse_btn = QPushButton('Browse')
        browse_btn.clicked.connect(self._browse_output)
        path_layout.addWidget(browse_btn)
        
        output_layout.addLayout(path_layout)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # === EXPORT FORMATS ===
        export_group = QGroupBox('Additional Export Formats')
        export_layout = QGridLayout()
        
        self.export_csv = QCheckBox('CSV Table')
        export_layout.addWidget(self.export_csv, 0, 0)
        
                
        self.export_html = QCheckBox('HTML Report')
        export_layout.addWidget(self.export_html, 1, 0)
        
        self.export_pdf = QCheckBox('PDF Report')
        export_layout.addWidget(self.export_pdf, 1, 1)
        
        self.export_json = QCheckBox('JSON')
        export_layout.addWidget(self.export_json, 2, 0)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        # === PROCESSING OPTIONS ===
        options_group = QGroupBox('Processing Options')
        options_layout = QVBoxLayout()
        
        self.auto_align = QCheckBox('Auto-align rasters (reproject/resample if needed)')
        self.auto_align.setChecked(True)
        self.auto_align.setToolTip('Automatically reproject and resample rasters to match polygon layer CRS')
        options_layout.addWidget(self.auto_align)
        
        self.handle_nodata = QCheckBox('Handle NoData correctly')
        self.handle_nodata.setChecked(True)
        self.handle_nodata.setToolTip('Skip NoData pixels in calculations')
        options_layout.addWidget(self.handle_nodata)
        
        self.enable_resume = QCheckBox('Enable resume mode (checkpoint system)')
        self.enable_resume.setChecked(True)
        self.enable_resume.setToolTip('Save progress periodically, allowing resume if interrupted')
        options_layout.addWidget(self.enable_resume)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def _create_performance_tab(self):
        """Create the Performance tab."""
        from qgis.PyQt.QtWidgets import QScrollArea
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        # Content widget
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        
        # System info
        info_group = QGroupBox('System Resources')
        info_layout = QVBoxLayout()
        
        # Get system info
        total_ram_gb = psutil.virtual_memory().total / (1024**3)
        cpu_count = psutil.cpu_count()
        
        info_layout.addWidget(QLabel(f'Total RAM: {total_ram_gb:.1f} GB'))
        info_layout.addWidget(QLabel(f'CPU Cores: {cpu_count}'))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # === RAM CONTROL ===
        ram_group = QGroupBox('Memory Management')
        ram_layout = QVBoxLayout()
        
        ram_layout.addWidget(QLabel('Maximum RAM usage:'))
        
        ram_slider_layout = QHBoxLayout()
        
        self.ram_slider = QSlider(Qt.Horizontal)
        self.ram_slider.setMinimum(1)
        self.ram_slider.setMaximum(int(total_ram_gb))
        self.ram_slider.setValue(int(total_ram_gb * 0.5))  # Default 50%
        self.ram_slider.setTickPosition(QSlider.TicksBelow)
        self.ram_slider.setTickInterval(2)
        ram_slider_layout.addWidget(self.ram_slider)
        
        self.ram_label = QLabel(f'{self.ram_slider.value()} GB')
        self.ram_label.setMinimumWidth(60)
        ram_slider_layout.addWidget(self.ram_label)
        
        ram_layout.addLayout(ram_slider_layout)
        
        ram_note = QLabel('⚠️ Recommended: Leave 4-8 GB free for system and other applications')
        ram_note.setStyleSheet('color: gray; font-style: italic;')
        ram_layout.addWidget(ram_note)
        
        ram_group.setLayout(ram_layout)
        layout.addWidget(ram_group)
        
        # === CPU CONTROL ===
        cpu_group = QGroupBox('CPU Management')
        cpu_layout = QVBoxLayout()
        
        cpu_layout.addWidget(QLabel('Number of CPU cores to use:'))
        
        cpu_slider_layout = QHBoxLayout()
        
        self.cpu_slider = QSlider(Qt.Horizontal)
        self.cpu_slider.setMinimum(1)
        self.cpu_slider.setMaximum(cpu_count)
        self.cpu_slider.setValue(max(1, cpu_count - 2))  # Leave 2 cores free
        self.cpu_slider.setTickPosition(QSlider.TicksBelow)
        self.cpu_slider.setTickInterval(1)
        cpu_slider_layout.addWidget(self.cpu_slider)
        
        self.cpu_label = QLabel(f'{self.cpu_slider.value()} cores')
        self.cpu_label.setMinimumWidth(60)
        cpu_slider_layout.addWidget(self.cpu_label)
        
        cpu_layout.addLayout(cpu_slider_layout)
        
        cpu_note = QLabel('⚠️ Recommended: Leave 1-2 cores free for QGIS and system')
        cpu_note.setStyleSheet('color: gray; font-style: italic;')
        cpu_layout.addWidget(cpu_note)
        
        cpu_group.setLayout(cpu_layout)
        layout.addWidget(cpu_group)
        
        # === PRIORITY ===
        priority_group = QGroupBox('Processing Priority')
        priority_layout = QVBoxLayout()
        
        self.priority_normal = QRadioButton('Normal (recommended)')
        self.priority_normal.setChecked(True)
        self.priority_normal.setToolTip('Balanced performance, allows other apps to run smoothly')
        priority_layout.addWidget(self.priority_normal)
        
        self.priority_low = QRadioButton('Low (runs slower, minimal system impact)')
        self.priority_low.setToolTip('Use when you need to work on other tasks simultaneously')
        priority_layout.addWidget(self.priority_low)
        
        self.priority_high = QRadioButton('High (faster, may slow other apps)')
        self.priority_high.setToolTip('Use only when this is the only important task')
        priority_layout.addWidget(self.priority_high)
        
        priority_group.setLayout(priority_layout)
        layout.addWidget(priority_group)
        
        # === BACKGROUND MODE ===
        background_group = QGroupBox('Background Processing')
        background_layout = QVBoxLayout()
        
        self.background_mode = QCheckBox('Run in background (keeps QGIS responsive)')
        self.background_mode.setChecked(True)
        self.background_mode.setToolTip('Processing runs in separate process, QGIS stays fully usable')
        background_layout.addWidget(self.background_mode)
        
        self.minimize_tray = QCheckBox('Minimize to system tray during processing')
        self.minimize_tray.setToolTip('Progress dialog minimizes, shows notification when complete')
        background_layout.addWidget(self.minimize_tray)
        
        background_group.setLayout(background_layout)
        layout.addWidget(background_group)
        
        # === DEPENDENCY STATUS SECTION ===
        deps_group = QGroupBox('📦 Dependencies & Features')
        deps_layout = QVBoxLayout()
        
        # Run checker
        from ..utils.dependency_checker import DependencyChecker
        checker = DependencyChecker()
        report = checker.get_detailed_report()
        
        # Status header
        if report['all_ok']:
            status_text = '✅ <b style="color: #4CAF50;">All dependencies installed</b><br>' \
                         '<small style="color: #757575;">All features available</span>'
        else:
            status_text = '⚠️ <b style="color: #FF9800;">Some optional packages missing</b><br>' \
                         '<small style="color: #757575;">Basic functionality available, some exports disabled</span>'
        
        status_label = QLabel(status_text)
        status_label.setWordWrap(True)
        deps_layout.addWidget(status_label)
        
        # Separator
        deps_layout.addSpacing(8)
        
        # Core packages
        core_label = QLabel('<b>Core Packages (Required):</b>')
        core_label.setStyleSheet('margin-top: 4px;')
        deps_layout.addWidget(core_label)
        
        core_grid = QGridLayout()
        core_grid.setSpacing(4)
        row = 0
        
        core_info = {
            'numpy': 'Numerical computations',
            'scipy': 'Statistical calculations'
        }
        
        for package, description in core_info.items():
            installed = package not in report['missing_core']
            
            check_icon = QLabel('✅' if installed else '❌')
            check_icon.setStyleSheet('font-size: 12pt;')
            core_grid.addWidget(check_icon, row, 0)
            
            pkg_label = QLabel(package)
            pkg_label.setStyleSheet('font-weight: 500;')
            core_grid.addWidget(pkg_label, row, 1)
            
            desc_label = QLabel(f'<small style="color: #757575;">{description}</span>')
            core_grid.addWidget(desc_label, row, 2)
            
            row += 1
        
        core_grid.setColumnStretch(2, 1)
        deps_layout.addLayout(core_grid)
        
        # Feature packages
        deps_layout.addSpacing(8)
        feature_label = QLabel('<b>Feature Packages (Optional):</b>')
        feature_label.setStyleSheet('margin-top: 4px;')
        deps_layout.addWidget(feature_label)
        
        feature_grid = QGridLayout()
        feature_grid.setSpacing(4)
        row = 0
        
        feature_info = {
            'pandas': 'CSV export, data processing',
            'reportlab': 'PDF reports',
            'jinja2': 'HTML reports',
            'plotly': 'Interactive charts',
            'matplotlib': 'Static charts'
        }
        
        for package, description in feature_info.items():
            installed = package in report['available_features']
            
            check_icon = QLabel('✅' if installed else '⚠️')
            check_icon.setStyleSheet('font-size: 11pt;')
            feature_grid.addWidget(check_icon, row, 0)
            
            pkg_label = QLabel(package)
            pkg_label.setStyleSheet('font-weight: 500;' if installed else 'color: #9E9E9E;')
            feature_grid.addWidget(pkg_label, row, 1)
            
            desc_label = QLabel(f'<small style="color: #757575;">{description}</span>')
            feature_grid.addWidget(desc_label, row, 2)
            
            row += 1
        
        feature_grid.setColumnStretch(2, 1)
        deps_layout.addLayout(feature_grid)
        
        # Install command if missing features
        if report['missing_features']:
            deps_layout.addSpacing(12)
            
            install_label = QLabel('<b>Install missing packages:</b>')
            deps_layout.addWidget(install_label)
            
            cmd = checker.get_installation_command(report['missing_features'])
            
            # Command container with copy button
            cmd_container = QWidget()
            cmd_container.setStyleSheet("""
                QWidget {
                    background-color: #F5F5F5;
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                }
            """)
            cmd_layout = QHBoxLayout()
            cmd_layout.setContentsMargins(8, 6, 8, 6)
            
            cmd_text = QLineEdit(cmd)
            cmd_text.setReadOnly(True)
            cmd_text.setStyleSheet(
                'QLineEdit {'
                '  background: transparent;'
                '  border: none;'
                '  font-family: Consolas, Monaco, monospace;'
                '  font-size: 9pt;'
                '  color: #202124;'
                '}'
            )
            cmd_layout.addWidget(cmd_text)
            
            copy_btn = QPushButton('📋 Copy')
            copy_btn.setMaximumWidth(70)
            copy_btn.setToolTip('Copy command to clipboard')
            copy_btn.clicked.connect(lambda: self._copy_to_clipboard(cmd))
            cmd_layout.addWidget(copy_btn)
            
            cmd_container.setLayout(cmd_layout)
            deps_layout.addWidget(cmd_container)
            
        # Help text
        help_label = QLabel(
            '<small style="color: #757575;">'
            '💡 Install packages in your Python environment or QGIS Python Console'
            '</span>'
        )
        help_label.setWordWrap(True)
        deps_layout.addWidget(help_label)
        
        deps_group.setLayout(deps_layout)
        layout.addWidget(deps_group)

        layout.addStretch()
        
        tab.setLayout(layout)
        # Set tab as scroll widget
        scroll.setWidget(tab)
        return scroll
    
    def _connect_signals(self):
        """Connect widget signals."""
        # Update labels when sliders change
        self.ram_slider.valueChanged.connect(
            lambda v: self.ram_label.setText(f'{v} GB')
        )
        self.cpu_slider.valueChanged.connect(
            lambda v: self.cpu_label.setText(f'{v} cores')
        )
        
        # Update info label when rasters change
        self.raster_widget.rastersChanged.connect(self._update_info)
        
        # Update output path enabled state
        self.output_new.toggled.connect(
            lambda checked: self.output_path.setEnabled(checked)
        )
    
    def _load_defaults(self):
        """Load default values."""
        # Set default output path
        default_path = os.path.join(
            os.path.expanduser('~'),
            'zonify_output.gpkg'
        )
        self.output_path.setText(default_path)
        
        self._update_info()
    
    def _select_basic_stats(self):
        """Select basic statistics (mean, sum, min, max)."""
        self.stat_mean.setChecked(True)
        self.stat_sum.setChecked(True)
        self.stat_min.setChecked(True)
        self.stat_max.setChecked(True)
    
    def _select_all_stats(self):
        """Select all statistics."""
        # Get all statistic checkboxes
        stat_checkboxes = [
            self.stat_mean, self.stat_sum, self.stat_min, self.stat_max,
            self.stat_median, self.stat_mode, self.stat_count, self.stat_minority, self.stat_range, self.stat_variety,
            self.stat_stddev, self.stat_variance, self.stat_cv,
            self.stat_p10, self.stat_p25, self.stat_p50, self.stat_p75,
            self.stat_p90, self.stat_p95
        ]
        
        for checkbox in stat_checkboxes:
            checkbox.setChecked(True)

    def _deselect_all_stats(self):
        """Deselect all statistics."""
        # Get all statistic checkboxes
        stat_checkboxes = [
            self.stat_mean, self.stat_sum, self.stat_min, self.stat_max,
            self.stat_median, self.stat_mode, self.stat_count, self.stat_minority, self.stat_range, self.stat_variety,
            self.stat_stddev, self.stat_variance, self.stat_cv,
            self.stat_p10, self.stat_p25, self.stat_p50, self.stat_p75,
            self.stat_p90, self.stat_p95
        ]
        
        for checkbox in stat_checkboxes:
            checkbox.setChecked(False)
    
    def _browse_output(self):
        """Open file dialog to select output path."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Select Output File',
            self.output_path.text(),
            'GeoPackage (*.gpkg);;All Files (*.*)'
        )
        
        if file_path:
            self.output_path.setText(file_path)
    
    def _update_info(self):
        """Update info label with current status."""
        poly_count = 0
        if self.polygon_combo.currentLayer():
            poly_count = self.polygon_combo.currentLayer().featureCount()
        
        raster_count = self.raster_widget.get_raster_count()
        
        if poly_count > 0 and raster_count > 0:
            self.info_label.setText(
                f'Ready: {poly_count:,} polygons × {raster_count} rasters'
            )
            self.info_label.setStyleSheet('color: green;')
            self.run_btn.setEnabled(True)
        else:
            self.info_label.setText('Select polygon layer and at least one raster')
            self.info_label.setStyleSheet('color: orange;')
            self.run_btn.setEnabled(False)
    
    def _on_run(self):
        """Handle Run button click."""
        # Validate inputs
        if not self._validate_inputs():
            return
        
        # Check for output file overwrite (if creating new layer)
        if self.output_new.isChecked():
            output_path = self.output_path.text()
            
            if os.path.exists(output_path):
                reply = QMessageBox.question(
                    self,
                    'File Exists',
                    f'Output file already exists:\n{output_path}\n\n'
                    'Do you want to overwrite it?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
                
                # Delete existing file
                try:
                    os.remove(output_path)
                    self.logger.info(f'Removed existing output file: {output_path}')
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        'Cannot Overwrite',
                        f'Failed to delete existing file:\n{str(e)}\n\n'
                        'Please choose a different output path or delete the file manually.'
                    )
                    return
        
        # Collect configuration
        config = self._collect_configuration()
        
        # Show confirmation
        reply = QMessageBox.question(
            self,
            'Confirm Processing',
            f'Start processing?\n\n'
            f'Polygons: {config["polygon_count"]:,}\n'
            f'Rasters: {config["raster_count"]}\n'
            f'Statistics: {len(config["statistics"])}\n'
            f'Total calculations: {config["polygon_count"] * config["raster_count"]:,}\n\n'
            f'Estimated time will be calculated during processing.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Emit signal to start processing
            self.runProcessing.emit(config)
    
    def _validate_inputs(self):
        """
        Validate user inputs.
        
        Returns:
            bool: True if valid, False otherwise
        """
        # Check polygon layer
        if not self.polygon_combo.currentLayer():
            QMessageBox.warning(
                self,
                'No Polygon Layer',
                'Please select a polygon layer.'
            )
            return False
        
        # Check rasters
        if self.raster_widget.get_raster_count() == 0:
            QMessageBox.warning(
                self,
                'No Rasters',
                'Please add at least one raster file.'
            )
            return False
        
        # Check statistics
        if not self._get_selected_statistics():
            QMessageBox.warning(
                self,
                'No Statistics',
                'Please select at least one statistic to calculate.'
            )
            return False
        
        # Check output path (if creating new layer)
        if self.output_new.isChecked():
            if not self.output_path.text():
                QMessageBox.warning(
                    self,
                    'No Output Path',
                    'Please specify an output file path.'
                )
                return False
        
        return True
    
    def _get_selected_statistics(self):
        """
        Get list of selected statistics.
        
        Returns:
            list: List of statistic names
        """
        stats = []
        
        stat_widgets = [
            (self.stat_mean, 'mean'),
            (self.stat_sum, 'sum'),
            (self.stat_min, 'min'),
            (self.stat_max, 'max'),
            (self.stat_coverage, 'coverage_pct'),
            (self.stat_median, 'median'),
            (self.stat_mode, 'mode'),
            (self.stat_minority, 'minority'),
            (self.stat_variety, 'variety'),
            (self.stat_count, 'count'),
            (self.stat_range, 'range'),
            (self.stat_stddev, 'stddev'),
            (self.stat_variance, 'variance'),
            (self.stat_cv, 'cv'),
            (self.stat_p10, 'p10'),
            (self.stat_p25, 'p25'),
            (self.stat_p50, 'p50'),
            (self.stat_p75, 'p75'),
            (self.stat_p90, 'p90'),
            (self.stat_p95, 'p95'),
        ]
        
        for widget, stat_name in stat_widgets:
            if widget.isChecked():
                stats.append(stat_name)
        
        return stats
    
    def _create_advanced_tab(self):
        """Create the Advanced tab with task-based UI."""
        from qgis.PyQt.QtWidgets import QScrollArea, QStackedWidget, QFrame
        
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content widget
        tab = QWidget()
        layout = QVBoxLayout()
        
        # === HEADER ===
        title = QLabel('<b>Advanced Analysis</b>')
        title_font = QFont()
        title_font.setPointSize(11)
        title.setFont(title_font)
        layout.addWidget(title)
        
        subtitle = QLabel(
            '<span style="color: #757575;">Transform your results into actionable insights</span>'
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        
        # === TASK-BASED UI ===
        
        # === SCORE CREATOR (collapsible with arrow) ===
        from qgis.PyQt.QtWidgets import QToolButton
        
        score_toggle = QToolButton()
        score_toggle.setText('▶ 🧮 Create Score / Index')
        score_toggle.setCheckable(True)
        score_toggle.setChecked(False)
        score_toggle.setStyleSheet(
            'QToolButton {'
            '  border: none;'
            '  background: transparent;'
            '  font-weight: bold;'
            '  font-size: 11pt;'
            '  padding: 8px;'
            '  text-align: left;'
            '}'
            'QToolButton:hover {'
            '  background-color: #f0f0f0;'
            '}'
        )
        layout.addWidget(score_toggle)
        
        score_content = QWidget()
        score_layout = QVBoxLayout()
        score_layout.setContentsMargins(20, 5, 5, 5)
        score_layout.addWidget(QLabel(
            '<span style="color: #757575;">Combine multiple indicators into single value.<br>'
            'Example: Risk score from flood + population</span>'
        ))
        
        self.score_creator_widget = ScoreCreatorWidget(self)
        score_layout.addWidget(self.score_creator_widget)
        
        score_content.setLayout(score_layout)
        score_content.setVisible(False)
        layout.addWidget(score_content)
        
        score_toggle.toggled.connect(lambda checked: self._toggle_section(score_toggle, score_content, checked, '🧮 Create Score / Index'))
        # === AREA CLASSIFIER (collapsible with arrow) ===
        classifier_toggle = QToolButton()
        classifier_toggle.setText('▶ 🎨 Classify Areas')
        classifier_toggle.setCheckable(True)
        classifier_toggle.setChecked(False)
        classifier_toggle.setStyleSheet(
            'QToolButton {'
            '  border: none;'
            '  background: transparent;'
            '  font-weight: bold;'
            '  font-size: 11pt;'
            '  padding: 8px;'
            '  text-align: left;'
            '}'
            'QToolButton:hover {'
            '  background-color: #f0f0f0;'
            '}'
        )
        layout.addWidget(classifier_toggle)
        
        classifier_content = QWidget()
        classifier_layout = QVBoxLayout()
        classifier_layout.setContentsMargins(20, 5, 5, 5)
        classifier_layout.addWidget(QLabel(
            '<span style="color: #757575;">Group continuous values into categories (Low/Medium/High).<br>'
            'Example: Classify flood risk levels</span>'
        ))
        
        self.area_classifier_widget = AreaClassifierWidget(self)
        classifier_layout.addWidget(self.area_classifier_widget)
        
        classifier_content.setLayout(classifier_layout)
        classifier_content.setVisible(False)
        layout.addWidget(classifier_content)
        
        classifier_toggle.toggled.connect(lambda checked: self._toggle_section(classifier_toggle, classifier_content, checked, '🎨 Classify Areas'))
        # === AREA HIGHLIGHTER (collapsible with arrow) ===
        highlighter_toggle = QToolButton()
        highlighter_toggle.setText('▶ 🏁 Highlight Top/Bottom Areas')
        highlighter_toggle.setCheckable(True)
        highlighter_toggle.setChecked(False)
        highlighter_toggle.setStyleSheet(
            'QToolButton {'
            '  border: none;'
            '  background: transparent;'
            '  font-weight: bold;'
            '  font-size: 11pt;'
            '  padding: 8px;'
            '  text-align: left;'
            '}'
            'QToolButton:hover {'
            '  background-color: #f0f0f0;'
            '}'
        )
        layout.addWidget(highlighter_toggle)
        
        highlighter_content = QWidget()
        highlighter_layout = QVBoxLayout()
        highlighter_layout.setContentsMargins(20, 5, 5, 5)
        highlighter_layout.addWidget(QLabel(
            '<span style="color: #757575;">Flag best/worst performing areas.<br>'
            'Example: Top 10% solar potential as "High Priority"</span>'
        ))
        
        self.area_highlighter_widget = AreaHighlighterWidget(self)
        highlighter_layout.addWidget(self.area_highlighter_widget)
        
        highlighter_content.setLayout(highlighter_layout)
        highlighter_content.setVisible(False)
        layout.addWidget(highlighter_content)
        
        highlighter_toggle.toggled.connect(lambda checked: self._toggle_section(highlighter_toggle, highlighter_content, checked, '🏁 Highlight Top/Bottom Areas'))
        # === RULE TAGGER (collapsible with arrow) ===
        tagger_toggle = QToolButton()
        tagger_toggle.setText('▶ 🏷️ Tag Areas by Rules')
        tagger_toggle.setCheckable(True)
        tagger_toggle.setChecked(False)
        tagger_toggle.setStyleSheet(
            'QToolButton {'
            '  border: none;'
            '  background: transparent;'
            '  font-weight: bold;'
            '  font-size: 11pt;'
            '  padding: 8px;'
            '  text-align: left;'
            '}'
            'QToolButton:hover {'
            '  background-color: #f0f0f0;'
            '}'
        )
        layout.addWidget(tagger_toggle)
        
        tagger_content = QWidget()
        tagger_layout = QVBoxLayout()
        tagger_layout.setContentsMargins(20, 5, 5, 5)
        tagger_layout.addWidget(QLabel(
            '<span style="color: #757575;">Flag areas meeting specific conditions.<br>'
            'Example: flood > 2.0 AND population > 1000 → "High Risk"</span>'
        ))
        
        self.rule_tagger_widget = RuleTaggerWidget(self)
        tagger_layout.addWidget(self.rule_tagger_widget)
        
        tagger_content.setLayout(tagger_layout)
        tagger_content.setVisible(False)
        layout.addWidget(tagger_content)
        
        tagger_toggle.toggled.connect(lambda checked: self._toggle_section(tagger_toggle, tagger_content, checked, '🏷️ Tag Areas by Rules'))

        # === SEPARATOR ===
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # === TIME SERIES (collapsible with arrow) ===
        timeseries_toggle = QToolButton()
        timeseries_toggle.setText('▶ 📈 Time Series Analysis')
        timeseries_toggle.setCheckable(True)
        timeseries_toggle.setChecked(False)
        timeseries_toggle.setStyleSheet(
            'QToolButton {'
            '  border: none;'
            '  background: transparent;'
            '  font-weight: bold;'
            '  font-size: 11pt;'
            '  padding: 8px;'
            '  text-align: left;'
            '}'
            'QToolButton:hover {'
            '  background-color: #f0f0f0;'
            '}'
        )
        layout.addWidget(timeseries_toggle)
        
        timeseries_content = QWidget()
        timeseries_layout = QVBoxLayout()
        timeseries_layout.setContentsMargins(20, 5, 5, 5)
        timeseries_layout.addWidget(QLabel(
            '<span style="color: #757575;">Analyze temporal patterns across multiple rasters.<br>'
            'Example: Change detection, trend analysis, seasonal patterns, extreme events</span>'
        ))
        
        self.time_series_widget = TimeSeriesWidget(self)
        timeseries_layout.addWidget(self.time_series_widget)
        
        timeseries_content.setLayout(timeseries_layout)
        timeseries_content.setVisible(False)
        layout.addWidget(timeseries_content)
        
        timeseries_toggle.toggled.connect(lambda checked: self._toggle_section(timeseries_toggle, timeseries_content, checked, '📈 Time Series Analysis'))
        
        layout.addStretch()
        
        tab.setLayout(layout)
        scroll.setWidget(tab)
        
        return scroll
    
    def _create_quick_map_tab(self):
        """Create Quick Map tab."""
        from qgis.PyQt.QtWidgets import QScrollArea
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Quick Map widget
        self.quick_map_widget = QuickMapWidget(self)
        layout.addWidget(self.quick_map_widget)
        
        layout.addStretch()
        
        tab.setLayout(layout)
        scroll.setWidget(tab)
        
        return scroll
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        # Oprește processing dacă rulează
        if hasattr(self, 'processing_thread') and self.processing_thread:
            if self.processing_thread.isRunning():
                self.processing_thread.cancel()
                self.processing_thread.wait()
        
        super().closeEvent(event)
    
    def _toggle_section(self, button, content, checked, title):
        """Toggle section visibility and update arrow."""
        content.setVisible(checked)
        arrow = '▼' if checked else '▶'
        button.setText(f'{arrow} {title}')
    
    def _on_score_configured(self, config):
        """
        Handle score configuration from Score Creator.
        Store it for processing.
        
        Args:
            config (dict): Score configuration
        """
        # Store score config
        if not hasattr(self, 'score_configs'):
            self.score_configs = []
        
        self.score_configs.append(config)
        
        self.logger.info(f"Score configured: {config['name']}")

    def _collect_configuration(self):
        """
        Collect all configuration from UI.
        
        Returns:
            dict: Configuration dictionary
        """
        poly_layer = self.polygon_combo.currentLayer()
        
        config = {
            # Input
            'polygon_layer': poly_layer,
            'polygon_count': poly_layer.featureCount(),
            'raster_paths': self.raster_widget.get_raster_paths(),
            'raster_count': self.raster_widget.get_raster_count(),
            
            # Statistics
            'statistics': self._get_selected_statistics(),
            
            # Output
            'output_mode': 'new' if self.output_new.isChecked() else 'modify',
            'output_path': self.output_path.text(),
            
            # Export formats
            'export_csv': self.export_csv.isChecked(),
            'export_html': self.export_html.isChecked(),
            'export_pdf': self.export_pdf.isChecked(),
            'export_json': self.export_json.isChecked(),
            
            # Processing options
            'auto_align': self.auto_align.isChecked(),
            'handle_nodata': self.handle_nodata.isChecked(),
            'enable_resume': self.enable_resume.isChecked(),
            
            # Performance
            'max_ram_gb': self.ram_slider.value(),
            'cpu_cores': self.cpu_slider.value(),
            'priority': 'high' if self.priority_high.isChecked() else 
                       'low' if self.priority_low.isChecked() else 'normal',
            'background_mode': self.background_mode.isChecked(),
            'minimize_tray': self.minimize_tray.isChecked(),
        }
        print("=" * 50)
        print("DEBUG: Configuration collected:")
        print(f"  export_csv = {config.get('export_csv')}")
        print(f"  export_html = {config.get('export_html')}")
        print(f"  export_pdf = {config.get('export_pdf')}")
        print(f"  export_json = {config.get('export_json')}")
        print("=" * 50)
        
        # Advanced features (Post-Processing + Time Series)
        config['score_configs'] = getattr(self, 'score_configs', [])
        config['time_series_config'] = self.time_series_widget.get_configuration()
        
        return config