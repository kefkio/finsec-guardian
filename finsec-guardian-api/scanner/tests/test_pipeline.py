from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
import importlib.util

from scanner.models import ScanJob
from scanner.services import SlitherService


VULNERABLE_CONTRACT = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VulnerableBank {
	mapping(address => uint256) public balances;
	address public owner;

	constructor() {
		owner = msg.sender;
	}

	function deposit() public payable {
		balances[msg.sender] += msg.value;
	}

	function withdraw(uint256 _amount) public {
		require(balances[msg.sender] >= _amount, \"Insufficient balance\");
		(bool sent, ) = msg.sender.call{value: _amount}(\"\");
		require(sent, \"Failed to send Ether\");
		balances[msg.sender] -= _amount;
	}

	function insecureAuth() public view returns (bool) {
		return tx.origin == owner;
	}
}
"""


class ScannerPipelineTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='scanner-user', password='secret123')
		self.client.force_authenticate(self.user)

	def test_slither_service_detects_reentrancy(self):
		result = SlitherService().run_analysis(VULNERABLE_CONTRACT, 'VulnerableBank')

		self.assertTrue(result['success'])
		self.assertTrue(any(f['title'] == 'reentrancy-eth' for f in result['findings']))

	def test_create_scan_returns_findings_for_source_code(self):
		response = self.client.post(
			'/api/scanner/scans/',
			{
				'contract_name': 'VulnerableBank',
				'source_code': VULNERABLE_CONTRACT,
			},
			format='json',
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data['status'], 'complete')
		self.assertTrue(response.data['syntax_valid'])
		self.assertGreaterEqual(response.data['finding_count'], 1)
		self.assertTrue(any(f['title'] == 'reentrancy-eth' for f in response.data['findings']))

	def test_create_scan_accepts_solidity_file_upload(self):
		uploaded_file = SimpleUploadedFile(
			'VulnerableBank.sol',
			VULNERABLE_CONTRACT.encode('utf-8'),
			content_type='text/plain',
		)

		response = self.client.post(
			'/api/scanner/scans/',
			{
				'contract_name': 'VulnerableBank',
				'uploaded_file': uploaded_file,
			},
			format='multipart',
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data['uploaded_filename'], 'VulnerableBank.sol')
		self.assertEqual(response.data['source_type'], 'upload')
		self.assertTrue(response.data['syntax_valid'])
		self.assertGreaterEqual(response.data['finding_count'], 1)

	def test_invalid_solidity_upload_is_recorded_as_failed_scan(self):
		response = self.client.post(
			'/api/scanner/scans/',
			{
				'contract_name': 'BrokenContract',
				'source_code': 'pragma solidity ^0.8.0; contract Broken { function x( public {} }',
			},
			format='json',
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data['status'], 'failed')
		self.assertFalse(response.data['syntax_valid'])
		self.assertIn('error', response.data['compilation_error'].lower())
		self.assertEqual(ScanJob.objects.count(), 1)

	def test_export_report_returns_structured_audit_report(self):
		scan_response = self.client.post(
			'/api/scanner/scans/',
			{
				'contract_name': 'VulnerableBank',
				'source_code': VULNERABLE_CONTRACT,
			},
			format='json',
		)

		self.assertEqual(scan_response.status_code, 201)
		scan_id = scan_response.data['id']

		report_response = self.client.post(
			f'/api/scanner/scans/{scan_id}/export_report/',
			{'format': 'json', 'type': 'detailed'},
			format='json',
		)

		self.assertEqual(report_response.status_code, 200)
		self.assertIn('summary', report_response.data)
		self.assertIn('severity_levels', report_response.data['summary'])
		self.assertIn('overall_risk_level', report_response.data['summary'])
		self.assertIn('vulnerabilities', report_response.data)
		self.assertIn('function_breakdown', report_response.data)
		self.assertIn('recommendations_summary', report_response.data)

		for vulnerability in report_response.data['vulnerabilities']:
			self.assertIn('severity_level', vulnerability)
			self.assertIn('function', vulnerability)
			self.assertIn('lines', vulnerability)

	def test_export_report_returns_html_document(self):
		scan_response = self.client.post(
			'/api/scanner/scans/',
			{
				'contract_name': 'VulnerableBank',
				'source_code': VULNERABLE_CONTRACT,
			},
			format='json',
		)

		scan_id = scan_response.data['id']
		report_response = self.client.post(
			f'/api/scanner/scans/{scan_id}/export_report/',
			{'format': 'html', 'type': 'executive'},
			format='json',
		)

		self.assertEqual(report_response.status_code, 200)
		self.assertTrue(report_response['Content-Type'].startswith('text/html'))
		self.assertIn('Smart Contract Security Audit', report_response.content.decode('utf-8'))

	def test_export_report_returns_pdf_document_when_reportlab_installed(self):
		if importlib.util.find_spec('reportlab') is None:
			self.skipTest('reportlab is not installed in the current environment')

		scan_response = self.client.post(
			'/api/scanner/scans/',
			{
				'contract_name': 'VulnerableBank',
				'source_code': VULNERABLE_CONTRACT,
			},
			format='json',
		)

		scan_id = scan_response.data['id']
		report_response = self.client.post(
			f'/api/scanner/scans/{scan_id}/export_report/',
			{'format': 'pdf', 'type': 'executive'},
			format='json',
		)

		self.assertEqual(report_response.status_code, 200)
		self.assertEqual(report_response['Content-Type'], 'application/pdf')
		self.assertTrue(report_response.content.startswith(b'%PDF'))
