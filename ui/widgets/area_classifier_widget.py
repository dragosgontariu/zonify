"""
Area Classifier Widget for Zonify

Allows users to classify continuous values into discrete categories.
Part of task-based UI for advanced analysis.

Example use case: Classify flood risk into Low/Medium/High categories

Author: Dragos Gontariu
License: GPL-3.0
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QRadioButton, QButtonGroup, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QApplication
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QFont
import json


class AreaClassifierWidget(QWidget):
    """
    Widget for classifying continuous values into categories.
    
    Signals:
        classificationApplied: Emitted when classification is applied
    """
    
    classificationApplied = pyqtSignal(dict)  # Emits classification config
    
    # Predefined class configurations
    CLASS_PRESETS = {
        3: ['Low', 'Medium', 'High'],
        5: ['Very Low', 'Low', 'Medium', 'High', 'Very High']
    }
    
    def __init__(self, parent=None):
        """
        Constructor.
        
        Args:
            parent: Parent widget (main dialog)
        """
        super(AreaClassifierWidget, self).__init__(parent)
        
        self.parent_dialog = parent
        self.available_fields = []
        self.custom_breaks = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # === EXPANDABLE HELP SECTION ===
        
        # Toggle button
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
        
        # Help content (initially hidden)
        self.help_content = QWidget()
        help_layout = QVBoxLayout()
        help_layout.setContentsMargins(15, 10, 15, 10)
        
        # Quick Guide section
        quick_guide = QLabel(
            '<b style="color: #1976d2; font-size: 11pt;">🎯 Quick Start Guide</b><br>'
            '<small>'
            '<b>Classifying values in 4 steps:</b><br>'
            '&nbsp;&nbsp;1️⃣ <b>Select field:</b> Choose which indicator to classify<br>'
            '&nbsp;&nbsp;2️⃣ <b>Choose method:</b> Pick how to group values (Natural Breaks recommended)<br>'
            '&nbsp;&nbsp;3️⃣ <b>Configure classes:</b> Set number and labels (3-5 classes work best)<br>'
            '&nbsp;&nbsp;4️⃣ <b>Apply:</b> Select source layer and run classification<br><br>'
            '<i>💡 The output will be a new file with a classification column!</i>'
            '</small>'
        )
        quick_guide.setWordWrap(True)
        help_layout.addWidget(quick_guide)
        
        # Separator
        from qgis.PyQt.QtWidgets import QFrame
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        help_layout.addWidget(line)
        
        # Detailed help
        detailed_help = QLabel(
            '<b style="color: #1976d2; font-size: 11pt;">📚 What is Classification?</b><br>'
            '<small style="color: gray;">'
            'Classification groups continuous values into discrete categories for easier interpretation.<br><br>'
            
            '<b>🎯 Example Use Cases:</b><br>'
            '&nbsp;&nbsp;• <b>Risk Classification:</b> Group flood risk values into Low/Medium/High categories<br>'
            '&nbsp;&nbsp;• <b>Land Suitability:</b> Classify areas as Unsuitable/Moderate/Suitable/Excellent<br>'
            '&nbsp;&nbsp;• <b>Priority Levels:</b> Categorize interventions by urgency (1-5 stars)<br><br>'
            
            '<b>⚙️ Classification Methods:</b><br>'
            '&nbsp;&nbsp;• <b>Equal Intervals:</b> Divides range into equal parts (good for uniform distributions)<br>'
            '&nbsp;&nbsp;• <b>Quantiles:</b> Equal number of features per class (good for skewed data)<br>'
            '&nbsp;&nbsp;• <b>Natural Breaks (Jenks):</b> Finds natural groupings in data (best for most cases)<br>'
            '&nbsp;&nbsp;• <b>Custom Breaks:</b> You define exact thresholds for precise control<br><br>'
            
            '<b>💡 Tips for Best Results:</b><br>'
            '&nbsp;&nbsp;• Use 3-5 classes for clarity (too many confuses interpretation)<br>'
            '&nbsp;&nbsp;• Choose Natural Breaks when unsure - it works well for most data<br>'
            '&nbsp;&nbsp;• Label classes meaningfully for your audience<br>'
            '&nbsp;&nbsp;• Test different methods to see which tells your story best<br>'
            '&nbsp;&nbsp;• Consider your audience: simple labels for general public, technical for experts'
            '</small>'
        )
        detailed_help.setWordWrap(True)
        help_layout.addWidget(detailed_help)
        
        self.help_content.setLayout(help_layout)
        self.help_content.setVisible(False)  # Start hidden
        self.help_content.setStyleSheet(
            'QWidget {'
            '  background-color: #f5f5f5;'
            '  border: 1px solid #e0e0e0;'
            '  border-radius: 4px;'
            '}'
        )
        layout.addWidget(self.help_content)
        
        # Connect toggle
        self.help_toggle_btn.toggled.connect(self._toggle_help)
        
        # === STEP 1: SELECT FIELD ===
        step1_label = QLabel('<b>Step 1:</b> Select field to classify')
        layout.addWidget(step1_label)
        
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel('Field:'))
        
        self.field_combo = QComboBox()
        self.field_combo.setMinimumWidth(300)
        self.field_combo.currentIndexChanged.connect(self._on_field_selected)
        field_layout.addWidget(self.field_combo)
        
        self.refresh_fields_btn = QPushButton('🔄 Refresh')
        self.refresh_fields_btn.clicked.connect(self._refresh_fields)
        field_layout.addWidget(self.refresh_fields_btn)
        
        field_layout.addStretch()
        layout.addLayout(field_layout)
        
        # === STEP 2: CHOOSE METHOD ===
        step2_label = QLabel('<b>Step 2:</b> Choose classification method')
        layout.addWidget(step2_label)
        
        self.method_group = QButtonGroup()
        method_layout = QVBoxLayout()
        
        self.method_equal = QRadioButton('Equal Intervals')
        self.method_equal.setToolTip(
            '<b>Equal Intervals:</b><br>'
            'Divides the range into equal-sized intervals.<br>'
            'Best for: Uniformly distributed data'
        )
        self.method_group.addButton(self.method_equal, 0)
        method_layout.addWidget(self.method_equal)
        
        self.method_quantile = QRadioButton('Quantiles (Equal Count)')
        self.method_quantile.setToolTip(
            '<b>Quantiles:</b><br>'
            'Each class contains equal number of features.<br>'
            'Best for: Skewed data distributions'
        )
        self.method_group.addButton(self.method_quantile, 1)
        method_layout.addWidget(self.method_quantile)
        
        self.method_jenks = QRadioButton('Natural Breaks (Jenks)')
        self.method_jenks.setToolTip(
            '<b>Natural Breaks (Jenks):</b><br>'
            'Finds natural groupings in data by minimizing variance within classes.<br>'
            'Best for: Most real-world data (recommended)'
        )
        self.method_jenks.setChecked(True)
        self.method_group.addButton(self.method_jenks, 2)
        method_layout.addWidget(self.method_jenks)
        
        self.method_custom = QRadioButton('Custom Breaks')
        self.method_custom.setToolTip(
            '<b>Custom Breaks:</b><br>'
            'Define your own break points for precise control.<br>'
            'Best for: When you have specific thresholds (e.g., policy limits)'
        )
        self.method_group.addButton(self.method_custom, 3)
        method_layout.addWidget(self.method_custom)
        
        layout.addLayout(method_layout)
        
        # Connect method change
        self.method_group.buttonClicked.connect(self._on_method_changed)
        
        # === STEP 3: CONFIGURE CLASSES ===
        step3_label = QLabel('<b>Step 3:</b> Configure classes')
        layout.addWidget(step3_label)
        
        # Number of classes (for non-custom methods)
        self.classes_widget = QWidget()
        classes_layout = QHBoxLayout()
        classes_layout.setContentsMargins(0, 0, 0, 0)
        classes_layout.addWidget(QLabel('Number of classes:'))
        
        self.num_classes_combo = QComboBox()
        self.num_classes_combo.addItems(['3', '5'])
        self.num_classes_combo.currentIndexChanged.connect(self._on_num_classes_changed)
        classes_layout.addWidget(self.num_classes_combo)
        
        classes_layout.addStretch()
        self.classes_widget.setLayout(classes_layout)
        layout.addWidget(self.classes_widget)
        
        # Custom breaks input (for custom method)
        self.breaks_widget = QWidget()
        breaks_layout = QVBoxLayout()
        breaks_layout.setContentsMargins(0, 0, 0, 0)
        
        breaks_header = QHBoxLayout()
        breaks_header.addWidget(QLabel('Break points:'))
        add_break_btn = QPushButton('+ Add Break')
        add_break_btn.clicked.connect(self._add_break_point)
        breaks_header.addWidget(add_break_btn)
        breaks_header.addStretch()
        breaks_layout.addLayout(breaks_header)
        
        self.breaks_table = QTableWidget()
        self.breaks_table.setColumnCount(2)
        self.breaks_table.setHorizontalHeaderLabels(['Break Value', ''])
        self.breaks_table.horizontalHeader().setStretchLastSection(False)
        self.breaks_table.setMaximumHeight(150)
        breaks_layout.addWidget(self.breaks_table)
        
        self.breaks_widget.setLayout(breaks_layout)
        self.breaks_widget.setVisible(False)
        layout.addWidget(self.breaks_widget)
        
        # Class labels
        labels_label = QLabel('Class labels:')
        layout.addWidget(labels_label)
        
        self.labels_table = QTableWidget()
        self.labels_table.setColumnCount(2)
        self.labels_table.setHorizontalHeaderLabels(['Class', 'Label'])
        self.labels_table.horizontalHeader().setStretchLastSection(True)
        self.labels_table.setMaximumHeight(150)
        layout.addWidget(self.labels_table)
        
        # === STEP 4: SELECT SOURCE LAYER ===
        step4_label = QLabel('<b>Step 4:</b> Select source layer')
        layout.addWidget(step4_label)
        
        layer_layout = QHBoxLayout()
        layer_layout.addWidget(QLabel('Source layer:'))
        
        from qgis.gui import QgsMapLayerComboBox
        from qgis.core import QgsMapLayerProxyModel
        
        self.source_layer_combo = QgsMapLayerComboBox()
        self.source_layer_combo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.source_layer_combo.setCurrentIndex(-1)
        self.source_layer_combo.currentIndexChanged.connect(self._on_layer_selected)
        layer_layout.addWidget(self.source_layer_combo)
        
        layout.addLayout(layer_layout)
        
        # Output path
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel('Output:'))
        
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText('Will be auto-generated: source_layer_class_FieldName.gpkg')
        self.output_path_edit.setReadOnly(True)
        output_layout.addWidget(self.output_path_edit)
        
        self.browse_output_btn = QPushButton('📁 Browse')
        self.browse_output_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_output_btn)
        
        layout.addLayout(output_layout)
        
        # === APPLY BUTTON ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton('🎨 Apply Classification')
        self.apply_btn.setMinimumWidth(180)
        self.apply_btn.setStyleSheet(
            'QPushButton {'
            '  background-color: #FF9800;'
            '  color: white;'
            '  padding: 8px;'
            '  font-weight: bold;'
            '  border-radius: 4px;'
            '}'
            'QPushButton:hover {'
            '  background-color: #F57C00;'
            '}'
            'QPushButton:disabled {'
            '  background-color: #cccccc;'
            '}'
        )
        self.apply_btn.clicked.connect(self._apply_classification)
        self.apply_btn.setEnabled(False)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
        
        # Progress indicator
        self.progress_label = QLabel('')
        self.progress_label.setStyleSheet('color: gray; font-style: italic;')
        layout.addWidget(self.progress_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Initialize
        self._populate_labels_table(3)
    
    def _toggle_help(self, checked):
        """Toggle help section visibility."""
        self.help_content.setVisible(checked)
        if checked:
            self.help_toggle_btn.setText('📚 Help & Guide (click to hide)')
        else:
            self.help_toggle_btn.setText('📚 Help & Guide (click to show)')
    
    def _refresh_fields(self):
        """Refresh available fields from Tab 1."""
        self.available_fields = self._get_available_fields()
        
        self.field_combo.clear()
        if self.available_fields:
            self.field_combo.addItems(self.available_fields)
        else:
            self.field_combo.addItem('(No fields available - process rasters first)')
    
    def _get_available_fields(self):
        """
        Get list of available fields from selected source layer.
        
        Returns:
            List of numeric field names from source layer
        """
        fields = []
        
        try:
            # Get selected source layer
            source_layer = self.source_layer_combo.currentLayer()
            
            if not source_layer:
                print("No source layer selected")
                return []
            
            # Get all numeric fields from layer
            layer_fields = source_layer.fields()
            
            for field in layer_fields:
                field_type = field.type()
                # QVariant types: 2=Int, 4=Double, 6=LongLong
                if field_type in [2, 4, 6]:
                    fields.append(field.name())
            
            print(f"Found {len(fields)} numeric fields in layer: {source_layer.name()}")
            return fields
            
        except Exception as e:
            print(f"Error getting available fields: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _on_field_selected(self, index):
        """Handle field selection."""
        self._update_output_path()
        self._validate_inputs()
    
    def _on_method_changed(self, button):
        """Handle classification method change."""
        is_custom = self.method_custom.isChecked()
        
        self.classes_widget.setVisible(not is_custom)
        self.breaks_widget.setVisible(is_custom)
        
        if is_custom:
            # Initialize with breaks if empty
            if self.breaks_table.rowCount() == 0:
                self._populate_breaks_table(2)  # Start with 3 classes (2 breaks)
        else:
            # Update labels based on selected number
            self._on_num_classes_changed(self.num_classes_combo.currentIndex())
        
        self._validate_inputs()
    
    def _on_num_classes_changed(self, index):
        """Handle number of classes change."""
        text = self.num_classes_combo.currentText()
        
        if text in ['3', '5']:
            n_classes = int(text)
            self._populate_labels_table(n_classes)
        else:  # Custom
            self._populate_labels_table(3)  # Start with 3
    
    def _populate_labels_table(self, n_classes):
        """Populate labels table with default labels."""
        self.labels_table.setRowCount(n_classes)
        
        labels = self.CLASS_PRESETS.get(n_classes, [f'Class {i+1}' for i in range(n_classes)])
        
        for i in range(n_classes):
            # Class number
            class_item = QTableWidgetItem(f'Class {i+1}')
            class_item.setFlags(Qt.ItemIsEnabled)
            self.labels_table.setItem(i, 0, class_item)
            
            # Label
            label_item = QTableWidgetItem(labels[i])
            self.labels_table.setItem(i, 1, label_item)
    
    def _populate_breaks_table(self, n_breaks):
        """Populate breaks table for custom method."""
        self.breaks_table.setRowCount(n_breaks)
        
        for i in range(n_breaks):
            # Break value
            value_item = QTableWidgetItem(str((i + 1) * 50.0))
            self.breaks_table.setItem(i, 0, value_item)
            
            # Remove button
            remove_btn = QPushButton('✖')
            remove_btn.setMaximumWidth(30)
            remove_btn.clicked.connect(lambda checked, row=i: self._remove_break_point(row))
            self.breaks_table.setCellWidget(i, 1, remove_btn)
    
    def _add_break_point(self):
        """Add a new break point."""
        row = self.breaks_table.rowCount()
        self.breaks_table.insertRow(row)
        
        # Default value
        value_item = QTableWidgetItem(str((row + 1) * 50.0))
        self.breaks_table.setItem(row, 0, value_item)
        
        # Remove button
        remove_btn = QPushButton('✖')
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda checked, r=row: self._remove_break_point(r))
        self.breaks_table.setCellWidget(row, 1, remove_btn)
        
        # Update labels
        self._populate_labels_table(row + 2)  # n_breaks + 1 classes
    
    def _remove_break_point(self, row):
        """Remove a break point."""
        if self.breaks_table.rowCount() <= 1:
            QMessageBox.warning(self, 'Cannot Remove', 'Must have at least 1 break point (2 classes).')
            return
        
        self.breaks_table.removeRow(row)
        
        # Update labels
        self._populate_labels_table(self.breaks_table.rowCount() + 1)
    
    def _on_layer_selected(self, index):
        """Handle source layer selection."""
        # Auto-refresh fields when layer changes
        self._refresh_fields()
        self._update_output_path()
        self._validate_inputs()
    
    def _update_output_path(self):
        """Update output path based on source layer and field."""
        layer = self.source_layer_combo.currentLayer()
        field_name = self.field_combo.currentText()
        
        if not layer or not field_name or field_name.startswith('('):
            self.output_path_edit.clear()
            return
        
        import os
        source_path = layer.source()
        base_dir = os.path.dirname(source_path)
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        
        new_filename = f"{base_name}_class_{field_name}.gpkg"
        new_path = os.path.join(base_dir, new_filename)
        
        self.output_path_edit.setText(new_path)
    
    def _browse_output(self):
        """Browse for output file."""
        from qgis.PyQt.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Save Classification Output',
            self.output_path_edit.text() or '',
            'GeoPackage (*.gpkg)'
        )
        
        if filename:
            self.output_path_edit.setText(filename)
    
    def _validate_inputs(self):
        """Validate inputs and enable/disable Apply button."""
        has_field = bool(self.field_combo.currentText() and 
                        not self.field_combo.currentText().startswith('('))
        has_layer = self.source_layer_combo.currentLayer() is not None
        has_output = bool(self.output_path_edit.text())
        
        self.apply_btn.setEnabled(has_field and has_layer and has_output)
    
    def _apply_classification(self):
        """Apply classification to selected layer."""
        from qgis.core import (
            QgsVectorFileWriter, QgsVectorLayer, QgsField, 
            QgsProject, QgsCoordinateTransformContext
        )
        from qgis.PyQt.QtCore import QVariant
        import os
        
        field_name = self.field_combo.currentText()
        source_layer = self.source_layer_combo.currentLayer()
        output_path = self.output_path_edit.text()
        
        # Validate
        if not field_name or field_name.startswith('('):
            QMessageBox.warning(self, 'No Field', 'Please select a field to classify.')
            return
        
        if not source_layer:
            QMessageBox.warning(self, 'No Layer', 'Please select a source layer.')
            return
        
        if not output_path:
            QMessageBox.warning(self, 'No Output Path', 'Please specify output path.')
            return
        
        # Check if output exists
        if os.path.exists(output_path):
            reply = QMessageBox.question(
                self,
                'File Exists',
                f'File {os.path.basename(output_path)} already exists.\nOverwrite?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            
            try:
                os.remove(output_path)
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Cannot remove existing file: {e}')
                return
        
        # Show progress
        self.progress_label.setText('⏳ Classifying values...')
        self.apply_btn.setEnabled(False)
        
        try:
            # Perform classification
            self._classify_and_export(source_layer, field_name, output_path)
            
            # Success
            self.progress_label.setText('✅ Classification applied successfully!')
            
            QMessageBox.information(
                self,
                '✅ Success!',
                f'<b>Classification completed successfully!</b><br><br>'
                f'<b>Field classified:</b> {field_name}<br>'
                f'<b>Output file:</b> {os.path.basename(output_path)}<br>'
                f'<b>Features processed:</b> {source_layer.featureCount()}<br><br>'
                f'<i>The new layer has been added to your QGIS project.<br>'
                f'Open the attribute table to see the classification column!</i>'
            )
            
        except Exception as e:
            self.progress_label.setText('❌ Error during classification')
            QMessageBox.critical(self, 'Error', f'Failed to classify:\n{str(e)}')
            import traceback
            print(traceback.format_exc())
        
        finally:
            self.apply_btn.setEnabled(True)
    
    def _classify_and_export(self, source_layer, field_name, output_path):
        """Perform classification and export to new file."""
        from qgis.core import (
            QgsVectorFileWriter, QgsVectorLayer, QgsField,
            QgsProject, QgsCoordinateTransformContext
        )
        from qgis.PyQt.QtCore import QVariant
        from ...algorithms.post_processing_engine import PostProcessingEngine
        import numpy as np
        
        # Copy layer
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'GPKG'
        
        error = QgsVectorFileWriter.writeAsVectorFormatV3(
            source_layer,
            output_path,
            QgsCoordinateTransformContext(),
            options
        )
        
        if error[0] != QgsVectorFileWriter.NoError:
            raise Exception(f"Failed to copy layer: {error[1]}")
        
        # Load new layer
        output_layer = QgsVectorLayer(output_path, f'{field_name}_classified', 'ogr')
        
        if not output_layer.isValid():
            raise Exception("Failed to load output layer")
        
        output_layer.startEditing()
        
        # Add classification field
        class_field_name = f'{field_name}_class'
        if output_layer.fields().indexOf(class_field_name) == -1:
            output_layer.addAttribute(QgsField(class_field_name, QVariant.String))
        output_layer.updateFields()
        
        # Extract values
        field_idx = output_layer.fields().indexOf(field_name)
        if field_idx == -1:
            raise Exception(f"Field '{field_name}' not found in layer")
        print(f"DEBUG: Field to classify: '{field_name}'")
        print(f"DEBUG: Field index: {field_idx}")
        print(f"DEBUG: All fields in layer: {[f.name() for f in output_layer.fields()]}")
        values = []
        feature_ids = []
        
        for feature in output_layer.getFeatures():
            feature_ids.append(feature.id())
            value = feature[field_idx]

            # Convert QVariant to native Python type
            from qgis.PyQt.QtCore import QVariant
            if isinstance(value, QVariant):
                if value.isNull():
                    value = None
                else:
                    value = value.value()

            # Convert to float
            if value is not None:
                try:
                    values.append(float(value))
                except (ValueError, TypeError):
                    # Invalid value - use NaN
                    values.append(np.nan)
            else:
                values.append(np.nan)
        print(f"DEBUG: Extracted {len(values)} values")
        print(f"DEBUG: First 5 values: {values[:5]}")
        print(f"DEBUG: Min/Max: {np.nanmin(values):.2f} / {np.nanmax(values):.2f}")
        values = np.array(values)
        
        # Get classification parameters
        method = self._get_selected_method()
        labels = self._get_class_labels()
        
        # Classify
        engine = PostProcessingEngine()
        
        if method in ['equal', 'quantile', 'jenks']:
            # For standard methods, use selected number of classes (3 or 5)
            num_classes_text = self.num_classes_combo.currentText()
            
            if num_classes_text == '3':
                n_classes = 3
                labels = ['Low', 'Medium', 'High']
            elif num_classes_text == '5':
                n_classes = 5
                labels = ['Very Low', 'Low', 'Medium', 'High', 'Very High']
            else:  # Custom for standard methods (shouldn't happen, but fallback)
                n_classes = len(self._get_class_labels())
                labels = self._get_class_labels()
            
            # Apply classification method
            if method == 'equal':
                class_labels, breaks = engine.classify_equal_intervals(values, n_classes, labels)
                print(f"DEBUG Equal: {n_classes} classes, {len(class_labels)} labels, sample: {class_labels[:5]}")
            
            elif method == 'quantile':
                class_labels, breaks = engine.classify_quantiles(values, n_classes, labels)
                print(f"DEBUG Quantile: {n_classes} classes, {len(class_labels)} labels, sample: {class_labels[:5]}")
            
            elif method == 'jenks':
                class_labels, breaks = engine.classify_jenks(values, n_classes, labels)
                print(f"DEBUG Jenks: {n_classes} classes, {len(class_labels)} labels, sample: {class_labels[:5]}")
                print(f"DEBUG Breaks: {breaks}")
        
        elif method == 'custom':
            # Custom method: user defines breaks and labels
            breaks = self._get_custom_breaks()
            labels = self._get_class_labels()
            class_labels = engine.classify_custom(values, breaks, labels)
            print(f"DEBUG Custom: {len(breaks)} breaks, {len(labels)} labels, sample: {class_labels[:5]}")
        
        # Verify labels
        print(f"Total features: {len(feature_ids)}")
        print(f"Total class_labels: {len(class_labels)}")
        print(f"Expected labels: {labels}")
        
        # Update features
        class_field_idx = output_layer.fields().indexOf(class_field_name)
        
        print(f"DEBUG: class_field_idx = {class_field_idx}")
        print(f"DEBUG: First 5 values to write: {[str(class_labels[i]) for i in range(min(5, len(class_labels)))]}")
        
        for i, feature_id in enumerate(feature_ids):
            # Convert numpy string to Python string
            value = str(class_labels[i]) if class_labels[i] is not None else None
            output_layer.changeAttributeValue(feature_id, class_field_idx, value)
            
            # Debug first few
            if i < 3:
                print(f"  Feature {feature_id}: set to '{value}'")
        
        print(f"DEBUG: Updated {len(feature_ids)} features")
        # COMMIT CHANGES
        print("DEBUG: Committing changes...")
        if not output_layer.commitChanges():
            errors = output_layer.commitErrors()
            raise Exception(f"Failed to commit changes: {errors}")
        
        print("DEBUG: Changes committed successfully")
        
        # ADD TO PROJECT
        print(f"DEBUG: Adding layer '{output_layer.name()}' to project...")
        QgsProject.instance().addMapLayer(output_layer)
        
        print("DEBUG: Layer added to project!")
        print(f"DEBUG: Total layers in project: {len(QgsProject.instance().mapLayers())}")
    
    def _get_selected_method(self):
        """Get selected classification method."""
        if self.method_equal.isChecked():
            return 'equal'
        elif self.method_quantile.isChecked():
            return 'quantile'
        elif self.method_jenks.isChecked():
            return 'jenks'
        elif self.method_custom.isChecked():
            return 'custom'
        return 'jenks'  # Default
    
    def _get_class_labels(self):
        """Get class labels from table."""
        labels = []
        for row in range(self.labels_table.rowCount()):
            label_item = self.labels_table.item(row, 1)
            if label_item:
                labels.append(label_item.text())
            else:
                labels.append(f'Class {row + 1}')
        return labels
    
    def _get_custom_breaks(self):
        """Get custom break points from table."""
        breaks = []
        for row in range(self.breaks_table.rowCount()):
            value_item = self.breaks_table.item(row, 0)
            if value_item:
                try:
                    breaks.append(float(value_item.text()))
                except ValueError:
                    breaks.append(50.0 * (row + 1))
        return sorted(breaks)
    
    def get_configuration(self):
        """Get current classification configuration."""
        return {
            'type': 'classification',
            'field': self.field_combo.currentText(),
            'method': self._get_selected_method(),
            'labels': self._get_class_labels()
        }
