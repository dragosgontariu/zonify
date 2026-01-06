"""
Zonify - Main Plugin Class

This is the main entry point for the Zonify plugin.
Handles plugin initialization, UI setup, and lifecycle management.

Architecture:
- NO ML/AI, NO Cloud, NO Network clustering
- Single machine optimized
- User-controlled resources (RAM/CPU)
- Background processing (separate process, non-blocking)

Author: Dragos Gontariu
License: GPL-3.0
"""
# FORCE RELOAD MARKER
__RELOAD_TIMESTAMP__ = "2024-12-10-14-45-00"
print(f"★★★ ZONIFY.PY LOADED - TIMESTAMP: {__RELOAD_TIMESTAMP__} ★★★")
import os
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsMessageLog, Qgis
from qgis.core import QgsProject
# Import dependency checker (will create this next)
from .utils.dependency_checker import DependencyChecker


class Zonify:
    """
    Main plugin class for Zonify.
    
    Manages plugin lifecycle:
    - Initialization
    - UI setup (toolbar, menu)
    - Cleanup on unload
    """
    
    def __init__(self, iface):
        """
        Constructor.
        
        Args:
            iface (QgisInterface): QGIS interface instance
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        # Initialize locale (English only for now)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'zonify_{locale}.qm'
        )
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        
        # Plugin actions
        self.actions = []
        self.menu = self.tr('&Zonify')
        
        # Check if plugin is started for the first time
        self.first_start = None
        
        # Main dialog reference (will be created on first run)
        self.dlg = None
        
        # Log startup
        QgsMessageLog.logMessage(
            'Zonify plugin initialized',
            'Zonify',
            Qgis.Info
        )
    
    def tr(self, message):
        """
        Get the translation for a string using Qt translation API.
        
        Args:
            message (str): String for translation
            
        Returns:
            str: Translated string
        """
        return QCoreApplication.translate('Zonify', message)
    
    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None
    ):
        """
        Add a toolbar icon and menu item to the plugin.
        
        Args:
            icon_path (str): Path to the icon for this action
            text (str): Text that should be shown in menu items
            callback (function): Function to be called when action is triggered
            enabled_flag (bool): Whether action should be enabled
            add_to_menu (bool): Add action to plugin menu
            add_to_toolbar (bool): Add action to toolbar
            status_tip (str): Optional status tip
            whats_this (str): Optional what's this text
            parent (QWidget): Parent widget for the new action
            
        Returns:
            QAction: The action that was created
        """
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        
        if status_tip is not None:
            action.setStatusTip(status_tip)
        
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        
        if add_to_toolbar:
            # Add to the toolbar
            self.iface.addToolBarIcon(action)
        
        if add_to_menu:
            # Add to the menu
            self.iface.addPluginToMenu(
                self.menu,
                action
            )
        
        self.actions.append(action)
        
        return action
    
    def initGui(self):
        """
        Create the menu entries and toolbar icons inside the QGIS GUI.
        Called by QGIS when plugin is loaded.
        """
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        
        self.add_action(
            icon_path,
            text=self.tr('Zonify - Advanced Zonal Statistics'),
            callback=self.run,
            parent=self.iface.mainWindow(),
            status_tip=self.tr('Open Zonify batch zonal statistics processor'),
            whats_this=self.tr('Process multiple rasters with advanced statistics')
        )
        
        # Mark that this is the first start
        self.first_start = True
    
    def unload(self):
        """
        Remove the plugin menu item and icon from QGIS GUI.
        Called by QGIS when plugin is unloaded.
        """
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&Zonify'),
                action
            )
            self.iface.removeToolBarIcon(action)
        
        # Clean up dialog if it exists
        if self.dlg is not None:
            self.dlg.close()
            self.dlg = None
        
        QgsMessageLog.logMessage(
            'Zonify plugin unloaded',
            'Zonify',
            Qgis.Info
        )
    
    def run(self):
        """
        Run method that performs all the real work.
        Called when user clicks the toolbar icon or menu item.
        """
        # First time: check dependencies
        if self.first_start:
            self.first_start = False
            
            # Check if required Python packages are installed
            checker = DependencyChecker()
            report = checker.get_detailed_report()
            
            if not report['can_run']:
                # Critical packages missing - cannot run
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle('Zonify - Missing Critical Dependencies')
                msg.setText(
                    'Zonify cannot run because critical packages are missing.\n\n'
                    f"Missing core packages: {', '.join(report['missing_core'])}"
                )
                msg.setInformativeText(
                    'Install using QGIS Python Console:\n\n'
                    'import subprocess, sys\n'
                    f"subprocess.check_call([sys.executable, '-m', 'pip', 'install', {' '.join(report['missing_core'])}])\n\n"
                    'Then restart QGIS.'
                )
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
                return
            
            elif report['missing_features']:
                # Optional packages missing - show info but allow to continue
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle('Zonify - Optional Features Disabled')
                msg.setText(
                    'Some export features will be disabled due to missing packages.\n\n'
                    'Disabled features:\n' + 
                    '\n'.join(f'  • {feature}' for feature in report['disabled_features'])
                )
                msg.setInformativeText(
                    'You can still use the plugin, but some export formats won\'t be available.\n\n'
                    'To enable all features, install missing packages:\n\n'
                    'In QGIS Python Console:\n'
                    'import subprocess, sys\n'
                    f"subprocess.check_call([sys.executable, '-m', 'pip', 'install', '{' '.join(report['missing_features'])}'])\n\n"
                    'Then restart QGIS.\n\n'
                    'Click OK to continue with available features.'
                )
                msg.setDetailedText(
                    checker.get_installation_instructions(
                        report['missing_core'],
                        report['missing_features']
                    )
                )
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                
                if msg.exec_() == QMessageBox.Cancel:
                    return
        
        # Import main dialog (only if dependencies are met)
        try:
            from .ui.main_dialog import ZonifyDialog
        except ImportError as e:
            QMessageBox.critical(
                self.iface.mainWindow(),
                'Zonify - Import Error',
                f'Failed to import main dialog:\n{str(e)}\n\n'
                'Please ensure all dependencies are installed.'
            )
            return
        
        # Create dialog if it doesn't exist
        if self.dlg is None:
            self.dlg = ZonifyDialog(self.iface)
            
            # Pass dependency info to dialog
            checker = DependencyChecker()
            report = checker.get_detailed_report()
            self.dlg.set_available_features(report)
            
            # Connect processing signal
            self.dlg.runProcessing.connect(self._start_processing)
        
        # Show the dialog
        self.dlg.show()
        
        # Bring to front
        self.dlg.raise_()
        self.dlg.activateWindow()

    def _start_processing(self, config):
        """
        Start batch processing with given configuration.
        Shows progress dialog.
        
        Args:
            config (dict): Processing configuration from dialog
        """
        print("=" * 50)
        print("DEBUG: _start_processing CALLED")
        print(f"DEBUG: Config keys = {list(config.keys())}")
        print(f"DEBUG: export_csv = {config.get('export_csv')}")
        print(f"DEBUG: export_html = {config.get('export_html')}")
        print(f"DEBUG: export_pdf = {config.get('export_pdf')}")
        print(f"DEBUG: export_json = {config.get('export_json')}")
        print("=" * 50)
        from .core.processor import BatchProcessor
        from .ui.progress_dialog import ProgressDialog
        from qgis.PyQt.QtWidgets import QMessageBox
        
        QgsMessageLog.logMessage(
            'Starting batch processing',
            'Zonify',
            Qgis.Info
        )
        
        # Create and show progress dialog
        progress_dlg = ProgressDialog(self.iface.mainWindow())
        progress_dlg.start_processing(
            config['raster_count'],
            config['polygon_count']
        )
        progress_dlg.show()
        
        # Create processor with progress dialog
        processor = BatchProcessor(config, progress_dialog=progress_dlg)
        
        # Connect cancel signal
        progress_dlg.cancelRequested.connect(processor.cancel)
        
        # Run processing (blocking for now - Phase 3 will add true background)
        result = processor.run()
        
        # Finish progress dialog
        if result['success']:
            progress_dlg.finish(
                True,
                f'Processed {result["processed_rasters"]} rasters in {result["elapsed_time"]:.1f}s'
            )
            
            # Add output layer to map (if new layer was created)
            if result.get('output_layer') and config['output_mode'] == 'new':
                QgsProject.instance().addMapLayer(result['output_layer'])
        else:
            error_msg = result.get('error', 'Unknown error')
            progress_dlg.finish(False, error_msg)