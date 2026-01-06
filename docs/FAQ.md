# Zonify - Frequently Asked Questions (FAQ)

Quick answers to common questions about Zonify.

---

## 📥 Installation & Setup

### Q: Where can I download Zonify?

**A:** 
- **Official:** QGIS Plugin Repository (search "Zonify" in Plugin Manager)
- **Development:** [GitHub Releases](https://github.com/dragosgontariu/zonify/releases)

---

### Q: What are the system requirements?

**A:**
- **QGIS:** 3.28 or higher
- **Python:** 3.9 or higher
- **RAM:** 4GB minimum, 16GB recommended
- **CPU:** 2 cores minimum, 4+ recommended

---

### Q: How do I install the Python dependencies?

**A:** Open terminal/command prompt and run:

**Windows (OSGeo4W Shell as Administrator):**
```bash
pip install numpy pandas scipy matplotlib plotly reportlab jinja2 psutil pyarrow
```

**Linux/Mac:**
```bash
pip3 install --user numpy pandas scipy matplotlib plotly reportlab jinja2 psutil pyarrow
```

---

### Q: I get "Module not found" errors. What should I do?

**A:** Python dependencies aren't installed. See answer above. If still failing:
1. Verify you're using the correct Python (QGIS Python, not system Python)
2. Try adding `--user` flag: `pip install --user ...`
3. Restart QGIS after installation

---

## 🔧 Usage

### Q: How many rasters can I process at once?

**A:** Unlimited! Zonify has been tested with 20+ rasters and works fine. Processing time increases linearly with number of rasters.

---

### Q: What raster formats are supported?

**A:** All formats supported by GDAL:
- GeoTIFF (.tif, .tiff)
- NetCDF (.nc)
- HDF (.hdf, .h5)
- IMG (.img)
- ASCII Grid (.asc)
- And many more!

---

### Q: Do polygons and rasters need to be in the same CRS?

**A:** No! Zonify automatically handles CRS differences. However, using the same CRS is faster.

---

### Q: What does "Coverage" mean?

**A:** Coverage is the percentage of a polygon that contains valid raster data (not NoData). 

Example: Coverage = 85% means 85% of polygon area has raster data, 15% is NoData or outside raster extent.

---

### Q: Which statistics should I use?

**A:** 
- **Mean** - Most common, good for average conditions (temperature, elevation)
- **Sum** - Good for counts/totals (population, area)
- **Min/Max** - Good for extremes (highest/lowest values)
- **Median** - Good when data has outliers
- **Std Dev** - Good for measuring variability

---

### Q: Can I process very large datasets?

**A:** Yes! Zonify has been tested with:
- 500,000+ features
- 20+ rasters
- Multi-gigabyte rasters

Tips for large datasets:
- Use SSD storage
- Allocate sufficient RAM
- Use multiple CPU cores
- Be patient - large jobs take hours!

---

## ⚡ Performance

### Q: How long does processing take?

**A:** Depends on data size. Examples (8-core PC, 16GB RAM, SSD):
- 10 polygons × 1 raster: ~5 seconds
- 1,000 polygons × 5 rasters: ~1-2 minutes
- 100,000 polygons × 10 rasters: ~20-30 minutes
- 500,000 polygons × 20 rasters: ~2-3 hours

---

### Q: Can I speed up processing?

**A:** Yes!
1. **Use more CPU cores** (Settings tab)
2. **Increase RAM limit** (if you have spare RAM)
3. **Use SSD instead of HDD** (2-3x faster)
4. **Reduce raster resolution** (if appropriate for your analysis)
5. **Process fewer statistics** (only calculate what you need)
6. **Close other applications** (free up resources)

---

### Q: Does QGIS freeze during processing?

**A:** No! Zonify uses background processing. QGIS stays fully responsive and you can continue working on other tasks.

---

### Q: Can I pause and resume processing?

**A:** Yes! Click "Pause" button during processing. Resume later from the same point using checkpoints.

---

## 📊 Results & Output

### Q: Where are my results?

**A:** 
1. **GeoPackage file** at the path you specified
2. Automatically added to QGIS Layers Panel
3. **HTML/PDF reports** in same folder as output file

---

### Q: How do I view the results?

**A:**
- **In QGIS:** Right-click output layer → Open Attribute Table
- **HTML Dashboard:** Click "Open HTML Dashboard" button or open .html file
- **PDF Report:** Open .pdf file in any PDF reader

---

### Q: What are the column names in the output?

**A:** Format: `{raster_name}_{statistic}`

Examples:
- `temperature_2023_mean`
- `population_density_sum`
- `elevation_min`

---

### Q: Can I export to Excel?

**A:** Yes! Export to CSV format, then open in Excel.

---

### Q: The HTML dashboard won't open. Why?

**A:** 
1. **Try different browser** (Chrome, Firefox, Edge)
2. **Check file path** - avoid special characters and spaces
3. **Browser security** - some browsers block local HTML files by default
4. **Regenerate** - Export HTML again

---

## 🎨 Advanced Features

### Q: What is Score Creator?

**A:** Tool to combine multiple indicators into a single composite score using weighted importance.

Example: Risk Score = Flood (High) + Population (High) + Elevation (Medium)

---

### Q: What classification methods are available?

**A:** 
- **Equal Intervals** - Equal-sized ranges
- **Quantiles** - Equal number of features per class
- **Natural Breaks (Jenks)** - Finds natural groupings
- **Custom Breaks** - You define thresholds

---

### Q: What is Time Series Analysis?

**A:** Analyzes changes over time using multiple rasters from different dates.

Calculates: Total change, Percent change, Trend slope, and more.

---

### Q: Can I generate maps?

**A:** Yes! Use **Quick Map** in Advanced tab to generate professional maps with legend, scale bar, and north arrow.

---

## 🐛 Troubleshooting

### Q: Processing failed with an error. What should I do?

**A:**
1. **Check error message** - often tells you what's wrong
2. **Verify input data:**
   - Polygons are valid geometries
   - Rasters aren't corrupted
   - Both have valid CRS
3. **Check available space** - ensure enough disk space
4. **Check RAM** - reduce RAM limit if system is low on memory
5. **Try with smaller dataset** - test with 10 polygons first

---

### Q: Results seem incorrect. How do I verify?

**A:**
1. **Check CRS** - ensure polygons and rasters align
2. **Check NoData values** - verify raster NoData is set correctly
3. **Check units** - ensure raster values are in expected units
4. **Visual inspection** - load results in QGIS and check visually
5. **Manual verification** - calculate statistics for 1-2 polygons by hand

---

### Q: Some polygons have very low coverage. Why?

**A:** Common reasons:
- Polygon extends outside raster extent
- Raster has NoData in that area (clouds, gaps in data)
- CRS mismatch causing misalignment

**Solution:** Check coverage statistics and decide if those polygons should be excluded from analysis.

---

### Q: Processing is very slow. What's wrong?

**A:**
1. **Check storage speed** - HDD much slower than SSD
2. **Check available RAM** - if RAM is full, system uses slow disk swap
3. **Check CPU usage** - should be high during processing
4. **Check other applications** - close unnecessary programs
5. **Reduce chunk size** if running out of RAM
6. **Check raster size** - very large rasters take longer

---

## 💾 Data & Compatibility

### Q: What input polygon formats are supported?

**A:** All QGIS-supported vector formats:
- GeoPackage (.gpkg)
- Shapefile (.shp)
- GeoJSON (.geojson)
- KML (.kml)
- And more!

---

### Q: Can I use multipolygons?

**A:** Yes! Zonify handles both Polygon and MultiPolygon geometries.

---

### Q: Can I use 3D or time-enabled rasters?

**A:** 
- **3D rasters (multi-band):** Yes, each band processed separately
- **Time-enabled rasters:** Yes, use Time Series Analysis feature

---

### Q: What about very large rasters (>10GB)?

**A:** Yes, Zonify can handle them! Tips:
- Ensure enough disk space (3x raster size for temp files)
- Use SSD for better performance
- Consider processing in chunks
- Be patient - processing takes time

---

## 🔐 Privacy & Security

### Q: Does Zonify send data anywhere?

**A:** No! All processing is done locally on your computer. No data is sent to external servers.

---

### Q: Is my data safe?

**A:** Yes! Zonify only reads/writes files you specify. It doesn't modify your original input files.

---

## 📖 Learning & Support

### Q: Where can I find tutorials?

**A:**
- [Quick Start Guide](QUICK_START.md) - 5-minute tutorial
- [User Guide](USER_GUIDE.md) - Comprehensive documentation
- YouTube channel *(coming soon)*

---

### Q: How do I report a bug?

**A:** [GitHub Issues](https://github.com/dragosgontariu/zonify/issues)

Please include:
- QGIS version
- Zonify version
- Operating system
- Steps to reproduce
- Error message (if any)

---

### Q: How do I request a feature?

**A:** [GitHub Issues](https://github.com/dragosgontariu/zonify/issues) with label "enhancement"

---

### Q: Can I contribute to Zonify?

**A:** Yes! Contributions welcome!
- Report bugs
- Suggest features
- Improve documentation
- Submit pull requests

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## 🎓 Advanced Questions

### Q: Can I use custom formulas?

**A:** Yes! In Tab 1, expand "Custom Formulas" section. Use Python expressions with numpy functions.

Example: `np.sqrt(field1**2 + field2**2)`

---

### Q: Can I automate Zonify with Python?

**A:** Yes! Zonify can be called from QGIS Python console. Documentation coming soon in API.md.

---

### Q: Does Zonify support parallel processing?

**A:** Yes! Multi-threaded processing uses all available CPU cores (configurable in Settings).

---

### Q: Can I process rasters with different resolutions?

**A:** Yes! Zonify handles different resolutions automatically. Statistics are calculated correctly regardless of pixel size.

---

### Q: What about rasters with different extents?

**A:** No problem! Each polygon gets statistics only from the rasters that cover it. Coverage statistic shows how much of polygon is covered.

---

## 💰 Licensing & Usage

### Q: Is Zonify free?

**A:** Yes! Zonify is open source under GPL-3.0 license.

---

### Q: Can I use Zonify commercially?

**A:** Yes! GPL-3.0 allows commercial use.

---

### Q: Can I modify Zonify?

**A:** Yes! You can modify and distribute under GPL-3.0 terms.

---

## 🔄 Updates

### Q: How do I update Zonify?

**A:** 
1. **QGIS Plugin Manager:** Checks for updates automatically
2. **Manual:** Download latest version from GitHub

---

### Q: What's the current version?

**A:** Check in QGIS Plugin Manager or see [GitHub Releases](https://github.com/dragosgontariu/zonify/releases)

---

### Q: What's planned for future versions?

**A:** See [CHANGELOG.md](../CHANGELOG.md) for roadmap and planned features.

---

## 📧 Still Need Help?

**Can't find your answer?**

- 💭 **Community Help:** [GitHub Discussions](https://github.com/dragosgontariu/zonify/discussions)
- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/dragosgontariu/zonify/issues)
- 📧 **Direct Contact:** gontariudragos@gmail.com

---

**Last Updated:** January 2026
```

---