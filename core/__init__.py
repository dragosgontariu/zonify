"""
Zonify Core Processing Package

Contains the main processing engine:
- Processor: Main batch processor orchestrator
- ZonalCalculator: Statistical calculations engine
- TileProcessor: Tile-based raster processing
- RasterHandler: Raster I/O and manipulation
- ResourceManager: RAM/CPU management
- BackgroundWorker: Non-blocking processing

Architecture:
- Single machine optimized
- User-controlled resources (RAM/CPU)
- Tile-based for memory efficiency
- Background processing (separate process)
- Resume/checkpoint support

Author: Dragos Gontariu
License: GPL-3.0
"""