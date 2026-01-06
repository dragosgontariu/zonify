"""
CSV Exporter for Zonify

Exports zonal statistics results to CSV format.
Creates clean, simple CSV files suitable for Excel, R, Python, etc.

Author: Dragos Gontariu
License: GPL-3.0
"""

import csv
import os
from ..utils.logger import Logger


class CSVExporter:
    """
    Export results to CSV format.
    """
    
    def __init__(self):
        """Constructor."""
        self.logger = Logger('CSVExporter')
    
    def export(self, output_layer, output_path, config):
        """
        Export layer to CSV.
        
        Args:
            output_layer (QgsVectorLayer): Layer with results
            output_path (str): Base output path (without extension)
            config (dict): Export configuration
            
        Returns:
            tuple: (success, output_file_path, error_message)
        """
        try:
            self.logger.info('Starting CSV export')
            
            # Determine output file path
            csv_path = output_path.replace('.gpkg', '.csv')
            if csv_path == output_path:
                csv_path = output_path + '.csv'
            
            # Get all fields
            fields = output_layer.fields()
            field_names = [field.name() for field in fields]
            
            self.logger.info(f'Exporting {len(field_names)} fields')
            
            # Open CSV file
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(field_names)
                
                # Write data
                feature_count = 0
                for feature in output_layer.getFeatures():
                    row = []
                    for field_name in field_names:
                        value = feature[field_name]
                        
                        # Handle None/NULL
                        if value is None:
                            row.append('')
                        else:
                            row.append(value)
                    
                    writer.writerow(row)
                    feature_count += 1
                
                self.logger.info(f'Exported {feature_count} features to CSV')
            
            return True, csv_path, ''
            
        except Exception as e:
            self.logger.error(f'CSV export failed: {str(e)}')
            import traceback
            self.logger.error(traceback.format_exc())
            return False, '', str(e)