"""
Post-Processing Engine for Zonify

Provides advanced operations for transforming zonal statistics results:
- Normalization (min-max, z-score)
- Classification (equal intervals, quantiles, Jenks, custom)
- Ranking and percentile ranking
- Flagging based on conditions or percentiles
- Combining multiple fields with weights

These are building blocks for task-based UI operations.

Author: Dragos Gontariu
License: GPL-3.0
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from qgis.core import QgsVectorLayer, QgsFeature, QgsField
from qgis.PyQt.QtCore import QVariant


class PostProcessingEngine:
    """
    Engine for post-processing zonal statistics results.
    Provides operations for normalization, classification, ranking, etc.
    """
    
    def __init__(self):
        """Initialize engine."""
        self.operations = []  # List of configured operations
    
    # ========== NORMALIZATION ==========
    
    @staticmethod
    def normalize_minmax(values: np.ndarray, output_range: Tuple[float, float] = (0, 100)) -> np.ndarray:
        """
        Min-Max normalization.
        
        Formula: (value - min) / (max - min) * (out_max - out_min) + out_min
        
        Args:
            values: Input values
            output_range: Tuple (min, max) for output range
            
        Returns:
            Normalized values
        """
        values = np.array(values, dtype=float)
        
        # Handle edge cases
        if len(values) == 0:
            return values
        
        v_min = np.nanmin(values)
        v_max = np.nanmax(values)
        
        # If all values are the same
        if v_max == v_min:
            return np.full_like(values, output_range[0])
        
        # Normalize
        normalized = (values - v_min) / (v_max - v_min)
        
        # Scale to output range
        out_min, out_max = output_range
        scaled = normalized * (out_max - out_min) + out_min
        
        return scaled
    
    @staticmethod
    def normalize_zscore(values: np.ndarray) -> np.ndarray:
        """
        Z-score standardization.
        
        Formula: (value - mean) / std_dev
        
        Args:
            values: Input values
            
        Returns:
            Standardized values (mean=0, std=1)
        """
        values = np.array(values, dtype=float)
        
        if len(values) == 0:
            return values
        
        mean = np.nanmean(values)
        std = np.nanstd(values)
        
        # Handle zero std
        if std == 0:
            return np.zeros_like(values)
        
        return (values - mean) / std
    
    # ========== CLASSIFICATION ==========
    
    @staticmethod
    def classify_equal_intervals(values: np.ndarray, n_classes: int = 3, 
                                 labels: Optional[List[str]] = None) -> Tuple[np.ndarray, List[float]]:
        """
        Classify using equal intervals.
        
        Args:
            values: Input values
            n_classes: Number of classes
            labels: Optional class labels (default: "Class 1", "Class 2", ...)
            
        Returns:
            Tuple of (class labels array, break points list)
        """
        values = np.array(values, dtype=float)
        
        if len(values) == 0:
            return values, []
        
        # Calculate breaks
        v_min = np.nanmin(values)
        v_max = np.nanmax(values)
        
        breaks = np.linspace(v_min, v_max, n_classes + 1)
        
        # Classify
        classes = np.digitize(values, breaks[1:-1])
        
        # Apply labels
        if labels is None:
            labels = [f"Class {i+1}" for i in range(n_classes)]
        
        class_labels = np.array([labels[min(c, n_classes-1)] for c in classes])
        
        return class_labels, breaks.tolist()
    
    @staticmethod
    def classify_quantiles(values: np.ndarray, n_classes: int = 3,
                          labels: Optional[List[str]] = None) -> Tuple[np.ndarray, List[float]]:
        """
        Classify using quantiles (equal count per class).
        
        Args:
            values: Input values
            n_classes: Number of classes
            labels: Optional class labels
            
        Returns:
            Tuple of (class labels array, break points list)
        """
        values = np.array(values, dtype=float)
        
        if len(values) == 0:
            return values, []
        
        # Calculate quantile breaks
        percentiles = np.linspace(0, 100, n_classes + 1)
        breaks = np.nanpercentile(values, percentiles)
        
        # Classify
        classes = np.digitize(values, breaks[1:-1])
        
        # Apply labels
        if labels is None:
            labels = [f"Class {i+1}" for i in range(n_classes)]
        
        class_labels = np.array([labels[min(c, n_classes-1)] for c in classes])
        
        return class_labels, breaks.tolist()
    
    @staticmethod
    def classify_jenks(values: np.ndarray, n_classes: int = 3,
                      labels: Optional[List[str]] = None) -> Tuple[np.ndarray, List[float]]:
        """
        Classify using Jenks Natural Breaks.
        
        Note: Simplified implementation. For production, consider using jenkspy library.
        
        Args:
            values: Input values
            n_classes: Number of classes
            labels: Optional class labels
            
        Returns:
            Tuple of (class labels array, break points list)
        """
        # For now, fallback to quantiles
        # TODO: Implement true Jenks or add jenkspy dependency
        return PostProcessingEngine.classify_quantiles(values, n_classes, labels)
    
    @staticmethod
    def classify_custom(values: np.ndarray, breaks: List[float],
                       labels: List[str]) -> np.ndarray:
        """
        Classify using custom break points.
        
        Args:
            values: Input values
            breaks: Break points (must have len = n_classes - 1)
            labels: Class labels (must have len = n_classes)
            
        Returns:
            Class labels array
        """
        values = np.array(values, dtype=float)
        
        if len(values) == 0:
            return values
        
        # Classify
        classes = np.digitize(values, breaks)
        
        # Apply labels
        class_labels = np.array([labels[min(c, len(labels)-1)] for c in classes])
        
        return class_labels
    
    # ========== RANKING ==========
    
    @staticmethod
    def rank_values(values: np.ndarray, ascending: bool = False) -> np.ndarray:
        """
        Rank values (1 = best, N = worst by default).
        
        Args:
            values: Input values
            ascending: If False (default), higher values get better rank (1)
                      If True, lower values get better rank (1)
            
        Returns:
            Rank values (1 to N)
        """
        values = np.array(values, dtype=float)
        
        if len(values) == 0:
            return values
        
        # Get sorting order
        if ascending:
            order = np.argsort(values)
        else:
            order = np.argsort(-values)  # Descending
        
        # Assign ranks
        ranks = np.empty_like(order)
        ranks[order] = np.arange(1, len(values) + 1)
        
        return ranks
    
    @staticmethod
    def percentile_rank(values: np.ndarray) -> np.ndarray:
        """
        Calculate percentile rank (0-100).
        
        Percentile rank = percentage of values below this value.
        
        Args:
            values: Input values
            
        Returns:
            Percentile ranks (0-100)
        """
        values = np.array(values, dtype=float)
        
        if len(values) == 0:
            return values
        
        # Calculate percentile rank for each value
        percentiles = np.zeros_like(values)
        
        for i, val in enumerate(values):
            # Count how many values are below this one
            count_below = np.sum(values < val)
            percentiles[i] = (count_below / len(values)) * 100
        
        return percentiles
    
    # ========== FLAGGING ==========
    
    @staticmethod
    def flag_condition(values: np.ndarray, condition: str, threshold: float) -> np.ndarray:
        """
        Flag values based on a condition.
        
        Args:
            values: Input values
            condition: Condition string: '>', '<', '>=', '<=', '==', '!='
            threshold: Threshold value
            
        Returns:
            Boolean array (1 = True, 0 = False)
        """
        values = np.array(values, dtype=float)
        
        if len(values) == 0:
            return values
        
        # Apply condition
        if condition == '>':
            flags = values > threshold
        elif condition == '<':
            flags = values < threshold
        elif condition == '>=':
            flags = values >= threshold
        elif condition == '<=':
            flags = values <= threshold
        elif condition == '==':
            flags = np.isclose(values, threshold)
        elif condition == '!=':
            flags = ~np.isclose(values, threshold)
        else:
            raise ValueError(f"Unknown condition: {condition}")
        
        return flags.astype(int)
    
    @staticmethod
    def flag_percentile(values: np.ndarray, top_percent: Optional[float] = None,
                       bottom_percent: Optional[float] = None) -> Dict[str, np.ndarray]:
        """
        Flag top and/or bottom percentiles.
        
        Args:
            values: Input values
            top_percent: Percentage for top flag (e.g., 10 for top 10%)
            bottom_percent: Percentage for bottom flag (e.g., 10 for bottom 10%)
            
        Returns:
            Dict with 'top' and/or 'bottom' flag arrays
        """
        values = np.array(values, dtype=float)
        
        if len(values) == 0:
            return {}
        
        result = {}
        
        # Top percentile
        if top_percent is not None:
            threshold = np.nanpercentile(values, 100 - top_percent)
            result['top'] = (values >= threshold).astype(int)
        
        # Bottom percentile
        if bottom_percent is not None:
            threshold = np.nanpercentile(values, bottom_percent)
            result['bottom'] = (values <= threshold).astype(int)
        
        return result
    
    # ========== COMBINING ==========
    
    @staticmethod
    def weighted_sum(fields_dict: Dict[str, np.ndarray], 
                    weights_dict: Dict[str, float]) -> np.ndarray:
        """
        Calculate weighted sum of multiple fields.
        
        Args:
            fields_dict: Dict of {field_name: values_array}
            weights_dict: Dict of {field_name: weight}
            
        Returns:
            Weighted sum array
        """
        if not fields_dict:
            return np.array([])
        
        # Initialize result
        first_key = list(fields_dict.keys())[0]
        result = np.zeros_like(fields_dict[first_key], dtype=float)
        
        # Sum weighted values
        for field_name, values in fields_dict.items():
            weight = weights_dict.get(field_name, 1.0)
            result += np.array(values, dtype=float) * weight
        
        return result
    
    @staticmethod
    def weighted_average(fields_dict: Dict[str, np.ndarray],
                        weights_dict: Dict[str, float]) -> np.ndarray:
        """
        Calculate weighted average of multiple fields.
        
        Args:
            fields_dict: Dict of {field_name: values_array}
            weights_dict: Dict of {field_name: weight}
            
        Returns:
            Weighted average array
        """
        weighted_sum = PostProcessingEngine.weighted_sum(fields_dict, weights_dict)
        
        # Sum of weights
        total_weight = sum(weights_dict.get(k, 1.0) for k in fields_dict.keys())
        
        if total_weight == 0:
            return weighted_sum
        
        return weighted_sum / total_weight


class PostProcessingOperation:
    """
    Represents a single post-processing operation to be applied.
    """
    
    def __init__(self, operation_type: str, config: Dict[str, Any]):
        """
        Initialize operation.
        
        Args:
            operation_type: Type of operation ('normalize', 'classify', 'rank', 'flag', 'combine')
            config: Configuration dict specific to operation type
        """
        self.operation_type = operation_type
        self.config = config
        self.name = config.get('name', 'Unnamed Operation')
    
    def execute(self, layer: QgsVectorLayer, feature: QgsFeature) -> Dict[str, Any]:
        """
        Execute operation on a feature.
        
        Args:
            layer: Vector layer
            feature: Feature to process
            
        Returns:
            Dict of {output_field_name: value}
        """
        # This will be implemented based on operation type
        # For now, placeholder
        return {}
    
    def get_output_fields(self) -> List[Tuple[str, QVariant]]:
        """
        Get list of output fields this operation will create.
        
        Returns:
            List of (field_name, field_type) tuples
        """
        return []


class PostProcessingManager:
    """
    Manages all post-processing operations.
    """
    
    def __init__(self):
        """Initialize manager."""
        self.operations = []
        self.engine = PostProcessingEngine()
    
    def add_operation(self, operation: PostProcessingOperation):
        """Add an operation."""
        self.operations.append(operation)
    
    def remove_operation(self, index: int):
        """Remove operation by index."""
        if 0 <= index < len(self.operations):
            del self.operations[index]
    
    def clear_operations(self):
        """Clear all operations."""
        self.operations.clear()
    
    def get_operations(self) -> List[PostProcessingOperation]:
        """Get list of all operations."""
        return self.operations.copy()
    
    def execute_all(self, layer: QgsVectorLayer) -> bool:
        """
        Execute all operations on entire layer.
        
        Args:
            layer: Vector layer to process
            
        Returns:
            Success status
        """
        try:
            # Add output fields
            for operation in self.operations:
                output_fields = operation.get_output_fields()
                for field_name, field_type in output_fields:
                    if layer.fields().indexOf(field_name) == -1:
                        layer.addAttribute(QgsField(field_name, field_type))
            
            layer.updateFields()
            
            # Process each feature
            for feature in layer.getFeatures():
                for operation in self.operations:
                    results = operation.execute(layer, feature)
                    
                    # Update feature
                    for field_name, value in results.items():
                        field_idx = layer.fields().indexOf(field_name)
                        if field_idx >= 0:
                            layer.changeAttributeValue(feature.id(), field_idx, value)
            
            return True
            
        except Exception as e:
            print(f"Error executing post-processing operations: {e}")
            return False
