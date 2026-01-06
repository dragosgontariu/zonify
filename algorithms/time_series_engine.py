"""
Time Series Engine for Zonify

Analyzes temporal patterns across multiple rasters.
Supports various analysis types: change detection, trend analysis, seasonal patterns, etc.

Features:
- Change detection (first vs last, custom periods)
- Trend analysis (linear regression, Sen's slope)
- Temporal statistics (mean, min, max, std, cv over time)
- Seasonal analysis (monthly, quarterly, seasonal patterns)
- Extreme events (max/min values with dates)

Author: Dragos Gontariu
License: GPL-3.0
"""

import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from scipy import stats


class TimeSeriesAnalyzer:
    """
    Analyzes time series patterns in raster data.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize analyzer with configuration.
        
        Args:
            config (dict): Configuration from UI
                {
                    'name': 'Temperature Trend 2020-2024',
                    'rasters': [{'date': '2020-01-01', 'path': 'temp_jan2020.tif'}, ...],
                    'analyses': {
                        'change_detection': {'enabled': True, 'compare': 'First vs Last'},
                        'trend_analysis': {'enabled': True, 'method': 'linear_regression'},
                        'temporal_statistics': {'enabled': True, 'stats': ['mean', 'min', 'max']},
                        'seasonal_analysis': {'enabled': True, 'group_by': 'month'},
                        'extreme_events': {'enabled': True}
                    },
                    'output_prefix': 'ts_temp_'
                }
        """
        self.config = config
        self.name = config['name']
        self.rasters = sorted(config['rasters'], key=lambda x: x['date'])
        self.analyses = config['analyses']
        self.prefix = config['output_prefix']
        
        # Parse dates
        self.dates = [datetime.fromisoformat(r['date']) for r in self.rasters]
        
        # Validate
        if len(self.rasters) == 0:
            raise ValueError("No rasters provided for time series analysis")
    
    def analyze(self, polygon, zonal_calculator) -> Dict[str, Any]:
        """
        Perform all enabled analyses for a polygon.
        
        Args:
            polygon: QgsFeature polygon
            zonal_calculator: ZonalCalculator instance to extract raster values
        
        Returns:
            dict: All analysis results
        """
        # Extract temporal data (mean values from all rasters)
        temporal_data = self._extract_temporal_data(polygon, zonal_calculator)
        
        if len(temporal_data) == 0:
            return self._get_empty_results()
        
        results = {}
        
        # Run each enabled analysis
        if self.analyses.get('change_detection', {}).get('enabled', False):
            results.update(self._change_detection(temporal_data))
        
        if self.analyses.get('trend_analysis', {}).get('enabled', False):
            results.update(self._trend_analysis(temporal_data))
        
        if self.analyses.get('temporal_statistics', {}).get('enabled', False):
            results.update(self._temporal_statistics(temporal_data))
        
        if self.analyses.get('seasonal_analysis', {}).get('enabled', False):
            results.update(self._seasonal_analysis(temporal_data))
        
        if self.analyses.get('extreme_events', {}).get('enabled', False):
            results.update(self._extreme_events(temporal_data))
        
        return results
    
    def _extract_temporal_data(self, polygon, zonal_calculator) -> List[Dict]:
        """
        Extract mean values from all rasters for this polygon.
        
        Returns:
            list: [{'date': datetime, 'mean': float, 'index': int}, ...]
        """
        data = []
        
        for i, raster_info in enumerate(self.rasters):
            try:
                # Extract pixels for this raster
                pixels = zonal_calculator._extract_pixels(raster_info['path'], polygon)
                
                if pixels is None or len(pixels) == 0:
                    continue
                
                # Calculate mean
                mean_value = np.mean(pixels)
                
                data.append({
                    'date': self.dates[i],
                    'mean': float(mean_value),
                    'index': i,
                    'date_str': raster_info['date']
                })
            
            except Exception as e:
                print(f"Warning: Failed to extract data from {raster_info['path']}: {str(e)}")
                continue
        
        return data
    
    def _change_detection(self, temporal_data: List[Dict]) -> Dict[str, Any]:
        """Compare first vs last period."""
        compare_mode = self.analyses['change_detection'].get('compare', 'First vs Last')
        
        if compare_mode == 'First vs Last':
            first = temporal_data[0]
            last = temporal_data[-1]
        else:
            # Default to first vs last for now
            first = temporal_data[0]
            last = temporal_data[-1]
        
        change = last['mean'] - first['mean']
        
        # Percent change (handle division by zero)
        if abs(first['mean']) > 1e-10:
            percent_change = (change / first['mean']) * 100
        else:
            percent_change = None
        
        return {
            f'{self.prefix}mean_change': change,
            f'{self.prefix}percent_change': percent_change,
            f'{self.prefix}first_value': first['mean'],
            f'{self.prefix}last_value': last['mean'],
            f'{self.prefix}first_date': first['date_str'],
            f'{self.prefix}last_date': last['date_str']
        }
    
    def _trend_analysis(self, temporal_data: List[Dict]) -> Dict[str, Any]:
        """Calculate linear trend."""
        method = self.analyses['trend_analysis'].get('method', 'linear_regression')
        
        # Prepare data
        x = np.array([d['index'] for d in temporal_data])
        y = np.array([d['mean'] for d in temporal_data])
        
        if method == 'linear_regression':
            # Linear regression
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                
                return {
                    f'{self.prefix}trend_slope': float(slope),
                    f'{self.prefix}trend_intercept': float(intercept),
                    f'{self.prefix}trend_r2': float(r_value ** 2),
                    f'{self.prefix}trend_pvalue': float(p_value),
                    f'{self.prefix}trend_stderr': float(std_err)
                }
            except Exception as e:
                print(f"Trend analysis failed: {str(e)}")
                return {
                    f'{self.prefix}trend_slope': None,
                    f'{self.prefix}trend_r2': None,
                    f'{self.prefix}trend_pvalue': None
                }
        
        elif method == 'sens_slope':
            # Sen's slope (non-parametric)
            try:
                from scipy.stats import theilslopes
                slope, intercept, lo_slope, up_slope = theilslopes(y, x)
                
                return {
                    f'{self.prefix}sens_slope': float(slope),
                    f'{self.prefix}sens_intercept': float(intercept),
                    f'{self.prefix}sens_slope_lo': float(lo_slope),
                    f'{self.prefix}sens_slope_up': float(up_slope)
                }
            except Exception as e:
                print(f"Sen's slope failed: {str(e)}")
                return {
                    f'{self.prefix}sens_slope': None
                }
        
        return {}
    
    def _temporal_statistics(self, temporal_data: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics over time."""
        stats_config = self.analyses['temporal_statistics'].get('stats', ['mean'])
        
        means = np.array([d['mean'] for d in temporal_data])
        
        results = {}
        
        if 'mean' in stats_config:
            results[f'{self.prefix}temporal_mean'] = float(np.mean(means))
        
        if 'min' in stats_config:
            results[f'{self.prefix}temporal_min'] = float(np.min(means))
        
        if 'max' in stats_config:
            results[f'{self.prefix}temporal_max'] = float(np.max(means))
        
        if 'std' in stats_config:
            results[f'{self.prefix}temporal_std'] = float(np.std(means))
        
        if 'cv' in stats_config:
            mean_val = np.mean(means)
            if abs(mean_val) > 1e-10:
                cv = (np.std(means) / mean_val) * 100
                results[f'{self.prefix}temporal_cv'] = float(cv)
            else:
                results[f'{self.prefix}temporal_cv'] = None
        
        return results
    
    def _seasonal_analysis(self, temporal_data: List[Dict]) -> Dict[str, Any]:
        """Group by season and calculate means."""
        group_by = self.analyses['seasonal_analysis'].get('group_by', 'month')
        
        if group_by == 'month':
            # Group by month (1-12)
            monthly_groups = {m: [] for m in range(1, 13)}
            
            for data in temporal_data:
                month = data['date'].month
                monthly_groups[month].append(data['mean'])
            
            results = {}
            month_names = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
            
            for month, values in monthly_groups.items():
                if values:
                    month_name = month_names[month - 1]
                    results[f'{self.prefix}month_{month_name}_mean'] = float(np.mean(values))
                    results[f'{self.prefix}month_{month_name}_count'] = len(values)
            
            return results
        
        elif group_by == 'quarter':
            # Group by quarter (Q1-Q4)
            quarterly_groups = {1: [], 2: [], 3: [], 4: []}
            
            for data in temporal_data:
                quarter = (data['date'].month - 1) // 3 + 1
                quarterly_groups[quarter].append(data['mean'])
            
            results = {}
            for quarter, values in quarterly_groups.items():
                if values:
                    results[f'{self.prefix}quarter_q{quarter}_mean'] = float(np.mean(values))
                    results[f'{self.prefix}quarter_q{quarter}_count'] = len(values)
            
            return results
        
        elif group_by == 'season':
            # Group by season (Winter, Spring, Summer, Fall)
            seasonal_groups = {
                'winter': [],
                'spring': [],
                'summer': [],
                'fall': []
            }
            
            for data in temporal_data:
                month = data['date'].month
                
                if month in [12, 1, 2]:
                    seasonal_groups['winter'].append(data['mean'])
                elif month in [3, 4, 5]:
                    seasonal_groups['spring'].append(data['mean'])
                elif month in [6, 7, 8]:
                    seasonal_groups['summer'].append(data['mean'])
                else:
                    seasonal_groups['fall'].append(data['mean'])
            
            results = {}
            for season, values in seasonal_groups.items():
                if values:
                    results[f'{self.prefix}seasonal_{season}_mean'] = float(np.mean(values))
                    results[f'{self.prefix}seasonal_{season}_count'] = len(values)
            
            return results
        
        return {}
    
    def _extreme_events(self, temporal_data: List[Dict]) -> Dict[str, Any]:
        """Find extreme values and their dates."""
        means = [d['mean'] for d in temporal_data]
        
        max_idx = np.argmax(means)
        min_idx = np.argmin(means)
        
        return {
            f'{self.prefix}max_value': temporal_data[max_idx]['mean'],
            f'{self.prefix}max_date': temporal_data[max_idx]['date_str'],
            f'{self.prefix}min_value': temporal_data[min_idx]['mean'],
            f'{self.prefix}min_date': temporal_data[min_idx]['date_str']
        }
    
    def _get_empty_results(self) -> Dict[str, Any]:
        """Return empty results when no data available."""
        results = {}
        
        # Add None for all possible fields
        if self.analyses.get('change_detection', {}).get('enabled', False):
            results.update({
                f'{self.prefix}mean_change': None,
                f'{self.prefix}percent_change': None,
                f'{self.prefix}first_value': None,
                f'{self.prefix}last_value': None
            })
        
        if self.analyses.get('trend_analysis', {}).get('enabled', False):
            results.update({
                f'{self.prefix}trend_slope': None,
                f'{self.prefix}trend_r2': None,
                f'{self.prefix}trend_pvalue': None
            })
        
        if self.analyses.get('temporal_statistics', {}).get('enabled', False):
            stats_config = self.analyses['temporal_statistics'].get('stats', ['mean'])
            for stat in stats_config:
                results[f'{self.prefix}temporal_{stat}'] = None
        
        return results
    
    def get_output_field_names(self) -> List[str]:
        """Get list of all possible output field names."""
        fields = []
        
        if self.analyses.get('change_detection', {}).get('enabled', False):
            fields.extend([
                f'{self.prefix}mean_change',
                f'{self.prefix}percent_change',
                f'{self.prefix}first_value',
                f'{self.prefix}last_value',
                f'{self.prefix}first_date',
                f'{self.prefix}last_date'
            ])
        
        if self.analyses.get('trend_analysis', {}).get('enabled', False):
            method = self.analyses['trend_analysis'].get('method', 'linear_regression')
            if method == 'linear_regression':
                fields.extend([
                    f'{self.prefix}trend_slope',
                    f'{self.prefix}trend_intercept',
                    f'{self.prefix}trend_r2',
                    f'{self.prefix}trend_pvalue',
                    f'{self.prefix}trend_stderr'
                ])
            else:
                fields.extend([
                    f'{self.prefix}sens_slope',
                    f'{self.prefix}sens_intercept'
                ])
        
        if self.analyses.get('temporal_statistics', {}).get('enabled', False):
            stats_config = self.analyses['temporal_statistics'].get('stats', ['mean'])
            for stat in stats_config:
                fields.append(f'{self.prefix}temporal_{stat}')
        
        if self.analyses.get('seasonal_analysis', {}).get('enabled', False):
            group_by = self.analyses['seasonal_analysis'].get('group_by', 'month')
            
            if group_by == 'month':
                month_names = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
                for month_name in month_names:
                    fields.extend([
                        f'{self.prefix}month_{month_name}_mean',
                        f'{self.prefix}month_{month_name}_count'
                    ])
            elif group_by == 'quarter':
                for q in range(1, 5):
                    fields.extend([
                        f'{self.prefix}quarter_q{q}_mean',
                        f'{self.prefix}quarter_q{q}_count'
                    ])
            elif group_by == 'season':
                for season in ['winter', 'spring', 'summer', 'fall']:
                    fields.extend([
                        f'{self.prefix}seasonal_{season}_mean',
                        f'{self.prefix}seasonal_{season}_count'
                    ])
        
        if self.analyses.get('extreme_events', {}).get('enabled', False):
            fields.extend([
                f'{self.prefix}max_value',
                f'{self.prefix}max_date',
                f'{self.prefix}min_value',
                f'{self.prefix}min_date'
            ])
        
        return fields
    
    def get_required_rasters(self) -> List[str]:
        """Get list of raster paths."""
        return [r['path'] for r in self.rasters]
