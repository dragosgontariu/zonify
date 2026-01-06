"""
Zonify Progress Dialog

Real-time progress tracking dialog for batch processing.

Features:
- Overall progress bar
- Current raster info
- Polygon processing count
- Live statistics
- Pause/Cancel buttons
- Minimize to tray
- Time estimates

Author: Dragos Gontariu
License: GPL-3.0
"""

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QGroupBox, QApplication
)
from qgis.PyQt.QtCore import Qt, QTimer, pyqtSignal
from qgis.PyQt.QtGui import QFont
from datetime import datetime, timedelta
import time


class ProgressDialog(QDialog):
    """
    Progress dialog for batch processing.
    Shows real-time progress, statistics, and allows pause/cancel.
    """
    
    # Signals
    cancelRequested = pyqtSignal()
    pauseRequested = pyqtSignal()
    resumeRequested = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Constructor.
        
        Args:
            parent: Parent widget
        """
        super(ProgressDialog, self).__init__(parent)
        
        # State
        self.is_paused = False
        self.is_cancelled = False
        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = 0
        
        # Setup UI
        self._setup_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_elapsed_time)
        self.update_timer.start(1000)  # Update every second
    
    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle('Zonify - Processing')
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        # Prevent closing with X button
        self.setWindowFlags(
            Qt.Window | 
            Qt.WindowTitleHint | 
            Qt.CustomizeWindowHint
        )
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('Processing Zonal Statistics')
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # === OVERALL PROGRESS ===
        overall_group = QGroupBox('Overall Progress')
        overall_layout = QVBoxLayout()
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setTextVisible(True)
        self.overall_progress.setFormat('%p% - %v/%m')
        overall_layout.addWidget(self.overall_progress)
        
        self.overall_label = QLabel('Starting...')
        overall_layout.addWidget(self.overall_label)
        
        overall_group.setLayout(overall_layout)
        layout.addWidget(overall_group)
        
        # === CURRENT RASTER ===
        current_group = QGroupBox('Current Raster')
        current_layout = QVBoxLayout()
        
        self.current_raster_label = QLabel('Waiting to start...')
        self.current_raster_label.setWordWrap(True)
        current_layout.addWidget(self.current_raster_label)
        
        self.raster_progress = QProgressBar()
        self.raster_progress.setTextVisible(True)
        current_layout.addWidget(self.raster_progress)
        
        self.polygon_count_label = QLabel('Polygons: 0 / 0')
        current_layout.addWidget(self.polygon_count_label)
        
        current_group.setLayout(current_layout)
        layout.addWidget(current_group)
        
        # === STATISTICS ===
        stats_group = QGroupBox('Statistics')
        stats_layout = QVBoxLayout()
        
        stats_grid = QHBoxLayout()
        
        # Time
        time_layout = QVBoxLayout()
        time_layout.addWidget(QLabel('<b>Time</b>'))
        self.elapsed_label = QLabel('Elapsed: 00:00:00')
        self.eta_label = QLabel('ETA: calculating...')
        time_layout.addWidget(self.elapsed_label)
        time_layout.addWidget(self.eta_label)
        stats_grid.addLayout(time_layout)
        
        # Performance
        perf_layout = QVBoxLayout()
        perf_layout.addWidget(QLabel('<b>Performance</b>'))
        self.speed_label = QLabel('Speed: -- polygons/sec')
        self.memory_label = QLabel('Memory: --')
        perf_layout.addWidget(self.speed_label)
        perf_layout.addWidget(self.memory_label)
        stats_grid.addLayout(perf_layout)
        
        stats_layout.addLayout(stats_grid)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # === LOG ===
        log_group = QGroupBox('Processing Log')
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # === BUTTONS ===
        button_layout = QHBoxLayout()
        
        button_layout.addStretch()
        
        self.pause_btn = QPushButton('Pause')
        self.pause_btn.setMinimumWidth(100)
        self.pause_btn.clicked.connect(self._on_pause)
        button_layout.addWidget(self.pause_btn)
        
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_btn)
        
        self.minimize_btn = QPushButton('Minimize')
        self.minimize_btn.setMinimumWidth(100)
        self.minimize_btn.clicked.connect(self.showMinimized)
        button_layout.addWidget(self.minimize_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def start_processing(self, total_rasters, total_polygons):
        """
        Start processing tracking.
        
        Args:
            total_rasters (int): Total number of rasters
            total_polygons (int): Total number of polygons
        """
        self.start_time = time.time()
        self.total_pause_duration = 0
        
        self.overall_progress.setMaximum(total_rasters)
        self.overall_progress.setValue(0)
        
        self.raster_progress.setMaximum(total_polygons)
        self.raster_progress.setValue(0)
        
        self.log('Started processing')
        self.log(f'Total rasters: {total_rasters}')
        self.log(f'Total polygons: {total_polygons}')
    
    def update_progress(self, data):
        """
        Update progress with new data.
        
        Args:
            data (dict): Progress data with keys:
                - message (str): Status message
                - percent (int): Overall progress percentage
                - current_raster (int): Current raster index
                - total_rasters (int): Total rasters
                - processed_polygons (int): Polygons processed
                - total_polygons (int): Total polygons
        """
        # Overall progress
        if 'percent' in data:
            self.overall_progress.setValue(data.get('current_raster', 0))
            self.overall_label.setText(data['message'])
        
        # Current raster
        if 'current_raster' in data and 'total_rasters' in data:
            current = data['current_raster']
            total = data['total_rasters']
            self.current_raster_label.setText(
                f'Processing raster {current}/{total}: {data.get("message", "")}'
            )
        
        # Polygon progress
        if 'processed_polygons' in data and 'total_polygons' in data:
            processed = data['processed_polygons']
            total = data['total_polygons']
            
            # Calculate current raster progress
            current_raster = data.get('current_raster', 1)
            total_rasters = data.get('total_rasters', 1)
            
            # For display: show progress within current raster
            if total > 0:
                raster_processed = processed % total
                if raster_processed == 0 and processed > 0:
                    raster_processed = total
            else:
                raster_processed = 0
            
            self.raster_progress.setValue(raster_processed)
            self.polygon_count_label.setText(f'Polygons: {raster_processed:,} / {total:,}')
            
            # Calculate speed and ETA based on TOTAL work
            if self.start_time and processed > 0 and total > 0:
                elapsed = time.time() - self.start_time - self.total_pause_duration
                if elapsed > 0:
                    speed = processed / elapsed
                    self.speed_label.setText(f'Speed: {speed:.1f} polygons/sec')
                    
                    # Calculate ETA for ALL remaining work
                    total_work = total * total_rasters
                    remaining = total_work - processed
                    if speed > 0 and remaining > 0:
                        eta_seconds = remaining / speed
                        eta = timedelta(seconds=int(eta_seconds))
                        self.eta_label.setText(f'ETA: {str(eta)}')
                    elif remaining <= 0:
                        self.eta_label.setText(f'ETA: finishing...')
            
            # Update memory usage
            try:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.memory_label.setText(f'Memory: {memory_mb:.1f} MB')
            except:
                self.memory_label.setText('Memory: --')
        
        # Force UI update
        QApplication.processEvents()
    
    def log(self, message):
        """
        Add message to log.
        
        Args:
            message (str): Message to log
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.append(f'[{timestamp}] {message}')
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        QApplication.processEvents()
    
    def _update_elapsed_time(self):
        """Update elapsed time label."""
        if self.start_time:
            if self.is_paused and self.pause_time:
                elapsed = self.pause_time - self.start_time - self.total_pause_duration
            else:
                elapsed = time.time() - self.start_time - self.total_pause_duration
            
            elapsed_td = timedelta(seconds=int(elapsed))
            self.elapsed_label.setText(f'Elapsed: {str(elapsed_td)}')
    
    def _on_pause(self):
        """Handle pause button click."""
        if self.is_paused:
            # Resume
            if self.pause_time:
                self.total_pause_duration += time.time() - self.pause_time
                self.pause_time = None
            
            self.is_paused = False
            self.pause_btn.setText('Pause')
            self.log('Processing resumed')
            self.resumeRequested.emit()
        else:
            # Pause
            self.pause_time = time.time()
            self.is_paused = True
            self.pause_btn.setText('Resume')
            self.log('Processing paused')
            self.pauseRequested.emit()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        from qgis.PyQt.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            'Cancel Processing',
            'Are you sure you want to cancel processing?\n\n'
            'Progress will be lost.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.is_cancelled = True
            self.cancel_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.log('Cancelling...')
            self.cancelRequested.emit()
    
    def finish(self, success, message=''):
        """
        Finish processing.
        
        Args:
            success (bool): Whether processing succeeded
            message (str): Final message
        """
        self.update_timer.stop()
        
        if success:
            self.overall_progress.setValue(self.overall_progress.maximum())
            self.log('✓ Processing completed successfully!')
            if message:
                self.log(message)
        else:
            self.log('✗ Processing failed!')
            if message:
                self.log(f'Error: {message}')
        
        # Change buttons
        self.pause_btn.setVisible(False)
        self.cancel_btn.setText('Close')
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.accept)
    
    def closeEvent(self, event):
        """Handle close event."""
        # Prevent closing during processing
        if not self.is_cancelled and self.overall_progress.value() < self.overall_progress.maximum():
            event.ignore()
            self.showMinimized()
        else:
            event.accept()