"""
Input Validators for Zonify

Validates user inputs and provides helpful error messages.

Author: Dragos Gontariu
License: GPL-3.0
"""

from qgis.core import QgsVectorLayer, QgsRasterLayer
from osgeo import gdal
import os


class InputValidator:
    """
    Validate processing inputs.
    """
    
    @staticmethod
    def validate_polygon_layer(layer):
        """
        Validate polygon layer.
        
        Args:
            layer (QgsVectorLayer): Layer to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if layer is None:
            return False, "No polygon layer selected"
        
        if not layer.isValid():
            return False, "Polygon layer is invalid"
        
        if layer.featureCount() == 0:
            return False, "Polygon layer has no features"
        
        # Check geometry type
        geom_type = layer.geometryType()
        if geom_type != 2:  # 2 = Polygon
            return False, f"Layer is not a polygon layer (type: {geom_type})"
        
        # Check CRS
        if not layer.crs().isValid():
            return False, "Polygon layer has invalid CRS"
        
        return True, ""
    
    @staticmethod
    def validate_raster_paths(raster_paths):
        """
        Validate raster file paths.
        
        Args:
            raster_paths (list): List of raster paths
            
        Returns:
            tuple: (is_valid, error_message, invalid_rasters)
        """
        if not raster_paths:
            return False, "No raster files selected", []
        
        invalid_rasters = []
        
        for raster_path in raster_paths:
            # Check if file exists
            if not os.path.exists(raster_path):
                invalid_rasters.append((raster_path, "File not found"))
                continue
            
            # Try to open with GDAL
            ds = gdal.Open(raster_path)
            if ds is None:
                invalid_rasters.append((raster_path, "Cannot open with GDAL"))
                continue
            
            # Check if has at least one band
            if ds.RasterCount == 0:
                invalid_rasters.append((raster_path, "No raster bands"))
                ds = None
                continue
            
            # Check CRS
            projection = ds.GetProjection()
            if not projection:
                invalid_rasters.append((raster_path, "No CRS defined"))
            
            ds = None
        
        if invalid_rasters:
            error_msg = f"{len(invalid_rasters)} invalid raster(s):\n"
            for path, reason in invalid_rasters[:5]:  # Show first 5
                filename = os.path.basename(path)
                error_msg += f"  • {filename}: {reason}\n"
            
            if len(invalid_rasters) > 5:
                error_msg += f"  ... and {len(invalid_rasters) - 5} more"
            
            return False, error_msg, invalid_rasters
        
        return True, "", []
    
    @staticmethod
    def validate_statistics(statistics):
        """
        Validate statistics selection.
        
        Args:
            statistics (list): List of statistic names
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not statistics:
            return False, "No statistics selected"
        
        valid_stats = [
            'mean', 'sum', 'min', 'max', 'median', 'mode',
            'count', 'range', 'stddev', 'variance', 'cv',
            'p10', 'p25', 'p50', 'p75', 'p90', 'p95'
        ]
        
        invalid_stats = [s for s in statistics if s not in valid_stats]
        
        if invalid_stats:
            return False, f"Invalid statistics: {', '.join(invalid_stats)}"
        
        return True, ""
    
    @staticmethod
    def validate_output_path(output_path, output_mode):
        """
        Validate output path.
        
        Args:
            output_path (str): Output file path
            output_mode (str): 'modify' or 'new'
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if output_mode == 'modify':
            return True, ""  # No output path needed
        
        if not output_path:
            return False, "No output path specified"
        
        # Check if directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            return False, f"Output directory does not exist: {output_dir}"
        
        # Check file extension
        if not output_path.lower().endswith('.gpkg'):
            return False, "Output file must have .gpkg extension"
        
        return True, ""
    
    @staticmethod
    def validate_all(config):
        """
        Validate entire configuration.
        
        Args:
            config (dict): Processing configuration
            
        Returns:
            tuple: (is_valid, error_messages_list)
        """
        errors = []
        
        # Validate polygon layer
        valid, msg = InputValidator.validate_polygon_layer(
            config.get('polygon_layer')
        )
        if not valid:
            errors.append(f"Polygon Layer: {msg}")
        
        # Validate rasters
        valid, msg, _ = InputValidator.validate_raster_paths(
            config.get('raster_paths', [])
        )
        if not valid:
            errors.append(f"Rasters: {msg}")
        
        # Validate statistics
        valid, msg = InputValidator.validate_statistics(
            config.get('statistics', [])
        )
        if not valid:
            errors.append(f"Statistics: {msg}")
        
        # Validate output
        valid, msg = InputValidator.validate_output_path(
            config.get('output_path', ''),
            config.get('output_mode', 'new')
        )
        if not valid:
            errors.append(f"Output: {msg}")
        
        return len(errors) == 0, errors