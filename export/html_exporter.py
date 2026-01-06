"""
Zonify HTML Dashboard Exporter - Dark Mode Edition

Modern dark-themed dashboard with side menu, toggle themes, and glassmorphism.
Adaptive visualizations with rainbow gradients for all selected statistics.

Author: Dragos Gontariu
License: GPL-3.0
"""

from datetime import datetime
import json
from ..utils.logger import Logger


class HTMLExporter:
    """
    Export zonal statistics to modern interactive HTML dashboard.
    """
    
    def __init__(self):
        """Constructor."""
        self.logger = Logger('HTMLExporter')
    
    def export(self, output_layer, output_path, config):
        """
        Export layer to interactive HTML dashboard.
        
        Args:
            output_layer (QgsVectorLayer): Layer with results
            output_path (str): Base output path
            config (dict): Export configuration
            
        Returns:
            tuple: (success, output_file_path, error_message)
        """
        try:
            self.logger.info('Starting HTML dashboard export')
            
            # Determine output path
            html_path = output_path.replace('.gpkg', '.html')
            if html_path == output_path:
                html_path = output_path + '.html'
            
            # Collect all data from layer
            data = self._collect_data(output_layer, config)
            
            # Generate HTML content
            html_content = self._generate_html_dashboard(data)
            
            # Write to file
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f'HTML dashboard exported: {html_path}')
            return True, html_path, ''
            
        except Exception as e:
            self.logger.error(f'HTML export failed: {str(e)}')
            import traceback
            self.logger.error(traceback.format_exc())
            return False, '', str(e)
    
    def _collect_data(self, output_layer, config):
        """
        Collect all data from output layer.
        
        Returns:
            dict: Comprehensive data structure
        """
        fields = output_layer.fields()
        field_names = [field.name() for field in fields]
        
        # Identify field types
        coverage_fields = [fn for fn in field_names if 'coverage_pct' in fn]
        stat_fields = [fn for fn in field_names if any(stat in fn for stat in 
                    ['_mean', '_sum', '_min', '_max', '_median', '_mode', 
                    '_minority', '_variety', '_count', '_range', '_stddev', 
                    '_variance', '_cv', '_p10', '_p25', '_p50', '_p75', '_p90', '_p95'])]
        
        # Extract raster names - check stat is at END of field name
        raster_names = set()
        for fn in stat_fields + coverage_fields:
            for stat in ['_coverage_pct', '_minority', '_variance', '_stddev', '_variety',
                        '_median', '_mean', '_sum', '_min', '_max', '_mode', 
                        '_count', '_range', '_cv', '_p10', '_p25', '_p50', '_p75', '_p90', '_p95']:
                if fn.endswith(stat):
                    raster_name = fn[:-len(stat)]
                    raster_names.add(raster_name)
                    break
        
        # Collect feature data
        features_data = []
        raster_data = {raster: {} for raster in raster_names}
        
        for feature in output_layer.getFeatures():
            feature_dict = {'fid': feature.id()}
            
            # Collect all field values
            for field_name in field_names:
                val = feature.attribute(field_name)
                feature_dict[field_name] = val
                
                # Organize by raster
                for raster_name in raster_names:
                    if field_name.startswith(raster_name + '_'):
                        stat_type = field_name[len(raster_name)+1:]
                        if stat_type not in raster_data[raster_name]:
                            raster_data[raster_name][stat_type] = []
                        raster_data[raster_name][stat_type].append(val)
            
            features_data.append(feature_dict)
        
        # Calculate summary statistics - COVERAGE-AWARE
        total_features = len(features_data)
        features_with_data = 0
        features_not_analyzed = 0
        has_coverage = len(coverage_fields) > 0
        
        if has_coverage:
            # Count features with >0% coverage
            for feature in features_data:
                has_any_coverage = False
                for cov_field in coverage_fields:
                    val = feature.get(cov_field)
                    if val is not None:
                        try:
                            from qgis.PyQt.QtCore import QVariant
                            if isinstance(val, QVariant):
                                if val.isNull():
                                    continue
                                val = val.value()
                            
                            if float(val) > 0:
                                has_any_coverage = True
                                break
                        except (ValueError, TypeError):
                            pass
                
                if has_any_coverage:
                    features_with_data += 1
                else:
                    features_not_analyzed += 1
        else:
            # No coverage - count features with any non-NULL statistic
            statistics = config.get('statistics', [])
            first_stat = next((s for s in statistics if s != 'coverage_pct'), None)
            
            if first_stat:
                # Find fields ending with this stat
                first_stat_fields = [fn for fn in stat_fields if fn.endswith(f'_{first_stat}')]
                
                for feature in features_data:
                    has_any_stat = False
                    for stat_field in first_stat_fields:
                        val = feature.get(stat_field)
                        if val is not None:
                            try:
                                from qgis.PyQt.QtCore import QVariant
                                if isinstance(val, QVariant):
                                    if not val.isNull():
                                        has_any_stat = True
                                        break
                                else:
                                    has_any_stat = True
                                    break
                            except:
                                pass
                    
                    if has_any_stat:
                        features_with_data += 1
                    else:
                        features_not_analyzed += 1
            else:
                # Fallback - all features analyzed
                features_with_data = total_features
        
        # Compile data dictionary
        data = {
            'metadata': {
                'title': 'Zonify - Zonal Statistics Dashboard',
                'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'layer_name': output_layer.name(),
                'total_features': total_features,
                'features_with_data': features_with_data,
                'features_not_analyzed': features_not_analyzed,
                'features_without_data': total_features - features_with_data,
                'raster_count': len(raster_names),
                'raster_names': list(raster_names),
                'statistics': config.get('statistics', []),
                'elapsed_time': config.get('elapsed_time', 0)
            },
            'fields': field_names,
            'coverage_fields': coverage_fields,
            'stat_fields': stat_fields,
            'features': features_data,
            'raster_data': raster_data,
            'has_coverage': has_coverage
        }
        
        return data
    def _generate_html_dashboard(self, data):
        """
        Generate complete HTML dashboard with side menu.
        
        Args:
            data (dict): Collected data
            
        Returns:
            str: Complete HTML content
        """
        # Generate individual sections
        overview_html = self._generate_overview_section(data)
        coverage_html = self._generate_coverage_section(data) if data['has_coverage'] else ''
        statistics_html = self._generate_statistics_section(data)
        data_table_html = self._generate_data_section(data)
        
        # Determine which menu items to show
        menu_items = [
            {'id': 'overview', 'icon': self._get_svg_icon('overview'), 'label': 'Overview'},
        ]
        
        if data['has_coverage']:
            menu_items.append({'id': 'coverage', 'icon': self._get_svg_icon('coverage'), 'label': 'Coverage'})
        
        menu_items.append({'id': 'statistics', 'icon': self._get_svg_icon('statistics'), 'label': 'Statistics'})
        menu_items.append({'id': 'data', 'icon': self._get_svg_icon('data'), 'label': 'Data'})
        
        # Build menu HTML
        menu_html = []
        for i, item in enumerate(menu_items):
            active = 'active' if i == 0 else ''
            menu_html.append(f'''
                <div class="menu-item {active}" onclick="showSection('{item['id']}')" id="menu-{item['id']}">
                    {item['icon']}
                    <span>{item['label']}</span>
                </div>
            ''')
        
        # Build content sections
        sections_html = [
            f'<div id="overview-section" class="content-section active">{overview_html}</div>',
        ]
        
        if data['has_coverage']:
            sections_html.append(f'<div id="coverage-section" class="content-section">{coverage_html}</div>')
        
        sections_html.append(f'<div id="statistics-section" class="content-section">{statistics_html}</div>')
        sections_html.append(f'<div id="data-section" class="content-section">{data_table_html}</div>')
        
        # Get HTML template and populate
        template = self._get_html_template()
        
        html = template.replace('{{MENU_ITEMS}}', '\n'.join(menu_html))
        html = html.replace('{{CONTENT_SECTIONS}}', '\n'.join(sections_html))
        html = html.replace('{{METADATA}}', json.dumps(data['metadata']))
        
        return html
    
    def _generate_overview_section(self, data):
        """Generate Overview section content."""
        meta = data['metadata']
        has_coverage = data.get('has_coverage', False)
        
        # Calculate coverage rate
        coverage_rate = (meta['features_with_data'] / meta['total_features'] * 100) if meta['total_features'] > 0 else 0
        
        # Terminology based on coverage availability
        if has_coverage:
            data_label = "With Coverage"
            data_subtitle = f"{coverage_rate:.1f}% have >0% overlap"
            no_data_label = "Zero Coverage"
            no_data_subtitle = f"{meta['features_not_analyzed']:,} features (0% overlap)"
        else:
            data_label = "Analyzed"
            data_subtitle = f"{coverage_rate:.1f}% have statistics"
            no_data_label = "Not Analyzed"
            no_data_subtitle = f"{meta['features_not_analyzed']:,} features (NULL)"
        
        # KPI Cards with custom SVG icons
        kpi_html = f'''
        <div class="kpi-grid">
            <div class="kpi-card kpi-purple">
                {self._get_svg_icon('features')}
                <div class="kpi-value">{meta['total_features']:,}</div>
                <div class="kpi-label">Total Features</div>
            </div>
            <div class="kpi-card kpi-green">
                {self._get_svg_icon('check')}
                <div class="kpi-value">{meta['features_with_data']:,}</div>
                <div class="kpi-label">{data_label}</div>
                <div class="kpi-subtitle">{data_subtitle}</div>
            </div>
            <div class="kpi-card kpi-orange">
                {self._get_svg_icon('clock')}
                <div class="kpi-value">{meta['elapsed_time']:.1f}s</div>
                <div class="kpi-label">Processing Time</div>
            </div>
            <div class="kpi-card kpi-blue">
                {self._get_svg_icon('layers')}
                <div class="kpi-value">{meta['raster_count']}</div>
                <div class="kpi-label">Raster{"s" if meta['raster_count'] > 1 else ""}</div>
            </div>
        </div>
        '''
        
        # Key Insights
        insights = []
        
        if has_coverage:
            if coverage_rate > 75:
                insights.append(f'✅ Excellent coverage: {coverage_rate:.1f}% of features overlap with raster')
            elif coverage_rate > 50:
                insights.append(f'✓ Good coverage: {coverage_rate:.1f}% of features overlap with raster')
            elif coverage_rate > 25:
                insights.append(f'⚠️ Moderate coverage: {coverage_rate:.1f}% of features overlap with raster')
            else:
                insights.append(f'❌ Low coverage: only {coverage_rate:.1f}% of features overlap with raster')
        else:
            if coverage_rate > 75:
                insights.append(f'✅ Excellent: {coverage_rate:.1f}% of features have valid statistics')
            elif coverage_rate > 50:
                insights.append(f'✓ Good: {coverage_rate:.1f}% of features have valid statistics')
            else:
                insights.append(f'⚠️ Limited: only {coverage_rate:.1f}% of features have valid statistics')
        
        if meta['elapsed_time'] > 0:
            speed = meta['total_features'] / meta['elapsed_time']
            insights.append(f'⚡ Processing speed: {speed:.0f} features/second')
        
        if meta['raster_count'] > 1:
            insights.append(f'📊 Multi-raster analysis: {meta["raster_count"]} rasters processed')
        
        stat_count = len(meta['statistics'])
        insights.append(f'📈 {stat_count} statistical metric{"s" if stat_count > 1 else ""} calculated')
        
        if meta['features_not_analyzed'] > 0:
            pct_no_data = (meta['features_not_analyzed'] / meta['total_features'] * 100)
            if has_coverage:
                insights.append(f'ℹ️ {meta["features_not_analyzed"]:,} features ({pct_no_data:.1f}%) have zero coverage')
            else:
                insights.append(f'ℹ️ {meta["features_not_analyzed"]:,} features ({pct_no_data:.1f}%) not analyzed (NULL)')
        
        insights_html = '<div class="insights-card"><h3>🔍 Key Insights</h3><ul>'
        for insight in insights:
            insights_html += f'<li>{insight}</li>'
        insights_html += '</ul></div>'
        
        # Processing Summary
        summary_html = f'''
        <div class="summary-card">
            <h3>📋 Processing Summary</h3>
            <div class="summary-grid">
                <div class="summary-item">
                    <span class="summary-label">Polygon Layer</span>
                    <span class="summary-value">{meta['layer_name']}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Rasters</span>
                    <span class="summary-value">{", ".join(meta['raster_names'][:3])}{" ..." if len(meta['raster_names']) > 3 else ""}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Statistics</span>
                    <span class="summary-value">{", ".join(meta['statistics'][:5])}{" ..." if len(meta['statistics']) > 5 else ""}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Generated</span>
                    <span class="summary-value">{meta['generated']}</span>
                </div>
            </div>
        </div>
        '''
        
        return kpi_html + insights_html + summary_html
    
    def _generate_coverage_section(self, data):
        """Generate Coverage Analysis section - PER RASTER with side-by-side layout."""
        if not data['has_coverage']:
            return '<p class="empty-state">Coverage analysis not available</p>'
        
        coverage_fields = data['coverage_fields']
        
        if not coverage_fields:
            return '<p class="empty-state">No coverage data available</p>'
        
        # Group coverage by raster
        raster_coverage = {}
        
        for cov_field in coverage_fields:
            # Extract raster name from field name
            raster_name = cov_field.replace('_coverage_pct', '')
            
            # Collect values for this raster
            all_coverage = []
            all_coverage_including_zero = []
            
            for feature in data['features']:
                val = feature.get(cov_field)
                if val is not None:
                    try:
                        from qgis.PyQt.QtCore import QVariant
                        if isinstance(val, QVariant):
                            if val.isNull():
                                continue
                            val = val.value()
                        
                        float_val = float(val)
                        all_coverage_including_zero.append(float_val)
                        if float_val > 0:
                            all_coverage.append(float_val)
                    except (ValueError, TypeError):
                        pass
            
            raster_coverage[raster_name] = {
                'values': all_coverage,
                'all_values': all_coverage_including_zero
            }
        
        # Generate HTML for each raster
        sections_html = ''
        
        for raster_name, cov_data in raster_coverage.items():
            all_coverage = cov_data['values']
            all_coverage_including_zero = cov_data['all_values']
            
            if not all_coverage:
                continue
            
            # Generate histogram
            chart_id = f'coverage-chart-{raster_name}'.replace('_', '-')
            histogram_script = self._create_histogram_plotly(
                all_coverage,
                f'{raster_name} - Coverage Distribution',
                'Coverage (%)',
                'Number of Features',
                chart_id=chart_id,
                gradient=True
            )
            
            # Calculate statistics
            import numpy as np
            coverage_stats = {
                'min': np.min(all_coverage),
                'max': np.max(all_coverage),
                'mean': np.mean(all_coverage),
                'median': np.median(all_coverage),
                'std': np.std(all_coverage)
            }
            
            # Coverage breakdown with visual bars
            bins = [0, 20, 40, 60, 80, 100]
            labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
            colors = ['#ef4444', '#f59e0b', '#eab308', '#84cc16', '#10b981']
            counts = [sum(1 for c in all_coverage_including_zero if bins[i] <= c < bins[i+1]) for i in range(len(bins)-1)]
            counts[-1] += sum(1 for c in all_coverage_including_zero if c == 100)
            
            total = len(all_coverage_including_zero)
            max_count = max(counts) if counts else 1
            
            breakdown_html = '<div class="coverage-breakdown-visual">'
            breakdown_html += f'<h4>Coverage Distribution ({len(all_coverage_including_zero):,} total features)</h4>'
            
            for label, count, color in zip(labels, counts, colors):
                pct = (count / total * 100) if total > 0 else 0
                bar_width = (count / max_count * 100) if max_count > 0 else 0
                
                breakdown_html += f'''
                <div class="breakdown-row">
                    <span class="breakdown-label">{label}</span>
                    <div class="breakdown-bar-container">
                        <div class="breakdown-bar" style="width: {bar_width}%; background: {color};"></div>
                    </div>
                    <span class="breakdown-value">{count:,} ({pct:.1f}%)</span>
                </div>
                '''
            
            breakdown_html += '</div>'
            
            # Stats summary
            stats_html = f'''
            <div class="coverage-stats-summary">
                <h4>Coverage Statistics</h4>
                <div class="stats-grid-compact">
                    <div class="stat-item-compact"><span>Min</span><strong>{coverage_stats["min"]:.1f}%</strong></div>
                    <div class="stat-item-compact"><span>Max</span><strong>{coverage_stats["max"]:.1f}%</strong></div>
                    <div class="stat-item-compact"><span>Mean</span><strong>{coverage_stats["mean"]:.1f}%</strong></div>
                    <div class="stat-item-compact"><span>Median</span><strong>{coverage_stats["median"]:.1f}%</strong></div>
                    <div class="stat-item-compact"><span>Std Dev</span><strong>{coverage_stats["std"]:.1f}%</strong></div>
                </div>
            </div>
            '''
            
            # Combine in 2-column layout
            # Count features with >0% coverage
            count_with_coverage = len(all_coverage)
            count_zero_coverage = len(all_coverage_including_zero) - len(all_coverage)

            sections_html += f'''
            <div class="raster-section">
                <h3 class="raster-title">📊 {raster_name}</h3>
                <p class="section-note">
                    <strong>Coverage Analysis:</strong> {count_with_coverage:,} features ({count_with_coverage/len(all_coverage_including_zero)*100:.1f}%) have >0% overlap with raster. 
                    {count_zero_coverage:,} features have no overlap (0% coverage).
                </p>
                <div class="two-column-layout">
                    <div class="column-left">
                        <div id="{chart_id}" class="chart-plot"></div>
                    </div>
                    <div class="column-right">
                        {breakdown_html}
                        {stats_html}
                    </div>
                </div>
            </div>
            <script>{histogram_script}</script>
            '''
        
        if not sections_html:
            return '<p class="empty-state">No coverage data available</p>'
        
        return sections_html
    
    def _generate_statistics_section(self, data):
        """Generate Statistics section - PER RASTER with 2 charts per row."""
        selected_stats = data['metadata']['statistics']
        raster_data = data['raster_data']
        
        if not selected_stats:
            return '<p class="empty-state">No statistics selected</p>'
        
        # Remove coverage_pct from display (it has its own tab)
        display_stats = [s for s in selected_stats if s != 'coverage_pct']
        
        if not display_stats:
            return '<p class="empty-state">Only coverage selected - see Coverage tab</p>'
        # Add explanatory note - DUPĂ verificare!
        note_html = '''
        <div class="section-note">
            <strong>Note:</strong> Statistics are calculated for all features where data exists. 
            Use the Coverage tab to see which features overlap with rasters.
        </div>
        '''

        sections_html = note_html
        total_charts = 0
        
        # For each raster
        for raster_name, stats_dict in raster_data.items():
            charts_html = ''
            chart_scripts = []
            chart_count = 0
            
            # Collect valid charts for this raster
            valid_charts = []
            
            for stat in display_stats:
                # Check if this stat exists in data
                if stat not in stats_dict:
                    continue
                
                values = [v for v in stats_dict[stat] if v is not None]
                
                if not values:
                    continue
                
                try:
                    # Convert QVariant to Python native type first
                    from qgis.PyQt.QtCore import QVariant
                    
                    python_values = []
                    for v in values:
                        if isinstance(v, QVariant):
                            if v.isNull():
                                continue
                            v = v.value()
                        
                        try:
                            python_values.append(float(v))
                        except (ValueError, TypeError):
                            continue
                    
                    if not python_values:
                        continue
                    
                    valid_charts.append({
                        'stat': stat,
                        'values': python_values
                    })
                    
                except Exception as e:
                    continue
            
            if not valid_charts:
                continue
            
            # Determine initially shown charts
            if len(valid_charts) <= 4:
                initially_shown = len(valid_charts)
            else:
                initially_shown = 2
            
            # Generate charts in pairs (2 per row)
            for idx, chart_data in enumerate(valid_charts):
                stat = chart_data['stat']
                values = chart_data['values']
                
                chart_id = f'chart-{raster_name}-{stat}'.replace('_', '-')
                
                # Determine if shown or collapsed
                is_shown = idx < initially_shown
                display_style = 'block' if is_shown else 'none'
                
                # Generate chart
                chart_script = self._create_histogram_plotly(
                    values,
                    f'{stat.replace("_", " ").title()}',
                    stat.replace("_", " ").title(),
                    'Frequency',
                    chart_id=chart_id,
                    gradient=True
                )
                
                # Create chart card (will be arranged in grid)
                charts_html += f'''
                <div class="stat-chart-card" id="card-{chart_id}" style="display: {display_style};">
                    <div id="{chart_id}" class="chart-plot"></div>
                </div>
                '''
                
                chart_scripts.append(chart_script)
                chart_count += 1
            
            if chart_count == 0:
                continue
            
            total_charts += chart_count
            
            # Add expand/collapse buttons if more than 4 charts
            buttons_html = ''
            if chart_count > 4:
                buttons_html = f'''
                <div class="chart-controls">
                    <button onclick="expandRasterCharts('{raster_name}')" class="control-btn">
                        📈 Show All ({chart_count} charts)
                    </button>
                    <button onclick="collapseRasterCharts('{raster_name}')" class="control-btn">
                        📉 Show Less
                    </button>
                </div>
                '''
            
            # Combine for this raster
            sections_html += f'''
            <div class="raster-section" data-raster="{raster_name}">
                <h3 class="raster-title">📊 {raster_name}</h3>
                {buttons_html}
                <div class="stats-grid-2col">
                    {charts_html}
                </div>
            </div>
            <script>{" ".join(chart_scripts)}</script>
            '''
        
        if total_charts == 0:
            return '<p class="empty-state">No valid data for selected statistics</p>'
        
        # Add global expand/collapse if multiple rasters
        if len(raster_data) > 1:
            global_controls = f'''
            <div class="global-controls">
                <button onclick="expandAllCharts()" class="control-btn control-btn-primary">
                    📈 Expand All Rasters
                </button>
                <button onclick="collapseAllCharts()" class="control-btn">
                    📉 Collapse All
                </button>
            </div>
            '''
            sections_html = global_controls + sections_html
        
        return sections_html
    def _generate_data_section(self, data):
        """Generate Data section with searchable, paginated table."""
        features = data['features']
        
        if not features:
            return '<p class="empty-state">No data available</p>'
        
        # Get all field names
        all_fields = set()
        for feature in features:
            all_fields.update(feature.keys())
        
        # Sort fields: fid first, then alphabetically
        sorted_fields = ['fid'] if 'fid' in all_fields else []
        other_fields = sorted([f for f in all_fields if f != 'fid'])
        sorted_fields.extend(other_fields)
        
        # Build table header
        header_html = '<tr>' + ''.join(f'<th>{field}</th>' for field in sorted_fields) + '</tr>'
        
        # Build table rows (all data, pagination handled by JS)
        rows_html = ''
        for feature in features:
            row = '<tr>'
            for field in sorted_fields:
                value = feature.get(field, '')
                if value is None:
                    display_value = 'NULL'
                elif isinstance(value, float):
                    display_value = f'{value:.4f}'
                else:
                    display_value = str(value)
                row += f'<td>{display_value}</td>'
            row += '</tr>'
            rows_html += row
        
        # Pagination controls
        total_rows = len(features)
        
        pagination_html = f'''
        <div class="pagination-container">
            <div class="pagination-info">
                Showing <span id="pageStart">1</span>-<span id="pageEnd">100</span> of <span id="totalRows">{total_rows:,}</span> entries
            </div>
            <div class="pagination-controls">
                <button onclick="goToFirstPage()" id="firstPageBtn" class="page-btn">⏮️ First</button>
                <button onclick="previousPage()" id="prevPageBtn" class="page-btn">◀️ Previous</button>
                <span class="page-number">Page <span id="currentPage">1</span> of <span id="totalPages">1</span></span>
                <button onclick="nextPage()" id="nextPageBtn" class="page-btn">Next ▶️</button>
                <button onclick="goToLastPage()" id="lastPageBtn" class="page-btn">Last ⏭️</button>
            </div>
            <div class="rows-per-page">
                <label>Rows per page:</label>
                <select id="rowsPerPage" onchange="changeRowsPerPage()">
                    <option value="50">50</option>
                    <option value="100" selected>100</option>
                    <option value="250">250</option>
                    <option value="500">500</option>
                </select>
            </div>
        </div>
        '''
        
        table_html = f'''
        <div class="data-table-container">
            <div class="search-container">
                <input type="text" id="searchInput" placeholder="🔍 Search in table..." onkeyup="filterTable()">
            </div>
            
            {pagination_html}
            
            <div class="table-wrapper">
                <table id="dataTable" class="data-table">
                    <thead>
                        {header_html}
                    </thead>
                    <tbody id="tableBody">
                        {rows_html}
                    </tbody>
                </table>
            </div>
            
            {pagination_html}
        </div>
        '''
        
        return table_html
    
    def _create_histogram_plotly(self, values, title, xlabel, ylabel='Frequency', chart_id='chart', gradient=False):
        """Create Plotly histogram with optional rainbow gradient."""
        import numpy as np
        
        mean_val = np.mean(values)
        median_val = np.median(values)
        
        # Color scheme
        if gradient:
            marker_color = 'rgba(99, 102, 241, 0.8)'  # Purple-blue
            gradient_colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe']
        else:
            marker_color = '#4CAF50'
        
        plotly_code = f'''
        var data_{chart_id.replace("-", "_")} = [{{
            x: {json.dumps(values)},
            type: 'histogram',
            marker: {{
                color: '{marker_color}',
                line: {{color: 'rgba(255,255,255,0.2)', width: 1}}
            }},
            nbinsx: 30,
            hovertemplate: '<b>Range:</b> %{{x}}<br><b>Count:</b> %{{y}}<extra></extra>'
        }}];
        
        var layout_{chart_id.replace("-", "_")} = {{
            title: {{
                text: '{title}',
                font: {{color: 'var(--text-primary)', size: 16, family: 'Inter, sans-serif'}}
            }},
            xaxis: {{
                title: '{xlabel}',
                gridcolor: 'rgba(255,255,255,0.1)',
                color: 'var(--text-secondary)'
            }},
            yaxis: {{
                title: '{ylabel}',
                gridcolor: 'rgba(255,255,255,0.1)',
                color: 'var(--text-secondary)'
            }},
            plot_bgcolor: 'transparent',
            paper_bgcolor: 'transparent',
            shapes: [
                {{type: 'line', x0: {mean_val}, x1: {mean_val}, y0: 0, y1: 1, yref: 'paper',
                  line: {{color: '#ef4444', width: 2, dash: 'dash'}}}},
                {{type: 'line', x0: {median_val}, x1: {median_val}, y0: 0, y1: 1, yref: 'paper',
                  line: {{color: '#10b981', width: 2, dash: 'dash'}}}}
            ],
            annotations: [
                {{x: {mean_val}, y: 1.05, yref: 'paper', 
                  text: 'Mean: {mean_val:.2f}', showarrow: false, 
                  font: {{color: '#ef4444', size: 11}}}},
                {{x: {median_val}, y: 0.95, yref: 'paper',
                  text: 'Median: {median_val:.2f}', showarrow: false,
                  font: {{color: '#10b981', size: 11}}}}
            ],
            margin: {{t: 60, r: 20, b: 60, l: 60}},
            height: 400,
            font: {{family: 'Inter, sans-serif'}}
        }};
        
        var config_{chart_id.replace("-", "_")} = {{
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d']
        }};
        
        Plotly.newPlot('{chart_id}', data_{chart_id.replace("-", "_")}, layout_{chart_id.replace("-", "_")}, config_{chart_id.replace("-", "_")});
        '''
        
        return plotly_code
    
    def _get_svg_icon(self, icon_type):
        """Get custom SVG icons."""
        icons = {
            'overview': '''<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>''',
            'coverage': '''<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>
            </svg>''',
            'statistics': '''<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/>
                <line x1="6" y1="20" x2="6" y2="16"/>
            </svg>''',
            'data': '''<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
            </svg>''',
            'features': '''<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            </svg>''',
            'check': '''<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
            </svg>''',
            'clock': '''<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>''',
            'layers': '''<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/>
                <polyline points="2 12 12 17 22 12"/>
            </svg>'''
        }
        return icons.get(icon_type, icons['overview'])
    
    def _get_html_template(self):
        """Get complete HTML template with dark mode."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zonify Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0F172A;
            --bg-secondary: #1E293B;
            --bg-card: rgba(30, 41, 59, 0.6);
            --text-primary: #F1F5F9;
            --text-secondary: #94A3B8;
            --accent-purple: #8B5CF6;
            --accent-green: #10B981;
            --accent-orange: #F59E0B;
            --accent-blue: #3B82F6;
            --border-color: rgba(148, 163, 184, 0.1);
            --glow-purple: rgba(139, 92, 246, 0.3);
            --glow-green: rgba(16, 185, 129, 0.3);
        }
        
        [data-theme="light"] {
            --bg-primary: #F8FAFC;
            --bg-secondary: #FFFFFF;
            --bg-card: rgba(255, 255, 255, 0.8);
            --text-primary: #0F172A;
            --text-secondary: #64748B;
            --border-color: rgba(15, 23, 42, 0.1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            transition: all 0.3s ease;
        }
        
        .dashboard {
            display: flex;
            min-height: 100vh;
        }
        
        /* Header */
        .header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 70px;
            background: var(--bg-secondary);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 30px;
            z-index: 1000;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .theme-toggle {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 10px 20px;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .theme-toggle:hover {
            background: var(--accent-purple);
            color: white;
            box-shadow: 0 0 20px var(--glow-purple);
        }
        
        /* Sidebar */
        .sidebar {
            position: fixed;
            left: 0;
            top: 70px;
            bottom: 0;
            width: 240px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            padding: 30px 0;
        }
        
        .menu-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 30px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.3s ease;
            border-left: 3px solid transparent;
        }
        
        .menu-item:hover {
            background: var(--bg-card);
            color: var(--text-primary);
        }
        
        .menu-item.active {
            background: var(--bg-card);
            color: var(--accent-purple);
            border-left-color: var(--accent-purple);
            box-shadow: 0 0 20px var(--glow-purple);
        }
        
        .menu-item .icon {
            width: 20px;
            height: 20px;
        }
        
        /* Main Content */
        .main-content {
            margin-left: 240px;
            margin-top: 70px;
            padding: 30px;
            width: calc(100% - 240px);
        }
        
        .content-section {
            display: none;
            animation: fadeIn 0.3s ease;
        }
        
        .content-section.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* KPI Cards */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .kpi-card {
            background: var(--bg-card);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .kpi-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
        }
        
        .kpi-purple { border-top: 3px solid var(--accent-purple); }
        .kpi-green { border-top: 3px solid var(--accent-green); }
        .kpi-orange { border-top: 3px solid var(--accent-orange); }
        .kpi-blue { border-top: 3px solid var(--accent-blue); }
        
        .kpi-card .icon {
            width: 40px;
            height: 40px;
            margin-bottom: 12px;
            stroke: currentColor;
        }
        
        .kpi-value {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .kpi-label {
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        /* Cards */
        .insights-card, .summary-card, .stats-card, .chart-card {
            background: var(--bg-card);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
        }
        
        .insights-card h3, .summary-card h3, .stats-card h3 {
            font-size: 18px;
            margin-bottom: 16px;
            color: var(--text-primary);
        }
        
        .insights-card ul {
            list-style: none;
        }
        
        .insights-card li {
            padding: 10px 0;
            border-bottom: 1px solid var(--border-color);
        }
        
        .insights-card li:last-child {
            border-bottom: none;
        }
        
        /* Summary Grid */
        .summary-grid {
            display: grid;
            gap: 16px;
        }
        
        .summary-item {
            display: flex;
            justify-content: space-between;
            padding: 12px;
            background: rgba(139, 92, 246, 0.05);
            border-radius: 8px;
        }
        
        .summary-label {
            color: var(--text-secondary);
            font-weight: 500;
        }
        
        .summary-value {
            color: var(--text-primary);
            font-weight: 600;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
        }
        
        .stat-item {
            text-align: center;
            padding: 16px;
            background: rgba(139, 92, 246, 0.05);
            border-radius: 8px;
        }
        
        .stat-item span {
            display: block;
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }
        
        .stat-item strong {
            font-size: 20px;
            color: var(--accent-purple);
        }
        
        /* Chart Cards */
        .chart-card {
            margin-bottom: 16px;
        }
        
        .chart-header {
            cursor: pointer;
            user-select: none;
            display: flex;
            align-items: center;
            padding: 4px 0;
        }
        
        .chart-header h3 {
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .arrow {
            display: inline-block;
            transition: transform 0.3s ease;
            color: var(--accent-purple);
        }
        
        .chart-content {
            margin-top: 16px;
        }
        
        /* Table */
        .search-bar {
            margin-bottom: 20px;
        }
        
        .search-bar input {
            width: 100%;
            padding: 14px 20px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            color: var(--text-primary);
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        .search-bar input:focus {
            outline: none;
            border-color: var(--accent-purple);
            box-shadow: 0 0 0 3px var(--glow-purple);
        }
        
        .table-wrapper {
            overflow-x: auto;
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .data-table th {
            background: var(--accent-purple);
            color: white;
            padding: 14px;
            text-align: left;
            font-weight: 600;
            font-size: 13px;
            position: sticky;
            top: 0;
        }
        
        .data-table td {
            padding: 12px 14px;
            border-bottom: 1px solid var(--border-color);
            font-size: 13px;
        }
        
        .data-table tr:hover {
            background: rgba(139, 92, 246, 0.05);
        }
        
        .null-value {
            color: var(--text-secondary);
            font-style: italic;
        }
        
        .stats-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .stats-table th {
            background: var(--accent-green);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        
        .stats-table td {
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
            font-size: 16px;
        }
        /* Section notes and explanations */
        .section-note {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.6;
            margin: 12px 0;
            padding: 12px;
            background: rgba(139, 92, 246, 0.1);
            border-left: 3px solid var(--accent-purple);
            border-radius: 8px;
        }

        .section-note strong {
            color: var(--text-primary);
        }

        /* KPI subtitle */
        .kpi-subtitle {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 4px;
        }
        /* Pagination */
        .pagination-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0;
            flex-wrap: wrap;
            gap: 16px;
        }

        .pagination-info {
            font-size: 14px;
            color: var(--text-secondary);
        }

        .pagination-controls {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .page-btn {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 8px 16px;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 13px;
            transition: all 0.3s ease;
        }

        .page-btn:hover:not(:disabled) {
            background: var(--accent-purple);
            color: white;
            border-color: var(--accent-purple);
            transform: translateY(-2px);
        }

        .page-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }

        .page-number {
            font-size: 14px;
            color: var(--text-primary);
            font-weight: 600;
            padding: 0 12px;
        }

        .rows-per-page {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .rows-per-page label {
            font-size: 14px;
            color: var(--text-secondary);
        }

        .rows-per-page select {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 8px 12px;
            color: var(--text-primary);
            font-size: 13px;
            cursor: pointer;
        }

        @media (max-width: 768px) {
            .pagination-container {
                justify-content: center;
            }
            
            .pagination-info,
            .rows-per-page {
                width: 100%;
                text-align: center;
                justify-content: center;
            }
        }
        /* Raster Sections */
        .raster-section {
            background: var(--bg-card);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
        }

        .raster-title {
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--accent-purple);
        }

        /* Two Column Layout */
        .two-column-layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }

        .column-left, .column-right {
            min-width: 0;
        }

        /* Coverage Breakdown Visual */
        .coverage-breakdown-visual {
            background: rgba(139, 92, 246, 0.05);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }

        .coverage-breakdown-visual h4 {
            font-size: 16px;
            margin-bottom: 16px;
            color: var(--text-primary);
        }

        .breakdown-row {
            display: grid;
            grid-template-columns: 80px 1fr 120px;
            gap: 12px;
            align-items: center;
            margin-bottom: 12px;
        }

        .breakdown-label {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
        }

        .breakdown-bar-container {
            background: rgba(148, 163, 184, 0.1);
            border-radius: 6px;
            height: 24px;
            overflow: hidden;
        }

        .breakdown-bar {
            height: 100%;
            border-radius: 6px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            padding-left: 8px;
            color: white;
            font-size: 11px;
            font-weight: 600;
        }

        .breakdown-value {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-primary);
            text-align: right;
        }

        /* Coverage Stats Summary */
        .coverage-stats-summary {
            background: rgba(16, 185, 129, 0.05);
            border-radius: 12px;
            padding: 20px;
        }

        .coverage-stats-summary h4 {
            font-size: 16px;
            margin-bottom: 16px;
            color: var(--text-primary);
        }

        .stats-grid-compact {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 12px;
        }

        .stat-item-compact {
            text-align: center;
            padding: 12px;
            background: rgba(139, 92, 246, 0.05);
            border-radius: 8px;
        }

        .stat-item-compact span {
            display: block;
            font-size: 11px;
            color: var(--text-secondary);
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-item-compact strong {
            font-size: 18px;
            color: var(--accent-green);
        }

        /* Statistics Grid - 2 Columns */
        .stats-grid-2col {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }

        .stat-chart-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            min-height: 400px;
        }

        /* Chart Controls */
        .chart-controls, .global-controls {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            justify-content: center;
        }

        .global-controls {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 24px;
        }

        .control-btn {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 20px;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .control-btn:hover {
            background: var(--accent-purple);
            color: white;
            border-color: var(--accent-purple);
            transform: translateY(-2px);
        }

        .control-btn-primary {
            background: var(--accent-purple);
            color: white;
            border-color: var(--accent-purple);
        }

        .control-btn-primary:hover {
            background: #7c3aed;
        }

        /* Responsive */
        @media (max-width: 1024px) {
            .two-column-layout {
                grid-template-columns: 1fr;
            }
            
            .stats-grid-2col {
                grid-template-columns: 1fr;
            }
        }

    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <div class="logo">
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                    <rect width="32" height="32" rx="8" fill="url(#gradient)"/>
                    <defs>
                        <linearGradient id="gradient" x1="0" y1="0" x2="32" y2="32">
                            <stop offset="0%" stop-color="#667eea"/>
                            <stop offset="100%" stop-color="#764ba2"/>
                        </linearGradient>
                    </defs>
                </svg>
                Zonify Dashboard
            </div>
            <button class="theme-toggle" onclick="toggleTheme()">
                <span id="theme-icon">🌙</span>
                <span id="theme-text">Dark Mode</span>
            </button>
        </div>
        
        <div class="sidebar">
            {{MENU_ITEMS}}
        </div>
        
        <div class="main-content">
            {{CONTENT_SECTIONS}}
        </div>
    </div>
    
    <script>
        // Theme Toggle
        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            const icon = document.getElementById('theme-icon');
            const text = document.getElementById('theme-text');
            
            if (newTheme === 'light') {
                icon.textContent = '☀️';
                text.textContent = 'Light Mode';
            } else {
                icon.textContent = '🌙';
                text.textContent = 'Dark Mode';
            }
        }
        
        
        
        // Section Navigation
        function showSection(sectionId) {
            // Hide all sections
            const sections = document.querySelectorAll('.content-section');
            sections.forEach(s => s.classList.remove('active'));
            
            // Remove active from all menu items
            const menuItems = document.querySelectorAll('.menu-item');
            menuItems.forEach(m => m.classList.remove('active'));
            
            // Show selected section
            const section = document.getElementById(sectionId + '-section');
            if (section) {
                section.classList.add('active');
            }
            
            // Activate menu item
            const menuItem = document.getElementById('menu-' + sectionId);
            if (menuItem) {
                menuItem.classList.add('active');
            }
        }

        // Chart Toggle (for old collapsible style)
        function toggleChart(chartId) {
            const container = document.getElementById(chartId + '-container');
            const arrow = document.getElementById('arrow-' + chartId);
            
            if (container && arrow) {
                if (container.style.display === 'none') {
                    container.style.display = 'block';
                    arrow.textContent = '▼';
                } else {
                    container.style.display = 'none';
                    arrow.textContent = '▶';
                }
            }
        }

        // Expand/Collapse per Raster
        function expandRasterCharts(rasterName) {
            const rasterSection = document.querySelector(`[data-raster="${rasterName}"]`);
            if (!rasterSection) return;
            
            const cards = rasterSection.querySelectorAll('.stat-chart-card');
            cards.forEach(card => card.style.display = 'block');
        }

        function collapseRasterCharts(rasterName) {
            const rasterSection = document.querySelector(`[data-raster="${rasterName}"]`);
            if (!rasterSection) return;
            
            const cards = rasterSection.querySelectorAll('.stat-chart-card');
            cards.forEach((card, index) => {
                if (index >= 2) {
                    card.style.display = 'none';
                }
            });
        }

        // Global Expand/Collapse All
        function expandAllCharts() {
            // Expand all stat chart cards
            const allCards = document.querySelectorAll('.stat-chart-card');
            allCards.forEach(card => card.style.display = 'block');
            
            // Expand old-style chart containers (if any)
            const containers = document.querySelectorAll('.chart-content');
            const arrows = document.querySelectorAll('.arrow');
            containers.forEach(c => c.style.display = 'block');
            arrows.forEach(a => a.textContent = '▼');
        }

        function collapseAllCharts() {
            // Collapse stat chart cards (show only first 2 per raster)
            const allSections = document.querySelectorAll('[data-raster]');
            allSections.forEach(section => {
                const cards = section.querySelectorAll('.stat-chart-card');
                cards.forEach((card, index) => {
                    if (index >= 2) {
                        card.style.display = 'none';
                    }
                });
            });
            
            // Collapse old-style chart containers (if any)
            const containers = document.querySelectorAll('.chart-content');
            const arrows = document.querySelectorAll('.arrow');
            containers.forEach(c => c.style.display = 'none');
            arrows.forEach(a => a.textContent = '▶');
        }
        // Pagination 
        let currentPage = 1;
        let rowsPerPage = 100;
        let filteredRows = [];

        window.addEventListener('DOMContentLoaded', () => {
            const savedTheme = localStorage.getItem('theme') || 'dark';
            document.documentElement.setAttribute('data-theme', savedTheme);
            
            const icon = document.getElementById('theme-icon');
            const text = document.getElementById('theme-text');
            
            if (savedTheme === 'light') {
                icon.textContent = '☀️';
                text.textContent = 'Light Mode';
            }
            
            // Initialize pagination
            initPagination();
        });

        function initPagination() {
            const table = document.getElementById('dataTable');
            if (!table) return;
            
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            filteredRows = rows;
            currentPage = 1;
            
            updatePagination();
        }

        function updatePagination() {
            const table = document.getElementById('dataTable');
            if (!table) return;
            
            const tbody = table.querySelector('tbody');
            const allRows = Array.from(tbody.querySelectorAll('tr'));
            
            // CRITICAL: Hide ALL rows first (not just filteredRows)
            allRows.forEach(row => row.style.display = 'none');
            
            const totalRows = filteredRows.length;
            const totalPages = Math.ceil(totalRows / rowsPerPage);
            
            // Show only current page of filtered rows
            const startIdx = (currentPage - 1) * rowsPerPage;
            const endIdx = Math.min(startIdx + rowsPerPage, totalRows);
            
            for (let i = startIdx; i < endIdx; i++) {
                if (filteredRows[i]) {
                    filteredRows[i].style.display = '';
                }
            }
            
            // Update UI
            const pageStart = document.getElementById('pageStart');
            const pageEnd = document.getElementById('pageEnd');
            const totalRowsSpan = document.getElementById('totalRows');
            const currentPageSpan = document.getElementById('currentPage');
            const totalPagesSpan = document.getElementById('totalPages');
            
            if (pageStart) pageStart.textContent = totalRows > 0 ? (startIdx + 1).toLocaleString() : '0';
            if (pageEnd) pageEnd.textContent = endIdx.toLocaleString();
            if (totalRowsSpan) totalRowsSpan.textContent = totalRows.toLocaleString();
            if (currentPageSpan) currentPageSpan.textContent = currentPage;
            if (totalPagesSpan) totalPagesSpan.textContent = totalPages || 1;
            
            // Update button states
            const firstBtn = document.getElementById('firstPageBtn');
            const prevBtn = document.getElementById('prevPageBtn');
            const nextBtn = document.getElementById('nextPageBtn');
            const lastBtn = document.getElementById('lastPageBtn');
            
            if (firstBtn) firstBtn.disabled = currentPage === 1;
            if (prevBtn) prevBtn.disabled = currentPage === 1;
            if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
            if (lastBtn) lastBtn.disabled = currentPage >= totalPages;
        }

        function nextPage() {
            const totalPages = Math.ceil(filteredRows.length / rowsPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                updatePagination();
            }
        }

        function previousPage() {
            if (currentPage > 1) {
                currentPage--;
                updatePagination();
            }
        }

        function goToFirstPage() {
            currentPage = 1;
            updatePagination();
        }

        function goToLastPage() {
            const totalPages = Math.ceil(filteredRows.length / rowsPerPage);
            currentPage = totalPages;
            updatePagination();
        }

        function changeRowsPerPage() {
            rowsPerPage = parseInt(document.getElementById('rowsPerPage').value);
            currentPage = 1;
            updatePagination();
        }

        function filterTable() {
            const input = document.getElementById('searchInput');
            if (!input) return;
            
            const filter = input.value.toUpperCase();
            const table = document.getElementById('dataTable');
            if (!table) return;
            
            const tbody = table.querySelector('tbody');
            const allRows = Array.from(tbody.querySelectorAll('tr'));
            
            // Filter rows based on search
            if (filter === '') {
                // No filter - show all rows
                filteredRows = allRows;
            } else {
                // Filter based on search term
                filteredRows = allRows.filter(row => {
                    const text = row.textContent || row.innerText;
                    return text.toUpperCase().indexOf(filter) > -1;
                });
            }
            
            // Reset to first page
            currentPage = 1;
            updatePagination();
        }
        </script>
        </body>
        </html>
        '''