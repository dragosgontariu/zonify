# Zonify - User Guide

Complete guide to using Zonify for advanced zonal statistics analysis in QGIS.

**Version:** 1.0.0  
**Last Updated:** January 2026

---

## 📑 Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [User Interface](#user-interface)
- [Core Features](#core-features)
- [Advanced Features](#advanced-features)
- [Export Formats](#export-formats)
- [Performance & Optimization](#performance--optimization)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Examples & Use Cases](#examples--use-cases)

---

## 🎯 Introduction

### What is Zonify?

Zonify is a professional QGIS plugin for performing advanced zonal statistics analysis. It allows you to efficiently extract and analyze raster data within polygon zones, with support for batch processing, multiple statistics, and professional reporting.

### Key Capabilities

- **Batch Processing**: Process unlimited rasters in one run
- **15+ Statistics**: From basic (mean, sum) to advanced (percentiles, CV)
- **Coverage Analysis**: Pixel-accurate geometric coverage calculation
- **Multi-threaded**: Utilize multiple CPU cores for faster processing
- **Smart Memory**: Configurable RAM limits prevent system overload
- **Background Processing**: QGIS stays fully responsive
- **Professional Reports**: HTML dashboards and PDF reports
- **Advanced Tools**: Score Creator, Classifier, Map Generator, and more

### Who is it for?

- **GIS Analysts** - Routine spatial analysis tasks
- **Environmental Scientists** - Monitoring and assessment
- **Urban Planners** - Accessibility and suitability analysis
- **Researchers** - Academic and applied research
- **Data Scientists** - Geospatial data processing pipelines

---

## 📥 Installation

### System Requirements

**Minimum:**
- QGIS 3.28 or higher
- Python 3.9 or higher
- 4GB RAM
- 2 CPU cores

**Recommended:**
- QGIS 3.34 or higher
- Python 3.11
- 16GB RAM
- 4+ CPU cores
- SSD storage for large datasets

### Dependency Installation

Zonify requires several Python packages. Install them based on your operating system:

#### Windows (OSGeo4W)

1. Open **OSGeo4W Shell** as Administrator
2. Run:
```bash
pip install numpy pandas scipy matplotlib plotly reportlab jinja2 psutil pyarrow
```

#### Windows (Standalone QGIS)

1. Open **Command Prompt** as Administrator
2. Navigate to QGIS Python:
```bash
cd "C:\Program Files\QGIS 3.X\bin"
python-qgis.bat -m pip install numpy pandas scipy matplotlib plotly reportlab jinja2 psutil pyarrow
```

#### Linux
```bash
pip3 install --user numpy pandas scipy matplotlib plotly reportlab jinja2 psutil pyarrow
```

#### macOS
```bash
/Applications/QGIS.app/Contents/MacOS/bin/pip3 install numpy pandas scipy matplotlib plotly reportlab jinja2 psutil pyarrow
```

### Verifying Installation

1. Open QGIS
2. Go to **Plugins** → **Manage and Install Plugins**
3. Find "Zonify" in the list
4. Check the box to enable
5. Look for Zonify icon in toolbar

---

## 🖥️ User Interface

### Main Window

The Zonify interface is organized into tabs:

#### Tab 1: Input & Statistics

**Purpose:** Configure input data and select statistics

**Components:**
- **Polygon Layer Selector** - Choose your zones layer
- **Raster List** - Add/remove raster files
- **Statistics Checkboxes** - Select which statistics to calculate
- **Output Configuration** - Set output path and formats

#### Tab 2: Advanced

**Purpose:** Access advanced analysis tools

**Tools:**
- **Score Creator** - Weighted multi-criteria analysis
- **Area Classifier** - Classify continuous values
- **Area Highlighter** - Identify top/bottom areas
- **Rule Tagger** - Apply conditional rules
- **Quick Map** - Generate professional maps
- **Time Series** - Temporal analysis

#### Tab 3: Settings

**Purpose:** Configure performance and behavior

**Options:**
- **CPU Cores** - Number of threads to use
- **RAM Limit** - Maximum memory allocation
- **Chunk Size** - Processing batch size
- **Temporary Directory** - Location for temp files

---

## 🔧 Core Features

### 1. Basic Zonal Statistics

#### Available Statistics

**Position Statistics:**
- **Mean** - Average value within zone
- **Median** - Middle value (50th percentile)
- **Mode** - Most frequent value
- **Min** - Minimum value
- **Max** - Maximum value

**Dispersion Statistics:**
- **Sum** - Total sum of values
- **Standard Deviation** - Measure of spread
- **Variance** - Square of standard deviation
- **Coefficient of Variation (CV)** - Std Dev / Mean × 100
- **Range** - Max - Min

**Distribution Statistics:**
- **Percentile 25** (Q1) - First quartile
- **Percentile 50** (Q2) - Median
- **Percentile 75** (Q3) - Third quartile
- **Percentile 90** - 90th percentile
- **Percentile 95** - 95th percentile

**Coverage Statistics:**
- **Count** - Number of pixels with data
- **Coverage** - Percentage of polygon covered by raster data

#### How Statistics are Calculated

1. **Pixel Extraction:**
   - All raster pixels that intersect the polygon are extracted
   - Uses ALL_TOUCHED mode (pixels touching polygon edge are included)
   - NoData values are excluded from calculations

2. **Aggregation:**
   - Statistics are calculated from all valid pixels
   - Geometric coverage accounts for partial pixels

3. **Output:**
   - New column added to output layer
   - Column name: `{raster_name}_{statistic}`
   - Example: `temperature_mean`, `population_sum`

#### When to Use Which Statistic

| Use Case | Recommended Statistics |
|----------|----------------------|
| Average conditions | Mean, Median |
| Total amounts | Sum |
| Extreme values | Min, Max, Percentiles |
| Variability | Std Dev, CV, Range |
| Distribution shape | Percentiles (25, 50, 75) |
| Data coverage | Count, Coverage |

---

### 2. Batch Processing

#### How Batch Processing Works

1. **VRT Creation:**
   - Virtual Raster (VRT) combines multiple rasters
   - Efficient reading without creating large temporary files

2. **Chunked Processing:**
   - Features processed in chunks (default: 1000 per chunk)
   - Prevents memory overflow on large datasets

3. **Multi-threading:**
   - Multiple CPU cores process different chunks simultaneously
   - Speeds up processing significantly

4. **Checkpointing:**
   - Progress saved periodically
   - Allows resuming if interrupted

#### Configuring Batch Processing

**CPU Cores:**
- Default: Auto-detect (uses all available cores - 1)
- Recommended: Leave 1-2 cores free for system
- Example: 8-core system → use 6 cores

**RAM Limit:**
- Default: 50% of system RAM
- Adjust based on other running applications
- Example: 16GB system → 8GB limit

**Chunk Size:**
- Default: 1000 features
- Larger chunks = faster but more RAM
- Smaller chunks = slower but less RAM

---

### 3. Coverage Calculation

#### What is Coverage?

Coverage is the percentage of a polygon that contains valid raster data.

**Example:**
```
Polygon area: 10,000 m²
Raster pixels covering polygon: 8,500 m²
Coverage: 85%
```

#### Why Coverage Matters

- Identifies polygons with incomplete data
- Helps assess data quality
- Important for interpreting statistics

**Example Use Case:**
```
Forest parcel: 100 hectares
Satellite coverage: 75%
→ 25% was cloudy during satellite pass
→ Statistics only represent 75% of parcel
```

#### Coverage Types

**Pixel Coverage:**
- Counts number of pixels
- Fast but less accurate for edge pixels

**Geometric Coverage:**
- Calculates actual area covered
- Slower but more accurate
- **Zonify uses this method!**

---

### 4. Resume Capability

#### How Checkpoints Work

**Automatic Checkpointing:**
- Progress saved every 100 features (configurable)
- Checkpoint files stored in temporary directory
- Small file size (~1KB per checkpoint)

**Resuming:**
1. Processing interrupted (crash, power loss, user cancellation)
2. Reopen Zonify
3. Load same configuration
4. Click **Resume**
5. Processing continues from last checkpoint

**Limitations:**
- Must use same input data
- Must use same output path
- Checkpoints expire after 24 hours

---

## 🎨 Advanced Features

### 1. Score Creator

**Purpose:** Combine multiple indicators into a single composite score

#### Use Cases

- **Risk Assessment:** Combine flood, earthquake, population → Risk Score
- **Suitability Analysis:** Combine slope, aspect, soil → Suitability Score
- **Priority Ranking:** Combine poverty, accessibility, infrastructure → Priority Score

#### How to Use

1. **Go to Advanced Tab → Score Creator**

2. **Select Source Layer:**
   - Choose layer with processed statistics
   - Must have numeric fields

3. **Refresh Available Fields:**
   - Click "🔄 Refresh Available Fields"
   - All numeric fields appear in table

4. **Select Indicators:**
   - Check indicators to include
   - Assign importance level:
     - Very High (50% weight)
     - High (30% weight)
     - Medium (15% weight)
     - Low (5% weight)

5. **Name Your Score:**
   - Give it a meaningful name
   - Example: "Risk_Score", "Suitability_Index"

6. **Choose Normalization (Advanced Options):**
   - **Min-Max (0-100):** Scales all values to 0-100 range
   - **Z-Score:** Standardizes using mean and standard deviation
   - **None:** Uses raw values

7. **Apply Score:**
   - New layer created with score field
   - Classify or visualize the scores

#### Example
```
Goal: Create Urban Livability Score

Indicators:
✓ park_accessibility_mean (Very High) → 50%
✓ school_distance_mean (High) → 30%
✓ air_quality_mean (Medium) → 15%
✓ noise_level_mean (Low) → 5%

Normalization: Min-Max (0-100)

Result: Each neighborhood gets score 0-100
Higher score = more livable
```

---

### 2. Area Classifier

**Purpose:** Classify continuous values into discrete categories

#### Classification Methods

**Equal Intervals:**
- Divides range into equal-sized bins
- Good for uniform distributions
- Example: 0-25 (Low), 25-50 (Medium), 50-75 (High), 75-100 (Very High)

**Quantiles:**
- Equal number of features per class
- Good for skewed distributions
- Each class has same count of features

**Natural Breaks (Jenks):**
- Finds natural groupings in data
- Minimizes within-class variance
- Best for most real-world data

**Custom Breaks:**
- You define exact thresholds
- Maximum control
- Example: <10 (Low), 10-50 (Medium), >50 (High)

#### How to Use

1. **Select Source Layer**
2. **Choose Field to Classify**
3. **Select Method** (Equal Intervals, Quantiles, Jenks, or Custom)
4. **Choose Number of Classes** (3 or 5)
5. **Customize Labels** (Optional)
6. **Apply Classification**

Result: New layer with categorical field

---

### 3. Quick Map

**Purpose:** Generate professional print-ready maps

#### Features

- **Automatic Layout:** Smart placement of elements
- **Legend:** Auto-generated from layer symbology
- **Scale Bar:** Automatically sized
- **North Arrow:** Standard cartographic symbol
- **Title & Subtitle:** Customizable text
- **Multiple Formats:** PNG, PDF, SVG

#### How to Use

1. **Select Layer to Map**
2. **Configure Elements:**
   - Title
   - Subtitle
   - Legend (on/off)
   - Scale Bar (on/off)
   - North Arrow (on/off)
   - Attribution text

3. **Choose Page Size:**
   - A4 (210×297mm)
   - A3 (297×420mm)
   - Letter (216×279mm)

4. **Orientation:**
   - Portrait
   - Landscape

5. **Generate Map:**
   - Opens in QGIS Layout Manager
   - Export to PNG/PDF

---

### 4. Time Series Analysis

**Purpose:** Analyze temporal changes and trends

#### What It Does

Given multiple rasters from different time periods, calculates:

- **First Value** - Value from earliest time period
- **Last Value** - Value from latest time period
- **Total Change** - Last - First
- **Percent Change** - (Change / First) × 100
- **Mean Change** - Average change per time step
- **Trend Slope** - Linear regression slope
- **Trend R²** - How well data fits linear trend
- **Temporal Mean** - Average across all time periods
- **Temporal Min/Max** - Minimum/maximum across time
- **Temporal Range** - Max - Min across time

#### Example Use Case
```
Forest Monitoring:
Rasters: NDVI monthly (Jan 2020 - Dec 2023) = 48 rasters

Output per forest parcel:
- ts_first_value: NDVI in Jan 2020
- ts_last_value: NDVI in Dec 2023
- ts_total_change: Change over 4 years
- ts_percent_change: % change
- ts_trend_slope: Rate of change (NDVI units/month)
- ts_trend_r2: How consistent is the trend

Interpretation:
- Negative slope = deforestation
- Positive slope = regrowth
- High R² = steady trend
- Low R² = variable/seasonal pattern
```

---

## 📤 Export Formats

### 1. GeoPackage (.gpkg)

**Primary output format**

**Advantages:**
- Single-file database
- Fast performance
- Works perfectly with QGIS
- Supports large datasets
- Maintains spatial index

**When to use:** Always! It's the best format for QGIS workflows.

---

### 2. CSV

**Tabular data export**

**Advantages:**
- Opens in Excel, Google Sheets
- Human-readable
- Easy to share
- Good for further analysis

**Disadvantages:**
- No spatial data
- Only attribute table

**When to use:** When sharing with non-GIS users or importing to spreadsheets

---

### 3. JSON

**Structured data format**

**Advantages:**
- Machine-readable
- Good for APIs
- Preserves data types
- Nested structures

**When to use:** Web applications, APIs, programmatic access

---

### 4. HTML Dashboard

**Interactive web report**

**Features:**
- Interactive Plotly charts
- Dark/Light mode
- Search and filter
- Pagination (100 entries/page)
- Coverage analysis
- Statistics per raster
- Responsive design

**When to use:** Exploring results, presentations, sharing with stakeholders

**Opening:** Double-click .html file or use "Open HTML Dashboard" button

---

### 5. PDF Report

**Professional printable report**

**Includes:**
- Summary statistics table
- Charts and visualizations
- Formatted for printing
- Page numbers and headers

**When to use:** Official reports, documentation, archiving

---

## ⚡ Performance & Optimization

### Processing Speed Factors

**What affects speed:**
1. **Number of features** - More polygons = longer processing
2. **Number of rasters** - More rasters = longer processing
3. **Raster resolution** - Higher resolution = more pixels = slower
4. **Number of statistics** - More stats = slightly slower
5. **CPU cores** - More cores = faster
6. **Storage speed** - SSD much faster than HDD

### Performance Benchmarks

**Example system: 8-core CPU, 16GB RAM, SSD**

| Features | Rasters | Statistics | Time |
|----------|---------|-----------|------|
| 10 | 1 | 5 | ~5 sec |
| 100 | 5 | 8 | ~30 sec |
| 1,000 | 10 | 10 | ~2 min |
| 10,000 | 10 | 10 | ~8 min |
| 100,000 | 10 | 10 | ~30 min |
| 500,000 | 20 | 15 | ~2-3 hours |

### Optimization Tips

**1. Use VRT for multiple rasters:**
- Zonify does this automatically
- Much faster than processing rasters individually

**2. Reduce raster resolution (if appropriate):**
- Resample to lower resolution for preliminary analysis
- Use full resolution for final analysis

**3. Use SSD storage:**
- 2-3x faster than HDD
- Especially important for large datasets

**4. Adjust chunk size:**
- Larger chunks = faster but more RAM
- Optimal: 1000-5000 features per chunk

**5. Close other applications:**
- Free up RAM and CPU
- Disable antivirus temporarily for very large jobs

**6. Use appropriate statistics:**
- Mean/Sum are fast
- Percentiles are slower (require sorting)
- Only calculate what you need

---

## 🎯 Best Practices

### Data Preparation

**1. Check CRS (Coordinate Reference Systems):**
- Ensure polygons and rasters use compatible CRS
- Zonify handles reprojection but it's slower
- Best: Use same CRS for all data

**2. Validate geometries:**
- Fix invalid polygons before processing
- Use QGIS: Vector → Geometry Tools → Check Validity

**3. Clean up polygons:**
- Remove tiny slivers (<1 pixel)
- Simplify overly complex boundaries (if appropriate)

**4. Prepare rasters:**
- Set NoData values correctly
- Check for corruption
- Consider creating pyramids for large rasters

### Project Organization

**1. Use descriptive names:**
```
Good: districts_temp_august_2023.gpkg
Bad: output1.gpkg
```

**2. Organize by project:**
```
project_name/
├── input/
│   ├── polygons/
│   └── rasters/
├── output/
│   ├── gpkg/
│   ├── reports/
│   └── maps/
└── documentation/
```

**3. Document your workflow:**
- Note which statistics you used and why
- Record any data processing steps
- Save QGIS project file

### Quality Control

**1. Visual inspection:**
- Load output in QGIS
- Check if values make sense
- Look for spatial patterns

**2. Check coverage:**
- Review coverage statistics
- Identify polygons with low coverage
- Decide if they should be excluded

**3. Validate against known values:**
- Compare results to manual calculations
- Check a few polygons by hand
- Verify units are correct

---

## 🔍 Troubleshooting

### Common Issues

#### Issue: "Module not found: numpy"

**Cause:** Python dependencies not installed

**Solution:**
```bash
# Windows (OSGeo4W Shell as Admin):
pip install numpy pandas scipy matplotlib plotly reportlab jinja2

# Linux/Mac:
pip3 install --user numpy pandas scipy matplotlib plotly reportlab jinja2
```

---

#### Issue: Processing crashes or freezes

**Possible causes:**
1. Out of memory
2. Corrupted raster file
3. Invalid geometries

**Solutions:**
1. Reduce RAM limit in settings
2. Process fewer rasters at once
3. Check raster files individually in QGIS
4. Validate and fix polygon geometries

---

#### Issue: Results seem incorrect

**Checks:**
1. Verify CRS matches between polygons and rasters
2. Check raster NoData values are set correctly
3. Verify raster units (e.g., temperature in Celsius vs Kelvin)
4. Check for attribute name conflicts
5. Review coverage statistics

---

#### Issue: Very slow performance

**Solutions:**
1. Increase chunk size (Settings tab)
2. Use more CPU cores
3. Use SSD instead of HDD
4. Close other applications
5. Process fewer statistics
6. Reduce raster resolution (if appropriate)

---

#### Issue: HTML dashboard doesn't open

**Causes:**
1. Browser security settings
2. File path contains special characters
3. HTML file corrupted

**Solutions:**
1. Try different browser (Chrome, Firefox, Edge)
2. Move file to simple path (no spaces, special chars)
3. Regenerate HTML export

---

## 📊 Examples & Use Cases

### Example 1: Flood Risk Assessment

**Objective:** Identify high-risk neighborhoods

**Data:**
- Polygons: City neighborhoods (250 features)
- Rasters:
  - Elevation (DEM)
  - Flood zones (depth in meters)
  - Population density

**Statistics:**
- Elevation: Mean, Min
- Flood zones: Mean, Max
- Population: Sum

**Workflow:**
1. Calculate statistics
2. Use Score Creator:
   - Flood depth (Very High)
   - Population (Very High)
   - Elevation (Medium - inverse)
3. Classify into risk categories
4. Generate risk map

**Time:** ~2 minutes

---

### Example 2: Solar Panel Suitability

**Objective:** Find best rooftops for solar panels

**Data:**
- Polygons: Building footprints (10,000)
- Rasters:
  - Solar radiation (kWh/m²/year)
  - Slope (degrees)
  - Aspect (degrees)

**Statistics:**
- All: Mean

**Workflow:**
1. Calculate statistics
2. Rule Tagger:
   - Solar radiation > 1500 kWh/m²
   - Slope < 45°
   - Aspect between 135-225° (south-facing)
3. Classify suitable buildings
4. Export ranked list

**Time:** ~5 minutes

---

### Example 3: Agricultural Productivity

**Objective:** Analyze crop yield patterns

**Data:**
- Polygons: Farm fields (500)
- Rasters:
  - NDVI time series (monthly, 3 years = 36 rasters)
  - Soil moisture
  - Precipitation

**Statistics:**
- All: Mean, Std Dev

**Workflow:**
1. Calculate statistics for all rasters
2. Use Time Series Analysis:
   - Trend detection
   - Seasonal patterns
   - Anomaly identification
3. Correlate with yield data
4. Generate report

**Time:** ~10 minutes

---

## 📚 Additional Resources

### Documentation

- [Quick Start Guide](QUICK_START.md) - 5-minute tutorial
- [FAQ](FAQ.md) - Frequently asked questions
- [API Documentation](API.md) - For developers

### Support

- **Issues:** [GitHub Issues](https://github.com/dragosgontariu/zonify/issues)
- **Discussions:** [GitHub Discussions](https://github.com/dragosgontariu/zonify/discussions)
- **Email:** gontariudragos@gmail.com

### Community

- Share your workflows
- Report bugs
- Suggest features
- Contribute code

---

## 📝 Changelog

See [CHANGELOG.md](../CHANGELOG.md) for version history and release notes.

---

## 📄 License

Zonify is licensed under GPL-3.0. See [LICENSE](../LICENSE) for details.

---

**Last Updated:** January 2026  
**Version:** 1.0.0  
**Author:** Dragos Gontariu