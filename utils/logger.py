"""
Zonify Logger

Provides consistent logging throughout the plugin.

Features:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)
- Writes to QGIS message log
- Optional file logging
- Timestamp support

Author: Dragos Gontariu
License: GPL-3.0
"""

from qgis.core import QgsMessageLog, Qgis
from datetime import datetime
import os


class Logger:
    """
    Logger for Zonify plugin.
    """
    
    def __init__(self, name='Zonify', log_file=None):
        """
        Constructor.
        
        Args:
            name (str): Logger name (used as tag in QGIS log)
            log_file (str): Optional path to log file
        """
        self.name = name
        self.log_file = log_file
        
        # Create log file if specified
        if self.log_file:
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
    
    def debug(self, message):
        """Log debug message."""
        self._log(message, Qgis.Info, 'DEBUG')
    
    def info(self, message):
        """Log info message."""
        self._log(message, Qgis.Info, 'INFO')
    
    def warning(self, message):
        """Log warning message."""
        self._log(message, Qgis.Warning, 'WARNING')
    
    def error(self, message):
        """Log error message."""
        self._log(message, Qgis.Critical, 'ERROR')
    
    def _log(self, message, qgis_level, level_str):
        """
        Internal logging method.
        
        Args:
            message (str): Message to log
            qgis_level (Qgis.MessageLevel): QGIS message level
            level_str (str): Level string for file logging
        """
        # Log to QGIS
        QgsMessageLog.logMessage(message, self.name, qgis_level)
        
        # Log to file if configured
        if self.log_file:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_line = f'[{timestamp}] [{level_str}] [{self.name}] {message}\n'
            
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line)
            except Exception as e:
                QgsMessageLog.logMessage(
                    f'Failed to write to log file: {str(e)}',
                    self.name,
                    Qgis.Warning
                )