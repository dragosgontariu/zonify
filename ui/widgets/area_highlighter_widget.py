"""
Area Highlighter Widget for Zonify

Allows users to flag top/bottom performing areas based on percentiles.
Part of task-based UI for advanced analysis.

Example use case: Highlight top 10% solar potential sites as "High Priority"

Author: Dragos Gontariu
License: GPL-3.0
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QSpinBox, QMessageBox,
    QGroupBox, QApplication
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QFont
import json


class AreaHighlighterWidget(QWidget):
    """
    Widget for highlighting top/bottom performing areas.
    
    Signals:
        highlightingApplied: Emitted when highlighting is applied
    """
    
    highlightingApplied = pyqtSignal(dict)  # Emits highlighting config
    
    def __init__(self, parent=None):
        """
        Constructor.
        
        Args:
            parent: Parent widget (main dialog)
        """
        super(AreaHighlighterWidget, self).__init__(parent)
        
        self.parent_dialog = parent
        self.available_fields = []
        
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
            '<b>Highlighting areas in 3 steps:</b><br>'
            '&nbsp;&nbsp;1️⃣ <b>Select field:</b> Choose which indicator to analyze<br>'
            '&nbsp;&nbsp;2️⃣ <b>Configure:</b> Check top/bottom boxes, set percentage and labels<br>'
            '&nbsp;&nbsp;3️⃣ <b>Apply:</b> Select source layer and run highlighting<br><br>'
            '<i>💡 The output will have flag fields (1/0) to identify special areas!</i>'
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
            '<b style="color: #1976d2; font-size: 11pt;">📚 What is Highlighting?</b><br>'
            '<small style="color: gray;">'
            'Highlighting marks the best and worst performing areas based on percentile thresholds.<br><br>'
            
            '<b>🎯 Example Use Cases:</b><br>'
            '&nbsp;&nbsp;• <b>Priority Areas:</b> Top 10% solar potential → "High Priority Sites"<br>'
            '&nbsp;&nbsp;• <b>At-Risk Areas:</b> Bottom 20% accessibility → "Needs Improvement"<br>'
            '&nbsp;&nbsp;• <b>Investment Focus:</b> Top 5% ROI → "Prime Investment Zones"<br>'
            '&nbsp;&nbsp;• <b>Intervention Zones:</b> Bottom 15% health index → "Critical Areas"<br><br>'
            
            '<b>⚙️ How it Works:</b><br>'
            '&nbsp;&nbsp;• Values are ranked from lowest to highest<br>'
            '&nbsp;&nbsp;• Top X% = areas with highest values (best performers)<br>'
            '&nbsp;&nbsp;• Bottom X% = areas with lowest values (worst performers)<br>'
            '&nbsp;&nbsp;• Creates binary flags (1/0) for easy filtering in QGIS<br>'
            '&nbsp;&nbsp;• Text labels make maps readable for any audience<br><br>'
            
            '<b>💡 Tips for Best Results:</b><br>'
            '&nbsp;&nbsp;• Use 5-20% for focused attention (too many dilutes focus)<br>'
            '&nbsp;&nbsp;• Top % depends on use case: investment (5%), assistance (20%)<br>'
            '&nbsp;&nbsp;• Combine with classification for complete analysis<br>'
            '&nbsp;&nbsp;• Use meaningful labels your audience understands<br>'
            '&nbsp;&nbsp;• Create multiple variants to test different thresholds<br>'
            '&nbsp;&nbsp;• Remember: higher values = top performers (adjust field if needed)'
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
        step1_label = QLabel('<b>Step 1:</b> Select field to analyze')
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
        
        # === STEP 2: CONFIGURE HIGHLIGHTING ===
        step2_label = QLabel('<b>Step 2:</b> Configure highlighting')
        layout.addWidget(step2_label)
        
        # Top performers
        self.top_enabled = QCheckBox('Highlight top performers')
        self.top_enabled.setChecked(True)
        self.top_enabled.toggled.connect(self._on_top_toggled)
        layout.addWidget(self.top_enabled)
        
        self.top_widget = QWidget()
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(20, 0, 0, 0)
        
        top_layout.addWidget(QLabel('Top'))
        
        self.top_percent = QSpinBox()
        self.top_percent.setMinimum(1)
        self.top_percent.setMaximum(50)
        self.top_percent.setValue(10)
        self.top_percent.setSuffix('%')
        self.top_percent.setToolTip(
            '<b>Top Percentage:</b><br>'
            'Percentage of highest values to flag.<br>'
            'Example: 10% means top 10% of areas by value'
        )
        top_layout.addWidget(self.top_percent)
        
        top_layout.addWidget(QLabel('→ Label:'))
        
        self.top_label = QLineEdit()
        self.top_label.setPlaceholderText('e.g., High Priority, Best Sites')
        self.top_label.setText('High Priority')
        top_layout.addWidget(self.top_label)
        
        top_layout.addStretch()
        self.top_widget.setLayout(top_layout)
        layout.addWidget(self.top_widget)
        
        # Bottom performers
        self.bottom_enabled = QCheckBox('Highlight bottom performers')
        self.bottom_enabled.setChecked(True)
        self.bottom_enabled.toggled.connect(self._on_bottom_toggled)
        layout.addWidget(self.bottom_enabled)
        
        self.bottom_widget = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(20, 0, 0, 0)
        
        bottom_layout.addWidget(QLabel('Bottom'))
        
        self.bottom_percent = QSpinBox()
        self.bottom_percent.setMinimum(1)
        self.bottom_percent.setMaximum(50)
        self.bottom_percent.setValue(10)
        self.bottom_percent.setSuffix('%')
        self.bottom_percent.setToolTip(
            '<b>Bottom Percentage:</b><br>'
            'Percentage of lowest values to flag.<br>'
            'Example: 10% means bottom 10% of areas by value'
        )
        bottom_layout.addWidget(self.bottom_percent)
        
        bottom_layout.addWidget(QLabel('→ Label:'))
        
        self.bottom_label = QLineEdit()
        self.bottom_label.setPlaceholderText('e.g., Needs Attention, Critical')
        self.bottom_label.setText('Needs Attention')
        bottom_layout.addWidget(self.bottom_label)
        
        bottom_layout.addStretch()
        self.bottom_widget.setLayout(bottom_layout)
        layout.addWidget(self.bottom_widget)
        
        # Output fields info
        info_label = QLabel(
            '<small style="color: gray;">'
            '<b>Output fields created:</b><br>'
            '• <i>is_top_X</i> (1 = yes, 0 = no)<br>'
            '• <i>top_label</i> (text label or blank)<br>'
            '• <i>is_bottom_X</i> (1 = yes, 0 = no)<br>'
            '• <i>bottom_label</i> (text label or blank)'
            '</small>'
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # === STEP 3: SELECT SOURCE LAYER ===
        step3_label = QLabel('<b>Step 3:</b> Select source layer')
        layout.addWidget(step3_label)
        
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
        self.output_path_edit.setPlaceholderText('Will be auto-generated: source_layer_highlight_FieldName.gpkg')
        self.output_path_edit.setReadOnly(True)
        output_layout.addWidget(self.output_path_edit)
        
        self.browse_output_btn = QPushButton('📁 Browse')
        self.browse_output_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_output_btn)
        
        layout.addLayout(output_layout)
        
        # === APPLY BUTTON ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton('🏁 Apply Highlighting')
        self.apply_btn.setMinimumWidth(180)
        self.apply_btn.setStyleSheet(
            'QPushButton {'
            '  background-color: #9C27B0;'
            '  color: white;'
            '  padding: 8px;'
            '  font-weight: bold;'
            '  border-radius: 4px;'
            '}'
            'QPushButton:hover {'
            '  background-color: #7B1FA2;'
            '}'
            'QPushButton:disabled {'
            '  background-color: #cccccc;'
            '}'
        )
        self.apply_btn.clicked.connect(self._apply_highlighting)
        self.apply_btn.setEnabled(False)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
        
        # Progress indicator
        self.progress_label = QLabel('')
        self.progress_label.setStyleSheet('color: gray; font-style: italic;')
        layout.addWidget(self.progress_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
    
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
    
    def _on_top_toggled(self, checked):
        """Handle top checkbox toggle."""
        self.top_widget.setEnabled(checked)
        self._validate_inputs()
    
    def _on_bottom_toggled(self, checked):
        """Handle bottom checkbox toggle."""
        self.bottom_widget.setEnabled(checked)
        self._validate_inputs()
    
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
        
        new_filename = f"{base_name}_highlight_{field_name}.gpkg"
        new_path = os.path.join(base_dir, new_filename)
        
        self.output_path_edit.setText(new_path)
    
    def _browse_output(self):
        """Browse for output file."""
        from qgis.PyQt.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Save Highlighting Output',
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
        has_config = self.top_enabled.isChecked() or self.bottom_enabled.isChecked()
        
        self.apply_btn.setEnabled(has_field and has_layer and has_output and has_config)
    
    def _apply_highlighting(self):
        """Apply highlighting to selected layer."""
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
            QMessageBox.warning(self, 'No Field', 'Please select a field to analyze.')
            return
        
        if not source_layer:
            QMessageBox.warning(self, 'No Layer', 'Please select a source layer.')
            return
        
        if not output_path:
            QMessageBox.warning(self, 'No Output Path', 'Please specify output path.')
            return
        
        if not (self.top_enabled.isChecked() or self.bottom_enabled.isChecked()):
            QMessageBox.warning(
                self,
                'No Highlighting Configured',
                'Please enable at least Top or Bottom highlighting.'
            )
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
        self.progress_label.setText('⏳ Highlighting areas...')
        self.apply_btn.setEnabled(False)
        
        try:
            # Perform highlighting
            self._highlight_and_export(source_layer, field_name, output_path)
            
            # Success
            self.progress_label.setText('✅ Highlighting applied successfully!')
            
            flags_created = []
            if self.top_enabled.isChecked():
                flags_created.append(f'Top {self.top_percent.value()}%')
            if self.bottom_enabled.isChecked():
                flags_created.append(f'Bottom {self.bottom_percent.value()}%')
            
            QMessageBox.information(
                self,
                '✅ Success!',
                f'<b>Highlighting completed successfully!</b><br><br>'
                f'<b>Field analyzed:</b> {field_name}<br>'
                f'<b>Flags created:</b> {", ".join(flags_created)}<br>'
                f'<b>Output file:</b> {os.path.basename(output_path)}<br>'
                f'<b>Features processed:</b> {source_layer.featureCount()}<br><br>'
                f'<i>The new layer has been added to your QGIS project.<br>'
                f'Open the attribute table to see the flag fields!</i>'
            )
            
        except Exception as e:
            self.progress_label.setText('❌ Error during highlighting')
            QMessageBox.critical(self, 'Error', f'Failed to highlight:\n{str(e)}')
            import traceback
            print(traceback.format_exc())
        
        finally:
            self.apply_btn.setEnabled(True)
    
    def _highlight_and_export(self, source_layer, field_name, output_path):
        """Perform highlighting and export to new file."""
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
        output_layer = QgsVectorLayer(output_path, f'{field_name}_highlighted', 'ogr')
        
        if not output_layer.isValid():
            raise Exception("Failed to load output layer")
        
        output_layer.startEditing()
        
        # Add flag fields
        top_percent = self.top_percent.value()
        bottom_percent = self.bottom_percent.value()
        
        fields_to_add = []
        
        if self.top_enabled.isChecked():
            fields_to_add.append(QgsField(f'is_top_{top_percent}', QVariant.Int))
            fields_to_add.append(QgsField('top_label', QVariant.String))
        
        if self.bottom_enabled.isChecked():
            fields_to_add.append(QgsField(f'is_bottom_{bottom_percent}', QVariant.Int))
            fields_to_add.append(QgsField('bottom_label', QVariant.String))
        
        for field in fields_to_add:
            if output_layer.fields().indexOf(field.name()) == -1:
                output_layer.addAttribute(field)
        
        output_layer.updateFields()
        
        # Extract values
        field_idx = output_layer.fields().indexOf(field_name)
        if field_idx == -1:
            raise Exception(f"Field '{field_name}' not found in layer")

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

        values = np.array(values)
        
        # Calculate flags
        engine = PostProcessingEngine()
        
        flags = engine.flag_percentile(
            values,
            top_percent=top_percent if self.top_enabled.isChecked() else None,
            bottom_percent=bottom_percent if self.bottom_enabled.isChecked() else None
        )
        
        # Update features
        top_label_text = self.top_label.text() or 'High Priority'
        bottom_label_text = self.bottom_label.text() or 'Needs Attention'
        
        for i, feature_id in enumerate(feature_ids):
            if self.top_enabled.isChecked() and 'top' in flags:
                # Top flag
                top_flag_idx = output_layer.fields().indexOf(f'is_top_{top_percent}')
                top_label_idx = output_layer.fields().indexOf('top_label')
                
                is_top = int(flags['top'][i])
                output_layer.changeAttributeValue(feature_id, top_flag_idx, is_top)
                
                if is_top:
                    output_layer.changeAttributeValue(feature_id, top_label_idx, top_label_text)
                else:
                    output_layer.changeAttributeValue(feature_id, top_label_idx, '')
            
            if self.bottom_enabled.isChecked() and 'bottom' in flags:
                # Bottom flag
                bottom_flag_idx = output_layer.fields().indexOf(f'is_bottom_{bottom_percent}')
                bottom_label_idx = output_layer.fields().indexOf('bottom_label')
                
                is_bottom = int(flags['bottom'][i])
                output_layer.changeAttributeValue(feature_id, bottom_flag_idx, is_bottom)
                
                if is_bottom:
                    output_layer.changeAttributeValue(feature_id, bottom_label_idx, bottom_label_text)
                else:
                    output_layer.changeAttributeValue(feature_id, bottom_label_idx, '')
        
        print(f"DEBUG: Updated {len(feature_ids)} features with highlighting")
        
        # Commit changes
        print("DEBUG: Committing changes...")
        if not output_layer.commitChanges():
            errors = output_layer.commitErrors()
            raise Exception(f"Failed to commit changes: {errors}")
        
        print("DEBUG: Changes committed successfully")
        
        # Add to project
        print(f"DEBUG: Adding layer '{output_layer.name()}' to project...")
        QgsProject.instance().addMapLayer(output_layer)
        
        print("DEBUG: Layer added to project!")
    
    def get_configuration(self):
        """Get current highlighting configuration."""
        config = {
            'type': 'highlighting',
            'field': self.field_combo.currentText()
        }
        
        if self.top_enabled.isChecked():
            config['top_percent'] = self.top_percent.value()
            config['top_label'] = self.top_label.text()
        
        if self.bottom_enabled.isChecked():
            config['bottom_percent'] = self.bottom_percent.value()
            config['bottom_label'] = self.bottom_label.text()
        
        return config
