import json

def parse_slither_output(slither_output):
    """
    Parse Slither JSON output and return a list of findings in a normalized format.
    Each finding is a dict with keys: swc_id, title, severity, description, recommendation, line_number
    """
    findings = []
    detectors = slither_output.get('results', {}).get('detectors', [])
    for detector in detectors:
        finding = {
            'swc_id': detector.get('swc-id', ''),
            'title': detector.get('check', 'Slither Finding'),
            'severity': detector.get('impact', 'info').lower(),
            'description': detector.get('description', ''),
            'recommendation': detector.get('first_markdown_element', {}).get('markdown', ''),
            'line_number': (
                detector.get('locations', [{}])[0].get('source_mapping', {}).get('lines', [None])[0]
                if detector.get('locations') else None
            )
        }
        findings.append(finding)
    return findings
