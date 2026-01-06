"""
Zonify Zonal Statistics Calculator

Calculates statistics for a polygon from a raster.
Handles automatic CRS transformation when polygon and raster have different CRS.

Supports:
- Basic statistics (mean, sum, min, max, count)
- Advanced statistics (median, mode, stddev, variance, CV)
- Percentiles (P10, P25, P50, P75, P90, P95)
- Automatic CRS detection and transformation

Handles:
- NoData values
- Coordinate system transformations (automatic)
- Memory-efficient processing

Author: Dragos Gontariu
License: GPL-3.0
"""
import os
from osgeo import gdal, ogr, osr
import numpy as np
from qgis.core import QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from ..utils.logger import Logger


class ZonalCalculator:
    """
    Calculate zonal statistics for polygons with automatic CRS handling.
    """
    
    def __init__(self, config):
        """
        Constructor.
        
        Args:
            config (dict): Processing configuration
        """
        self.config = config
        self.logger = Logger('ZonalCalculator')
        
        # NoData handling
        self.handle_nodata = config.get('handle_nodata', True)
        
        # Minimum coverage threshold (0.0 = accept any coverage)
        self.min_coverage_percent = config.get('min_coverage_percent', 0.0)
        
        # Get polygon layer CRS
        poly_layer = config.get('polygon_layer')
        if poly_layer:
            self.poly_crs = poly_layer.crs()
            self.logger.info(f'Polygon layer CRS: {self.poly_crs.authid()}')
        else:
            self.poly_crs = None
            self.logger.warning('No polygon layer in config')
    
    def _safe_pct(self, x):
        """
        Safely convert coverage percentage to float, handling NaN/inf.
        
        Args:
            x: Value to sanitize
            
        Returns:
            float: Safe percentage value (0.0 if invalid)
        """
        try:
            if x is None:
                return 0.0
            x = float(x)
            if not np.isfinite(x):
                return 0.0
            return round(x, 2)
        except Exception:
            return 0.0
    
    def calculate_for_feature(self, feature, raster_path, statistics):
        """
        Calculate statistics for a single feature (polygon).
        
        Args:
            feature (QgsFeature): Polygon feature
            raster_ds (gdal.Dataset): Raster dataset
            statistics (list): List of statistic names to calculate
            
        Returns:
            dict: Dictionary of statistic_name: value
        """
        try:
            # PRIMUL LOG - să vedem dacă ajunge aici
            self.logger.info(f"=== ENTER calculate_for_feature: {os.path.basename(raster_path)} ===")
            # Open fresh dataset
            raster_ds = gdal.Open(raster_path)
            if not raster_ds:
                self.logger.error(f"Failed to open raster: {raster_path}")
                results = {stat: None for stat in statistics}
                results['coverage_pct'] = 0.0
                return results
                
            self.logger.info(f"calculate_for_feature OPENED: {os.path.basename(raster_path)}")
            # === DEBUG: Log what we actually opened ===
            from osgeo import osr
            proj_wkt = raster_ds.GetProjection()
            srs = osr.SpatialReference()
            srs.ImportFromWkt(proj_wkt)
            self.logger.info(f"calculate_for_feature OPENED: {os.path.basename(raster_path)}")
            self.logger.info(f"  WKT snippet: {proj_wkt[:150]}")
            self.logger.info(f"  GDAL says CRS: {srs.GetAuthorityName(None)}:{srs.GetAuthorityCode(None)}")
            # Get feature geometry
            geom = feature.geometry()
            
            self.logger.debug(f'Processing feature ID: {feature.id()}')
            
            if geom.isEmpty():
                self.logger.warning(f'Feature {feature.id()} has empty geometry')
                results = {stat: None for stat in statistics}
                results['coverage_pct'] = 0.0
                return results
            
            if not geom.isGeosValid():
                self.logger.warning(f'Feature {feature.id()} has invalid geometry')
                results = {stat: None for stat in statistics}
                results['coverage_pct'] = 0.0
                return results
            
            # Log geometry info
            bbox = geom.boundingBox()
            self.logger.debug(f'Geometry bbox: {bbox.xMinimum():.6f}, {bbox.yMinimum():.6f}, {bbox.xMaximum():.6f}, {bbox.yMaximum():.6f}')
            # DEBUG: Log what CRS we think the raster has
            from osgeo import osr
            proj = raster_ds.GetProjection()
            srs = osr.SpatialReference()
            srs.ImportFromWkt(proj)
            self.logger.info(f"calculate_for_feature: About to extract pixels, raster CRS={srs.GetAuthorityName(None)}:{srs.GetAuthorityCode(None)}")
            # Extract pixel values within polygon (now returns tuple)
            extraction_result = self._extract_pixels(geom, raster_ds, feature.id())
            # Calculate geometric coverage if requested
            if extraction_result and 'coverage_pct' in statistics:
                pixel_values, _ = extraction_result  # Ignore default coverage
                coverage_pct = self._calculate_geometric_coverage(geom, raster_ds)
                extraction_result = (pixel_values, coverage_pct)  # Replace with geometric

            # CRITICAL: Check None BEFORE unpacking
            if extraction_result is None:
                self.logger.warning(f'Feature {feature.id()}: No pixels extracted (returned None)')
                # Return coverage 0% for all stats
                results = {stat: None for stat in statistics}
                results['coverage_pct'] = 0.0
                return results

            # Unpack the tuple
            pixel_values, coverage_pct = extraction_result
            # DEBUG - handle None safely
            if coverage_pct is not None:
                self.logger.info(f'>>> DEBUG: Feature {feature.id()}, coverage_pct = {coverage_pct:.2f}%')
            else:
                self.logger.info(f'>>> DEBUG: Feature {feature.id()}, coverage_pct = None')
            # Check if pixel_values is None
            if pixel_values is None:
                self.logger.warning(f'Feature {feature.id()}: No valid pixel values')
                results = {stat: None for stat in statistics}
                results['coverage_pct'] = self._safe_pct(coverage_pct)
                return results

            # Check minimum coverage threshold
            if coverage_pct < self.min_coverage_percent:
                self.logger.debug(f'Feature {feature.id()}: coverage {coverage_pct:.1f}% below threshold {self.min_coverage_percent}%')
                results = {stat: None for stat in statistics}
                results['coverage_pct'] = self._safe_pct(coverage_pct)
                return results

            if len(pixel_values) == 0:
                self.logger.warning(f'Feature {feature.id()}: No pixels found (empty array)')
                results = {stat: None for stat in statistics}
                results['coverage_pct'] = self._safe_pct(coverage_pct)
                return results
            
            self.logger.debug(f'Feature {feature.id()}: Found {len(pixel_values)} pixels, min={pixel_values.min():.2f}, max={pixel_values.max():.2f}')
            
            # Calculate requested statistics
            # Coverage is handled separately (already calculated from extraction)
            results = {'coverage_pct': self._safe_pct(coverage_pct)}
            
            for stat in statistics:
                # Skip coverage_pct - already added above
                if stat == 'coverage_pct':
                    continue
                    
                value = self._calculate_statistic(stat, pixel_values)
                results[stat] = value
                self.logger.debug(f'Feature {feature.id()}: {stat} = {value}')

            # DEBUG - Verifică dacă coverage_pct e în results
            self.logger.info(f'>>> DEBUG: Final results = {results}')
            self.logger.info(f'>>> DEBUG: coverage_pct in results? {"coverage_pct" in results}')  
              
            del raster_ds
            return results
            
        except Exception as e:
            self.logger.error(f'Error calculating statistics for feature {feature.id()}: {str(e)}')
            import traceback
            self.logger.error(traceback.format_exc())
            # Always return coverage_pct to avoid NULL fields
            results = {stat: None for stat in statistics}
            results['coverage_pct'] = 0.0
            return results
    
    def _extract_pixels(self, geom, raster_ds, fid=None):
        """
        Extract pixel values within a polygon geometry.
        Uses QGIS coordinate transformation (more reliable than OSR).
        
        Args:
            geom (QgsGeometry): Polygon geometry (in polygon layer CRS)
            raster_ds (gdal.Dataset): Raster dataset
            fid: Feature ID for logging
            
        Returns:
            tuple: (pixel_values, coverage_pct) or (None, 0.0)
        """
        try:
            self.logger.info('=== Starting _extract_pixels ===')
            
            # Get raster info
            gt = raster_ds.GetGeoTransform()
            band = raster_ds.GetRasterBand(1)
            nodata = band.GetNoDataValue()
            
            self.logger.info(f"Raster NoData value: {nodata}")
            self.logger.info(f"Raster size: {raster_ds.RasterXSize} x {raster_ds.RasterYSize}")
            
            # Get raster CRS
            raster_projection = raster_ds.GetProjection()
            raster_srs = osr.SpatialReference()
            raster_srs.ImportFromWkt(raster_projection)
            
            # Create QGIS CRS from raster
            raster_crs = QgsCoordinateReferenceSystem()
            raster_crs.createFromWkt(raster_projection)

            if not raster_crs.isValid():
                self.logger.error('Invalid raster CRS')
                return None, 0.0

            self.logger.info(f'Raster CRS: {raster_crs.authid()}')
            
            # Transform geometry if needed
            transformed_geom = geom
            
            if self.poly_crs and self.poly_crs != raster_crs:
                self.logger.info(f'Transforming polygon from {self.poly_crs.authid()} to {raster_crs.authid()}')
                
                transform = QgsCoordinateTransform(
                    self.poly_crs,
                    raster_crs,
                    QgsProject.instance()
                )
                
                transformed_geom = QgsGeometry(geom)
                result = transformed_geom.transform(transform)
                
                if result != 0:
                    self.logger.error(f'Transformation failed with code: {result}')
                    return None, 0.0
                
                bbox_transformed = transformed_geom.boundingBox()
                self.logger.info(f'Transformed bbox: X=[{bbox_transformed.xMinimum():.2f}, {bbox_transformed.xMaximum():.2f}], Y=[{bbox_transformed.yMinimum():.2f}, {bbox_transformed.yMaximum():.2f}]')
            
            # Convert to OGR geometry
            ogr_geom = ogr.CreateGeometryFromWkt(transformed_geom.asWkt())
            
            if ogr_geom is None:
                self.logger.error('Failed to create OGR geometry')
                return None, 0.0
            
            # Get envelope
            env = ogr_geom.GetEnvelope()
            minx, maxx, miny, maxy = env
            
            # Convert to pixel coordinates
            px_min = int((minx - gt[0]) / gt[1])
            px_max = int((maxx - gt[0]) / gt[1]) + 1
            py_min = int((maxy - gt[3]) / gt[5])
            py_max = int((miny - gt[3]) / gt[5]) + 1
            
            # Clip to raster bounds
            px_min = max(0, px_min)
            py_min = max(0, py_min)
            px_max = min(raster_ds.RasterXSize, px_max)
            py_max = min(raster_ds.RasterYSize, py_max)
            
            width = px_max - px_min
            height = py_max - py_min
            
            self.logger.info(f'Pixel window: x={px_min}, y={py_min}, size={width}x{height}')
            
            if width <= 0 or height <= 0:
                self.logger.warning(f'Empty pixel window ({width}x{height})')
                return None, 0.0
            
            # Read raster data
            data = band.ReadAsArray(px_min, py_min, width, height)
            
            if data is None:
                self.logger.error('Failed to read raster data')
                return None, 0.0
            
            # Create mask raster
            mem_driver = gdal.GetDriverByName('MEM')
            mask_ds = mem_driver.Create('', width, height, 1, gdal.GDT_Byte)
            
            # Set geotransform for mask
            mask_gt = [
                gt[0] + px_min * gt[1],
                gt[1],
                0,
                gt[3] + py_min * gt[5],
                0,
                gt[5]
            ]
            mask_ds.SetGeoTransform(mask_gt)
            mask_ds.SetProjection(raster_projection)
            
            # Rasterize geometry
            mask_band = mask_ds.GetRasterBand(1)
            mask_band.Fill(0)
            
            # Create temp vector layer
            mem_vector_ds = ogr.GetDriverByName('Memory').CreateDataSource('')
            mem_layer = mem_vector_ds.CreateLayer('mask', srs=raster_srs)
            
            layer_defn = mem_layer.GetLayerDefn()
            ogr_feature = ogr.Feature(layer_defn)
            ogr_feature.SetGeometry(ogr_geom)
            mem_layer.CreateFeature(ogr_feature)
            
            # Rasterize with ALL_TOUCHED
            err = gdal.RasterizeLayer(
                mask_ds, 
                [1], 
                mem_layer, 
                burn_values=[1],
                options=['ALL_TOUCHED=TRUE']
            )
            
            if err != 0:
                self.logger.error(f'Rasterize error: {err}')
                return None, 0.0
            
            # Read mask
            mask = mask_band.ReadAsArray()
            
            if mask is None:
                self.logger.error('Failed to read mask')
                return None, 0.0
            
            # Extract pixels
            masked_data = data[mask == 1]
            
            self.logger.info(f'Pixels in mask: {len(masked_data)}')
            
            if len(masked_data) == 0:
                self.logger.warning('No pixels in mask')
                return None, 0.0
            
            # === CRITICAL FIX: PROPER NoData FILTERING ===
            import numpy as np
            
            # Filter NoData values CORRECTLY
            if nodata is not None:
                # Handle different data types and NoData representations
                if np.isnan(nodata):
                    # NoData is NaN
                    valid_mask = ~np.isnan(masked_data)
                else:
                    # Convert both to float for reliable comparison
                    masked_data_float = masked_data.astype(np.float64)
                    nodata_float = float(nodata)
                    
                    # Use tolerance for float comparison
                    # For NoData=255 or other integer values, tolerance should be small
                    if abs(nodata_float) > 1e10:  # Very large NoData (like -3.4e38)
                        valid_mask = masked_data_float != nodata_float
                    else:  # Normal NoData values
                        valid_mask = ~np.isclose(masked_data_float, nodata_float, rtol=0, atol=0.001)
                
                # Also filter NaN and Inf
                valid_mask = valid_mask & np.isfinite(masked_data.astype(np.float64))
                
                masked_values = masked_data[valid_mask]
            else:
                # No NoData value - just filter NaN/Inf
                masked_values = masked_data[np.isfinite(masked_data.astype(np.float64))]
            
            self.logger.info(f'Valid pixels after NoData filtering: {len(masked_values)}')
            
            if len(masked_values) == 0:
                self.logger.warning('No valid pixels after filtering NoData')
                return None, 0.0
            
            # Log statistics
            self.logger.info(f'Extracted pixels: {len(masked_values)}')
            self.logger.info(f'  Unique values: {np.unique(masked_values)[:20]}')  # First 20
            self.logger.info(f'  Range: {masked_values.min():.4f} - {masked_values.max():.4f}')
            self.logger.info(f'  Mean: {masked_values.mean():.4f}')
            self.logger.info(f'  Sum: {masked_values.sum():.2f}')
            
            # Cleanup
            mask_ds = None
            mem_vector_ds = None
            ogr_geom = None
            
            # Return pixels and default coverage (will be recalculated if needed)
            return masked_values, 0.0
            
        except Exception as e:
            self.logger.error(f'Error extracting pixels: {str(e)}')
            import traceback
            self.logger.error(traceback.format_exc())
            return None, 0.0
        
    def _calculate_geometric_coverage(self, geom, raster_ds, nodata_threshold=0.0000001):
        """
        Calculate geometric coverage - precise pixel-by-pixel intersection.
        
        Args:
            geom: QgsGeometry of polygon (in polygon layer CRS)
            raster_ds: GDAL raster dataset
            nodata_threshold: Minimum value to consider valid
            
        Returns:
            float: Coverage percentage (0-100)
        """
        from osgeo import ogr, osr
        
        try:
            self.logger.info('=== GEOMETRIC COVERAGE: Pixel-by-pixel intersection ===')
            
            # STEP 1: Transform geometry to raster CRS
            from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
            
            raster_srs = osr.SpatialReference()
            raster_srs.ImportFromWkt(raster_ds.GetProjection())
            raster_crs = QgsCoordinateReferenceSystem(raster_srs.ExportToWkt())
            
            if self.poly_crs and self.poly_crs != raster_crs:
                transform = QgsCoordinateTransform(self.poly_crs, raster_crs, QgsProject.instance())
                geom_transformed = QgsGeometry(geom)
                geom_transformed.transform(transform)
            else:
                geom_transformed = geom
            
            # Create OGR geometry
            ogr_geom = ogr.CreateGeometryFromWkt(geom_transformed.asWkt())
            polygon_area = ogr_geom.GetArea()
            
            if polygon_area == 0:
                self.logger.warning('Polygon has zero area')
                return 0.0
            
            # STEP 2: Get raster info
            gt = raster_ds.GetGeoTransform()
            band = raster_ds.GetRasterBand(1)
            
            pixel_width = abs(gt[1])   # Pixel width in map units
            pixel_height = abs(gt[5])  # Pixel height in map units
            
            # STEP 3: Get bounding box in pixel coordinates
            envelope = ogr_geom.GetEnvelope()  # (minX, maxX, minY, maxY)
            minX, maxX, minY, maxY = envelope
            
            # Convert to pixel coordinates
            px_min = int((minX - gt[0]) / gt[1])
            px_max = int((maxX - gt[0]) / gt[1]) + 1
            py_min = int((maxY - gt[3]) / gt[5])  # Note: Y is inverted
            py_max = int((minY - gt[3]) / gt[5]) + 1
            
            # Clip to raster bounds
            px_min = max(0, px_min)
            py_min = max(0, py_min)
            px_max = min(raster_ds.RasterXSize, px_max)
            py_max = min(raster_ds.RasterYSize, py_max)
            
            width = px_max - px_min
            height = py_max - py_min
            
            if width <= 0 or height <= 0:
                self.logger.warning('No pixels in bounding box')
                return 0.0
            
            # STEP 4: Read raster data
            data = band.ReadAsArray(px_min, py_min, width, height)
            
            if data is None:
                self.logger.error('Failed to read raster data')
                return 0.0
            
            self.logger.debug(f'Processing {width}x{height} pixels')
            
            # STEP 5: Calculate intersection area pixel by pixel
            total_intersection_area = 0.0
            valid_pixels_count = 0
            
            for py in range(height):
                for px in range(width):
                    pixel_value = data[py, px]
                    
                    # Check if pixel is valid (> threshold, not NaN, finite)
                    if not (np.isfinite(pixel_value) and pixel_value > nodata_threshold):
                        continue
                    
                    valid_pixels_count += 1
                    
                    # Calculate pixel bounds in map coordinates
                    pixel_x = gt[0] + (px_min + px) * gt[1]
                    pixel_y = gt[3] + (py_min + py) * gt[5]
                    
                    # Create pixel geometry (square)
                    pixel_ring = ogr.Geometry(ogr.wkbLinearRing)
                    pixel_ring.AddPoint(pixel_x, pixel_y)
                    pixel_ring.AddPoint(pixel_x + pixel_width, pixel_y)
                    pixel_ring.AddPoint(pixel_x + pixel_width, pixel_y - pixel_height)
                    pixel_ring.AddPoint(pixel_x, pixel_y - pixel_height)
                    pixel_ring.AddPoint(pixel_x, pixel_y)  # Close ring
                    
                    pixel_geom = ogr.Geometry(ogr.wkbPolygon)
                    pixel_geom.AddGeometry(pixel_ring)
                    
                    # Calculate intersection
                    intersection = pixel_geom.Intersection(ogr_geom)
                    
                    if intersection and not intersection.IsEmpty():
                        intersection_area = intersection.Area()
                        total_intersection_area += intersection_area
            
            # STEP 6: Calculate coverage percentage
            coverage_pct = (total_intersection_area / polygon_area) * 100.0
            
            self.logger.info(f'Geometric coverage: {coverage_pct:.2f}% (intersection={total_intersection_area:.2f}m², polygon={polygon_area:.2f}m², valid_pixels={valid_pixels_count})')
            
            return min(100.0, max(0.0, coverage_pct))
            
        except Exception as e:
            self.logger.error(f'Error calculating geometric coverage: {e}')
            import traceback
            self.logger.error(traceback.format_exc())
            return 0.0
    
    def extract_pixels_for_custom(self, raster_path, polygon):
        """
        Extract raw pixel values for custom algorithms.
        Public wrapper that doesn't require dataset to be pre-opened.
        
        Args:
            raster_path (str): Path to raster file
            polygon: QgsFeature polygon
            
        Returns:
            np.ndarray: Pixel values or None
        """
        try:
            # Open raster
            raster_ds = gdal.Open(raster_path)
            if raster_ds is None:
                self.logger.error(f'Cannot open raster: {raster_path}')
                return None
            
            # Extract pixels using existing method
            pixel_values = self._extract_pixels_from_dataset(
                raster_ds,
                polygon,
                raster_ds.GetRasterBand(1).GetNoDataValue()
            )
            
            # Close
            raster_ds = None
            
            return pixel_values
            
        except Exception as e:
            self.logger.error(f'Error in extract_pixels_for_custom: {str(e)}')
            return None

    def _calculate_statistic(self, stat_name, pixel_values):
        """
        Calculate a single statistic.
        
        Args:
            stat_name (str): Name of statistic
            pixel_values (np.array): Array of pixel values
            
        Returns:
            float: Calculated value
        """
        if len(pixel_values) == 0:
            self.logger.warning(f'No pixel values for statistic: {stat_name}')
            return None
        
        try:
            if stat_name == 'mean':
                val = float(np.mean(pixel_values))
                return None if not np.isfinite(val) else round(val, 6)

            elif stat_name == 'sum':
                val = float(np.sum(pixel_values))
                return None if not np.isfinite(val) else round(val, 6)

            elif stat_name == 'min':
                val = float(np.min(pixel_values))
                return None if not np.isfinite(val) else round(val, 6)

            elif stat_name == 'max':
                val = float(np.max(pixel_values))
                return None if not np.isfinite(val) else round(val, 6)

            elif stat_name == 'median':
                val = float(np.median(pixel_values))
                return None if not np.isfinite(val) else round(val, 6)

            elif stat_name == 'mode':
                # Mode is most frequent value
                values, counts = np.unique(pixel_values, return_counts=True)
                val = float(values[np.argmax(counts)])
                return None if not np.isfinite(val) else round(val, 6)
            
            elif stat_name == 'minority':
                try:
                    # Find least frequently occurring value
                    unique, counts = np.unique(pixel_values, return_counts=True)
                    
                    self.logger.debug(f'Minority: found {len(unique)} unique values')
                    
                    if len(unique) == 0:
                        self.logger.debug('Minority: no unique values')
                        return None
                    elif len(unique) == 1:
                        self.logger.debug(f'Minority: only 1 unique value = {unique[0]}')
                        return float(unique[0])
                    else:
                        min_idx = np.argmin(counts)
                        minority_value = float(unique[min_idx])
                        self.logger.debug(f'Minority: value={minority_value}, count={counts[min_idx]}')
                        return minority_value
                except Exception as e:
                    self.logger.error(f'Error calculating minority: {e}')
                    import traceback
                    self.logger.error(traceback.format_exc())
                    return None

            elif stat_name == 'variety':
                # Count unique values
                return len(np.unique(pixel_values))

            elif stat_name == 'count':
                return int(len(pixel_values))

            elif stat_name == 'range':
                val = float(np.max(pixel_values) - np.min(pixel_values))
                return None if not np.isfinite(val) else round(val, 6)

            elif stat_name == 'stddev':
                val = float(np.std(pixel_values))
                return None if not np.isfinite(val) else round(val, 6)

            elif stat_name == 'variance':
                val = float(np.var(pixel_values))
                return None if not np.isfinite(val) else round(val, 6)

            elif stat_name == 'cv':
                # Coefficient of variation
                mean = np.mean(pixel_values)
                if mean == 0 or not np.isfinite(mean):
                    return None
                val = float(np.std(pixel_values) / mean * 100)
                return None if not np.isfinite(val) else round(val, 6)

            elif stat_name.startswith('p'):
                # Percentile (p10, p25, etc.)
                percentile = int(stat_name[1:])
                val = float(np.percentile(pixel_values, percentile))
                return None if not np.isfinite(val) else round(val, 6)
            
            else:
                self.logger.warning(f'Unknown statistic: {stat_name}')
                return None
                
        except Exception as e:
            self.logger.error(f'Error calculating {stat_name}: {str(e)}')
            return None