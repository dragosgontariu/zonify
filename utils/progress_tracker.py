"""
Progress Tracker for Zonify

Tracks and calculates processing progress, ETA, and performance metrics.

Author: Dragos Gontariu
License: GPL-3.0
"""

import time
from datetime import timedelta


class ProgressTracker:
    """
    Track processing progress and calculate statistics.
    """
    
    def __init__(self, total_rasters, total_polygons):
        """
        Constructor.
        
        Args:
            total_rasters (int): Total number of rasters
            total_polygons (int): Total number of polygons
        """
        self.total_rasters = total_rasters
        self.total_polygons = total_polygons
        
        self.current_raster = 0
        self.processed_polygons = 0
        
        self.start_time = time.time()
        self.raster_start_times = {}
        self.raster_durations = {}
        
        self.last_update_time = time.time()
        self.last_update_polygons = 0
    
    def start_raster(self, raster_index):
        """
        Mark start of raster processing.
        
        Args:
            raster_index (int): Raster index (0-based)
        """
        self.current_raster = raster_index
        self.raster_start_times[raster_index] = time.time()
    
    def finish_raster(self, raster_index):
        """
        Mark end of raster processing.
        
        Args:
            raster_index (int): Raster index (0-based)
        """
        if raster_index in self.raster_start_times:
            duration = time.time() - self.raster_start_times[raster_index]
            self.raster_durations[raster_index] = duration
    
    def update_polygons(self, processed_count):
        """
        Update processed polygon count.
        
        Args:
            processed_count (int): Number of polygons processed so far
        """
        self.processed_polygons = processed_count
    
    def get_overall_progress(self):
        """
        Get overall progress percentage.
        
        Returns:
            int: Progress percentage (0-100)
        """
        if self.total_rasters == 0:
            return 0
        
        # Weight by rasters completed
        raster_progress = (self.current_raster / self.total_rasters) * 100
        
        return int(min(100, raster_progress))
    
    def get_raster_progress(self):
        """
        Get current raster progress percentage.
        
        Returns:
            int: Progress percentage (0-100)
        """
        if self.total_polygons == 0:
            return 0
        
        polygons_this_raster = self.processed_polygons % self.total_polygons
        if polygons_this_raster == 0 and self.processed_polygons > 0:
            polygons_this_raster = self.total_polygons
        
        return int((polygons_this_raster / self.total_polygons) * 100)
    
    def get_elapsed_time(self):
        """
        Get elapsed time since start.
        
        Returns:
            timedelta: Elapsed time
        """
        elapsed_seconds = time.time() - self.start_time
        return timedelta(seconds=int(elapsed_seconds))
    
    def get_eta(self):
        """
        Estimate time remaining.
        
        Returns:
            timedelta: Estimated time remaining
        """
        if self.processed_polygons == 0:
            return None
        
        elapsed = time.time() - self.start_time
        
        # Calculate total work
        total_work = self.total_rasters * self.total_polygons
        completed_work = (self.current_raster * self.total_polygons) + (self.processed_polygons % self.total_polygons)
        
        if completed_work == 0:
            return None
        
        # Estimate remaining time
        rate = completed_work / elapsed
        remaining_work = total_work - completed_work
        
        eta_seconds = remaining_work / rate
        return timedelta(seconds=int(eta_seconds))
    
    def get_processing_speed(self):
        """
        Get current processing speed.
        
        Returns:
            float: Polygons processed per second
        """
        if self.processed_polygons == 0:
            return 0.0
        
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return 0.0
        
        return self.processed_polygons / elapsed
    
    def get_average_raster_time(self):
        """
        Get average time per raster.
        
        Returns:
            float: Average seconds per raster
        """
        if not self.raster_durations:
            return 0.0
        
        return sum(self.raster_durations.values()) / len(self.raster_durations)
    
    def get_summary(self):
        """
        Get progress summary.
        
        Returns:
            dict: Progress summary
        """
        return {
            'current_raster': self.current_raster + 1,
            'total_rasters': self.total_rasters,
            'processed_polygons': self.processed_polygons,
            'total_polygons': self.total_polygons,
            'overall_progress': self.get_overall_progress(),
            'raster_progress': self.get_raster_progress(),
            'elapsed_time': self.get_elapsed_time(),
            'eta': self.get_eta(),
            'speed': self.get_processing_speed(),
            'avg_raster_time': self.get_average_raster_time()
        }