"""
Time Series Analyzer Widget for Zonify

Allows users to configure flexible time series analysis with multiple rasters.
Supports various analysis types: change detection, trend analysis, seasonal patterns, etc.

Features:
- Import multiple temporal rasters
- Configure analysis types
- Flexible date-based grouping
- Custom output field naming

Author: Dragos Gontariu
License: GPL-3.0
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QGroupBox, QListWidget,
    QListWidgetItem, QFileDialog, QMessageBox, QDateEdit, QSpinBox
)
from qgis.PyQt.QtCore import Qt, pyqtSignal, QDate
from qgis.PyQt.QtGui import QFont
from osgeo import gdal
import os
from datetime import datetime


class TimeSeriesWidget(QWidget):
    """
    Widget for configuring time series analysis.
    
    Signals:
        configChanged: Emitted when configuration changes
    """
    
    configChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor.
        
        Args:
            parent: Parent widget
        """
        super(TimeSeriesWidget, self).__init__(parent)
        
        self.rasters = []  # List of {'date': str, 'path': str}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        
        # Main content
        content_layout = layout  # Use main layout directly, no wrapper
        
        
        
        
        
        # === ANALYSIS NAME ===
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel('Analysis Name:'))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('e.g., Temperature Trend 2020-2024')
        name_layout.addWidget(self.name_edit)
        self.name_edit.textChanged.connect(self._update_output_path) 
        self.name_edit.textChanged.connect(self._validate_inputs) 
        content_layout.addLayout(name_layout)
        
        # === TEMPORAL RASTERS ===
        rasters_group = QGroupBox('Temporal Rasters')
        rasters_layout = QVBoxLayout()
        
        self.raster_list = QListWidget()
        self.raster_list.setMaximumHeight(100)
        rasters_layout.addWidget(self.raster_list)
        
        raster_buttons = QHBoxLayout()
        
        self.add_raster_btn = QPushButton('Add Raster')
        self.add_raster_btn.clicked.connect(self._add_raster)
        raster_buttons.addWidget(self.add_raster_btn)
        
        self.import_multiple_btn = QPushButton('Import Multiple...')
        self.import_multiple_btn.clicked.connect(self._import_multiple)
        raster_buttons.addWidget(self.import_multiple_btn)
        
        self.remove_raster_btn = QPushButton('Remove Selected')
        self.remove_raster_btn.clicked.connect(self._remove_raster)
        raster_buttons.addWidget(self.remove_raster_btn)
        
        self.clear_all_btn = QPushButton('Clear All')
        self.clear_all_btn.clicked.connect(self._clear_all)
        raster_buttons.addWidget(self.clear_all_btn)
        
        raster_buttons.addStretch()
        rasters_layout.addLayout(raster_buttons)
        
        # Sort button
        sort_layout = QHBoxLayout()
        self.sort_btn = QPushButton('Sort by Date')
        self.sort_btn.clicked.connect(self._sort_by_date)
        sort_layout.addWidget(self.sort_btn)
        
        self.raster_count_label = QLabel('Total: 0 rasters')
        self.raster_count_label.setStyleSheet('color: gray;')
        sort_layout.addWidget(self.raster_count_label)
        sort_layout.addStretch()
        
        rasters_layout.addLayout(sort_layout)
        
        rasters_group.setLayout(rasters_layout)
        content_layout.addWidget(rasters_group)
        
        # === ANALYSIS TYPES ===
        analysis_group = QGroupBox('Analysis Types')
        analysis_layout = QVBoxLayout()
        
        analysis_layout.addWidget(QLabel('<small>Select the analyses to perform:</small>'))
        
        # Change Detection
        change_layout = QHBoxLayout()
        self.change_detection = QCheckBox('Change Detection')
        self.change_detection.setChecked(True)
        self.change_detection.toggled.connect(self._validate_inputs)
        change_layout.addWidget(self.change_detection)
        
        self.change_compare = QComboBox()
        self.change_compare.addItems(['First vs Last', 'Custom Periods'])
        self.change_compare.setMaximumWidth(150)
        change_layout.addWidget(self.change_compare)
        change_layout.addStretch()
        analysis_layout.addLayout(change_layout)
        
        # Trend Analysis
        trend_layout = QHBoxLayout()
        self.trend_analysis = QCheckBox('Trend Analysis')
        self.trend_analysis.setChecked(True)
        self.trend_analysis.toggled.connect(self._validate_inputs)
        trend_layout.addWidget(self.trend_analysis)
        
        self.trend_method = QComboBox()
        self.trend_method.addItems(['Linear Regression', 'Sen\'s Slope'])
        self.trend_method.setMaximumWidth(150)
        trend_layout.addWidget(self.trend_method)
        trend_layout.addStretch()
        analysis_layout.addLayout(trend_layout)
        
        # Temporal Statistics
        self.temporal_stats = QCheckBox('Temporal Statistics')
        self.temporal_stats.setChecked(True)
        self.temporal_stats.setToolTip('Mean, min, max, std dev over time')
        self.temporal_stats.toggled.connect(self._validate_inputs)
        analysis_layout.addWidget(self.temporal_stats)
        
        stats_detail = QHBoxLayout()
        stats_detail.addSpacing(20)
        self.stats_mean = QCheckBox('Mean')
        self.stats_mean.setChecked(True)
        stats_detail.addWidget(self.stats_mean)
        
        self.stats_minmax = QCheckBox('Min/Max')
        self.stats_minmax.setChecked(True)
        stats_detail.addWidget(self.stats_minmax)
        
        self.stats_std = QCheckBox('Std Dev')
        stats_detail.addWidget(self.stats_std)
        
        self.stats_cv = QCheckBox('Coeff. Var.')
        stats_detail.addWidget(self.stats_cv)
        
        stats_detail.addStretch()
        analysis_layout.addLayout(stats_detail)
        
         # Seasonal Analysis
        seasonal_layout = QHBoxLayout()
        self.seasonal_analysis = QCheckBox('Seasonal Analysis')
        self.seasonal_analysis.toggled.connect(self._validate_inputs)
        seasonal_layout.addWidget(self.seasonal_analysis)
        
        self.seasonal_group = QComboBox()
        self.seasonal_group.addItems(['Month', 'Quarter', 'Season'])
        self.seasonal_group.setMaximumWidth(100)
        seasonal_layout.addWidget(self.seasonal_group)
        seasonal_layout.addStretch()
        analysis_layout.addLayout(seasonal_layout)
        
        # Extreme Events
        self.extreme_events = QCheckBox('Extreme Events')
        self.extreme_events.setToolTip('Find maximum and minimum values with dates')
        self.extreme_events.toggled.connect(self._validate_inputs)
        analysis_layout.addWidget(self.extreme_events)
        
        analysis_group.setLayout(analysis_layout)
        content_layout.addWidget(analysis_group)
        
        # === OUTPUT CONFIGURATION ===
        output_group = QGroupBox('Output Configuration')
        output_layout = QVBoxLayout()
        
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel('Field Prefix:'))
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText('e.g., ts_temp_')
        self.prefix_edit.setText('ts_')
        self.prefix_edit.textChanged.connect(self._update_example_fields)
        prefix_layout.addWidget(self.prefix_edit)
        output_layout.addLayout(prefix_layout)
        
        output_layout.addWidget(QLabel('<small style="color: gray;">Example output fields:</small>'))
        
        self.example_fields_label = QLabel()
        self.example_fields_label.setWordWrap(True)
        self.example_fields_label.setStyleSheet('font-family: monospace; font-size: 10px;')
        self._update_example_fields()
        output_layout.addWidget(self.example_fields_label)
        
        output_group.setLayout(output_layout)
        content_layout.addWidget(output_group)
        
        content_layout.addStretch()
        
        
       
        
        # === SOURCE LAYER & OUTPUT (new section) === ← ADAUGĂ DE AICI
        
        # Separator
        from qgis.PyQt.QtWidgets import QFrame
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        apply_section_label = QLabel('<b>Apply Time Series Analysis</b>')
        layout.addWidget(apply_section_label)
        
        # Source layer selection
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
        self.output_path_edit.setPlaceholderText('Will be auto-generated: source_layer_timeseries_AnalysisName.gpkg')
        self.output_path_edit.setReadOnly(True)
        output_layout.addWidget(self.output_path_edit)
        
        self.browse_output_btn = QPushButton('📁 Browse')
        self.browse_output_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_output_btn)
        
        layout.addLayout(output_layout)
        
        # Apply button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton('📈 Apply Time Series')
        self.apply_btn.setMinimumWidth(180)
        self.apply_btn.setStyleSheet(
            'QPushButton {'
            '  background-color: #00BCD4;'
            '  color: white;'
            '  padding: 8px;'
            '  font-weight: bold;'
            '  border-radius: 4px;'
            '}'
            'QPushButton:hover {'
            '  background-color: #0097A7;'
            '}'
            'QPushButton:disabled {'
            '  background-color: #cccccc;'
            '}'
        )
        self.apply_btn.clicked.connect(self._apply_time_series)
        self.apply_btn.setEnabled(False)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
        
        # Progress indicator
        self.progress_label = QLabel('')
        self.progress_label.setStyleSheet('color: gray; font-style: italic;')
        layout.addWidget(self.progress_label)
        
        # ← PÂNĂ AICI (tot ce e între)
        
        self.setLayout(layout)
    
    
    
    def _add_raster(self):
        """Add single raster with date."""
        from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle('Add Temporal Raster')
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel('Raster File:'))
        
        file_layout = QHBoxLayout()
        file_edit = QLineEdit()
        file_layout.addWidget(file_edit)
        
        browse_btn = QPushButton('Browse...')
        
        def browse():
            path, _ = QFileDialog.getOpenFileName(
                dialog,
                'Select Raster',
                '',
                'Raster Files (*.tif *.tiff *.img *.asc);;All Files (*.*)'
            )
            if path:
                file_edit.setText(path)
        
        browse_btn.clicked.connect(browse)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        
        layout.addWidget(QLabel('Date:'))
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        layout.addWidget(date_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            path = file_edit.text().strip()
            date = date_edit.date().toString('yyyy-MM-dd')
            
            if not path:
                QMessageBox.warning(self, 'No File', 'Please select a raster file.')
                return
            
            if not os.path.exists(path):
                QMessageBox.warning(self, 'File Not Found', f'File does not exist:\n{path}')
                return
            
            # Validate raster
            ds = gdal.Open(path)
            if ds is None:
                QMessageBox.warning(self, 'Invalid Raster', f'Cannot open as raster:\n{path}')
                return
            ds = None
            
            # Add to list
            self._add_raster_to_list(date, path)
    
    def _import_multiple(self):
        """Import multiple rasters at once."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            'Select Multiple Rasters',
            '',
            'Raster Files (*.tif *.tiff *.img *.asc);;All Files (*.*)'
        )
        
        if not files:
            return
        
        # Try to extract dates from filenames
        added = 0
        for path in files:
            filename = os.path.basename(path)
            
            # Try to extract date (various formats)
            date = self._extract_date_from_filename(filename)
            
            if date:
                self._add_raster_to_list(date, path)
                added += 1
            else:
                # Ask user for date
                from qgis.PyQt.QtWidgets import QInputDialog
                date_str, ok = QInputDialog.getText(
                    self,
                    'Date for Raster',
                    f'Enter date for:\n{filename}\n\nFormat: YYYY-MM-DD',
                    text=datetime.now().strftime('%Y-%m-%d')
                )
                
                if ok and date_str:
                    self._add_raster_to_list(date_str, path)
                    added += 1
        
        if added > 0:
            QMessageBox.information(
                self,
                'Rasters Added',
                f'Added {added} temporal raster(s).'
            )
    
    def _extract_date_from_filename(self, filename):
        """
        Try to extract date from filename.
        Supports various formats: YYYY-MM-DD, YYYYMMDD, etc.
        
        Returns:
            str: Date in YYYY-MM-DD format, or None
        """
        import re
        
        # Try YYYY-MM-DD
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
        if match:
            return f'{match.group(1)}-{match.group(2)}-{match.group(3)}'
        
        # Try YYYYMMDD
        match = re.search(r'(\d{4})(\d{2})(\d{2})', filename)
        if match:
            return f'{match.group(1)}-{match.group(2)}-{match.group(3)}'
        
        # Try YYYY_MM_DD
        match = re.search(r'(\d{4})_(\d{2})_(\d{2})', filename)
        if match:
            return f'{match.group(1)}-{match.group(2)}-{match.group(3)}'
        
        return None
    
    def _add_raster_to_list(self, date, path):
        """Add raster to list widget."""
        # Check for duplicates
        for raster in self.rasters:
            if raster['path'] == path:
                return
        
        # Add to internal list
        self.rasters.append({'date': date, 'path': path})
        
        # Add to widget
        filename = os.path.basename(path)
        item = QListWidgetItem(f'📅 {date}  |  {filename}')
        item.setToolTip(path)
        item.setData(Qt.UserRole, {'date': date, 'path': path})
        self.raster_list.addItem(item)
        
        self._update_raster_count()
        self.configChanged.emit()
    
    def _remove_raster(self):
        """Remove selected raster."""
        current = self.raster_list.currentRow()
        if current >= 0:
            item = self.raster_list.item(current)
            data = item.data(Qt.UserRole)
            
            # Remove from internal list
            self.rasters = [r for r in self.rasters if r['path'] != data['path']]
            
            # Remove from widget
            self.raster_list.takeItem(current)
            
            self._update_raster_count()
            self.configChanged.emit()
    
    def _clear_all(self):
        """Clear all rasters."""
        if self.raster_list.count() == 0:
            return
        
        reply = QMessageBox.question(
            self,
            'Clear All',
            'Remove all temporal rasters?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.rasters.clear()
            self.raster_list.clear()
            self._update_raster_count()
            self.configChanged.emit()
    
    def _sort_by_date(self):
        """Sort rasters by date."""
        if len(self.rasters) == 0:
            return
        
        # Sort internal list
        self.rasters.sort(key=lambda x: x['date'])
        
        # Rebuild widget list
        self.raster_list.clear()
        for raster in self.rasters:
            filename = os.path.basename(raster['path'])
            item = QListWidgetItem(f'📅 {raster["date"]}  |  {filename}')
            item.setToolTip(raster['path'])
            item.setData(Qt.UserRole, raster)
            self.raster_list.addItem(item)
        
        QMessageBox.information(
            self,
            'Sorted',
            f'Sorted {len(self.rasters)} rasters by date.'
        )
    
    def _update_raster_count(self):
        """Update raster count label."""
        count = len(self.rasters)
        
        if count == 0:
            self.raster_count_label.setText('Total: 0 rasters')
        else:
            dates = [r['date'] for r in self.rasters]
            min_date = min(dates)
            max_date = max(dates)
            self.raster_count_label.setText(
                f'Total: {count} rasters from {min_date} to {max_date}'
            )
    
    def _update_example_fields(self):
        """Update example output fields with descriptions."""
        prefix = self.prefix_edit.text()
        
        # Build complete field list with descriptions
        field_descriptions = []
        
        if self.change_detection.isChecked():
            field_descriptions.extend([
                (f'{prefix}first_value', 'Value from the first time period'),
                (f'{prefix}last_value', 'Value from the last time period'),
                (f'{prefix}mean_change', 'Average change between consecutive periods'),
                (f'{prefix}total_change', 'Total change from first to last (last - first)'),
                (f'{prefix}percent_change', 'Percentage change from first to last (%)')
            ])
        
        if self.trend_analysis.isChecked():
            field_descriptions.extend([
                (f'{prefix}trend_slope', 'Linear trend slope (rate of change per period)'),
                (f'{prefix}trend_r2', 'Trend R² goodness of fit (0-1)'),
                (f'{prefix}trend_pvalue', 'Trend p-value <0.05 = significant')
            ])
        
        if self.temporal_stats.isChecked():
            temp_fields = []
            if self.stats_mean.isChecked():
                temp_fields.append((f'{prefix}temporal_mean', 'Mean value across all periods'))
            if self.stats_std.isChecked():
                temp_fields.append((f'{prefix}temporal_std', 'Standard deviation across periods'))
            if self.stats_minmax.isChecked():
                temp_fields.extend([
                    (f'{prefix}temporal_min', 'Minimum value across periods'),
                    (f'{prefix}temporal_max', 'Maximum value across periods'),
                    (f'{prefix}temporal_range', 'Range (max - min) across periods')
                ])
            if self.stats_cv.isChecked():
                temp_fields.append((f'{prefix}temporal_cv', 'Coefficient of variation (%) across periods'))
            field_descriptions.extend(temp_fields)
        
        if self.seasonal_analysis.isChecked():
            field_descriptions.extend([
                (f'{prefix}seasonal_winter_mean', 'Mean value for winter months (Dec-Feb)'),
                (f'{prefix}seasonal_spring_mean', 'Mean value for spring months (Mar-May)'),
                (f'{prefix}seasonal_summer_mean', 'Mean value for summer months (Jun-Aug)'),
                (f'{prefix}seasonal_fall_mean', 'Mean value for fall months (Sep-Nov)')
            ])
        
        if self.extreme_events.isChecked():
            field_descriptions.extend([
                (f'{prefix}max_value', 'Maximum value in time series'),
                (f'{prefix}max_date', 'Date when maximum occurred'),
                (f'{prefix}min_value', 'Minimum value in time series'),
                (f'{prefix}min_date', 'Date when minimum occurred')
            ])
        
        # Display all fields with descriptions
        if field_descriptions:
            html_lines = []
            for field_name, description in field_descriptions:
                html_lines.append(
                    f'<span style="color: #202124; font-weight: 500;">{field_name}</span> '
                    f'<span style="color: #757575;">— {description}</span>'
                )
            
            self.example_fields_label.setText('<br>'.join(html_lines))
        else:
            self.example_fields_label.setText('<i style="color: #9AA0A6;">No analyses selected</i>')
    def is_enabled(self):
        """Check if time series analysis is enabled."""
        # Always enabled if widget is visible (collapse handles visibility)
        return len(self.rasters) >= 2  # Need at least 2 rasters for time series
    
    def get_configuration(self):
        """
        Get time series configuration.
        
        Returns:
            dict: Configuration dictionary
        """
        if not self.is_enabled() or len(self.rasters) == 0:
            return None
        
        # Collect enabled analyses
        analyses = {}
        
        if self.change_detection.isChecked():
            analyses['change_detection'] = {
                'enabled': True,
                'compare': self.change_compare.currentText()
            }
        
        if self.trend_analysis.isChecked():
            analyses['trend_analysis'] = {
                'enabled': True,
                'method': self.trend_method.currentText().lower().replace(' ', '_').replace("'", '')
            }
        
        if self.temporal_stats.isChecked():
            stats = []
            if self.stats_mean.isChecked():
                stats.append('mean')
            if self.stats_minmax.isChecked():
                stats.extend(['min', 'max'])
            if self.stats_std.isChecked():
                stats.append('std')
            if self.stats_cv.isChecked():
                stats.append('cv')
            
            analyses['temporal_statistics'] = {
                'enabled': True,
                'stats': stats
            }
        
        if self.seasonal_analysis.isChecked():
            analyses['seasonal_analysis'] = {
                'enabled': True,
                'group_by': self.seasonal_group.currentText().lower()
            }
        
        if self.extreme_events.isChecked():
            analyses['extreme_events'] = {
                'enabled': True
            }
        
        return {
            'name': self.name_edit.text().strip() or 'Time Series Analysis',
            'rasters': self.rasters.copy(),
            'analyses': analyses,
            'output_prefix': self.prefix_edit.text()
        }

    def _on_layer_selected(self, index):
        """Handle source layer selection."""
        self._update_output_path()
        self._validate_inputs()
    
    def _update_output_path(self):
        """Update output path based on source layer and analysis name."""
        layer = self.source_layer_combo.currentLayer()
        analysis_name = self.name_edit.text().strip()
        
        if not layer or not analysis_name:
            self.output_path_edit.clear()
            return
        
        import os
        source_path = layer.source()
        base_dir = os.path.dirname(source_path)
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        
        new_filename = f"{base_name}_timeseries_{analysis_name}.gpkg"
        new_path = os.path.join(base_dir, new_filename)
        
        self.output_path_edit.setText(new_path)
    
    def _browse_output(self):
        """Browse for output file."""
        from qgis.PyQt.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Save Time Series Output',
            self.output_path_edit.text() or '',
            'GeoPackage (*.gpkg)'
        )
        
        if filename:
            self.output_path_edit.setText(filename)
    
    def _validate_inputs(self):
        """Validate inputs and enable/disable Apply button."""
        has_rasters = self.raster_list.count() >= 2
        has_analysis = self.name_edit.text().strip() != ''
        has_layer = self.source_layer_combo.currentLayer() is not None
        has_output = bool(self.output_path_edit.text())
        has_types = (self.change_detection.isChecked() or 
                    self.trend_analysis.isChecked() or
                    self.temporal_stats.isChecked() or
                    self.seasonal_analysis.isChecked() or
                    self.extreme_events.isChecked())
        
        self.apply_btn.setEnabled(has_rasters and has_analysis and has_layer and 
                                  has_output and has_types)
    
    def _apply_time_series(self):
        """Apply time series analysis to selected layer."""
        from qgis.core import QgsVectorFileWriter, QgsVectorLayer, QgsProject, QgsCoordinateTransformContext
        from qgis.PyQt.QtWidgets import QMessageBox
        import os
        
        source_layer = self.source_layer_combo.currentLayer()
        output_path = self.output_path_edit.text()
        analysis_name = self.name_edit.text().strip()
        
        # Validate
        if not source_layer:
            QMessageBox.warning(self, 'No Layer', 'Please select a source layer.')
            return
        
        if not output_path:
            QMessageBox.warning(self, 'No Output Path', 'Please specify output path.')
            return
        
        if self.raster_list.count() < 2:
            QMessageBox.warning(
                self,
                'Not Enough Rasters',
                'Time series analysis requires at least 2 temporal rasters.'
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
        self.progress_label.setText('⏳ Processing time series...')
        self.apply_btn.setEnabled(False)
        
        try:
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
            output_layer = QgsVectorLayer(output_path, f'{analysis_name}_timeseries', 'ogr')
            
            if not output_layer.isValid():
                raise Exception("Failed to load output layer")
            
            # Apply time series calculations
            print("DEBUG: Starting time series calculation...")
            self._calculate_time_series(output_layer)
            
            QMessageBox.information(
                self,
                '✅ Success!',
                f'<b>Time series analysis completed!</b><br><br>'
                f'<b>Analysis:</b> {analysis_name}<br>'
                f'<b>Temporal rasters:</b> {self.raster_list.count()}<br>'
                f'<b>Output file:</b> {os.path.basename(output_path)}<br><br>'
                f'<i>The new layer has been added to your QGIS project.<br>'
                f'Open the attribute table to see the time series fields!</i>'
            )
            
            # Add to project
            QgsProject.instance().addMapLayer(output_layer)
            
            self.progress_label.setText('✅ Time series applied!')
            
        except Exception as e:
            self.progress_label.setText('❌ Error during time series')
            QMessageBox.critical(self, 'Error', f'Failed:\n{str(e)}')
            import traceback
            print(traceback.format_exc())
        
        finally:
            self.apply_btn.setEnabled(True)

    def _calculate_time_series(self, output_layer):
        """Calculate time series for all features in layer."""
        from qgis.core import QgsField, QgsRasterLayer
        from qgis.PyQt.QtCore import QVariant
        from qgis.PyQt.QtWidgets import QApplication
        from qgis.analysis import QgsZonalStatistics
        
        # Get configuration
        config = self.get_configuration()
        if not config:
            raise Exception("Failed to get time series configuration")
        
        print(f"DEBUG: Time series config: {len(config['rasters'])} rasters")
        
        # Load rasters first
        raster_layers = {}
        for raster_info in config['rasters']:
            raster_path = raster_info['path']
            raster_layer = QgsRasterLayer(raster_path, f"ts_{raster_info['date']}")
            if raster_layer.isValid():
                raster_layers[raster_info['date']] = raster_layer
            else:
                print(f"WARNING: Could not load raster: {raster_path}")
        
        print(f"DEBUG: Loaded {len(raster_layers)} valid rasters")
        
        # Extract mean values for each raster using zonal statistics
        for date_str, raster_layer in raster_layers.items():
            field_name = f'_temp_{date_str.replace("-", "")}_'  # ← Adaugă underscore final
            
            # Run zonal statistics to add mean field
            zonal_stats = QgsZonalStatistics(
                output_layer,
                raster_layer,
                field_name,
                1,  # Band 1
                QgsZonalStatistics.Mean
            )
            
            zonal_stats.calculateStatistics(None)
            print(f"DEBUG: Extracted values for {date_str}")
        
        # Now we have temporal data in the layer
        # Create analyzer and calculate results
        from ...algorithms.time_series_engine import TimeSeriesAnalyzer
        
        analyzer = TimeSeriesAnalyzer(config)
        
        # Start editing
        output_layer.startEditing()
        
        # Add output fields
        output_field_names = analyzer.get_output_field_names()
        
        for field_name in output_field_names:
            if output_layer.fields().indexOf(field_name) == -1:
                if '_date' in field_name:
                    output_layer.addAttribute(QgsField(field_name, QVariant.String))
                else:
                    output_layer.addAttribute(QgsField(field_name, QVariant.Double))
        
        output_layer.updateFields()
        
        # Process each feature
        feature_count = output_layer.featureCount()
        processed = 0
        
        for feature in output_layer.getFeatures():
            try:
                # Extract temporal data from temporary fields
                temporal_data = []
                
                # DEBUG: Check what fields exist
                if processed == 0:
                    print(f"DEBUG: Available fields: {[f.name() for f in output_layer.fields()]}")
                
                for date_str in raster_layers.keys():
                    temp_field = f'_temp_{date_str.replace("-", "")}_mean'  # ← Adaugă _mean
                    field_idx = output_layer.fields().indexOf(temp_field)
                    
                    # DEBUG
                    if processed == 0:
                        print(f"DEBUG: Looking for field '{temp_field}', index={field_idx}")
                    
                    if field_idx != -1:
                        value = feature[field_idx]
                        
                        # DEBUG
                        if processed == 0:
                            print(f"DEBUG: Field '{temp_field}' value = {value}")
                        
                        if value is not None:
                            temporal_data.append({
                                'date': date_str,
                                'value': float(value)
                            })
                
                # DEBUG
                if processed == 0:
                    print(f"DEBUG: Extracted temporal_data: {temporal_data}")
                
                # Calculate time series results
                results = self._calculate_time_series_results(temporal_data, config)
                
                # DEBUG
                if processed == 0:
                    print(f"DEBUG: Calculated results: {results}")
                
                # Calculate time series results
                results = self._calculate_time_series_results(temporal_data, config)
                
                # Update feature
                for field_name, value in results.items():
                    field_idx = output_layer.fields().indexOf(field_name)
                    if field_idx != -1:
                        output_layer.changeAttributeValue(feature.id(), field_idx, value)
                
                processed += 1
                
                if processed % 50 == 0:
                    self.progress_label.setText(f'⏳ Processing: {processed}/{feature_count}...')
                    QApplication.processEvents()
            
            except Exception as e:
                print(f"WARNING: Failed to process feature {feature.id()}: {e}")
        
        # Remove temporary fields
        fields_to_remove = []
        for field in output_layer.fields():
            if field.name().startswith('_temp_'):
                fields_to_remove.append(output_layer.fields().indexOf(field.name()))
        
        for field_idx in sorted(fields_to_remove, reverse=True):
            output_layer.deleteAttribute(field_idx)
        
        # Commit
        if not output_layer.commitChanges():
            errors = output_layer.commitErrors()
            raise Exception(f"Failed to commit: {errors}")
        
        print(f"DEBUG: Complete! Processed {processed} features")


    def _calculate_time_series_results(self, temporal_data, config):
        """Calculate time series results from temporal data."""
        import numpy as np
        from datetime import datetime
        
        if len(temporal_data) < 2:
            return {}
        
        # Sort by date
        temporal_data = sorted(temporal_data, key=lambda x: x['date'])
        
        values = np.array([d['value'] for d in temporal_data])
        dates = [datetime.fromisoformat(d['date']) for d in temporal_data]
        
        results = {}
        prefix = config.get('output_prefix', 'ts_')
        
        # Change detection
        if config['analyses'].get('change_detection', {}).get('enabled'):
            change = values[-1] - values[0]
            percent_change = (change / values[0] * 100) if values[0] != 0 else 0
            
            results[f'{prefix}mean_change'] = float(change)
            results[f'{prefix}percent_change'] = float(percent_change)
            results[f'{prefix}first_value'] = float(values[0])
            results[f'{prefix}last_value'] = float(values[-1])
            results[f'{prefix}first_date'] = temporal_data[0]['date']
            results[f'{prefix}last_date'] = temporal_data[-1]['date']
        
        # Trend analysis
        if config['analyses'].get('trend_analysis', {}).get('enabled'):
            from scipy import stats as scipy_stats
            
            # Linear regression
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, values)
            
            results[f'{prefix}trend_slope'] = float(slope)
            results[f'{prefix}trend_intercept'] = float(intercept)
            results[f'{prefix}trend_r2'] = float(r_value ** 2)
            results[f'{prefix}trend_pvalue'] = float(p_value)
            results[f'{prefix}trend_stderr'] = float(std_err)
        
        # Temporal statistics
        if config['analyses'].get('temporal_statistics', {}).get('enabled'):
            stats_list = config['analyses']['temporal_statistics'].get('stats', [])
            
            if 'mean' in stats_list:
                results[f'{prefix}temporal_mean'] = float(np.mean(values))
            if 'min' in stats_list:
                results[f'{prefix}temporal_min'] = float(np.min(values))
            if 'max' in stats_list:
                results[f'{prefix}temporal_max'] = float(np.max(values))
            if 'std' in stats_list:
                results[f'{prefix}temporal_std'] = float(np.std(values))
            if 'cv' in stats_list:
                mean_val = np.mean(values)
                cv = (np.std(values) / mean_val * 100) if mean_val != 0 else 0
                results[f'{prefix}temporal_cv'] = float(cv)
        
        # Extreme events
        if config['analyses'].get('extreme_events', {}).get('enabled'):
            max_idx = np.argmax(values)
            min_idx = np.argmin(values)
            
            results[f'{prefix}max_value'] = float(values[max_idx])
            results[f'{prefix}max_date'] = temporal_data[max_idx]['date']
            results[f'{prefix}min_value'] = float(values[min_idx])
            results[f'{prefix}min_date'] = temporal_data[min_idx]['date']
        
        return results