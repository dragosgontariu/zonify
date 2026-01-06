# Changelog

All notable changes to the Zonify plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-XX (Upcoming)

### Added
- **Core Processing Engine:**
  - Batch processing of unlimited raster files
  - 15+ statistical measures (mean, sum, min, max, median, mode, std dev, variance, CV, percentiles, etc.)
  - Geometric coverage calculation (pixel-accurate)
  - All-touched pixel extraction for edge cases
  - Multi-threaded processing with user-controlled CPU cores
  - Smart RAM management with configurable limits
  - Resume/checkpoint system for long-running jobs
  
- **Advanced Features:**
  - **Score Creator:** Combine multiple indicators with weighted importance
  - **Area Classifier:** Classify continuous values into categories (Equal Intervals, Quantiles, Jenks, Custom)
  - **Area Highlighter:** Identify top/bottom performing areas based on criteria
  - **Rule Tagger:** Apply custom rules with AND/OR logic
  - **Quick Map:** Generate professional maps with legend, scale bar, north arrow
  - **Time Series Analysis:** Temporal trend detection and change analysis
  
- **Custom Algorithms:**
  - User-defined formulas for aggregated statistics
  - Pixel-by-pixel operations
  - Safe evaluation with restricted namespace
  
- **Export Formats:**
  - GeoPackage (.gpkg) - primary output
  - CSV - tabular data
  - JSON - structured data
  - HTML - interactive dashboards with charts and visualizations
  - PDF - professional reports
  
- **HTML Dashboard Features:**
  - Interactive Plotly charts
  - Responsive design
  - Dark/Light mode toggle
  - Pagination for large datasets (100 entries/page)
  - Search/filter functionality
  - Coverage analysis with breakdown by ranges
  - Statistics visualization per raster
  
- **User Interface:**
  - Modern tab-based interface
  - Real-time validation
  - Progress tracking with pause/resume
  - Background processing (non-blocking)
  - Comprehensive error messages
  
- **Performance:**
  - VRT (Virtual Raster) support for multi-raster efficiency
  - Chunked processing for memory efficiency
  - Automatic raster alignment
  - NoData handling
  
### Fixed
- QVariant conversion issues across all widgets
- Edge pixel extraction accuracy (ALL_TOUCHED mode)
- Coverage calculation precision (geometric vs pixel-based)
- Layer selection from Layer Panel in Advanced widgets
- Auto-refresh fields when layer is selected
- Map extent buffer optimization in Quick Map
- Pagination display logic in HTML exports

### Changed
- Improved terminology: "Features with coverage" vs "Features analyzed" (coverage-aware)
- Optimized HTML dashboard layout (reduced margins, better space utilization)
- Enhanced KPI cards with contextual subtitles

### Technical
- Python 3.9+ required
- QGIS 3.28+ required
- Dependencies: numpy, pandas, scipy, matplotlib, plotly, reportlab, jinja2, psutil, pyarrow

---

## [Unreleased]

### Planned for v1.1.0
- Spatial autocorrelation (Moran's I, Getis-Ord Gi*)
- Excel export (.xlsx)
- Before/after comparison analysis
- Batch map generation
- Plugin localization (i18n)

### Planned for v1.2.0
- Integration with cloud storage (GDrive, Dropbox)
- Real-time collaboration features
- Advanced caching system
- Performance profiling tools

### Planned for v2.0.0
- 3D visualization support
- Animation generation for time series
- Machine learning integration
- Web service API

---

## Version History

### Pre-release Development
- 2025-12-09: Initial plugin structure
- 2025-12-10: Core processing engine
- 2025-12-11: Basic UI implementation
- 2025-12-12: Export formats added
- 2025-12-19: Time Series widget
- 2026-01-03: Quick Map and PDF export
- 2026-01-04: HTML dashboard enhancements
- 2026-01-05: Validation tests on 150K+ features
- 2026-01-06: QVariant fixes and Advanced widget improvements

---

For detailed commit history, see: https://github.com/dragosgontariu/zonify/commits/main
