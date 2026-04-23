import io
import re
from collections import defaultdict
from datetime import date

from django.utils.html import escape
from django.utils.timezone import now

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except Exception:  # pragma: no cover - graceful fallback when reportlab is unavailable
    colors = None
    A4 = None
    getSampleStyleSheet = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None


SEVERITY_COLORS = {
    'critical': '#B91C1C',
    'high': '#DC2626',
    'medium': '#D97706',
    'low': '#2563EB',
    'info': '#0F766E',
}

SEVERITY_TEXT_COLORS = {
    'critical': '#FEE2E2',
    'high': '#FEE2E2',
    'medium': '#FEF3C7',
    'low': '#DBEAFE',
    'info': '#CCFBF1',
}

SEVERITY_ORDER = {
    'critical': 0,
    'high': 1,
    'medium': 2,
    'low': 3,
    'info': 4,
}


def build_executive_report_payload(scan, report_type='executive'):
    findings = list(scan.findings.all())
    formatted_findings = [_format_finding(finding) for finding in findings]

    severity_counts = {
        'critical': scan.critical_count,
        'high': scan.high_count,
        'medium': scan.medium_count,
        'low': scan.low_count,
        'info': scan.info_count,
    }

    by_function = defaultdict(list)
    for item in formatted_findings:
        by_function[item['function']].append(item)

    recommendations = []
    for item in formatted_findings:
        recommendations.append(
            {
                'issue': item['title'],
                'severity': item['severity_level'],
                'action': item['recommendation'] or _default_recommendation(item['severity_level']),
            }
        )

    return {
        'report_type': report_type,
        'generated_at': now().isoformat(),
        'audit_date': date.today().strftime('%d-%b-%Y'),
        'scanner_used': 'Slither',
        'scan': {
            'id': scan.id,
            'contract_name': scan.contract_name or 'UnnamedContract.sol',
            'status': scan.status,
            'created_at': scan.created_at.isoformat() if scan.created_at else None,
            'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
            'solidity_version': scan.solidity_version.version if scan.solidity_version else 'Unknown',
        },
        'summary': {
            'severity_levels': severity_counts,
            'total_vulnerabilities': scan.total_findings,
            'overall_risk_level': _overall_risk_label(severity_counts),
            'summary_text': _summary_text(scan.contract_name or 'contract', severity_counts),
        },
        'vulnerabilities': sorted(
            formatted_findings,
            key=lambda item: (SEVERITY_ORDER.get(item['severity_level'], 99), item['title']),
        ),
        'function_breakdown': dict(by_function),
        'recommendations_summary': recommendations,
    }


def render_executive_report_html(report_data):
    severity_rows = []
    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        count = report_data['summary']['severity_levels'][severity]
        note = _severity_note(severity, count)
        severity_rows.append(
            f"<tr><td><span class='pill sev-{severity}'>{severity.upper()}</span></td>"
            f"<td>{count}</td><td>{escape(note)}</td></tr>"
        )

    vulnerabilities = report_data['vulnerabilities']
    high_risk_html = _render_findings_html(vulnerabilities, {'critical', 'high'})
    medium_low_html = _render_findings_html(vulnerabilities, {'medium', 'low'})
    info_html = _render_findings_html(vulnerabilities, {'info'})

    recommendation_rows = []
    for rec in report_data['recommendations_summary']:
        recommendation_rows.append(
            "<tr>"
            f"<td>{escape(rec['issue'])}</td>"
            f"<td><span class='pill sev-{rec['severity']}'>{rec['severity'].upper()}</span></td>"
            f"<td>{escape(rec['action'])}</td>"
            "</tr>"
        )

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>Security Audit Report</title>
  <style>
    :root {{
      --paper: #f8fafc;
      --ink: #0f172a;
      --accent: #1e3a8a;
      --line: #d1d5db;
      --critical: {SEVERITY_COLORS['critical']};
      --high: {SEVERITY_COLORS['high']};
      --medium: {SEVERITY_COLORS['medium']};
      --low: {SEVERITY_COLORS['low']};
      --info: {SEVERITY_COLORS['info']};
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: linear-gradient(120deg,#e2e8f0,#f8fafc 35%,#e0f2fe); color: var(--ink); font-family: Georgia, 'Times New Roman', serif; }}
    .page {{ width: 960px; margin: 24px auto; background: white; border: 1px solid var(--line); border-radius: 12px; box-shadow: 0 12px 30px rgba(15, 23, 42, 0.10); padding: 28px; }}
    h1,h2,h3 {{ margin: 0 0 10px; }}
    h1 {{ font-size: 30px; letter-spacing: .2px; color: var(--accent); }}
    h2 {{ font-size: 20px; margin-top: 20px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; }}
    h3 {{ font-size: 16px; margin-top: 14px; }}
    p, li {{ font-size: 14px; line-height: 1.6; }}
    .meta {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 8px 0 16px; }}
    .meta-card {{ background: var(--paper); border: 1px solid var(--line); border-radius: 10px; padding: 10px; font-size: 13px; }}
    .risk {{ font-weight: 700; padding: 8px 10px; border-left: 4px solid #b45309; background: #fff7ed; margin: 12px 0; }}
    .pill {{ font-size: 11px; font-weight: 700; border-radius: 999px; padding: 4px 8px; display: inline-block; letter-spacing: .2px; }}
    .sev-critical {{ background: {SEVERITY_COLORS['critical']}; color: {SEVERITY_TEXT_COLORS['critical']}; }}
    .sev-high {{ background: {SEVERITY_COLORS['high']}; color: {SEVERITY_TEXT_COLORS['high']}; }}
    .sev-medium {{ background: {SEVERITY_COLORS['medium']}; color: {SEVERITY_TEXT_COLORS['medium']}; }}
    .sev-low {{ background: {SEVERITY_COLORS['low']}; color: {SEVERITY_TEXT_COLORS['low']}; }}
    .sev-info {{ background: {SEVERITY_COLORS['info']}; color: {SEVERITY_TEXT_COLORS['info']}; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
    th, td {{ border: 1px solid var(--line); text-align: left; padding: 8px; vertical-align: top; font-size: 13px; }}
    th {{ background: #f1f5f9; }}
    .finding {{ border: 1px solid var(--line); border-left-width: 5px; border-radius: 8px; padding: 10px 12px; margin: 10px 0; background: #fcfcfd; }}
    .finding-critical {{ border-left-color: var(--critical); }}
    .finding-high {{ border-left-color: var(--high); }}
    .finding-medium {{ border-left-color: var(--medium); }}
    .finding-low {{ border-left-color: var(--low); }}
    .finding-info {{ border-left-color: var(--info); }}
    @media print {{ body {{ background: #fff; }} .page {{ box-shadow: none; border-radius: 0; margin: 0; width: auto; }} }}
    @media (max-width: 990px) {{ .page {{ width: auto; margin: 8px; padding: 18px; }} .meta {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class=\"page\">
    <h1>Smart Contract Security Audit - {escape(report_data['scan']['contract_name'])}</h1>
    <div class=\"meta\">
      <div class=\"meta-card\"><strong>Audit Date:</strong><br/>{escape(report_data['audit_date'])}</div>
      <div class=\"meta-card\"><strong>Scanner Used:</strong><br/>{escape(report_data['scanner_used'])}</div>
      <div class=\"meta-card\"><strong>Solidity Version:</strong><br/>{escape(report_data['scan']['solidity_version'])}</div>
    </div>

    <h2>1. Executive Summary</h2>
    <p>{escape(report_data['summary']['summary_text'])}</p>
    <table>
      <thead><tr><th>Severity</th><th>Count</th><th>Notes</th></tr></thead>
      <tbody>
        {''.join(severity_rows)}
      </tbody>
    </table>
    <div class=\"risk\">Overall Risk Level: {escape(report_data['summary']['overall_risk_level'])}</div>

    <h2>2. High-Risk Issues</h2>
    {high_risk_html}

    <h2>3. Medium/Low-Risk Issues</h2>
    {medium_low_html}

    <h2>4. Informational Notices</h2>
    {info_html}

    <h2>5. Recommendations Summary</h2>
    <table>
      <thead><tr><th>Issue</th><th>Severity</th><th>Action</th></tr></thead>
      <tbody>{''.join(recommendation_rows)}</tbody>
    </table>
  </div>
</body>
</html>
"""


def render_executive_report_pdf(report_data):
    if not all([colors, A4, getSampleStyleSheet, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle]):
        raise RuntimeError('PDF generation dependency is unavailable. Install reportlab to enable PDF exports.')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Smart Contract Security Audit - {escape(report_data['scan']['contract_name'])}", styles['Title']))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Audit Date: {report_data['audit_date']}", styles['Normal']))
    story.append(Paragraph(f"Scanner Used: {report_data['scanner_used']}", styles['Normal']))
    story.append(Paragraph(f"Solidity Version: {report_data['scan']['solidity_version']}", styles['Normal']))
    story.append(Spacer(1, 10))

    story.append(Paragraph('1. Executive Summary', styles['Heading2']))
    story.append(Paragraph(escape(report_data['summary']['summary_text']), styles['BodyText']))

    summary_table_data = [['Severity', 'Count', 'Notes']]
    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        summary_table_data.append([
            severity.upper(),
            str(report_data['summary']['severity_levels'][severity]),
            _severity_note(severity, report_data['summary']['severity_levels'][severity]),
        ])

    summary_table = Table(summary_table_data, colWidths=[90, 60, 360])
    summary_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]
    for idx, severity in enumerate(['critical', 'high', 'medium', 'low', 'info'], start=1):
        summary_style.append(('TEXTCOLOR', (0, idx), (0, idx), colors.HexColor(SEVERITY_COLORS[severity])))
        summary_style.append(('FONTNAME', (0, idx), (0, idx), 'Helvetica-Bold'))
    summary_table.setStyle(TableStyle(summary_style))
    story.append(summary_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Overall Risk Level: {escape(report_data['summary']['overall_risk_level'])}", styles['BodyText']))
    story.append(Spacer(1, 12))

    for heading, levels in [
        ('2. High-Risk Issues', {'critical', 'high'}),
        ('3. Medium/Low-Risk Issues', {'medium', 'low'}),
        ('4. Informational Notices', {'info'}),
    ]:
        story.append(Paragraph(heading, styles['Heading2']))
        section = [item for item in report_data['vulnerabilities'] if item['severity_level'] in levels]
        if not section:
            story.append(Paragraph('No findings in this section.', styles['BodyText']))
            continue
        for item in section:
            story.append(Paragraph(f"{item['title']} [{item['severity_level'].upper()}]", styles['Heading4']))
            story.append(Paragraph(f"Function: {item['function']}", styles['BodyText']))
            story.append(Paragraph(f"Lines: {item['lines']}", styles['BodyText']))
            story.append(Paragraph(f"Description: {escape(item['description'])}", styles['BodyText']))
            story.append(Paragraph(f"Recommendation: {escape(item['recommendation'])}", styles['BodyText']))
            story.append(Spacer(1, 6))

    story.append(Paragraph('5. Recommendations Summary', styles['Heading2']))
    rec_table_data = [['Issue', 'Severity', 'Action']]
    for rec in report_data['recommendations_summary']:
        rec_table_data.append([rec['issue'], rec['severity'].upper(), rec['action']])
    rec_table = Table(rec_table_data, colWidths=[180, 70, 260])
    rec_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )
    story.append(rec_table)

    doc.build(story)
    return buffer.getvalue()


def _format_finding(finding):
    severity = (finding.severity or 'info').lower()
    recommendation = _plain_text(finding.recommendation) or _default_recommendation(severity)
    function_name = _extract_function_name(finding)
    lines = _format_lines(finding)
    return {
        'id': finding.id,
        'swc_id': finding.swc_id,
        'title': finding.title,
        'severity_level': severity,
        'description': _plain_text(finding.description),
        'recommendation': recommendation,
        'line_number': finding.line_number,
        'line_start': finding.line_start,
        'line_end': finding.line_end,
        'lines': lines,
        'function': function_name,
        'status': finding.status,
        'reference_url': finding.reference_url,
        'code_snippet': finding.code_snippet,
    }


def _extract_function_name(finding):
    metadata = finding.metadata or {}
    for key in ('function', 'function_name', 'signature', 'element_name'):
        value = metadata.get(key)
        if value:
            return str(value)

    if finding.code_snippet and '(' in finding.code_snippet and ')' in finding.code_snippet:
        return finding.code_snippet.strip()

    description = finding.description or ''
    match = re.search(r'function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', description)
    if match:
        return f"{match.group(1)}(...)"

    return 'Not specified'


def _format_lines(finding):
    if finding.line_start and finding.line_end and finding.line_start != finding.line_end:
        return f"{finding.line_start}-{finding.line_end}"
    if finding.line_number:
        return str(finding.line_number)
    return 'N/A'


def _overall_risk_label(counts):
    if counts['critical'] > 0:
        return 'Critical - Immediate remediation required.'
    if counts['high'] > 0:
        return 'Moderate-High - Immediate attention needed on high-risk items.'
    if counts['medium'] > 0:
        return 'Moderate - Address medium findings in the next sprint.'
    if counts['low'] > 0:
        return 'Low - No urgent issues, schedule routine hardening.'
    return 'Informational - No exploitable issues detected in this scan.'


def _summary_text(contract_name, counts):
    return (
        f"This audit analyzes {contract_name} for common smart contract security vulnerabilities. "
        f"The scan identified {counts['critical']} critical, {counts['high']} high, "
        f"{counts['medium']} medium, {counts['low']} low, and {counts['info']} informational findings."
    )


def _severity_note(severity, count):
    if count == 0:
        return 'No issues identified in this severity bucket.'
    templates = {
        'critical': 'Immediate blocker - fix before deployment.',
        'high': 'High exploitation risk - prioritize remediation.',
        'medium': 'Potentially impactful - remediate in planned cycle.',
        'low': 'Hardening recommendation - low immediate risk.',
        'info': 'Informational guidance and code-quality notes.',
    }
    return templates[severity]


def _default_recommendation(severity):
    defaults = {
        'critical': 'Apply immediate patch and block production release until verification passes.',
        'high': 'Remediate before next release and validate with a regression security scan.',
        'medium': 'Plan and implement remediation during the next development iteration.',
        'low': 'Address during routine hardening and code-quality improvements.',
        'info': 'Review for best-practice alignment and monitor in future scans.',
    }
    return defaults.get(severity, defaults['info'])


def _plain_text(value):
    text = str(value or '').strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('`', '')
    return text


def _render_findings_html(vulnerabilities, severities):
    section_items = [item for item in vulnerabilities if item['severity_level'] in severities]
    if not section_items:
        return '<p>No findings in this section.</p>'

    html_items = []
    for item in section_items:
        html_items.append(
            "<article class='finding finding-{}'>"
            "<h3>{} <span class='pill sev-{}'>{}</span></h3>"
            "<p><strong>Function:</strong> {}</p>"
            "<p><strong>Lines:</strong> {}</p>"
            "<p><strong>Description:</strong> {}</p>"
            "<p><strong>Recommendation:</strong> {}</p>"
            "</article>".format(
                escape(item['severity_level']),
                escape(item['title']),
                escape(item['severity_level']),
                escape(item['severity_level'].upper()),
                escape(item['function']),
                escape(item['lines']),
                escape(item['description']),
                escape(item['recommendation']),
            )
        )
    return ''.join(html_items)