"""
JSON/GeoJSON Exporter for Zonify

Exports zonal statistics results to JSON and GeoJSON formats.

Author: Dragos Gontariu
License: GPL-3.0
"""

import json
import os
from ..utils.logger import Logger


class JSONExporter:
    """
    Export results to JSON/GeoJSON format.
    """
    
    def __init__(self):
        """Constructor."""
        self.logger = Logger('JSONExporter')
    
    def export(self, output_layer, output_path, config):
        """
        Export layer to JSON and GeoJSON.
        
        Args:
            output_layer (QgsVectorLayer): Layer with results
            output_path (str): Base output path
            config (dict): Export configuration
            
        Returns:
            tuple: (success, output_files_list, error_message)
        """
        try:
            self.logger.info('Starting JSON export')
            
            output_files = []
            
            # Export regular JSON (no geometry)
            json_path = output_path.replace('.gpkg', '.json')
            if json_path == output_path:
                json_path = output_path + '.json'
            
            self._export_json(output_layer, json_path, config)
            output_files.append(json_path)
            
            # Export GeoJSON (with geometry)
            geojson_path = output_path.replace('.gpkg', '.geojson')
            if geojson_path == output_path:
                geojson_path = output_path + '.geojson'
            
            self._export_geojson(output_layer, geojson_path, config)
            output_files.append(geojson_path)
            
            self.logger.info(f'JSON export completed')
            return True, output_files, ''
            
        except Exception as e:
            self.logger.error(f'JSON export failed: {str(e)}')
            import traceback
            self.logger.error(traceback.format_exc())
            return False, [], str(e)
    
    def _export_json(self, layer, output_path, config):
        """Export to regular JSON (attributes only)."""
        
        # Get fields
        fields = layer.fields()
        field_names = [field.name() for field in fields]
        
        # Collect features
        features_data = []
        for feature in layer.getFeatures():
            feature_dict = {'id': feature.id()}
            
            for field_name in field_names:
                value = feature[field_name]
                
                # Convert QVariant to Python type
                if value is None or (hasattr(value, 'isNull') and value.isNull()):
                    feature_dict[field_name] = None
                else:
                    # Convert to native Python type
                    feature_dict[field_name] = value if not hasattr(value, 'value') else value.value()
            
            features_data.append(feature_dict)
        
        # Build final JSON
        output_data = {
            'type': 'FeatureCollection',
            'metadata': {
                'name': layer.name(),
                'count': layer.featureCount(),
                'rasters_processed': config.get('raster_count', 0),
                'statistics': config.get('statistics', []),
                'processing_time': config.get('elapsed_time', 0)
            },
            'features': features_data
        }
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f'JSON exported: {output_path}')
    
    def _export_geojson(self, layer, output_path, config):
        """Export to GeoJSON (with geometry)."""
        
        # Get fields
        fields = layer.fields()
        field_names = [field.name() for field in fields]
        
        # Collect features
        features_data = []
        for feature in layer.getFeatures():
            # Get geometry
            geom = feature.geometry()
            geom_json = json.loads(geom.asJson())
            
            # Get properties
            properties = {}
            for field_name in field_names:
                value = feature[field_name]
                
                # Convert QVariant to Python type
                if value is None or (hasattr(value, 'isNull') and value.isNull()):
                    properties[field_name] = None
                else:
                    properties[field_name] = value if not hasattr(value, 'value') else value.value()
            
            # Build feature
            feature_geojson = {
                'type': 'Feature',
                'id': feature.id(),
                'geometry': geom_json,
                'properties': properties
            }
            
            features_data.append(feature_geojson)
        
        # Build GeoJSON
        output_data = {
            'type': 'FeatureCollection',
            'name': layer.name(),
            'crs': {
                'type': 'name',
                'properties': {
                    'name': layer.crs().authid()
                }
            },
            'features': features_data
        }
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f'GeoJSON exported: {output_path}')