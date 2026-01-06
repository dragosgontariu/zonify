"""
Custom Algorithm Engine for Zonify

Evaluates user-defined formulas for zonal statistics.
Supports both aggregated (using statistics) and pixel-by-pixel operations.

Features:
- Safe formula evaluation (restricted namespace)
- Aggregated mode: (A_mean * 2) / (B_sum + 1)
- Pixel-by-pixel mode: (A - B) / (A + B)
- Validation and error handling

Author: Dragos Gontariu
License: GPL-3.0
"""

import numpy as np
import ast
import re
from typing import Dict, List, Any, Optional


class CustomAlgorithmEngine:
    """
    Engine for evaluating custom user-defined algorithms.
    """
    
    def __init__(self, algorithm_config: Dict):
        """
        Initialize engine with algorithm configuration.
        
        Args:
            algorithm_config (dict): Algorithm configuration from UI
                {
                    'name': str,
                    'description': str,
                    'inputs': [{'variable': 'A', 'raster': 'temp', 'statistics': ['mean', 'max']}, ...],
                    'mode': 'aggregated' or 'pixel_by_pixel',
                    'formula': str,
                    'output_statistics': ['mean', 'max', ...] (for pixel mode only)
                }
        """
        self.config = algorithm_config
        self.name = algorithm_config['name']
        self.mode = algorithm_config['mode']
        self.formula = algorithm_config['formula']
        self.inputs = algorithm_config['inputs']
        self.output_statistics = algorithm_config.get('output_statistics', ['mean'])
        
        # Validate formula syntax
        self._validate_formula()
    
    def _validate_formula(self):
        """Validate formula syntax and variables."""
        try:
            # Parse formula as Python expression
            ast.parse(self.formula, mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Invalid formula syntax in '{self.name}': {str(e)}")
        
        # Extract variables used in formula
        if self.mode == 'aggregated':
            # Variables like A_mean, B_sum, etc.
            vars_in_formula = set(re.findall(r'[A-Z]_\w+', self.formula))
            
            # Check each variable is defined
            for var in vars_in_formula:
                var_letter = var.split('_')[0]
                var_stat = var.split('_', 1)[1]
                
                # Check if variable letter is defined in inputs
                if not any(inp['variable'] == var_letter for inp in self.inputs):
                    raise ValueError(
                        f"Variable '{var_letter}' used in formula but not defined in inputs"
                    )
                
                # Check if statistic is available for this variable
                input_def = next(inp for inp in self.inputs if inp['variable'] == var_letter)
                if var_stat not in input_def['statistics']:
                    raise ValueError(
                        f"Statistic '{var_stat}' for variable '{var_letter}' not enabled in inputs"
                    )
        
        else:  # pixel_by_pixel
            # Variables like A, B, C (single letters)
            vars_in_formula = set(re.findall(r'\b[A-Z]\b', self.formula))
            
            # Check each variable is defined
            for var in vars_in_formula:
                if not any(inp['variable'] == var for inp in self.inputs):
                    raise ValueError(
                        f"Variable '{var}' used in formula but not defined in inputs"
                    )
    
    def calculate_aggregated(self, polygon_stats: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate using aggregated statistics.
        
        Args:
            polygon_stats (dict): Statistics for current polygon
                {
                    'temperature_mean': 25.5,
                    'temperature_max': 35.2,
                    'precipitation_sum': 450.0,
                    'precipitation_mean': 37.5,
                    ...
                }
        
        Returns:
            dict: Result as {algorithm_name: value}
        """
        # Build namespace with available variables
        namespace = {}
        
        for input_def in self.inputs:
            var = input_def['variable']
            raster = input_def['raster']
            print(f"DEBUG Custom Algorithm: var={var}, raster={raster}")
            
            # Map each statistic to variable name
            for stat in input_def['statistics']:
                # Field name in polygon_stats: "raster_statistic"
                field_name = f"{raster}_{stat}"
                
                # Variable name in formula: "A_mean", "B_sum", etc.
                var_name = f"{var}_{stat}"
                
                # Get value (default to 0 if missing)
                value = polygon_stats.get(field_name, 0)
                
                # ============ FIX: Convert QVariant to native Python type ============
                from qgis.PyQt.QtCore import QVariant
                if isinstance(value, QVariant):
                    if value.isNull():
                        value = 0  # Use 0 for NULL values
                    else:
                        value = value.value()
                
                # Convert to float (handle None and invalid values)
                try:
                    value = float(value) if value is not None else 0
                except (ValueError, TypeError):
                    value = 0  # Fallback for invalid values
                # =====================================================================
                
                print(f"  Looking for field: {field_name}, found value: {value} (type: {type(value).__name__})")
                namespace[var_name] = value
        
        # Safe evaluation with restricted namespace
        try:
            # Allow only basic math operations
            safe_dict = {
                '__builtins__': {},
                'abs': abs,
                'min': min,
                'max': max,
                'round': round,
                'pow': pow
            }
            safe_dict.update(namespace)
            
            result = eval(self.formula, safe_dict, {})
            
            # Handle invalid results
            if np.isnan(result) or np.isinf(result):
                result = None
            
            return {self.name: float(result) if result is not None else None}
            
        except ZeroDivisionError:
            return {self.name: None}
        except Exception as e:
            raise RuntimeError(f"Error evaluating formula '{self.name}': {str(e)}")
    
    def calculate_pixel_by_pixel(self, pixel_arrays: Dict[str, np.ndarray]) -> Dict[str, float]:
        """
        Calculate using pixel-by-pixel operations.
        
        Args:
            pixel_arrays (dict): Pixel arrays for current polygon
                {
                    'temperature': np.array([23, 24, 25, ...]),
                    'precipitation': np.array([10, 15, 12, ...]),
                    ...
                }
        
        Returns:
            dict: Statistics of result array
                {
                    'algorithm_name_mean': 0.456,
                    'algorithm_name_max': 0.892,
                    ...
                }
        """
        # Build namespace with arrays
        namespace = {}
        
        for input_def in self.inputs:
            var = input_def['variable']
            raster = input_def['raster']
            
            # Get array for this variable
            if raster not in pixel_arrays:
                raise ValueError(f"Raster '{raster}' not found in pixel arrays")
            
            namespace[var] = pixel_arrays[raster]
        
        # Add numpy functions
        safe_dict = {
            '__builtins__': {},
            'mean': np.mean,
            'sum': np.sum,
            'min': np.min,
            'max': np.max,
            'median': np.median,
            'std': np.std,
            'sqrt': np.sqrt,
            'abs': np.abs,
            'log': np.log,
            'log10': np.log10,
            'exp': np.exp,
            'power': np.power,
            'square': np.square
        }
        safe_dict.update(namespace)
        
        try:
            # Evaluate formula to get result array
            result_array = eval(self.formula, safe_dict, {})
            
            # Ensure it's a numpy array
            if not isinstance(result_array, np.ndarray):
                result_array = np.array(result_array)
            
            # Filter out NaN and Inf
            valid_mask = np.isfinite(result_array)
            valid_values = result_array[valid_mask]
            
            if len(valid_values) == 0:
                # No valid values
                return {f'{self.name}_{stat}': None for stat in self.output_statistics}
            
            # Calculate output statistics
            results = {}
            
            for stat in self.output_statistics:
                field_name = f'{self.name}_{stat}'
                
                if stat == 'mean':
                    results[field_name] = float(np.mean(valid_values))
                elif stat == 'median':
                    results[field_name] = float(np.median(valid_values))
                elif stat == 'min':
                    results[field_name] = float(np.min(valid_values))
                elif stat == 'max':
                    results[field_name] = float(np.max(valid_values))
                elif stat == 'stddev' or stat == 'std':
                    results[field_name] = float(np.std(valid_values))
                elif stat == 'sum':
                    results[field_name] = float(np.sum(valid_values))
                elif stat == 'count':
                    results[field_name] = int(len(valid_values))
                else:
                    results[field_name] = None
            
            return results
            
        except Exception as e:
            raise RuntimeError(f"Error evaluating pixel formula '{self.name}': {str(e)}")
    
    def get_required_rasters(self) -> List[str]:
        """
        Get list of raster names required by this algorithm.
        
        Returns:
            list: List of raster names
        """
        return [inp['raster'] for inp in self.inputs]
    
    def get_required_statistics(self) -> Dict[str, List[str]]:
        """
        Get required statistics per raster (for aggregated mode).
        
        Returns:
            dict: {raster_name: [statistics]}
        """
        if self.mode != 'aggregated':
            return {}
        
        result = {}
        for inp in self.inputs:
            result[inp['raster']] = inp['statistics']
        
        return result
    
    def get_output_field_names(self) -> List[str]:
        """
        Get list of output field names this algorithm produces.
        
        Returns:
            list: Field names
        """
        if self.mode == 'aggregated':
            return [self.name]
        else:
            return [f'{self.name}_{stat}' for stat in self.output_statistics]


class CustomAlgorithmManager:
    """
    Manages multiple custom algorithms.
    """
    
    def __init__(self, algorithms_config: List[Dict]):
        """
        Initialize manager with list of algorithm configs.
        
        Args:
            algorithms_config (list): List of algorithm configurations
        """
        self.engines = []
        
        for config in algorithms_config:
            try:
                engine = CustomAlgorithmEngine(config)
                self.engines.append(engine)
            except Exception as e:
                # Log warning but continue with other algorithms
                print(f"Warning: Failed to initialize algorithm '{config.get('name', 'Unknown')}': {str(e)}")
    
    def calculate_all_aggregated(self, polygon_stats: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate all algorithms in aggregated mode.
        
        Args:
            polygon_stats (dict): Polygon statistics
        
        Returns:
            dict: Combined results from all algorithms
        """
        results = {}
        
        for engine in self.engines:
            if engine.mode == 'aggregated':
                try:
                    algo_results = engine.calculate_aggregated(polygon_stats)
                    results.update(algo_results)
                except Exception as e:
                    print(f"Error calculating algorithm '{engine.name}': {str(e)}")
                    # Add None values for failed algorithms
                    for field_name in engine.get_output_field_names():
                        results[field_name] = None
        
        return results
    
    def calculate_all_pixel(self, pixel_arrays: Dict[str, np.ndarray]) -> Dict[str, float]:
        """
        Calculate all algorithms in pixel-by-pixel mode.
        
        Args:
            pixel_arrays (dict): Pixel arrays
        
        Returns:
            dict: Combined results from all algorithms
        """
        results = {}
        
        for engine in self.engines:
            if engine.mode == 'pixel_by_pixel':
                try:
                    algo_results = engine.calculate_pixel_by_pixel(pixel_arrays)
                    results.update(algo_results)
                except Exception as e:
                    print(f"Error calculating pixel algorithm '{engine.name}': {str(e)}")
                    # Add None values for failed algorithms
                    for field_name in engine.get_output_field_names():
                        results[field_name] = None
        
        return results
    
    def get_all_output_fields(self) -> List[str]:
        """Get all output field names from all algorithms."""
        fields = []
        for engine in self.engines:
            fields.extend(engine.get_output_field_names())
        return fields
    
    def has_pixel_algorithms(self) -> bool:
        """Check if any algorithm uses pixel-by-pixel mode."""
        return any(engine.mode == 'pixel_by_pixel' for engine in self.engines)
    
    def get_required_rasters_for_algorithms(self) -> Dict[str, List[str]]:
        """
        Get mapping of algorithm names to required rasters.
        
        Returns:
            dict: {algorithm_name: [raster_names]}
        """
        result = {}
        for engine in self.engines:
            result[engine.name] = engine.get_required_rasters()
        return result
