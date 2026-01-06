"""
Quick Map Widget for Zonify

One-click professional map generation and export.
Creates styled maps with legend, scale bar, north arrow, and exports to PNG/PDF.

Author: Dragos Gontariu
License: GPL-3.0
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QSpinBox, QRadioButton,
    QButtonGroup, QGroupBox, QMessageBox, QFileDialog, QApplication
)
from qgis.PyQt.QtCore import Qt, QSize
from qgis.PyQt.QtGui import QFont
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsGraduatedSymbolRenderer, QgsCategorizedSymbolRenderer,
    QgsRendererRange, QgsRendererCategory, QgsSymbol,
    QgsStyle, QgsGradientColorRamp, QgsColorRampShader,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLegend,
    QgsLayoutItemScaleBar, QgsLayoutItemLabel, QgsLayoutItemPicture,
    QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter,
    QgsRectangle, QgsCoordinateReferenceSystem, QgsApplication, QgsLegendStyle, QgsScaleBarSettings
)
import os


class QuickMapWidget(QWidget):
    """
    Widget for quick map generation and export.
    
    Creates professional maps with automatic layout, styling, and export.
    """
    
    # Color ramps organized by category
    COLOR_RAMPS = {
        'Diverging': ['Spectral', 'RdYlGn', 'RdYlBu', 'RdBu', 'PiYG', 'BrBG', 'PRGn'],
        'Sequential': ['Blues', 'Greens', 'Reds', 'Oranges', 'Purples', 
                      'Viridis', 'Plasma', 'Inferno', 'Magma'],
        'Qualitative': ['Set1', 'Set2', 'Set3', 'Pastel1', 'Pastel2', 'Dark2']
    }
    
    # Classification modes
    CLASSIFICATION_MODES = [
        'Natural Breaks (Jenks)',
        'Equal Interval',
        'Quantile (Equal Count)',
        'Standard Deviation',
        'Pretty Breaks'
    ]
    
    # Nice scale denominators
    NICE_SCALES = [
        ('Auto (best fit)', 0),
        ('1:10,000', 10000),
        ('1:25,000', 25000),
        ('1:50,000', 50000),
        ('1:100,000', 100000),
        ('1:250,000', 250000),
        ('1:500,000', 500000),
        ('1:1,000,000', 1000000),
        ('1:2,500,000', 2500000),
        ('1:5,000,000', 5000000)
    ]
    
    def __init__(self, parent=None):
        """
        Constructor.
        
        Args:
            parent: Parent widget (main dialog)
        """
        super(QuickMapWidget, self).__init__(parent)
        
        self.parent_dialog = parent
        self.current_layout = None
        self.setObjectName('quickMapWidget')
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # === HEADER ===
        header = QLabel(
            '<b>🗺️ Quick Map Generator</b><br>'
            '<span style="color: #757575;">'
            'Create professional maps with automatic layout and export - no Layout Manager needed!'
            '</span>'
        )
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # === EXPANDABLE HELP ===
        self.help_toggle_btn = QPushButton('📚 Help & Guide (click to show)')
        self.help_toggle_btn.setCheckable(True)
        self.help_toggle_btn.setChecked(False)
        self.help_toggle_btn.setStyleSheet(
            'QPushButton {'
            '  text-align: left;'
            '  padding: 8px;'
            '  background-color: #e3f2fd;'
            '  border: 1px solid #90caf9;'
            '  border-radius: 4px;'
            '  font-weight: bold;'
            '}'
            'QPushButton:hover {'
            '  background-color: #bbdefb;'
            '}'
            'QPushButton:checked {'
            '  background-color: #90caf9;'
            '}'
        )
        layout.addWidget(self.help_toggle_btn)
        
        self.help_content = QWidget()
        help_layout = QVBoxLayout()
        help_layout.setContentsMargins(15, 10, 15, 10)
        
        help_text = QLabel(
            '<b style="color: #1976d2; font-size: 11pt;">🎯 Quick Start</b><br>'
            '<small>'
            '1️⃣ Select layer and field to visualize<br>'
            '2️⃣ Choose symbology (colors, classes, method)<br>'
            '3️⃣ Configure map layout (title, elements)<br>'
            '4️⃣ Generate & export to PNG/PDF<br><br>'
            
            '<b style="color: #1976d2;">💡 Use Cases:</b><br>'
            '• Export analysis results for presentations<br>'
            '• Create report-ready maps quickly<br>'
            '• Generate multiple maps with consistent styling<br>'
            '• Professional cartography without Layout Manager<br><br>'
            
            '<b style="color: #1976d2;">✨ Features:</b><br>'
            '• Auto-scale calculation for optimal display<br>'
            '• Smart element positioning<br>'
            '• Multiple color ramp categories<br>'
            '• Export to PNG (300 DPI) and PDF (vector)<br>'
            '• Customizable legend, scale bar, north arrow'
            '</small>'
        )
        help_text.setWordWrap(True)
        help_layout.addWidget(help_text)
        
        self.help_content.setLayout(help_layout)
        self.help_content.setVisible(False)
        self.help_content.setStyleSheet(
            'QWidget {'
            '  background-color: #f5f5f5;'
            '  border: 1px solid #e0e0e0;'
            '  border-radius: 4px;'
            '}'
        )
        layout.addWidget(self.help_content)
        
        self.help_toggle_btn.toggled.connect(self._toggle_help)
        
        # === STEP 1: LAYER & FIELD ===
        step1_group = QGroupBox('Step 1: Select Layer & Field')
        step1_layout = QVBoxLayout()
        
        # Layer selection
        layer_layout = QHBoxLayout()
        layer_layout.addWidget(QLabel('Layer:'))
        
        from qgis.gui import QgsMapLayerComboBox
        from qgis.core import QgsMapLayerProxyModel
        
        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.layer_combo.layerChanged.connect(self._on_layer_changed)
        layer_layout.addWidget(self.layer_combo)
        
        step1_layout.addLayout(layer_layout)
        
        # Field selection
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel('Field:'))
        
        self.field_combo = QComboBox()
        self.field_combo.currentIndexChanged.connect(self._on_field_changed)
        field_layout.addWidget(self.field_combo)
        
        step1_layout.addLayout(field_layout)
        
        # Field type detection
        self.field_type_label = QLabel('<small><i>Field type will be detected automatically</i></small>')
        step1_layout.addWidget(self.field_type_label)
        
        step1_group.setLayout(step1_layout)
        layout.addWidget(step1_group)
        
        # === STEP 2: SYMBOLOGY ===
        step2_group = QGroupBox('Step 2: Symbology')
        step2_layout = QVBoxLayout()
        
        # Method
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel('Method:'))
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(['Graduated (Numeric)', 'Categorized (Text)', 'Single Symbol'])
        self.method_combo.currentIndexChanged.connect(self._on_method_changed)
        method_layout.addWidget(self.method_combo)
        
        step2_layout.addLayout(method_layout)
        
        # Classes (for graduated)
        self.classes_widget = QWidget()
        classes_layout = QHBoxLayout()
        classes_layout.setContentsMargins(0, 0, 0, 0)
        classes_layout.addWidget(QLabel('Classes:'))
        
        self.classes_spin = QSpinBox()
        self.classes_spin.setMinimum(3)
        self.classes_spin.setMaximum(10)
        self.classes_spin.setValue(5)
        classes_layout.addWidget(self.classes_spin)
        classes_layout.addStretch()
        
        self.classes_widget.setLayout(classes_layout)
        step2_layout.addWidget(self.classes_widget)
        
        # Classification mode (for graduated)
        self.mode_widget = QWidget()
        mode_layout = QHBoxLayout()
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.addWidget(QLabel('Mode:'))
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(self.CLASSIFICATION_MODES)
        mode_layout.addWidget(self.mode_combo)
        
        self.mode_widget.setLayout(mode_layout)
        step2_layout.addWidget(self.mode_widget)
        
        # Color ramp
        color_label_layout = QHBoxLayout()
        color_label_layout.addWidget(QLabel('Color Ramp:'))
        color_label_layout.addStretch()
        
        self.invert_colors_check = QCheckBox('Invert Colors')
        color_label_layout.addWidget(self.invert_colors_check)
        
        step2_layout.addLayout(color_label_layout)
        
        # Combo box below label (full width)
        self.color_combo = QComboBox()
        self.color_combo.setObjectName('colorRampCombo')
        # Combo box below label (full width)
        self.color_combo = QComboBox()
        self.color_combo.setObjectName('colorRampCombo')
        
        # Set icon size for color ramp preview
        from qgis.PyQt.QtCore import QSize
        self.color_combo.setIconSize(QSize(650, 24))
        self._populate_color_ramps()
        step2_layout.addWidget(self.color_combo)
        
        # Preview button
        preview_layout = QHBoxLayout()
        preview_layout.addStretch()
        
        self.preview_btn = QPushButton('🎨 Preview Style')
        self.preview_btn.clicked.connect(self._preview_style)
        preview_layout.addWidget(self.preview_btn)
        
        step2_layout.addLayout(preview_layout)
        
        step2_group.setLayout(step2_layout)
        layout.addWidget(step2_group)
        
        # === STEP 3: LAYOUT ===
        step3_group = QGroupBox('Step 3: Map Layout')
        step3_layout = QVBoxLayout()
        
        # Page setup
        page_layout = QHBoxLayout()
        
        page_layout.addWidget(QLabel('Page:'))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(['A4', 'A3', 'Letter'])
        page_layout.addWidget(self.page_size_combo)
        
        self.orientation_landscape = QRadioButton('Landscape')
        self.orientation_landscape.setChecked(True)
        page_layout.addWidget(self.orientation_landscape)
        
        self.orientation_portrait = QRadioButton('Portrait')
        page_layout.addWidget(self.orientation_portrait)
        
        page_layout.addStretch()
        step3_layout.addLayout(page_layout)
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel('Title:'))
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText('e.g., Risk Assessment Map')
        title_layout.addWidget(self.title_edit)
        
        step3_layout.addLayout(title_layout)
        
        # Subtitle
        subtitle_layout = QHBoxLayout()
        subtitle_layout.addWidget(QLabel('Subtitle:'))
        
        self.subtitle_edit = QLineEdit()
        self.subtitle_edit.setPlaceholderText('e.g., Analysis Date: 2024-12-12')
        subtitle_layout.addWidget(self.subtitle_edit)
        
        step3_layout.addLayout(subtitle_layout)
        
        # Elements
        elements_label = QLabel('<small><b>Map Elements:</b></small>')
        step3_layout.addWidget(elements_label)
        
        elements_layout = QHBoxLayout()
        
        self.legend_check = QCheckBox('Legend')
        self.legend_check.setChecked(True)
        elements_layout.addWidget(self.legend_check)
        
        self.scale_bar_check = QCheckBox('Scale Bar')
        self.scale_bar_check.setChecked(True)
        elements_layout.addWidget(self.scale_bar_check)
        
        self.north_arrow_check = QCheckBox('North Arrow')
        self.north_arrow_check.setChecked(True)
        elements_layout.addWidget(self.north_arrow_check)
        
        self.scale_text_check = QCheckBox('Scale Text (1:xxx)')
        self.scale_text_check.setChecked(False)  # ← OFF by default
        elements_layout.addWidget(self.scale_text_check)
        
        elements_layout.addStretch()
        step3_layout.addLayout(elements_layout)
        
        # Attribution
        attrib_layout = QHBoxLayout()
        attrib_layout.addWidget(QLabel('Attribution:'))
        
        self.attribution_edit = QLineEdit()
        self.attribution_edit.setPlaceholderText('e.g., Data: Source')
        attrib_layout.addWidget(self.attribution_edit)
        
        step3_layout.addLayout(attrib_layout)
        
        step3_group.setLayout(step3_layout)
        layout.addWidget(step3_group)
        
        # === STEP 4: SCALE & EXTENT ===
        step4_group = QGroupBox('Step 4: Scale & Extent')
        step4_layout = QVBoxLayout()
        
        # Extent options
        extent_label = QLabel('<small><b>Map Extent:</b></small>')
        step4_layout.addWidget(extent_label)
        
        self.extent_layer = QRadioButton('Fit to layer extent')
        self.extent_layer.setChecked(True)
        step4_layout.addWidget(self.extent_layer)
        
        self.extent_canvas = QRadioButton('Current canvas extent')
        step4_layout.addWidget(self.extent_canvas)
        
        # Scale
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel('Target Scale:'))
        
        self.scale_combo = QComboBox()
        for scale_name, scale_value in self.NICE_SCALES:
            self.scale_combo.addItem(scale_name, scale_value)
        scale_layout.addWidget(self.scale_combo)
        scale_layout.addStretch()
        
        step4_layout.addLayout(scale_layout)
        
        step4_group.setLayout(step4_layout)
        layout.addWidget(step4_group)
        
        # === STEP 5: EXPORT ===
        step5_group = QGroupBox('Step 5: Export')
        step5_layout = QVBoxLayout()
        
        # Format options
        format_label = QLabel('<small><b>Export Formats:</b></small>')
        step5_layout.addWidget(format_label)
        
        format_layout = QHBoxLayout()
        
        self.export_png_check = QCheckBox('PNG (300 DPI)')
        self.export_png_check.setChecked(True)
        format_layout.addWidget(self.export_png_check)
        
        self.export_pdf_check = QCheckBox('PDF (Vector)')
        self.export_pdf_check.setChecked(True)
        format_layout.addWidget(self.export_pdf_check)
        
        self.export_svg_check = QCheckBox('SVG (Vector)')
        format_layout.addWidget(self.export_svg_check)
        
        format_layout.addStretch()
        step5_layout.addLayout(format_layout)
        
        # Output path
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel('Output:'))
        
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText('Output file path (without extension)')
        output_layout.addWidget(self.output_path_edit)
        
        self.browse_output_btn = QPushButton('📁 Browse')
        self.browse_output_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_output_btn)
        
        step5_layout.addLayout(output_layout)
        
        step5_group.setLayout(step5_layout)
        layout.addWidget(step5_group)
        
        # === GENERATE BUTTON ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.generate_btn = QPushButton('🗺️ Generate & Export Map')
        self.generate_btn.setMinimumWidth(200)
        self.generate_btn.setStyleSheet(
            'QPushButton {'
            '  background-color: #2196F3;'
            '  color: white;'
            '  padding: 10px;'
            '  font-weight: bold;'
            '  font-size: 11pt;'
            '  border-radius: 5px;'
            '}'
            'QPushButton:hover {'
            '  background-color: #1976D2;'
            '}'
            'QPushButton:disabled {'
            '  background-color: #cccccc;'
            '}'
        )
        self.generate_btn.clicked.connect(self._generate_map)
        button_layout.addWidget(self.generate_btn)
        
        layout.addLayout(button_layout)
        
        # Progress
        self.progress_label = QLabel('')
        self.progress_label.setStyleSheet('color: gray; font-style: italic;')
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Initialize
        self._on_layer_changed()
    
    def _toggle_help(self, checked):
        """Toggle help visibility."""
        self.help_content.setVisible(checked)
        if checked:
            self.help_toggle_btn.setText('📚 Help & Guide (click to hide)')
        else:
            self.help_toggle_btn.setText('📚 Help & Guide (click to show)')
    
    def _populate_color_ramps(self):
        """Populate color ramp combo with organized ramps and preview."""
        from qgis.PyQt.QtGui import QIcon, QPixmap, QPainter
        from qgis.PyQt.QtCore import QSize
        
        style = QgsStyle.defaultStyle()
        
        for category, ramps in self.COLOR_RAMPS.items():
            for ramp_name in ramps:
                # Get color ramp
                color_ramp = style.colorRamp(ramp_name)
                
                if color_ramp:
                    # Create preview icon (larger)
                    pixmap = QPixmap(650, 24)
                    pixmap.fill(Qt.transparent)
                    
                    painter = QPainter(pixmap)
                    
                    # Draw gradient
                    for i in range(650):  
                        color = color_ramp.color(i / 650.0)
                        painter.setPen(color)
                        painter.drawLine(i, 0, i, 24)  
                    
                    painter.end()
                    
                    icon = QIcon(pixmap)
                    self.color_combo.addItem(icon, f'{ramp_name}', ramp_name)
                else:
                    # Fallback without icon
                    self.color_combo.addItem(f'{category}: {ramp_name}', ramp_name)
        
        # Add separator
        self.color_combo.insertSeparator(self.color_combo.count())
        
        # Add Custom option
        self.color_combo.addItem('🎨 Custom Colors...', 'custom')
    
    def _create_custom_color_ramp(self):
        """Create custom color ramp from user colors."""
        from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QPushButton, QColorDialog
        from qgis.core import QgsGradientColorRamp
        from qgis.PyQt.QtGui import QColor
        
        dialog = QDialog(self)
        dialog.setWindowTitle('Custom Color Ramp')
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel('Select start and end colors:'))
        
        # Start color button
        start_color = QColor(255, 0, 0)  # Red
        start_btn = QPushButton('Start Color')
        
        def pick_start():
            nonlocal start_color
            color = QColorDialog.getColor(start_color, self, 'Select Start Color')
            if color.isValid():
                start_color = color
                start_btn.setStyleSheet(f'background-color: {color.name()};')
        
        start_btn.clicked.connect(pick_start)
        start_btn.setStyleSheet(f'background-color: {start_color.name()}; min-height: 30px;')
        layout.addWidget(start_btn)
        
        # End color button
        end_color = QColor(0, 255, 0)  # Green
        end_btn = QPushButton('End Color')
        
        def pick_end():
            nonlocal end_color
            color = QColorDialog.getColor(end_color, self, 'Select End Color')
            if color.isValid():
                end_color = color
                end_btn.setStyleSheet(f'background-color: {color.name()};')
        
        end_btn.clicked.connect(pick_end)
        end_btn.setStyleSheet(f'background-color: {end_color.name()}; min-height: 30px;')
        layout.addWidget(end_btn)
        
        # OK/Cancel
        buttons = QHBoxLayout()
        ok_btn = QPushButton('OK')
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # Create gradient ramp
            ramp = QgsGradientColorRamp(start_color, end_color)
            return ramp
        
        return None

    def _on_layer_changed(self):
        """Handle layer selection change."""
        layer = self.layer_combo.currentLayer()
        
        self.field_combo.clear()
        
        if layer and isinstance(layer, QgsVectorLayer):
            # Add numeric fields
            for field in layer.fields():
                if field.type() in [2, 3, 4, 6]:  # Int, Double, etc.
                    self.field_combo.addItem(f'{field.name()} (numeric)', field.name())
            
            # Add text fields
            for field in layer.fields():
                if field.type() in [10]:  # String
                    self.field_combo.addItem(f'{field.name()} (text)', field.name())
            
            # Auto-generate title
            if self.title_edit.text() == '':
                self.title_edit.setText(f'{layer.name()} Map')
    
    def _on_field_changed(self):
        """Handle field selection change."""
        # Detect field type and adjust method
        field_text = self.field_combo.currentText()
        
        if '(numeric)' in field_text:
            self.method_combo.setCurrentIndex(0)  # Graduated
            self.field_type_label.setText('<small style="color: green;">✓ Numeric field - use Graduated symbology</small>')
        elif '(text)' in field_text:
            self.method_combo.setCurrentIndex(1)  # Categorized
            self.field_type_label.setText('<small style="color: blue;">✓ Text field - use Categorized symbology</small>')
    
    def _on_method_changed(self):
        """Handle symbology method change."""
        method = self.method_combo.currentIndex()
        
        # Show/hide options based on method
        self.classes_widget.setVisible(method == 0)  # Graduated
        self.mode_widget.setVisible(method == 0)  # Graduated
    
    def _preview_style(self):
        """Preview style on layer."""
        layer = self.layer_combo.currentLayer()
        if not layer:
            QMessageBox.warning(self, 'No Layer', 'Please select a layer first.')
            return
        
        field_name = self.field_combo.currentData()
        if not field_name:
            QMessageBox.warning(self, 'No Field', 'Please select a field first.')
            return
        
        try:
            self._apply_symbology(layer, field_name, preview=True)
            
            QMessageBox.information(
                self,
                '✓ Style Applied',
                'Style has been applied to the layer.\n'
                'Check the layer in QGIS to see the preview.'
            )
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to apply style:\n{str(e)}')
    
    def _apply_symbology(self, layer, field_name, preview=False):
        """
        Apply symbology to layer.
        
        Args:
            layer: QgsVectorLayer
            field_name: Field name to symbolize
            preview: If True, just preview (don't save)
        """
        from qgis.core import (
            QgsGraduatedSymbolRenderer,
            QgsCategorizedSymbolRenderer,
            QgsSymbol,
            QgsRendererRange,
            QgsRendererCategory,
            QgsStyle,
            QgsClassificationMethod,
            QgsClassificationJenks,
            QgsClassificationEqualInterval,
            QgsClassificationQuantile,
            QgsClassificationStandardDeviation,
            QgsClassificationPrettyBreaks
        )
        
        method_idx = self.method_combo.currentIndex()
        color_ramp_name = self.color_combo.currentData()
        invert = self.invert_colors_check.isChecked()
        
        # Get color ramp
        if color_ramp_name == 'custom':
            # Custom color ramp - open color dialog
            color_ramp = self._create_custom_color_ramp()
            if not color_ramp:
                # User cancelled - use Spectral
                style = QgsStyle.defaultStyle()
                color_ramp = style.colorRamp('Spectral')
        else:
            style = QgsStyle.defaultStyle()
            color_ramp = style.colorRamp(color_ramp_name)
            
            if not color_ramp:
                # Fallback to Spectral
                color_ramp = style.colorRamp('Spectral')
        
        if invert:
            color_ramp.invert()
        
        if method_idx == 0:  # Graduated (Numeric)
            self._apply_graduated_symbology(layer, field_name, color_ramp)
        
        elif method_idx == 1:  # Categorized (Text)
            self._apply_categorized_symbology(layer, field_name, color_ramp)
        
        elif method_idx == 2:  # Single Symbol
            self._apply_single_symbology(layer)
        
        # Refresh layer
        layer.triggerRepaint()
        
        if preview:
            print(f"DEBUG: Applied {self.method_combo.currentText()} symbology to {layer.name()}")
    
    def _apply_graduated_symbology(self, layer, field_name, color_ramp):
        """Apply graduated symbology for numeric fields."""
        from qgis.core import (
            QgsGraduatedSymbolRenderer,
            QgsRendererRange,
            QgsSymbol
        )
        
        n_classes = self.classes_spin.value()
        mode_name = self.mode_combo.currentText()
        
        # Get field index
        field_idx = layer.fields().indexOf(field_name)
        if field_idx == -1:
            raise Exception(f"Field '{field_name}' not found")
        
        # Extract values
        values = []
        for feature in layer.getFeatures():
            val = feature[field_idx]
            if val is not None:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass
        
        if len(values) == 0:
            raise Exception("No valid values found for classification")
        
        import numpy as np
        values = np.array(values)
        
        # Calculate breaks based on mode
        if 'Natural Breaks' in mode_name or 'Jenks' in mode_name:
            breaks = self._calculate_jenks_breaks(values, n_classes)
        elif 'Equal Interval' in mode_name:
            breaks = np.linspace(values.min(), values.max(), n_classes + 1)
        elif 'Quantile' in mode_name:
            breaks = np.percentile(values, np.linspace(0, 100, n_classes + 1))
        elif 'Standard Deviation' in mode_name:
            mean = np.mean(values)
            std = np.std(values)
            breaks = [mean + i * std for i in range(-n_classes//2, n_classes//2 + 2)]
            breaks = sorted([b for b in breaks if values.min() <= b <= values.max()])
        else:  # Pretty Breaks
            breaks = self._calculate_pretty_breaks(values, n_classes)
        
        # Create renderer
        renderer = QgsGraduatedSymbolRenderer(field_name)
        renderer.setSourceColorRamp(color_ramp.clone())
        
        # Add ranges
        ranges = []
        for i in range(len(breaks) - 1):
            min_val = breaks[i]
            max_val = breaks[i + 1]
            
            label = f'{min_val:.2f} - {max_val:.2f}'
            
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            
            range_obj = QgsRendererRange(min_val, max_val, symbol, label)
            ranges.append(range_obj)
        
        renderer.addClassRange(ranges[0])
        for r in ranges[1:]:
            renderer.addClassRange(r)
        
        renderer.updateColorRamp(color_ramp.clone())
        renderer.updateSymbols(QgsSymbol.defaultSymbol(layer.geometryType()))
        
        layer.setRenderer(renderer)
    
    def _apply_categorized_symbology(self, layer, field_name, color_ramp):
        """Apply categorized symbology for text fields."""
        from qgis.core import (
            QgsCategorizedSymbolRenderer,
            QgsRendererCategory,
            QgsSymbol
        )
        
        # Get unique values
        field_idx = layer.fields().indexOf(field_name)
        if field_idx == -1:
            raise Exception(f"Field '{field_name}' not found")
        
        unique_values = set()
        for feature in layer.getFeatures():
            val = feature[field_idx]
            if val is not None and val != '':
                unique_values.add(str(val))
        
        unique_values = sorted(list(unique_values))
        
        if len(unique_values) == 0:
            raise Exception("No unique values found")
        
        # Create renderer
        renderer = QgsCategorizedSymbolRenderer(field_name)
        
        # Add categories
        n_values = len(unique_values)
        for i, value in enumerate(unique_values):
            # Get color from ramp
            color = color_ramp.color(i / max(n_values - 1, 1))
            
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol.setColor(color)
            
            category = QgsRendererCategory(value, symbol, str(value))
            renderer.addCategory(category)
        
        layer.setRenderer(renderer)
    
    def _apply_single_symbology(self, layer):
        """Apply single symbol."""
        from qgis.core import QgsSingleSymbolRenderer, QgsSymbol
        
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        renderer = QgsSingleSymbolRenderer(symbol)
        layer.setRenderer(renderer)
    
    def _calculate_jenks_breaks(self, values, n_classes):
        """Calculate Jenks natural breaks."""
        try:
            from jenkspy import jenks_breaks
            return jenks_breaks(values, n_classes)
        except ImportError:
            # Fallback to quantiles if jenkspy not available
            import numpy as np
            return np.percentile(values, np.linspace(0, 100, n_classes + 1))
    
    def _calculate_pretty_breaks(self, values, n_classes):
        """Calculate pretty breaks (human-readable)."""
        import numpy as np
        
        min_val = values.min()
        max_val = values.max()
        range_val = max_val - min_val
        
        # Find nice step size
        raw_step = range_val / n_classes
        magnitude = 10 ** np.floor(np.log10(raw_step))
        
        # Round to nice numbers (1, 2, 5 * 10^n)
        normalized = raw_step / magnitude
        
        if normalized < 1.5:
            nice_step = 1 * magnitude
        elif normalized < 3:
            nice_step = 2 * magnitude
        elif normalized < 7:
            nice_step = 5 * magnitude
        else:
            nice_step = 10 * magnitude
        
        # Generate breaks
        start = np.floor(min_val / nice_step) * nice_step
        breaks = [start]
        
        while breaks[-1] < max_val:
            breaks.append(breaks[-1] + nice_step)
        
        return np.array(breaks)
    
    def _create_layout(self, layer):
        """
        Create print layout with all elements - OPTIMIZED VERSION.
        
        Args:
            layer: QgsVectorLayer to display
        
        Returns:
            QgsPrintLayout
        """
        from qgis.core import (
            QgsPrintLayout,
            QgsLayoutItemMap,
            QgsLayoutItemLegend,
            QgsLayoutItemScaleBar,
            QgsLayoutItemLabel,
            QgsLayoutSize,
            QgsUnitTypes,
            QgsLayoutPoint,
            QgsLayoutMeasurement
        )
        
        project = QgsProject.instance()
        
        # Get settings
        title = self.title_edit.text() or f'{layer.name()} Map'
        subtitle = self.subtitle_edit.text()
        page_size = self.page_size_combo.currentText()
        landscape = self.orientation_landscape.isChecked()
        
        # Create layout
        layout_name = f'QuickMap_{title.replace(" ", "_")}'
        
        # Remove existing layout with same name
        existing = project.layoutManager().layoutByName(layout_name)
        if existing:
            project.layoutManager().removeLayout(existing)
        
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName(layout_name)
        
        # === PAGE SETUP ===
        page_collection = layout.pageCollection()
        page = page_collection.page(0)
        
        if page_size == 'A4':
            width, height = (297, 210) if landscape else (210, 297)
        elif page_size == 'A3':
            width, height = (420, 297) if landscape else (297, 420)
        else:  # Letter
            width, height = (279, 216) if landscape else (216, 279)
        
        page.setPageSize(QgsLayoutSize(width, height, QgsUnitTypes.LayoutMillimeters))
        
        # === LAYOUT CALCULATIONS ===
        margin = 6
        
        # Header space
        title_height = 12 if title else 0
        subtitle_height = 6 if subtitle else 0
        spacing_after_header = 5 if (title or subtitle) else 0  # Increase from 5 to 8
        header_height = title_height + subtitle_height + spacing_after_header
       
        
        # Footer space
        footer_height = 15  # For scale bar + attribution
        
        # Available space for map + legend
        available_height = height - (2 * margin) - header_height - footer_height
        available_width = width - (2 * margin)
        
        # Legend space
        if self.legend_check.isChecked():
            if landscape:
                # Landscape: legend on right (20% of width, max 65mm)
                legend_width = min(65, available_width * 0.2)
                map_width = available_width - legend_width - 8  # 8mm gap
                map_height = available_height
                
                legend_x = margin + map_width + 8
                legend_y = margin + header_height
                legend_height = available_height
            else:
                # Portrait: legend BELOW map, not overlapping
                legend_height_max = 70  # Max legend height
                
                # Recalculate: map takes most space, legend below
                map_width = available_width
                map_height = available_height - legend_height_max - 8  # 8mm gap
                
                legend_x = margin
                legend_y = margin + header_height + map_height + 8
                legend_width = available_width
                legend_height = legend_height_max
        else:
            # No legend: full space for map
            map_width = available_width
            map_height = available_height
        
        # === MAP ITEM ===
        map_item = QgsLayoutItemMap(layout)
        
        map_x = margin
        map_y = margin + header_height
        
        map_item.attemptResize(QgsLayoutSize(map_width, map_height, QgsUnitTypes.LayoutMillimeters))
        map_item.attemptMove(QgsLayoutPoint(map_x, map_y, QgsUnitTypes.LayoutMillimeters))
        
        # === SET MAP EXTENT - CRITICAL SECTION ===
        # Determine extent source
        if self.extent_canvas.isChecked():
            # Use current canvas extent
            from qgis.utils import iface
            source_extent = iface.mapCanvas().extent()
            print(f"DEBUG: Using canvas extent: {source_extent.toString()}")
        else:
            # Use layer extent (default)
            source_extent = layer.extent()
            print(f"DEBUG: Using layer extent: {source_extent.toString()}")
        
        # Store for calculations
        layer_extent = source_extent
        # Get FULL layer extent
        layer_extent = layer.extent()
        
        print(f"DEBUG: Layer extent: {layer_extent.toString()}")
        print(f"DEBUG: Layer extent size: {layer_extent.width()} x {layer_extent.height()} units")
        print(f"DEBUG: Map item size: {map_width} x {map_height} mm")
        
        # Calculate map aspect ratio (width/height)
        map_aspect = map_width / map_height
        
        # Calculate layer extent aspect ratio
        layer_aspect = layer_extent.width() / layer_extent.height()
        
        print(f"DEBUG: Map aspect ratio: {map_aspect:.3f}")
        print(f"DEBUG: Layer aspect ratio: {layer_aspect:.3f}")
        
        # Add buffer (2%)
        buffer = 0.02
        
        # Adjust extent to match map aspect ratio
        if layer_aspect > map_aspect:
            # Layer is wider than map → expand height
            target_width = layer_extent.width() * (1 + buffer)
            target_height = target_width / map_aspect
            
            height_diff = target_height - layer_extent.height()
            
            adjusted_extent = QgsRectangle(
                layer_extent.xMinimum() - (layer_extent.width() * buffer / 2),
                layer_extent.yMinimum() - (height_diff / 2),
                layer_extent.xMaximum() + (layer_extent.width() * buffer / 2),
                layer_extent.yMaximum() + (height_diff / 2)
            )
        else:
            # Layer is taller than map → expand width
            target_height = layer_extent.height() * (1 + buffer)
            target_width = target_height * map_aspect
            
            width_diff = target_width - layer_extent.width()
            
            adjusted_extent = QgsRectangle(
                layer_extent.xMinimum() - (width_diff / 2),
                layer_extent.yMinimum() - (layer_extent.height() * buffer / 2),
                layer_extent.xMaximum() + (width_diff / 2),
                layer_extent.yMaximum() + (layer_extent.height() * buffer / 2)
            )
        
        print(f"DEBUG: Adjusted extent: {adjusted_extent.toString()}")
        print(f"DEBUG: Adjusted size: {adjusted_extent.width()} x {adjusted_extent.height()} units")
        
        # Set extent on map item
        map_item.setExtent(adjusted_extent)
        
        # Force refresh
        map_item.refresh()
        
        # Set scale if specified
        target_scale = self.scale_combo.currentData()
        if target_scale > 0:
            print(f"DEBUG: User wants target scale: 1:{target_scale}")
            
            # IMPORTANT: Set scale AFTER extent
            # Scale will be applied but extent center is preserved
            center = adjusted_extent.center()
            map_item.setScale(target_scale)
            
            # Recalculate extent at new scale, keeping center
            new_extent = map_item.extent()
            
            # Adjust to center on original point
            dx = center.x() - new_extent.center().x()
            dy = center.y() - new_extent.center().y()
            
            final_extent = QgsRectangle(
                new_extent.xMinimum() + dx,
                new_extent.yMinimum() + dy,
                new_extent.xMaximum() + dx,
                new_extent.yMaximum() + dy
            )
            
            map_item.setExtent(final_extent)
            print(f"DEBUG: Applied scale 1:{target_scale}, recentered extent")
        else:
            print(f"DEBUG: Using auto scale based on extent")
        
        final_scale = map_item.scale()
        print(f"DEBUG: Final map scale: 1:{int(final_scale)}")
        
        layout.addLayoutItem(map_item)
        
        print(f"DEBUG: Map extent set to layer bounds: {layer_extent.toString()}")
        print(f"DEBUG: Map size: {map_width}x{map_height} mm")
        print(f"DEBUG: Map scale: 1:{int(map_item.scale())}")
        
        # === TITLE ===
        if title:
            title_item = QgsLayoutItemLabel(layout)
            title_item.setText(title)
            
            title_font = QFont('Arial', 18, QFont.Bold)
            title_item.setFont(title_font)
            title_item.setHAlign(Qt.AlignHCenter)
            
            title_item.attemptResize(QgsLayoutSize(width - 2*margin, title_height, QgsUnitTypes.LayoutMillimeters))
            title_item.attemptMove(QgsLayoutPoint(margin, margin, QgsUnitTypes.LayoutMillimeters))
            
            layout.addLayoutItem(title_item)
        
        # === SUBTITLE ===
        if subtitle:
            subtitle_item = QgsLayoutItemLabel(layout)
            subtitle_item.setText(subtitle)
            
            subtitle_font = QFont('Arial', 11)
            subtitle_item.setFont(subtitle_font)
            subtitle_item.setHAlign(Qt.AlignHCenter)
            
            subtitle_y = margin + title_height + 2
            
            subtitle_item.attemptResize(QgsLayoutSize(width - 2*margin, subtitle_height, QgsUnitTypes.LayoutMillimeters))
            subtitle_item.attemptMove(QgsLayoutPoint(margin, subtitle_y, QgsUnitTypes.LayoutMillimeters))
            
            layout.addLayoutItem(subtitle_item)
        
        # === LEGEND ===
        if self.legend_check.isChecked():
            legend = QgsLayoutItemLegend(layout)
            legend.setTitle('')
            legend.setLinkedMap(map_item)
            
            # Filter to current layer only
            legend.setAutoUpdateModel(False)
            model = legend.model()
            root_group = model.rootGroup()
            root_group.clear()
            root_group.addLayer(layer)
            legend.updateLegend()
            
            # Set font
            legend_font = QFont('Arial', 9)
            legend.setStyleFont(QgsLegendStyle.Title, legend_font)
            legend.setStyleFont(QgsLegendStyle.Group, legend_font)
            legend.setStyleFont(QgsLegendStyle.Subgroup, legend_font)
            legend.setStyleFont(QgsLegendStyle.SymbolLabel, legend_font)
            
            # Position
            legend.attemptMove(QgsLayoutPoint(legend_x, legend_y, QgsUnitTypes.LayoutMillimeters))
            
            if landscape:
                legend.attemptResize(QgsLayoutSize(legend_width, legend_height, QgsUnitTypes.LayoutMillimeters))
            else:
                legend.attemptResize(QgsLayoutSize(legend_width, legend_height, QgsUnitTypes.LayoutMillimeters))
            
            legend.adjustBoxSize()
            
            print(f"DEBUG: Legend positioned at x={legend_x}, y={legend_y}, size={legend_width}x{legend_height}mm")
            print(f"DEBUG: Map ends at y={map_y + map_height}mm, legend starts at y={legend_y}mm")
            
            layout.addLayoutItem(legend)
            
            print(f"DEBUG: Legend positioned at ({legend_x}, {legend_y})")
        
        # === SCALE BAR ===
        if self.scale_bar_check.isChecked():
            from qgis.core import QgsLayoutItemScaleBar
            
            scale_bar = QgsLayoutItemScaleBar(layout)
            scale_bar.setLinkedMap(map_item)
            
            # === CRITICAL: Get actual map scale ===
            current_map_scale = map_item.scale()
            print(f"DEBUG: Current map scale: 1:{int(current_map_scale)}")
            
            # === Calculate appropriate segment size ===
            # Based on map scale, determine nice round numbers
            
            if current_map_scale < 10000:
                segment_km = 1
            elif current_map_scale < 25000:
                segment_km = 2
            elif current_map_scale < 50000:
                segment_km = 5
            elif current_map_scale < 100000:
                segment_km = 10
            elif current_map_scale < 250000:          
                segment_km = 20
            elif current_map_scale < 500000:
                segment_km = 30
            else:
                segment_km = 50
            
            print(f"DEBUG: Segment size: {segment_km} km")
            
            # === UNITS SETUP ===
            scale_bar.setUnits(QgsUnitTypes.DistanceKilometers)
            scale_bar.setUnitLabel('km')
            
            # Set segment size (in kilometers)
            scale_bar.setUnitsPerSegment(segment_km)
            
            # === STYLE ===
            # Line Ticks Below style - cleanest and most standard
            scale_bar.setStyle('Line Ticks Down')
            
            # Number of segments
            scale_bar.setNumberOfSegments(2)  # Show 2 segments (0-X-2X)
            scale_bar.setNumberOfSegmentsLeft(0)
            
            # === APPEARANCE ===
            scale_bar.setHeight(3)  # Bar height
            scale_bar.setLineWidth(0.3)  # Line thickness
            
            # Tick height
            from qgis.core import QgsLayoutMeasurement
            scale_bar.setSubdivisionsHeight(1.5)  # Tick marks height
            
            # Font
            scale_bar_font = QFont('Arial', 9)
            scale_bar.setFont(scale_bar_font)
            
            # Label position
            scale_bar.setLabelVerticalPlacement(QgsScaleBarSettings.LabelBelowSegment)
            scale_bar.setLabelHorizontalPlacement(QgsScaleBarSettings.LabelCenteredEdge)
            
            # === POSITION ===
            scale_bar_x = margin + 3
            scale_bar_y = height - margin - 12
            
            scale_bar.attemptMove(QgsLayoutPoint(scale_bar_x, scale_bar_y, QgsUnitTypes.LayoutMillimeters))
            # Maximum width: 40% of available width (leave room for scale text)
            max_scale_bar_width = available_width * 0.4
            # Size - let it auto-size based on scale
            scale_bar.attemptResize(QgsLayoutSize(max_scale_bar_width, 12, QgsUnitTypes.LayoutMillimeters))
            
            # Force update
            scale_bar.refresh()
            
            layout.addLayoutItem(scale_bar)
            
            print(f"DEBUG: Scale bar added - {segment_km}km per segment")
        # === SCALE TEXT ===
        if self.scale_text_check.isChecked():
            scale_text = QgsLayoutItemLabel(layout)
            
            # Get ACTUAL scale from map (after all adjustments)
            current_scale = int(map_item.scale())
            scale_text.setText(f'Scale 1:{current_scale:,}')
            
            scale_font = QFont('Arial', 9)
            scale_text.setFont(scale_font)
            scale_text.setHAlign(Qt.AlignRight)  # ← RIGHT align
            
            # Position at BOTTOM RIGHT (opposite of scale bar)
            scale_text_width = 70
            scale_text_x = width - margin - scale_text_width
            scale_text_y = height - margin - 8
            
            scale_text.attemptResize(QgsLayoutSize(scale_text_width, 8, QgsUnitTypes.LayoutMillimeters))
            scale_text.attemptMove(QgsLayoutPoint(scale_text_x, scale_text_y, QgsUnitTypes.LayoutMillimeters))
            
            layout.addLayoutItem(scale_text)
        
        # === NORTH ARROW ===
        if self.north_arrow_check.isChecked():
            from qgis.core import QgsLayoutItemPicture
            
            north_arrow = QgsLayoutItemPicture(layout)
            
            # Try to load north arrow SVG
            svg_path = ':/images/north_arrows/layout_default_north_arrow.svg'
            north_arrow.setPicturePath(svg_path)
            
            # Position at top right of map
            arrow_size = 15
            arrow_x = map_x + map_width - arrow_size - 8
            arrow_y = map_y + 8
            
            north_arrow.attemptResize(QgsLayoutSize(arrow_size, arrow_size, QgsUnitTypes.LayoutMillimeters))
            north_arrow.attemptMove(QgsLayoutPoint(arrow_x, arrow_y, QgsUnitTypes.LayoutMillimeters))
            
            layout.addLayoutItem(north_arrow)
        
        # === ATTRIBUTION ===
        attribution_text = self.attribution_edit.text()
        if attribution_text:
            attribution = QgsLayoutItemLabel(layout)
            attribution.setText(attribution_text)
            
            attrib_font = QFont('Arial', 8)
            attribution.setFont(attrib_font)
            attribution.setHAlign(Qt.AlignRight)
            
            attrib_y = height - margin - 5
            
            attribution.attemptResize(QgsLayoutSize(available_width, 8, QgsUnitTypes.LayoutMillimeters))
            attribution.attemptMove(QgsLayoutPoint(margin, attrib_y, QgsUnitTypes.LayoutMillimeters))
            
            layout.addLayoutItem(attribution)
        
        # Add to project
        project.layoutManager().addLayout(layout)
        
        print(f"DEBUG: Layout '{layout_name}' created with {len(layout.items())} items")
        
        return layout
    
    def _export_layout(self, layout, output_path, format_type):
        """
        Export layout to file.
        
        Args:
            layout: QgsPrintLayout
            output_path: Output file path
            format_type: 'png' | 'pdf' | 'svg'
        
        Returns:
            bool: Success status
        """
        from qgis.core import QgsLayoutExporter
        
        exporter = QgsLayoutExporter(layout)
        
        try:
            if format_type == 'png':
                settings = QgsLayoutExporter.ImageExportSettings()
                settings.dpi = 300
                
                result = exporter.exportToImage(output_path, settings)
                
                if result == QgsLayoutExporter.Success:
                    print(f"DEBUG: Exported PNG to {output_path}")
                    return True
                else:
                    print(f"ERROR: PNG export failed with code {result}")
                    return False
            
            elif format_type == 'pdf':
                settings = QgsLayoutExporter.PdfExportSettings()
                settings.dpi = 300
                settings.rasterizeWholeImage = False
                
                result = exporter.exportToPdf(output_path, settings)
                
                if result == QgsLayoutExporter.Success:
                    print(f"DEBUG: Exported PDF to {output_path}")
                    return True
                else:
                    print(f"ERROR: PDF export failed with code {result}")
                    return False
            
            elif format_type == 'svg':
                settings = QgsLayoutExporter.SvgExportSettings()
                settings.dpi = 300
                
                result = exporter.exportToSvg(output_path, settings)
                
                if result == QgsLayoutExporter.Success:
                    print(f"DEBUG: Exported SVG to {output_path}")
                    return True
                else:
                    print(f"ERROR: SVG export failed with code {result}")
                    return False
        
        except Exception as e:
            print(f"ERROR: Export exception: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _browse_output(self):
        """Browse for output location."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Save Map Output',
            '',
            'All Files (*)'
        )
        
        if filename:
            # Remove extension if provided
            base = os.path.splitext(filename)[0]
            self.output_path_edit.setText(base)
    
    def _generate_map(self):
        """Generate and export map."""
        layer = self.layer_combo.currentLayer()
        if not layer:
            QMessageBox.warning(self, 'No Layer', 'Please select a layer.')
            return
        
        field_name = self.field_combo.currentData()
        if not field_name:
            QMessageBox.warning(self, 'No Field', 'Please select a field.')
            return
        
        output_base = self.output_path_edit.text()
        if not output_base:
            QMessageBox.warning(self, 'No Output', 'Please specify output path.')
            return
        
        # Check at least one export format selected
        if not (self.export_png_check.isChecked() or 
                self.export_pdf_check.isChecked() or 
                self.export_svg_check.isChecked()):
            QMessageBox.warning(self, 'No Format', 'Please select at least one export format.')
            return
        
        self.progress_label.setText('⏳ Generating map...')
        self.generate_btn.setEnabled(False)
        QApplication.processEvents()
        
        try:
            # Step 1: Apply symbology
            self.progress_label.setText('⏳ Applying symbology...')
            QApplication.processEvents()
            
            self._apply_symbology(layer, field_name)
            
            # Step 2: Create layout
            self.progress_label.setText('⏳ Creating layout...')
            QApplication.processEvents()
            
            layout = self._create_layout(layer)
            
            # Step 3: Export
            exported_files = []
            
            if self.export_png_check.isChecked():
                self.progress_label.setText('⏳ Exporting PNG...')
                QApplication.processEvents()
                
                png_path = f'{output_base}.png'
                if self._export_layout(layout, png_path, 'png'):
                    exported_files.append(os.path.basename(png_path))
            
            if self.export_pdf_check.isChecked():
                self.progress_label.setText('⏳ Exporting PDF...')
                QApplication.processEvents()
                
                pdf_path = f'{output_base}.pdf'
                if self._export_layout(layout, pdf_path, 'pdf'):
                    exported_files.append(os.path.basename(pdf_path))
            
            if self.export_svg_check.isChecked():
                self.progress_label.setText('⏳ Exporting SVG...')
                QApplication.processEvents()
                
                svg_path = f'{output_base}.svg'
                if self._export_layout(layout, svg_path, 'svg'):
                    exported_files.append(os.path.basename(svg_path))
            
            # Success message
            files_list = '<br>'.join([f'• {f}' for f in exported_files])
            
            QMessageBox.information(
                self,
                '✅ Success!',
                f'<b>Map generated successfully!</b><br><br>'
                f'<b>Style applied to:</b> {layer.name()}<br>'
                f'<b>Layout created:</b> {layout.name()}<br><br>'
                f'<b>Files exported:</b><br>{files_list}'
            )
            
            self.progress_label.setText('✅ Map generated successfully!')
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to generate map:\n{str(e)}')
            self.progress_label.setText('❌ Error generating map')
            import traceback
            print(traceback.format_exc())
        
        finally:
            self.generate_btn.setEnabled(True)
