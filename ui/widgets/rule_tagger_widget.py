"""
Rule Tagger Widget for Zonify

Allows users to tag areas based on custom conditional rules.
Part of task-based UI for advanced analysis.

Example use case: Tag areas where flood > 2.0 AND population > 1000 as "High Risk"

Author: Dragos Gontariu
License: GPL-3.0
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QApplication, QDoubleSpinBox
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QFont
import json


class RuleTaggerWidget(QWidget):
    """
    Widget for tagging areas based on conditional rules.
    
    Signals:
        taggingApplied: Emitted when tagging is applied
    """
    
    taggingApplied = pyqtSignal(dict)  # Emits tagging config
    
    # Available operators
    OPERATORS = {
        'greater than': '>',
        'greater or equal': '>=',
        'less than': '<',
        'less or equal': '<=',
        'equal to': '==',
        'not equal': '!='
    }
    
    def __init__(self, parent=None):
        """
        Constructor.
        
        Args:
            parent: Parent widget (main dialog)
        """
        super(RuleTaggerWidget, self).__init__(parent)
        
        self.parent_dialog = parent
        self.available_fields = []
        self.conditions = []  # List of condition widgets
        
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
            '<b>Tagging areas in 4 steps:</b><br>'
            '&nbsp;&nbsp;1️⃣ <b>Build rule:</b> Add conditions (field, operator, value)<br>'
            '&nbsp;&nbsp;2️⃣ <b>Set logic:</b> Choose AND/OR between conditions<br>'
            '&nbsp;&nbsp;3️⃣ <b>Name tag:</b> Give it a meaningful name<br>'
            '&nbsp;&nbsp;4️⃣ <b>Apply:</b> Select source layer and run tagging<br><br>'
            '<i>💡 The output will have binary flags (1/0) for areas matching your rule!</i>'
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
            '<b style="color: #1976d2; font-size: 11pt;">📚 What is Rule-Based Tagging?</b><br>'
            '<small style="color: gray;">'
            'Tagging marks areas that meet specific criteria you define using conditional logic.<br><br>'
            
            '<b>🎯 Example Use Cases:</b><br>'
            '&nbsp;&nbsp;• <b>High Risk:</b> flood > 2.0 AND population > 1000 → "High Risk Areas"<br>'
            '&nbsp;&nbsp;• <b>Investment Zones:</b> ROI > 15% AND accessibility > 0.7 → "Prime Investment"<br>'
            '&nbsp;&nbsp;• <b>Priority Areas:</b> poverty > 0.5 OR health_index < 0.3 → "Needs Intervention"<br>'
            '&nbsp;&nbsp;• <b>Suitable Sites:</b> solar > 5 AND slope < 10 → "Excellent for Solar"<br><br>'
            
            '<b>⚙️ How it Works:</b><br>'
            '&nbsp;&nbsp;• Define conditions using your data fields (e.g., flood_risk > 2.0)<br>'
            '&nbsp;&nbsp;• Combine conditions with AND (all must match) or OR (any can match)<br>'
            '&nbsp;&nbsp;• Areas matching the rule get flagged with 1, others with 0<br>'
            '&nbsp;&nbsp;• Text labels make it easy to communicate findings<br>'
            '&nbsp;&nbsp;• Binary flags allow quick filtering in QGIS<br><br>'
            
            '<b>💡 Tips for Best Results:</b><br>'
            '&nbsp;&nbsp;• Start simple: 1-2 conditions, then add complexity if needed<br>'
            '&nbsp;&nbsp;• Use AND when all criteria must be met (strict matching)<br>'
            '&nbsp;&nbsp;• Use OR when any criterion is enough (flexible matching)<br>'
            '&nbsp;&nbsp;• Test with different thresholds to optimize results<br>'
            '&nbsp;&nbsp;• Combine multiple tags to create decision trees<br>'
            '&nbsp;&nbsp;• Name tags clearly: what they mean, not how they\'re calculated<br>'
            '&nbsp;&nbsp;• Review the preview to ensure your rule makes sense'
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
        
        # === STEP 1: BUILD RULE ===
        step1_label = QLabel('<b>Step 1:</b> Build your rule')
        layout.addWidget(step1_label)
        
        # Refresh fields button
        refresh_layout = QHBoxLayout()
        self.refresh_fields_btn = QPushButton('🔄 Refresh Available Fields')
        self.refresh_fields_btn.clicked.connect(self._refresh_fields)
        refresh_layout.addWidget(self.refresh_fields_btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        # Conditions table
        self.conditions_table = QTableWidget()
        self.conditions_table.setColumnCount(5)
        self.conditions_table.setHorizontalHeaderLabels(['Field', 'Operator', 'Value', 'Logic', ''])
        self.conditions_table.horizontalHeader().setStretchLastSection(False)
        self.conditions_table.setMaximumHeight(200)
        self.conditions_table.setAlternatingRowColors(True)
        layout.addWidget(self.conditions_table)
        
        # Add condition button
        add_layout = QHBoxLayout()
        self.add_condition_btn = QPushButton('+ Add Condition')
        self.add_condition_btn.clicked.connect(self._add_condition)
        add_layout.addWidget(self.add_condition_btn)
        add_layout.addStretch()
        layout.addLayout(add_layout)
        
        # Preview
        preview_label = QLabel('<b>Preview:</b> Flag areas where:')
        layout.addWidget(preview_label)
        
        self.preview_text = QLabel('<i style="color: gray;">Add conditions to see preview...</i>')
        self.preview_text.setWordWrap(True)
        self.preview_text.setStyleSheet('padding: 5px; background-color: #f9f9f9; border: 1px solid #ddd;')
        layout.addWidget(self.preview_text)
        
        # === STEP 2: NAME TAG ===
        step2_label = QLabel('<b>Step 2:</b> Name your tag')
        layout.addWidget(step2_label)
        
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel('Tag name:'))
        
        self.tag_name_edit = QLineEdit()
        self.tag_name_edit.setPlaceholderText('e.g., High_Risk, Priority_Zone, Suitable_Area')
        self.tag_name_edit.textChanged.connect(self._update_output_info)
        tag_layout.addWidget(self.tag_name_edit)
        
        layout.addLayout(tag_layout)
        
        # Output fields info
        self.output_info_label = QLabel(
            '<small style="color: gray;">'
            '<b>Output fields created:</b><br>'
            '• <i>TagName</i> (1 = matches rule, 0 = doesn\'t)<br>'
            '• <i>TagName_label</i> (text label or blank)'
            '</small>'
        )
        self.output_info_label.setWordWrap(True)
        layout.addWidget(self.output_info_label)
        
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
        self.output_path_edit.setPlaceholderText('Will be auto-generated: source_layer_tag_TagName.gpkg')
        self.output_path_edit.setReadOnly(True)
        output_layout.addWidget(self.output_path_edit)
        
        self.browse_output_btn = QPushButton('📁 Browse')
        self.browse_output_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_output_btn)
        
        layout.addLayout(output_layout)
        
        # === APPLY BUTTON ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton('🏷️ Apply Tagging')
        self.apply_btn.setMinimumWidth(180)
        self.apply_btn.setStyleSheet(
            'QPushButton {'
            '  background-color: #2196F3;'
            '  color: white;'
            '  padding: 8px;'
            '  font-weight: bold;'
            '  border-radius: 4px;'
            '}'
            'QPushButton:hover {'
            '  background-color: #1976D2;'
            '}'
            'QPushButton:disabled {'
            '  background-color: #cccccc;'
            '}'
        )
        self.apply_btn.clicked.connect(self._apply_tagging)
        self.apply_btn.setEnabled(False)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
        
        # Progress indicator
        self.progress_label = QLabel('')
        self.progress_label.setStyleSheet('color: gray; font-style: italic;')
        layout.addWidget(self.progress_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Add initial condition
        self._add_condition()
    
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
        
        # Update all field combos
        for row in range(self.conditions_table.rowCount()):
            field_combo = self.conditions_table.cellWidget(row, 0)
            if field_combo:
                current = field_combo.currentText()
                field_combo.clear()
                if self.available_fields:
                    field_combo.addItems(self.available_fields)
                    # Restore selection if still valid
                    idx = field_combo.findText(current)
                    if idx >= 0:
                        field_combo.setCurrentIndex(idx)
                else:
                    field_combo.addItem('(No fields available)')
    
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
    
    def _add_condition(self):
        """Add a new condition row."""
        row = self.conditions_table.rowCount()
        self.conditions_table.insertRow(row)
        
        # Field combo
        field_combo = QComboBox()
        if self.available_fields:
            field_combo.addItems(self.available_fields)
        else:
            field_combo.addItem('(No fields available)')
        field_combo.currentIndexChanged.connect(self._update_preview)
        self.conditions_table.setCellWidget(row, 0, field_combo)
        
        # Operator combo
        operator_combo = QComboBox()
        operator_combo.addItems(list(self.OPERATORS.keys()))
        operator_combo.currentIndexChanged.connect(self._update_preview)
        self.conditions_table.setCellWidget(row, 1, operator_combo)
        
        # Value spinbox
        value_spin = QDoubleSpinBox()
        value_spin.setMinimum(-999999)
        value_spin.setMaximum(999999)
        value_spin.setDecimals(2)
        value_spin.setValue(0.0)
        value_spin.valueChanged.connect(self._update_preview)
        self.conditions_table.setCellWidget(row, 2, value_spin)
        
        # Logic combo (only if not first row)
        if row > 0:
            logic_combo = QComboBox()
            logic_combo.addItems(['AND', 'OR'])
            logic_combo.currentIndexChanged.connect(self._update_preview)
            self.conditions_table.setCellWidget(row, 3, logic_combo)
        else:
            # First row has no logic
            label = QLabel('-')
            label.setAlignment(Qt.AlignCenter)
            self.conditions_table.setCellWidget(row, 3, label)
        
        # Remove button
        remove_btn = QPushButton('✖')
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda checked, r=row: self._remove_condition(r))
        self.conditions_table.setCellWidget(row, 4, remove_btn)
        
        # Adjust column widths
        self.conditions_table.setColumnWidth(0, 200)
        self.conditions_table.setColumnWidth(1, 120)
        self.conditions_table.setColumnWidth(2, 80)
        self.conditions_table.setColumnWidth(3, 60)
        self.conditions_table.setColumnWidth(4, 40)
        
        self._update_preview()
        self._validate_inputs()
    
    def _remove_condition(self, row):
        """Remove a condition row."""
        if self.conditions_table.rowCount() <= 1:
            QMessageBox.warning(
                self,
                'Cannot Remove',
                'Must have at least 1 condition.'
            )
            return
        
        self.conditions_table.removeRow(row)
        
        # Fix logic column for first row (should show '-')
        if self.conditions_table.rowCount() > 0:
            first_logic_widget = self.conditions_table.cellWidget(0, 3)
            if isinstance(first_logic_widget, QComboBox):
                label = QLabel('-')
                label.setAlignment(Qt.AlignCenter)
                self.conditions_table.setCellWidget(0, 3, label)
        
        self._update_preview()
        self._validate_inputs()
    
    def _update_preview(self):
        """Update the preview text."""
        if self.conditions_table.rowCount() == 0:
            self.preview_text.setText('<i style="color: gray;">Add conditions to see preview...</i>')
            return
        
        preview_parts = []
        
        for row in range(self.conditions_table.rowCount()):
            field_combo = self.conditions_table.cellWidget(row, 0)
            operator_combo = self.conditions_table.cellWidget(row, 1)
            value_spin = self.conditions_table.cellWidget(row, 2)
            logic_widget = self.conditions_table.cellWidget(row, 3)
            
            if not field_combo or not operator_combo or not value_spin:
                continue
            
            field = field_combo.currentText()
            operator = operator_combo.currentText()
            value = value_spin.value()
            
            # Add logic operator if not first row
            if row > 0 and isinstance(logic_widget, QComboBox):
                logic = logic_widget.currentText()
                preview_parts.append(f'<b>{logic}</b>')
            
            preview_parts.append(f'• {field} <b>{operator}</b> {value}')
        
        preview_html = '<br>'.join(preview_parts)
        self.preview_text.setText(preview_html)
    
    def _update_output_info(self):
        """Update output fields info based on tag name."""
        tag_name = self.tag_name_edit.text().strip() or 'TagName'
        
        self.output_info_label.setText(
            f'<small style="color: gray;">'
            f'<b>Output fields created:</b><br>'
            f'• <i>{tag_name}</i> (1 = matches rule, 0 = doesn\'t)<br>'
            f'• <i>{tag_name}_label</i> (text label or blank)'
            f'</small>'
        )
        
        self._update_output_path()
        self._validate_inputs()
    
    def _on_layer_selected(self, index):
        """Handle source layer selection."""
        # Auto-refresh fields when layer changes
        self._refresh_fields()
        self._update_output_path()
        self._validate_inputs()
    
    def _update_output_path(self):
        """Update output path based on source layer and tag name."""
        layer = self.source_layer_combo.currentLayer()
        tag_name = self.tag_name_edit.text().strip()
        
        if not layer or not tag_name:
            self.output_path_edit.clear()
            return
        
        import os
        source_path = layer.source()
        base_dir = os.path.dirname(source_path)
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        
        new_filename = f"{base_name}_tag_{tag_name}.gpkg"
        new_path = os.path.join(base_dir, new_filename)
        
        self.output_path_edit.setText(new_path)
    
    def _browse_output(self):
        """Browse for output file."""
        from qgis.PyQt.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Save Tagging Output',
            self.output_path_edit.text() or '',
            'GeoPackage (*.gpkg)'
        )
        
        if filename:
            self.output_path_edit.setText(filename)
    
    def _validate_inputs(self):
        """Validate inputs and enable/disable Apply button."""
        has_conditions = self.conditions_table.rowCount() > 0
        has_tag = bool(self.tag_name_edit.text().strip())
        has_layer = self.source_layer_combo.currentLayer() is not None
        has_output = bool(self.output_path_edit.text())
        
        self.apply_btn.setEnabled(has_conditions and has_tag and has_layer and has_output)
    
    def _apply_tagging(self):
        """Apply tagging to selected layer."""
        from qgis.core import (
            QgsVectorFileWriter, QgsVectorLayer, QgsField, 
            QgsProject, QgsCoordinateTransformContext
        )
        from qgis.PyQt.QtCore import QVariant
        import os
        
        tag_name = self.tag_name_edit.text().strip()
        source_layer = self.source_layer_combo.currentLayer()
        output_path = self.output_path_edit.text()
        
        # Validate
        if not tag_name:
            QMessageBox.warning(self, 'No Tag Name', 'Please enter a name for your tag.')
            return
        
        if self.conditions_table.rowCount() == 0:
            QMessageBox.warning(
                self,
                'No Conditions',
                'Please add at least 1 condition.'
            )
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
        self.progress_label.setText('⏳ Tagging areas...')
        self.apply_btn.setEnabled(False)
        
        try:
            # Perform tagging
            tagged_count = self._tag_and_export(source_layer, tag_name, output_path)
            
            # Success
            self.progress_label.setText(f'✅ {tagged_count} areas tagged successfully!')
            
            QMessageBox.information(
                self,
                '✅ Success!',
                f'<b>Tagging completed successfully!</b><br><br>'
                f'<b>Tag name:</b> {tag_name}<br>'
                f'<b>Areas tagged:</b> {tagged_count} of {source_layer.featureCount()}<br>'
                f'<b>Output file:</b> {os.path.basename(output_path)}<br><br>'
                f'<i>The new layer has been added to your QGIS project.<br>'
                f'Open the attribute table to see the tag fields!</i>'
            )
            
        except Exception as e:
            self.progress_label.setText('❌ Error during tagging')
            QMessageBox.critical(self, 'Error', f'Failed to tag:\n{str(e)}')
            import traceback
            print(traceback.format_exc())
        
        finally:
            self.apply_btn.setEnabled(True)
    
    def _tag_and_export(self, source_layer, tag_name, output_path):
        """Perform tagging and export to new file."""
        from qgis.core import (
            QgsVectorFileWriter, QgsVectorLayer, QgsField,
            QgsProject, QgsCoordinateTransformContext
        )
        from qgis.PyQt.QtCore import QVariant
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
        output_layer = QgsVectorLayer(output_path, f'{tag_name}_tagged', 'ogr')
        
        if not output_layer.isValid():
            raise Exception("Failed to load output layer")
        
        output_layer.startEditing()
        
        # Add tag fields
        if output_layer.fields().indexOf(tag_name) == -1:
            output_layer.addAttribute(QgsField(tag_name, QVariant.Int))
        
        label_field = f'{tag_name}_label'
        if output_layer.fields().indexOf(label_field) == -1:
            output_layer.addAttribute(QgsField(label_field, QVariant.String))
        
        output_layer.updateFields()
        
        # Get conditions
        conditions = self._get_conditions()
        
        print(f"DEBUG: Evaluating {len(conditions)} conditions")
        
        # Evaluate rule for each feature
        tag_field_idx = output_layer.fields().indexOf(tag_name)
        label_field_idx = output_layer.fields().indexOf(label_field)
        
        tagged_count = 0
        
        for feature in output_layer.getFeatures():
            matches = self._evaluate_rule(feature, conditions, output_layer)
            
            if matches:
                output_layer.changeAttributeValue(feature.id(), tag_field_idx, 1)
                output_layer.changeAttributeValue(feature.id(), label_field_idx, tag_name)
                tagged_count += 1
            else:
                output_layer.changeAttributeValue(feature.id(), tag_field_idx, 0)
                output_layer.changeAttributeValue(feature.id(), label_field_idx, '')
        
        print(f"DEBUG: Tagged {tagged_count} features")
        
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
        
        return tagged_count
    
    def _get_conditions(self):
        """Extract conditions from table."""
        conditions = []
        
        for row in range(self.conditions_table.rowCount()):
            field_combo = self.conditions_table.cellWidget(row, 0)
            operator_combo = self.conditions_table.cellWidget(row, 1)
            value_spin = self.conditions_table.cellWidget(row, 2)
            logic_widget = self.conditions_table.cellWidget(row, 3)
            
            if not field_combo or not operator_combo or not value_spin:
                continue
            
            condition = {
                'field': field_combo.currentText(),
                'operator': self.OPERATORS[operator_combo.currentText()],
                'value': value_spin.value()
            }
            
            if row > 0 and isinstance(logic_widget, QComboBox):
                condition['logic'] = logic_widget.currentText()
            
            conditions.append(condition)
        
        return conditions
    
    def _evaluate_rule(self, feature, conditions, layer):
        """Evaluate if feature matches the rule."""
        if not conditions:
            return False
        
        # Evaluate first condition
        first_cond = conditions[0]
        result = self._evaluate_condition(feature, first_cond, layer)
        
        # Evaluate remaining conditions with logic
        for i in range(1, len(conditions)):
            cond = conditions[i]
            cond_result = self._evaluate_condition(feature, cond, layer)
            
            logic = cond.get('logic', 'AND')
            
            if logic == 'AND':
                result = result and cond_result
            elif logic == 'OR':
                result = result or cond_result
        
        return result
    
    def _evaluate_condition(self, feature, condition, layer):
        """Evaluate a single condition."""
        field_name = condition['field']
        operator = condition['operator']
        threshold = condition['value']
        
        # Get field index
        field_idx = layer.fields().indexOf(field_name)
        if field_idx == -1:
            print(f"WARNING: Field '{field_name}' not found")
            return False
        
        # Get value
        value = feature[field_idx]
        if value is None:
            return False
        
        try:
            value = float(value)
        except (ValueError, TypeError):
            return False
        
        # Evaluate operator
        if operator == '>':
            return value > threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '<':
            return value < threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '==':
            return abs(value - threshold) < 0.0001  # Floating point comparison
        elif operator == '!=':
            return abs(value - threshold) >= 0.0001
        
        return False
    
    def get_configuration(self):
        """Get current tagging configuration."""
        return {
            'type': 'tagging',
            'tag_name': self.tag_name_edit.text().strip(),
            'conditions': self._get_conditions()
        }
