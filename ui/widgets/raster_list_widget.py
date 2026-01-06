"""
Raster List Widget for Zonify

Custom widget for displaying and managing multiple raster files.
Shows raster metadata (resolution, CRS, size) and allows multi-selection.

Features:
- Add files (single or multiple)
- Add folder (batch import)
- Remove selected
- Clear all
- Show raster metadata
- Drag & drop support (Phase 3)

Author: Dragos Gontariu
License: GPL-3.0
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.core import QgsRasterLayer
from osgeo import gdal
import os


class RasterListWidget(QWidget):
    """
    Custom widget for managing multiple raster files.
    
    Signals:
        rastersChanged: Emitted when raster list changes
    """
    
    rastersChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor.
        
        Args:
            parent: Parent widget
        """
        super(RasterListWidget, self).__init__(parent)
        
        self.raster_paths = []  # List of raster file paths
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        # Add header label with instructions
        from qgis.PyQt.QtWidgets import QLabel
        header = QLabel(
            '<b>📂 Raster Files</b><br>'
            '<span style="color: #757575;">'
            'Add raster files to process. Metadata will be displayed for each file.<br>'
            'Supported formats: GeoTIFF (.tif), IMG, ASCII Grid (.asc), VRT'
            '</span>'
        )
        header.setWordWrap(True)
        layout.addWidget(header)
        # List widget to display rasters
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setWordWrap(True)  # Enable word wrap
        self.list_widget.setSpacing(5)  # Add spacing between items
        layout.addWidget(self.list_widget)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Add files button
        self.add_files_btn = QPushButton('Add Files')
        self.add_files_btn.clicked.connect(self._add_files)
        buttons_layout.addWidget(self.add_files_btn)
        
        # Add folder button
        self.add_folder_btn = QPushButton('Add Folder')
        self.add_folder_btn.clicked.connect(self._add_folder)
        buttons_layout.addWidget(self.add_folder_btn)
        
        # Remove selected button
        self.remove_btn = QPushButton('Remove Selected')
        self.remove_btn.clicked.connect(self._remove_selected)
        buttons_layout.addWidget(self.remove_btn)
        
        # Clear all button
        self.clear_btn = QPushButton('Clear All')
        self.clear_btn.clicked.connect(self._clear_all)
        buttons_layout.addWidget(self.clear_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def _add_files(self):
        """Open file dialog to add raster files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            'Select Raster Files',
            '',
            'Raster Files (*.tif *.tiff *.img *.asc *.vrt);;All Files (*.*)'
        )
        
        if files:
            added = 0
            for file_path in files:
                if self._add_raster(file_path):
                    added += 1
            
            if added > 0:
                self.rastersChanged.emit()
                QMessageBox.information(
                    self,
                    'Rasters Added',
                    f'Added {added} raster(s) successfully.'
                )
    
    def _add_folder(self):
        """Open folder dialog to add all rasters from a folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            'Select Folder with Rasters'
        )
        
        if folder:
            # Find all raster files in folder
            raster_extensions = ['.tif', '.tiff', '.img', '.asc', '.vrt']
            added = 0
            
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file)[1].lower()
                    if ext in raster_extensions:
                        if self._add_raster(file_path):
                            added += 1
            
            if added > 0:
                self.rastersChanged.emit()
                QMessageBox.information(
                    self,
                    'Rasters Added',
                    f'Added {added} raster(s) from folder.'
                )
            else:
                QMessageBox.warning(
                    self,
                    'No Rasters Found',
                    f'No raster files found in:\n{folder}'
                )
    
    def _add_raster(self, file_path):
        """
        Add a single raster to the list.
        
        Args:
            file_path (str): Path to raster file
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        # Check if already added
        if file_path in self.raster_paths:
            return False
        
        # Validate raster
        try:
            dataset = gdal.Open(file_path)
            if dataset is None:
                QMessageBox.warning(
                    self,
                    'Invalid Raster',
                    f'Cannot open raster:\n{file_path}'
                )
                return False
            
            # Get metadata
            width = dataset.RasterXSize
            height = dataset.RasterYSize
            bands = dataset.RasterCount
            
            # Get CRS with full description
            projection = dataset.GetProjection()
            crs_text = 'Unknown CRS'
            crs_description = ''
            
            if projection:
                try:
                    from osgeo import osr
                    srs = osr.SpatialReference()
                    srs.ImportFromWkt(projection)
                    
                    # Get EPSG code
                    epsg_code = srs.GetAuthorityCode(None)
                    if epsg_code:
                        crs_text = f'EPSG:{epsg_code}'
                        # Get CRS name/description
                        crs_name = srs.GetName()
                        if crs_name:
                            crs_description = crs_name
                    else:
                        crs_text = 'Custom CRS'
                        crs_description = 'Non-standard projection'
                except:
                    crs_text = 'Custom CRS'
                    crs_description = 'Could not parse CRS'
            
            # Get pixel size
            geotransform = dataset.GetGeoTransform()
            resolution_text = 'Unknown'
            
            if geotransform:
                pixel_width = abs(geotransform[1])
                pixel_height = abs(geotransform[5])
                
                # Check if it's in degrees (EPSG:4326) or meters
                if 'EPSG:4326' in crs_text or 'WGS 84' in crs_description:
                    # Geographic coordinates - show as degrees
                    resolution_text = f'{pixel_width:.6f}° ({pixel_width * 111000:.1f}m at equator)'
                else:
                    # Projected coordinates - show as meters
                    resolution_text = f'{pixel_width:.2f}m'
            
            dataset = None  # Close dataset
            
            # Create rich display text with proper formatting
            filename = os.path.basename(file_path)
            
            # Multi-line display with emoji icons
            display_lines = [
                f'📊 {filename}',
                f'   Size: {width:,} × {height:,} px  |  Bands: {bands}',
                f'   Resolution: {resolution_text}',
                f'   CRS: {crs_text}'
            ]
            
            if crs_description:
                display_lines.append(f'   ({crs_description})')
            
            display_text = '\n'.join(display_lines)
            # Add to list
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, file_path)  # Store full path
            item.setToolTip(file_path)  # Show full path on hover
            self.list_widget.addItem(item)
            
            self.raster_paths.append(file_path)
            
            return True
            
        except Exception as e:
            QMessageBox.warning(
                self,
                'Error',
                f'Error reading raster:\n{file_path}\n\nError: {str(e)}'
            )
            return False
    
    def _remove_selected(self):
        """Remove selected rasters from the list."""
        selected_items = self.list_widget.selectedItems()
        
        if not selected_items:
            QMessageBox.information(
                self,
                'No Selection',
                'Please select rasters to remove.'
            )
            return
        
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            self.raster_paths.remove(file_path)
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
        
        self.rastersChanged.emit()
    
    def _clear_all(self):
        """Clear all rasters from the list."""
        if self.list_widget.count() == 0:
            return
        
        reply = QMessageBox.question(
            self,
            'Clear All Rasters',
            'Remove all rasters from the list?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.list_widget.clear()
            self.raster_paths.clear()
            self.rastersChanged.emit()
    
    def get_raster_paths(self):
        """
        Get list of all raster paths.
        
        Returns:
            list: List of raster file paths
        """
        return self.raster_paths.copy()
    
    def get_raster_count(self):
        """
        Get number of rasters in the list.
        
        Returns:
            int: Number of rasters
        """
        return len(self.raster_paths)