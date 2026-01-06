"""
Score Creator Widget for Zonify

Allows users to create composite scores/indices from multiple indicators.
Part of task-based UI for advanced analysis.

Example use case: Risk score = flood_mean (High) + population (High) + elevation (Medium)

Author: Dragos Gontariu
License: GPL-3.0
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QApplication
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QFont
import json


class ScoreCreatorWidget(QWidget):
    """
    Widget for creating composite scores from multiple indicators.
    
    Signals:
        scoreConfigured: Emitted when a score is configured
    """
    
    scoreConfigured = pyqtSignal(dict)  # Emits score configuration
    
    # Importance mapping
    IMPORTANCE_WEIGHTS = {
        'Very High': 0.5,
        'High': 0.3,
        'Medium': 0.15,
        'Low': 0.05
    }
    
    def __init__(self, parent=None):
        """
        Constructor.
        
        Args:
            parent: Parent widget (main dialog)
        """
        super(ScoreCreatorWidget, self).__init__(parent)
        
        self.parent_dialog = parent
        self.available_fields = []
        self.selected_indicators = {}  # {field_name: importance_level}
        
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
            '<b>Creating a score in 3 simple steps:</b><br>'
            '&nbsp;&nbsp;1️⃣ <b>Select indicators:</b> Check 2+ fields and set their importance<br>'
            '&nbsp;&nbsp;2️⃣ <b>Name your score:</b> Give it a meaningful name (e.g., Risk_Score)<br>'
            '&nbsp;&nbsp;3️⃣ <b>Choose source & apply:</b> Select the layer to process and click Apply Score<br><br>'
            '<i>💡 The output will be a new file with your score added as a new column!</i>'
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
            '<b style="color: #1976d2; font-size: 11pt;">📚 What is a Score?</b><br>'
            '<small style="color: gray;">'
            'A score combines multiple indicators into a single value that helps you make decisions.<br><br>'
            
            '<b>🎯 Example Use Cases:</b><br>'
            '&nbsp;&nbsp;• <b>Risk Score:</b> flood (High) + population (High) + elevation (Medium) → identifies high-risk areas<br>'
            '&nbsp;&nbsp;• <b>Suitability Score:</b> solar radiation (Very High) + slope (High) → finds best locations for solar panels<br>'
            '&nbsp;&nbsp;• <b>Priority Score:</b> poverty (High) + accessibility (High) → prioritizes areas for development<br><br>'
            
            '<b>⚙️ How it Works:</b><br>'
            '&nbsp;&nbsp;1. Values are normalized to a common scale (e.g., 0-100)<br>'
            '&nbsp;&nbsp;2. Each indicator is weighted by importance<br>'
            '&nbsp;&nbsp;3. Weighted values are combined into final score<br>'
            '&nbsp;&nbsp;4. Higher score = better match for your objective<br><br>'
            
            '<b>💡 Tips for Best Results:</b><br>'
            '&nbsp;&nbsp;• Use "Very High" for the most critical indicators<br>'
            '&nbsp;&nbsp;• Include 2-5 indicators (too many dilutes the score)<br>'
            '&nbsp;&nbsp;• Test different importance levels to find what works best<br>'
            '&nbsp;&nbsp;• Create multiple score variations to compare approaches'
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
        
        # === STEP 1: SELECT INDICATORS ===
        step1_label = QLabel('<b>Step 1:</b> Select indicators to include in your score')
        layout.addWidget(step1_label)
        
        # Field selection table
        self.indicators_table = QTableWidget()
        self.indicators_table.setColumnCount(3)
        self.indicators_table.setHorizontalHeaderLabels(['☑', 'Indicator', 'Importance'])
        self.indicators_table.horizontalHeader().setStretchLastSection(False)
        self.indicators_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.indicators_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.indicators_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.indicators_table.setColumnWidth(0, 40)
        self.indicators_table.setColumnWidth(2, 120)
        self.indicators_table.setMaximumHeight(200)
        self.indicators_table.setAlternatingRowColors(True)
        layout.addWidget(self.indicators_table)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton('🔄 Refresh Available Fields')
        self.refresh_btn.clicked.connect(self._refresh_fields)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        # === STEP 2: NAME YOUR SCORE ===
        step2_label = QLabel('<b>Step 2:</b> Name your score')
        layout.addWidget(step2_label)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel('Score name:'))
        self.score_name_edit = QLineEdit()
        self.score_name_edit.setPlaceholderText('e.g., Risk_Score, Suitability_Index')
        name_layout.addWidget(self.score_name_edit)
        layout.addLayout(name_layout)
        
        # === ADVANCED OPTIONS (collapsible) ===
        self.advanced_group = QGroupBox('Advanced Options')
        self.advanced_group.setCheckable(True)
        self.advanced_group.setChecked(False)
        advanced_layout = QVBoxLayout()
        
        # Normalization method
        norm_layout = QHBoxLayout()
        norm_layout.addWidget(QLabel('Normalization ℹ️:'))
        self.norm_combo = QComboBox()
        self.norm_combo.addItems(['Min-Max (0-100)', 'Z-Score', 'None'])
        self.norm_combo.setToolTip(
            '<b>Normalization Methods:</b><br>'
            '<b>• Min-Max (0-100):</b> Scales all values to 0-100 range. Best for combining different units.<br>'
            '<b>• Z-Score:</b> Standardizes using mean and standard deviation. Best for statistical analysis.<br>'
            '<b>• None:</b> Uses raw values without transformation.'
        )
        norm_layout.addWidget(self.norm_combo)
        norm_layout.addStretch()
        advanced_layout.addLayout(norm_layout)
        
        # Combination method
        combine_layout = QHBoxLayout()
        combine_layout.addWidget(QLabel('Combination ℹ️:'))
        self.combine_combo = QComboBox()
        self.combine_combo.addItems(['Weighted Sum', 'Weighted Average'])
        self.combine_combo.setToolTip(
            '<b>Combination Methods:</b><br>'
            '<b>• Weighted Sum:</b> Adds all weighted values together. Result can be larger than 100.<br>'
            '<b>• Weighted Average:</b> Calculates weighted average. Result stays in normalized range.'
        )
        combine_layout.addWidget(self.combine_combo)
        combine_layout.addStretch()
        advanced_layout.addLayout(combine_layout)
        
        self.advanced_group.setLayout(advanced_layout)
        layout.addWidget(self.advanced_group)
        
        # === STEP 3: SELECT SOURCE LAYER ===
        step3_label = QLabel('<b>Step 3:</b> Select layer to process')
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
        self.output_path_edit.setPlaceholderText('Will be auto-generated: source_layer_score_ScoreName.gpkg')
        self.output_path_edit.setReadOnly(True)
        output_layout.addWidget(self.output_path_edit)
        
        self.browse_output_btn = QPushButton('📁 Browse')
        self.browse_output_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_output_btn)
        
        layout.addLayout(output_layout)
        
        # === APPLY BUTTON ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton('🧮 Apply Score')
        self.apply_btn.setMinimumWidth(150)
        self.apply_btn.setStyleSheet(
            'QPushButton {'
            '  background-color: #4CAF50;'
            '  color: white;'
            '  padding: 8px;'
            '  font-weight: bold;'
            '  border-radius: 4px;'
            '}'
            'QPushButton:hover {'
            '  background-color: #45a049;'
            '}'
            'QPushButton:disabled {'
            '  background-color: #cccccc;'
            '}'
        )
        self.apply_btn.clicked.connect(self._apply_score)
        self.apply_btn.setEnabled(False)
        button_layout.addWidget(self.apply_btn)
        
        
        layout.addLayout(button_layout)
        # Progress indicator
        self.progress_label = QLabel('')
        self.progress_label.setStyleSheet('color: gray; font-style: italic;')
        layout.addWidget(self.progress_label)
        
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Connect signals
        self.indicators_table.itemChanged.connect(self._on_table_changed)
        self.score_name_edit.textChanged.connect(self._validate_inputs)
        self.score_name_edit.textChanged.connect(self._update_output_path)

    def _toggle_help(self, checked):
        """Toggle help section visibility."""
        self.help_content.setVisible(checked)
        if checked:
            self.help_toggle_btn.setText('📚 Help & Guide (click to hide)')
        else:
            self.help_toggle_btn.setText('📚 Help & Guide (click to show)')
    
    def _refresh_fields(self):
        """Refresh available fields from Tab 1 (Input & Statistics)."""
        self.available_fields = self._get_available_fields()
        self._populate_table()
    
    def _get_available_fields(self) -> list:
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
    
    def _populate_table(self):
        """Populate table with available fields."""
        self.indicators_table.setRowCount(0)
        
        if not self.available_fields:
            # Show message
            self.indicators_table.setRowCount(1)
            msg_item = QTableWidgetItem('No fields available. Process rasters first, then refresh.')
            msg_item.setFlags(Qt.ItemIsEnabled)
            self.indicators_table.setItem(0, 1, msg_item)
            self.indicators_table.setSpan(0, 1, 1, 2)
            return
        
        # Populate table
        for row, field_name in enumerate(self.available_fields):
            self.indicators_table.insertRow(row)
            
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setProperty('field_name', field_name)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.indicators_table.setCellWidget(row, 0, checkbox_widget)
            
            # Field name
            field_item = QTableWidgetItem(field_name)
            field_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.indicators_table.setItem(row, 1, field_item)
            
            # Importance dropdown
            importance_combo = QComboBox()
            importance_combo.addItems(list(self.IMPORTANCE_WEIGHTS.keys()))
            importance_combo.setCurrentText('High')
            importance_combo.setProperty('field_name', field_name)
            importance_combo.setToolTip(
                '<b>Importance Weights:</b><br>'
                'Very High = 0.5 (50%)<br>'
                'High = 0.3 (30%)<br>'
                'Medium = 0.15 (15%)<br>'
                'Low = 0.05 (5%)'
            )
            self.indicators_table.setCellWidget(row, 2, importance_combo)
            
            # Connect signals
            checkbox.toggled.connect(self._on_checkbox_toggled)
            importance_combo.currentTextChanged.connect(self._on_importance_changed)
    
    def _on_checkbox_toggled(self, checked):
        """Handle checkbox toggle."""
        checkbox = self.sender()
        field_name = checkbox.property('field_name')
        
        if checked:
            # Add to selected
            importance = self._get_importance_for_field(field_name)
            self.selected_indicators[field_name] = importance
        else:
            # Remove from selected
            if field_name in self.selected_indicators:
                del self.selected_indicators[field_name]
        
        self._validate_inputs()

    def _on_layer_selected(self, index):
        """Handle source layer selection."""
        layer = self.source_layer_combo.currentLayer()
        
        if layer:
            # Auto-generate output path
            score_name = self.score_name_edit.text().strip()
            if score_name:
                self._update_output_path()
        
        self._validate_inputs()
    
    def _update_output_path(self):
        """Update output path based on source layer and score name."""
        layer = self.source_layer_combo.currentLayer()
        score_name = self.score_name_edit.text().strip()
        
        if not layer or not score_name:
            self.output_path_edit.clear()
            return
        
        # Get source layer path
        import os
        source_path = layer.source()
        
        # Generate new path
        base_dir = os.path.dirname(source_path)
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        
        new_filename = f"{base_name}_score_{score_name}.gpkg"
        new_path = os.path.join(base_dir, new_filename)
        
        self.output_path_edit.setText(new_path)
    
    def _browse_output(self):
        """Browse for output file."""
        from qgis.PyQt.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Save Score Output',
            self.output_path_edit.text() or '',
            'GeoPackage (*.gpkg)'
        )
        
        if filename:
            self.output_path_edit.setText(filename)    
    
    def _on_importance_changed(self, importance):
        """Handle importance dropdown change."""
        combo = self.sender()
        field_name = combo.property('field_name')
        
        # Update if selected
        if field_name in self.selected_indicators:
            self.selected_indicators[field_name] = importance
    
    def _on_table_changed(self):
        """Handle table changes."""
        self._validate_inputs()
    
    def _get_importance_for_field(self, field_name):
        """Get importance level for a field from table."""
        for row in range(self.indicators_table.rowCount()):
            cell_widget = self.indicators_table.cellWidget(row, 2)
            if isinstance(cell_widget, QComboBox):
                if cell_widget.property('field_name') == field_name:
                    return cell_widget.currentText()
        return 'High'  # Default
    
    def _validate_inputs(self):
        """Validate inputs and enable/disable Apply button."""
        # Need at least 2 indicators
        has_indicators = len(self.selected_indicators) >= 2
        
        # Need a name
        has_name = bool(self.score_name_edit.text().strip())
        
        # Need a source layer
        has_layer = self.source_layer_combo.currentLayer() is not None
        
        # Update output path when name changes
        if has_name and has_layer:
            self._update_output_path()
        
        # Enable button if all valid
        self.apply_btn.setEnabled(has_indicators and has_name and has_layer)
    
    def _apply_score(self):
        """Apply score to selected layer and create new output."""
        from qgis.core import QgsVectorFileWriter, QgsVectorLayer, QgsField, QgsProject
        from qgis.PyQt.QtCore import QVariant
        import os
        
        score_name = self.score_name_edit.text().strip()
        source_layer = self.source_layer_combo.currentLayer()
        output_path = self.output_path_edit.text()
        
        # Validate
        if not score_name:
            QMessageBox.warning(self, 'Missing Name', 'Please enter a name for your score.')
            return
        
        if len(self.selected_indicators) < 2:
            QMessageBox.warning(
                self,
                'Not Enough Indicators',
                'Please select at least 2 indicators to combine into a score.'
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
            
            # Remove existing
            try:
                os.remove(output_path)
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Cannot remove existing file: {e}')
                return
        
        # Show progress
        self.progress_label.setText('⏳ Step 1/3: Copying layer...')
        self.apply_btn.setEnabled(False)
        
        try:
            # Calculate score
            self._calculate_and_export_score(source_layer, output_path, score_name)
            
            # Success
            self.progress_label.setText('✅ Score calculated successfully! Layer added to project.')
            
            QMessageBox.information(
                self,
                '✅ Success!',
                f'<b>Score "{score_name}" calculated successfully!</b><br><br>'
                f'<b>Output file:</b> {os.path.basename(output_path)}<br>'
                f'<b>Indicators used:</b> {len(self.selected_indicators)}<br>'
                f'<b>Features processed:</b> {source_layer.featureCount()}<br><br>'
                f'<i>The new layer has been added to your QGIS project.<br>'
                f'Open the attribute table to see the "{score_name}" column!</i>'
            )
            
            # Clear inputs
            self._clear_inputs()
            
        except Exception as e:
            self.progress_label.setText('❌ Error calculating score')
            QMessageBox.critical(self, 'Error', f'Failed to calculate score:\n{str(e)}')
            import traceback
            print(traceback.format_exc())
        
        finally:
            self.apply_btn.setEnabled(True)
        
        # Build configuration
        config = {
            'type': 'score',
            'name': score_name,
            'indicators': self.selected_indicators.copy(),
            'weights': {
                field: self.IMPORTANCE_WEIGHTS[importance]
                for field, importance in self.selected_indicators.items()
            },
            'normalization': self.norm_combo.currentText(),
            'combination': self.combine_combo.currentText()
        }
        
        # Emit signal
        self.scoreConfigured.emit(config)
        
        # Show success
        QMessageBox.information(
            self,
            'Score Created',
            f'Score "{score_name}" configured successfully!\n\n'
            f'Indicators: {len(self.selected_indicators)}\n'
            f'This score will be calculated when you run processing.'
        )
        
        # Clear inputs
        self._clear_inputs()

    def _calculate_and_export_score(self, source_layer, output_path, score_name):
        """
        Calculate score and export to new file.
        
        Args:
            source_layer: Source vector layer
            output_path: Output file path
            score_name: Name of score field
        """
        from qgis.core import (
            QgsVectorFileWriter, QgsVectorLayer, QgsField, 
            QgsProject, QgsCoordinateTransformContext
        )
        from qgis.PyQt.QtCore import QVariant
        from ...algorithms.post_processing_engine import PostProcessingEngine
        import numpy as np
        
        # Copy layer to new file
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
        output_layer = QgsVectorLayer(output_path, score_name, 'ogr')
        
        if not output_layer.isValid():
            raise Exception("Failed to load output layer")
        
        # Start editing
        output_layer.startEditing()
        
        # Add score field
        if output_layer.fields().indexOf(score_name) == -1:
            output_layer.addAttribute(QgsField(score_name, QVariant.Double))
        output_layer.updateFields()
        
        # Get field indices
        field_indices = {}
        for field_name in self.selected_indicators.keys():
            idx = output_layer.fields().indexOf(field_name)
            if idx == -1:
                raise Exception(f"Field '{field_name}' not found in layer")
            field_indices[field_name] = idx
        
        # Extract values
        field_values = {field: [] for field in field_indices.keys()}
        feature_ids = []
        
        for feature in output_layer.getFeatures():
            feature_ids.append(feature.id())
            for field_name, field_idx in field_indices.items():
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
                        field_values[field_name].append(float(value))
                    except (ValueError, TypeError):
                        # Invalid value - use 0
                        field_values[field_name].append(0.0)
                else:
                    field_values[field_name].append(0.0)
        
        # Get weights
        weights = {
            field: self.IMPORTANCE_WEIGHTS[importance]
            for field, importance in self.selected_indicators.items()
        }
        
        # Normalize
        engine = PostProcessingEngine()
        normalized_values = {}
        
        normalization = self.norm_combo.currentText()
        
        if 'Min-Max' in normalization:
            for field_name, values in field_values.items():
                normalized_values[field_name] = engine.normalize_minmax(
                    np.array(values),
                    output_range=(0, 100)
                )
        elif 'Z-Score' in normalization:
            for field_name, values in field_values.items():
                normalized_values[field_name] = engine.normalize_zscore(
                    np.array(values)
                )
        else:  # No normalization
            normalized_values = {k: np.array(v) for k, v in field_values.items()}
        
        # Calculate scores
        scores = engine.weighted_sum(normalized_values, weights)
        
        # Update features
        score_field_idx = output_layer.fields().indexOf(score_name)
        
        for i, feature_id in enumerate(feature_ids):
            output_layer.changeAttributeValue(feature_id, score_field_idx, float(scores[i]))
        
        # Commit changes
        output_layer.commitChanges()
        
        # Add to project
        QgsProject.instance().addMapLayer(output_layer)    
    
    def _clear_inputs(self):
        """Clear all inputs."""
        # Uncheck all checkboxes
        for row in range(self.indicators_table.rowCount()):
            checkbox_widget = self.indicators_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
        
        # Clear name
        self.score_name_edit.clear()
        
        # Clear selected
        self.selected_indicators.clear()
    
    def get_configuration(self):
        """
        Get current score configuration (if any).
        
        Returns:
            Dict or None
        """
        # For now, scores are emitted via signal
        # We could also store them here if needed
        return None
