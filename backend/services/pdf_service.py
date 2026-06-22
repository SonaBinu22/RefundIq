"""
PDF Fraud Report Generator (Feature 14)
Generates downloadable PDF reports using ReportLab.
"""
import io
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, HRFlowable)
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_refund_report(refund: dict, explanation: dict, timeline: list, similarity: dict = None) -> bytes:
    if not REPORTLAB_AVAILABLE:
        return b'PDF generation unavailable. Install reportlab.'

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             topMargin=1.5*cm, bottomMargin=1.5*cm,
                             leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle('header', fontSize=20, textColor=colors.HexColor('#1a1a2e'),
                                   spaceAfter=4, fontName='Helvetica-Bold')
    sub_style = ParagraphStyle('sub', fontSize=11, textColor=colors.grey, spaceAfter=16)
    story.append(Paragraph('RefundIQ+ Fraud Analysis Report', header_style))
    story.append(Paragraph(f'Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}', sub_style))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e0e0e0')))
    story.append(Spacer(1, 0.4*cm))

    # Risk Score Banner
    risk_score = explanation.get('risk_score', 0) if explanation else refund.get('risk_score', 0)
    risk_level = explanation.get('risk_level', '') if explanation else refund.get('risk_level', '')
    risk_color = colors.HexColor('#e74c3c') if 'High' in risk_level else \
                 colors.HexColor('#f39c12') if 'Medium' in risk_level else \
                 colors.HexColor('#27ae60')

    risk_table = Table([[f'Risk Score: {risk_score}/100', f'Level: {risk_level}']],
                        colWidths=[8*cm, 8*cm])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), risk_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 13),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [risk_color]),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 0.5*cm))

    # Refund Details
    story.append(Paragraph('Refund Details', styles['Heading2']))
    details = [
        ['Refund ID', f"#{refund.get('refund_id', '—')}"],
        ['Customer', refund.get('user_name', '—')],
        ['Email', refund.get('user_email', '—')],
        ['Product', refund.get('product_name', '—')],
        ['Order ID', refund.get('order_id', '—')],
        ['Amount', f"₹{refund.get('refund_amount', '—')}"],
        ['Reason', refund.get('refund_reason', '—')],
        ['Status', refund.get('status', '—').replace('_', ' ').title()],
        ['Submitted', refund.get('created_at', '—')[:10] if refund.get('created_at') else '—'],
    ]
    t = Table(details, colWidths=[5*cm, 11*cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f8f9fa'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # AI Narrative
    if explanation and explanation.get('narrative'):
        story.append(Paragraph('AI Fraud Analysis Narrative', styles['Heading2']))
        narrative_style = ParagraphStyle('narrative', fontSize=10, leading=16,
                                          textColor=colors.HexColor('#333333'),
                                          backColor=colors.HexColor('#f0f4ff'),
                                          borderPadding=(8, 8, 8, 8))
        story.append(Paragraph(explanation['narrative'], styles['Normal']))
        story.append(Spacer(1, 0.4*cm))

    # Risk Factors
    if explanation and explanation.get('factors'):
        story.append(Paragraph('Risk Factors', styles['Heading2']))
        for f in explanation['factors']:
            impact_color = colors.HexColor('#e74c3c') if 'High' in f.get('impact', '') else \
                           colors.HexColor('#f39c12') if 'Medium' in f.get('impact', '') else \
                           colors.HexColor('#27ae60')
            row = Table([[Paragraph(f"• {f['description']}", styles['Normal']),
                          Paragraph(f['impact'], styles['Normal'])]],
                         colWidths=[13*cm, 4*cm])
            row.setStyle(TableStyle([
                ('TEXTCOLOR', (1, 0), (1, 0), impact_color),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(row)
        story.append(Spacer(1, 0.4*cm))

    # Similarity
    if similarity and similarity.get('flagged'):
        story.append(Paragraph('Duplicate Detection Alert', styles['Heading2']))
        story.append(Paragraph(
            f"Similarity Score: {similarity['similarity_score']} — "
            f"Matched Refund: #{similarity.get('matched_refund_id', '—')} — "
            f"Fraud Probability: {similarity['fraud_probability']}",
            styles['Normal']
        ))
        story.append(Spacer(1, 0.4*cm))

    # Timeline
    if timeline:
        story.append(Paragraph('Refund Timeline', styles['Heading2']))
        for event in timeline:
            ts = event.get('created_at', '')[:16].replace('T', ' ')
            story.append(Paragraph(
                f"<b>{ts}</b> — {event['event']}" +
                (f": {event['detail']}" if event.get('detail') else ''),
                styles['Normal']
            ))
        story.append(Spacer(1, 0.4*cm))

    # Recommendations
    if explanation and explanation.get('recommendations'):
        story.append(Paragraph('Recommendations', styles['Heading2']))
        for rec in explanation['recommendations']:
            story.append(Paragraph(f'• {rec}', styles['Normal']))

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.grey))
    story.append(Paragraph('Confidential — RefundIQ+ Automated Report', styles['Normal']))

    doc.build(story)
    return buf.getvalue()
