"""
Zonify - Advanced Zonal Statistics for QGIS

This plugin provides professional batch zonal statistics processing with:
- Multiple raster batch processing
- 15+ statistical measures
- Custom formulas
- Smart resource management
- Background processing (non-blocking)
- Professional reporting

Author: Dragos Gontariu
Email: gontariudragos@gmail.com
License: GPL-3.0
"""

def classFactory(iface):
    """
    Load Zonify plugin class from file zonify.py
    
    Args:
        iface: A QGIS interface instance
        
    Returns:
        Zonify plugin instance
    """
    from .zonify import Zonify
    return Zonify(iface)