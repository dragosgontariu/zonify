"""
PDF Exporter for Zonify

Exports zonal statistics results to professional PDF format.

Author: Dragos Gontariu
License: GPL-3.0
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, A3, A2, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os
from ..utils.logger import Logger


class PDFExporter:
    """
    Export results to PDF format.
    """
    
    def __init__(self):
        """Constructor."""
        self.logger = Logger('PDFExporter')
    
    def export(self, output_layer, output_path, config):
        """
        Export layer to professional PDF with adaptive layout.
        
        Args:
            output_layer (QgsVectorLayer): Layer with results
            output_path (str): Base output path
            config (dict): Export configuration
            
        Returns:
            tuple: (success, output_file_path, error_message)
        """
        try:
            self.logger.info('Starting professional PDF export')
            
            # Determine output path
            pdf_path = output_path.replace('.gpkg', '.pdf')
            if pdf_path == output_path:
                pdf_path = output_path + '.pdf'
            
            # Get fields
            fields = output_layer.fields()
            field_names = [field.name() for field in fields]
            num_cols = len(field_names)
            
            # Adaptive page size based on columns
            if num_cols <= 6:
                pagesize = A4
                orientation = 'portrait'
            elif num_cols <= 10:
                pagesize = landscape(A4)
                orientation = 'landscape A4'
            elif num_cols <= 15:
                from reportlab.lib.pagesizes import A3
                pagesize = landscape(A3)
                orientation = 'landscape A3'
            else:
                from reportlab.lib.pagesizes import A2
                pagesize = landscape(A2)
                orientation = 'landscape A2'
            
            self.logger.info(f'Using {orientation} for {num_cols} columns')
            
            # Adaptive font size
            if num_cols <= 8:
                header_font = 9
                data_font = 8
            elif num_cols <= 12:
                header_font = 7
                data_font = 6
            else:
                header_font = 6
                data_font = 5.5
            
            # Create PDF
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=pagesize,
                rightMargin=0.3*inch,
                leftMargin=0.3*inch,
                topMargin=0.5*inch,
                bottomMargin=0.4*inch
            )
            
            # Build story
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#2563eb'),
                spaceAfter=10,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#64748b'),
                spaceAfter=20,
                alignment=TA_CENTER
            )
            
            # Title
            story.append(Paragraph('Zonify - Zonal Statistics Report', title_style))
            story.append(Paragraph(
                f'Generated on {datetime.now().strftime("%B %d, %Y at %H:%M")}',
                subtitle_style
            ))
            
            # === SUMMARY SECTION ===
            story.append(Paragraph('Executive Summary', styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            # Calculate summary statistics
            total_features = output_layer.featureCount()

            # Find ALL coverage fields (if coverage was calculated)
            coverage_fields = [fn for fn in field_names if 'coverage_pct' in fn]

            # Use statistic fields (NOT coverage) to determine "has data"
            # Coverage can be 0.0 even when feature has no data, so it's not reliable
            stat_fields = [fn for fn in field_names if any(stat in fn for stat in ['_mean', '_sum', '_min', '_max'])]
            self.logger.info(f'Using {len(stat_fields)} statistic fields for "has data" calculation (excluding coverage)')

            # Also detect coverage fields for separate statistics
            coverage_fields = [fn for fn in field_names if 'coverage_pct' in fn]
            if coverage_fields:
                self.logger.info(f'Found {len(coverage_fields)} coverage fields: {coverage_fields}')

            # Count features with ANY VALID data (not NULL)
            features_with_data = 0
            for feature in output_layer.getFeatures():
                has_valid_data = False
                
                for field in stat_fields:
                    val = feature.attribute(field)
                    # Check for valid data: not None, not QVariant NULL, and is a number
                    if val is not None:
                        try:
                            # Try to convert to float - will fail for NULL
                            float_val = float(val)
                            # If we got here, it's a valid number
                            has_valid_data = True
                            break
                        except (ValueError, TypeError):
                            # NULL or invalid value
                            continue
                
                if has_valid_data:
                    features_with_data += 1

            coverage_rate = (features_with_data / total_features * 100) if total_features > 0 else 0

            # Get actual raster count from config or count unique raster prefixes
            rasters_processed = config.get('raster_count', 0)
            if rasters_processed == 0:
                # Count unique raster names from field names
                raster_names = set()
                for fn in field_names:
                    for stat in ['_mean', '_sum', '_min', '_max', '_coverage_pct']:
                        if stat in fn:
                            raster_name = fn.replace(stat, '')
                            raster_names.add(raster_name)
                            break
                rasters_processed = len(raster_names)

            summary_data = [
                [
                    Paragraph('<b>Metric</b>', styles['Normal']),
                    Paragraph('<b>Value</b>', styles['Normal'])
                ],
                ['Total Features', f'{total_features:,}'],
                ['Features with Data (any raster)', f'{features_with_data:,} ({coverage_rate:.1f}%)'],
                ['Features without Data', f'{total_features - features_with_data:,}'],
                ['Rasters Processed', str(rasters_processed)],
                ['Statistics Calculated', f"{len(config.get('statistics', []))} metrics: {', '.join(config.get('statistics', []))[:40]}..."],
                ['Processing Time', f"{config.get('elapsed_time', 0):.1f} seconds"],
            ]

            # Add coverage statistics ONLY if coverage was calculated
            if coverage_fields:
                # For each raster, calculate separately
                raster_stats = {}
                
                for cov_field in coverage_fields:
                    raster_name = cov_field.replace('_coverage_pct', '')
                    
                    raster_with_data = 0
                    raster_coverage_values = []
                    raster_all_coverage = []
                    
                    for feature in output_layer.getFeatures():
                        cov = feature.attribute(cov_field)
                        
                        if cov is not None:
                            raster_all_coverage.append(cov)
                            
                            if cov > 0:
                                raster_with_data += 1
                                raster_coverage_values.append(cov)
                    
                    # Calculate averages
                    avg_with_data = sum(raster_coverage_values) / len(raster_coverage_values) if raster_coverage_values else 0
                    avg_all = sum(raster_all_coverage) / len(raster_all_coverage) if raster_all_coverage else 0
                    
                    raster_stats[raster_name] = {
                        'features_with_data': raster_with_data,
                        'avg_coverage_with_data': avg_with_data,
                        'avg_coverage_all': avg_all,
                        'coverage_rate': (raster_with_data / total_features * 100) if total_features > 0 else 0
                    }
                
                # Add separator and coverage stats
                summary_data.append(['', ''])
                summary_data.append([
                    Paragraph('<b>Coverage Statistics (per raster)</b>', styles['Normal']),
                    ''
                ])
                
                # Add per-raster stats
                for raster_name, stats in raster_stats.items():
                    summary_data.append([f'  {raster_name[:30]}...', ''])
                    summary_data.append([f'    Features with data', f"{stats['features_with_data']:,} ({stats['coverage_rate']:.1f}%)"])
                    summary_data.append([f'    Avg coverage (all)', f"{stats['avg_coverage_all']:.2f}%"])
                    summary_data.append([f'    Avg coverage (with data)', f"{stats['avg_coverage_with_data']:.2f}%"])
            
            summary_table = Table(summary_data, colWidths=[2.5*inch, 3*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 0.3*inch))
            
            # === DATA TABLE SECTION ===
            story.append(Paragraph('Detailed Results', styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            # Note about data
            max_rows_per_page = 50
            total_pages = (total_features + max_rows_per_page - 1) // max_rows_per_page
            
            if total_features > max_rows_per_page:
                story.append(Paragraph(
                    f'<i>Note: Showing results in batches of {max_rows_per_page} features across {total_pages} pages. '
                    f'Total: {total_features:,} features.</i>',
                    styles['Normal']
                ))
                story.append(Spacer(1, 0.1*inch))
            
            # Calculate column widths
            page_width = pagesize[0] - (0.6*inch)  # Total width minus margins
            col_width = page_width / num_cols
            
            # Build data in chunks
            chunk_size = max_rows_per_page
            all_features = list(output_layer.getFeatures())
            
            for chunk_idx in range(0, len(all_features), chunk_size):
                chunk_features = all_features[chunk_idx:chunk_idx + chunk_size]
                
                # Header row with word wrap
                header_row = [Paragraph(f'<b>{name}</b>', ParagraphStyle(
                    'TableHeader',
                    parent=styles['Normal'],
                    fontSize=header_font,
                    alignment=TA_CENTER,
                    textColor=colors.white
                )) for name in field_names]
                
                data_table = [header_row]
                
                # Data rows
                for feature in chunk_features:
                    row = []
                    for field_name in field_names:
                        value = feature[field_name]
                        
                        if value is None:
                            cell_text = '<font color="#94a3b8">NULL</font>'
                        elif isinstance(value, float):
                            cell_text = f'{value:.2f}'
                        else:
                            cell_text = str(value)[:50]  # Truncate long text
                        
                        cell = Paragraph(cell_text, ParagraphStyle(
                            'TableCell',
                            parent=styles['Normal'],
                            fontSize=data_font,
                            alignment=TA_CENTER
                        ))
                        row.append(cell)
                    
                    data_table.append(row)
                
                # Create table
                data_table_obj = Table(data_table, colWidths=[col_width] * num_cols, repeatRows=1)
                data_table_obj.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
                ]))
                
                story.append(data_table_obj)
                
                # Page break between chunks (except last)
                if chunk_idx + chunk_size < len(all_features):
                    story.append(PageBreak())
                    story.append(Paragraph(
                        f'Detailed Results (continued) - Features {chunk_idx + chunk_size + 1} to {min(chunk_idx + 2*chunk_size, len(all_features))}',
                        styles['Heading2']
                    ))
                    story.append(Spacer(1, 0.1*inch))
            
            # Footer
            story.append(Spacer(1, 0.2*inch))
            footer = Paragraph(
                '<b>Zonify</b> - Advanced Zonal Statistics for QGIS | '
                f'Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                ParagraphStyle(
                    'Footer',
                    parent=styles['Normal'],
                    fontSize=7,
                    textColor=colors.HexColor('#64748b'),
                    alignment=TA_CENTER
                )
            )
            story.append(footer)
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f'Professional PDF export completed: {pdf_path}')
            return True, pdf_path, ''
            
        except Exception as e:
            self.logger.error(f'PDF export failed: {str(e)}')
            import traceback
            self.logger.error(traceback.format_exc())
            return False, '', str(e)