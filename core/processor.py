"""
Zonify Batch Processor

Main processing engine for batch zonal statistics.
Orchestrates the workflow from input validation to output creation.

NO ML/AI - pure statistical calculations
NO Cloud processing - local only
Single machine optimized

Author: Dragos Gontariu
License: GPL-3.0
"""
# FORCE RELOAD MARKER - DO NOT REMOVE
__RELOAD_TIMESTAMP__ = "2025-12-05"
print(f"★★★ PROCESSOR.PY LOADED - TIMESTAMP: {__RELOAD_TIMESTAMP__} ★★★")
import time
import os
import numpy as np
from osgeo import gdal
from qgis.core import (
    QgsVectorLayer, QgsField, QgsFeature, QgsGeometry,
    QgsVectorFileWriter, QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext
)
from qgis.PyQt.QtCore import QVariant
from ..utils.logger import Logger
from .zonal_calculator import ZonalCalculator
from ..algorithms.post_processing_engine import PostProcessingEngine
# Advanced features
try:
    from ..algorithms.custom_algorithm_engine import CustomAlgorithmManager
    from ..algorithms.time_series_engine import TimeSeriesAnalyzer
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False
    print("Warning: Advanced features not available (missing algorithms package)")

class BatchProcessor:
    """
    Batch processor for zonal statistics.
    
    Processes multiple rasters against a polygon layer,
    calculating statistics for each polygon-raster combination.
    """
    
    def __init__(self, config, progress_callback=None, progress_dialog=None):
        """
        Constructor.
        
        Args:
            config (dict): Processing configuration from UI
            progress_callback (callable): Function to call with progress updates
            progress_dialog: ProgressDialog instance (optional)
        """
        self.config = config
        self.progress_callback = progress_callback
        self.progress_dialog = progress_dialog
        
        # Processing state
        self.is_cancelled = False
        self.current_raster_index = 0
        self.processed_polygons = 0
        self.total_polygons = 0
        self.total_rasters = 0
        
        # Results
        self.errors = []
        self.start_time = None
        self.end_time = None
        
        # Logger
        self.logger = Logger('BatchProcessor')
        # Post-processing engine
        self.post_processing_engine = PostProcessingEngine()
        self.score_configs = []  # Will store score configurations
        # Initialize advanced features
        self.custom_algorithm_manager = None
        self.time_series_analyzer = None
        
        if ADVANCED_FEATURES_AVAILABLE:
            # Custom algorithms
            if config.get('custom_algorithms'):
                try:
                    self.custom_algorithm_manager = CustomAlgorithmManager(config['custom_algorithms'])
                    self.logger.info(f"✓ Initialized {len(config['custom_algorithms'])} custom algorithms")
                except Exception as e:
                    self.logger.error(f"Failed to initialize custom algorithms: {str(e)}")
            
            # Time series
            if config.get('time_series_config'):
                try:
                    self.time_series_analyzer = TimeSeriesAnalyzer(config['time_series_config'])
                    self.logger.info(f"✓ Initialized time series: {config['time_series_config']['name']}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize time series: {str(e)}")

    def cancel(self):
        """Cancel processing."""
        self.is_cancelled = True
        self.logger.warning('Processing cancelled by user')
    
    def run(self):
        """
        Main processing loop.
        
        Returns:
            dict: Results dictionary with success status and details
        """
        try:
            self.start_time = time.time()
            self.logger.info('=== STARTING BATCH PROCESSING ===')
            
            # Step 1: Validate inputs
            self._log_progress('Validating inputs...', 0)
            if not self._validate_inputs():
                return self._create_error_result('Input validation failed')
            
            # Step 2: Prepare output layer
            self._log_progress('Preparing output layer...', 5)
            output_layer = self._prepare_output_layer()
            if output_layer is None:
                return self._create_error_result('Failed to prepare output layer')
            
            # Step 3: Process each raster
            raster_paths = self.config['raster_paths']
            self.total_rasters = len(raster_paths)
            self.total_polygons = output_layer.featureCount()

            # LOG RASTERS TO BE PROCESSED
            self.logger.info(f"=== RASTERS TO PROCESS ===")
            self.logger.info(f"Total rasters: {len(raster_paths)}")
            for i, rpath in enumerate(raster_paths):
                self.logger.info(f"  Raster {i+1}: {os.path.basename(rpath)}")
                
                # Check if file exists
                if not os.path.exists(rpath):
                    self.logger.error(f"  ERROR: File does not exist!")
                else:
                    # Try to open with GDAL to check CRS
                    try:
                        from osgeo import gdal, osr
                        ds = gdal.Open(rpath)
                        if ds:
                            proj = ds.GetProjection()
                            srs = osr.SpatialReference()
                            srs.ImportFromWkt(proj)
                            self.logger.info(f"    CRS: {srs.GetAuthorityName(None)}:{srs.GetAuthorityCode(None)}")
                            ds = None
                        else:
                            self.logger.error(f"    ERROR: Could not open with GDAL")
                    except Exception as e:
                        self.logger.error(f"    ERROR reading CRS: {e}")

            self.logger.info("=" * 50)

            for raster_index, raster_path in enumerate(raster_paths):
                if self.is_cancelled:
                    return self._create_error_result('Processing cancelled')
                
                self.current_raster_index = raster_index
                
                # Process this raster
                raster_name = os.path.splitext(os.path.basename(raster_path))[0]
                self._log_progress(
                    f'Processing raster {raster_index + 1}/{self.total_rasters}: {raster_name}',
                    10 + (raster_index / self.total_rasters * 80)
                )
                
                success = self._process_raster(
                    raster_path,
                    raster_name,
                    output_layer
                )
                
                if not success:
                    self.logger.error(f'Failed to process raster: {raster_name}')
                    self.errors.append(f'Raster {raster_name}: Processing failed')
            
            # Step 3.4: Calculate Scores (after all rasters, before time series)
            if self.config.get('score_configs'):
                self._log_progress('Calculating scores...', 90)
                self._calculate_scores(output_layer)    

            # Step 3.5: Time Series Analysis (after all rasters processed)
            if self.time_series_analyzer:
                self._log_progress('Running time series analysis...', 92)
                self.logger.info('Starting time series analysis...')
                
                try:
                    # Add time series fields
                    ts_fields = self.time_series_analyzer.get_output_field_names()
                    for field_name in ts_fields:
                        if output_layer.fields().indexFromName(field_name) == -1:
                            # Determine field type
                            if field_name.endswith('_date'):
                                output_layer.addAttribute(QgsField(field_name, QVariant.String))
                            else:
                                output_layer.addAttribute(QgsField(field_name, QVariant.Double))
                    output_layer.updateFields()
                    
                    # Create calculator for time series
                    ts_calculator = ZonalCalculator(self.config)
                    
                    # Process each polygon
                    ts_count = 0
                    for feature in output_layer.getFeatures():
                        if self.is_cancelled:
                            break
                        
                        # Analyze this polygon
                        ts_results = self.time_series_analyzer.analyze(feature, ts_calculator)
                        
                        # Update feature
                        for field_name, value in ts_results.items():
                            field_index = output_layer.fields().indexFromName(field_name)
                            if field_index != -1:
                                output_layer.changeAttributeValue(feature.id(), field_index, value)
                        
                        ts_count += 1
                        
                        # Progress update
                        if ts_count % 50 == 0:
                            self._log_progress(
                                f'Time series: {ts_count}/{self.total_polygons} polygons',
                                92 + (ts_count / self.total_polygons * 3)
                            )
                    
                    
                    
                    
                    self.logger.info(f'✓ Time series analysis completed for {ts_count} polygons')
                
                except Exception as e:
                    self.logger.error(f'Time series analysis failed: {str(e)}')
                    import traceback
                    self.logger.error(traceback.format_exc()) 

            # Step 4: Finalize
            self._log_progress('Finalizing results...', 95)
            self._finalize_output(output_layer)
            
            # Step 5: Export additional formats (if requested)
            print("=" * 80)
            print("DEBUG: Checking export flags...")
            export_flags = {
                'csv': self.config.get('export_csv'),
                'html': self.config.get('export_html'),
                'pdf': self.config.get('export_pdf'),
                'json': self.config.get('export_json')
            }
            print(f"DEBUG: Export flags = {export_flags}")
            print(f"DEBUG: Config keys = {list(self.config.keys())}")
            print(f"DEBUG: export_html value = {self.config.get('export_html')}")
            print(f"DEBUG: export_html type = {type(self.config.get('export_html'))}")
            self.logger.info(f'Export flags: {export_flags}')
            print("=" * 80)
            
            if any([
                self.config.get('export_csv'),
                self.config.get('export_html'),
                self.config.get('export_pdf'),
                self.config.get('export_json')
            ]):
                print("DEBUG: Starting exports...")
                self._log_progress('Exporting additional formats...', 98)
                self.logger.info('CALLING _export_additional_formats')
                self._export_additional_formats(output_layer)
                self.logger.info('FINISHED _export_additional_formats')
            else:
                print("DEBUG: No exports selected")
                self.logger.info('No exports selected - skipping export step')
            
            self._log_progress('Complete!', 100)
            
            self.end_time = time.time()
            
            return self._create_success_result(output_layer)
            
        except Exception as e:
            self.logger.error(f'Fatal error during processing: {str(e)}')
            import traceback
            self.logger.error(traceback.format_exc())
            return self._create_error_result(str(e))

    def _validate_inputs(self):
        """Validate all inputs before processing."""
        self.logger.info('Validating inputs...')
        
        # Check polygon layer
        polygon_layer = self.config.get('polygon_layer')
        if not polygon_layer or not polygon_layer.isValid():
            self.logger.error('Invalid polygon layer')
            return False
        
        # Check raster paths
        raster_paths = self.config.get('raster_paths', [])
        if not raster_paths:
            self.logger.error('No raster files specified')
            return False
        
        # Verify raster files exist
        for raster_path in raster_paths:
            if not os.path.exists(raster_path):
                self.logger.error(f'Raster file not found: {raster_path}')
                return False
        
        # Check statistics
        statistics = self.config.get('statistics', [])
        if not statistics:
            self.logger.error('No statistics selected')
            return False
        
        self.logger.info('✓ Input validation passed')
        return True
    
    def _prepare_output_layer(self):
        """Prepare output layer (modify existing or create new)."""
        output_mode = self.config.get('output_mode', 'new')
        polygon_layer = self.config['polygon_layer']
        
        if output_mode == 'modify':
            # Modify existing layer
            self.logger.info('=== MODIFY MODE ===')
            self.logger.info('Using existing layer (modify mode)')
            output_layer = polygon_layer
            self.logger.info(f'Layer editable BEFORE startEditing? {output_layer.isEditable()}')
            output_layer.startEditing()
            self.logger.info(f'Layer editable AFTER startEditing? {output_layer.isEditable()}')
            return output_layer
        
        else:
            # Create new layer
            output_path = self.config.get('output_path')
            if not output_path:
                self.logger.error('No output path specified for new layer')
                return None
            
            self.logger.info(f'Creating new layer: {output_path}')
            
            # Get layer info
            crs = polygon_layer.crs()
            fields = polygon_layer.fields()
            geom_type = polygon_layer.wkbType()
            
            # Create writer options
            save_options = QgsVectorFileWriter.SaveVectorOptions()
            save_options.driverName = 'GPKG'
            save_options.fileEncoding = 'UTF-8'
            
            # Use QgsVectorFileWriter to create and write
            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                polygon_layer,
                output_path,
                QgsCoordinateTransformContext(),
                save_options
            )
            
            if error[0] != QgsVectorFileWriter.NoError:
                self.logger.error(f'Error creating output layer: {error[1]}')
                return None
            
            # Load the created layer
            output_layer = QgsVectorLayer(output_path, 'Zonify Output', 'ogr')
            
            if not output_layer.isValid():
                self.logger.error('Failed to load created output layer')
                return None
            
            self.logger.info('=== NEW LAYER MODE ===')
            self.logger.info(f'Layer editable BEFORE startEditing? {output_layer.isEditable()}')
            output_layer.startEditing()
            self.logger.info(f'Layer editable AFTER startEditing? {output_layer.isEditable()}')
            return output_layer
    
    def _add_custom_fields_upfront(self, output_layer, raster_name, statistics):
        """
        Pre-create all custom algorithm fields BEFORE processing loop.
        This prevents updateFields() calls during iteration which can cause data loss.
        """
        if not self.custom_algorithm_manager:
            return
        
        try:
            # Create dummy statistics dict to get all possible custom field names
            dummy_stats = {}
            for stat in statistics:
                field_name = f'{raster_name}_{stat}'
                dummy_stats[field_name] = 0.0
            
            # Get all custom aggregated field names
            try:
                custom_agg_results = self.custom_algorithm_manager.calculate_all_aggregated(dummy_stats)
                if custom_agg_results:
                    for field_name in custom_agg_results.keys():
                        if output_layer.fields().indexFromName(field_name) == -1:
                            output_layer.addAttribute(QgsField(field_name, QVariant.Double))
                            self.logger.debug(f'Pre-created custom aggregated field: {field_name}')
            except Exception as e:
                self.logger.warning(f'Could not pre-create custom aggregated fields: {e}')
            
            # Get all custom pixel field names (if applicable)
            if self.custom_algorithm_manager.has_pixel_algorithms():
                try:
                    dummy_pixels = {raster_name: [0.0]}  # Dummy pixel array
                    custom_pixel_results = self.custom_algorithm_manager.calculate_all_pixel(dummy_pixels)
                    if custom_pixel_results:
                        for field_name in custom_pixel_results.keys():
                            if output_layer.fields().indexFromName(field_name) == -1:
                                output_layer.addAttribute(QgsField(field_name, QVariant.Double))
                                self.logger.debug(f'Pre-created custom pixel field: {field_name}')
                except Exception as e:
                    self.logger.warning(f'Could not pre-create custom pixel fields: {e}')
            
            # Update fields ONCE after all additions
            output_layer.updateFields()
            self.logger.info('Pre-created all custom algorithm fields')
            
        except Exception as e:
            self.logger.error(f'Error pre-creating custom fields: {e}')
    
    def _process_raster(self, raster_path, raster_name, output_layer):
        """
        Process a single raster against all polygons.
        
        Args:
            raster_path (str): Path to raster file
            raster_name (str): Base name of raster (for field naming)
            output_layer (QgsVectorLayer): Output layer
            
        Returns:
            bool: Success status
        """
        try:
            # Reset polygon counter for this raster
            processed_count = 0
            # Open raster with GDAL (force fresh read)
            raster_ds = gdal.Open(raster_path, gdal.GA_ReadOnly)
            if raster_ds is None:
                self.logger.error(f'Failed to open raster: {raster_path}')
                return False

            # Force GDAL to actually read the projection from disk
            raster_ds.FlushCache()  # <-- Flush DATASET cache, not module
            proj = raster_ds.GetProjection()
            geotransform = raster_ds.GetGeoTransform()

            # Verify we got valid data
            if not proj or len(proj) < 10:
                self.logger.error(f'Raster has no valid projection: {raster_path}')
                return False

            # DEBUG: Log raster details
            from osgeo import osr
            srs = osr.SpatialReference()
            srs.ImportFromWkt(proj)
            self.logger.info(f"_process_raster: Raster={os.path.basename(raster_path)}")
            self.logger.info(f"  Full path: {raster_path}")
            self.logger.info(f"  CRS: {srs.GetAuthorityName(None)}:{srs.GetAuthorityCode(None)}")
            self.logger.info(f"  Geotransform: {geotransform}")
            self.logger.info(f"  Dataset ID: {id(raster_ds)}")
            # Get statistics to calculate
            statistics = self.config['statistics']
            
            # Add fields for this raster's statistics (if they don't exist)
            # Coverage is now treated as a regular statistic (coverage_pct)
            for stat in statistics:
                field_name = f'{raster_name}_{stat}'
                
                # Truncate field name to 63 characters (PostgreSQL limit)
                if len(field_name) > 63:
                    field_name = field_name[:63]
                
                # Check if field already exists
                if output_layer.fields().indexFromName(field_name) == -1:
                    output_layer.addAttribute(QgsField(field_name, QVariant.Double))

            output_layer.updateFields()
            
            # Pre-create ALL custom algorithm fields BEFORE processing loop
            # This prevents updateFields() during iteration which causes data loss
            self._add_custom_fields_upfront(output_layer, raster_name, statistics)
            
            # Create zonal calculator
            calculator = ZonalCalculator(self.config)
            
            # Process each polygon
            processed_count = 0
            for feature in output_layer.getFeatures():
                if self.is_cancelled:
                    return False
                
                # LOG ÎNAINTE DE APEL
                self.logger.info(f">>> About to call calculate_for_feature for feature {feature.id()} with raster {os.path.basename(raster_path)}")
                
                # Calculate statistics for this feature
                results = calculator.calculate_for_feature(
                    feature,
                    raster_path,
                    statistics  
                )
                
                # LOG DUPĂ APEL
                self.logger.info(f"<<< Returned from calculate_for_feature, results: {results}")
                
                # Update feature attributes
                for stat, value in results.items():
                    # All statistics use the same naming: {raster_name}_{stat}
                    field_name = f'{raster_name}_{stat}'
                    
                    if len(field_name) > 63:
                        field_name = field_name[:63]
                    
                    field_index = output_layer.fields().indexFromName(field_name)
                    
                    # DEBUG
                    self.logger.info(f'>>> Writing {stat}={value} to field "{field_name}", index={field_index}')
                    
                    if field_index != -1:
                        output_layer.changeAttributeValue(feature.id(), field_index, value)
                    else:
                        self.logger.warning(f'>>> Field "{field_name}" NOT FOUND in layer!')
                
                
                
                # === CUSTOM ALGORITHMS ===
                # MUTAT AFARĂ DIN LOOP!
                if self.custom_algorithm_manager:
                    try:
                        # Build full statistics dict with raster names as keys
                        full_stats = {}
                        for stat, value in results.items():
                            field_name = f'{raster_name}_{stat}'
                            full_stats[field_name] = value
                        
                        # Aggregated algorithms (use full statistics)
                        custom_agg_results = self.custom_algorithm_manager.calculate_all_aggregated(full_stats)
                        
                        if custom_agg_results:
                            # Fields already pre-created - just update values
                            for field_name, value in custom_agg_results.items():
                                field_index = output_layer.fields().indexFromName(field_name)
                                if field_index != -1:
                                    output_layer.changeAttributeValue(feature.id(), field_index, value)
                                else:
                                    self.logger.warning(f'Custom aggregated field not found: {field_name}')
                        
                        # Pixel-by-pixel algorithms
                        if self.custom_algorithm_manager.has_pixel_algorithms():
                            pixels = calculator.extract_pixels_for_custom(raster_path, feature)
                            if pixels is not None and len(pixels) > 0:
                                pixel_arrays = {raster_name: pixels}
                                custom_pixel_results = self.custom_algorithm_manager.calculate_all_pixel(pixel_arrays)
                                
                                if custom_pixel_results:
                                    # Fields already pre-created - just update values
                                    for field_name, value in custom_pixel_results.items():
                                        field_index = output_layer.fields().indexFromName(field_name)
                                        if field_index != -1:
                                            output_layer.changeAttributeValue(feature.id(), field_index, value)
                                        else:
                                            self.logger.warning(f'Custom pixel field not found: {field_name}')
                    
                    except Exception as e:
                        self.logger.warning(f"Custom algorithm failed for feature {feature.id()}: {str(e)}")
                
                processed_count += 1
                self.processed_polygons += 1
                
                # Update progress every 100 polygons
                if processed_count % 100 == 0:
                    # Calculate correct progress: base_progress + raster_progress
                    base_progress = 10 + (self.current_raster_index / self.total_rasters * 80)
                    raster_progress = (processed_count / self.total_polygons) * (80 / self.total_rasters)
                    total_progress = base_progress + raster_progress
                    
                    self._log_progress(
                        f'Processing: {processed_count}/{self.total_polygons} polygons',
                        total_progress
                    )
            
            # DON'T commit here - keep editing mode active for next rasters!
            # Final commit happens after all rasters are processed
            
            # Close raster and flush dataset cache
            if raster_ds:
                raster_ds.FlushCache()  # <-- Pe DATASET, nu pe module
                del raster_ds
            raster_ds = None

            self.logger.info(f'Closed raster dataset for: {raster_name}')
            
            self.logger.info(f'✓ Completed processing raster: {raster_name}')
            return True
            
        except Exception as e:
            self.logger.error(f'Error processing raster {raster_name}: {str(e)}')
            import traceback
            self.logger.error(traceback.format_exc())
            return False
        
    def _calculate_scores(self, output_layer):
        """
        Calculate configured scores for all features.
        
        Args:
            output_layer: Output vector layer
        """
        score_configs = self.config.get('score_configs', [])
        
        if not score_configs:
            return
        
        self.logger.info(f'Calculating {len(score_configs)} score(s)...')
        
        for score_config in score_configs:
            try:
                self._calculate_single_score(output_layer, score_config)
                self.logger.info(f"✓ Score '{score_config['name']}' calculated")
            except Exception as e:
                self.logger.error(f"Failed to calculate score '{score_config['name']}': {e}")
    
    def _calculate_single_score(self, layer, score_config):
        """
        Calculate a single score for all features.
        
        Args:
            layer: Vector layer
            score_config: Score configuration dict
        """
        from qgis.core import QgsField
        from qgis.PyQt.QtCore import QVariant
        
        score_name = score_config['name']
        indicators = score_config['indicators']  # {field_name: importance}
        weights = score_config['weights']  # {field_name: weight}
        normalization = score_config.get('normalization', 'Min-Max (0-100)')
        
        # Add score field if doesn't exist
        if layer.fields().indexOf(score_name) == -1:
            layer.addAttribute(QgsField(score_name, QVariant.Double))
        layer.updateFields()
        
        # Get field indices
        field_indices = {}
        for field_name in indicators.keys():
            idx = layer.fields().indexOf(field_name)
            if idx == -1:
                self.logger.warning(f"Field '{field_name}' not found in layer")
                continue
            field_indices[field_name] = idx
        
        if not field_indices:
            raise ValueError(f"No valid fields found for score '{score_name}'")
        
        # Extract all values for normalization
        field_values = {field: [] for field in field_indices.keys()}
        feature_ids = []
        
        for feature in layer.getFeatures():
            feature_ids.append(feature.id())
            for field_name, field_idx in field_indices.items():
                value = feature[field_idx]

                # Convert QVariant to native Python type
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
        
        # Normalize values
        normalized_values = {}
        
        if 'Min-Max' in normalization:
            for field_name, values in field_values.items():
                normalized_values[field_name] = self.post_processing_engine.normalize_minmax(
                    np.array(values),
                    output_range=(0, 100)
                )
        elif 'Z-Score' in normalization:
            for field_name, values in field_values.items():
                normalized_values[field_name] = self.post_processing_engine.normalize_zscore(
                    np.array(values)
                )
        else:  # No normalization
            normalized_values = {k: np.array(v) for k, v in field_values.items()}
        
        # Calculate weighted scores
        scores = self.post_processing_engine.weighted_sum(
            normalized_values,
            weights
        )
        
        # Update features
        score_field_idx = layer.fields().indexOf(score_name)
        
        for i, feature_id in enumerate(feature_ids):
            layer.changeAttributeValue(feature_id, score_field_idx, float(scores[i]))
        
        self.logger.info(f"Calculated score '{score_name}' for {len(feature_ids)} features")    
    
    def _finalize_output(self, output_layer):
        """Finalize output layer."""
        if output_layer.isEditable():
            output_layer.commitChanges()
        
            self.logger.info('Output layer committed and finalized')
        else:
            self.logger.warning('Output layer was not editable - no commit needed')
        
    def _export_additional_formats(self, output_layer):
        """
        Export to additional formats (CSV, HTML, PDF, JSON).
        
        Args:
            output_layer (QgsVectorLayer): Layer with results
        """
        print("=" * 80)
        print("DEBUG: _export_additional_formats CALLED!")
        self.logger.info('=== Starting additional format exports ===')
        
        base_path = self.config.get('output_path', '')
        if not base_path:
            self.logger.warning('No output path for additional exports')
            print("DEBUG: No base path - returning")
            return
        
        print(f"DEBUG: Base path = {base_path}")
        
        # Debug: show what's selected
        self.logger.info(f"Export flags - CSV: {self.config.get('export_csv')}, HTML: {self.config.get('export_html')}, PDF: {self.config.get('export_pdf')}, JSON: {self.config.get('export_json')}")
        
        # Import exporters
        from ..export.csv_exporter import CSVExporter
        from ..export.html_exporter import HTMLExporter
        from ..export.pdf_exporter import PDFExporter
        from ..export.json_exporter import JSONExporter
        
        # CSV Export
        if self.config.get('export_csv'):
            self.logger.info('Starting CSV export...')
            print("DEBUG: Starting CSV export...")
            try:
                exporter = CSVExporter()
                success, path, error = exporter.export(output_layer, base_path, self.config)
                if success:
                    self.logger.info(f'✓ CSV exported: {path}')
                    print(f"DEBUG: CSV success: {path}")
                else:
                    self.logger.error(f'✗ CSV export failed: {error}')
                    print(f"DEBUG: CSV failed: {error}")
                    self.errors.append(f'CSV: {error}')
            except Exception as e:
                self.logger.error(f'✗ CSV export exception: {str(e)}')
                print(f"DEBUG: CSV exception: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
        
        # HTML Export
        if self.config.get('export_html'):
            self.logger.info('Starting HTML export...')
            print("DEBUG: Starting HTML export...")
            try:
                # Add elapsed_time to config before export
                elapsed_time = time.time() - self.start_time
                self.config['elapsed_time'] = elapsed_time
                
                exporter = HTMLExporter()
                success, path, error = exporter.export(output_layer, base_path, self.config)
                if success:
                    self.logger.info(f'✓ HTML exported: {path}')
                    print(f"DEBUG: HTML success: {path}")
                else:
                    self.logger.error(f'✗ HTML export failed: {error}')
                    print(f"DEBUG: HTML failed: {error}")
                    self.errors.append(f'HTML: {error}')
            except Exception as e:
                self.logger.error(f'✗ HTML export exception: {str(e)}')
                print(f"DEBUG: HTML exception: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
        
        # PDF Export
        if self.config.get('export_pdf'):
            self.logger.info('Starting PDF export...')
            print("DEBUG: Starting PDF export...")
            try:
                # Add elapsed_time to config before export
                elapsed_time = time.time() - self.start_time
                self.config['elapsed_time'] = elapsed_time
                
                exporter = PDFExporter()
                success, path, error = exporter.export(output_layer, base_path, self.config)
                if success:
                    self.logger.info(f'✓ PDF exported: {path}')
                    print(f"DEBUG: PDF success: {path}")
                else:
                    self.logger.error(f'✗ PDF export failed: {error}')
                    print(f"DEBUG: PDF failed: {error}")
                    self.errors.append(f'PDF: {error}')
            except Exception as e:
                self.logger.error(f'✗ PDF export exception: {str(e)}')
                print(f"DEBUG: PDF exception: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
        else:
            self.logger.info('PDF export not selected (checkbox not checked)')
            print("DEBUG: PDF not selected")
        
        # JSON Export
        if self.config.get('export_json'):
            self.logger.info('Starting JSON export...')
            print("DEBUG: Starting JSON export...")
            try:
                exporter = JSONExporter()
                success, paths, error = exporter.export(output_layer, base_path, self.config)
                if success:
                    for path in paths:
                        self.logger.info(f'✓ JSON exported: {path}')
                        print(f"DEBUG: JSON success: {path}")
                else:
                    self.logger.error(f'✗ JSON export failed: {error}')
                    print(f"DEBUG: JSON failed: {error}")
                    self.errors.append(f'JSON: {error}')
            except Exception as e:
                self.logger.error(f'✗ JSON export exception: {str(e)}')
                print(f"DEBUG: JSON exception: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
        
        print("=" * 80)
        self.logger.info('=== Finished additional format exports ===')
    
    def _log_progress(self, message, percent):
        """
        Log progress and call callback.
        
        Args:
            message (str): Progress message
            percent (int): Progress percentage
        """
        self.logger.info(f'[{percent}%] {message}')
        
        progress_data = {
            'message': message,
            'percent': percent,
            'current_raster': self.current_raster_index + 1,
            'total_rasters': self.total_rasters,
            'processed_polygons': self.processed_polygons,
            'total_polygons': self.total_polygons
        }
        
        if self.progress_callback:
            self.progress_callback(progress_data)
        
        if self.progress_dialog:
            self.progress_dialog.update_progress(progress_data)
            self.progress_dialog.log(message)
    
    def _create_success_result(self, output_layer):
        """Create success result dictionary."""
        elapsed_time = self.end_time - self.start_time if self.end_time else 0
        
        return {
            'success': True,
            'output_layer': output_layer,
            'processed_rasters': self.total_rasters,
            'processed_polygons': self.processed_polygons,
            'elapsed_time': elapsed_time,
            'errors': self.errors
        }
    
    def _create_error_result(self, error_message):
        """Create error result dictionary."""
        return {
            'success': False,
            'error': error_message,
            'processed_rasters': self.current_raster_index,
            'processed_polygons': self.processed_polygons,
            'errors': self.errors
        }
 